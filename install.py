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

No external dependencies — Python 3.9+ stdlib only.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
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
    Tool("shared", "Shared (~/.agents — skills read by opencode + Codex)",
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
        sys.exit(f"refusing to install {tool.key} into {tool.config_root}: it already "
                 f"holds the {other} install, and both write {tool.agents_dir}/<name>.md "
                 f"in different formats — the second would silently replace the first. "
                 f"Use one of them per project, or remove {tool.agents_dir} first.")


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
KIRO_TOOLS = {"read": ["read", "grep", "glob", "web_fetch", "web_search", "subagent"],
              "full": ["*"]}
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
GUARD_FRONTMATTER = ("hooks:\n"
                     "  PreToolUse:\n"
                     "    - matcher: \"Bash\"\n"
                     "      hooks:\n"
                     "        - type: command\n"
                     "          command: {command}\n")
SHELL_GUARD_CHOICE: Optional[bool] = None   # set by --shell-write-guard / --no-…


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
        print(f"    guard  → {dest}")
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(GUARD_SOURCE.read_bytes())
        return
    recorded = (run_for(tool).stamp or {}).get("shell_write_guard_sha256")
    if dest.is_file() and recorded and file_hash(dest) == recorded:
        print(f"    guard  → removed {dest} (--no-shell-write-guard)")
        if not dry_run:
            dest.unlink()


def guard_status(tool: Tool) -> str:
    """One line for --status: whether the guard is on, and whether the script
    on disk is the catalog's current one."""
    dest = guard_path(tool)
    if not guard_on(tool):
        extra = f" (a copy is still at {dest})" if dest.is_file() else ""
        return f"guard    shell-write guard off{extra} — enable: --refresh --shell-write-guard"
    if not dest.is_file():
        state = "script MISSING — the agents' hook fails open; reinstall"
    elif file_hash(dest) != file_hash(GUARD_SOURCE):
        state = "script stale — --refresh updates it"
    else:
        state = "script current"
    return f"guard    shell-write guard on · {state} · {dest}"


def access_of(meta: dict) -> str:
    tier = (meta or {}).get("access", "full")
    if tier not in ACCESS_TIERS:
        sys.exit(f"unknown access tier {tier!r} — expected one of {ACCESS_TIERS}")
    return tier


def render_agent(tool: Tool, name: str, body: str, description: str,
                 skill_names: list, meta: dict = None, guard: Optional[str] = None) -> tuple:
    """Return (destination_path, file_contents) for the agent in this tool's
    format. `meta` is the catalog AGENTS.md frontmatter (description/model/…).
    `guard` is the shell-write guard's hook command, or None (see
    guard_command). Add a branch here only for a genuinely new file format."""
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
        # B-083: the shell-write guard, only where the agent has a shell. The
        # read tier has no Bash, so a hook there would guard nothing.
        hooks_lines = (GUARD_FRONTMATTER.format(command=json.dumps(guard))
                       if guard and tier == "full" else "")
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
def resolve_name(dest_dir: Path, base: str, suffix: str, policy: str,
                 interactive: bool) -> Optional[str]:
    """Given a desired install name, return the final name to use, or None to
    skip. `suffix` is "" for skill folders or ".md"/".json" for agent files."""
    def exists(nm: str) -> bool:
        return (dest_dir / f"{nm}{suffix}").exists()

    if not exists(base):
        return base

    if policy == "overwrite":
        return base
    if policy == "skip":
        print(f"    · exists, skipping: {base}")
        return None
    if policy == "rename":
        return _auto_rename(exists, base)

    # policy == "ask"
    if not interactive:
        return _auto_rename(exists, base)  # safe default in non-interactive runs
    while True:
        ans = input(f"    '{base}{suffix}' already exists at {dest_dir}. "
                    f"[o]verwrite / [r]ename / [s]kip? ").strip().lower()
        if ans in ("o", "overwrite"):
            return base
        if ans in ("s", "skip"):
            return None
        if ans in ("r", "rename"):
            new = input(f"    new name (default {base}-2): ").strip() or f"{base}-2"
            if exists(new):
                print(f"    '{new}' also exists — try again.")
                continue
            return new


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
        print(f"    note   → {tool.label}: installed before install records existed, "
              f"from a commit this catalog cannot rebuild — hand edits there cannot be "
              f"told apart, and catalog files are updated")
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
                    inherited, deps = resolve_deps(ag, old_agents, old_by_name)
                except SystemExit:
                    # A commit from before `inherits:` existed cannot be
                    # rendered by today's rules; it must not abort the refresh.
                    return None
                meta, desc, body = compose_agent(ag, inherited)
                dest, text = render_agent(tool, name, body, desc, sorted(s.name for s in deps), meta)
                if dest.exists():
                    agents[dest.name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
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
    return OURS if recs[f.name] == file_hash(f) else EDITED


_SAFE = {
    FOREIGN: "not ours (no local-agents id)",
    LINK: "a link to another tool's copy",
    EDITED: "edited by hand since it was installed",
    "foreign agent": "not ours (no install record of it)",
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
        print(f"    · {what}: {_SAFE[LINK]} — left alone")
        return "skip"
    if policy == "overwrite":
        return "write"
    if policy == "rename" and kind == FOREIGN:
        return "rename"
    if policy == "ask" and interactive:
        while True:
            ans = input(f"    {what} is {why}. [o]verwrite / [s]kip? ").strip().lower()
            if ans in ("o", "overwrite"):
                return "write"
            if ans in ("s", "skip", ""):
                return "skip"
    print(f"    · {what}: {why} — left alone "
          f"(--on-conflict overwrite replaces it)")
    return "skip"


def copy_skill(skill: Skill, tool: Tool, name: str, dry_run: bool):
    dest = tool.skills_dir / name
    print(f"    skill  → {dest}")
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
    that — a foreign folder left with our SKILL.md next to its own files)."""
    if dry_run:
        return
    run = run_for(tool)
    present = present_skills(tool.skills_dir, skills_by_name)
    for name in sorted(present):
        d = tool.skills_dir / name
        if name not in run.skills_written and classify_skill(d, run.stamp)[0] != OURS:
            continue
        src = skills_by_name[name]
        md = d / "SKILL.md"
        fresh = render_skill((src.path / "SKILL.md").read_text(encoding="utf-8"),
                             src.agent, name, present)
        if md.read_text(encoding="utf-8") != fresh:
            md.write_text(fresh, encoding="utf-8")
            run.skills_written.add(name)


def sweep_retired(tool: Tool, dry_run: bool):
    """Remove our old copies that a renamed skill left behind — but only those
    that are ours (our id), replaced (that id is installed at its current
    name) and intact (the hash the stamp recorded under THIS old name). Until
    then a host lists both, with the same description, and may load the old
    one. Anything short of all three is kept and reported by --status: a
    duplicate costs less than a lost edit. A stamp from before B-058 has no
    record under the old name, so nothing is removed there."""
    if dry_run or not tool.skills_dir.is_dir():
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
            shutil.rmtree(d)
            print(f"    retired → removed {d.name} (now {sk.name})")


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
        sys.exit(f"{agent.name}/AGENTS.md declares no `inherits:` — add the list of "
                 f"agents it inherits from (`inherits: []` for none)")
    names = [n.strip() for n in raw.strip().strip("[]").split(",") if n.strip()]
    unknown = [n for n in names if n not in agents]
    if unknown:
        sys.exit(f"{agent.name}/AGENTS.md inherits from unknown agent(s): {', '.join(unknown)}")
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
    print(f"\n  Installing agent '{agent.name}' → {tool.label}")

    if with_deps:
        inherited, dep_skills = resolve_deps(agent, agents, skills_by_name)
    else:
        inherited, dep_skills = [], list(agent.skills)

    if not skip_skills:
        own = {s.name for s in agent.skills}
        extra = [s.name for s in dep_skills if s.name not in own]
        if inherited:
            print(f"    deps   → inherits (reasoning inlined): {', '.join(a.name for a in inherited)}")
        if extra:
            print(f"    deps   → extra skills pulled in: {', '.join(extra)}")

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
        print(f"    note   → {tool.label} has nowhere to put an agent body. "
              f"Skills installed above.")
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
                                  guard=guard_command(tool))
    print(f"    agent  → {dest}")
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
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
            print(f"    retire → {old} (pre-TOML roster body)")
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
        print(f"    keep   → roster block in {roster}: the shared install still uses it")
        return
    rest = (text[:text.index(ROSTER_BEGIN)]
            + text[text.index(ROSTER_END) + len(ROSTER_END):]).strip()
    print(f"    retire → roster block in {roster}")
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
            contents, verb = head + block + tail, "roster updated in"
        else:
            contents = current.rstrip() + "\n\n" + block + "\n"
            verb = "roster appended to"
    else:
        contents, verb = block + "\n", "roster written to"

    print(f"    {verb} → {dest}")
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
                  "scripts/shell_write_guard.py")   # copied by --shell-write-guard


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
    where = (f"@ {commit[:7]}{' (dirty tree)' if dirty else ''}" if commit
             else "(catalog is not a git checkout: no commit recorded)")
    print(f"    stamp  → {dest.name} {where}")
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
                agents[f.name] = file_hash(f)
            elif old_agents is not None and f.name in old_agents:
                agents[f.name] = old_agents[f.name]
            elif old_agents is None and old and f.stem in names:
                agents[f.name] = file_hash(f)   # a pre-B-058 stamp: ours, once
    return skills, agents


def read_manifest(tool: Tool):
    path = tool.config_root / MANIFEST
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def provenance_line(tool: Tool, catalog: Path, installed_names: set):
    """One or two lines describing how far behind this install is.

    Degrades honestly at every step: no manifest, no git, or a commit that is no
    longer in history (rebase, force-push, fresh clone) each get a specific
    message rather than a wrong number."""
    man = read_manifest(tool)
    if not man:
        return ["provenance: unknown — installed before stamping, or by hand"]
    was = man.get("catalog_commit") or ""
    if not was:
        return ["installed from a catalog that was not a git checkout — no commit to compare"]
    now = git(catalog, "rev-parse", "HEAD")
    if not now:
        return [f"installed from {was[:7]} (catalog is not a git checkout here)"]
    stamp = f"installed from {was[:7]}"
    if man.get("catalog_dirty"):
        stamp += " + uncommitted changes"
    if was == now:
        return [f"{stamp} — up to date with the catalog"]
    if git(catalog, "cat-file", "-e", f"{was}^{{commit}}") is None:
        return [f"{stamp} — that commit is not in this history "
                f"(rebased, or a different clone); reinstall to resync"]
    behind = git(catalog, "rev-list", "--count", f"{was}..{now}") or "?"
    out = [f"{stamp} — {behind} commit(s) behind {now[:7]}"]
    diff = git(catalog, "diff", "--name-only", was, now) or ""
    moved = sorted({
        m.group(1) for line in diff.splitlines()
        for m in [re.search(r"skills/([a-z][a-z-]*)/SKILL\.md$", line)]
        if m and m.group(1) in installed_names
    })
    agents_moved = sorted({
        m.group(1) for line in diff.splitlines()
        for m in [re.match(r"([a-z][a-z-]*)/AGENTS\.md$", line)]
        if m and m.group(1) in installed_names
    })
    for label, items in (("skills changed", moved), ("agents changed", agents_moved)):
        if items:
            out.append(f"  {label}: {', '.join(items[:8])}"
                       f"{f' +{len(items) - 8} more' if len(items) > 8 else ''}")
    return out


def install_suite(tool: Tool, policy: str, interactive: bool, dry_run: bool,
                  agents: dict, skills_by_name: dict, catalog: Path = None):
    """Install the WHOLE catalog — every skill once, then every agent file with
    its inheritance inlined. This guarantees all cross-agent handoffs, shared
    skills, and orchestration references resolve, because everything is present."""
    print(f"\n  Installing the WHOLE SUITE ({len(agents)} agents, "
          f"{len(skills_by_name)} skills) → {tool.label}")

    print("  — skills (each installed once) —")
    for name in sorted(skills_by_name):
        install_skill(skills_by_name[name], tool, policy, interactive, dry_run)
    relink_skills(tool, skills_by_name, dry_run)
    sweep_retired(tool, dry_run)

    if tool.agents_dir is None:
        print(f"  — {tool.label} has no named-agent slot: skills above are the install. —")
        return

    print("  — agents (inheritance inlined; skills already installed above) —")
    for name in sorted(agents):
        install_agent(agents[name], tool, policy, interactive, dry_run,
                      agents, skills_by_name, with_deps=True, skip_skills=True,
                      roster=False)

    if tool.agent_style == "roster_md":
        print("  — roster (no named-agent slot: the bodies above are indexed "
              "in AGENTS.md) —")
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
    print(f"\n  Refreshing what was installed → {tool.label}")
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
# Interactive menu
# --------------------------------------------------------------------------- #
def choose(prompt: str, options: list) -> Optional[int]:
    for i, o in enumerate(options, 1):
        print(f"  {i}. {o}")
    while True:
        raw = input(f"{prompt} (number, or q to quit): ").strip().lower()
        if raw in ("q", "quit", ""):
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return int(raw) - 1
        print("  invalid choice.")


def tool_menu_label(t: Tool) -> str:
    mark = "✓" if t.config_root.exists() else "·"
    return f"[{mark}] {t.label}  ({t.key})"


def interactive(agents, all_skills, skills_by_name, policy, dry_run, with_deps, project=None, catalog=None):
    print("\nWhat do you want to install?")
    mode = choose("select", ["The WHOLE suite (all agents + skills)",
                             "One agent (with its skills + inherited deps)",
                             "Standalone skill(s)"])
    if mode is None:
        return

    tool_idx = choose("target tool", [tool_menu_label(t) for t in TOOLS])
    if tool_idx is None:
        return
    tool = TOOLS[tool_idx]
    if project:
        tool = project_tool(tool, project)
        refuse_shared_project_dir(tool, agents)
    if not tool.config_root.exists():
        ans = input(f"  {tool.label} doesn't look installed ({tool.config_root} "
                    f"missing). Install anyway? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            return

    if mode == 0:
        install_suite(tool, policy, True, dry_run, agents, skills_by_name, catalog)
    elif mode == 1:
        names = sorted(agents)
        idx = choose("which agent", [f"{n}  ({len(agents[n].skills)} skills)" for n in names])
        if idx is None:
            return
        install_agent(agents[names[idx]], tool, policy, True, dry_run,
                      agents, skills_by_name, with_deps)
        write_manifest(tool, catalog, dry_run)
    else:
        labels = [s.qualified for s in all_skills]
        print("  (enter comma-separated numbers to install several)")
        for i, o in enumerate(labels, 1):
            print(f"  {i}. {o}")
        raw = input("which skill(s): ").strip()
        picks = [int(x) - 1 for x in re.split(r"[,\s]+", raw) if x.isdigit()]
        for p in picks:
            if 0 <= p < len(all_skills):
                install_skill(all_skills[p], tool, policy, True, dry_run)
        relink_skills(tool, skills_by_name, dry_run)
        write_manifest(tool, catalog, dry_run)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def shadow_report(tool: Tool, skills_by_name: dict, project=None) -> list:
    """Lines warning that this host sees a catalog skill in more than one dir
    and at least one copy is stale.

    A host that reads several skill dirs keeps ONE copy per name, and which one
    is not stable: measured on opencode 1.18.11, three identical runs took 32,
    10 and 4 of 48 skills from the project and the rest from global copies — one
    of them two months old. Identical copies make that harmless; a stale one
    makes the skill the host loads a coin toss. So the report is about stale
    copies, not duplicates, and it names the refresh that fixes each."""
    dirs = [tool.skills_dir, *tool.also_reads]
    owners, owner_tool = {}, {}
    for t in TOOLS:
        t = project_tool(t, project) if project else t
        owners.setdefault(t.skills_dir, t.key)
        owner_tool.setdefault(t.skills_dir, t)
    seen_twice, stale_in = 0, {}
    ours = {d: present_skills(d, skills_by_name) for d in dirs}   # a foreign same-name skill is not a copy of ours
    for name, src in skills_by_name.items():
        copies = [d for d in dirs if name in ours[d]]
        if len(copies) < 2:
            continue
        seen_twice += 1
        text = (src.path / "SKILL.md").read_text(encoding="utf-8")
        for d in copies:
            if d in owner_tool and classify_skill(d / name, run_for(owner_tool[d]).stamp)[0] == EDITED:
                continue   # kept on purpose, and refresh leaves it: not a stale copy
            fresh = render_skill(text, src.agent, name, ours[d])
            if (d / name / "SKILL.md").read_text(encoding="utf-8") != fresh:
                stale_in[d] = stale_in.get(d, 0) + 1
    if not stale_in:
        return []
    lines = [f"shadowing: {seen_twice} catalog skills are visible here from more "
             f"than one dir, and the host may load any copy — stale ones:"]
    for d, n in sorted(stale_in.items(), key=lambda kv: str(kv[0])):
        owner = owners.get(d)
        scope = f" --project {project}" if project else ""
        fix = (f"  → ./install.py --all --tool {owner}{scope}" if owner else "")
        lines.append(f"  {n} stale in {d}{fix}")
    return lines


def print_status(agents, skills_by_name, project=None, catalog=None):
    """What is actually installed in each tool, and whether it still matches the
    catalog. Answers the question `--list` cannot: not "what could I install"
    but "what is out there, and is it current".

    Staleness is decided by re-rendering: a skill is compared byte-for-byte, an
    agent is re-composed through the same path the installer uses and compared
    to the file on disk. Anything the catalog doesn't own is reported as foreign
    and never touched."""
    if project:
        print(f"scope: project {project}")
    for tool in TOOLS:
        if project:
            tool = project_tool(tool, project)
        if not tool.config_root.exists():
            state = "not set up here" if project else "not detected"
            print(f"\n{tool.label}  ({tool.key})\n  {state} — {tool.config_root} missing")
            continue
        print(f"\n{tool.label}  ({tool.key})\n  {tool.config_root}")

        # --- skills: who owns each folder, then whether ours is current ---
        stamp = run_for(tool).stamp
        here = present_skills(tool.skills_dir, skills_by_name)
        groups = {k: [] for k in ("stale", EDITED, FOREIGN, LINK, RETIRED, ELSEWHERE)}
        present = []
        if tool.skills_dir.exists():
            for d in sorted(p for p in tool.skills_dir.iterdir() if p.is_dir() or p.is_symlink()):
                kind, sk = classify_skill(d, stamp)
                if kind in (FOREIGN, LINK, RETIRED):
                    groups[kind].append(d.name)
                    continue
                if kind == ELSEWHERE:
                    groups[ELSEWHERE].append(f"{sk.name} as {d.name}")
                    continue
                present.append(d.name)
                if kind == EDITED:
                    groups[EDITED].append(d.name)
                    continue
                fresh = render_skill((sk.path / "SKILL.md").read_text(encoding="utf-8"),
                                     sk.agent, d.name, here)
                if fresh != (d / "SKILL.md").read_text(encoding="utf-8"):
                    groups["stale"].append(d.name)
        missing = sorted(set(skills_by_name) - set(present))
        counts = [f"{len(groups['stale'])} stale" if groups["stale"] else "",
                  f"{len(groups[EDITED])} edited by hand (refresh leaves them)" if groups[EDITED] else "",
                  f"{len(missing)} missing" if missing else "",
                  f"{len(groups[FOREIGN])} not ours (untouched)" if groups[FOREIGN] else "",
                  f"{len(groups[LINK])} links (untouched)" if groups[LINK] else "",
                  f"{len(groups[RETIRED])} retired copies" if groups[RETIRED] else "",
                  f"{len(groups[ELSEWHERE])} under another name" if groups[ELSEWHERE] else ""]
        print(f"    skills   {len(present)}/{len(skills_by_name)} from catalog"
              + "".join(f" · {c}" for c in counts if c))
        for label, items in (("stale", groups["stale"]), ("edited", groups[EDITED]),
                             ("missing", missing), ("links", groups[LINK]),
                             ("ours under another name", groups[ELSEWHERE])):
            if items:
                print(f"      {label}: {', '.join(items[:8])}"
                      f"{f' +{len(items) - 8} more' if len(items) > 8 else ''}")
        if groups[RETIRED]:
            # Ours, under a name the catalog no longer uses: a renamed or removed
            # skill, or a `-2` copy an older installer left. Nothing loads the
            # right one by that name any more; deleting is the user's call.
            print(f"      retired (ours, old name — safe to delete): {', '.join(groups[RETIRED])}")
            print(f"        rm -r " + " ".join(str(tool.skills_dir / n) for n in groups[RETIRED]))
        for line in shadow_report(tool, skills_by_name, project):
            print(f"    {line}")

        # --- agents: the stamp says which files we wrote ---
        if tool.agents_dir is None:
            print("    agents   (this tool has no place for agent bodies)")
            continue
        suffix = agent_suffix(tool)
        files = (sorted(tool.agents_dir.glob(f"*{suffix}")) if tool.agents_dir.exists() else [])
        a_present, a_foreign, a_edited, a_stale = [], [], [], []
        for f in files:
            kind = classify_agent(f, set(agents), stamp)
            if kind in (FOREIGN, LINK) or f.stem not in agents:
                a_foreign.append(f.stem)
                continue
            a_present.append(f.stem)
            if kind == EDITED:
                a_edited.append(f.stem)
                continue
            inherited, dep_skills = resolve_deps(agents[f.stem], agents, skills_by_name)
            meta, desc, body = compose_agent(agents[f.stem], inherited)
            _, fresh = render_agent(tool, f.stem, body, desc,
                                    sorted(s.name for s in dep_skills), meta,
                                    guard=guard_command(tool))
            if f.read_text(encoding="utf-8") != fresh:
                a_stale.append(f.stem)
        a_missing = sorted(set(agents) - set(a_present))
        if stamp is None and any(f.stem in agents for f in files):
            # An install from before stamps: its agents look like ours but
            # nothing records them, so nothing updates them on its own.
            print(f"    note     agents named like the catalog's, with no install record: "
                  f"install once with --all --tool {tool.key}"
                  f"{f' --project {project}' if project else ''} --on-conflict overwrite "
                  f"to adopt them (it replaces them)")
        print(f"    agents   {len(a_present)}/{len(agents)} from catalog"
              f"{f' · {len(a_stale)} stale' if a_stale else ''}"
              f"{f' · {len(a_edited)} edited by hand (refresh leaves them)' if a_edited else ''}"
              f"{f' · {len(a_missing)} missing' if a_missing else ''}"
              f"{f' · {len(a_foreign)} not ours (untouched)' if a_foreign else ''}")
        for label, items in (("stale", a_stale), ("edited", a_edited), ("missing", a_missing)):
            if items:
                print(f"      {label}: {', '.join(items)}")
        if tool.agent_style in GUARD_STYLES:
            print(f"    {guard_status(tool)}")

        if catalog:
            for line in provenance_line(tool, catalog, set(present) | set(a_present)):
                print(f"    {line}")

        if tool.agent_style == "roster_md":
            roster = tool.roster
            if not roster.exists():
                print("      roster: MISSING — the bodies above are unreachable "
                      "without it")
            else:
                rows = len(re.findall(r"^\| `[a-z-]+` \|", roster.read_text(encoding="utf-8"), re.M))
                mark = "" if rows == len(a_present) else f" (≠ {len(a_present)} bodies)"
                print(f"      roster: {rows} rows in {roster.name}{mark}")

    scope = f" --project {project}" if project else ""
    print(f"\ncatalog: {len(agents)} agents, {len(skills_by_name)} skills — bring every install "
          f"up to date:  ./install.py --refresh{scope}"
          f"\n  (it updates only what it installed; edited and foreign files stay as they are)")


def print_list(agents, all_skills, skills_by_name):
    print("\nAgents:")
    for n, a in sorted(agents.items()):
        # Installing an agent also brings what it inherits and links to, so the
        # count that matches the disk is resolve_deps', not the agent's own.
        _, deps = resolve_deps(a, agents, skills_by_name)
        print(f"  {n}  — {len(a.skills)} own skills ({len(deps)} installed with "
              f"inheritance): {', '.join(s.name for s in a.skills)}")
    print(f"\nSkills: {len(all_skills)} total (address as agent:skill)")
    print("\nTools:")
    key_w = max(len(t.key) for t in TOOLS)
    label_w = max(len(t.label) for t in TOOLS)
    for t in TOOLS:
        mark = "available" if t.config_root.exists() else "not detected"
        agentcap = "agents+skills" if t.agents_dir else "skills only"
        print(f"  {t.key:{key_w}}  {t.label:{label_w}}  [{mark}, {agentcap}]")


def main():
    ap = argparse.ArgumentParser(description="Install catalog agents/skills into a tool's global config.")
    ap.add_argument("--catalog", type=Path, default=Path(__file__).resolve().parent,
                    help="catalog root (default: the clone this script sits in)")
    ap.add_argument("--list", action="store_true", help="list agents, skills, tools and exit")
    ap.add_argument("--project", type=Path, nargs="?", const=Path("."), default=None,
                    metavar="PATH",
                    help="install into a project checkout (default: cwd) instead of "
                         "your home config, so the setup travels with the repo")
    ap.add_argument("--status", action="store_true",
                    help="show what is installed in each tool and whether it is current")
    ap.add_argument("--refresh", action="store_true",
                    help="reinstall the whole suite into every tool that already holds "
                         "a catalog install (overwrites catalog files only)")
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
    args = ap.parse_args()
    global SHELL_GUARD_CHOICE
    SHELL_GUARD_CHOICE = args.shell_write_guard

    catalog = args.catalog
    if not catalog.exists():
        sys.exit(f"catalog not found: {catalog}")
    agents, all_skills = discover(catalog)
    if not agents and not all_skills:
        sys.exit(f"no agents or skills found under {catalog}")
    # skill names are unique across the catalog → safe to map by name
    skills_by_name = {}
    for s in all_skills:
        skills_by_name.setdefault(s.name, s)

    project = None
    if args.project is not None:
        project = args.project.resolve()
        if not project.is_dir():
            sys.exit(f"project path is not a directory: {project}")
        if project == catalog.resolve():
            sys.exit("refusing to install into the catalog itself — pass the path of "
                     "the project that should receive the agents")

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
        print_status(agents, skills_by_name, project, catalog)
        return

    if args.dry_run:
        print("=== DRY RUN — no files will be written ===")

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
            sys.exit("--refresh: no tool here holds a catalog install (no "
                     f"{MANIFEST} found) — install one with --all --tool <key>")
        # `update`, not `overwrite`: a refresh brings what we installed up to
        # date and leaves everything else — foreign, edited, links — alone.
        for t in installed:
            refresh_tool(target(t), args.dry_run, agents, skills_by_name, catalog)
        return

    # Non-interactive: whole suite
    if args.all:
        if not args.tool:
            sys.exit("--tool is required with --all")
        if args.tool not in TOOLS_BY_KEY:
            sys.exit(f"unknown tool '{args.tool}'. Known: {', '.join(TOOLS_BY_KEY)}")
        install_suite(target(TOOLS_BY_KEY[args.tool]), args.on_conflict, False, args.dry_run,
                      agents, skills_by_name, catalog)
        return

    # Non-interactive path
    if args.agent or args.skill:
        if not args.tool:
            sys.exit("--tool is required with --agent/--skill")
        if args.tool not in TOOLS_BY_KEY:
            sys.exit(f"unknown tool '{args.tool}'. Known: {', '.join(TOOLS_BY_KEY)}")
        tool = target(TOOLS_BY_KEY[args.tool])

        for name in args.agent:
            if name not in agents:
                sys.exit(f"unknown agent '{name}'. Known: {', '.join(sorted(agents))}")
            install_agent(agents[name], tool, args.on_conflict, False, args.dry_run,
                          agents, skills_by_name, with_deps=not args.no_deps)

        skills_by_q = {s.qualified: s for s in all_skills}
        for ref in args.skill:
            sk = skills_by_q.get(ref) or skills_by_name.get(ref)
            if not sk:
                sys.exit(f"unknown skill '{ref}'. Use --list to see options.")
            print(f"\n  Installing skill '{sk.qualified}' → {tool.label}")
            install_skill(sk, tool, args.on_conflict, False, args.dry_run)
        relink_skills(tool, skills_by_name, args.dry_run)
        # Once, after the last write — a relink after the stamp would read as a
        # hand edit next time.
        write_manifest(tool, catalog, args.dry_run)
        return

    # Interactive path
    interactive(agents, all_skills, skills_by_name, args.on_conflict,
                args.dry_run, with_deps=not args.no_deps, project=project, catalog=catalog)


if __name__ == "__main__":
    main()
