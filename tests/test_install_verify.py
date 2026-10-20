"""`install.py --verify-hook [CMD]` (B-084): off by default, on when asked
(each repo declares its check; CMD is the optional default), remembered by
--refresh, reported by --status, and taken out again by --no-verify-hook.
Every test installs into a throwaway HOME:

    python3 -m unittest discover -s tests
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_install import CATALOG, clean_env

FULL, READ = "senior-dev", "visionary"   # access: full / access: read
CMD = "npm test -- --silent"
STOP = "  Stop:\n    - hooks:\n        - type: command\n"
GUARD = 'hooks:\n  PreToolUse:\n    - matcher: "Bash"\n'


class VerifyHookInstall(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(self._tmp.name)
        self.home = tmp / "home"
        self.home.mkdir()
        self.claude = self.home / ".claude"
        self.script = self.claude / "hooks" / "local-agents" / "verify_before_stop.py"
        self.env = clean_env(HOME=str(self.home), USERPROFILE=str(self.home),
                             XDG_CONFIG_HOME=str(tmp / "config"))

    def install(self, *args):
        run = subprocess.run([sys.executable, str(CATALOG / "install.py"), *args],
                             capture_output=True, text=True, env=self.env,
                             stdin=subprocess.DEVNULL, timeout=300)
        self.assertEqual(run.returncode, 0, run.stderr[-800:])
        return run.stdout

    def agent(self, name):
        return (self.claude / "agents" / f"{name}.md").read_text()

    def frontmatter(self, name):
        return self.agent(name).split("\n---\n", 1)[0]

    def stamp(self):
        return json.loads((self.claude / ".local-agents.json").read_text())

    def test_off_by_default(self):
        self.install("--all", "--tool", "claude")
        self.assertNotIn("hooks:", self.frontmatter(FULL))
        self.assertFalse(self.script.exists())
        self.assertIs(self.stamp()["verify_hook"], False)
        self.assertIn("verify hook off", self.install("--status"))

    def test_bare_flag_hooks_every_full_agent_without_a_default(self):
        self.install("--all", "--tool", "claude", "--verify-hook")
        fm = self.frontmatter(FULL)
        self.assertIn("hooks:\n" + STOP, fm)
        self.assertIn(f'command: "python3 \\"{self.script}\\""', fm)
        # The read tier has no work a check could fail.
        self.assertNotIn("hooks:", self.frontmatter(READ))
        self.assertEqual(self.script.read_bytes(),
                         (CATALOG / "scripts" / "verify_before_stop.py").read_bytes())
        st = self.stamp()
        self.assertIs(st["verify_hook"], True)
        self.assertEqual(st["verify_hook_default"], "")
        self.assertEqual(len(st["verify_hook_sha256"]), 64)
        self.assertIn("verify hook on · runs each repo's .local-agents/verify, no default",
                      self.install("--status"))

    def test_a_command_is_the_default_on_argv(self):
        self.install("--all", "--tool", "claude", "--verify-hook", CMD)
        self.assertIn(f'command: "python3 \\"{self.script}\\" \'{CMD}\'"', self.frontmatter(FULL))
        self.assertEqual(self.stamp()["verify_hook_default"], CMD)

    def test_the_installed_hook_command_runs_the_repos_declared_check(self):
        red = f'"{sys.executable}" -c "import sys; print(\'1 failing\'); sys.exit(1)"'
        self.install("--all", "--tool", "claude", "--verify-hook")
        repo = Path(self._tmp.name) / "work"
        (repo / ".local-agents").mkdir(parents=True)
        (repo / ".local-agents" / "verify").write_text(red + "\n")
        fm = self.frontmatter(FULL)
        line = next(l for l in fm.splitlines() if "command:" in l and "verify_before_stop" in l)
        command = json.loads(line.split("command:", 1)[1].strip())
        event = json.dumps({"hook_event_name": "SubagentStop", "stop_hook_active": False,
                            "cwd": str(repo)})
        proc = subprocess.run(command, shell=True, input=event, capture_output=True,
                              text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        out = json.loads(proc.stdout)
        self.assertEqual(out["decision"], "block")
        self.assertIn("1 failing", out["reason"])

    def test_both_hooks_share_one_block(self):
        self.install("--all", "--tool", "claude", "--shell-write-guard", "--verify-hook", CMD)
        fm = self.frontmatter(FULL)
        self.assertIn(GUARD, fm)
        self.assertIn(STOP, fm)
        self.assertEqual(sum(1 for l in fm.splitlines() if l == "hooks:"), 1)
        self.assertLess(fm.index("PreToolUse:"), fm.index("Stop:"))

    def test_status_reports_the_default_and_agents_current(self):
        self.install("--all", "--tool", "claude", "--verify-hook", CMD)
        out = self.install("--status")
        self.assertIn(f"verify hook on · runs each repo's .local-agents/verify, default {CMD!r} "
                      f"· script current", out)
        claude = out.split("Claude Code  (claude)")[1].split("\n\n")[0]
        self.assertNotIn("stale", claude)

    def test_refresh_keeps_it_a_new_default_replaces_it_and_no_flag_turns_it_off(self):
        self.install("--all", "--tool", "claude", "--verify-hook", CMD)
        self.install("--refresh")
        self.assertIn(f"'{CMD}'", self.frontmatter(FULL))
        self.install("--refresh", "--verify-hook")            # bare: on, default kept
        self.assertIn(f"'{CMD}'", self.frontmatter(FULL))
        self.install("--refresh", "--verify-hook", "make check")
        self.assertIn("'make check'", self.frontmatter(FULL))
        self.assertNotIn(CMD, self.frontmatter(FULL))
        self.assertEqual(self.stamp()["verify_hook_default"], "make check")
        self.install("--refresh", "--no-verify-hook")
        self.assertNotIn("hooks:", self.frontmatter(FULL))
        self.assertFalse(self.script.exists())
        self.assertIs(self.stamp()["verify_hook"], False)
        self.assertNotIn("verify_hook_default", self.stamp())

    def test_turning_one_hook_off_leaves_the_other(self):
        self.install("--all", "--tool", "claude", "--shell-write-guard", "--verify-hook", CMD)
        self.install("--refresh", "--no-shell-write-guard")
        fm = self.frontmatter(FULL)
        self.assertNotIn("PreToolUse:", fm)
        self.assertIn(STOP, fm)
        self.assertTrue(self.script.exists())

    def test_a_script_edited_by_hand_is_not_removed(self):
        self.install("--all", "--tool", "claude", "--verify-hook", CMD)
        self.script.write_text("# mine now\n")
        self.install("--refresh", "--no-verify-hook")
        self.assertTrue(self.script.exists())

    def test_a_project_install_points_at_the_repo_copy(self):
        repo = Path(self._tmp.name) / "repo"
        repo.mkdir()
        self.install("--all", "--tool", "claude", "--project", str(repo), "--verify-hook", CMD)
        fm = (repo / ".claude" / "agents" / f"{FULL}.md").read_text()
        self.assertIn('$CLAUDE_PROJECT_DIR/.claude/hooks/local-agents/verify_before_stop.py', fm)
        self.assertTrue((repo / ".claude" / "hooks" / "local-agents" / "verify_before_stop.py").is_file())

    def test_other_hosts_are_untouched(self):
        self.install("--all", "--tool", "kiro", "--verify-hook", CMD)
        kiro = json.loads((self.home / ".kiro" / "agents" / f"{FULL}.json").read_text())
        self.assertNotIn("hooks", kiro)
        self.assertNotIn("verify_hook",
                         json.loads((self.home / ".kiro" / ".local-agents.json").read_text()))


if __name__ == "__main__":
    unittest.main()
