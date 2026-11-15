"""What an install, a refresh and an uninstall SAY: one row per tool, what was
kept and why, one closing line — and one line per file only on request.
Standard library only, no network:

    python3 -m unittest discover -s tests

The counts are the point. "3 updated, 63 unchanged" is only worth printing if
it is true, and a dry run only worth running if it predicts the real one.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1]
SKILL = "lh-verification"


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_bytes() if p.is_file() else None
            for p in sorted(root.rglob("*"))}


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

    def own_catalog(self):
        dest = self.tmp / "catalog"
        shutil.copytree(CATALOG, dest, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.catalog = dest
        self.git("init", "--quiet")
        self.commit("copy")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.catalog), *args], env=self.env, check=True,
                       capture_output=True)

    def commit(self, message):
        self.git("add", "-A")
        self.git("commit", "--quiet", "-m", message)

    def change_upstream(self, *skills, agent=None):
        for name in skills:
            md = next(self.catalog.glob(f"*/skills/{name}/SKILL.md"))
            md.write_text(md.read_text() + "\nA new line upstream.\n")
        if agent:
            md = self.catalog / agent / "AGENTS.md"
            md.write_text(md.read_text() + "\nOne more line.\n")
        self.commit("upstream change")

    def row(self, key, out):
        return next(l for l in out.splitlines() if l.startswith(f"  {key} "))


class Install(Base):
    def test_a_first_install_counts_what_it_installed(self):
        out = self.run_install("--all", "--tool", "claude")
        self.assertEqual(out.splitlines()[0], "Installing the whole catalog into claude (~/.claude)")
        self.assertRegex(out, r"(?m)^  skills +51 installed$")
        self.assertRegex(out, r"(?m)^  agents +15 installed$")
        self.assertRegex(out, r"(?m)^Done: 66 files installed in claude(, from catalog [0-9a-f]{7})?\.$")
        self.assertIn("Check any time: ./install.py --status", out)

    def test_installing_again_changes_nothing_and_says_so(self):
        self.run_install("--all", "--tool", "claude")
        out = self.run_install("--all", "--tool", "claude")
        self.assertRegex(out, r"(?m)^  skills +51 unchanged$")
        self.assertRegex(out, r"(?m)^  agents +15 unchanged$")
        self.assertIn("Done: nothing to change in claude; 66 files already up to date.", out)

    def test_the_normal_view_is_short_and_verbose_has_a_line_per_file(self):
        out = self.run_install("--all", "--tool", "claude")
        self.assertLess(len(out.splitlines()), 12, out)
        self.claude.joinpath(".local-agents.json").unlink()
        shutil.rmtree(self.claude)
        verbose = self.run_install("--all", "--tool", "claude", "--verbose")
        files = [l for l in verbose.splitlines() if re.match(r"  installed +(skill|agent) ", l)]
        self.assertEqual(len(files), 66)
        self.assertIn("claude (Claude Code)  ~/.claude", verbose)
        self.assertRegex(verbose, r"(?m)^Done: 66 files installed in claude")

    def test_one_agent_brings_its_skills_and_names_what_it_is_installing(self):
        out = self.run_install("--agent", "qa", "--tool", "claude")
        self.assertEqual(out.splitlines()[0], "Installing agent qa into claude (~/.claude)")
        self.assertRegex(out, r"(?m)^  agents +1 installed$")
        self.assertRegex(out, r"(?m)^  skills +\d+ installed$")

    def test_an_option_turned_on_is_a_row_and_one_already_there_is_not(self):
        out = self.run_install("--all", "--tool", "claude", "--shell-write-guard")
        self.assertRegex(out, r"(?m)^  options +1 installed$")
        self.assertRegex(out, r"Done: 67 files installed")
        again = self.run_install("--refresh")
        self.assertNotIn("options", again)

    def test_a_tool_that_keeps_an_index_says_what_happened_to_it(self):
        out = self.run_install("--all", "--tool", "shared")
        self.assertRegex(out, r"(?m)^  index +agent index \(AGENTS\.md\) written$")


class Refresh(Base):
    def test_nothing_to_bring_is_one_line(self):
        self.run_install("--all", "--tool", "claude")
        out = self.run_install("--refresh")
        self.assertRegex(out, r"No installed file differs from (catalog [0-9a-f]{7}|the catalog)\. "
                              r"Nothing to update\.")
        self.assertNotIn("Done:", out)
        self.assertLess(len(out.splitlines()), 6)

    def test_it_counts_what_changed_and_what_did_not(self):
        self.own_catalog()
        self.run_install("--all", "--tool", "claude")
        self.change_upstream(SKILL, "lh-pairing", agent="qa")
        out = self.run_install("--refresh")
        self.assertRegex(out.splitlines()[0], r"^Updating 1 tool from catalog [0-9a-f]{7}$")
        self.assertRegex(self.row("claude", out), r"^  claude +3 updated, 63 unchanged$")
        self.assertIn("Done: 3 files updated in claude.", out)

    def test_several_tools_get_a_row_each_and_one_total(self):
        self.own_catalog()
        self.run_install("--all", "--tool", "claude")
        self.run_install("--all", "--tool", "kiro")
        self.change_upstream(SKILL)
        out = self.run_install("--refresh")
        self.assertRegex(self.row("claude", out), r"1 updated, 65 unchanged$")
        self.assertRegex(self.row("kiro", out), r"1 updated, 65 unchanged$")
        self.assertIn("Done: 2 files updated in 2 tools.", out)

    def test_a_kept_file_is_named_with_its_reason_its_path_and_the_way_out(self):
        self.own_catalog()
        self.run_install("--all", "--tool", "claude")
        self.run_install("--all", "--tool", "kiro")
        mine = self.claude / "skills" / "lh-pairing" / "SKILL.md"
        mine.write_text(mine.read_text() + "\nmine\n")
        self.change_upstream(SKILL, "lh-pairing")
        out = self.run_install("--refresh")
        self.assertRegex(self.row("claude", out), r"1 updated, 64 unchanged, 1 kept$")
        self.assertIn("Kept 1 file as it is:", out)
        self.assertRegex(out, r"(?m)^  claude +skill lh-pairing +edited by hand +"
                              r"~/\.claude/skills/lh-pairing$")
        self.assertIn("  ./install.py --all --tool claude --on-conflict overwrite", out)
        self.assertNotIn("--tool kiro --on-conflict", out)          # nothing was kept there
        self.assertIn("Done: 3 files updated in 2 tools, 1 kept.", out)
        self.assertIn("mine", mine.read_text())


class DryRun(Base):
    def counts(self, out):
        return self.row("claude", out).split(None, 1)[1].replace("would update", "updated").split(", ")

    def test_a_dry_run_predicts_the_real_run_and_writes_nothing(self):
        self.own_catalog()
        self.run_install("--all", "--tool", "claude")
        self.change_upstream(SKILL, "lh-pairing", agent="architect")
        before = snapshot(self.home)
        dry = self.run_install("--refresh", "--dry-run")
        self.assertEqual(snapshot(self.home), before)
        self.assertEqual(dry.splitlines()[0], "Dry run: nothing is written.")
        self.assertRegex(self.row("claude", dry), r"would update 3, 63 unchanged$")
        self.assertIn("Done (dry run): would update 3 files in claude.", dry)
        self.assertEqual(dry.splitlines()[-1],
                         "Dry run: nothing was written. Run again without --dry-run to apply.")
        real = self.run_install("--refresh")
        self.assertRegex(self.row("claude", real), r"3 updated, 63 unchanged$")

    def test_a_dry_run_with_nothing_to_bring_agrees_with_the_real_one(self):
        self.run_install("--all", "--tool", "claude")
        self.assertIn("Nothing to update.", self.run_install("--refresh", "--dry-run"))
        self.assertIn("Nothing to update.", self.run_install("--refresh"))

    def test_a_dry_run_of_a_first_install(self):
        out = self.run_install("--all", "--tool", "claude", "--dry-run")
        self.assertRegex(out, r"(?m)^  skills +would install 51$")
        self.assertRegex(out, r"(?m)^  agents +would install 15$")
        self.assertIn("Done (dry run): would install 66 files in claude.", out)
        self.assertNotIn("Check any time", out)
        self.assertFalse(self.claude.exists())

    def test_a_dry_run_names_the_old_copy_it_would_remove(self):
        self.own_catalog()
        self.run_install("--all", "--tool", "claude")
        self.run_install("--skill", SKILL, "--tool", "claude")
        old = self.claude / "skills" / "lh-verification-old"
        shutil.copytree(self.claude / "skills" / SKILL, old)
        # recorded under the old name, as an install before a rename would have left it
        import json
        stamp_file = self.claude / ".local-agents.json"
        stamp = json.loads(stamp_file.read_text())
        sid = next(k for k, v in stamp["skills"].items() if v["name"] == SKILL)
        stamp["skills"][sid] = {"name": "lh-verification-old", "sha256": self._tree_hash(old)}
        stamp_file.write_text(json.dumps(stamp))
        out = self.run_install("--refresh", "--dry-run", "--verbose")
        self.assertRegex(out, r"would remove +skill lh-verification-old +old copy of lh-verification")
        self.assertTrue(old.is_dir())

    def _tree_hash(self, d):
        import importlib.util
        spec = importlib.util.spec_from_file_location("installer_for_hash", CATALOG / "install.py")
        mod = importlib.util.module_from_spec(spec)
        sys.modules["installer_for_hash"] = mod
        spec.loader.exec_module(mod)
        return mod.tree_hash(d)


class Uninstall(Base):
    def test_it_counts_what_it_removed(self):
        self.run_install("--all", "--tool", "claude")
        self.run_install("--all", "--tool", "shared")
        out = self.run_install("--uninstall")
        self.assertEqual(out.splitlines()[0], "Removing what this installer put in 2 tools")
        self.assertRegex(self.row("claude", out), r"^  claude +66 removed$")
        self.assertRegex(self.row("shared", out), r"66 removed, agent index removed from AGENTS\.md$")
        self.assertIn("Done: 132 files removed from 2 tools.", out)
        self.assertNotIn("Check any time", out)

    def test_a_default_agent_left_behind_is_one_note_for_every_tool(self):
        import json
        self.run_install("--all", "--tool", "claude")
        self.run_install("--all", "--tool", "kiro")
        (self.claude / "settings.json").write_text(json.dumps({"agent": "generalist"}))
        (self.home / ".kiro" / "settings").mkdir()
        (self.home / ".kiro" / "settings" / "cli.json").write_text(
            json.dumps({"chat.defaultAgent": "generalist"}))
        out = self.run_install("--uninstall")
        self.assertEqual(out.count("default_agent.py"), 1)
        self.assertIn("Still to do:", out)
        self.assertIn("Try: ./default_agent.py --restore --tool claude,kiro", out)


class Shape(Base):
    def test_every_line_fits_80_columns_and_is_plain_ascii(self):
        self.own_catalog()
        outs = [self.run_install("--all", "--tool", "claude", "--shell-write-guard"),
                self.run_install("--all", "--tool", "shared")]
        mine = self.claude / "skills" / "lh-pairing" / "SKILL.md"
        mine.write_text(mine.read_text() + "\nmine\n")
        self.change_upstream(SKILL, "lh-pairing", agent="qa")
        outs += [self.run_install("--refresh", "--dry-run"), self.run_install("--refresh", "--verbose"),
                 self.run_install("--agent", "qa", "--agent", "security", "--agent", "architect",
                                  "--skill", "lh-icons", "--tool", "claude"),
                 self.run_install("--uninstall", "--dry-run"), self.run_install("--uninstall")]
        for out in outs:
            for line in out.splitlines():
                self.assertLessEqual(len(line), 80, line)
                self.assertTrue(line.isascii(), line)


if __name__ == "__main__":
    unittest.main()
