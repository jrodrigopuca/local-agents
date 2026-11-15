"""default_agent.py: a catalog agent as the one a session starts with, and the
way back. Every test runs against a throwaway home — never the real host
settings. Standard library only:

    python3 -m unittest discover -s tests
"""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import default_agent as da  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        roots = {"claude": self.home / ".claude", "opencode": self.home / ".config/opencode",
                 "kiro": self.home / ".kiro"}
        tools = {k: SimpleNamespace(key=k, label=k, config_root=r, agents_dir=r / "agents")
                 for k, r in roots.items()}
        patch = mock.patch.object(da, "TOOLS_BY_KEY", tools)
        patch.start()
        self.addCleanup(patch.stop)
        for k, r in roots.items():
            (r / "agents").mkdir(parents=True)
        (roots["claude"] / "agents/generalist.md").write_text("---\nname: generalist\n---\nbody\n")
        (roots["opencode"] / "agents/generalist.md").write_text("---\ndescription: x\nmode: primary\n---\nbody\n")
        (roots["opencode"] / "agents/qa.md").write_text("---\ndescription: x\nmode: subagent\n---\nbody\n")
        (roots["kiro"] / "agents/generalist.json").write_text("{}")
        self.claude, self.opencode, self.kiro = (da.HOSTS[k] for k in ("claude", "opencode", "kiro"))

    def settings(self, host):
        return json.loads(host.path.read_text())

    def run_main(self, *args):
        out = io.StringIO()
        with redirect_stdout(out):
            code = da.main(list(args))
        return code, out.getvalue()


class Set(Base):
    def test_each_host_gets_its_own_setting(self):
        for host, key in ((self.claude, "agent"), (self.opencode, "default_agent"), (self.kiro, "chat.defaultAgent")):
            da.set_default(host, "generalist")
            self.assertEqual(self.settings(host)[key], "generalist")

    def test_the_rest_of_the_settings_file_is_kept(self):
        self.claude.path.write_text('{\n    "theme": "dark",\n    "model": "opus"\n}\n')
        da.set_default(self.claude, "generalist")
        self.assertEqual(self.settings(self.claude), {"theme": "dark", "model": "opus", "agent": "generalist"})
        self.assertIn('\n    "theme"', self.claude.path.read_text())      # its own indent

    def test_an_agent_that_is_not_installed_is_refused(self):
        with self.assertRaises(da.Refused):
            da.set_default(self.claude, "nobody")
        self.assertFalse(self.claude.path.exists())

    def test_opencode_refuses_an_agent_that_is_not_primary(self):
        # opencode falls back to `build` without a word
        with self.assertRaises(da.Refused):
            da.set_default(self.opencode, "qa")

    def test_a_settings_file_with_comments_is_refused_not_rewritten(self):
        text = '{\n  // mine\n  "theme": "dark"\n}\n'
        self.opencode.path.write_text(text)
        with self.assertRaises(da.Refused):
            da.set_default(self.opencode, "generalist")
        self.assertEqual(self.opencode.path.read_text(), text)
        self.assertFalse(self.opencode.state.exists())

    def test_a_host_that_is_not_there_is_skipped(self):
        import shutil
        shutil.rmtree(self.kiro.tool.config_root)
        self.assertIn("skipped", da.set_default(self.kiro, "generalist"))
        self.assertFalse(self.kiro.tool.config_root.exists())

    def test_dry_run_changes_nothing(self):
        self.claude.path.write_text('{"theme": "dark"}')
        self.assertIn("would set", da.set_default(self.claude, "generalist", dry_run=True))
        self.assertEqual(self.claude.path.read_text(), '{"theme": "dark"}')
        self.assertFalse(self.claude.state.exists())


