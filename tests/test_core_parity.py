"""core-parity (B-069): every rule of generalist/CORE.md has its version in
the generalist body, which does not inherit the CORE. Runs without PyYAML, as
the CI test step does: the check reads no YAML, so a bare stand-in is enough
for validate.py to import.

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

CORE = """# Core
- **Evidence ladder.** Know which rung you are on.
- **Act vs. stop.** Reversible → act.
"""
MAP = {"Evidence ladder.": ["Evidence > memory"],
       "Act vs. stop.": ["Reversible and in-scope → act", "Asked → stop"]}
BODY = """1. **Evidence > memory > inference.** Know
the tier.
- **Reversible and in-scope → act.** Do it.
- **Asked → stop.** End the turn.
"""


class Parity(unittest.TestCase):

    def test_a_body_with_every_anchor_passes(self):
        self.assertEqual(validate.core_parity(CORE, BODY, MAP), [])

    def test_anchors_match_across_line_wraps(self):
        body = BODY.replace("Evidence > memory", "Evidence >\n   memory")
        self.assertEqual(validate.core_parity(CORE, body, MAP), [])

    def test_a_core_rule_without_an_entry_in_the_map_fails(self):
        core = CORE + "- **Approval follows the effect.** New rule.\n"
        errs = validate.core_parity(core, BODY, MAP)
        self.assertEqual(len(errs), 1)
        self.assertIn("Approval follows the effect.", errs[0])
        self.assertIn("no entry in CORE_PARITY", errs[0])

    def test_an_anchor_missing_from_the_body_fails(self):
        errs = validate.core_parity(CORE, BODY.replace("Asked → stop", "When asked, end"), MAP)
        self.assertEqual(len(errs), 1)
        self.assertIn("lacks `Asked → stop`", errs[0])

    def test_a_mapped_rule_gone_from_the_core_is_reported(self):
        core = CORE.replace("- **Act vs. stop.** Reversible → act.\n", "")
        errs = validate.core_parity(core, BODY, MAP)
        self.assertEqual(len(errs), 1)
        self.assertIn("no longer a rule", errs[0])

    def test_the_real_map_covers_every_rule_of_the_real_core(self):
        core = (ROOT / "generalist" / "CORE.md").read_text(encoding="utf-8")
        import re
        titles = re.findall(r"^- \*\*(.+?)\*\*", core, re.M)
        self.assertEqual(sorted(titles), sorted(validate.CORE_PARITY))


if __name__ == "__main__":
    unittest.main()
