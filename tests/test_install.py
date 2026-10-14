"""What install.py may touch in a host's dir, decided by identity, not by name
(B-058). Standard library only, no network:

    python3 -m unittest discover -s tests

Every test installs into a throwaway HOME. The ones that need the catalog to
change (an update, a rename) work on a throwaway git copy of it, never on this
checkout.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1]
NAME = "lh-code-review"        # apple-dev's. Unprefixed, 723k installs of a same-name skill existed (B-053)
SKILL = "lh-verification"      # generalist's


def clean_env(**extra):
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_CONFIG_DIR", "CODEX_HOME") and not k.startswith("GIT_")}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
               GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t", **extra)
    return env


def foreign_skill(where: Path, name: str = NAME) -> Path:
    """A third-party skill with one of our names: no id, another author, and
    a file of its own next to SKILL.md (as mattpocock/skills' code-review has)."""
    d = where / name
    (d / "agents").mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: someone else's\n---\nTheirs.\n")
    (d / "agents" / "openai.yaml").write_text("theirs: true\n")
    return d


class InstallTest(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.skills = self.home / ".claude" / "skills"
        self.agents = self.home / ".claude" / "agents"
        self.stamp = self.home / ".claude" / ".local-agents.json"
        self.env = clean_env(HOME=str(self.home), USERPROFILE=str(self.home),
                             XDG_CONFIG_HOME=str(self.tmp / "config"))
        self.catalog = CATALOG

    # -- helpers ---------------------------------------------------------- #

    def install(self, *args):
        return subprocess.run([sys.executable, str(self.catalog / "install.py"), *args],
                              capture_output=True, text=True, env=self.env,
                              stdin=subprocess.DEVNULL, timeout=300)

    def install_all(self, *extra):
        run = self.install("--all", "--tool", "claude", *extra)
        self.assertEqual(run.returncode, 0, run.stderr[-500:])
        return run

    def status(self):
        return self.install("--status").stdout

    def own_copy_of_catalog(self):
        """A git copy of this checkout, working tree included (the code under
        test may be uncommitted), to change without touching the real one."""
        dest = self.tmp / "catalog"
        shutil.copytree(CATALOG, dest, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        for cmd in (["init", "--quiet"], ["add", "-A"], ["commit", "--quiet", "-m", "copy"]):
            subprocess.run(["git", "-C", str(dest), *cmd], env=self.env, check=True,
                           capture_output=True)
        self.catalog = dest
        return dest

    def commit(self, message):
        for cmd in (["add", "-A"], ["commit", "--quiet", "-m", message]):
            subprocess.run(["git", "-C", str(self.catalog), *cmd], env=self.env, check=True,
                           capture_output=True)

    def is_ours(self, d: Path) -> bool:
        return "local-agents-id" in (d / "SKILL.md").read_text()

    # -- running it twice ------------------------------------------------- #

    def test_the_default_command_twice_creates_no_duplicates(self):
        # Before B-058 the second run renamed every file it found, ours too:
        # 48 → 96 skills and 15 → 30 agents.
        self.install_all()
        self.install_all()
        self.assertFalse([p for p in self.skills.iterdir() if p.name.endswith("-2")])
        self.assertFalse([p for p in self.agents.iterdir() if "-2" in p.stem])
        self.assertEqual(len(list(self.skills.iterdir())), 48)
        self.assertEqual(len(list(self.agents.iterdir())), 15)

    def test_the_stamp_records_what_we_own_and_its_hash(self):
        self.install_all()
        stamp = json.loads(self.stamp.read_text())
        self.assertEqual(len(stamp["skills"]), 48)
        self.assertEqual(len(stamp["agents"]), 15)
        self.assertTrue(all(len(r["sha256"]) == 64 for r in stamp["skills"].values()))

    # -- foreign ---------------------------------------------------------- #

    def test_a_foreign_skill_with_our_name_is_left_whole(self):
        self.skills.mkdir(parents=True)
        theirs = foreign_skill(self.skills)
        before = (theirs / "SKILL.md").read_text()
        run = self.install_all()
        # Untouched, both files — B-053 measured our SKILL.md written into it.
        self.assertEqual((theirs / "SKILL.md").read_text(), before)
        self.assertTrue((theirs / "agents" / "openai.yaml").is_file())
        self.assertIn("not ours", run.stdout)
        self.assertFalse((self.skills / f"{NAME}-2").exists())
        self.assertEqual(len(list(self.agents.iterdir())), 15, "the rest must still install")
        self.assertTrue(self.stamp.is_file())
        self.assertIn("not ours", self.status())

    def test_refresh_leaves_a_foreign_skill_alone(self):
        self.install_all()
        shutil.rmtree(self.skills / NAME)
        theirs = foreign_skill(self.skills)   # what `npx skills add` does over ours
        self.install("--refresh")
        self.assertFalse(self.is_ours(theirs))

    def test_explicit_overwrite_replaces_a_foreign_skill(self):
        self.skills.mkdir(parents=True)
        foreign_skill(self.skills)
        self.install_all("--on-conflict", "overwrite")
        self.assertTrue(self.is_ours(self.skills / NAME))

    def test_a_foreign_agent_file_is_left_alone(self):
        self.agents.mkdir(parents=True)
        theirs = self.agents / "architect.md"
        theirs.write_text("---\nname: architect\n---\nSomeone else's architect.\n")
        self.install_all()
        self.assertEqual(theirs.read_text(), "---\nname: architect\n---\nSomeone else's architect.\n")
        self.assertEqual(len(list(self.agents.iterdir())), 15)

    # -- links ------------------------------------------------------------ #

    def test_a_symlink_is_never_followed_and_the_install_completes(self):
        # `npx skills` for two hosts: its copy in ~/.agents/skills, a link here.
        # B-053: install.py died on it (rmtree on a link), 7 of 48 skills, no agents.
        canonical = foreign_skill(self.tmp / "agents-skills")
        self.skills.mkdir(parents=True)
        (self.skills / NAME).symlink_to(canonical)
        before = (canonical / "SKILL.md").read_text()
        self.install_all()
        self.assertTrue((self.skills / NAME).is_symlink())
        self.assertEqual((canonical / "SKILL.md").read_text(), before)
        self.assertEqual(len(list(self.agents.iterdir())), 15)
        self.assertTrue(self.stamp.is_file())
        self.install("--refresh")
        self.assertTrue((self.skills / NAME).is_symlink())
        self.assertIn("links", self.status())

    # -- edited by hand --------------------------------------------------- #

    def test_an_edited_skill_survives_refresh_and_stays_edited(self):
        self.install_all()
        md = self.skills / SKILL / "SKILL.md"
        md.write_text(md.read_text() + "\nmy own note\n")
        for _ in range(2):   # a second refresh must not launder the edit into "intact"
            run = self.install("--refresh")
            self.assertIn("edited by hand", run.stdout)
            self.assertIn("my own note", md.read_text())
        self.assertIn("edited by hand", self.status())
        self.install_all("--on-conflict", "overwrite")
        self.assertNotIn("my own note", md.read_text())

    def test_an_edited_agent_survives_refresh(self):
        self.install_all()
        f = self.agents / "architect.md"
        f.write_text(f.read_text() + "\nmy own rule\n")
        self.install("--refresh")
        self.assertIn("my own rule", f.read_text())

    # -- intact ----------------------------------------------------------- #

    def test_an_intact_skill_is_updated_by_refresh(self):
        catalog = self.own_copy_of_catalog()
        self.install_all()
        src = catalog / "generalist" / "skills" / SKILL / "SKILL.md"
        src.write_text(src.read_text() + "\nnew in the catalog\n")
        self.commit("change a skill")
        self.install("--refresh")
        self.assertIn("new in the catalog", (self.skills / SKILL / "SKILL.md").read_text())

    # -- retired ---------------------------------------------------------- #

    def rename_in_catalog(self, catalog, old_name, new_name):
        old = catalog / "generalist" / "skills" / old_name
        new = old.with_name(new_name)
        old.rename(new)
        md = new / "SKILL.md"
        md.write_text(md.read_text().replace(f"name: {old_name}", f"name: {new_name}", 1))
        self.commit("rename a skill, keeping its id")

    def test_a_renamed_skill_replaces_its_intact_old_copy(self):
        # Ours, replaced, and untouched since we wrote it: refresh removes it,
        # so the host does not list two skills with the same description.
        catalog = self.own_copy_of_catalog()
        self.install_all()
        self.rename_in_catalog(catalog, SKILL, "lh-verification-method")
        run = self.install("--refresh")
        self.assertIn(f"retired → removed {SKILL}", run.stdout)
        self.assertFalse((self.skills / SKILL).exists())
        self.assertTrue(self.is_ours(self.skills / "lh-verification-method"))
        self.assertNotIn("retired", self.status())

    def test_an_edited_old_copy_of_a_renamed_skill_is_kept_and_reported(self):
        catalog = self.own_copy_of_catalog()
        self.install_all()
        md = self.skills / SKILL / "SKILL.md"
        md.write_text(md.read_text() + "\nmy own note\n")
        self.rename_in_catalog(catalog, SKILL, "lh-verification-method")
        self.install("--refresh")
        self.assertIn("my own note", md.read_text())
        status = self.status()
        self.assertIn("retired", status)
        self.assertIn(f"rm -r {self.skills / SKILL}", status)

    def test_a_pre_b058_stamp_removes_no_old_copy(self):
        # No record under the old name: nothing proves the copy is untouched.
        catalog = self.own_copy_of_catalog()
        self.install_all()
        self.make_legacy(self.stamp)
        self.rename_in_catalog(catalog, SKILL, "lh-verification-method")
        self.install("--refresh")
        self.assertTrue((self.skills / SKILL).exists())

    # -- an install from before B-058 ------------------------------------- #

    def test_an_install_from_before_ids_is_taken_as_ours_and_upgraded(self):
        # The real path, as it happened: installed from a commit with no ids,
        # stamped without records; then the catalog gains its ids.
        catalog = self.own_copy_of_catalog()
        mds = sorted(catalog.glob("*/skills/*/SKILL.md"))
        with_ids = {md: md.read_text() for md in mds}
        for md in mds:
            md.write_text("\n".join(l for l in with_ids[md].split("\n")
                                    if "local-agents-id" not in l))
        self.commit("a catalog from before ids")
        self.install_all()
        self.make_legacy(self.stamp)
        for md, text in with_ids.items():
            md.write_text(text)
        self.commit("the catalog gains its ids")
        run = self.install("--refresh")
        self.assertEqual(run.returncode, 0, run.stderr[-500:])
        # Rebuilt from the stamped commit, not the author fallback: only the
        # rebuild can tell an edit apart.
        self.assertNotIn("cannot be told apart", run.stdout)
        self.assertNotIn("left alone", run.stdout)
        self.assertTrue(all(self.is_ours(d) for d in self.skills.iterdir()))
        self.assertFalse([p for p in self.agents.iterdir() if "-2" in p.stem])
        stamp = json.loads(self.stamp.read_text())
        self.assertEqual((len(stamp["skills"]), len(stamp["agents"])), (48, 15))

    # -- found by review: every path records what it wrote ---------------- #

    def test_a_skill_installed_alone_is_recorded_and_its_edit_survives(self):
        run = self.install("--skill", "lh-data-modeling", "--tool", "claude")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(self.stamp.is_file(), "--skill installed and left no record")
        md = self.skills / "lh-data-modeling" / "SKILL.md"
        md.write_text(md.read_text() + "\nMY EDIT\n")
        refresh = self.install("--refresh")
        # It must have run on this host — surviving because refresh skipped the
        # host altogether would prove nothing.
        self.assertEqual(refresh.returncode, 0, refresh.stderr)
        self.assertIn("edited by hand", refresh.stdout)
        self.assertIn("MY EDIT", md.read_text())

    def test_an_agent_then_skills_leave_nothing_marked_edited(self):
        # A relink after the stamp was written used to read as a hand edit.
        self.install("--agent", "qa", "--tool", "claude")
        self.install("--skill", "lh-threat-modeling", "--skill", "lh-remediation", "--tool", "claude")
        self.assertNotIn("edited by hand", self.status())

    def test_an_interactive_one_agent_install_is_recorded(self):
        (self.home / ".claude").mkdir()
        run = subprocess.run([sys.executable, str(self.catalog / "install.py")],
                             input="2\n1\n1\n", capture_output=True, text=True,
                             env=self.env, timeout=300)
        self.assertEqual(run.returncode, 0, run.stderr[-500:])
        self.assertTrue(self.stamp.is_file(), "the menu installed an agent and left no record")
        self.assertIn("agent", run.stdout)
        again = self.install("--agent", "apple-dev", "--tool", "claude")
        self.assertNotIn("not ours", again.stdout)

    def test_a_catalog_that_is_not_a_git_checkout_still_records_and_protects(self):
        plain = self.tmp / "plain-catalog"
        shutil.copytree(CATALOG, plain, ignore=shutil.ignore_patterns(".git", "__pycache__"))
        self.catalog = plain
        self.install_all()
        stamp = json.loads(self.stamp.read_text())
        self.assertNotIn("catalog_commit", stamp)
        self.assertEqual((len(stamp["skills"]), len(stamp["agents"])), (48, 15))
        md = self.skills / "lh-tradeoffs" / "SKILL.md"
        md.write_text(md.read_text() + "\nMY EDIT\n")
        self.install_all()
        self.assertIn("MY EDIT", md.read_text())
        self.assertNotIn("not ours", self.status())

    # -- found by review: rename -------------------------------------------- #

    def test_rename_twice_updates_the_same_copy_and_is_not_retired(self):
        self.skills.mkdir(parents=True)
        foreign_skill(self.skills, "lh-tradeoffs")
        self.install_all("--on-conflict", "rename")
        self.install_all("--on-conflict", "rename")
        self.assertTrue(self.is_ours(self.skills / "lh-tradeoffs-2"))
        self.assertFalse((self.skills / "lh-tradeoffs-3").exists())
        status = self.status()
        self.assertNotIn("rm -r", status, "our only copy must never be offered for deletion")
        self.assertIn("lh-tradeoffs as lh-tradeoffs-2", status)

    # -- found by review: what counts as an edit ------------------------- #

    def test_a_dotfile_does_not_make_a_skill_edited(self):
        self.install_all()
        (self.skills / "lh-pairing" / ".DS_Store").write_bytes(b"\0finder")
        self.assertNotIn("edited by hand", self.status())

    # -- found by review: migrating from a stamp without records --------- #

    def strip_records(self):
        self.make_legacy(self.stamp)

    @staticmethod
    def make_legacy(stamp_file):
        """A stamp exactly as install.py wrote it before B-058: commit, dirty,
        path, time — no records and no `suite`."""
        stamp = json.loads(stamp_file.read_text())
        for k in ("skills", "agents", "suite"):
            stamp.pop(k, None)
        stamp_file.write_text(json.dumps(stamp))

    def test_a_pre_b058_install_keeps_its_hand_edits(self):
        self.own_copy_of_catalog()
        self.install_all()
        md = self.skills / SKILL / "SKILL.md"
        md.write_text(md.read_text() + "\nmy own note\n")
        agent = self.agents / "architect.md"
        agent.write_text(agent.read_text() + "\nmy own rule\n")
        self.strip_records()
        run = self.install("--refresh")
        self.assertIn("my own note", md.read_text())
        self.assertIn("my own rule", agent.read_text())
        self.assertIn("edited by hand", run.stdout)
        stamp = json.loads(self.stamp.read_text())
        self.assertEqual((len(stamp["skills"]), len(stamp["agents"])), (48, 15))

    def test_a_pre_b058_install_from_an_unknown_commit_says_so(self):
        self.install_all()
        self.make_legacy(self.stamp)
        stamp = json.loads(self.stamp.read_text())
        stamp["catalog_commit"] = "0" * 40
        self.stamp.write_text(json.dumps(stamp))
        run = self.install("--refresh")
        self.assertIn("cannot be told apart", run.stdout)
        self.assertFalse([p for p in self.agents.iterdir() if "-2" in p.stem])


    # -- refresh keeps the shape of what was installed ------------------- #

    def test_refresh_of_a_partial_install_stays_partial(self):
        self.install("--skill", "lh-data-modeling", "--tool", "claude")
        self.install("--refresh")
        self.assertEqual([p.name for p in self.skills.iterdir()], ["lh-data-modeling"])
        self.assertFalse(self.agents.exists() and list(self.agents.iterdir()))

    def test_refresh_of_a_whole_install_brings_new_catalog_skills(self):
        catalog = self.own_copy_of_catalog()
        self.install_all()
        new = catalog / "generalist" / "skills" / "brand-new"
        new.mkdir()
        (new / "SKILL.md").write_text(
            '---\nname: brand-new\ndescription: "New. Trigger: never."\nlicense: Apache-2.0\n'
            'metadata:\n  author: jrodrigopuca\n  version: "1.0"\n  local-agents-id: "sk-abc123"\n---\nBody.\n')
        self.commit("add a skill")
        self.install("--refresh")
        self.assertTrue(self.is_ours(self.skills / "brand-new"))


    # -- found migrating a real install --------------------------------- #

    def legacy_install_from_a_catalog_without_ids(self, tool):
        """What a real install from before B-058 looks like: installed from a
        commit without ids, stamped without records; then the catalog moves on."""
        catalog = self.own_copy_of_catalog()
        mds = sorted(catalog.glob("*/skills/*/SKILL.md"))
        with_ids = {md: md.read_text() for md in mds}
        for md in mds:
            md.write_text("\n".join(l for l in with_ids[md].split("\n")
                                    if "local-agents-id" not in l))
        self.commit("before ids")
        run = self.install("--all", "--tool", tool, "--on-conflict", "overwrite")
        self.assertEqual(run.returncode, 0, run.stderr[-300:])
        for md, text in with_ids.items():
            md.write_text(text)
        self.commit("ids")

    def test_refreshing_a_legacy_whole_install_takes_the_whole_catalog_path(self):
        # Measured on a real machine: a legacy stamp took the partial path, met
        # each shared skill once per agent, and called our own fresh writes
        # "edited by hand" — 1482 times over six hosts.
        self.legacy_install_from_a_catalog_without_ids("claude")
        self.make_legacy(self.stamp)
        run = self.install("--refresh")
        self.assertIn("Installing the WHOLE SUITE", run.stdout)
        self.assertNotIn("left alone", run.stdout)
        self.assertTrue(json.loads(self.stamp.read_text())["suite"])

    def test_kiro_agents_list_all_their_skills_after_a_legacy_refresh(self):
        self.legacy_install_from_a_catalog_without_ids("kiro")
        kiro_stamp = self.home / ".kiro" / ".local-agents.json"
        self.make_legacy(kiro_stamp)
        self.install("--refresh")
        kiro = self.status().split("Kiro CLI")[1].split("\nCodex")[0]
        self.assertNotIn("stale", kiro)
        self.assertNotIn("edited", kiro.replace("(it updates only", ""))

    def test_a_partial_refresh_with_shared_dependencies_warns_about_nothing(self):
        # Two agents that share a skill, and that skill changed upstream: the
        # second agent meets our fresh write, which differs from the record.
        catalog = self.own_copy_of_catalog()
        self.install("--agent", "qa", "--agent", "security", "--tool", "claude")
        src = catalog / "generalist" / "skills" / SKILL / "SKILL.md"
        src.write_text(src.read_text() + "\nnew in the catalog\n")
        self.commit("change a shared skill")
        run = self.install("--refresh")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertNotIn("left alone", run.stdout)
        self.assertIn("new in the catalog", (self.skills / SKILL / "SKILL.md").read_text())


if __name__ == "__main__":
    unittest.main()
