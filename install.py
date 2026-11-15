#!/usr/bin/env python3
"""install.py — install catalog agents (with their skills) or standalone skills
into a coding tool's config, globally or inside a project checkout.

This automates Pattern B ("vendor/copy") from INTEGRATION.md: instead of the
tool config REFERENCING the catalog, we COPY the agent + skills into the tool's
own directories so they travel with the machine.

Usage:
  ./install.py                          # interactive
  ./install.py --list                   # show detected agents/skills + tools
  ./install.py --status                 # show what is installed, and if it is current
  ./install.py --agent architect --tool claude
  ./install.py --skill architect:tradeoffs --tool codex
  ./install.py --agent qa --tool kiro --on-conflict rename --dry-run
  ./install.py --all --tool claude --project ~/code/repo   # vendor into a repo
  ./install.py --all --tool claude --shell-write-guard     # + refuse file writes via Bash
  ./install.py --all --tool claude --verify-hook   # + run each repo's declared check before the agent finishes

No external dependencies — Python 3.9+ stdlib only.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Optional

# Ensure UTF-8 I/O across platforms (particularly on Windows)
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

HOME = Path.home()


def env_dir(var: str, default: Path) -> Path:
    """Honour a tool's own config-dir override when it defines one.

    Only two do: Claude Code reads CLAUDE_CONFIG_DIR (multi-account setups)
    and Codex reads CODEX_HOME. opencode's docs prescribe a literal
    `~/.config/opencode` with no env override — it is NOT XDG-aware, so do not
    "fix" it to use XDG_CONFIG_HOME. Kiro and Antigravity publish no such
    variable."""
    value = os.environ.get(var)
    return Path(value).expanduser() if value else default


CLAUDE_ROOT = env_dir("CLAUDE_CONFIG_DIR", HOME / ".claude")
CODEX_ROOT = env_dir("CODEX_HOME", HOME / ".codex")
# Antigravity reads both agents and skills from the config dir it shares with
# the IDE; per workspace both live under `.agents/`. Measured on agy 1.3.3: the
# docs give `~/.gemini/antigravity-cli/skills/` for the CLI, but agy does not
# read it — `~/.gemini/config/skills/` is the only skills path in the binary,
# and a skill placed there is the one it sees.
AGY_ROOT = HOME / ".gemini/config"


# --------------------------------------------------------------------------- #
# TOOL REGISTRY
#
# To add a tool: append one Tool(...) below. That's it — UNLESS the tool needs
# a brand-new agent-file FORMAT, in which case also add a branch in
# render_agent(). Existing styles: "claude_md", "opencode_md", "kiro_json",
# "antigravity_md", "codex_toml", "roster_md".
# A tool with agents_dir=None has no named-agent concept (installing an "agent"
# there installs its skills and prints an AGENTS.md snippet to add by hand).
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Tool:
    key: str
    label: str
    config_root: Path            # existence of this dir => tool is installed
    skills_dir: Path
    agents_dir: Optional[Path]   # None => no place to put agent bodies at all
    agent_style: Optional[str]   # "claude_md" | "opencode_md" | "kiro_json" | "roster_md" | "antigravity_md" | "codex_toml"
    project_dir: str             # per-repo config dir, relative to the project root
    roster_file: Optional[Path] = None   # roster destination; defaults to config_root/AGENTS.md
    # Skill dirs the HOST also reads besides skills_dir — global paths, and
    # project paths relative to the repo root. Only used to report shadowing:
    # the installer never relies on another tool's copy (see shadow_report).
    also_reads: tuple = ()
    project_also_reads: tuple = ()

    @property
    def roster(self) -> Path:
        return self.roster_file or (self.config_root / "AGENTS.md")


# `roster_md` is for tools with no named-agent concept (the shared folder). The
# bodies still get copied — self-contained, same as everywhere else — and a
# short roster is written into the tool's AGENTS.md pointing at them, so the
# identities are discoverable without paying every full prompt of context on
# every session.
TOOLS = [
    Tool("claude", "Claude Code",
         CLAUDE_ROOT, CLAUDE_ROOT / "skills",
         CLAUDE_ROOT / "agents", "claude_md", ".claude"),
    # Measured on opencode 1.18.11 with `opencode debug skill`: it also loads
    # skills from Claude Code's dir, the shared dir and its legacy singular
    # `skill/`, and per project from `.agents/skills` and `.claude/skills`. It
    # does NOT read agents from `.agents/agents`.
    Tool("opencode", "opencode",
         HOME / ".config/opencode", HOME / ".config/opencode/skills",
         HOME / ".config/opencode/agents", "opencode_md", ".opencode",
         also_reads=(HOME / ".claude/skills", HOME / ".agents/skills",
                     HOME / ".config/opencode/skill"),
         project_also_reads=(".agents/skills", ".claude/skills")),
    Tool("kiro", "Kiro CLI",
         HOME / ".kiro", HOME / ".kiro/skills",
         HOME / ".kiro/agents", "kiro_json", ".kiro"),
    # Documented, not measured: Codex scans `~/.agents/skills`, and per project
    # `.agents/skills`. Agents are TOML files (measured on codex-cli 0.144.5).
    Tool("codex", "Codex",
         CODEX_ROOT, CODEX_ROOT / "skills",
         CODEX_ROOT / "agents", "codex_toml", ".codex",
         also_reads=(HOME / ".agents/skills",),
         project_also_reads=(".agents/skills",)),
    Tool("antigravity", "Antigravity CLI",
         AGY_ROOT, AGY_ROOT / "skills",
         AGY_ROOT / "agents", "antigravity_md", ".agents"),
    Tool("shared", "Shared: ~/.agents, skills read by opencode and Codex",
         HOME / ".agents", HOME / ".agents/skills",
         HOME / ".agents/agents", "roster_md", ".agents"),
]


def project_tool(tool: Tool, root: Path) -> Tool:
    """Retarget a tool at a project checkout instead of the user's home.

    Every supported tool reads a per-repo config dir, so the same rendering
    works — only the destination moves. A roster tool's roster goes to the REPO
    ROOT `AGENTS.md`, which is where Codex reads it per project; for Codex that
    path is still recorded, because it is where an older install left its
    roster (see retire_roster_install)."""
    base = root / tool.project_dir
    return replace(
        tool,
        label=f"{tool.label} — project {root.name}/",
        config_root=base,
        skills_dir=base / "skills",
        agents_dir=(base / "agents") if tool.agents_dir else None,
        roster_file=(root / "AGENTS.md") if tool.agent_style in ("roster_md", "codex_toml") else None,
        also_reads=tuple(root / rel for rel in tool.project_also_reads),
    )

def refuse_shared_project_dir(tool: Tool, agents: dict):
    """Per project, `shared` and `antigravity` both live in `.agents/` and write
    the SAME agent paths in different formats, so the second install would
    replace the first's files. Measured on agy 1.3.3: a body without
    frontmatter is not loaded as an agent, so `--agent NAME` silently gets the
    global agent of that name if there is one, else agy's main agent — either
    way not the project's. Refuse the mix instead of picking a winner
    silently. Call only for project installs: globally the two tools
    use different directories."""
    other = shared_dir_owner(tool, agents)
    if other:
        where = f"{tool.project_dir}/{tool.agents_dir.name}"
        fail(f"this project already holds the {other} install.",
             f"{tool.key} and {other} write the same agent files in {where}, in different "
             f"formats; the second would replace the first.",
             f"Use one of them per project, or remove {where} first.", refused=True)


def shared_dir_owner(tool: Tool, agents: dict) -> Optional[str]:
    """The key of ANOTHER tool whose agent files already occupy this tool's
    agents_dir, told apart by format (frontmatter or not); None if the dir is
    empty, already this tool's, or not shared with any other tool — a tool
    alone in its dir may find an older install of ITSELF there, in another
    format (Codex's pre-TOML roster bodies), and that is a migration, not a
    clash."""
    neighbours = [t.key for t in TOOLS
                  if t.key != tool.key and t.project_dir == tool.project_dir]
    if not neighbours or not tool.agents_dir or not tool.agents_dir.is_dir():
        return None
    wants_frontmatter = tool.agent_style != "roster_md"
    for name in sorted(agents):
        f = tool.agents_dir / f"{name}.md"
        if not f.is_file():
            continue
        if f.read_text(encoding="utf-8").startswith("---\n") == wants_frontmatter:
            return None
        return neighbours[0]
    return None


AGENT_SUFFIX = {"kiro_json": ".json", "codex_toml": ".toml"}


def agent_suffix(tool: Tool) -> str:
    return AGENT_SUFFIX.get(tool.agent_style, ".md")


ROSTER_BEGIN = "<!-- BEGIN:local-agents -->"
ROSTER_END = "<!-- END:local-agents -->"

TOOLS_BY_KEY = {t.key: t for t in TOOLS}

# --------------------------------------------------------------------------- #
# Errors
#
# One form, to stderr, in at most three parts: what is wrong, what was found,
# and a command that works. `error:` is something that cannot be done (exit 1);
# `refused:` is something that could be done and is not safe to (exit 2), and
# it always ends by saying nothing was changed. The codes are the ones
# update.py and the launcher document: a script around any of the three reads
# them alike. A mistyped argument is an error, not a refusal — argparse's own
# exit code is 2, so the parser below overrides it.
# --------------------------------------------------------------------------- #
OK, ERROR, REFUSED = 0, 1, 2


def listed(label: str, items) -> str:
    """`Label: a, b, c`, folded at 80 columns under the first item."""
    import textwrap
    return textwrap.fill(f"{label}: {', '.join(items)}", width=78, initial_indent="  ",
                         subsequent_indent=" " * (len(label) + 4), break_long_words=False,
                         break_on_hyphens=False)


def did_you_mean(word: str, known) -> list:
    import difflib
    close = difflib.get_close_matches(word, list(known), n=3, cutoff=0.6)
    return [f"  Did you mean: {', '.join(close)}"] if close else []


def fail(what: str, *detail: str, hint: str = "", refused: bool = False):
    """Say what is wrong and stop. `detail` lines that are already laid out
    (they start with two spaces) are printed as they are; the rest are folded."""
    import textwrap
    def fold(text: str, first: str) -> str:
        # A long path cannot be folded, and folding around it strands the words before it.
        if any(len(w) > 50 for w in text.split()):
            return first + text
        return textwrap.fill(text, width=78, initial_indent=first, subsequent_indent="  ",
                             break_long_words=False, break_on_hyphens=False)

    lines = [fold(what, "refused: " if refused else "error: ")]
    for d in detail:
        lines.append(d if d.startswith("  ") else fold(d, "  "))
    if hint:
        lines.append(f"  {hint}" if len(hint) + 2 <= 80 or ": " not in hint
                     else f"  {hint.split(': ', 1)[0]}:\n    {hint.split(': ', 1)[1]}")
    if refused:
        lines.append("  Nothing was changed.")
    print("\n".join(lines), file=sys.stderr)
    sys.exit(REFUSED if refused else ERROR)


class Parser(argparse.ArgumentParser):
    """A usage error is an error (1), not a refusal (2)."""
    def error(self, message):
        name = Path(self.prog).name
        helps = command("install", "--help") if name == "install.py" else f"{script(name)} --help"
        print(f"error: {message}\n  Try: {helps}", file=sys.stderr)
        sys.exit(ERROR)


# --------------------------------------------------------------------------- #
# The command to run next, as THIS person can type it
#
# Every `Try:` and `Next:` goes through command(). Someone who came in through
# a launcher (`npx github:…/local-hero update`) never sees install.py: telling
# them to run `./install.py --refresh` is telling them to run a file they do
# not know they have. So whoever is in front says how it was typed, in one
# environment variable, and the same intent comes out in that grammar:
#
#   unset             the scripts' own flags       ./install.py --refresh
#   a prefix          the verbs of update.py       npx github:…/local-hero update
#   "-"               the verbs, with no prefix    `update`
#
# update.py sets it for itself and for the install.py it runs; a launcher that
# knows its own name sets it first. "-" is a launcher that did not say: the
# verb alone is less than the whole command, and it is not a wrong one.
# --------------------------------------------------------------------------- #
FRONT_ENV = "LOCAL_AGENTS_FRONT"
SELF_DIR = Path(__file__).resolve().parent
VERBS = {"refresh": "update", "install": "bootstrap", "status": "bootstrap --status",
         "uninstall": "bootstrap --uninstall", "list": "bootstrap --list", "menu": "bootstrap"}
FLAGS = {"refresh": "--refresh", "install": "", "status": "--status",
         "uninstall": "--uninstall", "list": "--list", "menu": ""}


def script(name: str = "install.py") -> str:
    """One of the catalog's scripts as it can be typed from where the person
    is: `./install.py` inside the catalog, its path from anywhere else."""
    try:
        here = Path.cwd().resolve() == SELF_DIR
    except OSError:
        here = False
    return f"./{name}" if here else shell_arg(show_path(SELF_DIR / name))


def command(intent: str, *args: str) -> str:
    """The command for `intent` (a key of FLAGS, or "default"), with `args`."""
    args = [a.strip() for a in args if a and a.strip()]
    front = os.environ.get(FRONT_ENV, "").strip()
    if front and intent in VERBS:
        verb = VERBS[intent]
        if intent == "refresh" and args:
            verb = "bootstrap --refresh"    # `update` takes no options and refreshes the home installs only
        text = " ".join([verb, *args])
        return f"`{text}`" if front == "-" else f"{front} {text}"
    if intent == "default":
        return " ".join([script("default_agent.py"), *args])
    return " ".join(x for x in (script(), FLAGS[intent], *args) if x)


# --------------------------------------------------------------------------- #
# Catalog discovery
# --------------------------------------------------------------------------- #
@dataclass
class Skill:
    name: str          # folder name
    agent: Optional[str]  # owning agent folder, or None if top-level
    path: Path         # the skill directory (contains SKILL.md)
    id: Optional[str] = None  # metadata.local-agents-id — who it is, whatever its name

    @property
    def qualified(self) -> str:
        return f"{self.agent}:{self.name}" if self.agent else self.name


@dataclass
class Agent:
    name: str
    path: Path            # the agent directory
    agents_md: Path       # its AGENTS.md
    skills: list          # list[Skill]


def discover(catalog: Path):
    """Find agents (dirs with AGENTS.md) and every skill (dirs with SKILL.md),
    and make this catalog the one ownership is judged against."""
    global CATALOG_ROOT
    agents, all_skills = scan_catalog(catalog)
    CATALOG_ROOT = catalog
    SKILLS_BY_ID.clear()
    SKILLS_BY_ID.update({s.id: s for s in all_skills if s.id})
    return agents, all_skills


def scan_catalog(catalog: Path):
    """discover() without side effects: also used to read an OLD commit of the
    catalog, which must not replace the current one."""
    agents: dict[str, Agent] = {}
    all_skills: list[Skill] = []

    for agents_md in sorted(catalog.glob("*/AGENTS.md")):
        agent_dir = agents_md.parent
        name = agent_dir.name
        skills = []
        for skill_md in sorted(agent_dir.glob("skills/*/SKILL.md")):
            sk = Skill(name=skill_md.parent.name, agent=name, path=skill_md.parent,
                       id=skill_id_at(skill_md.parent))
            skills.append(sk)
            all_skills.append(sk)
        agents[name] = Agent(name=name, path=agent_dir, agents_md=agents_md, skills=skills)

    # Also catch any skill folders not under a discovered agent (defensive).
    for skill_md in sorted(catalog.glob("skills/*/SKILL.md")):
        all_skills.append(Skill(name=skill_md.parent.name, agent=None, path=skill_md.parent,
                                id=skill_id_at(skill_md.parent)))

    return agents, all_skills


# --------------------------------------------------------------------------- #
# Frontmatter / description helpers (no YAML dependency)
# --------------------------------------------------------------------------- #
def agent_description(agents_md_text: str) -> str:
    """First sentence of the first real paragraph after the H1 — used as the
    tool-facing description when the target format needs one."""
    lines = agents_md_text.splitlines()
    para = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#"):
            if para:
                break
            continue
        para.append(s)
    text = " ".join(para).strip()
    if not text:
        return "Catalog agent."
    # first sentence-ish, capped so frontmatter stays tidy
    sentence = re.split(r"(?<=[.!?])\s", text)[0]
    return (sentence[:197] + "...") if len(sentence) > 200 else sentence


def split_frontmatter(text: str):
    """Split a leading `---`…`---` YAML block from the body. Returns (meta, body).
    Handles simple `key: value` lines and block scalars (`key: |`)."""
    m = re.match(r"---\n(.*?)\n---\n?", text, re.DOTALL)
    if not m:
        return {}, text
    fm_lines, body = m.group(1).split("\n"), text[m.end():]
    meta, i = {}, 0
    while i < len(fm_lines):
        km = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", fm_lines[i])
        if not km:
            i += 1
            continue
        key, val = km.group(1), km.group(2).strip()
        if val in ("|", ">", "|-", ">-", "|+", ">+"):  # block scalar
            i += 1
            block, base = [], None
            while i < len(fm_lines):
                ln = fm_lines[i]
                if ln.strip() == "":
                    block.append("")
                    i += 1
                    continue
                indent = len(ln) - len(ln.lstrip())
                if indent == 0:
                    break
                base = indent if base is None else base
                block.append(ln[base:])
                i += 1
            meta[key] = "\n".join(block).strip("\n")
        else:
            meta[key] = val.strip('"')
            i += 1
    return meta, body


def yaml_description(desc: str) -> str:
    """Render a description as a YAML value — block scalar if it has newlines."""
    if "\n" in desc:
        indented = "\n".join(("  " + ln) if ln else "" for ln in desc.split("\n"))
        return "description: |\n" + indented
    return f"description: {desc}"


def flatten_description(skill_md_text: str) -> str:
    """Write a block-scalar `description:` (`>` / `|`) as ONE double-quoted line.

    Measured on kiro-cli 2.29.1: Kiro reads only the first line of the
    description, so `description: >` reached it EMPTY — and the description is
    the trigger that tells an agent when to load the skill, so in Kiro no
    catalog skill ever fired. A one-line quoted scalar means the same to every
    YAML parser, so it is written for every host; the catalog sources keep the
    readable block form. Lines are joined with spaces (folding); a quoted
    string is JSON-escaped, which is valid YAML."""
    if not skill_md_text.startswith("---"):
        return skill_md_text
    end = skill_md_text.find("\n---", 3)
    if end == -1:
        return skill_md_text
    lines = skill_md_text[:end].split("\n")
    out, i = [], 0
    while i < len(lines):
        m = re.match(r"^description:\s*([>|][+-]?)\s*$", lines[i])
        if not m:
            out.append(lines[i])
            i += 1
            continue
        i += 1
        block = []
        while i < len(lines) and (lines[i].strip() == "" or lines[i][:1] in (" ", "\t")):
            block.append(lines[i].strip())
            i += 1
        folded = " ".join(part for part in block if part)
        out.append(f"description: {json.dumps(folded, ensure_ascii=False)}")
    return "\n".join(out) + skill_md_text[end:]


def rewrite_skill_name(skill_md_text: str, new_name: str) -> str:
    """Replace the `name:` value inside the first frontmatter block, so a
    renamed skill's metadata matches its new folder (tools key on both)."""
    if not skill_md_text.startswith("---"):
        return skill_md_text
    end = skill_md_text.find("\n---", 3)
    if end == -1:
        return skill_md_text
    head, rest = skill_md_text[:end], skill_md_text[end:]
    head = re.sub(r"(?m)^(\s*name:).*$", rf"\1 {new_name}", head, count=1)
    return head + rest


# --------------------------------------------------------------------------- #
# Rendering an agent file per tool format
# --------------------------------------------------------------------------- #
# What an agent may DO, declared once in its frontmatter (`access:`) and
# rendered into whatever each host can enforce. Two tiers on purpose: `read`
# for advisors (they read, search, fetch and delegate; they never edit or run),
# `full` for builders. Finer promises — "qa edits only tests", "security never
# exfiltrates" — cannot be expressed by tool name on any host and stay in the
# prompt, guarded by the behavioural harness. A tier is a floor, not the rule.
ACCESS_TIERS = ("read", "full")
# `Skill` loads an instruction file; it writes and runs nothing. Without it a
# read-tier agent cannot load its own skills: measured on Claude Code 2.1.299
# (harness run 20261014-003338), visionary and eng-manager loaded none in 8 of
# 8 prompts that called for one. They found the file with Glob and Read only
# because the harness copies skills into its workspace; in a real project the
# skills live in ~/.claude/skills, out of a Glob's reach.
CLAUDE_READ_TOOLS = "Read, Grep, Glob, WebFetch, WebSearch, Agent, Skill"
# Measured on kiro-cli 2.29.1, which enforces this list (an agent with
# ["read"] could not write). `full` is every tool, as a full agent inherits
# everything in Claude Code. `read` mirrors CLAUDE_READ_TOOLS: read, search,
# fetch and delegate (skills arrive as `skill://` resources, not as a tool). `code` is left out because its AST rewrite edits files;
# `subagent` stays, and a delegated agent can write — the same as `Agent` in
# Claude Code, and what rule 16 means by "delegate".
# `kiro-cli agent validate` accepts unknown tags, so it cannot check this.
#
# Kiro has two agent formats and upgrades the old one by itself (B-099). A
# file with `allowedTools` is rewritten in place at every launch of the CLI:
# it gains a `permissions` block and, since 3.x, a `kiroUpgrade` marker with
# two hashes of Kiro's own. Measured on 2026-11-11, three ways of living with
# that, two of them wrong:
#   1. Writing the shape 2.29.1 left: 3.2.0 rewrote it again five minutes on.
#   2. Writing `permissions` and no `allowedTools`, which `agent upgrade
#      --dry-run` calls "v3-only" and leaves alone: `kiro-cli chat --agent`
#      then fails with "Mode not found". The agents were unusable.
#   3. Writing the 2.x file and letting Kiro upgrade it — the only file Kiro
#      itself produces, and the only one seen to start. This is what we do.
# So the host's rewrite is expected, and KIRO_HOST_KEYS are the fields it
# owns: agent_hash() leaves them out, which keeps a file Kiro upgraded ours
# to update instead of "edited by hand" (how Kiro once ran a 19-day-old
# catalog). `tools` is already sorted and carries `web`, the way Kiro leaves
# it, so the upgrade has nothing to change in a field we do compare.
KIRO_TOOLS = {"read": ["glob", "grep", "read", "subagent", "web", "web_fetch", "web_search"],
              "full": ["*"]}
KIRO_HOST_KEYS = ("permissions", "kiroUpgrade")
# Antigravity needs `tools:` on EVERY agent, not only the read tier. Measured
# against agy 1.3.3: with the field omitted a subagent gets a minimal default
# (view_file, read_url_content, search_web, ...) — no grep, no write, no shell —
# so a builder would silently lose the ability to build. Every name below was
# accepted by agy's tool registry; an unknown one aborts the agent at startup
# ("tool ... not found in registry"), which is why `search_in_file` and
# `command_status` are absent although the binary mentions them.
# `full` mirrors what agy's main agent exposes, plus the search tools.
AGY_TOOLS = {
    "read": ["view_file", "list_dir", "find_by_name", "grep_search",
             "read_url_content", "search_web", "invoke_subagent"],
    "full": ["view_file", "list_dir", "find_by_name", "grep_search",
             "write_to_file", "replace_file_content", "multi_replace_file_content",
             "run_command", "read_url_content", "search_web", "invoke_subagent",
             "define_subagent", "manage_subagents", "manage_task", "send_message",
             "schedule", "ask_question"],
}


# --------------------------------------------------------------------------- #
# Shell-write guard (B-083) — optional, Claude Code only
# --------------------------------------------------------------------------- #
# The CORE says files change only through the editing tool; in Claude Code's
# acceptEdits, auto and bypassPermissions modes nothing enforces it, and auto
# and bypass tell the model to edit with sed and heredocs. `--shell-write-guard`
# installs scripts/shell_write_guard.py and hooks it into every `full` agent's
# frontmatter as a PreToolUse hook on Bash. The frontmatter `hooks:` field is
# documented for subagent files and fires both when the agent is spawned and
# when it runs as the main session (`--agent`). A PROJECT agent's frontmatter
# hooks need the folder trusted and never run under `-p` (documented), so a
# project install is guarded only in a trusted interactive session.
# Kiro has `hooks.preToolUse` and `toolsSettings` in its agent JSON (strings
# in kiro-cli-chat), but how a hook blocks there is not verified: not rendered.
# Off by default. The choice is recorded in the stamp, so `--refresh` keeps it
# and `--status` judges agent files against it.
GUARD_SOURCE = Path(__file__).resolve().parent / "scripts" / "shell_write_guard.py"
GUARD_REL = Path("hooks") / "local-agents" / "shell_write_guard.py"
GUARD_STYLES = ("claude_md",)
SHELL_GUARD_CHOICE: Optional[bool] = None   # set by --shell-write-guard / --no-…

# Verify hook (B-084) — optional, Claude Code only
# The loop-engineering stop rule a machine checks: a turn does not end with
# the project's check red unless the agent has seen it. `--verify-hook CMD`
# installs scripts/verify_before_stop.py and hooks it into every `full`
# agent's frontmatter as a `Stop` hook; Claude Code turns a subagent's `Stop`
# into `SubagentStop` (documented), so it fires when the agent finishes a
# delegation and when it runs as the main session. The check is DECLARED by
# each repo in `.local-agents/verify` (the agents install globally; one
# command cannot fit every repo), and `--verify-hook CMD` records CMD as the
# default for repos that declare nothing. The catalog never infers it from
# `package.json` or a `Makefile`: a hook that guesses fails where nobody is
# watching. The script blocks once per turn and fails open (see its docstring).
# Other hosts, not rendered yet: Codex documents Stop/SubagentStop with the
# same input (`stop_hook_active`) and the same blocking output, and its
# SubagentStop matcher filters by `agent_type`, so this script could be
# scoped to the catalog's agents unchanged — but Codex hooks live in the
# user's `hooks.json`/`config.toml`, which the installer does not touch, and
# whether an empty stdout on exit 0 is accepted there is unmeasured.
# opencode's `session.idle` is an observer event with no documented way to
# block a stop; Kiro and Antigravity have no known stop event.
VERIFY_SOURCE = Path(__file__).resolve().parent / "scripts" / "verify_before_stop.py"
VERIFY_REL = Path("hooks") / "local-agents" / "verify_before_stop.py"
VERIFY_CHOICE = None   # None: as last install; False: off; "": on; "CMD": on with that default


def hooks_frontmatter(guard: Optional[str], verify: Optional[str]) -> str:
    """The `hooks:` block of a `full` Claude Code agent's frontmatter, or ""
    when neither hook is on. Both hooks share the one block."""
    parts = []
    if guard:
        parts.append("  PreToolUse:\n"
                     "    - matcher: \"Bash\"\n"
                     "      hooks:\n"
                     "        - type: command\n"
                     f"          command: {json.dumps(guard)}\n")
    if verify:
        parts.append("  Stop:\n"
                     "    - hooks:\n"
                     "        - type: command\n"
                     f"          command: {json.dumps(verify)}\n")
    return "hooks:\n" + "".join(parts) if parts else ""


def guard_on(tool: Tool) -> bool:
    """This run's choice when one was given, else what the last install chose."""
    if tool.agent_style not in GUARD_STYLES:
        return False
    if SHELL_GUARD_CHOICE is not None:
        return SHELL_GUARD_CHOICE
    return bool((run_for(tool).stamp or {}).get("shell_write_guard"))


def guard_path(tool: Tool) -> Path:
    return tool.config_root / GUARD_REL


def guard_command(tool: Tool) -> Optional[str]:
    """The hook command, or None when the guard is off. A project install
    points at the copy inside the repo through the variable Claude Code exports
    to every hook, so the file still works after the repo moves or is cloned."""
    if not guard_on(tool):
        return None
    home = TOOLS_BY_KEY.get(tool.key)
    if home is not None and tool.config_root != home.config_root:
        return f'python3 "$CLAUDE_PROJECT_DIR/{tool.project_dir}/{GUARD_REL.as_posix()}"'
    return f'python3 "{guard_path(tool)}"'


def sync_guard(tool: Tool, dry_run: bool):
    """Put the script in place when the guard is on; take OUR copy away when it
    is off. A file we did not write (its hash is not the recorded one) stays."""
    if tool.agent_style not in GUARD_STYLES:
        return
    dest = guard_path(tool)
    if guard_on(tool):
        REPORT.did("installed" if not dest.is_file() else
                   "unchanged" if file_hash(dest) == file_hash(GUARD_SOURCE) else "updated",
                   "hook", "shell-write guard", tool=tool)
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(GUARD_SOURCE.read_bytes())
        return
    recorded = (run_for(tool).stamp or {}).get("shell_write_guard_sha256")
    if dest.is_file() and recorded and file_hash(dest) == recorded:
        REPORT.did("removed", "hook", "shell-write guard", why="--no-shell-write-guard", tool=tool)
        if not dry_run:
            dest.unlink()


def script_state(dest: Path, source: Path) -> str:
    """Whether a hook script on disk is the catalog's current one."""
    if not dest.is_file():
        return "script MISSING: the agents' hook fails open; reinstall"
    if file_hash(dest) != file_hash(source):
        return "script out of date: --refresh updates it"
    return "script current"


def guard_status(tool: Tool) -> str:
    """One line for --status: whether the guard is on, and whether the script
    on disk is the catalog's current one."""
    dest = guard_path(tool)
    if not guard_on(tool):
        extra = f" (a copy is still at {dest})" if dest.is_file() else ""
        return f"shell-write guard off{extra}"
    return f"shell-write guard on, {script_state(dest, GUARD_SOURCE)}, {show_path(dest)}"


def verify_on(tool: Tool) -> bool:
    """This run's choice when one was given, else what the last install chose."""
    if tool.agent_style not in GUARD_STYLES:
        return False
    if VERIFY_CHOICE is not None:
        return VERIFY_CHOICE is not False
    return bool((run_for(tool).stamp or {}).get("verify_hook"))


def verify_default(tool: Tool) -> str:
    """The default check for repos that declare none: CMD when this run gave
    one, else the recorded one (a bare --verify-hook keeps it); "" for none."""
    if not verify_on(tool):
        return ""
    if isinstance(VERIFY_CHOICE, str) and VERIFY_CHOICE.strip():
        return VERIFY_CHOICE.strip()
    return str((run_for(tool).stamp or {}).get("verify_hook_default") or "")


def verify_path(tool: Tool) -> Path:
    return tool.config_root / VERIFY_REL


def verify_command(tool: Tool) -> Optional[str]:
    """The hook command, or None when the verify hook is off. The default
    check, if any, goes on argv shell-quoted; a project install points at the
    copy inside the repo, as guard_command does."""
    if not verify_on(tool):
        return None
    home = TOOLS_BY_KEY.get(tool.key)
    if home is not None and tool.config_root != home.config_root:
        script = f'"$CLAUDE_PROJECT_DIR/{tool.project_dir}/{VERIFY_REL.as_posix()}"'
    else:
        script = f'"{verify_path(tool)}"'
    default = verify_default(tool)
    return f"python3 {script}" + (f" {shlex.quote(default)}" if default else "")


def sync_verify(tool: Tool, dry_run: bool):
    """Put the script in place when the hook is on; take OUR copy away when it
    is off. A file we did not write (its hash is not the recorded one) stays."""
    if tool.agent_style not in GUARD_STYLES:
        return
    dest = verify_path(tool)
    if verify_on(tool):
        REPORT.did("installed" if not dest.is_file() else
                   "unchanged" if file_hash(dest) == file_hash(VERIFY_SOURCE) else "updated",
                   "hook", "verify hook", tool=tool)
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(VERIFY_SOURCE.read_bytes())
        return
    recorded = (run_for(tool).stamp or {}).get("verify_hook_sha256")
    if dest.is_file() and recorded and file_hash(dest) == recorded:
        REPORT.did("removed", "hook", "verify hook", why="--no-verify-hook", tool=tool)
        if not dry_run:
            dest.unlink()


def verify_status(tool: Tool) -> str:
    """One line for --status: whether the verify hook is on, what it runs, and
    whether the script on disk is the catalog's current one."""
    dest = verify_path(tool)
    if not verify_on(tool):
        extra = f" (a copy is still at {dest})" if dest.is_file() else ""
        return f"verify hook off{extra}"
    default = verify_default(tool)
    what = (f"runs each repo's .local-agents/verify, default {default!r}" if default
            else "runs each repo's .local-agents/verify, no default")
    return f"verify hook on, {what}, {script_state(dest, VERIFY_SOURCE)}, {show_path(dest)}"


def access_of(meta: dict) -> str:
    tier = (meta or {}).get("access", "full")
    if tier not in ACCESS_TIERS:
        fail(f"the catalog is not valid: unknown access tier {tier!r}.",
             f"Expected one of: {', '.join(ACCESS_TIERS)}", hint=f"Try: {script('validate.py')}")
    return tier


def render_agent(tool: Tool, name: str, body: str, description: str,
                 skill_names: list, meta: dict = None, guard: Optional[str] = None,
                 verify: Optional[str] = None) -> tuple:
    """Return (destination_path, file_contents) for the agent in this tool's
    format. `meta` is the catalog AGENTS.md frontmatter (description/model/…).
    `guard` is the shell-write guard's hook command and `verify` the verify
    hook's, each None when off (guard_command, verify_command). Add a branch
    here only for a genuinely new file format."""
    meta = meta or {}
    desc = meta.get("description") or description
    tier = access_of(meta)
    # A read-only agent has to KNOW it is read-only, or it discovers it when
    # an edit is refused and narrates around the gap. Measured: with the tool
    # list alone, architect could no longer edit but never said so. The note
    # goes into the body on every host, enforced or not.
    if tier == "read":
        body = ("> **Access: read-only.** On this host you read, search, fetch, "
                "load your skills and delegate; you do not edit files or run commands. When a task needs "
                "a change made, say so in one line and hand the exact change to the "
                "user or to the agent that builds — never narrate an edit you cannot "
                "make.\n\n") + body
    if tool.agent_style == "claude_md":
        # `tools:` is an allowlist; omitted, the subagent inherits every tool.
        tools_line = f"tools: {CLAUDE_READ_TOOLS}\n" if tier == "read" else ""
        # No `memory:` for the read tier. Measured on Claude Code 2.1.296: an
        # agent with memory gets Edit and Write ADDED to its allowlist, with no
        # limit to its memory dir — a probe with only read tools plus
        # `memory: local` wrote a file in the working directory. Every agent
        # was installed with `memory: user`, so visionary and eng-manager could
        # edit anything and rule 16 did not hold on this host. Without memory
        # the tools are exactly CLAUDE_READ_TOOLS.
        memory_line = "" if tier == "read" else f"memory: {meta.get('memory', 'user')}\n"
        # B-083/B-084: the hooks, only where the agent builds. The read tier
        # has no Bash to guard and no work a check could fail.
        hooks_lines = hooks_frontmatter(guard, verify) if tier == "full" else ""
        fm = ("---\n"
              f"name: {name}\n"
              f"{yaml_description(desc)}\n"
              f"model: {meta.get('model', 'inherit')}\n"
              f"{memory_line}"
              f"{tools_line}"
              f"{hooks_lines}"
              "---\n\n")
        return tool.agents_dir / f"{name}.md", fm + body
    if tool.agent_style == "opencode_md":
        perm = "permission:\n  edit: deny\n  bash: deny\n" if tier == "read" else ""
        fm = f"---\n{yaml_description(desc)}\nmode: {meta.get('mode', 'primary')}\n{perm}---\n\n"
        return tool.agents_dir / f"{name}.md", fm + body
    if tool.agent_style == "kiro_json":
        obj = {
            "name": name,
            "description": desc,
            "prompt": body,
            # Kiro tool tags, not free-form names: `write` already covers editing
            # and deleting, and there is no `edit` tool — an unknown tag is a
            # config error, so keep KIRO_TOOLS in sync with USAGE.md's recipe.
            "tools": KIRO_TOOLS[tier],
            "allowedTools": ["read"],
            "resources": [f"skill://~/.kiro/skills/{s}/SKILL.md" for s in skill_names],
            # Nothing of KIRO_HOST_KEYS: Kiro adds those itself at its next launch.
        }
        return tool.agents_dir / f"{name}.json", json.dumps(obj, indent=2, ensure_ascii=False)
    if tool.agent_style == "codex_toml":
        # Measured on codex-cli 0.144.5: Codex loads one TOML per agent and
        # honours `sandbox_mode = "read-only"` when the session's sandbox comes
        # from config (`config.toml`, `-c sandbox_mode=...`), but the `--sandbox`
        # flag beats every agent file. `full` leaves sandbox_mode out, so the
        # agent inherits the sandbox the user chose instead of raising it.
        sandbox = 'sandbox_mode = "read-only"\n' if tier == "read" else ""
        # A literal string keeps the markdown byte-for-byte; it cannot hold
        # `'''` and a trailing quote would merge with the delimiter, so those
        # bodies fall back to an escaped basic string.
        if "'''" in body or body.endswith("'"):
            instructions = f"developer_instructions = {json.dumps(body, ensure_ascii=False)}\n"
        else:
            instructions = f"developer_instructions = '''\n{body}'''\n"
        toml = (f"name = {json.dumps(name)}\n"
                f"description = {json.dumps(desc, ensure_ascii=False)}\n"
                f"{sandbox}{instructions}")
        return tool.agents_dir / f"{name}.toml", toml
    if tool.agent_style == "roster_md":
        # No frontmatter: nothing parses it here. The lead paragraph states what
        # the file is so a model that opens it knows immediately — including
        # its access tier, since a roster host has nothing to enforce it with.
        head = (f"# `{name}` agent\n\n"
                f"Adopt this identity fully when the task matches its row in the "
                f"agent catalog (`../AGENTS.md`). Load the skills it references "
                f"when their triggers fire.\n\n---\n\n")
        return tool.agents_dir / f"{name}.md", head + body
    if tool.agent_style == "antigravity_md":
        # `tools:` is an explicit allowlist and is always written (see
        # AGY_TOOLS). Antigravity's own model aliases are `flash` / `pro`, so a
        # catalog model name never maps — inherit.
        fm = ("---\n"
              f"name: {name}\n"
              f"{yaml_description(desc)}\n"
              "model: inherit\n"
              f"tools: [{', '.join(AGY_TOOLS[tier])}]\n"
              "---\n\n")
        return tool.agents_dir / f"{name}.md", fm + body
    raise ValueError(f"Tool {tool.key} has no agent format")


# --------------------------------------------------------------------------- #
# Conflict resolution
# --------------------------------------------------------------------------- #
def _auto_rename(exists_fn, base: str) -> str:
    i = 2
    while exists_fn(f"{base}-{i}"):
        i += 1
    return f"{base}-{i}"


# --------------------------------------------------------------------------- #
# Install operations
# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
# Ownership: what in a host's dir is ours (B-058)
#
# A host's skill dir is shared — `npx skills` writes there too, and 26 of our 48
# skill names already exist in public registries (measured 2026-10-13, B-053).
# A name decides nothing. A skill is OURS when it carries our id in its
# metadata; an installed file is INTACT when its hash still matches the one the
# stamp recorded when we wrote it. Agents carry no id — every host has its own
# format — so for them the stamp is the only witness.
#
#   ours     our id, at its own name, untouched since we wrote it → update freely
#   edited   our id, but changed since we wrote it → never overwritten silently
#   foreign  no id of ours → never touched unless the user says so
#   link     a symlink (`npx skills` links each host to its own copy) → never
#            followed, never deleted
#   retired  our id under another name, or an id the catalog no longer has: an
#            old copy of a renamed or removed skill → reported, for the user to delete
# --------------------------------------------------------------------------- #
OURS, EDITED, FOREIGN, LINK, RETIRED = "ours", "edited", "foreign", "link", "retired"
ELSEWHERE = "elsewhere"   # our only copy of a skill, under another name (a rename install)
SKILLS_BY_ID: dict = {}   # filled by discover()
CATALOG_ROOT: Optional[Path] = None
_SKILL_ID = re.compile(r'^\s+local-agents-id:\s*"?([a-z0-9-]+)"?\s*$', re.M)
# Every catalog skill had this author before ids existed: the one sign that an
# id-less copy from an older install is ours.
_OUR_AUTHOR = re.compile(r"^\s+author:\s*jrodrigopuca\s*$", re.M)


def _frontmatter(md: Path) -> str:
    try:
        m = re.match(r"---\n(.*?)\n---", md.read_text(encoding="utf-8"), re.DOTALL)
    except (OSError, UnicodeDecodeError):
        return ""
    return m.group(1) if m else ""


def skill_id_at(d: Path) -> Optional[str]:
    m = _SKILL_ID.search(_frontmatter(d / "SKILL.md"))
    return m.group(1) if m else None


UNREADABLE = "unreadable"   # never equal to a recorded hash: an unreadable copy is left alone


def tree_hash(d: Path) -> str:
    """Hash of what a skill folder holds. Dotfiles are left out — Finder's
    .DS_Store would otherwise turn every opened skill into "edited" — and links
    inside are not followed, so nothing outside the folder is ever read."""
    h = hashlib.sha256()
    try:
        files = []
        for root, dirs, names in os.walk(d, followlinks=False):
            dirs[:] = sorted(x for x in dirs if not x.startswith("."))
            files += [Path(root) / n for n in names if not n.startswith(".")]
        for f in sorted(files, key=lambda p: p.relative_to(d).as_posix()):
            if f.is_symlink():
                continue
            h.update(f.relative_to(d).as_posix().encode() + b"\0" + f.read_bytes() + b"\0")
    except OSError:
        return UNREADABLE
    return h.hexdigest()


def file_hash(f: Path) -> str:
    try:
        return hashlib.sha256(f.read_bytes()).hexdigest()
    except OSError:
        return UNREADABLE


def agent_text_hash(text: str, name: str) -> str:
    """The hash of an agent file as WE wrote it. For a Kiro JSON agent the
    fields the host adds on its own (KIRO_HOST_KEYS) are left out and the rest
    is hashed in a canonical form: Kiro upgrading the file is not somebody
    editing it. Any other file, or a JSON that does not parse, is hashed as
    it is."""
    if name.endswith(".json"):
        try:
            obj = json.loads(text)
        except ValueError:
            obj = None
        if isinstance(obj, dict):
            ours = {k: v for k, v in obj.items() if k not in KIRO_HOST_KEYS}
            text = json.dumps(ours, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def agent_hash(f: Path) -> str:
    try:
        return agent_text_hash(f.read_text(encoding="utf-8"), f.name)
    except (OSError, UnicodeDecodeError):
        return UNREADABLE


@dataclass
class Run:
    """One install run on one host: the stamp as it was BEFORE the run (what we
    wrote last time), and what this run wrote. Kept per host dir so the many
    paths that install (suite, one agent, one skill, menus) share it without
    threading it through every call."""
    stamp: Optional[dict]
    skills_written: set = field(default_factory=set)
    agents_written: set = field(default_factory=set)


_RUNS: dict = {}


def run_for(tool: Tool) -> Run:
    if tool.config_root not in _RUNS:
        stamp = read_manifest(tool)
        if stamp is not None and ("skills" not in stamp or "agents" not in stamp):
            stamp = with_legacy_records(tool, stamp)
        _RUNS[tool.config_root] = Run(stamp)
    return _RUNS[tool.config_root]


def with_legacy_records(tool: Tool, stamp: dict) -> dict:
    """A stamp from before B-058 says which commit was installed but records no
    hashes. Rebuild them: render that commit of the catalog the way the
    installer does, and take the hash of each file as it would have been
    written. A copy that still matches is ours and untouched; one that does not
    was edited by hand, and is left alone. If the renderer changed since that
    commit, an untouched copy reads as edited — the safe side: it is kept, and
    --status says so."""
    rebuilt = legacy_records(tool, stamp.get("catalog_commit"))
    if rebuilt is None:
        REPORT.note("installed before install records existed, from a commit this catalog "
                    "cannot rebuild: hand edits there cannot be told apart, and catalog files "
                    "are updated.", tool=tool)
        return {**stamp, "suite": stamp.get("suite", True)}
    skills, agents = rebuilt
    # Before B-058 every refresh reinstalled the whole catalog; a stamp from
    # then means exactly that.
    return {**stamp, "skills": stamp.get("skills", skills),
            "agents": stamp.get("agents", agents), "suite": stamp.get("suite", True)}


def legacy_records(tool: Tool, commit: Optional[str]):
    if not commit or CATALOG_ROOT is None:
        return None
    if git(CATALOG_ROOT, "cat-file", "-e", f"{commit}^{{commit}}") is None:
        return None
    tar = subprocess.run(["git", "-C", str(CATALOG_ROOT), "archive", "--format=tar", commit],
                         capture_output=True)
    if tar.returncode != 0:
        return None
    with tempfile.TemporaryDirectory() as tmp:
        old_root, expected = Path(tmp) / "catalog", Path(tmp) / "expected"
        with tarfile.open(fileobj=io.BytesIO(tar.stdout)) as tf:
            tf.extractall(old_root)
        old_agents, old_skills = scan_catalog(old_root)
        old_by_name = {s.name: s for s in old_skills}
        current_id = {s.name: s.id for s in SKILLS_BY_ID.values()}
        skills = {}
        if tool.skills_dir.is_dir():
            here = {d.name for d in tool.skills_dir.iterdir()
                    if d.name in old_by_name and not d.is_symlink() and (d / "SKILL.md").is_file()}
            for name in sorted(here):
                if not current_id.get(name):
                    continue
                src, dest = old_by_name[name], expected / name
                shutil.copytree(src.path, dest)
                md = dest / "SKILL.md"
                md.write_text(render_skill(md.read_text(encoding="utf-8"), src.agent, name, here),
                              encoding="utf-8")
                skills[current_id[name]] = {"name": name, "sha256": tree_hash(dest)}
        agents = {}
        if tool.agents_dir is not None and tool.agents_dir.is_dir():
            for name, ag in old_agents.items():
                try:
                    # fail() speaks before it stops; here the stop is expected
                    # and handled, so what it says must not reach the user.
                    with contextlib.redirect_stderr(io.StringIO()):
                        inherited, deps = resolve_deps(ag, old_agents, old_by_name)
                except SystemExit:
                    # A commit from before `inherits:` existed cannot be
                    # rendered by today's rules; it must not abort the refresh.
                    return None
                meta, desc, body = compose_agent(ag, inherited)
                dest, text = render_agent(tool, name, body, desc, sorted(s.name for s in deps), meta)
                if dest.exists():
                    agents[dest.name] = agent_text_hash(text, dest.name)
    return skills, agents


def classify_skill(d: Path, stamp: Optional[dict]) -> tuple:
    """(kind, catalog skill or None) for a folder in a host's skills dir."""
    if d.is_symlink():
        return LINK, None
    if not (d / "SKILL.md").is_file():
        return FOREIGN, None
    sid = skill_id_at(d)
    if sid is None:
        if not _OUR_AUTHOR.search(_frontmatter(d / "SKILL.md")):
            return FOREIGN, None
        # An id-less copy from before ids existed: ours by its author.
        by_name = {s.name: s for s in SKILLS_BY_ID.values()}
        if d.name not in by_name:
            return RETIRED, None
        sk = by_name[d.name]
        sid, kind = sk.id, OURS
    else:
        sk = SKILLS_BY_ID.get(sid)
        if sk is None:
            return RETIRED, None          # an id the catalog no longer has
        kind = OURS
        if sk.name != d.name:
            # Retired only when the real one is installed at its own name; else
            # this is our only copy, put elsewhere (`--on-conflict rename` next
            # to a foreign skill, or a catalog rename not yet installed) — not
            # something to tell the user to delete.
            own = d.parent / sk.name
            if not own.is_symlink() and (own / "SKILL.md").is_file() and skill_id_at(own) == sid:
                return RETIRED, sk
            kind = ELSEWHERE
    rec = ((stamp or {}).get("skills") or {}).get(sid)
    if rec and rec.get("name") == d.name and rec.get("sha256") != tree_hash(d):
        return EDITED, sk
    return kind, sk


def classify_agent(f: Path, agent_names: set, stamp: Optional[dict]) -> str:
    """Kind of an agent file in a host's agents dir. No stamp at all: nothing
    says we wrote it, so it is foreign. A stamp from before B-058 has no
    `agents` map: a catalog name counts as ours, once."""
    if f.is_symlink():
        return LINK
    if stamp is None:
        return FOREIGN
    recs = stamp.get("agents")
    if recs is None:
        return OURS if f.stem in agent_names else FOREIGN
    if f.name not in recs:
        return FOREIGN
    # file_hash too: a record written before agent_hash existed holds the raw
    # hash, and a file nobody touched since must not turn "edited" overnight.
    return OURS if recs[f.name] in (agent_hash(f), file_hash(f)) else EDITED


_SAFE = {
    FOREIGN: "not from this catalog",
    LINK: "a link to another tool's copy",
    EDITED: "edited by hand",
    "foreign agent": "not from this catalog",
}


def decide(kind: str, policy: str, interactive: bool, what: str) -> str:
    """write | skip | rename for an existing destination of this kind.

    `update` is --refresh: it brings OUR untouched files up to date and nothing
    else. `overwrite` is the user saying "replace it" — the only way something
    edited or foreign gets replaced. A link is never replaced: deleting it would
    break the tool that made it, and writing through it would rewrite its copy."""
    if kind in (OURS, RETIRED, ELSEWHERE):
        return "write"
    why = _SAFE["foreign agent"] if kind == FOREIGN and what.startswith("agent") else _SAFE[kind]
    if kind == LINK:
        REPORT.keep(what, _SAFE[LINK])
        return "skip"
    if policy == "overwrite":
        return "write"
    if policy == "rename" and kind == FOREIGN:
        return "rename"
    if policy == "ask" and interactive:
        choice = ask_conflict(what, kind)
        if choice != "skip":
            return choice
    REPORT.keep(what, why)
    return "skip"


def ask_conflict(what: str, kind: str) -> str:
    """The one question the menu asks about a file that is already there.
    Enter keeps it: the safe answer is the default, and it is shown as such."""
    theirs = kind == FOREIGN
    print(f"\n{what} " + ("is not from this catalog: something else has that name."
                           if theirs else "was edited by hand since it was installed."))
    options = ("  [k] keep " + ("it" if theirs else "your version") + " (default)   "
               "[r] replace with the catalog's" + ("\n  [n] install ours under another name" if theirs else ""))
    keys = "k, r or n" if theirs else "k or r"
    while True:
        print(options)
        try:
            ans = input("  > ").strip().lower()
        except EOFError:
            return "skip"                   # nobody there: keep, as without a terminal
        if ans in ("", "k", "keep", "s", "skip"):
            return "skip"
        if ans in ("r", "replace", "o", "overwrite"):
            return "write"
        if theirs and ans in ("n", "name", "rename"):
            return "rename"
        print(f"  Type {keys}.")


# --------------------------------------------------------------------------- #
# What a run did, said once
#
# Every path that installs, refreshes or uninstalls records what happened to
# each file here instead of printing it: installed, updated, unchanged, kept
# (with the reason) or removed. The run then says it the way a person reads
# it — one row per tool, the files it chose not to touch with the command that
# changes that, and one closing line. One line per file is for --verbose.
#
# It grew out of B-099: Kiro sat 19 days on an old catalog behind fifteen
# "left alone" lines lost among a few hundred. What a run did NOT do is the
# part that has to survive the scroll.
# --------------------------------------------------------------------------- #
VERB = {"installed": "install", "updated": "update", "removed": "remove", "kept": "keep"}
FILE_KINDS = ("skill", "agent", "hook")


def plural(n: int, one: str, many: str = "") -> str:
    return f"{n} {one if n == 1 else (many or one + 's')}"


@dataclass
class Tally:
    """What one run did in one tool."""
    tool: Tool
    done: dict = field(default_factory=dict)       # (kind, action) -> [names]
    kept: list = field(default_factory=list)       # [(what, why, path)]
    notes: list = field(default_factory=list)
    index: str = ""                                # what happened to the agent index
    planned: dict = field(default_factory=dict)    # skill folder -> (Skill, its hash before, or None)
    strangers: int = 0                             # files that were never ours (uninstall)
    closing: list = field(default_factory=list)

    def n(self, action: str, kinds=FILE_KINDS) -> int:
        return sum(len(self.done.get((k, action), ())) for k in kinds)


class Report:
    def __init__(self):
        self.verbose = self.dry_run = False
        self.mode = "install"          # install | refresh | uninstall
        self.tallies, self.current = {}, None
        self.project = self.commit = None
        self.todo = []                 # (tool key, agent) left pointing at a removed agent
        self.undo = False              # a menu install: say how to take it back

    # -- recording -------------------------------------------------------- #
    def open(self, title: str) -> None:
        if self.dry_run:
            print("Dry run: nothing is written.\n")
        print(title)
        if not self.verbose:
            print()

    def begin(self, tool: Tool) -> Tally:
        t = self.tallies.get(tool.config_root)
        if t is None:
            t = self.tallies[tool.config_root] = Tally(tool)
            if self.verbose:
                label = tool.label.replace(" — ", ", ")
                print(f"\n{tool.key} ({label})  {show_path(tool.config_root, self.project)}")
        self.current = t
        return t

    def line(self, action: str, what: str, why: str = "") -> None:
        if not self.verbose:
            return
        word = f"would {VERB[action]}" if self.dry_run and action in VERB else action
        print(f"  {word:<13} {what}".rstrip() + (f"   {why}" if why else ""))

    def did(self, action: str, kind: str, name: str, why: str = "", tool: Tool = None) -> None:
        t = self.begin(tool) if tool is not None else self.current
        t.done.setdefault((kind, action), []).append(name)
        self.line(action, f"{kind} {name}", why)

    def keep(self, what: str, why: str, path=None, tool: Tool = None) -> None:
        """A file the run chose not to touch: said again at the end, with its reason."""
        t = self.begin(tool) if tool is not None else self.current
        if path is None:
            kind, _, name = what.partition(" ")
            path = (t.tool.skills_dir / name if kind == "skill" or t.tool.agents_dir is None
                    else t.tool.agents_dir / f"{name}{agent_suffix(t.tool)}")
        if any(k[0] == what for k in t.kept):
            return                  # met again as another agent's dependency: one file, said once
        t.kept.append((what, why, path))
        self.line("kept", what, why)

    def note(self, text: str, tool: Tool = None) -> None:
        t = self.begin(tool) if tool is not None else self.current
        t.notes.append(text)
        self.line("note", text)

    def plan_skill(self, tool: Tool, name: str, skill, before: Optional[str]) -> None:
        """A skill folder about to be written. Whether that is an install, an
        update or no change is known only once every link in it is settled."""
        self.begin(tool).planned[name] = (skill, before)

    def settle(self, tool: Tool, skills_by_name: dict) -> None:
        t = self.tallies.get(tool.config_root)
        if t is None or not t.planned:
            return
        present = present_skills(tool.skills_dir, skills_by_name) | {
            n for n in t.planned if n in skills_by_name}
        for name, (skill, before) in sorted(t.planned.items()):
            if before is None:
                action = "installed"
            else:
                after = (expected_tree_hash(skill, name, present) if self.dry_run
                         else tree_hash(tool.skills_dir / name))
                action = "unchanged" if after == before else "updated"
            self.did(action, "skill", name, tool=tool)
        t.planned.clear()

    # -- saying it -------------------------------------------------------- #
    def phrase(self, action: str, n: int) -> str:
        if self.dry_run and action in VERB:
            return f"would {VERB[action]} {n}"
        return f"{n} {action}"

    def would(self, done: str) -> str:
        return f"would be {done}" if self.dry_run and done != "unchanged" else done

    def parts(self, t: Tally, kinds=FILE_KINDS, with_kept: bool = True) -> list:
        out = [self.phrase(a, t.n(a, kinds)) for a in ("installed", "updated", "unchanged", "removed")
               if t.n(a, kinds)]
        if with_kept:
            kept = [k for k in t.kept if k[0].split(" ")[0] in kinds]
            if kept:
                out.append(self.phrase("kept", len(kept)))
        return out

    def finish(self, scope: str = "") -> None:
        tallies = [t for t in self.tallies.values()]
        if not tallies:
            return
        total = {a: sum(t.n(a) for t in tallies) for a in ("installed", "updated", "unchanged", "removed")}
        kept = [(t, k) for t in tallies for k in t.kept]
        changed = total["installed"] + total["updated"] + total["removed"]
        where = tallies[0].tool.key if len(tallies) == 1 else f"{len(tallies)} tools"
        cat = f" catalog {self.commit}" if self.commit else " the catalog"
        if self.verbose:
            print()

        nothing = self.mode == "refresh" and not changed and not kept
        if nothing:
            print(f"No installed file differs from{cat}. Nothing to update.")
        elif len(tallies) == 1 and self.mode == "install":
            t = tallies[0]
            for label, kinds in (("skills", ("skill",)), ("agents", ("agent",)), ("options", ("hook",))):
                parts = self.parts(t, kinds)
                # a hook script that was already there says nothing
                if parts and not (label == "options" and not (t.n("installed", kinds) + t.n("updated", kinds)
                                                                + t.n("removed", kinds))):
                    print(f"  {label:<8} {', '.join(parts)}")
            if t.index:
                print(f"  index    agent index ({t.tool.roster.name}) {self.would(t.index)}")
        else:
            for t in tallies:
                parts = self.parts(t) + ([f"agent index {self.would(t.index)}"]
                                         if t.index and t.index != "unchanged" else [])
                print(wrapped(", ".join(parts) or "nothing to do", 16, f"  {t.tool.key:<13} "))

        if kept:
            n = len(kept)
            print(f"\nKept {plural(n, 'file')} as {'it is' if n == 1 else 'they are'}:")
            width = max(len(k[0]) for _, k in kept)
            for t, (what, why, path) in kept:
                lead = f"  {t.tool.key:<8} " if len(tallies) > 1 else "  "
                print(f"{lead}{what:<{width}}   {why}   {show_path(path, self.project)}")
            if self.mode == "uninstall":
                print(wrapped(f"{'It is' if n == 1 else 'They are'} yours now: the catalog no longer "
                              f"tracks {'it' if n == 1 else 'them'}. Delete {'it' if n == 1 else 'them'} "
                              f"by hand if you do not want {'it' if n == 1 else 'them'}.", 0))
            else:
                fixable = [t for t in tallies if any(w != _SAFE[LINK] for _, w, _ in t.kept)]
                if fixable:
                    print(wrapped(f"{'It still has its' if n == 1 else 'They still have their'} old "
                                  f"content. To replace {'it' if n == 1 else 'them'} with the "
                                  f"catalog's version:", 0))
                    for t in fixable:
                        # Name what was kept: `--all` would install the whole
                        # catalog into a tool that only ever had one agent.
                        mine = [w for w, why, _ in t.kept if why != _SAFE[LINK]]
                        flags = [f"--{w}" for w in mine] if len(mine) <= 6 else ["--all"]
                        print("  " + command("install", *flags, f"--tool {t.tool.key}", scope,
                                             "--on-conflict overwrite"))
                        if flags == ["--all"]:
                            print(f"  (the whole catalog: replaces every kept file in {t.tool.key})")
        for t in tallies:
            for note in t.notes:
                print(wrapped(f"Note ({t.tool.key}): {note}", 2))

        if self.todo:
            agents = sorted({a for _, a in self.todo})
            keys = [k for k, _ in self.todo]
            print("\nStill to do:")
            listed = keys[0] if len(keys) == 1 else f"{', '.join(keys[:-1])} and {keys[-1]}"
            print(wrapped(f"{listed} {'is' if len(keys) == 1 else 'are'} set to start with "
                          f"{', '.join(f'`{a}`' for a in agents)}, which "
                          f"{'this would remove' if self.dry_run else 'was just removed'}.", 2, "  "))
            print("  Try: " + command("default", "--restore", f"--tool {','.join(keys)}"))

        if not nothing:
            if self.mode == "uninstall":
                r = total["removed"]
                done = (f"would remove {plural(r, 'file')}" if self.dry_run
                        else f"{plural(r, 'file')} removed") + f" from {where}"
            elif changed:
                words = [(a, total[a]) for a in ("installed", "updated", "removed") if total[a]]
                first_a, first_n = words[0]
                head = (f"would {VERB[first_a]} {plural(first_n, 'file')}" if self.dry_run
                        else f"{plural(first_n, 'file')} {first_a}")
                done = ", ".join([head] + [self.phrase(a, n) for a, n in words[1:]]) + f" in {where}"
            else:
                done = (f"nothing to {'update' if self.mode == 'refresh' else 'change'} in {where}; "
                        f"{plural(total['unchanged'], 'file')} already up to date")
            if kept:
                done += f", {self.phrase('kept', len(kept))}"
            if self.mode == "install" and changed and self.commit and not self.dry_run:
                done += f", from catalog {self.commit}"
            print(f"\nDone{' (dry run)' if self.dry_run else ''}: {done}.")
        strangers = sum(t.strangers for t in tallies)
        if strangers:
            print(f"{plural(strangers, 'file')} not from this catalog "
                  f"{'was' if strangers == 1 else 'were'} not touched.")
        for t in tallies:
            for line in t.closing:
                print(wrapped(f"{t.tool.key}: {line}", 2))
        if self.dry_run:
            print("Dry run: nothing was written. Run again without --dry-run to apply.")
        elif self.mode == "install" and not self.todo:
            print("Check any time: " + command("status", scope))
            if self.undo and changed:
                print("Undo: " + command("uninstall", f"--tool {tallies[0].tool.key}", scope))


REPORT = Report()


def expected_tree_hash(skill, name: str, present: Optional[set] = None) -> str:
    """The tree_hash the installed folder would have: the catalog's files, with
    SKILL.md rendered as it gets installed. What a dry run compares against,
    since it writes nothing to hash."""
    h = hashlib.sha256()
    d = skill.path
    try:
        files = []
        for root, dirs, names_ in os.walk(d, followlinks=False):
            dirs[:] = sorted(x for x in dirs if not x.startswith("."))
            files += [Path(root) / n for n in names_ if not n.startswith(".")]
        for f in sorted(files, key=lambda p: p.relative_to(d).as_posix()):
            if f.is_symlink():
                continue
            rel, data = f.relative_to(d).as_posix(), f.read_bytes()
            if rel == "SKILL.md":
                data = render_skill(data.decode("utf-8"), skill.agent, name, present).encode("utf-8")
            h.update(rel.encode() + b"\0" + data + b"\0")
    except OSError:
        return UNREADABLE
    return h.hexdigest()


def copy_skill(skill: Skill, tool: Tool, name: str, dry_run: bool):
    dest = tool.skills_dir / name
    REPORT.plan_skill(tool, name, skill,
                      tree_hash(dest) if dest.is_dir() and not dest.is_symlink() else None)
    if dry_run:
        return name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():   # decide() never sends one here; never delete a link's target
        raise RuntimeError(f"refusing to replace the link {dest}")
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(skill.path, dest)
    md = dest / "SKILL.md"
    if md.exists():
        md.write_text(render_skill(md.read_text(encoding="utf-8"), skill.agent, name), encoding="utf-8")
    run_for(tool).skills_written.add(name)
    return name


def present_skills(skills_dir: Path, skills_by_name: dict) -> set:
    """Catalog skills installed in this dir — what a link there can reach. A
    folder counts only if it holds OUR copy of that skill: a foreign skill with
    the same name is not a target our links should point at."""
    if not skills_dir.is_dir():
        return set()
    return {d.name for d in skills_dir.iterdir()
            if d.name in skills_by_name
            and classify_skill(d, None)[0] == OURS}


def relink_skills(tool: Tool, skills_by_name: dict, dry_run: bool):
    """Re-render every catalog skill in tool.skills_dir against the skills that
    are actually there, after an install changed that set. Links to a missing
    skill become its name; a later install that brings it turns the name back
    into a link. Only our untouched copies: an edited one keeps its edits, and
    a foreign one with our name is not ours to rewrite (B-053 measured exactly
    that — a foreign folder left with our SKILL.md next to its own files).
    A dry run walks the same skills and says which it would rewrite."""
    run = run_for(tool)
    planned = REPORT.begin(tool).planned
    present = present_skills(tool.skills_dir, skills_by_name) | (
        {n for n in planned if n in skills_by_name} if dry_run else set())
    for name in sorted(present):
        d = tool.skills_dir / name
        if name in planned and dry_run:
            continue                      # not on disk yet; settle() says what it would be
        if name not in run.skills_written and classify_skill(d, run.stamp)[0] != OURS:
            continue
        src = skills_by_name[name]
        md = d / "SKILL.md"
        fresh = render_skill((src.path / "SKILL.md").read_text(encoding="utf-8"),
                             src.agent, name, present)
        if md.read_text(encoding="utf-8") != fresh:
            if not dry_run:
                md.write_text(fresh, encoding="utf-8")
                run.skills_written.add(name)
            if name not in planned:       # a skill this run did not install, re-pointed
                REPORT.did("updated", "skill", name, why="its links to other skills", tool=tool)
    REPORT.settle(tool, skills_by_name)


def sweep_retired(tool: Tool, dry_run: bool):
    """Remove our old copies that a renamed skill left behind — but only those
    that are ours (our id), replaced (that id is installed at its current
    name) and intact (the hash the stamp recorded under THIS old name). Until
    then a host lists both, with the same description, and may load the old
    one. Anything short of all three is kept and reported by --status: a
    duplicate costs less than a lost edit. A stamp from before B-058 has no
    record under the old name, so nothing is removed there. A dry run says
    what it finds on disk; a copy that only becomes old once the run has
    written the new name is not there to be seen yet."""
    if not tool.skills_dir.is_dir():
        return
    recs = (run_for(tool).stamp or {}).get("skills") or {}
    for d in sorted(tool.skills_dir.iterdir()):
        if d.is_symlink():
            continue
        kind, sk = classify_skill(d, None)
        if kind != RETIRED or sk is None:
            continue
        rec = recs.get(sk.id)
        if rec and rec.get("name") == d.name and rec.get("sha256") == tree_hash(d):
            if not dry_run:
                shutil.rmtree(d)
            REPORT.did("removed", "skill", d.name, why=f"old copy of {sk.name}", tool=tool)


def install_skill(skill: Skill, tool: Tool, policy: str, interactive: bool, dry_run: bool):
    # Already written in this run (an agent's dependency met again): it is ours
    # and fresh. Classifying it again against the stamp from BEFORE the run
    # would read our own write as a hand edit.
    if skill.name in run_for(tool).skills_written:
        return skill.name
    dest = tool.skills_dir / skill.name
    if not (dest.exists() or dest.is_symlink()):
        return copy_skill(skill, tool, skill.name, dry_run)
    kind, _ = classify_skill(dest, run_for(tool).stamp)
    choice = decide(kind, policy, interactive, f"skill {skill.name}")
    if choice == "skip":
        return None
    if choice == "rename":
        # Ours is already next to the foreign one from an earlier rename: update
        # that copy, or every run would add another `-N`.
        mine = sorted(p for p in tool.skills_dir.iterdir()
                      if p.name != skill.name and not p.is_symlink() and skill_id_at(p) == skill.id)
        if mine:
            kind2, _ = classify_skill(mine[0], run_for(tool).stamp)
            if decide(kind2, policy, interactive, f"skill {mine[0].name}") == "skip":
                return None
            return copy_skill(skill, tool, mine[0].name, dry_run)
        return copy_skill(skill, tool, _auto_rename(
            lambda nm: (tool.skills_dir / nm).exists(), skill.name), dry_run)
    return copy_skill(skill, tool, skill.name, dry_run)


# Inheritance is DECLARED, in each agent's frontmatter: `inherits:` is the full,
# ordered list of agents whose CORE.md (or whole body, without one) is inlined
# into this agent, in that order — explicit, not resolved recursively. It used
# to be detected from prose: a `../X/AGENTS.md` link with a trigger phrase
# ("reasoning model") within 140 characters. Rewording that sentence installed
# the agent without its parent's CORE, silently, and where the links happened to
# sit decided the inlining order. `validate.py` checks the list is complete.


def declared_inherits(agent: Agent, agents: dict) -> list:
    """The agents `agent` inherits from, in inlining order, from `inherits:`."""
    meta, _ = split_frontmatter(agent.agents_md.read_text(encoding="utf-8"))
    raw = meta.get("inherits")
    if raw is None:
        fail(f"the catalog is not valid: {agent.name}/AGENTS.md declares no `inherits:`.",
             "Add the list of agents it inherits from (`inherits: []` for none).",
             hint=f"Try: {script('validate.py')}")
    names = [n.strip() for n in raw.strip().strip("[]").split(",") if n.strip()]
    unknown = [n for n in names if n not in agents]
    if unknown:
        fail(f"the catalog is not valid: {agent.name}/AGENTS.md inherits from unknown "
             f"agent(s): {', '.join(unknown)}.", hint=f"Try: {script('validate.py')}")
    return [agents[n] for n in names]


def scan_refs(text: str) -> set:
    """Skill names linked from `text` (names are unique across the catalog)."""
    return set(re.findall(r"skills/([a-z][a-z-]*)/SKILL\.md", text))


def resolve_deps(agent: Agent, agents: dict, skills_by_name: dict):
    """What `agent` needs: the declared, ordered list of agents it inherits
    from (to inline), and the skills to install — its own, those of every agent
    it inherits from, and the skills any of them link to."""
    inherited = declared_inherits(agent, agents)
    skill_names = set()
    for ag in (agent, *inherited):
        texts = [ag.agents_md.read_text(encoding="utf-8")]
        for sk in ag.skills:
            skill_names.add(sk.name)
            texts.append((sk.path / "SKILL.md").read_text(encoding="utf-8"))
        for txt in texts:
            skill_names.update(scan_refs(txt))
    skills = [skills_by_name[n] for n in sorted(skill_names) if n in skills_by_name]
    return inherited, skills


def deref_skill_links(body: str) -> str:
    """Turn skill links into skill NAMES for the installed copy.

    In the catalog `[visual-craft](skills/lh-visual-craft/SKILL.md)` is navigable.
    Installed, the agent is a flat file and skills live in a sibling directory,
    so that path resolves to nothing. Observed consequence, from a real trace:
    an agent searched for its own skills, failed, and answered "no pude leer los
    skills de mi catálogo — voy con criterio propio". It worked without them.

    Rewriting to the tool's real layout was rejected in favour of this: the
    targets each have their own layout, and every host already discovers skills by NAME
    from their description. A name works everywhere; a path works in one place."""
    def sub(m):
        text, name = m.group(1), m.group(2)
        if "SKILL.md" in text or "/" in text:
            return f"`{name}`"          # the label was the path itself
        if name.lower() in text.lower():
            return text                 # already names its target
        return f"{text} (`{name}`)"
    body = re.sub(r"\[([^\]]+)\]\((?:\.\./)*(?:[a-z][a-z-]*/)*skills/([a-z][a-z-]*)/SKILL\.md\)",
                  sub, body)

    # The skills table's third column was the path. With the path gone it just
    # repeats the first column under a header that now says "File" about
    # nothing, so drop it rather than ship a column that lies.
    out = []
    for line in body.split("\n"):
        cells = [c.strip() for c in line.split("|")[1:-1]] if line.startswith("|") and line.rstrip().endswith("|") else []
        if len(cells) == 3 and (cells[2] == cells[0] or cells[2] == "File"
                                or set(cells[2]) <= set("-: ")):
            out.append("| " + " | ".join(cells[:2]) + " |")
        else:
            out.append(line)
    return "\n".join(out)


def render_skill(text: str, owner: Optional[str], name: str,
                 available: Optional[set] = None) -> str:
    """Build SKILL.md exactly as it gets installed. Shared with `--status`, so
    the staleness report compares against what the installer would write.

    The catalog is a tree; every tool installs skills FLAT, one folder per skill
    under a single directory. That decides what happens to each link shape:

    - `../x/SKILL.md` (sibling) already resolves installed — untouched.
    - `../../../agent/skills/x/SKILL.md` (cross-agent) becomes `../x/SKILL.md`:
      installed, every skill is a sibling of every other, in every layout.
      The label keeps naming the target so name-based discovery still works
      if a host renders the file without resolving links.
    - `../../AGENTS.md` / `../../../agent/AGENTS.md` become the agent's NAME:
      agent files land in another directory with a per-tool filename, so no
      relative path is true everywhere (same reasoning as deref_skill_links).

    `available` is the set of skills present next to this one. A link to a
    skill that is not there becomes its NAME instead of a dead path: a partial
    install (one agent, one skill) brings the skills it references, not the
    skills those reference, and measured on 2026-10-11 the 15 single-agent
    installs left 171 dead links. None means every catalog skill is present
    (the whole suite)."""
    text = flatten_description(rewrite_skill_name(text, name))

    def skill_sub(m):
        label, target = m.group(1), m.group(2)
        if available is not None and target not in available:
            if "SKILL.md" in label or "/" in label or target.lower() in label.lower():
                return f"the `{target}` skill"
            return f"{label} (the `{target}` skill)"
        if "SKILL.md" in label or "/" in label:
            label = f"`{target}`"           # the label was the path itself
        elif target.lower() not in label.lower():
            label = f"{label} (`{target}`)"
        return f"[{label}](../{target}/SKILL.md)"
    text = re.sub(r"\[([^\]]+)\]\((?:\.\./){2,}[a-z][a-z-]*/skills/([a-z][a-z-]*)/SKILL\.md\)",
                  skill_sub, text)
    if available is not None:
        # Sibling links (`../x/SKILL.md`, same agent) need no rewrite in a full
        # install, but in a partial one the sibling may not be there either.
        def sibling_sub(m):
            label, target = m.group(1), m.group(2)
            if target in available:
                return m.group(0)
            if "SKILL.md" in label or "/" in label or target.lower() in label.lower():
                return f"the `{target}` skill"
            return f"{label} (the `{target}` skill)"
        text = re.sub(r"\[([^\]]+)\]\(\.\./([a-z][a-z-]*)/SKILL\.md\)", sibling_sub, text)

    def agent_sub(m):
        label, ups, agent = m.group(1), m.group(2).count("../"), m.group(3)
        if agent is None:
            # two levels up from skills/x/ is the owning agent; three is the catalog root
            agent = owner if ups == 2 else None
        if agent is None:
            return "the catalog's root `AGENTS.md`" if "AGENTS.md" in label else label
        if "AGENTS.md" in label or "/" in label:
            return f"the `{agent}` agent"
        if agent.lower() in label.lower():
            return label
        return f"{label} (`{agent}` agent)"
    return re.sub(r"\[([^\]]+)\]\(((?:\.\./)+)(?:([a-z][a-z-]*)/)?AGENTS\.md\)", agent_sub, text)


def compose_agent(agent: Agent, inherited: list):
    """Build the agent body exactly as it gets installed: own body plus the
    inherited CORE.md sections. Shared with `--status`, which re-renders to
    detect drift — if the two ever diverged, the staleness report would lie."""
    meta, body = split_frontmatter(agent.agents_md.read_text(encoding="utf-8"))
    desc = meta.get("description") or agent_description(body)  # before inlining
    if inherited:
        parts = [body, "\n\n---\n\n# Inherited context (installed automatically)\n"]
        for pa in inherited:
            core = pa.path / "CORE.md"
            if core.exists():
                # curated, condensed essence — preferred over a full-file dump
                parts.append(f"\n{core.read_text(encoding='utf-8').strip()}\n")
            else:
                _, pbody = split_frontmatter(pa.agents_md.read_text(encoding="utf-8"))
                parts.append(f"\n## Inherited from `{pa.name}` (full)\n\n{pbody}\n")
        body = "".join(parts)
    return meta, desc, deref_skill_links(body)


def install_agent(agent: Agent, tool: Tool, policy: str, interactive: bool,
                  dry_run: bool, agents: dict, skills_by_name: dict,
                  with_deps: bool = True, skip_skills: bool = False,
                  roster: bool = True):
    REPORT.begin(tool)

    if with_deps:
        inherited, dep_skills = resolve_deps(agent, agents, skills_by_name)
    else:
        inherited, dep_skills = [], list(agent.skills)

    if not skip_skills:
        own = {s.name for s in agent.skills}
        extra = [s.name for s in dep_skills if s.name not in own]
        if inherited:
            REPORT.line("with", f"agent {agent.name}",
                        f"inherits {', '.join(a.name for a in inherited)} (reasoning inlined)")
        if extra:
            REPORT.line("with", f"agent {agent.name}", f"skills pulled in: {', '.join(extra)}")

    # install all skills (own + inherited/cross-agent deps) unless already done
    # globally by a bulk (--all) run
    if skip_skills:
        installed_skill_names = [s.name for s in dep_skills]
    else:
        installed_skill_names = []
        for sk in dep_skills:
            nm = install_skill(sk, tool, policy, interactive, dry_run)
            if nm:
                installed_skill_names.append(nm)
        relink_skills(tool, skills_by_name, dry_run)
        # A dependency left alone because it was edited is still ours and still
        # there: the agent must keep pointing at it (Kiro lists them).
        if not dry_run:
            present = present_skills(tool.skills_dir, skills_by_name)
            installed_skill_names += [s.name for s in dep_skills
                                      if s.name in present and s.name not in installed_skill_names]

    if tool.agents_dir is None:
        REPORT.note(f"this tool has no place for agent files; `{agent.name}` is its skills.")
        return

    meta, desc, body = compose_agent(agent, inherited)

    # Ours (the stamp recorded it, unchanged) is updated in place; anything else
    # is decided like a skill. Before B-058 `ask` without a TTY renamed even our
    # own files, so running the default command twice installed every agent twice.
    run = run_for(tool)
    suffix = agent_suffix(tool)
    final = agent.name
    existing = tool.agents_dir / f"{agent.name}{suffix}"
    if existing.exists() or existing.is_symlink():
        kind = classify_agent(existing, set(agents), run.stamp)
        choice = decide(kind, policy, interactive, f"agent {agent.name}")
        if choice == "skip":
            return
        if choice == "rename":
            recs = (run.stamp or {}).get("agents") or {}
            prior = sorted(f for f in recs
                           if re.fullmatch(re.escape(agent.name) + r"-\d+" + re.escape(suffix), f)
                           and (tool.agents_dir / f).exists())
            if prior:   # ours already sits next to the foreign one: update it
                again = classify_agent(tool.agents_dir / prior[0], set(agents), run.stamp)
                if decide(again, policy, interactive, f"agent {prior[0]}") == "skip":
                    return
                final = prior[0][:-len(suffix)]
            else:
                final = _auto_rename(lambda nm: (tool.agents_dir / f"{nm}{suffix}").exists(),
                                     agent.name)
    dest, contents = render_agent(tool, final, body, desc, installed_skill_names, meta,
                                  guard=guard_command(tool), verify=verify_command(tool))
    there = dest.is_file() and not dest.is_symlink()
    REPORT.did("installed" if not there else
               "unchanged" if agent_hash(dest) == agent_text_hash(contents, dest.name) else "updated",
               "agent", final)
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        # A host that upgrades our file (Kiro) keeps a backup each time it
        # does. When what WE wrote is unchanged, leave the host's version in
        # place: rewriting it would only make the host upgrade it again.
        if not (dest.is_file() and not dest.is_symlink()
                and agent_hash(dest) == agent_text_hash(contents, dest.name)
                and file_hash(dest) != hashlib.sha256(contents.encode("utf-8")).hexdigest()):
            dest.write_text(contents, encoding="utf-8")
        run.agents_written.add(dest.name)

    # Tools with no named-agent concept only find the body through the roster,
    # so writing one without the other leaves a half-install. The suite path
    # passes roster=False and writes it once at the end instead.
    if roster and tool.agent_style == "roster_md":
        write_roster(tool, agents, [final], dry_run)
    if roster:
        retire_roster_install(tool, agents, dry_run)


ROSTER_BODY_HEAD = "# `{name}` agent\n"


def retire_roster_install(tool: Tool, agents: dict, dry_run: bool):
    """Codex used to get a roster install (catalog bodies as `.md` plus a block
    in AGENTS.md); it now has named TOML agents, so the old copy would sit next
    to the new one and the roster would keep pointing at it. Remove only what
    the catalog wrote: `.md` bodies that open with the roster header, and the
    marker block. Per project the root AGENTS.md block is shared with the
    `shared` tool's install, so it stays if that install is present."""
    if tool.agent_style != "codex_toml" or not tool.agents_dir or not tool.agents_dir.is_dir():
        return
    for name in sorted(agents):
        old = tool.agents_dir / f"{name}.md"
        if old.is_file() and old.read_text(encoding="utf-8").startswith(
                ROSTER_BODY_HEAD.format(name=name)):
            REPORT.did("removed", "agent", old.name, why="left by an older install", tool=tool)
            if not dry_run:
                old.unlink()
    roster = tool.roster
    if not roster.is_file():
        return
    text = roster.read_text(encoding="utf-8")
    if ROSTER_BEGIN not in text or ROSTER_END not in text:
        return
    shared_bodies = roster.parent / ".agents" / "agents"
    if roster.parent != tool.config_root and any(
            f.read_text(encoding="utf-8").startswith("# `")
            for f in shared_bodies.glob("*.md")):
        REPORT.line("kept", f"agent index in {roster.name}", "the shared install still uses it")
        return
    rest = (text[:text.index(ROSTER_BEGIN)]
            + text[text.index(ROSTER_END) + len(ROSTER_END):]).strip()
    REPORT.begin(tool).index = "removed"
    REPORT.line("removed", f"agent index in {roster.name}", "left by an older install")
    if not dry_run:
        if rest:
            roster.write_text(rest + "\n", encoding="utf-8")
        else:
            roster.unlink()


def short_description(agent: Agent) -> str:
    """One line for the roster: the curated frontmatter description up to its
    first sentence, or the body's opening sentence when there is no frontmatter."""
    meta, body = split_frontmatter(agent.agents_md.read_text(encoding="utf-8"))
    desc = meta.get("description") or agent_description(body)
    desc = desc.split("<example>")[0].strip()
    first = re.split(r"(?<=[.!?])\s", " ".join(desc.split()))[0]
    return first if len(first) <= 160 else first[:157] + "..."


def write_roster(tool: Tool, agents: dict, just_installed: list, dry_run: bool):
    """Write the agent roster into the tool's AGENTS.md, between markers.

    Anything outside the markers is the user's and is preserved verbatim: an
    existing block is replaced in place, and a file with no block keeps all of
    its content with the block appended.

    The roster lists every agent body present in `agents_dir`, not just the ones
    installed in this run — otherwise installing one agent would drop the rows
    for the thirteen already there. (In `--dry-run` nothing is on disk yet, so
    this run's names are unioned in to show what the result would look like.)"""
    dest = tool.roster
    run = run_for(tool)
    on_disk = ({p.stem for p in tool.agents_dir.glob("*.md")
                if p.name in run.agents_written
                or classify_agent(p, set(agents), run.stamp) in (OURS, EDITED)}
               if tool.agents_dir.exists() else set())
    listed = sorted((on_disk | set(just_installed)) & set(agents))
    rows = "\n".join(
        f"| `{n}` | {short_description(agents[n])} | [`agents/{n}.md`](agents/{n}.md) |"
        for n in listed)
    block = (f"{ROSTER_BEGIN}\n"
             f"## Agent catalog\n\n"
             f"These agent definitions are installed locally. When a task matches one,\n"
             f"read its file and adopt that identity for the task — reasoning model,\n"
             f"heuristics, and limits. Load the skills it references when their triggers\n"
             f"fire; they live in `skills/`.\n\n"
             f"| Agent | Use it for | Definition |\n"
             f"|-------|-----------|------------|\n"
             f"{rows}\n"
             f"{ROSTER_END}")

    if dest.exists():
        current = dest.read_text(encoding="utf-8")
        if ROSTER_BEGIN in current and ROSTER_END in current:
            head = current[:current.index(ROSTER_BEGIN)]
            tail = current[current.index(ROSTER_END) + len(ROSTER_END):]
            contents, verb = head + block + tail, "updated"
        else:
            contents = current.rstrip() + "\n\n" + block + "\n"
            verb = "added"
    else:
        contents, verb = block + "\n", "written"

    same = dest.exists() and dest.read_text(encoding="utf-8") == contents
    REPORT.begin(tool).index = "unchanged" if same else verb
    REPORT.line("unchanged" if same else verb, f"agent index ({dest.name})")
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(contents, encoding="utf-8")


# --------------------------------------------------------------------------- #
# Provenance
#
# An installed copy is a snapshot, and the only question that matters later is
# "how far behind is it, and what moved". Git already knows both exactly, so
# nothing here is maintained by hand: the installer records WHICH catalog commit
# it copied from, and `--status` asks git for the rest. A per-file version field
# would be a worse copy of information the repository already holds.
# --------------------------------------------------------------------------- #
MANIFEST = ".local-agents.json"


def git(catalog: Path, *args):
    """Run a read-only git command in the catalog. Returns stripped stdout, or
    None if this isn't a repo / git isn't installed — provenance is a nicety,
    never a reason to fail an install."""
    try:
        proc = subprocess.run(["git", "-C", str(catalog), *args],
                              capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return proc.stdout.strip() if proc.returncode == 0 else None


# What an install is rendered from. A change anywhere else — a new doc at the
# root, an edited README — leaves every installed file identical, so it must
# not mark the stamp dirty; an uncommitted skill or agent edit must.
INSTALL_INPUTS = ("install.py", ":(glob)*/AGENTS.md", ":(glob)*/CORE.md",
                  ":(glob)*/skills/**", ":(glob)skills/**",
                  "scripts/shell_write_guard.py",   # copied by --shell-write-guard
                  "scripts/verify_before_stop.py")  # copied by --verify-hook


def catalog_state(catalog: Path):
    """(commit, dirty) for the catalog as it is being installed FROM. Dirty
    means uncommitted changes in INSTALL_INPUTS, untracked files included: a
    new skill folder is installed before it is committed."""
    commit = git(catalog, "rev-parse", "HEAD")
    if not commit:
        return None, False
    status = git(catalog, "status", "--porcelain", "--untracked-files=all",
                 "--", *INSTALL_INPUTS)
    return commit, bool(status or "")


def write_manifest(tool: Tool, catalog: Path, dry_run: bool, suite: bool = False):
    """Written by every path that installs. Without git there is no commit to
    record, but the ownership records still are: without them nothing could
    tell our files from a stranger's or an edited one (B-058)."""
    commit, dirty = catalog_state(catalog)
    dest = tool.config_root / MANIFEST
    sync_guard(tool, dry_run)
    sync_verify(tool, dry_run)
    where = (f"@ {commit[:7]}{' (dirty tree)' if dirty else ''}" if commit
             else "(catalog is not a git checkout: no commit recorded)")
    REPORT.begin(tool)
    REPORT.line("record", dest.name, where)
    if commit:
        REPORT.commit = commit[:7]
    if dry_run:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    skills, agents = owned_records(tool, catalog)
    data = {"catalog_commit": commit, "catalog_dirty": dirty} if commit else {}
    # Whole catalog here, once, means whole catalog on every refresh — new
    # skills and agents included. A partial install stays what the user chose.
    old = run_for(tool).stamp or {}
    data["suite"] = bool(suite or old.get("suite", "skills" not in old and bool(old)))
    data.update({
        "catalog_path": str(catalog.resolve()),
        "installed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "skills": skills,
        "agents": agents,
    })
    if tool.agent_style in GUARD_STYLES:
        data["shell_write_guard"] = guard_on(tool)
        if guard_on(tool):
            data["shell_write_guard_sha256"] = file_hash(guard_path(tool))
        data["verify_hook"] = verify_on(tool)
        if verify_on(tool):
            data["verify_hook_default"] = verify_default(tool)
            data["verify_hook_sha256"] = file_hash(verify_path(tool))
    dest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def owned_records(tool: Tool, catalog: Path) -> tuple:
    """What we own on this host and the hash of each as WE left it (B-058).

    Written this run → its hash now. Not touched this run → the hash recorded
    last time, kept as it was: re-recording the current hash would launder a
    hand edit into "intact" and the next refresh would overwrite it. Ours but
    never recorded (an install from before B-058) → its hash now, once."""
    run = run_for(tool)
    old = run.stamp or {}
    old_skills, old_agents = old.get("skills") or {}, old.get("agents")
    skills = {}
    if tool.skills_dir.is_dir():
        found = [(d,) + classify_skill(d, None) for d in sorted(tool.skills_dir.iterdir())]
        # At its own name first; a copy elsewhere only when it is the only one.
        for d, kind, sk in sorted(found, key=lambda x: x[1] != OURS):
            if kind not in (OURS, ELSEWHERE) or not sk.id or sk.id in skills:
                continue
            prev = old_skills.get(sk.id)
            if d.name in run.skills_written or not prev or prev.get("name") != d.name:
                skills[sk.id] = {"name": d.name, "sha256": tree_hash(d)}
            else:
                skills[sk.id] = prev
    agents = {}
    if tool.agents_dir is not None and tool.agents_dir.is_dir():
        names = {p.parent.name for p in catalog.glob("*/AGENTS.md")}
        for f in sorted(tool.agents_dir.glob(f"*{agent_suffix(tool)}")):
            if f.is_symlink():
                continue
            if f.name in run.agents_written:
                agents[f.name] = agent_hash(f)
            elif old_agents is not None and f.name in old_agents:
                agents[f.name] = old_agents[f.name]
            elif old_agents is None and old and f.stem in names:
                agents[f.name] = agent_hash(f)   # a pre-B-058 stamp: ours, once
    return skills, agents


def read_manifest(tool: Tool):
    path = tool.config_root / MANIFEST
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def provenance_line(tool: Tool, catalog: Path, behind: bool = False):
    """Lines for --status --verbose: which catalog commit this install came
    from, and how far the catalog has moved since. Context, not the verdict:
    `behind` says whether any installed file actually differs, and a count of
    commits that changed none of them must not read as something to do.

    Degrades honestly at every step: no manifest, no git, or a commit that is no
    longer in history (rebase, force-push, fresh clone) each get a specific
    message rather than a wrong number."""
    man = read_manifest(tool)
    if not man:
        return ["no install record: installed before records existed, or by hand"]
    was = man.get("catalog_commit") or ""
    if not was:
        return ["installed from a catalog that was not a git checkout: no commit to compare"]
    now = git(catalog, "rev-parse", "HEAD")
    if not now:
        return [f"installed from {was[:7]} (catalog is not a git checkout here)"]
    stamp = f"installed from {was[:7]}"
    if man.get("catalog_dirty"):
        stamp += " + uncommitted changes"
    if was == now:
        return [f"{stamp}, the catalog's current commit"]
    if git(catalog, "cat-file", "-e", f"{was}^{{commit}}") is None:
        return [f"{stamp}; that commit is not in this history "
                f"(rebased, or a different clone); reinstall to resync"]
    n = git(catalog, "rev-list", "--count", f"{was}..{now}") or "?"
    return [f"{stamp}, {n} commit{'s' if n != '1' else ''} before {now[:7]}; "
            + ("a refresh brings what changed" if behind else "no installed file differs")]


def install_suite(tool: Tool, policy: str, interactive: bool, dry_run: bool,
                  agents: dict, skills_by_name: dict, catalog: Path = None):
    """Install the WHOLE catalog — every skill once, then every agent file with
    its inheritance inlined. This guarantees all cross-agent handoffs, shared
    skills, and orchestration references resolve, because everything is present."""
    REPORT.begin(tool)
    for name in sorted(skills_by_name):
        install_skill(skills_by_name[name], tool, policy, interactive, dry_run)
    relink_skills(tool, skills_by_name, dry_run)
    sweep_retired(tool, dry_run)

    if tool.agents_dir is None:
        return

    for name in sorted(agents):
        install_agent(agents[name], tool, policy, interactive, dry_run,
                      agents, skills_by_name, with_deps=True, skip_skills=True,
                      roster=False)

    if tool.agent_style == "roster_md":
        write_roster(tool, agents, sorted(agents), dry_run)
    retire_roster_install(tool, agents, dry_run)

    write_manifest(tool, catalog, dry_run, suite=True)


def refresh_tool(tool: Tool, dry_run: bool, agents: dict, skills_by_name: dict,
                 catalog: Path):
    """Bring one host's install up to date: the whole catalog where the whole
    catalog was installed, otherwise exactly what the stamp records — one
    skill installed alone must not become 48 skills and 15 agents."""
    stamp = run_for(tool).stamp or {}
    if stamp.get("suite", "skills" not in stamp):
        install_suite(tool, "update", False, dry_run, agents, skills_by_name, catalog)
        return
    REPORT.begin(tool)
    suffix = agent_suffix(tool) if tool.agents_dir is not None else None
    for f in sorted((stamp.get("agents") or {})):
        name = f[:-len(suffix)] if suffix and f.endswith(suffix) else None
        if name in agents:
            install_agent(agents[name], tool, "update", False, dry_run, agents,
                          skills_by_name, with_deps=True)
    for sid in sorted(stamp.get("skills") or {}):
        sk = SKILLS_BY_ID.get(sid)
        if sk is not None:
            install_skill(sk, tool, "update", False, dry_run)
    relink_skills(tool, skills_by_name, dry_run)
    sweep_retired(tool, dry_run)
    write_manifest(tool, catalog, dry_run)


# --------------------------------------------------------------------------- #
# Uninstall (B-107)
#
# The way back takes what the installer put, and only that. "Ours" is decided
# the way every other path decides it — by identity and by the hash the stamp
# recorded, never by name: a copy that still is what we wrote goes; one that
# was edited since stays, because a leftover file costs less than a lost edit;
# a stranger's file with one of our names is not ours to judge. Nothing is
# guessed: a copy the stamp holds no record of is kept.
# --------------------------------------------------------------------------- #
def _rmdir_if_empty(d: Path, dry_run: bool) -> None:
    """Take away a directory we may have made, when nothing is left in it."""
    if dry_run or not d.is_dir() or d.is_symlink():
        return
    try:
        next(d.iterdir())
    except StopIteration:
        d.rmdir()
    except OSError:
        pass


def remove_roster_block(roster: Path, dry_run: bool) -> bool:
    """Take our marker block out of an AGENTS.md. Everything outside the
    markers is the user's and stays byte for byte; a file that held nothing
    else goes with the block."""
    if not roster.is_file():
        return False
    text = roster.read_text(encoding="utf-8")
    if ROSTER_BEGIN not in text or ROSTER_END not in text:
        return False
    head = text[:text.index(ROSTER_BEGIN)]
    tail = text[text.index(ROSTER_END) + len(ROSTER_END):]
    # write_roster appends "\n\n" + block + "\n" to a file that had content,
    # so undo exactly that; a block placed in the middle keeps both sides.
    if head.strip() and tail.strip():
        rest = head.rstrip("\n") + "\n\n" + tail.lstrip("\n")
    else:
        rest = head.rstrip("\n") + "\n" if head.strip() else tail.lstrip("\n")
    REPORT.line("removed", f"agent index from {roster.name}")
    if not dry_run:
        if rest.strip():
            roster.write_text(rest, encoding="utf-8")
        else:
            roster.unlink()
    return True


def _owns_roster(tool: Tool) -> bool:
    """Whether the block in this tool's AGENTS.md is this install's to remove.
    A roster host's always is. Codex only left one before it had TOML agents,
    and per project that root AGENTS.md is the `shared` install's too: while
    its bodies are there, the block is still in use (see retire_roster_install)."""
    if tool.agent_style == "roster_md":
        return True
    if tool.agent_style != "codex_toml":
        return False
    bodies = tool.roster.parent / ".agents" / "agents"
    return tool.roster.parent == tool.config_root or not any(
        f.read_text(encoding="utf-8", errors="replace").startswith("# `") for f in bodies.glob("*.md"))


def uninstall_tool(tool: Tool, dry_run: bool, agents: dict) -> bool:
    """Remove this host's catalog install. Returns False when there is none."""
    stamp_file = tool.config_root / MANIFEST
    if not stamp_file.is_file():
        return False
    stamp = run_for(tool).stamp or {}
    tally = REPORT.begin(tool)

    # Skills: ours by id, and still the bytes the stamp recorded under that name.
    recs = stamp.get("skills") or {}
    if tool.skills_dir.is_dir():
        for d in sorted(tool.skills_dir.iterdir()):
            kind, sk = classify_skill(d, stamp)
            if kind in (FOREIGN, LINK):
                tally.strangers += kind == FOREIGN
                continue
            # A skill the catalog no longer has is still ours if the stamp recorded it here.
            rec = recs.get(sk.id) if sk is not None else next(
                (r for r in recs.values() if r.get("name") == d.name), None)
            if kind != EDITED and rec and rec.get("name") == d.name and rec.get("sha256") == tree_hash(d):
                REPORT.did("removed", "skill", d.name)
                if not dry_run:
                    shutil.rmtree(d)
            else:
                REPORT.keep(f"skill {d.name}", _SAFE[EDITED] if kind == EDITED or rec
                            else "no install record for it", d)

    # Agents: the files the stamp lists, while they are what we wrote.
    backups, gone = 0, []
    if tool.agents_dir is not None and tool.agents_dir.is_dir():
        for f in sorted(tool.agents_dir.iterdir()):
            if not f.is_file() or not f.name.endswith(agent_suffix(tool)):
                continue
            kind = classify_agent(f, set(agents), stamp)
            if kind == OURS:
                REPORT.did("removed", "agent", f.stem)
                gone.append(f.stem)
                # Kiro keeps its own backup of an agent it upgraded; that file is Kiro's.
                backups += (f.parent / (f.name + ".bak")).is_file()
                if not dry_run:
                    f.unlink()
            elif kind == EDITED:
                REPORT.keep(f"agent {f.stem}", _SAFE[EDITED], f)
            elif kind == FOREIGN:
                tally.strangers += 1

    # Hook scripts: only a copy whose hash is the one we recorded.
    for rel, key, name in ((GUARD_REL, "shell_write_guard_sha256", "shell-write guard"),
                           (VERIFY_REL, "verify_hook_sha256", "verify hook")):
        f = tool.config_root / rel
        if not f.is_file():
            continue
        if stamp.get(key) and file_hash(f) == stamp[key]:
            REPORT.did("removed", "hook", name)
            if not dry_run:
                f.unlink()
        else:
            REPORT.keep(f"hook {rel.name}", "not the copy that was installed", f)

    if _owns_roster(tool) and remove_roster_block(tool.roster, dry_run):
        tally.index = f"removed from {tool.roster.name}"
    REPORT.line("removed", f"install record ({stamp_file.name})")
    if not dry_run:
        stamp_file.unlink()
        for d in (tool.config_root / GUARD_REL.parent, tool.config_root / GUARD_REL.parent.parent,
                  tool.skills_dir, tool.agents_dir):
            if d is not None:
                _rmdir_if_empty(d, dry_run)
        home = TOOLS_BY_KEY.get(tool.key)
        if home is not None and tool.config_root != home.config_root:
            _rmdir_if_empty(tool.config_root, dry_run)      # a project's own config dir, never the home one
    if backups:
        tally.closing.append(f"{plural(backups, 'backup')} made by Kiro itself (*.bak) "
                             f"remain{'s' if backups == 1 else ''} in "
                             f"{show_path(tool.agents_dir, REPORT.project)}")
    _warn_default_agent(tool, gone)
    return True


def _warn_default_agent(tool: Tool, removed: list) -> None:
    """A host told to start with an agent that is gone starts badly. The
    setting is default_agent.py's to put back, not ours — say so, once for
    every tool it happened in."""
    home = TOOLS_BY_KEY.get(tool.key)
    if home is None or tool.config_root != home.config_root:
        return
    try:
        sys.dont_write_bytecode = True      # no __pycache__ in the catalog: it would read as a dirty tree
        import default_agent
        host = default_agent.HOSTS.get(tool.key)
        now = default_agent.current(host) if host else default_agent.ABSENT
    except Exception:           # the script is optional; its absence must not break an uninstall
        return
    if isinstance(now, str) and now in removed:
        REPORT.todo.append((tool.key, now))


# --------------------------------------------------------------------------- #
# Interactive menu
# --------------------------------------------------------------------------- #
class Cancelled(Exception):
    """The person left the menu before anything was written."""


def ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        # No one at the keyboard (a script, CI): the menu cannot be answered.
        print(flush=True)
        fail("the menu needs someone to answer it, and there is no input.",
             hint="Try: " + command("list"))


def choose(prompt: str, options: list) -> int:
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o}")
    while True:
        raw = ask(f"{prompt} (number, or q to quit): ").lower()
        if raw in ("q", "quit", ""):
            raise Cancelled
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print(f"  Type a number from 1 to {len(options)}, or q to quit.")


def interactive(agents, all_skills, skills_by_name, policy, dry_run, with_deps, project=None, catalog=None):
    try:
        _interactive(agents, all_skills, skills_by_name, policy, dry_run, with_deps, project, catalog)
    except Cancelled:
        print("Cancelled: nothing was changed.")


def _interactive(agents, all_skills, skills_by_name, policy, dry_run, with_deps, project, catalog):
    print("What do you want to install?")
    mode = choose("Choose", [f"The whole catalog ({len(agents)} agents, {len(skills_by_name)} skills)",
                             "One agent, with the skills it uses",
                             "One or more skills"])

    # The same row --status prints: what is there before choosing where.
    print("\nInto which tool?")
    states = [tool_state(project_tool(t, project) if project else t, agents, skills_by_name, project)
              for t in TOOLS]
    tool_idx = choose("Choose", [
        f"{st.tool.key:<13} " + (f"{len(st.behind)} out of date" if st.state == OUT_OF_DATE else st.state)
        for st in states])
    tool = TOOLS[tool_idx]
    if project:
        tool = project_tool(tool, project)
        refuse_shared_project_dir(tool, agents)
    if not tool.config_root.exists():
        ans = ask(f"{tool.key} was not detected ({show_path(tool.config_root, project)} does not "
                  f"exist). Install there anyway? [y/N] ").lower()
        if ans not in ("y", "yes"):
            raise Cancelled

    into = f"{tool.key} ({show_path(tool.config_root, project)})"
    REPORT.undo = True
    if mode == 0:
        print()
        REPORT.open(f"Installing the whole catalog into {into}")
        install_suite(tool, policy, True, dry_run, agents, skills_by_name, catalog)
    elif mode == 1:
        names_ = sorted(agents)
        print("\nWhich agent?")
        idx = choose("Choose", [f"{n:<16} {plural(len(resolve_deps(agents[n], agents, skills_by_name)[1]), 'skill')}"
                                for n in names_])
        print()
        REPORT.open(f"Installing agent {names_[idx]} into {into}")
        install_agent(agents[names_[idx]], tool, policy, True, dry_run,
                      agents, skills_by_name, with_deps)
        write_manifest(tool, catalog, dry_run)
    else:
        print("\nWhich skills?")
        for i, sk in enumerate(all_skills, 1):
            print(f"  {i}. {sk.qualified}")
        while True:
            raw = ask("Numbers, separated by commas (or q to quit): ").lower()
            if raw in ("q", "quit", ""):
                raise Cancelled
            tokens = [x for x in re.split(r"[,\s]+", raw) if x]
            bad = [x for x in tokens if not (x.isdigit() and 1 <= int(x) <= len(all_skills))]
            if not bad:
                break
            # The whole line again: installing "the ones that were right" is not what was typed.
            print(f"  {', '.join(bad)} {'is' if len(bad) == 1 else 'are'} not on the list. "
                  f"Type numbers from 1 to {len(all_skills)}.")
        picks = [all_skills[int(x) - 1] for x in dict.fromkeys(tokens)]
        print()
        REPORT.open(wrapped(f"Installing {', '.join(f'skill {sk.name}' for sk in picks)} into {into}", 2))
        REPORT.begin(tool)
        for sk in picks:
            install_skill(sk, tool, policy, True, dry_run)
        relink_skills(tool, skills_by_name, dry_run)
        write_manifest(tool, catalog, dry_run)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def shadow_report(tool: Tool, skills_by_name: dict, project=None) -> list:
    """[(dir, out-of-date copies there, key of the tool that owns that dir)]
    for a host that sees a catalog skill in more than one dir with at least
    one copy out of date.

    A host that reads several skill dirs keeps ONE copy per name, and which one
    is not stable: measured on opencode 1.18.11, three identical runs took 32,
    10 and 4 of 48 skills from the project and the rest from global copies — one
    of them two months old. Identical copies make that harmless; an out-of-date
    one makes the skill the host loads a coin toss. So the report is about
    out-of-date copies, not duplicates, and it names the refresh that fixes each."""
    dirs = [tool.skills_dir, *tool.also_reads]
    owners, owner_tool = {}, {}
    for t in TOOLS:
        t = project_tool(t, project) if project else t
        owners.setdefault(t.skills_dir, t.key)
        owner_tool.setdefault(t.skills_dir, t)
    stale_in = {}
    ours = {d: present_skills(d, skills_by_name) for d in dirs}   # a foreign same-name skill is not a copy of ours
    for name, src in skills_by_name.items():
        copies = [d for d in dirs if name in ours[d]]
        if len(copies) < 2:
            continue
        text = (src.path / "SKILL.md").read_text(encoding="utf-8")
        for d in copies:
            if d in owner_tool and classify_skill(d / name, run_for(owner_tool[d]).stamp)[0] == EDITED:
                continue   # kept on purpose, and refresh leaves it: not an out-of-date copy
            fresh = render_skill(text, src.agent, name, ours[d])
            if (d / name / "SKILL.md").read_text(encoding="utf-8") != fresh:
                stale_in[d] = stale_in.get(d, 0) + 1
    return [(d, n, owners.get(d)) for d, n in sorted(stale_in.items(), key=lambda kv: str(kv[0]))]


# --------------------------------------------------------------------------- #
# Status
#
# What a person asks of --status is one thing: do I have to do something? So
# the state of each tool is computed first, as a value, and printed after: the
# headline is the answer, there is one row per tool, and the detail a person
# only wants when something is off (what is not ours, what is switched off, how
# many commits ago) waits behind --verbose.
#
# "Out of date" is decided by CONTENT, never by commits: every installed file
# is rendered again from the catalog and compared. A commit that touches the
# catalog without changing an installed file is not something to refresh for.
# --------------------------------------------------------------------------- #
UP_TO_DATE, OUT_OF_DATE, NOTHING, NOT_DETECTED = ("up to date", "out of date",
                                                  "nothing installed", "not detected")


def show_path(p, project=None) -> str:
    """A path as a person would type it: relative to the project, `~` for the
    home on POSIX (PowerShell does not expand `~` in an argument), else whole."""
    p = Path(p)
    if project is not None:
        try:
            return str(p.relative_to(project)) or "."
        except ValueError:
            pass
    if os.name != "nt":
        try:
            return "~/" + p.relative_to(HOME).as_posix()
        except ValueError:
            pass
    return str(p)


def shell_arg(path: str) -> str:
    """A path inside a command to copy. Quoted only when it has to be: quotes
    around `~/x` would stop the shell from expanding the home."""
    return path if re.fullmatch(r"[\w@%+=:,./~-]+", path) else shlex.quote(path)


def names(items: list, limit: int = 4) -> str:
    return ", ".join(items[:limit]) + (f" +{len(items) - limit} more" if len(items) > limit else "")


@dataclass
class ToolState:
    """Everything --status knows about one tool, before a word is printed."""
    tool: Tool
    detected: bool = True
    stamp: Optional[dict] = None
    skills: dict = field(default_factory=lambda: {k: [] for k in (
        "present", "stale", "edited", "missing", "blocked", "foreign", "links", "old", "elsewhere")})
    agents: dict = field(default_factory=lambda: {k: [] for k in (
        "present", "stale", "edited", "missing", "foreign")})
    has_agents: bool = True
    adoptable: bool = False          # agents named like ours and no install record
    hooks: list = field(default_factory=list)     # [(label, on, state, line for --verbose)]
    shadow: list = field(default_factory=list)
    index: Optional[tuple] = None    # (exists, rows) for a tool that needs an agent index
    record: list = field(default_factory=list)

    @property
    def installed(self) -> bool:
        return self.detected and bool(self.stamp is not None or self.skills["present"]
                                      or self.agents["present"])

    @property
    def suite(self) -> bool:
        stamp = self.stamp or {}
        return bool(stamp.get("suite", "skills" not in stamp and bool(stamp)))

    @property
    def behind(self) -> list:
        """What a refresh would bring, by name. A file missing from an install
        of the whole catalog counts; from a partial one it was never asked for."""
        out = list(self.skills["stale"]) + [f"agent {a}" for a in self.agents["stale"]]
        if self.suite:
            out += self.skills["missing"] + [f"agent {a}" for a in self.agents["missing"]]
        out += [f"{label} script" for label, on, state, _ in self.hooks if on and state != "current"]
        return out

    @property
    def edited(self) -> list:
        return list(self.skills["edited"]) + [f"agent {a}" for a in self.agents["edited"]]

    @property
    def state(self) -> str:
        if not self.detected:
            return NOT_DETECTED
        if not self.installed:
            return NOTHING
        return OUT_OF_DATE if self.behind else UP_TO_DATE


def tool_state(tool: Tool, agents: dict, skills_by_name: dict, project=None, catalog=None) -> ToolState:
    """The state of one tool. Out-of-date is decided by re-rendering: a skill is
    compared byte-for-byte, an agent is re-composed through the same path the
    installer uses and compared to the file on disk. Anything the catalog does
    not own is counted and never touched."""
    st = ToolState(tool, has_agents=tool.agents_dir is not None)
    if not tool.config_root.exists():
        st.detected = False
        return st
    st.stamp = stamp = run_for(tool).stamp
    here = present_skills(tool.skills_dir, skills_by_name)
    sk_ = st.skills
    if tool.skills_dir.exists():
        for d in sorted(p for p in tool.skills_dir.iterdir() if p.is_dir() or p.is_symlink()):
            kind, sk = classify_skill(d, stamp)
            if kind in (FOREIGN, LINK, RETIRED):
                sk_[{FOREIGN: "foreign", LINK: "links", RETIRED: "old"}[kind]].append(d.name)
                continue
            if kind == ELSEWHERE:
                sk_["elsewhere"].append(f"{sk.name} as {d.name}")
                continue
            sk_["present"].append(d.name)
            if kind == EDITED:
                sk_["edited"].append(d.name)
                continue
            fresh = render_skill((sk.path / "SKILL.md").read_text(encoding="utf-8"),
                                 sk.agent, d.name, here)
            if fresh != (d / "SKILL.md").read_text(encoding="utf-8"):
                sk_["stale"].append(d.name)
    # Ours is not there because something that is not ours has its name: a
    # refresh leaves that alone, so it is not something a refresh would bring.
    taken = set(sk_["foreign"]) | set(sk_["links"])
    absent = set(skills_by_name) - set(sk_["present"]) - {x.split(" as ")[0] for x in sk_["elsewhere"]}
    sk_["blocked"] = sorted(absent & taken)
    sk_["missing"] = sorted(absent - taken)
    st.shadow = shadow_report(tool, skills_by_name, project)

    if tool.agents_dir is not None:
        ag_ = st.agents
        files = sorted(tool.agents_dir.glob(f"*{agent_suffix(tool)}")) if tool.agents_dir.exists() else []
        for f in files:
            kind = classify_agent(f, set(agents), stamp)
            if kind in (FOREIGN, LINK) or f.stem not in agents:
                ag_["foreign"].append(f.stem)
                continue
            ag_["present"].append(f.stem)
            if kind == EDITED:
                ag_["edited"].append(f.stem)
                continue
            inherited, dep_skills = resolve_deps(agents[f.stem], agents, skills_by_name)
            meta, desc, body = compose_agent(agents[f.stem], inherited)
            _, fresh = render_agent(tool, f.stem, body, desc,
                                    sorted(s.name for s in dep_skills), meta,
                                    guard=guard_command(tool), verify=verify_command(tool))
            # Compared as agent_hash does: a Kiro agent that Kiro upgraded
            # carries the host's own fields and is still current.
            if agent_hash(f) != agent_text_hash(fresh, f.name):
                ag_["stale"].append(f.stem)
        ag_["missing"] = sorted(set(agents) - set(ag_["present"]))
        # An install from before records: its agents look like ours but nothing
        # records them, so nothing updates them on its own.
        st.adoptable = stamp is None and any(f.stem in agents for f in files)

    if tool.agent_style in GUARD_STYLES:
        for label, on, dest, source, line in (
                ("shell-write guard", guard_on(tool), guard_path(tool), GUARD_SOURCE, guard_status(tool)),
                ("verify hook", verify_on(tool), verify_path(tool), VERIFY_SOURCE, verify_status(tool))):
            state = ("off" if not on else "missing" if not dest.is_file()
                     else "current" if file_hash(dest) == file_hash(source) else "stale")
            st.hooks.append((label, on, state, line))
    if catalog:
        st.record = provenance_line(tool, catalog, bool(st.behind))
    if tool.agent_style == "roster_md":
        roster = tool.roster
        rows = (len(re.findall(r"^\| `[a-z-]+` \|", roster.read_text(encoding="utf-8"), re.M))
                if roster.exists() else 0)
        st.index = (roster.exists(), rows)
    return st


def status_warnings(st: ToolState, project=None) -> list:
    """What is off in a tool that a refresh alone does not say, each with the
    command that deals with it."""
    tool, key, out = st.tool, st.tool.key, []
    scope = f" --project {project}" if project else ""
    if st.skills["old"]:
        n = len(st.skills["old"])
        out.append((f"{key}: {n} old cop{'y' if n == 1 else 'ies'} of a skill the catalog renamed or "
                    f"dropped: {names(st.skills['old'])}",
                    "Safe to delete: rm -r " + " ".join(
                        shell_arg(show_path(tool.skills_dir / x, project)) for x in st.skills["old"])))
    if st.skills["blocked"] and st.suite:
        n = len(st.skills["blocked"])
        out.append((f"{key}: {names(st.skills['blocked'])} {'is' if n == 1 else 'are'} not installed: "
                    f"{'a skill' if n == 1 else 'skills'} not from this catalog "
                    f"{'has that name' if n == 1 else 'have those names'}.",
                    f"To install ours beside {'it' if n == 1 else 'them'}: "
                    + command("install", "--all", f"--tool {key}", scope, "--on-conflict rename")))
    for d, n, owner in st.shadow:
        out.append((f"{key}: {n} skill{'s' if n != 1 else ''} also read from {show_path(d, project)} "
                    f"{'are' if n != 1 else 'is'} out of date there; {key} may load either copy.",
                    "Try: " + command("install", "--all", f"--tool {owner}", scope) if owner else ""))
    if st.index is not None and st.agents["present"]:
        exists, rows = st.index
        if not exists:
            out.append((f"{key}: the agent index ({tool.roster.name}) is missing; the "
                        f"{len(st.agents['present'])} agents there cannot be reached without it.",
                        "Try: " + command("install", "--all", f"--tool {key}", scope)))
        elif rows != len(st.agents["present"]):
            out.append((f"{key}: the agent index ({tool.roster.name}) lists {rows} agents and "
                        f"{len(st.agents['present'])} are installed.",
                        "Try: " + command("install", "--all", f"--tool {key}", scope)))
    if st.adoptable:
        out.append((f"{key}: agents named like the catalog's, with no install record: nothing "
                    f"updates them.",
                    "To adopt them (it replaces them): "
                    + command("install", "--all", f"--tool {key}", scope, "--on-conflict overwrite")))
    return out


def wrapped(text: str, indent: int, first: str = "") -> str:
    """`first` + text, folded to 80 columns with the rest indented."""
    import textwrap
    return textwrap.fill(text, width=80, initial_indent=first, subsequent_indent=" " * indent,
                         break_long_words=False, break_on_hyphens=False)


def print_status(agents, skills_by_name, project=None, catalog=None, verbose=False):
    """`--status`: the answer first, one row per tool, the rest on request."""
    states = [tool_state(project_tool(t, project) if project else t,
                         agents, skills_by_name, project, catalog) for t in TOOLS]
    installed = [s for s in states if s.installed]
    behind = [s for s in installed if s.behind]
    scope = f" --project {project}" if project else ""
    if not installed:
        print("Nothing from this catalog is installed yet.")
    elif behind:
        print(f"{len(behind)} of {len(installed)} tool{'s' if len(installed) != 1 else ''} "
              f"{'are' if len(behind) != 1 else 'is'} out of date.")
    else:
        print("Everything installed is up to date.")
    if project:
        print(f"Project: {project}")
    print()

    for st in states:
        tool, key = st.tool, st.tool.key
        if verbose:
            label = tool.label.replace(" — ", ", ")     # plain ASCII: readable in any console
            print(f"{key} ({label})  {show_path(tool.config_root, project)}")
            print(f"  state     {st.state if st.state != OUT_OF_DATE else f'{len(st.behind)} out of date'}")
            if not st.detected:
                print()
                continue
            for title, total, grp, extra in (
                    ("skills", len(skills_by_name), st.skills,
                     (("not from this catalog", "foreign"), ("links, not touched", "links"),
                      ("old copies", "old"), ("installed as", "elsewhere"))),
                    ("agents", len(agents), st.agents, (("not from this catalog", "foreign"),))):
                if title == "agents" and not st.has_agents:
                    print("  agents    this tool has no place for agent files")
                    continue
                print(f"  {title:9} {len(grp['present'])} of {total} installed")
                for label, k in (("out of date", "stale"), ("edited by hand", "edited"),
                                 ("missing", "missing"),
                                 ("not installed, the name is taken", "blocked")) + extra:
                    if k not in grp:
                        continue
                    if grp[k]:
                        print(wrapped(f"{len(grp[k])} {label}: {names(grp[k], 8)}", 12, " " * 12))
            lead = "  options   "
            for _, on, _, line in st.hooks:
                if on:
                    print(wrapped(line, 12, lead))
                    lead = " " * 12
            off = [(label, line) for label, on, _, line in st.hooks if not on]
            if off:
                print(wrapped(", ".join(line for _, line in off), 12, lead))
                for i, (label, _) in enumerate(off):
                    print(('            enable: ' if i == 0 else ' ' * 20) + command(
                        "refresh", f"--{'shell-write-guard' if 'guard' in label else 'verify-hook'}"))
            for i, line in enumerate(st.record):
                print(wrapped(line, 12, "  record    " if i == 0 else " " * 12))
            if st.index is not None and st.index[0]:
                print(f"  index     {st.index[1]} rows in {tool.roster.name}")
            print()
            continue
        if st.state == NOT_DETECTED:
            print(f"  {key:<13} {NOT_DETECTED:<15} ({show_path(tool.config_root, project)} does not exist)")
        elif st.state == NOTHING:
            print(f"  {key:<13} {NOTHING}")
        else:
            have = f"{len(st.agents['present'])} agents, {len(st.skills['present'])} skills"
            if st.behind:
                print(wrapped(f"{len(st.behind)} out of date".ljust(15) + " " + names(st.behind), 16,
                              f"  {key:<13} "))
            else:
                print(f"  {key:<13} {UP_TO_DATE:<15} {have}")
            if st.edited:
                print(wrapped(f"{len(st.edited)} edited by hand, kept as "
                              f"{'it is' if len(st.edited) == 1 else 'they are'}: {names(st.edited)}",
                              16, " " * 16))
    if not verbose:
        print()

    warnings = [w for st in states for w in status_warnings(st, project)]
    for what, fix in warnings:
        print(wrapped(what, 2, "! "))
        # A command is never folded: one that does not fit goes on its own line.
        if fix and len(fix) > 78 and ": " in fix:
            say, to_run = fix.split(": ", 1)
            print(f"  {say}:\n    {to_run}")
        elif fix:
            print(f"  {fix}")
    if warnings:
        print()

    if not installed:
        first = next((s.tool.key for s in states if s.detected), TOOLS[0].key)
        print(f"Next: {command('install', '--all', f'--tool {first}', scope)}\n"
              f"      or, to choose from a menu: {command('menu', scope)}")
    elif behind:
        print(f"Next: {command('refresh', scope)}\n"
              f"      Updates only files this installer wrote. Files edited by hand\n"
              f"      and files not from this catalog stay as they are.")
    else:
        head = git(catalog, "rev-parse", "--short=7", "HEAD") if catalog else None
        where = f"Catalog {head}. " if head else ""
        if not verbose:
            print(f"{where}Details: {command('status', '--verbose', scope)}")
        elif head:
            print(where.strip())


def print_list(agents, all_skills, skills_by_name):
    print(f"Agents ({len(agents)})")
    for n, a in sorted(agents.items()):
        # Installing an agent also brings what it inherits and links to, so the
        # count that matches the disk is resolve_deps', not the agent's own.
        _, deps = resolve_deps(a, agents, skills_by_name)
        print(f"  {n:<16} {plural(len(a.skills), 'skill')} of its own, {len(deps)} installed with it")
        print(wrapped(", ".join(s.name for s in a.skills), 19, " " * 19))
    print(f"\nSkills: {len(all_skills)} in all. One alone: {command('install', '--skill <name>', '--tool <tool>')}")
    print("\nTools")
    for t in TOOLS:
        mark = "available" if t.config_root.exists() else NOT_DETECTED
        holds = "agents and skills" if t.agents_dir else "skills only"
        print(f"  {t.key:<13} {mark:<15} {holds}")
    print(wrapped("`shared` is ~/.agents, a folder opencode and Codex both read skills from.", 2, "  "))


def main():
    ap = Parser(description="Install catalog agents/skills into a tool's global config.")
    ap.add_argument("--catalog", type=Path, default=Path(__file__).resolve().parent,
                    help="catalog root (default: the clone this script sits in)")
    ap.add_argument("--list", action="store_true", help="list agents, skills, tools and exit")
    ap.add_argument("--project", type=Path, nargs="?", const=Path("."), default=None,
                    metavar="PATH",
                    help="install into a project checkout (default: cwd) instead of "
                         "your home config, so the setup travels with the repo")
    ap.add_argument("--status", action="store_true",
                    help="show what is installed in each tool and whether it is current")
    ap.add_argument("--verbose", action="store_true",
                    help="one line per file when installing, refreshing or uninstalling; with "
                         "--status, every tool in full")
    ap.add_argument("--refresh", action="store_true",
                    help="reinstall the whole suite into every tool that already holds "
                         "a catalog install (overwrites catalog files only)")
    ap.add_argument("--uninstall", action="store_true",
                    help="remove what the installer put, and only that: catalog files that are "
                         "still as installed. Edited copies and anything foreign stay. Every "
                         "tool that holds an install, or the one named with --tool")
    ap.add_argument("--all", action="store_true", help="install the whole suite (all agents + skills)")
    ap.add_argument("--agent", action="append", default=[], help="agent name to install (repeatable)")
    ap.add_argument("--skill", action="append", default=[], help="skill as agent:skill or name (repeatable)")
    ap.add_argument("--tool", help=f"target tool key ({', '.join(TOOLS_BY_KEY)})")
    ap.add_argument("--on-conflict", choices=["ask", "overwrite", "rename", "skip"], default="ask")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen, change nothing")
    ap.add_argument("--no-deps", action="store_true",
                    help="install only the agent's own skills; skip inherited/cross-agent deps")
    guard = ap.add_mutually_exclusive_group()
    guard.add_argument("--shell-write-guard", dest="shell_write_guard", action="store_true",
                       default=None,
                       help="Claude Code: hook a PreToolUse guard into every `full` agent that "
                            "refuses file writes through Bash (B-083). Remembered by --refresh")
    guard.add_argument("--no-shell-write-guard", dest="shell_write_guard", action="store_false",
                       help="Claude Code: take the shell-write guard out again")
    verify = ap.add_mutually_exclusive_group()
    verify.add_argument("--verify-hook", dest="verify_hook", metavar="CMD", nargs="?",
                        const="", default=None,
                        help="Claude Code: hook a `Stop` hook into every `full` agent that runs "
                             "the check each repo declares in .local-agents/verify when the agent "
                             "tries to finish and, if it fails, sends the failure back once "
                             "(B-084). CMD, optional, is the default for repos that declare "
                             "none. Remembered by --refresh")
    verify.add_argument("--no-verify-hook", dest="verify_hook", action="store_const", const=False,
                        help="Claude Code: take the verify hook out again")
    args = ap.parse_args()
    global SHELL_GUARD_CHOICE, VERIFY_CHOICE
    SHELL_GUARD_CHOICE = args.shell_write_guard
    VERIFY_CHOICE = args.verify_hook

    catalog = args.catalog
    if not catalog.exists():
        fail(f"no catalog at {catalog}.",
             hint="Try: run install.py from a clone of the catalog, or pass --catalog <path>")
    agents, all_skills = discover(catalog)
    if not agents and not all_skills:
        fail(f"{catalog} does not look like the catalog: no agents or skills in it.",
             hint="Try: run install.py from a clone of the catalog, or pass --catalog <path>")
    # skill names are unique across the catalog → safe to map by name
    skills_by_name = {}
    for s in all_skills:
        skills_by_name.setdefault(s.name, s)

    project = None
    if args.project is not None:
        project = args.project.resolve()
        if not project.is_dir():
            fail(f"--project needs a folder; {project} is not one.")
        if project == catalog.resolve():
            fail("that folder is the catalog itself.",
                 "Pass the project you want to install into: --project <path>", refused=True)

    scope = f" --project {project}" if project else ""
    tools_line = listed("Tools", TOOLS_BY_KEY)
    first_tool = next((t.key for t in TOOLS
                       if (project_tool(t, project) if project else t).config_root.exists()), TOOLS[0].key)

    def known_tool(key: str) -> None:
        if key not in TOOLS_BY_KEY:
            fail(f"unknown tool '{key}'.", tools_line, *did_you_mean(key, TOOLS_BY_KEY))

    def target(tool: Tool) -> Tool:
        if not project:
            return tool
        tool = project_tool(tool, project)
        refuse_shared_project_dir(tool, agents)
        return tool

    if args.list:
        print_list(agents, all_skills, skills_by_name)
        return

    if args.status:
        print_status(agents, skills_by_name, project, catalog, args.verbose)
        return

    REPORT.verbose, REPORT.dry_run, REPORT.project = args.verbose, args.dry_run, project
    head = git(catalog, "rev-parse", "--short=7", "HEAD")
    REPORT.commit = head
    from_catalog = f"catalog {head}" if head else "the catalog"

    def into(tool: Tool) -> str:
        return f"{tool.key} ({show_path(tool.config_root, project)})"

    # One stale copy is enough for a host that reads several skill dirs to load
    # it (see shadow_report), so refresh every catalog install, not one tool.
    if args.refresh:
        # Per project, shared and antigravity share `.agents/` and its stamp, so
        # the stamp alone cannot say which one is installed — the agent files can.
        installed = []
        for t in TOOLS:
            here = project_tool(t, project) if project else t
            if (here.config_root / MANIFEST).is_file() and not shared_dir_owner(here, agents):
                installed.append(t)
        if not installed:
            fail("nothing to refresh: no catalog install found"
                 + (f" in {project}." if project else "."),
                 hint="Try: " + command("install", "--all", f"--tool {first_tool}", scope))
        # `update`, not `overwrite`: a refresh brings what we installed up to
        # date and leaves everything else — foreign, edited, links — alone.
        REPORT.mode = "refresh"
        REPORT.open(f"Updating {plural(len(installed), 'tool')} from {from_catalog}")
        for t in installed:
            refresh_tool(target(t), args.dry_run, agents, skills_by_name, catalog)
        REPORT.finish(scope)
        return

    if args.uninstall:
        if args.all or args.agent or args.skill:
            fail("--uninstall removes a whole install and cannot be combined with --all, "
                 "--agent or --skill.",
                 hint="Try: " + command("uninstall", f"--tool {args.tool}" if args.tool else "", scope))
        if args.tool:
            known_tool(args.tool)
        targets, seen = [], set()
        for t in ([TOOLS_BY_KEY[args.tool]] if args.tool else TOOLS):
            here = project_tool(t, project) if project else t
            # Per project, shared and antigravity are one `.agents/` and one install record.
            if here.config_root in seen:
                if here.agent_style == "roster_md" and (here.config_root / MANIFEST).is_file():
                    targets.append((here, True))
                continue
            seen.add(here.config_root)
            if (here.config_root / MANIFEST).is_file():
                targets.append((here, False))
        if not targets:
            fail("nothing to uninstall: no catalog install found in "
                 f"{args.tool if args.tool else 'any tool'}"
                 + (f" under {project}." if project else "."),
                 hint="Try: " + command("status", scope))
        REPORT.mode = "uninstall"
        REPORT.open(f"Removing what this installer put in "
                    f"{plural(len([1 for _, twin in targets if not twin]), 'tool')}")
        twins = [here for here, twin in targets if twin]
        for here, twin in targets:
            if not twin:
                uninstall_tool(here, args.dry_run, agents)
        for here in twins:                # the same folder under its other name: only its index is left
            if remove_roster_block(here.roster, args.dry_run):
                REPORT.tallies[here.config_root].index = f"removed from {here.roster.name}"
        REPORT.finish(scope)
        return

    # Non-interactive: whole suite
    if args.all:
        if not args.tool:
            fail("--all needs a target tool.", tools_line,
                 hint="Try: " + command("install", "--all", f"--tool {first_tool}", scope))
        known_tool(args.tool)
        tool = target(TOOLS_BY_KEY[args.tool])
        REPORT.open(f"Installing the whole catalog into {into(tool)}")
        install_suite(tool, args.on_conflict, False, args.dry_run, agents, skills_by_name, catalog)
        REPORT.finish(scope)
        return

    # Non-interactive path
    if args.agent or args.skill:
        if not args.tool:
            asked = "".join(f" --agent {a}" for a in args.agent) + "".join(
                f" --skill {k}" for k in args.skill)
            fail("--agent and --skill need a target tool.", tools_line,
                 hint="Try: " + command("install", asked, f"--tool {first_tool}", scope))
        known_tool(args.tool)
        tool = target(TOOLS_BY_KEY[args.tool])
        skills_by_q = {s.qualified: s for s in all_skills}
        for name in args.agent:
            if name not in agents:
                fail(f"unknown agent '{name}'.", listed("Agents", sorted(agents)),
                     *did_you_mean(name, agents))
        for ref in args.skill:
            if not (skills_by_q.get(ref) or skills_by_name.get(ref)):
                fail(f"unknown skill '{ref}'.",
                     *did_you_mean(ref.split(":")[-1], skills_by_name),
                     hint="Try: " + command("list"))
        what = [f"agent {n}" for n in args.agent] + [f"skill {r.split(':')[-1]}" for r in args.skill]
        REPORT.open(wrapped(f"Installing {', '.join(what)} into {into(tool)}", 2))

        for name in args.agent:
            install_agent(agents[name], tool, args.on_conflict, False, args.dry_run,
                          agents, skills_by_name, with_deps=not args.no_deps)

        for ref in args.skill:
            sk = skills_by_q.get(ref) or skills_by_name.get(ref)
            REPORT.begin(tool)
            install_skill(sk, tool, args.on_conflict, False, args.dry_run)
        relink_skills(tool, skills_by_name, args.dry_run)
        # Once, after the last write — a relink after the stamp would read as a
        # hand edit next time.
        write_manifest(tool, catalog, args.dry_run)
        REPORT.finish(scope)
        return

    # Interactive path
    interactive(agents, all_skills, skills_by_name, args.on_conflict,
                args.dry_run, with_deps=not args.no_deps, project=project, catalog=catalog)
    REPORT.finish(scope)


if __name__ == "__main__":
    main()
