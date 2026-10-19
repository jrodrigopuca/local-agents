#!/usr/bin/env python3
"""shell_write_guard.py — a Claude Code PreToolUse hook that refuses a Bash
command which writes a file the agent itself decides (B-083).

The catalog's CORE says files change only through the host's editing tool
("Approval follows the effect"). Measured in Claude Code (B-075): no prompt
text moved senior-dev off heredocs, and in `default` mode the host's own
permission engine already refuses those writes — but `acceptEdits`, `auto` and
`bypassPermissions` let them through, and `auto`/`bypass` even tell the model
to edit with sed and heredocs. This hook closes that gap where it is installed.

What it refuses is NARROW on purpose: bytes the agent decides, written by the
shell — a redirection to a file, `sed -i`, `tee FILE`, an inline script that
opens a file for writing, cp/mv/touch/truncate, `dd of=`, `git apply`, `patch`,
`ed`. What it lets through: project tools that write as a side effect
(`npm install`, `npm run gen`, `prettier --write`, `node --test`), deletions,
directory creation and git state commands. Those are a project tool deciding
the bytes, or another rule's business. The harness keeps its own, WIDER list
(`&shell-write-detours`) to measure this one; the two are never shared.

A text match, not a sandbox: an agent determined to write can obfuscate past
it. It turns a model's habit into a refusal; it is not a defence against an
adversary.

Decision format: JSON on stdout with `permissionDecision: "deny"`, exit 0 —
documented for PreToolUse, and the reason is shown to Claude. Exit 2 with the
reason on stderr would also block; JSON is the structured, current form.

Fail-open: if the hook itself breaks (bad input, a bug), it exits 1, which
Claude Code treats as a non-blocking error, and says why on stderr. A guard
against a model's preference must not brick every shell command on a
teammate's machine; a fail-closed hook would.

Escape: LOCAL_AGENTS_SHELL_GUARD=off in the environment Claude Code runs in.

Standard library only, Python 3.9+.
"""
import json
import os
import re
import sys
from typing import Optional

# Up to the first file-redirection operator outside quotes, then a target that
# is not under /dev/. `2>&1`, `>&2`, `=>`, `->` and `>=` are not file writes.
_REDIR_TARGET = r"(?<![=<>-])(?:&>>?|\d*>{1,2}(?!&))\|?\s*(?!/dev/)[^\s&|;<>=]"

RULES = (
    # A command without a heredoc: every line, outside quotes.
    ("redirect to a file",
     r"""\A(?![\s\S]*<<)(?:[^'"\\]|\\.|'[^']*'|"(?:[^"\\]|\\.)*")*?""" + _REDIR_TARGET),
    # A command with a heredoc: its first line only; the body is data.
    ("heredoc redirected to a file",
     r"""\A(?=[^\n]*<<)(?:[^'"\\\n]|\\.|'[^'\n]*'|"(?:[^"\\\n]|\\.)*")*?""" + _REDIR_TARGET),
    # A shell or eval running a string or a script that redirects.
    ("shell string that redirects to a file",
     r"""(?:\b(?:ba|z)?sh\s+(?:-c\b|-s\b|<<|-\s*<<)|\beval\b)[\s\S]*?(?<![=<>-])"""
     r"""(?:&>>?|\d*>{1,2}(?!&))\s*(?!/dev/)[^\s&|;<>'"=]"""),
    ("in-place sed", r"\bsed\b[^|;&\n]*?\s(?:-[A-Za-z]*i|--in-place)"),
    ("in-place perl/ruby", r"\b(?:perl|ruby)\b[^|;&\n]*?\s-(?![A-Za-z]*M)[A-Za-z]*i"),
    ("in-place awk", r"\b[gm]?awk\b[^|;&\n]*?-i\s*inplace"),
    ("tee to a file", r"\btee\b(?:\s+-\S+)*\s+(?!/dev/)[^\s|;&<>-]"),
    ("open() for writing",
     r"""\bopen(?:Sync)?\s*\(\s*[^,)]+,\s*(?:mode\s*=\s*)?['"](?:[wax]|r\+)"""),
    ("script file write",
     r"\b(?:writeFileSync|writeFile|writeSync|appendFileSync|appendFile|createWriteStream"
     r"|copyFileSync|copyFile|cpSync|renameSync|truncateSync)\s*\("
     r"|\bBun\.write\b|\bDeno\.write\w*|\b(?:File|IO)\.(?:write|binwrite)\b"
     r"|\bwrite\(\s*to(?:File)?:"
     r"|\bwrite_(?:text|bytes)\s*\(|\bshutil\.(?:copy\w*|move)\s*\(|\bos\.(?:rename|replace)\s*\("),
    ("perl open for writing", r"""\bperl\b[\s\S]*?\bopen\b[^;\n]*?['"]\+?>"""),
    ("cp/mv/touch/truncate",
     r"(?:^|[;&|(\n]\s*|\b(?:sudo|env|command|xargs|exec|nohup|time)\s+(?:-\S+\s+)*)"
     r"(?:/(?:usr/)?bin/)?(?:cp|mv|touch|truncate)\s+(?![=)])"),
    ("dd of=", r"\bdd\b[^|;&\n]*\bof="),
    ("git apply",
     r"\bgit\s+(?:-C\s+\S+\s+)?apply\b(?!\s+(?:--check|--stat|--numstat|--summary)\b)"),
    ("patch", r"(?:^|[;&|(\n]\s*)patch\s"),
    ("line editor", r"(?:^|[;&|(\n]\s*)(?:ed|ex|vim?|nvim)\s"),
)
COMPILED = tuple((name, re.compile(rx)) for name, rx in RULES)

REASON = (
    "Refused by the local-agents shell-write guard ({rule}). In this session a file "
    "changes only through the editing tool (Edit, Write), never through the shell. "
    "This refuses the route, not the change: the change itself was not refused. "
    "If no editing tool is available to you, or it is refused, no other route is "
    "permitted either: say so and leave the change as a diff for the user."
)

OFF_VALUES = {"off", "0", "false", "no"}


def classify(command: str) -> Optional[str]:
    """The name of the first rule the command matches, or None."""
    for name, rx in COMPILED:
        if rx.search(command or ""):
            return name
    return None


def decide(event: dict) -> Optional[dict]:
    """The hook's stdout for one PreToolUse event, or None to stay silent."""
    if event.get("tool_name") != "Bash":
        return None
    command = (event.get("tool_input") or {}).get("command")
    if not isinstance(command, str):
        return None
    rule = classify(command)
    if rule is None:
        return None
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": REASON.format(rule=rule),
    }}


def main(stdin=None, stdout=None, stderr=None, environ=None) -> int:
    stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
    environ = os.environ if environ is None else environ
    if environ.get("LOCAL_AGENTS_SHELL_GUARD", "").strip().lower() in OFF_VALUES:
        return 0
    try:
        event = json.loads(stdin.read() or "{}")
        if not isinstance(event, dict):
            raise ValueError("hook input is not a JSON object")
        out = decide(event)
    except Exception as exc:  # fail-open, loudly: see the module docstring
        stderr.write(f"shell-write guard: not blocking, the guard itself failed: {exc!r}\n")
        return 1
    if out is not None:
        stdout.write(json.dumps(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
