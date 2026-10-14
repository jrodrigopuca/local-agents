"""Behaviour of update.py against a fake remote: a local bare repo, a throwaway
HOME, no network. Standard library only, like the script it tests:

    python3 -m unittest discover -s tests

It never runs against the real catalog's clone — a test that pulls into the
developer's working tree is an accident waiting to happen. The fake remote is
seeded from the catalog's HEAD, so the installs it makes are real ones.

Every test runs THIS checkout's update.py (the code under test), which finds
the managed clone through the stamps the bootstrap install wrote. Each test
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

    def sh(self, *cmd, cwd=None):
        return subprocess.run(list(cmd), capture_output=True, text=True, env=self.env,
                              cwd=cwd, stdin=subprocess.DEVNULL, timeout=300)

    def upd(self, *args, cwd=None):
        return self.sh(sys.executable, str(UPDATER), *args, cwd=str(cwd or self.tmp))

    def head(self, repo):
        return self.sh("git", "-C", str(repo), "rev-parse", "HEAD").stdout.strip()

    def bootstrap(self):
        boot = self.upd("bootstrap", "--all", "--tool", "claude", "--on-conflict", "overwrite")
        self.assertEqual(boot.returncode, 0, boot.stderr or boot.stdout)
        self.assertTrue(self.stamp.is_file(), "bootstrap wrote no install stamp")

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

    # -- bootstrap -------------------------------------------------------- #

    def test_bootstrap_clones_partially_and_stamps_the_managed_clone(self):
        self.bootstrap()
        stamped = json.loads(self.stamp.read_text())["catalog_path"]
        self.assertEqual(Path(stamped).resolve(), self.managed.resolve())
        promisor = self.sh("git", "-C", str(self.managed), "config", "remote.origin.promisor")
        self.assertEqual(promisor.stdout.strip(), "true", "not cloned with --filter=blob:none")

    def test_bootstrap_refuses_a_folder_that_holds_something_else(self):
        self.managed.mkdir(parents=True)
        (self.managed / "notes.txt").write_text("mine\n")
        self.assertRefused(self.upd("bootstrap"), "not empty")

    def test_bootstrap_refuses_an_interrupted_clone(self):
        # What a Ctrl-C mid-clone used to leave: a .git with no commit.
        self.sh("git", "init", "--quiet", str(self.managed))
        self.assertRefused(self.upd("bootstrap"), "incomplete clone")

    # -- check ------------------------------------------------------------ #

    def test_check_on_a_fresh_install_says_up_to_date(self):
        self.bootstrap()
        chk = self.upd("check")
        self.assertEqual(chk.returncode, 0, chk.stderr)
        self.assertIn("installs claude: up to date", chk.stdout)

    def test_check_names_the_commits_and_the_skill_and_writes_nothing(self):
        self.bootstrap()
        self.upstream_commits("line one", "line two")
        head, skill = self.head(self.managed), self.installed.read_text(encoding="utf-8")
        chk = self.upd("check")
        self.assertEqual(chk.returncode, 0, chk.stderr)
        self.assertIn("2 commits behind", chk.stdout)
        self.assertIn("skill lh-verification", chk.stdout)
        self.assertEqual(self.head(self.managed), head, "check moved the clone")
        self.assertEqual(self.installed.read_text(encoding="utf-8"), skill, "check changed an install")

    def test_installs_from_two_clones_are_refused(self):
        # Only the user knows which clone is right.
        self.bootstrap()
        other = self.home / ".kiro" / ".local-agents.json"
        other.parent.mkdir(parents=True)
        other.write_text(json.dumps({"catalog_commit": self.head(self.managed),
                                     "catalog_path": str(self.tmp / "another-clone")}))
        self.assertRefused(self.upd("check"), "different clones")

    def test_a_deleted_remote_branch_is_refused_not_a_traceback(self):
        # A bare repo will not delete its current branch, so the clone is
        # pointed at one that never existed — the state a pruning fetch leaves
        # behind once a branch is deleted upstream.
        self.bootstrap()
        self.sh("git", "-C", str(self.managed), "config", "branch.main.merge", "refs/heads/gone")
        self.assertRefused(self.upd("check"), "no longer has")

    def test_an_unreachable_remote_exits_3(self):
        self.bootstrap()
        self.sh("git", "-C", str(self.managed), "remote", "set-url", "origin",
                str(self.tmp / "nowhere.git"))
        self.assertEqual(self.upd("check").returncode, 3)

    # -- update ----------------------------------------------------------- #

    def test_update_from_home_fast_forwards_and_refreshes(self):
        # From $HOME, where npx usually runs: the global install must not be
        # mistaken for a project install of the home directory.
        self.bootstrap()
        self.upstream_commits("line one", "line two")
        run = self.upd("update", cwd=self.home)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(self.head(self.managed), self.head(self.work))
        self.assertIn("line two", self.installed.read_text(encoding="utf-8"))
        self.assertEqual(json.loads(self.stamp.read_text())["catalog_commit"], self.head(self.work))
        self.assertNotIn("project install", run.stdout)
        self.assertLess(run.stdout.find("catalog "), run.stdout.find("refresh "),
                        "the report and install.py's output are out of order when piped")

    def test_update_refuses_a_tracked_change_and_names_it(self):
        self.bootstrap()
        self.upstream_commits("line one")
        head = self.head(self.managed)
        with open(self.managed / "README.md", "a", encoding="utf-8") as fh:
            fh.write("local edit\n")
        self.assertRefused(self.upd("update"), "(README.md)")
        self.assertEqual(self.head(self.managed), head)

    def test_update_refuses_an_untracked_file_that_would_be_installed(self):
        self.bootstrap()
        self.upstream_commits("line one")
        head = self.head(self.managed)
        new_skill = self.managed / "generalist" / "skills" / "zz-untracked" / "SKILL.md"
        new_skill.parent.mkdir(parents=True)
        new_skill.write_text("x\n")
        self.assertRefused(self.upd("update"), "uncommitted changes")
        self.assertEqual(self.head(self.managed), head)

    def test_update_refuses_local_commits(self):
        self.bootstrap()
        self.upstream_commits("line one")
        self.sh("git", "-C", str(self.managed), "commit", "--quiet", "--allow-empty", "-m", "local")
        local = self.head(self.managed)
        self.assertRefused(self.upd("update"), "not on")
        self.assertEqual(self.head(self.managed), local)


if __name__ == "__main__":
    unittest.main()
