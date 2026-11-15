"""install.py --status: the answer first, decided by content. Standard library
only, no network:

    python3 -m unittest discover -s tests

What --status has to answer is "do I have to do something?". These tests pin
that answer in each situation — and that it comes from what is on disk, not
from how many commits the catalog has moved.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1]
SKILL = "lh-verification"


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.claude = self.home / ".claude"
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("CLAUDE_CONFIG_DIR", "CODEX_HOME") and not k.startswith("GIT_")}
        self.env.update(HOME=str(self.home), USERPROFILE=str(self.home),
                        XDG_CONFIG_HOME=str(self.tmp / "config"),
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
                        PYTHONDONTWRITEBYTECODE="1")
        self.catalog = CATALOG

    def run_install(self, *args):
        run = subprocess.run([sys.executable, str(self.catalog / "install.py"), *args],
                             capture_output=True, text=True, env=self.env,
                             stdin=subprocess.DEVNULL, timeout=300)
        self.assertEqual(run.returncode, 0, (run.stdout + run.stderr)[-800:])
        return run.stdout

    def status(self, *args):
        return self.run_install("--status", *args)

    def row(self, key, status):
        return next(l for l in status.splitlines() if l.startswith(f"  {key} "))

    def own_catalog(self):
        """A git copy of this checkout to move forward without touching the real one."""
        dest = self.tmp / "catalog"
        shutil.copytree(CATALOG, dest, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.catalog = dest
        self.git("init", "--quiet")
        self.commit("copy")
        return dest

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.catalog), *args], env=self.env, check=True,
                       capture_output=True)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", message)


class Verdict(Base):
    def test_nothing_installed_says_so_and_how_to_start(self):
        self.claude.mkdir()
        out = self.status()
        self.assertEqual(out.splitlines()[0], "Nothing from this catalog is installed yet.")
        self.assertEqual(self.row("claude", out).split(), ["claude", "nothing", "installed"])
        self.assertIn("not detected", self.row("kiro", out))
        self.assertIn("(~/.kiro does not exist)", self.row("kiro", out))
        self.assertIn("Next: ./install.py --all --tool claude", out)

    def test_an_install_that_matches_the_catalog_is_up_to_date(self):
        self.run_install("--all", "--tool", "claude")
        out = self.status()
        self.assertEqual(out.splitlines()[0], "Everything installed is up to date.")
        self.assertRegex(self.row("claude", out), r"^  claude +up to date +15 agents, 51 skills$")
        self.assertIn("Details: ./install.py --status --verbose", out)
        self.assertNotIn("Next:", out)

    def test_commits_that_change_no_installed_file_are_not_something_to_do(self):
        # The false alarm this replaced: "11 commit(s) behind" on six tools
        # when not one installed file differed.
        self.own_catalog()
        self.run_install("--all", "--tool", "claude")
        (self.catalog / "BACKLOG.es.md").write_text("changed\n")
        self.commit("docs only")
        (self.catalog / "README.md").write_text("changed too\n")
        self.commit("docs again")
        out = self.status()
        self.assertEqual(out.splitlines()[0], "Everything installed is up to date.")
        self.assertNotIn("commit", out)
        verbose = " ".join(self.status("--verbose").split())
        self.assertIn("2 commits before", verbose)
        self.assertIn("no installed file differs", verbose)

    def test_a_skill_the_catalog_changed_is_out_of_date_and_named(self):
        self.own_catalog()
        self.run_install("--all", "--tool", "claude")
        md = self.catalog / "generalist" / "skills" / SKILL / "SKILL.md"
        md.write_text(md.read_text() + "\nA new line upstream.\n")
        self.commit("skill changed")
        out = self.status()
        self.assertEqual(out.splitlines()[0], "1 of 1 tool is out of date.")
        self.assertRegex(self.row("claude", out), rf"^  claude +1 out of date +{SKILL}$")
        self.assertIn("Next: ./install.py --refresh", out)
        self.assertIn("a refresh brings what changed", " ".join(self.status("--verbose").split()))
        self.run_install("--refresh")
        self.assertEqual(self.status().splitlines()[0], "Everything installed is up to date.")

    def test_a_changed_agent_is_named_as_an_agent(self):
        self.own_catalog()
        self.run_install("--all", "--tool", "claude")
        md = self.catalog / "qa" / "AGENTS.md"
        md.write_text(md.read_text() + "\nOne more line.\n")
        self.commit("agent changed")
        self.assertRegex(self.row("claude", self.status()), r"1 out of date +agent qa$")

    def test_the_count_is_of_tools_that_hold_an_install(self):
        self.own_catalog()
        self.run_install("--all", "--tool", "claude")
        self.run_install("--all", "--tool", "kiro")
        (self.home / ".codex").mkdir()                 # detected, nothing installed
        md = self.catalog / "qa" / "AGENTS.md"
        md.write_text(md.read_text() + "\nOne more line.\n")
        self.commit("agent changed")
        self.assertEqual(self.status().splitlines()[0], "2 of 2 tools are out of date.")

    def test_what_the_whole_catalog_gained_is_missing_from_a_whole_install(self):
        self.own_catalog()
        self.run_install("--all", "--tool", "claude")
        new = self.catalog / "generalist" / "skills" / "lh-brand-new"
        shutil.copytree(self.catalog / "generalist" / "skills" / SKILL, new)
        md = new / "SKILL.md"
        md.write_text(md.read_text().replace(f"name: {SKILL}", "name: lh-brand-new")
                      .replace('local-agents-id: "', 'local-agents-id: "sk-0f0f0f" # was "'))
        self.commit("a new skill")
        out = self.status()
        self.assertEqual(out.splitlines()[0], "1 of 1 tool is out of date.", out)
        self.assertIn("lh-brand-new", self.row("claude", out))

    def test_one_skill_installed_alone_is_not_missing_the_other_fifty(self):
        self.run_install("--skill", SKILL, "--tool", "claude")
        out = self.status()
        self.assertEqual(out.splitlines()[0], "Everything installed is up to date.")
        self.assertRegex(self.row("claude", out), r"up to date +0 agents, 1 skills$")

    def test_a_file_edited_by_hand_is_said_and_is_not_out_of_date(self):
        self.run_install("--all", "--tool", "claude")
        md = self.claude / "skills" / SKILL / "SKILL.md"
        md.write_text(md.read_text() + "\nmine\n")
        out = self.status()
        self.assertEqual(out.splitlines()[0], "Everything installed is up to date.")
        self.assertIn(f"1 edited by hand, kept as it is: {SKILL}", out)

    def test_a_hook_script_that_fell_behind_counts(self):
        self.run_install("--all", "--tool", "claude", "--shell-write-guard")
        (self.claude / "hooks" / "local-agents" / "shell_write_guard.py").write_text("# old\n")
        out = self.status()
        self.assertEqual(out.splitlines()[0], "1 of 1 tool is out of date.")
        self.assertIn("shell-write guard script", self.row("claude", out))


class Shape(Base):
    def outputs(self):
        self.own_catalog()
        self.run_install("--all", "--tool", "claude", "--shell-write-guard")
        self.run_install("--all", "--tool", "shared")
        yield self.status()
        yield self.status("--verbose")
        for name in ("lh-verification", "lh-decomposition", "lh-next-step", "lh-pairing", "lh-mentoring"):
            md = next(self.catalog.glob(f"*/skills/{name}/SKILL.md"))
            md.write_text(md.read_text() + "\nA new line upstream.\n")
        self.commit("five skills changed")
        (self.claude / "skills" / "lh-icons" / "SKILL.md").write_text("mine\n")
        (self.home / ".agents" / "AGENTS.md").unlink()
        yield self.status()
        yield self.status("--verbose")

    def test_every_line_fits_80_columns_and_is_plain_ascii(self):
        for out in self.outputs():
            for line in out.splitlines():
                self.assertLessEqual(len(line), 80, line)
                self.assertTrue(line.isascii(), line)

    def test_a_long_list_of_names_is_cut_with_a_count(self):
        *_, behind, _verbose = self.outputs()
        self.assertIn("+1 more", self.row("claude", behind) + behind)

    def test_a_warning_names_the_tool_and_the_command(self):
        *_, behind, _verbose = self.outputs()
        flat = " ".join(behind.split())
        self.assertIn("! shared: the agent index (AGENTS.md) is missing", flat)
        self.assertIn("Try: ./install.py --all --tool shared", behind)

    def test_verbose_gives_each_tool_its_block(self):
        _, verbose, *_ = self.outputs()
        self.assertIn("claude (Claude Code)  ~/.claude", verbose)
        self.assertIn("  skills    51 of 51 installed", verbose)
        self.assertIn("  index     15 rows in AGENTS.md", verbose)
        self.assertIn("shell-write guard on, script current", verbose)
        self.assertIn("verify hook off", verbose)
        self.assertIn("enable: ./install.py --refresh --verify-hook", verbose)


class Project(Base):
    def test_a_project_is_named_and_its_paths_are_relative_to_it(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.run_install("--all", "--tool", "claude", "--project", str(repo))
        out = self.status("--project", str(repo))
        self.assertEqual(out.splitlines()[0], "Everything installed is up to date.")
        self.assertIn(f"Project: {repo.resolve()}", out)
        self.assertIn("(.kiro does not exist)", self.row("kiro", out))
        self.assertIn(f"--status --verbose --project {repo.resolve()}", out)
        self.assertIn("claude (Claude Code, project repo/)  .claude", self.status("--verbose", "--project", str(repo)))


if __name__ == "__main__":
    unittest.main()
