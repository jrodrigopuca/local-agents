"""judgment-refs (rule 14): a skill's "judgment #N" resolves to a numbered
judgment of the right agent's body, and to the rule it was pinned to. Runs
without PyYAML, as the CI test step does: the check reads no YAML.

    python3 -m unittest discover -s tests
"""
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
try:
    import yaml  # noqa: F401
except ImportError:
    sys.modules["yaml"] = types.ModuleType("yaml")
import validate  # noqa: E402

DEV = """# Dev
## Peer Contract
1. **Say what you will do.** Then do it.
2. **Leave the call to the user.** Once.

## Developer Judgment — the core
1. **Read before writing.** The repo first.
2. **Small diffs.** Reviewable.
3. **Tests are a safety net, not a ceremony.** Cover
   the risk.
"""
QA = """# QA
## QA Judgment — the core
1. **The bug is the adversary.** Never the dev.
2. **Risk-based.** Not everything.
"""
NOSECTION = """# Mentor
## How you teach
1. **Socratic first.** Ask.
"""
AGENTS = {"dev": DEV, "qa": QA, "mentor": NOSECTION}
PINS = {("dev", 1): "Read before writing.", ("dev", 2): "Small diffs.",
        ("dev", 3): "Tests are a safety net, not a ceremony.",
        ("qa", 1): "The bug is the adversary.", ("qa", 2): "Risk-based."}


def refs(text, owner="qa", pins=None, agents=None):
    """Errors for one skill owned by `owner`, ignoring pins nobody cites."""
    errs = validate.judgment_refs(agents or AGENTS, {"lh-x": (owner, "qa/skills/lh-x/SKILL.md", text)},
                                  PINS if pins is None else pins)
    return [e for e in errs if "no skill cites" not in e]


class Resolution(unittest.TestCase):

    def test_unqualified_resolves_to_owner(self):
        self.assertEqual(refs("see judgment #2 here"), [])
        self.assertTrue(refs("see judgment #3 here"), "qa has no #3; dev's #3 must not satisfy it")

    def test_agent_prefix_resolves_cross_agent(self):
        self.assertEqual(refs("the dev judgment #3 applies"), [])

    def test_link_target_resolves_cross_agent(self):
        text = "[dev](../../../dev/AGENTS.md), Developer Judgment #3 (tests)"
        self.assertEqual(refs(text), [])

    def test_a_link_further_back_does_not_requalify(self):
        text = "the machinery is [dev](../../../dev/AGENTS.md)'s to build, the doctrine is judgment #2."
        self.assertEqual(refs(text), [], "judgment #2 here is the owner's (qa), not dev's")

    def test_capitalised_section_word_is_allowed(self):
        self.assertEqual(refs("Management judgment #1: step aside"), [])

    def test_ignores_non_judgment_numbered_lists(self):
        section = validate.judgment_section(DEV)
        self.assertEqual(section[1], "Read before writing.")
        self.assertEqual(section[3], "Tests are a safety net, not a ceremony.")

    def test_bare_hash_ignored(self):
        self.assertEqual(refs("as pattern (#9) says"), [])


class Failures(unittest.TestCase):

    def test_missing_number_fails(self):
        errs = refs("judgment #7")
        self.assertEqual(len(errs), 1)
        self.assertIn("does not exist", errs[0])
        self.assertIn("SKILL.md:1:", errs[0])

    def test_range_both_ends_checked(self):
        self.assertEqual(refs("([judgment #1-2](../../AGENTS.md))"), [])
        errs = refs("([judgment #2-3](../../AGENTS.md))")
        self.assertEqual(len(errs), 1)
        self.assertIn("#3", errs[0])

    def test_title_mismatch_fails_after_renumber(self):
        renumbered = QA.replace("1. **The bug is the adversary.**", "1. **Reproduce first.**") \
                       .replace("2. **Risk-based.**", "2. **The bug is the adversary.**")
        errs = refs("judgment #1", agents={**AGENTS, "qa": renumbered})
        self.assertEqual(len(errs), 1)
        self.assertIn("renumbered or renamed", errs[0])

    def test_unpinned_citation_fails(self):
        errs = refs("judgment #1", pins={})
        self.assertIn("not pinned", errs[0])

    def test_stale_pin_fails(self):
        errs = validate.judgment_refs(AGENTS, {"lh-x": ("qa", "x", "nothing cited")}, {("qa", 1): "The bug is the adversary."})
        self.assertEqual(len(errs), 1)
        self.assertIn("no skill cites", errs[0])

    def test_agent_without_judgment_section_fails_loudly(self):
        errs = refs("judgment #1", owner="mentor")
        self.assertEqual(len(errs), 1)
        self.assertIn("no `## … Judgment — the core` list", errs[0])

    def test_line_is_the_citation_not_the_word_before(self):
        errs = refs("first line ends with the\njudgment #7 on the second")
        self.assertIn("SKILL.md:2:", errs[0])


if __name__ == "__main__":
    unittest.main()
