"""The shell-write guard (B-083): which Bash commands it refuses, what it
prints, and that it never blocks when it breaks. Standard library only:

    python3 -m unittest discover -s tests

The corpus is real. DETOURS are commands agents ran in the harness
(interaction, runs 20261012..20261019), every one a write by the shell the
CORE forbids; LEGIT are commands from the same runs that the harness's wide
list (`&shell-write-detours`) did not flag, plus the project tools the guard
must never stop. Over all 1298 distinct Bash commands of those runs, the
guard flagged 115 and the wide list flagged the same 115 plus 21 (rm, git
checkout/stash/rm, rsync), none of them a write the agent authored.
"""
import importlib.util
import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "shell_write_guard.py"
_spec = importlib.util.spec_from_file_location("shell_write_guard", SCRIPT)
guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(guard)

DETOURS = [
    # heredocs into a file (B-075, runs 20261019-115116 and -115630)
    "mkdir -p test && cat > test/webhook.test.mjs <<'EOF'\nimport test from \"node:test\";\nEOF",
    "cat > src/webhook.mjs <<'EOF'\n// Handler del webhook\nexport const x = 1;\nEOF",
    "cat >> README.md <<'EOF'\n\n## Idempotencia\nEOF",
    "cat > /tmp/probe.mjs <<'EOF'\nimport { processOrder } from './x.mjs'\nEOF",
    "cat <<'EOF' > notes.md\nhola\nEOF",
    # python and node scripts that open a file for writing
    "python3 - <<'EOF'\np='parseCSVLine.mjs'\ns=open(p).read()\ns=s.replace('a','b')\nopen(p,'w').write(s)\nEOF",
    "python3 -I - <<'EOF'\np='parseCSVLine.mjs'\nwith open(p, 'w') as f:\n    f.write(s)\nEOF",
    "python3 -c \"from pathlib import Path; Path('a.txt').write_text('x')\"",
    "python3 -c \"import shutil; shutil.copy('a', 'b')\"",
    "node -e 'const fs=require(\"fs\"); fs.writeFileSync(\"package.json\", s)'",
    "node -e \"require('fs').appendFileSync('log.txt', 'x')\"",
    "cat > pnpm-workspace.yaml <<'EOF'\npackages:\n  - packages/*\nEOF\nnode -e '\nconst fs=require(\"fs\");\nfs.writeFileSync(f, s)'",
    # in-place editors
    "sed -i '' 's/export function parseCSVLine(line) {/export function parseCSVLine(line, sep) {/' parseCSVLine.mjs",
    "sed -i 's|    \"invoices:void\",|    \"invoices:export\",|' permissions.json && npm run gen 2>&1 | tail -5",
    "f=parseCSVLine.mjs\nsed -i '' 's/a/b/' $f",
    "perl -pi -e 's/a/b/' src/x.mjs",
    "gawk -i inplace '{print}' a.txt",
    # plain redirections
    "echo '{\"host\":\"127.0.0.1\",\"port\":18081}' > config/tmpcheck.json",
    "git show HEAD:src/webhook.mjs > src/webhook.mjs",
    "printf 'x\\n' >> README.md",
    "node --test --test-reporter=spec > /tmp/out.txt 2>&1; grep -c ok /tmp/out.txt",
    "bash -c 'echo hi > out.txt'",
    "echo data | tee out.txt",
    "echo data | tee -a log/out.txt >/dev/null",
    # copies, moves, low-level and patch tools
    "cp src/webhook.mjs /tmp/webhook.fixed.mjs",
    "mv a.mjs b.mjs",
    "touch src/new.mjs",
    "truncate -s 0 log.txt",
    "dd if=/dev/zero of=blob.bin bs=1 count=1",
    "git apply fix.patch",
    "patch -p1 < fix.diff",
    "ed -s file.txt <<< $'1d\\nw'",
]

