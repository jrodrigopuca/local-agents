"""The verify hook (B-084): runs the project's check when the agent tries to
finish, blocks once with the failure, and never blocks when it cannot judge.
Standard library only:

    python3 -m unittest discover -s tests
"""
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_before_stop.py"
_spec = importlib.util.spec_from_file_location("verify_before_stop", SCRIPT)
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)

PY = sys.executable
GREEN = f'"{PY}" -c "print(\'42 passing\')"'
RED = f'"{PY}" -c "import sys; print(\'1 failing: parseMoney rounds down\'); sys.exit(1)"'


def run(cmd, event, env=None):
    """main() on one event; returns (exit code, parsed stdout or None, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    rc = hook.main([cmd] if cmd is not None else [], io.StringIO(json.dumps(event)), out, err,
                   environ=env or {})
    text = out.getvalue()
    return rc, (json.loads(text) if text else None), err.getvalue()


def stop(**fields):
    return {"hook_event_name": "Stop", "stop_hook_active": False, **fields}


class Blocking(unittest.TestCase):

    def test_green_check_is_silent(self):
        rc, out, err = run(GREEN, stop())
        self.assertEqual((rc, out, err), (0, None, ""))

    def test_red_check_blocks_with_exit_code_and_output(self):
        rc, out, _ = run(RED, stop())
        self.assertEqual(rc, 0)
        self.assertEqual(out["decision"], "block")
        self.assertIn("(exit 1)", out["reason"])
        self.assertIn("1 failing: parseMoney rounds down", out["reason"])
        self.assertIn(RED, out["reason"])

    def test_subagent_stop_is_the_same_event(self):
        rc, out, _ = run(RED, {"hook_event_name": "SubagentStop", "stop_hook_active": False})
        self.assertEqual(out["decision"], "block")

    def test_second_attempt_goes_through_without_running(self):
        with tempfile.TemporaryDirectory() as tmp:
            marker = Path(tmp) / "ran"
            cmd = f'"{PY}" -c "open({str(marker)!r}, \'w\').close(); raise SystemExit(1)"'
            rc, out, _ = run(cmd, stop(stop_hook_active=True))
            self.assertEqual((rc, out), (0, None))
            self.assertFalse(marker.exists(), "the budget is one block per turn")

    def test_runs_in_the_session_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "marker").write_text("x")
            cmd = f'"{PY}" -c "import os, sys; sys.exit(0 if os.path.exists(\'marker\') else 3)"'
            self.assertEqual(run(cmd, stop(cwd=tmp))[1], None)
            self.assertEqual(run(cmd, stop(cwd=tempfile.gettempdir()))[1]["decision"], "block")

    def test_a_missing_cwd_does_not_break_the_hook(self):
        rc, out, _ = run(GREEN, stop(cwd="/nonexistent/dir/for/sure"))
        self.assertEqual((rc, out), (0, None))

    def test_only_the_tail_of_a_long_output_is_sent(self):
        cmd = f'"{PY}" -c "import sys; [print(f\'line {{i}}\') for i in range(200)]; sys.exit(2)"'
        reason = run(cmd, stop())[1]["reason"]
        self.assertIn("line 199", reason)
        self.assertNotIn("line 0\n", reason)
        self.assertIn("(exit 2)", reason)

    def test_stderr_of_the_check_is_part_of_the_output(self):
        cmd = f'"{PY}" -c "import sys; sys.stderr.write(\'TypeError: boom\\n\'); sys.exit(1)"'
        self.assertIn("TypeError: boom", run(cmd, stop())[1]["reason"])


class Silence(unittest.TestCase):

    def test_other_events_are_ignored(self):
        event = {"hook_event_name": "PreToolUse", "tool_name": "Bash"}
        self.assertEqual(run(RED, event), (0, None, ""))

    def test_no_file_and_no_default_means_nothing_to_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".git").mkdir()
            rc, out, err = run(None, stop(cwd=tmp))
        self.assertEqual((rc, out), (0, None))
        self.assertIn("nothing to check", err)
        self.assertIn("no install default", err)

    def test_env_switch_turns_it_off(self):
        rc, out, err = run(RED, stop(), env={"LOCAL_AGENTS_VERIFY_HOOK": "off"})
        self.assertEqual((rc, out, err), (0, None, ""))


class ProjectFile(unittest.TestCase):
    """The repo declares its check in .local-agents/verify; argv is the default."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name) / "repo"
        (self.repo / ".git").mkdir(parents=True)
        (self.repo / "pkg" / "sub").mkdir(parents=True)

    def declare(self, text, where=None):
        d = (where or self.repo) / ".local-agents"
        d.mkdir(exist_ok=True)
        (d / "verify").write_text(text)

    def test_the_declared_check_beats_the_default(self):
        self.declare(RED + "\n")
        out = run(GREEN, stop(cwd=str(self.repo)))[1]
        self.assertEqual(out["decision"], "block")
        self.assertIn("declared in", out["reason"])
        self.assertIn(".local-agents", out["reason"])

    def test_found_from_a_subdirectory_up_to_the_repo_root(self):
        self.declare(RED + "\n")
        self.assertEqual(run(None, stop(cwd=str(self.repo / "pkg" / "sub")))[1]["decision"], "block")

    def test_not_found_beyond_the_repo_root(self):
        self.declare(RED + "\n", where=Path(self._tmp.name))   # above the .git
        rc, out, err = run(None, stop(cwd=str(self.repo)))
        self.assertEqual((rc, out), (0, None))
        self.assertIn("nothing to check", err)

    def test_comments_and_blank_lines_are_skipped(self):
        self.declare("# the suite, see README\n\n" + RED + "\n# trailing\n")
        self.assertEqual(run(None, stop(cwd=str(self.repo)))[1]["decision"], "block")

    def test_an_empty_file_opts_the_repo_out_even_with_a_default(self):
        self.declare("# nothing here\n")
        rc, out, err = run(RED, stop(cwd=str(self.repo)))
        self.assertEqual((rc, out), (0, None))
        self.assertIn("declares no check", err)

    def test_the_default_applies_where_nothing_is_declared(self):
        out = run(RED, stop(cwd=str(self.repo)))[1]
        self.assertEqual(out["decision"], "block")
        self.assertIn("the install default", out["reason"])


