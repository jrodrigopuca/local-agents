"""install.py's errors: one form, a command that works, and the exit codes the
launcher documents. Standard library only, no network:

    python3 -m unittest discover -s tests

    0 done · 1 error (it cannot be done) · 2 refused (it could, and is not
    safe to: nothing was changed)

Each error here is checked for what a person needs from it: what is wrong on
the first line, to stderr, and — where there is one — a `Try:` that runs.
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1]


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("CLAUDE_CONFIG_DIR", "CODEX_HOME") and not k.startswith("GIT_")}
        self.env.update(HOME=str(self.home), USERPROFILE=str(self.home),
                        XDG_CONFIG_HOME=str(self.tmp / "config"),
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                        PYTHONDONTWRITEBYTECODE="1")

    def run_install(self, *args):
        return subprocess.run([sys.executable, str(CATALOG / "install.py"), *args],
                              capture_output=True, text=True, env=self.env,
                              stdin=subprocess.DEVNULL, timeout=300)

    def error(self, *args, code=1, prefix="error: "):
        run = self.run_install(*args)
        self.assertEqual(run.returncode, code, run.stderr)
        self.assertEqual(run.stdout, "", "an error says nothing on stdout")
        self.assertTrue(run.stderr.startswith(prefix), run.stderr)
        for line in run.stderr.splitlines():
            # a path or a command is never folded; everything else fits
            if not any(len(word) > 40 for word in line.split()):
                self.assertLessEqual(len(line), 80, line)
            self.assertTrue(line.isascii(), line)
        return run.stderr

    def suggested(self, stderr):
        """The command after `Try:`, as arguments for install.py."""
        m = re.search(r"Try:\s+\./install\.py (.+)", stderr)
        self.assertIsNotNone(m, stderr)
        return m.group(1).split()


class Usage(Base):
    def test_a_mistyped_flag_is_an_error_not_a_refusal(self):
        # argparse exits 2 by itself, which the launcher's contract reads as "refused"
        err = self.error("--bogus")
        self.assertIn("unrecognized arguments: --bogus", err)
        self.assertIn("Try: ./install.py --help", err)

    def test_all_without_a_tool_lists_the_tools_and_a_command_that_runs(self):
        err = self.error("--all")
        self.assertIn("error: --all needs a target tool.", err)
        self.assertIn("Tools: claude, opencode, kiro, codex, antigravity, shared", err)
        dry = self.run_install(*self.suggested(err), "--dry-run")
        self.assertEqual(dry.returncode, 0, dry.stderr)

    def test_the_suggested_tool_is_one_that_is_there(self):
        (self.home / ".claude").rmdir()
        (self.home / ".kiro").mkdir()
        self.assertIn("--tool kiro", self.error("--all"))

    def test_an_agent_without_a_tool_keeps_what_was_asked_in_the_suggestion(self):
        err = self.error("--agent", "qa", "--skill", "lh-icons")
        self.assertEqual(self.suggested(err), ["--agent", "qa", "--skill", "lh-icons", "--tool", "claude"])
        self.assertEqual(self.run_install(*self.suggested(err), "--dry-run").returncode, 0)

    def test_uninstall_does_not_combine_with_an_install(self):
        err = self.error("--uninstall", "--all", "--tool", "kiro")
        self.assertIn("cannot be combined", " ".join(err.split()))
        self.assertEqual(self.suggested(err), ["--uninstall", "--tool", "kiro"])


class Unknown(Base):
    def test_an_unknown_tool_lists_them_and_offers_the_close_one(self):
        err = self.error("--all", "--tool", "claud")
        self.assertIn("error: unknown tool 'claud'.", err)
        self.assertIn("Did you mean: claude", err)
        self.assertNotIn("Did you mean", self.error("--all", "--tool", "vim"))

    def test_an_unknown_agent_lists_them_folded_and_offers_the_close_one(self):
        err = self.error("--agent", "archtect", "--tool", "claude")
        self.assertIn("error: unknown agent 'archtect'.", err)
        self.assertIn("Agents: apple-dev, architect,", err)
        self.assertIn("Did you mean: architect", err)

    def test_an_unknown_skill_offers_the_close_ones_and_the_list(self):
        err = self.error("--skill", "lh-verfication", "--tool", "claude")
        self.assertIn("Did you mean: lh-verification", err)
        self.assertEqual(self.suggested(err), ["--list"])

    def test_a_bad_name_is_caught_before_anything_is_installed(self):
        self.error("--agent", "qa", "--agent", "nobody", "--tool", "claude")
        self.assertEqual(list((self.home / ".claude").iterdir()), [])


class NothingThere(Base):
    def test_refresh_with_nothing_installed_says_how_to_install(self):
        err = self.error("--refresh")
        self.assertIn("error: nothing to refresh: no catalog install found.", err)
        self.assertEqual(self.suggested(err), ["--all", "--tool", "claude"])

    def test_uninstall_with_nothing_installed_names_where_it_looked(self):
        self.assertIn("no catalog install found in any tool.", self.error("--uninstall"))
        self.assertIn("no catalog install found in kiro.", self.error("--uninstall", "--tool", "kiro"))

    def test_a_project_is_carried_into_the_suggestion(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        err = self.error("--refresh", "--project", str(repo))
        self.assertIn(f"--project {repo.resolve()}", " ".join(err.split()))

    def test_a_project_that_is_not_a_folder(self):
        self.assertIn("--project needs a folder", self.error("--all", "--tool", "claude",
                                                             "--project", str(self.tmp / "nope")))

    def test_a_folder_that_is_not_the_catalog(self):
        err = self.error("--catalog", str(self.tmp), "--list")
        self.assertIn("does not look like the catalog", " ".join(err.split()))


class Refusals(Base):
    def test_installing_into_the_catalog_itself_is_refused_with_exit_2(self):
        err = self.error("--all", "--tool", "claude", "--project", str(CATALOG),
                         code=2, prefix="refused: ")
        self.assertEqual(err.splitlines()[-1], "  Nothing was changed.")
        self.assertFalse((CATALOG / ".claude" / ".local-agents.json").exists())

    def test_two_tools_that_share_a_project_folder_are_refused_with_exit_2(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        first = self.run_install("--agent", "qa", "--tool", "shared", "--project", str(repo))
        self.assertEqual(first.returncode, 0, first.stderr)
        body = repo / ".agents" / "agents" / "qa.md"
        before = body.read_text()
        err = self.error("--agent", "qa", "--tool", "antigravity", "--project", str(repo),
                         code=2, prefix="refused: ")
        self.assertIn("refused: this project already holds the shared install.", err)
        self.assertIn("remove .agents/agents first", err)
        self.assertEqual(err.splitlines()[-1], "  Nothing was changed.")
        self.assertEqual(body.read_text(), before)


if __name__ == "__main__":
    unittest.main()
