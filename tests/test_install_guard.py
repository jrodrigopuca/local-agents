"""`install.py --shell-write-guard` (B-083): off by default, on when asked,
remembered by --refresh, reported by --status, and taken out again by
--no-shell-write-guard. Every test installs into a throwaway HOME:

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
HOOK = 'hooks:\n  PreToolUse:\n    - matcher: "Bash"\n'


class ShellWriteGuardInstall(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(self._tmp.name)
        self.home = tmp / "home"
        self.home.mkdir()
        self.claude = self.home / ".claude"
        self.script = self.claude / "hooks" / "local-agents" / "shell_write_guard.py"
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

    def stamp(self):
        return json.loads((self.claude / ".local-agents.json").read_text())

    def frontmatter(self, name):
        return self.agent(name).split("\n---\n", 1)[0]

    def test_off_by_default(self):
        self.install("--all", "--tool", "claude")
        self.assertNotIn("hooks:", self.frontmatter(FULL))
        self.assertFalse(self.script.exists())
        self.assertIs(self.stamp()["shell_write_guard"], False)
        self.assertIn("shell-write guard off", self.install("--status"))

    def test_on_hooks_every_full_agent_and_no_read_agent(self):
        self.install("--all", "--tool", "claude", "--shell-write-guard")
        fm = self.frontmatter(FULL)
        self.assertIn(HOOK, fm)
        self.assertIn(f'command: "python3 \\"{self.script}\\""', fm)
        # The read tier has no Bash: a hook there would guard nothing.
        self.assertNotIn("hooks:", self.frontmatter(READ))
        self.assertEqual(self.script.read_bytes(),
                         (CATALOG / "scripts" / "shell_write_guard.py").read_bytes())
        st = self.stamp()
        self.assertIs(st["shell_write_guard"], True)
        self.assertEqual(len(st["shell_write_guard_sha256"]), 64)

    def test_the_installed_hook_command_runs_the_guard(self):
        self.install("--all", "--tool", "claude", "--shell-write-guard")
        event = {"tool_name": "Bash", "tool_input": {"command": "cat > a.txt <<'EOF'\nx\nEOF"}}
        proc = subprocess.run([sys.executable, str(self.script)], input=json.dumps(event),
                              capture_output=True, text=True, timeout=30)
        self.assertEqual(json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"],
                         "deny")

    def test_status_reports_on_and_agents_current(self):
        self.install("--all", "--tool", "claude", "--shell-write-guard")
        out = self.install("--status")
        self.assertIn("shell-write guard on · script current", out)
        claude = out.split("Claude Code  (claude)")[1].split("\n\n")[0]
        self.assertNotIn("stale", claude)

    def test_refresh_keeps_it_and_no_flag_turns_it_off(self):
        self.install("--all", "--tool", "claude", "--shell-write-guard")
        self.install("--refresh")
        self.assertIn(HOOK, self.frontmatter(FULL))
        self.install("--refresh", "--no-shell-write-guard")
        self.assertNotIn("hooks:", self.frontmatter(FULL))
        self.assertFalse(self.script.exists())
        self.assertIs(self.stamp()["shell_write_guard"], False)

    def test_a_script_edited_by_hand_is_not_removed(self):
        self.install("--all", "--tool", "claude", "--shell-write-guard")
        self.script.write_text("# mine now\n")
        self.install("--refresh", "--no-shell-write-guard")
        self.assertTrue(self.script.exists())

    def test_a_project_install_points_at_the_repo_copy(self):
        repo = Path(self._tmp.name) / "repo"
        repo.mkdir()
        self.install("--all", "--tool", "claude", "--project", str(repo), "--shell-write-guard")
        fm = (repo / ".claude" / "agents" / f"{FULL}.md").read_text()
        self.assertIn('$CLAUDE_PROJECT_DIR/.claude/hooks/local-agents/shell_write_guard.py', fm)
        self.assertTrue((repo / ".claude" / "hooks" / "local-agents" / "shell_write_guard.py").is_file())

    def test_other_hosts_are_untouched(self):
        self.install("--all", "--tool", "kiro", "--shell-write-guard")
        kiro = json.loads((self.home / ".kiro" / "agents" / f"{FULL}.json").read_text())
        self.assertNotIn("hooks", kiro)
        self.assertNotIn("shell_write_guard", self.stamp_of(self.home / ".kiro"))

    def stamp_of(self, root):
        return json.loads((root / ".local-agents.json").read_text())


if __name__ == "__main__":
    unittest.main()