class FailOpen(unittest.TestCase):

    def test_bad_input_never_blocks(self):
        out, err = io.StringIO(), io.StringIO()
        rc = hook.main([RED], io.StringIO("not json"), out, err, environ={})
        self.assertEqual((rc, out.getvalue()), (1, ""))
        self.assertIn("not blocking", err.getvalue())

    def test_a_check_that_hangs_never_blocks(self):
        cmd = f'"{PY}" -c "import time; time.sleep(10)"'
        rc, out, err = run(cmd, stop(), env={"LOCAL_AGENTS_VERIFY_TIMEOUT": "1"})
        self.assertEqual((rc, out), (1, None))
        self.assertIn("did not finish in 1 s", err)

    def test_a_command_that_cannot_start_blocks_with_the_shell_error(self):
        # Through the shell a missing command is exit 127: that is the check
        # failing, so it blocks with "command not found" — the user sees the
        # install mistake in the agent's reply, not a silent pass.
        out = run("definitely-not-a-command-xyz", stop())[1]
        self.assertEqual(out["decision"], "block")
        self.assertIn("(exit 127)", out["reason"])


class AsClaudeRunsIt(unittest.TestCase):

    def test_end_to_end_through_the_shell(self):
        event = json.dumps(stop(cwd=str(Path(__file__).parent)))
        proc = subprocess.run([PY, str(SCRIPT), RED], input=event,
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["decision"], "block")
        proc = subprocess.run([PY, str(SCRIPT), GREEN], input=event,
                              capture_output=True, text=True, timeout=60)
        self.assertEqual((proc.returncode, proc.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
