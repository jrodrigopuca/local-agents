"""The interactive menu (install.py with no arguments) and --list. Standard
library only, no network:

    python3 -m unittest discover -s tests

A menu is the one place where the installer waits for a person, so what it
does with an answer it did not expect is the behaviour that matters: it says
so, it never installs "the part that was right", and leaving it changes
nothing.
"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1]


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): p.read_bytes() if p.is_file() else None
            for p in sorted(root.rglob("*"))}


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.home = Path(self._tmp.name) / "home"
        self.claude = self.home / ".claude"
        self.claude.mkdir(parents=True)
        self.env = {k: v for k, v in os.environ.items()
                    if k not in ("CLAUDE_CONFIG_DIR", "CODEX_HOME", "LOCAL_AGENTS_FRONT")
                    and not k.startswith("GIT_")}
        self.env.update(HOME=str(self.home), USERPROFILE=str(self.home), PYTHONDONTWRITEBYTECODE="1")

    def run_install(self, *args, typed=None):
        return subprocess.run([sys.executable, str(CATALOG / "install.py"), *args],
                              input=typed, capture_output=True, text=True, env=self.env,
                              stdin=None if typed is not None else subprocess.DEVNULL,
                              timeout=300, cwd=str(CATALOG))

    def menu(self, *answers):
        return self.run_install(typed="".join(f"{a}\n" for a in answers))

    def installed(self, kind):
        d = self.claude / kind
        return sorted(p.name for p in d.iterdir()) if d.is_dir() else []


class Choosing(Base):
    def test_the_tool_menu_shows_the_state_of_each_tool(self):
        self.run_install("--all", "--tool", "claude")
        out = self.menu("1", "q").stdout
        self.assertRegex(out, r"(?m)^  1\. claude +up to date$")
        self.assertRegex(out, r"(?m)^  3\. kiro +not detected$")

    def test_one_agent_installs_and_says_how_to_take_it_back(self):
        run = self.menu("2", "1", "10")              # an agent, into claude, the tenth: qa
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("Installing agent qa into claude (~/.claude)", run.stdout)
        self.assertRegex(run.stdout, r"(?m)^  agents +1 installed$")
        self.assertIn("Undo: ./install.py --uninstall --tool claude", run.stdout)
        self.assertEqual(self.installed("agents"), ["qa.md"])
        undo = self.run_install("--uninstall", "--tool", "claude")
        self.assertEqual(undo.returncode, 0, undo.stderr)
        self.assertEqual(snapshot(self.home), {".claude": None})

    def test_a_number_off_the_list_is_said_and_asked_again(self):
        run = self.menu("9", "0", "abc", "2", "1", "10")
        self.assertEqual(run.stdout.count("Type a number from 1 to 3, or q to quit."), 3)
        self.assertEqual(self.installed("agents"), ["qa.md"])

    def test_a_tool_that_is_not_there_asks_first_and_no_is_the_default(self):
        run = self.menu("1", "3", "")                # kiro, then Enter at "anyway?"
        self.assertIn("kiro was not detected (~/.kiro does not exist). Install there anyway? [y/N]",
                      run.stdout)
        self.assertIn("Cancelled: nothing was changed.", run.stdout)
        self.assertFalse((self.home / ".kiro").exists())


class Leaving(Base):
    def test_q_or_enter_at_any_menu_changes_nothing_and_says_so(self):
        before = snapshot(self.home)
        for answers in (("q",), ("",), ("1", "q"), ("2", "1", "q"), ("3", "1", "q"), ("3", "1", "")):
            with self.subTest(answers=answers):
                run = self.menu(*answers)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertTrue(run.stdout.rstrip().endswith("Cancelled: nothing was changed."),
                                run.stdout[-200:])
                self.assertNotIn("Done", run.stdout)
                self.assertEqual(snapshot(self.home), before)

    def test_no_one_at_the_keyboard_is_an_error_not_a_traceback(self):
        run = self.run_install()                     # stdin closed, as in CI
        self.assertEqual(run.returncode, 1)
        self.assertIn("error: the menu needs someone to answer it", run.stderr)
        self.assertIn("Try: ./install.py --list", run.stderr)
        self.assertNotIn("Traceback", run.stderr)
        self.assertEqual(snapshot(self.home), {".claude": None})


class Skills(Base):
    def numbers(self, *names):
        listing = self.menu("3", "1", "q").stdout.splitlines()
        return [next(l.split(".")[0].strip() for l in listing if l.strip().endswith(f":{n}")) for n in names]

    def test_several_skills_at_once(self):
        a, b = self.numbers("lh-icons", "lh-mockups")
        run = self.menu("3", "1", f"{a}, {b}")
        self.assertIn("Installing skill lh-icons, skill lh-mockups into claude (~/.claude)", run.stdout)
        self.assertEqual(self.installed("skills"), ["lh-icons", "lh-mockups"])

    def test_one_bad_number_rejects_the_whole_line_and_installs_nothing_yet(self):
        # it used to drop the bad ones in silence and install the rest
        a, = self.numbers("lh-icons")
        run = self.menu("3", "1", f"{a}, 99, x", "q")
        self.assertIn("99, x are not on the list. Type numbers from 1 to 51.", run.stdout)
        self.assertIn("Cancelled: nothing was changed.", run.stdout)
        self.assertEqual(self.installed("skills"), [])

    def test_the_same_number_twice_is_one_skill(self):
        a, = self.numbers("lh-icons")
        run = self.menu("3", "1", f"{a} {a}")
        self.assertIn("Installing skill lh-icons into claude", run.stdout)
        self.assertRegex(run.stdout, r"(?m)^  skills +1 installed$")


class Conflict(Base):
    def setUp(self):
        super().setUp()
        self.run_install("--agent", "qa", "--tool", "claude")
        self.mine = self.claude / "skills" / "lh-bug-reporting" / "SKILL.md"
        self.mine.write_text(self.mine.read_text() + "\nmine\n")

    def test_a_file_edited_by_hand_is_asked_about_and_enter_keeps_it(self):
        run = self.menu("2", "1", "10", "")
        self.assertIn("skill lh-bug-reporting was edited by hand since it was installed.", run.stdout)
        self.assertIn("[k] keep your version (default)   [r] replace with the catalog's", run.stdout)
        self.assertIn("Kept 1 file as it is:", run.stdout)
        self.assertIn("mine", self.mine.read_text())

    def test_an_answer_that_is_not_one_of_the_keys_is_said_and_asked_again(self):
        run = self.menu("2", "1", "10", "zz", "r")
        self.assertIn("Type k or r.", run.stdout)
        self.assertNotIn("Kept", run.stdout)
        self.assertNotIn("mine", self.mine.read_text())

    def test_a_name_something_else_holds_offers_to_install_ours_beside_it(self):
        self.mine.write_text("---\nname: lh-bug-reporting\ndescription: theirs\n---\n")
        run = self.menu("2", "1", "10", "n")
        self.assertIn("skill lh-bug-reporting is not from this catalog: something else has that name.",
                      run.stdout)
        self.assertIn("[n] install ours under another name", run.stdout)
        self.assertTrue((self.claude / "skills" / "lh-bug-reporting-2" / "SKILL.md").is_file())
        self.assertIn("theirs", self.mine.read_text())


class Listing(Base):
    def test_it_fits_80_columns_in_plain_ascii(self):
        out = self.run_install("--list").stdout
        for line in out.splitlines():
            self.assertLessEqual(len(line), 80, line)
            self.assertTrue(line.isascii(), line)

    def test_an_agent_shows_its_own_skills_and_what_comes_with_it(self):
        lines = self.run_install("--list").stdout.splitlines()
        i = next(n for n, l in enumerate(lines) if l.startswith("  architect "))
        self.assertRegex(lines[i], r"^  architect +3 skills of its own, \d+ installed with it$")
        self.assertEqual(lines[i + 1].strip(), "lh-design-review, lh-mentoring, lh-tradeoffs")

    def test_tools_are_named_by_their_key_with_what_is_there(self):
        out = self.run_install("--list").stdout
        self.assertRegex(out, r"(?m)^  claude +available +agents and skills$")
        self.assertRegex(out, r"(?m)^  kiro +not detected +agents and skills$")


if __name__ == "__main__":
    unittest.main()
