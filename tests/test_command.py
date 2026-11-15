"""The command a message suggests has to be one the person can type.
Standard library only, no network:

    python3 -m unittest discover -s tests

Someone who came in through a launcher never sees install.py; someone in their
own clone has it at hand; someone who ran it from another folder needs its
path. One function decides, from one environment variable.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import install  # noqa: E402
import update   # noqa: E402

FRONT = "npx github:x/local-hero"


class Command(unittest.TestCase):
    def at(self, cwd, front=None):
        env = {} if front is None else {install.FRONT_ENV: front}
        stack = [mock.patch.object(Path, "cwd", return_value=Path(cwd))]
        patcher = mock.patch.dict(os.environ, env)
        patcher.start()
        self.addCleanup(patcher.stop)
        if front is None:
            os.environ.pop(install.FRONT_ENV, None)
        for p in stack:
            p.start()
            self.addCleanup(p.stop)

    def test_inside_the_catalog_it_is_the_script_as_typed_there(self):
        self.at(ROOT)
        self.assertEqual(install.command("refresh"), "./install.py --refresh")
        self.assertEqual(install.command("install", "--all", "--tool claude"),
                         "./install.py --all --tool claude")
        self.assertEqual(install.command("menu"), "./install.py")
        self.assertEqual(install.command("default", "--restore"), "./default_agent.py --restore")

    def test_from_another_folder_it_is_the_script_s_path(self):
        self.at("/somewhere/else")
        cmd = install.command("status", "--verbose")
        self.assertTrue(cmd.endswith("/install.py --status --verbose"), cmd)
        self.assertFalse(cmd.startswith("./"), cmd)
        run = subprocess.run(cmd.replace("~", str(Path.home()), 1).split()[:1] + ["--list"],
                             capture_output=True, text=True, cwd="/")
        self.assertEqual(run.returncode, 0, run.stderr)

    def test_behind_a_launcher_it_is_the_launcher_s_verbs(self):
        self.at(ROOT, FRONT)
        self.assertEqual(install.command("refresh"), f"{FRONT} update")
        self.assertEqual(install.command("install", "--all", "--tool kiro"),
                         f"{FRONT} install --all --tool kiro")
        self.assertEqual(install.command("status"), f"{FRONT} status")
        self.assertEqual(install.command("uninstall", "--tool kiro"), f"{FRONT} uninstall --tool kiro")
        self.assertEqual(install.command("list"), f"{FRONT} list")
        self.assertEqual(install.command("menu"), f"{FRONT} install")
        self.assertEqual(install.command("default", "--restore"), f"{FRONT} default --restore")

    def test_update_takes_no_options_so_a_refresh_with_any_goes_through_install(self):
        self.at(ROOT, FRONT)
        self.assertEqual(install.command("refresh", "--project /repo"),
                         f"{FRONT} install --refresh --project /repo")
        self.assertEqual(install.command("refresh", "--verify-hook"),
                         f"{FRONT} install --refresh --verify-hook")

    def test_a_launcher_that_did_not_say_its_name_gets_the_verb_alone(self):
        self.at(ROOT, "-")
        self.assertEqual(install.command("refresh"), "`update`")
        self.assertEqual(install.command("install", "--all", "--tool claude"),
                         "`install --all --tool claude`")

    def test_empty_arguments_leave_no_double_spaces(self):
        self.at(ROOT)
        self.assertEqual(install.command("uninstall", "", " --project /r "), "./install.py --uninstall --project /r")

    def test_every_verb_it_suggests_is_one_update_py_has_and_runs_the_same_thing(self):
        # A verb is a script with its flags (update.SCRIPT_VERBS), or `install`,
        # which hands what follows to install.py untouched. Whatever command()
        # says behind a front must come out, through that table, as exactly
        # what it says when the script is run directly.
        cases = (("install", ("--all", "--tool claude")), ("status", ("--verbose",)),
                 ("uninstall", ("--tool kiro",)), ("list", ()), ("menu", ()),
                 ("refresh", ("--project /r",)), ("default", ("--restore", "--tool claude")))
        for intent, args in cases:
            with self.subTest(intent=intent):
                self.at(ROOT)
                script, *direct = install.command(intent, *args).split()
                self.at(ROOT, FRONT)
                verb, *rest = install.command(intent, *args)[len(FRONT):].split()
                if verb == "install":
                    runs, passed = "install.py", rest
                else:
                    runs, flags = update.SCRIPT_VERBS[verb]
                    passed = flags + rest
                self.assertEqual(script, f"./{runs}")
                self.assertEqual(passed, direct)


class EndToEnd(unittest.TestCase):
    """Every message that suggests something, through each way in."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name) / "home"
        (self.home / ".claude").mkdir(parents=True)
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("CLAUDE_CONFIG_DIR", "CODEX_HOME", install.FRONT_ENV)
                    and not k.startswith("GIT_")}
        self.env.update(HOME=str(self.home), USERPROFILE=str(self.home), PYTHONDONTWRITEBYTECODE="1")

    def out(self, *args, front=None, cwd=ROOT):
        env = dict(self.env, **({install.FRONT_ENV: front} if front else {}))
        run = subprocess.run([sys.executable, str(ROOT / "install.py"), *args], capture_output=True,
                             text=True, env=env, stdin=subprocess.DEVNULL, timeout=300, cwd=str(cwd))
        return run.stdout + run.stderr

    def messages(self, **how):
        yield self.out("--status", **how)                       # nothing installed: Next
        yield self.out("--all", **how)                          # error: Try
        yield self.out("--refresh", **how)                      # error: Try
        self.out("--all", "--tool", "claude", **how)
        md = self.home / ".claude" / "skills" / "lh-pairing" / "SKILL.md"
        md.write_text(md.read_text() + "\nmine\n")
        yield self.out("--all", "--tool", "claude", **how)      # kept: the way to replace it
        yield self.out("--status", **how)                       # up to date: Details
        yield self.out("--status", "--verbose", **how)          # options: enable
        (self.home / ".claude" / "settings.json").write_text('{"agent": "qa"}')
        yield self.out("--uninstall", **how)                    # still to do

    def test_behind_a_launcher_nothing_points_at_install_py(self):
        seen = "\n".join(self.messages(front=FRONT))
        self.assertNotIn("install.py", seen)
        self.assertNotIn("default_agent.py", seen)
        for must in (f"Next: {FRONT} install --all --tool claude",
                     f"Try: {FRONT} install --all --tool claude",
                     f"{FRONT} install --skill lh-pairing --tool claude --on-conflict overwrite",
                     f"Details: {FRONT} status --verbose",
                     f"enable: {FRONT} install --refresh --shell-write-guard",
                     f"Check any time: {FRONT} status",
                     f"Try: {FRONT} default --restore --tool claude"):
            self.assertIn(must, seen)

    def test_in_one_s_own_clone_it_is_the_scripts(self):
        seen = "\n".join(self.messages())
        for must in ("Next: ./install.py --all --tool claude",
                     "Try: ./install.py --all --tool claude",
                     "  ./install.py --skill lh-pairing --tool claude --on-conflict overwrite",
                     "Details: ./install.py --status --verbose",
                     "enable: ./install.py --refresh --shell-write-guard",
                     "Try: ./default_agent.py --restore --tool claude"):
            self.assertIn(must, seen)

    def test_from_another_folder_no_suggestion_starts_with_dot_slash(self):
        seen = "\n".join(self.messages(cwd=self.home))
        self.assertNotIn("./install.py", seen)
        self.assertNotIn("./default_agent.py", seen)
        self.assertIn("/install.py --all --tool claude", seen)


if __name__ == "__main__":
    unittest.main()
