#!/usr/bin/env python3
"""verify_before_stop.py — a Claude Code `Stop` hook that runs the project's
own check when the agent tries to finish and, if it is red, sends the agent
back once with the failure (B-084).

    python3 verify_before_stop.py                    # the project declares the check
    python3 verify_before_stop.py '<command>'        # plus a default for projects that don't

The catalog's CORE asks the agent to verify before claiming done, and
`lh-verification` says how; but the one judging whether the work is verified
is the model that did it, and a model grading its own work leans to PASS.
This hook is the stop rule a machine checks: a turn does not end with the
project's check red unless the agent has SEEN it red.

What it does, in order:
  1. Nothing unless the event is `Stop` or `SubagentStop` (Claude Code turns
     a subagent's frontmatter `Stop` into `SubagentStop`, documented), and
     nothing when `stop_hook_active` is true: a stop hook already sent the
     agent back this turn, so this attempt goes through. One block per turn —
     a budget, not a loop. Claude Code caps consecutive continuations at 8
     on its own; this hook spends one.
  2. Runs the command in the session's `cwd`, through the shell, with a
     timeout (LOCAL_AGENTS_VERIFY_TIMEOUT seconds, default 300).
  3. Exit 0 → silent. Success is silent, failures are verbose.
  4. Anything else → `{"decision": "block", "reason": ...}` with the exit
     code and the tail of the output, which Claude Code hands the agent as
     the reason to keep working (for a subagent, as its next instruction).

Where the command comes from — declared, never guessed:
  1. `.local-agents/verify` in the session's cwd or a parent of it, up to
     the repo root (the first directory holding `.git`): its first line that
     is not blank or a `#` comment. The catalog's agents install globally and
     one command cannot fit every repo, so each repo declares its own, in a
     file git carries to the whole team. An EMPTY file (or comments only)
     opts the repo out of the hook entirely, default included.
  2. Else the command on argv: the default `install.py --verify-hook CMD`
     recorded, for projects that declare nothing.
  3. Else nothing to check: silent, with a note on stderr.
The catalog does not infer a command from `package.json` or a `Makefile`: a
hook that guesses fails where nobody is watching.

Fail-open: no command, a command that cannot start, a timeout, bad input or
a bug in the hook never block. Exit 1 with the reason on stderr is Claude
Code's non-blocking error; the agent finishes and the user sees why in the
transcript. A verification aid must not strand every turn on a teammate's
machine.

Escape: LOCAL_AGENTS_VERIFY_HOOK=off in the environment Claude Code runs in.

Host-neutral on purpose: JSON in on stdin, JSON out on stdout, the command on
argv. Which EVENT delivers "the agent wants to finish" is each host's; this
file carries nothing of Claude Code but the output shape it documents.

Standard library only, Python 3.9+.
"""
import json
import os
import subprocess
import sys
from typing import Optional

EVENTS = ("Stop", "SubagentStop")
PROJECT_FILE = os.path.join(".local-agents", "verify")
OFF_VALUES = {"off", "0", "false", "no"}
DEFAULT_TIMEOUT = 300
TAIL_LINES = 40
TAIL_CHARS = 4000

REASON = (
    "The project check `{cmd}` ({source}) fails (exit {code}) and you were about to finish. "
    "Last lines of its output:\n\n{tail}\n\n"
    "A turn does not end with this check red and unmentioned. Either fix the cause "
    "and run `{cmd}` again, or finish by reporting the failure with this output and "
    "what you tried. This hook blocks once per turn: the next attempt to finish "
    "goes through."
)


def tail(text: str, lines: int = TAIL_LINES, chars: int = TAIL_CHARS) -> str:
    """The last `lines` lines of `text`, at most `chars` characters."""
    kept = (text or "").rstrip().splitlines()[-lines:]
    out = "\n".join(kept)
    if len(out) > chars:
        out = "…" + out[-chars:]
    return out or "(no output)"


def timeout_seconds(environ) -> float:
    try:
        return max(1.0, float(environ.get("LOCAL_AGENTS_VERIFY_TIMEOUT", DEFAULT_TIMEOUT)))
    except ValueError:
        return float(DEFAULT_TIMEOUT)


def read_command(path: str) -> str:
    """The command a `.local-agents/verify` file declares: its first line that
    is not blank or a comment; "" when it declares none (the repo opts out)."""
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                return line
    return ""


def project_command(cwd: str) -> Optional[tuple]:
    """(command, file) from the nearest `.local-agents/verify` between `cwd`
    and the repo root, or None when no directory on that path has one."""
    d = os.path.abspath(cwd)
    while True:
        f = os.path.join(d, PROJECT_FILE)
        if os.path.isfile(f):
            return read_command(f), f
        if os.path.exists(os.path.join(d, ".git")):
            return None
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def resolve_command(cwd: Optional[str], default: str) -> tuple:
    """(command, where it came from). An empty command means nothing to run:
    the repo opted out, or nothing is declared and there is no default."""
    found = project_command(cwd) if cwd else None
    if found is not None:
        cmd, path = found
        return (cmd, f"declared in {path}") if cmd else ("", f"{path} declares no check")
    if default:
        return default, "the install default, no .local-agents/verify in this repo"
    return "", "no .local-agents/verify in this repo and no install default"


def decide(event: dict, default: str, environ, stderr) -> Optional[dict]:
    """The hook's stdout for one event, or None to stay silent. Raises on a
    command that cannot run or does not finish; main() turns that into a
    non-blocking error."""
    if event.get("hook_event_name") not in EVENTS:
        return None
    if event.get("stop_hook_active"):
        return None
    cwd = event.get("cwd") or None
    if cwd and not os.path.isdir(cwd):
        cwd = None
    cmd, source = resolve_command(cwd, default)
    if not cmd:
        stderr.write(f"verify hook: nothing to check ({source})\n")
        return None
    proc = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True,
                          errors="replace", timeout=timeout_seconds(environ),
                          stdin=subprocess.DEVNULL)
    if proc.returncode == 0:
        return None
    output = proc.stdout + ("\n" if proc.stdout and proc.stderr else "") + proc.stderr
    return {"decision": "block",
            "reason": REASON.format(cmd=cmd, source=source, code=proc.returncode,
                                    tail=tail(output))}


def main(argv=None, stdin=None, stdout=None, stderr=None, environ=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    stdin, stdout, stderr = stdin or sys.stdin, stdout or sys.stdout, stderr or sys.stderr
    environ = os.environ if environ is None else environ
    if environ.get("LOCAL_AGENTS_VERIFY_HOOK", "").strip().lower() in OFF_VALUES:
        return 0
    default = " ".join(argv).strip()
    try:
        event = json.loads(stdin.read() or "{}")
        if not isinstance(event, dict):
            raise ValueError("hook input is not a JSON object")
        out = decide(event, default, environ, stderr)
    except subprocess.TimeoutExpired as exc:
        stderr.write(f"verify hook: not blocking, `{exc.cmd}` did not finish in "
                     f"{timeout_seconds(environ):g} s (LOCAL_AGENTS_VERIFY_TIMEOUT)\n")
        return 1
    except Exception as exc:  # fail-open, loudly: see the module docstring
        stderr.write(f"verify hook: not blocking, the hook itself failed: {exc!r}\n")
        return 1
    if out is not None:
        stdout.write(json.dumps(out) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
