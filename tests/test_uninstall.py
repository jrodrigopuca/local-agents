"""install.py --uninstall (B-107): the way back takes what the installer put,
and only that. Standard library only, no network:

    python3 -m unittest discover -s tests

Every test works in a throwaway HOME. The measure is the directory itself:
what was there before an install is there, byte for byte, after the uninstall.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1]
NAME = "lh-code-review"
ROOTS = {"claude": ".claude", "opencode": ".config/opencode", "kiro": ".kiro", "codex": ".codex",
         "antigravity": ".gemini/config", "shared": ".agents"}
SUFFIX = {"kiro": ".json", "codex": ".toml"}


def snapshot(root: Path) -> dict:
    """Every file under root with its bytes, and every directory."""
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root).as_posix()
        out[rel] = p.read_bytes() if p.is_file() else None
    return out


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("CLAUDE_CONFIG_DIR", "CODEX_HOME") and not k.startswith("GIT_")}
        self.env.update(HOME=str(self.home), USERPROFILE=str(self.home),
                        XDG_CONFIG_HOME=str(self.tmp / "config"),
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
                        # macOS's python keeps its bytecode cache under HOME/Library:
                        # that is the interpreter's, not the installer's
                        PYTHONDONTWRITEBYTECODE="1")

    def run_install(self, *args, ok=True):
        run = subprocess.run([sys.executable, str(CATALOG / "install.py"), *args],
                             capture_output=True, text=True, env=self.env,
                             stdin=subprocess.DEVNULL, timeout=300)
        if ok:
            self.assertEqual(run.returncode, 0, (run.stdout + run.stderr)[-800:])
        return run

    def root(self, key="claude") -> Path:
        return self.home / ROOTS[key]

    def seed(self, key="claude") -> Path:
        """A host dir the user already lives in: settings, a skill and an
        agent of their own — one of each under one of OUR names."""
        r = self.root(key)
        (r / "skills" / NAME).mkdir(parents=True)
        (r / "skills" / NAME / "SKILL.md").write_text(f"---\nname: {NAME}\ndescription: theirs\n---\nTheirs.\n")
        (r / "skills" / "mine").mkdir()
        (r / "skills" / "mine" / "SKILL.md").write_text("---\nname: mine\ndescription: x\n---\n")
        (r / "agents").mkdir()
        (r / "agents" / f"my-agent{SUFFIX.get(key, '.md')}").write_text("mine\n")
        (r / "settings.json").write_text('{"theme": "dark"}\n')
        return r


class ByteForByte(Base):
    def test_every_host_is_left_as_it_was_before_the_install(self):
        for key in ROOTS:
            with self.subTest(tool=key):
                r = self.seed(key)
                if key == "shared":
                    (r / "AGENTS.md").write_text("# Mine\n\nMy own rules.\n")
                before = snapshot(self.home)
                self.run_install("--all", "--tool", key, "--on-conflict", "skip")
                self.assertNotEqual(snapshot(self.home), before, "the install must have written something")
                self.run_install("--uninstall", "--tool", key)
                self.assertEqual(snapshot(self.home), before)

    def test_an_empty_home_is_left_with_what_the_host_dir_held(self):
        r = self.root()
        r.mkdir()
        self.run_install("--all", "--tool", "claude")
        self.run_install("--uninstall")
        self.assertEqual(snapshot(self.home), {".claude": None})

    def test_installing_again_afterwards_works(self):
        self.run_install("--all", "--tool", "claude")
        self.run_install("--uninstall")
        self.run_install("--all", "--tool", "claude")
        self.assertEqual(len(list((self.root() / "agents").iterdir())), 15)


class WhatStays(Base):
    def test_an_edited_skill_and_an_edited_agent_stay_and_are_named(self):
        self.run_install("--all", "--tool", "claude")
        skill = self.root() / "skills" / "lh-verification" / "SKILL.md"
        skill.write_text(skill.read_text() + "\nmy note\n")
        agent = self.root() / "agents" / "qa.md"
        agent.write_text(agent.read_text() + "\nmy note\n")
        out = self.run_install("--uninstall").stdout
        self.assertTrue(skill.is_file())
        self.assertIn("my note", agent.read_text())
        self.assertIn("Kept 2 files as they are:", out)
        self.assertRegex(out, r"skill lh-verification +edited by hand +~/.claude/skills/lh-verification")
        self.assertRegex(out, r"agent qa +edited by hand +~/.claude/agents/qa.md")
        self.assertIn("They are yours now", out)
        self.assertRegex(out, r"Done: 64 files removed from claude, 2 kept\.")
        self.assertEqual(sorted(p.name for p in (self.root() / "skills").iterdir()), ["lh-verification"])
        self.assertEqual(sorted(p.name for p in (self.root() / "agents").iterdir()), ["qa.md"])
        self.assertFalse((self.root() / ".local-agents.json").exists())

    def test_a_stranger_with_one_of_our_names_is_not_ours_to_remove(self):
        r = self.seed()
        theirs = (r / "skills" / NAME / "SKILL.md").read_text()
        self.run_install("--all", "--tool", "claude", "--on-conflict", "skip")
        out = self.run_install("--uninstall").stdout
        self.assertEqual((r / "skills" / NAME / "SKILL.md").read_text(), theirs)
        self.assertTrue((r / "agents" / "my-agent.md").is_file())
        self.assertIn("3 files not from this catalog were not touched.", out)

    def test_a_skill_installed_alone_goes_alone(self):
        r = self.seed()
        before = snapshot(self.home)
        self.run_install("--skill", "lh-verification", "--tool", "claude")
        self.run_install("--uninstall")
        self.assertEqual(snapshot(self.home), before)

    def test_what_kiro_backed_up_is_kiro_s(self):
        self.run_install("--all", "--tool", "kiro")
        bak = self.root("kiro") / "agents" / "qa.json.bak"
        bak.write_text("{}")
        out = self.run_install("--uninstall").stdout
        self.assertTrue(bak.is_file())
        self.assertIn("kiro: 1 backup made by Kiro itself (*.bak) remains in ~/.kiro/agents", out)
        self.assertEqual([p.name for p in (self.root("kiro") / "agents").iterdir()], ["qa.json.bak"])


class Roster(Base):
    def test_the_user_s_agents_md_keeps_everything_outside_the_markers(self):
        r = self.root("shared")
        r.mkdir()
        (r / "AGENTS.md").write_text("# Mine\n\nMy own rules.\n")
        self.run_install("--all", "--tool", "shared")
        self.assertIn("BEGIN:local-agents", (r / "AGENTS.md").read_text())
        self.run_install("--uninstall")
        self.assertEqual((r / "AGENTS.md").read_text(), "# Mine\n\nMy own rules.\n")

    def test_text_the_user_added_after_the_block_stays_too(self):
        r = self.root("shared")
        r.mkdir()
        self.run_install("--all", "--tool", "shared")
        f = r / "AGENTS.md"
        f.write_text("# Before\n\n" + f.read_text() + "\n# After\n")
        self.run_install("--uninstall")
        self.assertEqual(f.read_text(), "# Before\n\n# After\n")

    def test_a_roster_that_was_only_ours_goes_with_the_block(self):
        self.root("shared").mkdir()
        self.run_install("--all", "--tool", "shared")
        self.run_install("--uninstall")
        self.assertFalse((self.root("shared") / "AGENTS.md").exists())


class Hooks(Base):
    def test_the_hook_scripts_we_copied_go(self):
        self.root().mkdir()
        self.run_install("--all", "--tool", "claude", "--shell-write-guard", "--verify-hook")
        hooks = self.root() / "hooks" / "local-agents"
        self.assertEqual(len(list(hooks.iterdir())), 2)
        self.run_install("--uninstall")
        self.assertEqual(snapshot(self.home), {".claude": None})

    def test_a_hook_script_changed_since_stays(self):
        self.run_install("--all", "--tool", "claude", "--shell-write-guard")
        guard = self.root() / "hooks" / "local-agents" / "shell_write_guard.py"
        guard.write_text("# mine now\n")
        out = self.run_install("--uninstall").stdout
        self.assertEqual(guard.read_text(), "# mine now\n")
        self.assertRegex(out, r"hook shell_write_guard\.py +not the copy that was installed")

    def test_the_user_s_own_hooks_folder_is_not_removed(self):
        (self.root() / "hooks").mkdir(parents=True)
        (self.root() / "hooks" / "mine.sh").write_text("echo\n")
        self.run_install("--all", "--tool", "claude", "--shell-write-guard")
        self.run_install("--uninstall")
        self.assertEqual(snapshot(self.root()), {"hooks": None, "hooks/mine.sh": b"echo\n"})


class Scope(Base):
    def test_dry_run_changes_nothing_and_says_what_it_would_do(self):
        self.run_install("--all", "--tool", "claude")
        before = snapshot(self.home)
        out = self.run_install("--uninstall", "--dry-run").stdout
        self.assertEqual(snapshot(self.home), before)
        self.assertIn("would remove 66", out)       # 51 skills + 15 agents

    def test_without_a_tool_every_install_goes(self):
        self.run_install("--all", "--tool", "claude")
        self.run_install("--all", "--tool", "kiro")
        self.run_install("--uninstall")
        self.assertEqual(snapshot(self.home), {".claude": None, ".kiro": None})

    def test_with_a_tool_only_that_one_goes(self):
        self.run_install("--all", "--tool", "claude")
        self.run_install("--all", "--tool", "kiro")
        self.run_install("--uninstall", "--tool", "kiro")
        self.assertTrue((self.root() / ".local-agents.json").is_file())
        self.assertEqual(snapshot(self.root("kiro")), {})

    def test_nothing_installed_is_an_error_that_says_so(self):
        run = self.run_install("--uninstall", ok=False)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("no catalog install found", run.stderr)

    def test_it_does_not_combine_with_an_install(self):
        run = self.run_install("--uninstall", "--all", "--tool", "claude", ok=False)
        self.assertNotEqual(run.returncode, 0)

    def test_a_project_install_leaves_the_repo_as_it_was(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        (repo / "README.md").write_text("# repo\n")
        (repo / "AGENTS.md").write_text("# Mine\n")
        before = snapshot(repo)
        for key in ("claude", "shared", "codex"):
            self.run_install("--all", "--tool", key, "--project", str(repo))
        self.run_install("--uninstall", "--project", str(repo))
        self.assertEqual(snapshot(repo), before)

    def test_a_project_uninstall_does_not_reach_the_home_install(self):
        repo = self.tmp / "repo"
        repo.mkdir()
        self.run_install("--all", "--tool", "claude")
        self.run_install("--all", "--tool", "claude", "--project", str(repo))
        home_before = snapshot(self.home)
        self.run_install("--uninstall", "--project", str(repo))
        self.assertEqual(snapshot(self.home), home_before)
        self.assertEqual(snapshot(repo), {})


class DefaultAgent(Base):
    def test_a_host_still_set_to_start_with_a_removed_agent_is_flagged(self):
        self.run_install("--all", "--tool", "claude")
        (self.root() / "settings.json").write_text(json.dumps({"agent": "generalist"}))
        out = self.run_install("--uninstall").stdout
        self.assertIn("default_agent.py --restore --tool claude", out)

    def test_no_note_when_the_default_is_not_one_of_ours(self):
        self.run_install("--all", "--tool", "claude")
        (self.root() / "settings.json").write_text(json.dumps({"agent": "my-agent"}))
        self.assertNotIn("default_agent.py", self.run_install("--uninstall").stdout)


if __name__ == "__main__":
    unittest.main()
