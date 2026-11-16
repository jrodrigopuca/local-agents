"""Behaviour of update.py against a fake remote: a local bare repo, a throwaway
HOME, no network. Standard library only, like the script it tests:

    python3 -m unittest discover -s tests

It never runs against the real catalog's clone — a test that pulls into the
developer's working tree is an accident waiting to happen. The fake remote is
seeded from the catalog's HEAD, so the installs it makes are real ones.

Every test runs THIS checkout's update.py (the code under test), which finds
the managed clone through the records the first install wrote. Each test
gets its own HOME, remote and clone, so one failure never cascades.
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

CATALOG = Path(__file__).resolve().parents[1]
UPDATER = CATALOG / "update.py"
SKILL = Path("generalist/skills/lh-verification/SKILL.md")


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_CONFIG_DIR", "CODEX_HOME", "XDG_DATA_HOME")
           and not k.startswith("GIT_")}
    # The user's git config may sign commits or rewrite URLs; none of it
    # belongs in a test. XDG_CONFIG_HOME too: git before 2.32 ignores
    # GIT_CONFIG_GLOBAL and still reads $XDG_CONFIG_HOME/git/config.
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t", **extra)
    return env


class UpdateTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Seeded from the WORKING TREE, not from HEAD: the code under test may
        # be uncommitted, and a seed from HEAD would test the last commit
        # instead (a rename not yet committed broke these tests exactly so).
        cls._seed_dir = tempfile.TemporaryDirectory()
        root = Path(cls._seed_dir.name)
        cls.seed, work = root / "seed.git", root / "tree"
        shutil.copytree(CATALOG, work, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        env = clean_env(XDG_CONFIG_HOME=cls._seed_dir.name)
        for cmd in (["git", "init", "--quiet", "--bare", str(cls.seed)],
                    ["git", "--git-dir", str(cls.seed), "symbolic-ref", "HEAD", "refs/heads/main"],
                    ["git", "-C", str(work), "init", "--quiet"],
                    ["git", "-C", str(work), "add", "-A"],
                    ["git", "-C", str(work), "commit", "--quiet", "-m", "working tree"],
                    ["git", "-C", str(work), "push", "--quiet", str(cls.seed),
                     "HEAD:refs/heads/main"]):
            proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
            if proc.returncode != 0:
                raise RuntimeError(f"could not seed the fake remote: {proc.stderr}")

    @classmethod
    def tearDownClass(cls):
        cls._seed_dir.cleanup()

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.bare = self.tmp / "remote.git"
        self.work = self.tmp / "work"
        self.managed = self.tmp / "data" / "local-agents"
        self.stamp = self.home / ".claude" / ".local-agents.json"
        self.installed = self.home / ".claude" / "skills" / "lh-verification" / "SKILL.md"
        self.env = clean_env(HOME=str(self.home), USERPROFILE=str(self.home),
                             XDG_DATA_HOME=str(self.tmp / "data"),
                             XDG_CONFIG_HOME=str(self.tmp / "config"),
                             LOCAL_AGENTS_REPO=str(self.bare))
        self.sh("git", "clone", "--quiet", "--bare", str(self.seed), str(self.bare))

    # -- helpers ---------------------------------------------------------- #

    def sh(self, *cmd, cwd=None, env=None):
        return subprocess.run(list(cmd), capture_output=True, text=True,
                              env=dict(self.env, **(env or {})),
                              cwd=cwd, stdin=subprocess.DEVNULL, timeout=300)

    def upd(self, *args, cwd=None, env=None):
        return self.sh(sys.executable, str(UPDATER), *args, cwd=str(cwd or self.tmp), env=env)

    def head(self, repo):
        return self.sh("git", "-C", str(repo), "rev-parse", "HEAD").stdout.strip()

    def install(self):
        boot = self.upd("install", "--all", "--tool", "claude", "--on-conflict", "overwrite")
        self.assertEqual(boot.returncode, 0, boot.stderr or boot.stdout)
        self.assertTrue(self.stamp.is_file(), "install wrote no install record")

    def upstream_commits(self, *messages):
        """New commits on the fake remote, each touching one skill."""
        if not self.work.exists():
            self.sh("git", "clone", "--quiet", str(self.bare), str(self.work))
        for msg in messages:
            with open(self.work / SKILL, "a", encoding="utf-8") as fh:
                fh.write(f"\n{msg}\n")
            self.sh("git", "-C", str(self.work), "commit", "--quiet", "-am", msg)
        push = self.sh("git", "-C", str(self.work), "push", "--quiet", "origin", "main")
        self.assertEqual(push.returncode, 0, push.stderr)

    def assertRefused(self, proc, says):
        self.assertEqual(proc.returncode, 2, proc.stderr or proc.stdout)
        self.assertIn(says, proc.stderr)

    # -- the contract with launchers -------------------------------------- #

    def test_launcher_api_is_1(self):
        self.assertEqual(self.upd("--launcher-api").stdout.strip(), "1")

    def test_usage_error_is_1_not_refused(self):
        self.assertEqual(self.upd("bogus").returncode, 1)

    def test_relative_xdg_data_home_is_ignored(self):
        # The XDG spec ignores it, and the launcher computes the same path.
        spec = importlib.util.spec_from_file_location("update_under_test", UPDATER)
        update = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(update)
        with mock.patch.dict(os.environ, {"XDG_DATA_HOME": "relative/data"}):
            self.assertEqual(update.managed_dir(),
                             Path.home() / ".local" / "share" / "local-agents")

    def test_install_hint_names_the_command_the_reader_can_type(self):
        # Behind a launcher install.py is not on the PATH: the way in is
        # `install`. A clone of one's own has install.py at hand.
        spec = importlib.util.spec_from_file_location("update_under_test", UPDATER)
        update = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(update)
        # Whoever is in front says how it was typed; the hint starts with that.
        hint = lambda: update.typed("install --all --tool <tool>")
        with mock.patch.dict(os.environ, {update.FRONT_ENV: "npx github:x/local-hero"}):
            self.assertEqual("npx github:x/local-hero install --all --tool <tool>", hint())
        # A launcher that did not say its name, running the managed clone: the verb alone.
        with mock.patch.dict(os.environ), mock.patch.object(update, "HERE", update.managed_dir().resolve()):
            os.environ.pop(update.FRONT_ENV, None)
            self.assertEqual("`install --all --tool <tool>`", hint())
        # A clone of one's own, run directly: this script, from where the person is.
        with mock.patch.dict(os.environ), mock.patch.object(update, "HERE", Path.cwd().resolve()):
            os.environ.pop(update.FRONT_ENV, None)
            self.assertEqual("./update.py install --all --tool <tool>", hint())

    def test_the_installer_it_runs_suggests_commands_through_update_py(self):
        # install.py's own error, reached through `install`: the way out it
        # offers has to go back through the door the person used.
        self.install()
        run = self.upd("install", "--all")
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertRegex(run.stderr, r"Try:\s+\S*update\.py install --all --tool claude")
        self.assertNotIn("install.py", run.stderr)
        named = self.upd("install", "--all", env={"LOCAL_AGENTS_FRONT": "local-hero"})
        self.assertIn("Try: local-hero install --all --tool claude", named.stderr)

    def test_second_install_says_it_installs_not_that_it_refuses(self):
        self.install()
        again = self.upd("install", "--all", "--tool", "claude", "--on-conflict", "overwrite")
        self.assertEqual(again.returncode, 0, again.stderr or again.stdout)
        # It goes straight to the install: the clone being there already is not news.
        self.assertTrue(again.stdout.startswith("Installing the whole catalog into claude"), again.stdout)
        self.assertNotIn("refused", again.stdout + again.stderr)
        self.assertNotIn("lone", again.stdout)          # no "cloning", no "already cloned"

    def test_install_without_arguments_opens_the_menu_only_on_a_terminal(self):
        import pty
        # No terminal (this run's pipes): the commands to copy, not a path to install.py.
        plain = self.upd("install")
        self.assertEqual(plain.returncode, 0, plain.stderr)
        self.assertRegex(plain.stdout, r"Next: \S*update\.py list\n")
        self.assertIn("install --all --tool <tool>", plain.stdout)
        self.assertNotIn("install.py", plain.stdout)
        # ... and through a launcher that says its name, the launcher's command
        named = self.upd("install", env={"LOCAL_AGENTS_FRONT": "npx github:x/local-hero"})
        self.assertIn("Next: npx github:x/local-hero list", named.stdout)
        # A terminal: install.py's own menu, which asks before touching anything.
        pid, fd = pty.fork()
        if pid == 0:
            os.environ.update(self.env)
            os.execv(sys.executable, [sys.executable, str(UPDATER), "install"])
        out = b""
        try:
            while b"quit" not in out:
                chunk = os.read(fd, 4096)
                if not chunk:
                    break
                out += chunk
            os.write(fd, b"q\n")
        finally:
            os.close(fd)
            os.waitpid(pid, 0)
        self.assertIn(b"quit", out, out.decode(errors="replace")[-500:])

    # -- install: the first run clones ------------------------------------ #

    def test_install_clones_partially_and_stamps_the_managed_clone(self):
        self.install()
        stamped = json.loads(self.stamp.read_text())["catalog_path"]
        self.assertEqual(Path(stamped).resolve(), self.managed.resolve())
        promisor = self.sh("git", "-C", str(self.managed), "config", "remote.origin.promisor")
        self.assertEqual(promisor.stdout.strip(), "true", "not cloned with --filter=blob:none")

    def test_install_refuses_a_folder_that_holds_something_else(self):
        self.managed.mkdir(parents=True)
        (self.managed / "notes.txt").write_text("mine\n")
        self.assertRefused(self.upd("install"), "not empty")

    def test_install_refuses_an_interrupted_clone(self):
        # What a Ctrl-C mid-clone used to leave: a .git with no commit.
        self.sh("git", "init", "--quiet", str(self.managed))
        self.assertRefused(self.upd("install"), "incomplete clone")

    # -- check ------------------------------------------------------------ #

    def test_check_on_a_fresh_install_says_up_to_date(self):
        self.install()
        chk = self.upd("check")
        self.assertEqual(chk.returncode, 0, chk.stderr)
        self.assertEqual(chk.stdout.splitlines()[0], "Everything installed is up to date.")
        self.assertRegex(chk.stdout, r"(?m)^  claude +up to date +15 agents, 51 skills$")
        self.assertRegex(chk.stdout, r"(?m)^Catalog [0-9a-f]{7}, same as origin/main\.$")
        self.assertNotIn("Next:", chk.stdout)

    def test_check_names_the_commits_and_the_skill_and_writes_nothing(self):
        self.install()
        self.upstream_commits("line one", "line two")
        head, skill = self.head(self.managed), self.installed.read_text(encoding="utf-8")
        chk = self.upd("check")
        self.assertEqual(chk.returncode, 0, chk.stderr)
        self.assertEqual(chk.stdout.splitlines()[0], "An update is available.")
        self.assertIn("your catalog is 2 commits behind", chk.stdout)
        self.assertRegex(chk.stdout, r"(?m)^  changes +skill lh-verification$")
        self.assertRegex(chk.stdout, r"(?m)^  claude +update available$")
        self.assertRegex(chk.stdout, r"(?m)^Next: \S*update\.py update$")
        self.assertEqual(self.head(self.managed), head, "check moved the clone")
        self.assertEqual(self.installed.read_text(encoding="utf-8"), skill, "check changed an install")

    def test_installs_from_two_clones_are_refused(self):
        # Only the user knows which clone is right.
        self.install()
        other = self.home / ".kiro" / ".local-agents.json"
        other.parent.mkdir(parents=True)
        other.write_text(json.dumps({"catalog_commit": self.head(self.managed),
                                     "catalog_path": str(self.tmp / "another-clone")}))
        self.assertRefused(self.upd("check"), "different clones")

    def test_a_deleted_remote_branch_is_refused_not_a_traceback(self):
        # A bare repo will not delete its current branch, so the clone is
        # pointed at one that never existed — the state a pruning fetch leaves
        # behind once a branch is deleted upstream.
        self.install()
        self.sh("git", "-C", str(self.managed), "config", "branch.main.merge", "refs/heads/gone")
        self.assertRefused(self.upd("check"), "no longer has")

    def test_an_unreachable_remote_exits_3(self):
        self.install()
        self.sh("git", "-C", str(self.managed), "remote", "set-url", "origin",
                str(self.tmp / "nowhere.git"))
        self.assertEqual(self.upd("check").returncode, 3)

    # -- update ----------------------------------------------------------- #

    def test_update_from_home_fast_forwards_and_refreshes(self):
        # From $HOME, where npx usually runs: the global install must not be
        # mistaken for a project install of the home directory.
        self.install()
        self.upstream_commits("line one", "line two")
        run = self.upd("update", cwd=self.home)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.head(self.managed), self.head(self.work))
        self.assertIn("line two", self.installed.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(self.stamp.read_text())["catalog_commit"], self.head(self.work))
        self.assertNotIn("project install", run.stdout)
        # One answer, in order when piped: the catalog's part, then the installs'.
        lines = run.stdout.splitlines()
        self.assertRegex(lines[0], r"^Catalog updated: [0-9a-f]{7} -> [0-9a-f]{7} \(2 commits\)$")
        self.assertRegex(run.stdout, r"(?m)^Updating 1 tool from catalog [0-9a-f]{7}$")
        self.assertRegex(run.stdout, r"(?m)^  claude +1 updated, 65 unchanged$")
        self.assertIn("Done: 1 file updated in claude.", run.stdout)
        self.assertNotIn("install.py", run.stdout)

    def test_update_refuses_a_tracked_change_and_names_it(self):
        self.install()
        self.upstream_commits("line one")
        head = self.head(self.managed)
        with open(self.managed / "README.md", "a", encoding="utf-8") as fh:
            fh.write("local edit\n")
        self.assertRefused(self.upd("update"), "(README.md)")
        self.assertEqual(self.head(self.managed), head)

    def test_update_refuses_an_untracked_file_that_would_be_installed(self):
        self.install()
        self.upstream_commits("line one")
        head = self.head(self.managed)
        new_skill = self.managed / "generalist" / "skills" / "zz-untracked" / "SKILL.md"
        new_skill.parent.mkdir(parents=True)
        new_skill.write_text("x\n")
        self.assertRefused(self.upd("update"), "uncommitted changes")
        self.assertEqual(self.head(self.managed), head)

    def test_update_refuses_local_commits(self):
        self.install()
        self.upstream_commits("line one")
        self.sh("git", "-C", str(self.managed), "commit", "--quiet", "--allow-empty", "-m", "local")
        local = self.head(self.managed)
        self.assertRefused(self.upd("update"), "not on")
        self.assertEqual(self.head(self.managed), local)

    # -- one answer, in the words --status uses ---------------------------- #

    def docs_only_commits(self, n):
        if not self.work.exists():
            self.sh("git", "clone", "--quiet", str(self.bare), str(self.work))
        for i in range(n):
            with open(self.work / "README.md", "a", encoding="utf-8") as fh:
                fh.write(f"\nnote {i}\n")
            self.sh("git", "-C", str(self.work), "commit", "--quiet", "-am", f"docs {i}")
        self.sh("git", "-C", str(self.work), "push", "--quiet", "origin", "main")

    def assertPlain(self, text):
        for line in text.splitlines():
            if not any(len(word) > 40 for word in line.split()):     # a path is never folded
                self.assertLessEqual(len(line), 80, line)
            self.assertTrue(line.isascii(), line)

    def test_commits_that_change_no_installed_file_are_not_an_update(self):
        self.install()
        self.docs_only_commits(3)
        chk = self.upd("check")
        self.assertEqual(chk.stdout.splitlines()[0], "Everything installed is up to date.")
        self.assertIn("origin/main has 3 newer commits; none changes an installed file.", chk.stdout)
        self.assertNotIn("update available", chk.stdout)
        self.assertNotIn("Next:", chk.stdout)
        self.assertPlain(chk.stdout)
        # bringing them is still allowed, and says the installs had nothing to gain
        run = self.upd("update")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertRegex(run.stdout.splitlines()[0], r"^Catalog updated: .* \(3 commits\)$")
        self.assertIn("Nothing to update.", run.stdout)

    def test_update_with_nothing_to_bring_is_one_line(self):
        self.install()
        run = self.upd("update")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "Everything installed is up to date. Nothing to do.")

    def test_check_with_nothing_installed_says_how_to_install(self):
        self.assertEqual(self.upd("list").returncode, 0)       # the checkout's own scripts are there
        boot = self.upd("install")                           # clones, installs nothing (no terminal)
        self.assertEqual(boot.returncode, 0, boot.stderr)
        chk = self.sh(sys.executable, str(self.managed / "update.py"), "check", cwd=str(self.tmp))
        self.assertEqual(chk.returncode, 0, chk.stderr)
        self.assertEqual(chk.stdout.splitlines()[0], "Nothing from this catalog is installed yet.")
        self.assertIn("Next: `install --all --tool <tool>`", chk.stdout)   # a launcher that gave no name

    def test_the_output_of_check_and_update_is_plain_and_fits(self):
        self.install()
        self.upstream_commits("line one", "line two")
        self.assertPlain(self.upd("check").stdout)
        self.assertPlain(self.upd("update").stdout)

    def test_a_refusal_has_one_form_and_says_nothing_was_changed(self):
        self.install()
        self.upstream_commits("line one")
        with open(self.managed / "README.md", "a", encoding="utf-8") as fh:
            fh.write("local edit\n")
        run = self.upd("update")
        self.assertEqual(run.returncode, 2)
        self.assertTrue(run.stderr.startswith("refused: "), run.stderr)
        self.assertEqual(run.stderr.splitlines()[-1], "  Nothing was changed.")
        self.assertEqual(run.stdout, "")
        self.assertIn("Commit or discard them", run.stderr)

    def test_an_unreachable_remote_is_an_error_with_its_own_code(self):
        self.install()
        self.sh("git", "-C", str(self.managed), "remote", "set-url", "origin",
                str(self.tmp / "nowhere.git"))
        run = self.upd("check")
        self.assertEqual(run.returncode, 3)
        self.assertTrue(run.stderr.startswith("error: could not reach the remote"), run.stderr)

    # -- the verbs --------------------------------------------------------- #

    def test_install_installs(self):
        run = self.upd("install", "--all", "--tool", "claude")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(self.stamp.is_file())
        self.assertIn("Done: 66 files installed in claude", run.stdout)

    def test_status_is_this_machine_with_no_network(self):
        self.install()
        self.sh("git", "-C", str(self.managed), "remote", "set-url", "origin",
                str(self.tmp / "nowhere.git"))                    # check would exit 3 here
        run = self.upd("status")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.splitlines()[0], "Everything installed is up to date.")
        self.assertRegex(run.stdout, r"Details: \S*update\.py status --verbose")
        verbose = self.upd("status", "--verbose")
        self.assertIn("claude (Claude Code)", verbose.stdout)

    def test_list_names_the_tools(self):
        run = self.upd("list")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertRegex(run.stdout, r"(?m)^  claude +(available|not detected) +agents and skills$")

    def test_uninstall_takes_the_install_away_and_its_flags_go_through(self):
        self.install()
        dry = self.upd("uninstall", "--dry-run")
        self.assertIn("would remove 66", dry.stdout)
        self.assertTrue(self.stamp.is_file())
        run = self.upd("uninstall", "--tool", "claude")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Done: 66 files removed from claude.", run.stdout)
        self.assertFalse(self.stamp.exists())

    def test_uninstalling_through_a_launcher_names_the_copy_it_left(self):
        # Run from the managed clone, as a launcher does: the clone is the one
        # thing that person never saw, and the last thing left on the machine.
        self.install()
        mine = lambda *a: self.sh(sys.executable, str(self.managed / "update.py"), *a, cwd=str(self.tmp))
        self.assertNotIn("remains at", mine("uninstall", "--dry-run").stdout)
        run = mine("uninstall")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(f"The catalog copy remains at {self.managed.resolve()}\n"
                      f"Delete that folder to remove it completely.", run.stdout)

    def test_default_is_the_agent_a_session_starts_with(self):
        self.install()
        shown = self.upd("default")
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertIn("starts with the host's own default assistant", shown.stdout)
        self.assertRegex(shown.stdout, r"Change it: \S*update\.py default --set <agent>")
        run = self.upd("default", "--set", "generalist", "--tool", "claude")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads((self.home / ".claude" / "settings.json").read_text())["agent"],
                         "generalist")
        self.assertRegex(run.stdout, r"Undo: \S*update\.py default --restore")

    def test_a_verb_s_own_error_comes_back_through_this_door(self):
        run = self.upd("uninstall")
        self.assertEqual(run.returncode, 1)
        self.assertIn("error: nothing to uninstall", run.stderr)
        self.assertRegex(run.stderr, r"Try:\s+\S*update\.py status")

    def test_help_names_every_verb(self):
        out = self.upd("--help").stdout
        for verb in ("check", "update", "install", "status", "list", "uninstall", "default"):
            self.assertRegex(out, rf"(?m)^\s+{verb}\s")

    def test_the_old_word_for_install_still_runs_and_is_said_nowhere(self):
        # Scripts written against `bootstrap` keep working; nobody is told to type it.
        run = self.upd("bootstrap", "--all", "--tool", "claude")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(self.stamp.is_file())
        said = (run.stdout + self.upd("--help").stdout + self.upd("check").stdout
                + self.upd("install", "--all").stderr + self.upd("uninstall", "--dry-run").stdout
                + self.upd("status").stdout + self.upd("bogus").stderr)
        self.assertNotIn("bootstrap", said)

    def test_help_is_headed_by_the_command_that_was_typed(self):
        # argparse folds the usage line to the terminal's width, and a long
        # path (CI checks out under /home/runner/work/...) moves the fold: read
        # it with the folds taken out.
        def usage(*args, env=None):
            return " ".join(self.upd(*args, env=env).stdout.split())
        named = {"LOCAL_AGENTS_FRONT": "npx github:x/local-hero"}
        self.assertTrue(usage("--help", env=named).startswith("usage: npx github:x/local-hero "))
        self.install()
        self.assertTrue(usage("install", "--help", env=named).startswith(
            "usage: npx github:x/local-hero install "))
        self.assertTrue(usage("default", "--help", env=named).startswith(
            "usage: npx github:x/local-hero default "))
        # run directly, a script is headed by its own name
        self.assertRegex(usage("--help"), r"^usage: \S*update\.py ")

    def test_a_mistyped_verb_is_an_error_with_the_way_to_the_help(self):
        run = self.upd("bogus")
        self.assertEqual(run.returncode, 1)
        self.assertTrue(run.stderr.startswith("error: "), run.stderr)
        self.assertRegex(run.stderr, r"Try: \S*update\.py --help")


if __name__ == "__main__":
    unittest.main()