class Restore(Base):
    def test_a_setting_that_did_not_exist_is_removed(self):
        self.claude.path.write_text('{"theme": "dark"}')
        da.set_default(self.claude, "generalist")
        da.restore(self.claude)
        self.assertEqual(self.settings(self.claude), {"theme": "dark"})
        self.assertFalse(self.claude.state.exists())

    def test_the_agent_the_user_had_comes_back(self):
        (self.claude.tool.agents_dir / "architect.md").write_text("x")
        self.claude.path.write_text('{"agent": "architect"}')
        da.set_default(self.claude, "generalist")
        da.restore(self.claude)
        self.assertEqual(self.settings(self.claude), {"agent": "architect"})

    def test_setting_twice_does_not_forget_what_was_there_first(self):
        (self.claude.tool.agents_dir / "architect.md").write_text("x")
        (self.claude.tool.agents_dir / "stark.md").write_text("x")
        self.claude.path.write_text('{"agent": "architect"}')
        da.set_default(self.claude, "generalist")
        da.set_default(self.claude, "stark")
        da.restore(self.claude)
        self.assertEqual(self.settings(self.claude), {"agent": "architect"})

    def test_a_value_the_user_changed_afterwards_is_left_alone(self):
        da.set_default(self.claude, "generalist")
        self.claude.path.write_text('{"agent": "architect"}')
        self.assertIn("left alone", da.restore(self.claude))
        self.assertEqual(self.settings(self.claude), {"agent": "architect"})
        self.assertFalse(self.claude.state.exists())

    def test_a_file_made_only_for_the_setting_is_removed(self):
        self.assertFalse(self.kiro.path.exists())
        da.set_default(self.kiro, "generalist")
        da.restore(self.kiro)
        self.assertFalse(self.kiro.path.exists())

    def test_a_file_that_was_there_stays_even_if_empty(self):
        self.kiro.path.parent.mkdir(parents=True)
        self.kiro.path.write_text("{}")
        da.set_default(self.kiro, "generalist")
        da.restore(self.kiro)
        self.assertEqual(self.settings(self.kiro), {})

    def test_nothing_recorded_nothing_touched(self):
        self.claude.path.write_text('{"agent": "generalist"}')      # the user's own choice
        self.assertIn("nothing recorded", da.restore(self.claude))
        self.assertEqual(self.settings(self.claude), {"agent": "generalist"})

    def test_dry_run_changes_nothing(self):
        da.set_default(self.claude, "generalist")
        self.assertIn("would put", da.restore(self.claude, dry_run=True))
        self.assertEqual(self.settings(self.claude), {"agent": "generalist"})
        self.assertTrue(self.claude.state.exists())


class Cli(Base):
    def test_status_says_who_set_it(self):
        da.set_default(self.claude, "generalist")
        self.kiro.path.parent.mkdir(parents=True)
        self.kiro.path.write_text('{"chat.defaultAgent": "generalist"}')
        _, out = self.run_main("--status")
        lines = {l.split()[0]: l for l in out.splitlines()}
        self.assertIn("set by this script", lines["claude"])
        self.assertNotIn("set by this script", lines["kiro"])
        self.assertIn("own default assistant", lines["opencode"])
        self.assertIn("Codex", out)

    def test_a_refusal_in_one_host_does_not_stop_the_others_and_exits_1(self):
        self.opencode.path.write_text("{ // x\n}")
        code, out = self.run_main("--set", "generalist")
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", out)
        self.assertEqual(self.settings(self.claude)["agent"], "generalist")
        self.assertEqual(self.settings(self.kiro)["chat.defaultAgent"], "generalist")

    def test_only_the_tools_named_are_touched(self):
        self.run_main("--set", "generalist", "--tool", "kiro")
        self.assertFalse(self.claude.path.exists())
        self.assertTrue(self.kiro.path.exists())

    def test_running_it_leaves_no_bytecode_in_the_catalog(self):
        # a __pycache__ there reads as a dirty tree in every install stamp
        import os, shutil, subprocess
        copy = self.home / "catalog"
        copy.mkdir()
        for f in ("default_agent.py", "install.py"):
            shutil.copy(ROOT / f, copy / f)
        env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
        env.update(HOME=str(self.home), USERPROFILE=str(self.home))
        env.pop("PYTHONPYCACHEPREFIX", None)
        run = subprocess.run([sys.executable, str(copy / "default_agent.py"), "--status"],
                             capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(sorted(p.name for p in copy.iterdir()), ["default_agent.py", "install.py"])

    def test_codex_and_antigravity_are_named_as_unsupported(self):
        with self.assertRaises(SystemExit), redirect_stdout(io.StringIO()), mock.patch("sys.stderr", io.StringIO()) as err:
            da.main(["--set", "generalist", "--tool", "codex"])
        self.assertIn("no default-agent setting", err.getvalue())


if __name__ == "__main__":
    unittest.main()