LEGIT = [
    # project tools the guard must never stop (B-073: bytes a tool decides)
    "npm install",
    "npm ci 2>&1 | tail -3; npm run build 2>&1 | tail -8",
    "npm run gen",
    "npm run gen 2>&1 | tail -5; npm run check:gen 2>&1 | tail -3; git diff --stat",
    "npx prettier --write .",
    "npx eslint --fix src",
    "node --test",
    "node --test src/webhook.test.mjs 2>&1 | tail -30",
    "node --test --test-reporter=spec 2>&1 | grep -E \"^(ℹ (tests|pass|fail)|✖)\"",
    "node scripts/gen.mjs",
    # deletions, directories and git state are another rule's business
    "rm -rf node_modules",
    "rm config/tmpcheck.json && git status --short",
    "mkdir -p test",
    "git checkout -b feature/x",
    "git checkout parseCSVLine.test.mjs && git diff parseCSVLine.mjs | head -50",
    "git stash list",
    "git mv a.mjs b.mjs",
    "git apply --check fix.patch",
    # output to /dev, fd duplication and reads
    "echo x > /dev/null",
    "npm run gen > /dev/null 2>&1",
    "command -v tree >/dev/null && tree -a",
    "node scripts/healthcheck.mjs; echo \"exit=$?\"",
    "cat src/db/sql.mjs src/routes/users.mjs",
    "git status --short | head -30; git log --oneline | head -10; ls",
    "rg -n \"parseCSVLine\" --glob '!node_modules' . ; git status --short",
    "rg -n --no-heading '\\bformatCents\\b' .",
    "find . -maxdepth 3 -not -path './.git/*'",
    "ls -a && cat .gitignore; tail -c1 .gitignore | xxd",
    "for f in README.md package.json config/*.json; do echo \"=== $f\"; cat $f; done",
    "grep -E '\"(jest|vitest|test)[^\"]*\"' package.json",
    "git log --format=%H -- src/orders.mjs | wc -l",
    "node -e 'console.log(1 > 0 ? \"a\" : \"b\")'",
    "node -e 'const fs=require(\"fs\"); console.log(fs.readFileSync(\"package.json\",\"utf8\"))'",
    "python3 -c \"print(open('a.txt').read())\"",
    "[ -f package.json ] && echo yes",
    "git commit -m \"parseCSVLine: separator => configurable\"",
]


def run_main(payload, environ=None):
    out, err = io.StringIO(), io.StringIO()
    stdin = io.StringIO(payload if isinstance(payload, str) else json.dumps(payload))
    code = guard.main(stdin=stdin, stdout=out, stderr=err, environ=environ or {})
    return code, out.getvalue(), err.getvalue()


def bash_event(cmd):
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash",
            "tool_input": {"command": cmd}, "permission_mode": "auto"}


class Corpus(unittest.TestCase):

    def test_every_detour_is_refused(self):
        for cmd in DETOURS:
            with self.subTest(cmd=cmd[:60]):
                self.assertIsNotNone(guard.classify(cmd))

    def test_every_legitimate_command_passes(self):
        for cmd in LEGIT:
            with self.subTest(cmd=cmd[:60]):
                self.assertIsNone(guard.classify(cmd), guard.classify(cmd))


class Output(unittest.TestCase):

    def test_a_refusal_is_the_documented_pretooluse_deny(self):
        code, out, err = run_main(bash_event("cat > a.txt <<'EOF'\nx\nEOF"))
        self.assertEqual((code, err), (0, ""))
        hso = json.loads(out)["hookSpecificOutput"]
        self.assertEqual(hso["hookEventName"], "PreToolUse")
        self.assertEqual(hso["permissionDecision"], "deny")
        self.assertIn("heredoc redirected to a file", hso["permissionDecisionReason"])

    def test_the_reason_refuses_the_route_not_the_change(self):
        reason = guard.REASON
        self.assertIn("refuses the route, not the change", reason)
        self.assertIn("editing tool", reason)
        # B-078: without an editing tool, no other route either.
        self.assertIn("no other route", reason)
        self.assertIn("diff", reason)

    def test_an_allowed_command_prints_nothing(self):
        self.assertEqual(run_main(bash_event("npm run gen")), (0, "", ""))

    def test_other_tools_are_not_its_business(self):
        ev = {"tool_name": "Write", "tool_input": {"file_path": "a > b", "content": "x"}}
        self.assertEqual(run_main(ev), (0, "", ""))

    def test_the_escape_variable_turns_it_off(self):
        ev = bash_event("echo x > a.txt")
        for value in ("off", "OFF", "0", "false"):
            self.assertEqual(run_main(ev, {"LOCAL_AGENTS_SHELL_GUARD": value}), (0, "", ""))
        self.assertIn("deny", run_main(ev, {"LOCAL_AGENTS_SHELL_GUARD": "on"})[1])


class FailOpen(unittest.TestCase):
    """A guard that breaks says so and blocks nothing: exit 1 is a
    non-blocking error for Claude Code; exit 2 would block."""

    def test_unparseable_input_does_not_block(self):
        code, out, err = run_main("not json")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("not blocking", err)

    def test_input_that_is_not_an_object_does_not_block(self):
        code, out, err = run_main("[1, 2]")
        self.assertEqual((code, out), (1, ""))

    def test_a_missing_command_is_not_a_refusal(self):
        self.assertEqual(run_main({"tool_name": "Bash", "tool_input": {}}), (0, "", ""))


class AsAProcess(unittest.TestCase):

    def test_the_script_runs_as_the_hook_command_runs_it(self):
        proc = subprocess.run([sys.executable, "-I", str(SCRIPT)],
                              input=json.dumps(bash_event("sed -i 's/a/b/' x")),
                              capture_output=True, text=True, timeout=30,
                              env={k: v for k, v in os.environ.items()
                                   if k != "LOCAL_AGENTS_SHELL_GUARD"})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
