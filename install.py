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

No external dependencies — Python 3.9+ stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

HOME = Path.home()


def env_dir(var: str, default: Path) -> Path:
    """Honour a tool's own config-dir override when it defines one.

    Only two of the five do: Claude Code reads CLAUDE_CONFIG_DIR (multi-account
    setups) and Codex reads CODEX_HOME. opencode's docs prescribe a literal
    `~/.config/opencode` with no env override — it is NOT XDG-aware, so do not
    "fix" it to use XDG_CONFIG_HOME. Kiro publishes no such variable."""
    value = os.environ.get(var)
    return Path(value).expanduser() if value else default


CLAUDE_ROOT = env_dir("CLAUDE_CONFIG_DIR", HOME / ".claude")
CODEX_ROOT = env_dir("CODEX_HOME", HOME / ".codex")


# --------------------------------------------------------------------------- #
# TOOL REGISTRY
#
# To add a tool: append one Tool(...) below. That's it — UNLESS the tool needs
# a brand-new agent-file FORMAT, in which case also add a branch in
# render_agent(). Existing styles: "claude_md", "opencode_md", "kiro_json".
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
    agent_style: Optional[str]   # "claude_md" | "opencode_md" | "kiro_json" | "roster_md"
    project_dir: str             # per-repo config dir, relative to the project root
    roster_file: Optional[Path] = None   # roster destination; defaults to config_root/AGENTS.md

    @property
    def roster(self) -> Path:
        return self.roster_file or (self.config_root / "AGENTS.md")


# `roster_md` is for tools with no named-agent concept (Codex, and the shared
# folder). The bodies still get copied — self-contained, same as everywhere else
# — and a short roster is written into the tool's AGENTS.md pointing at them, so
# the identities are discoverable without paying 14 full prompts of context on
# every session.
TOOLS = [
    Tool("claude", "Claude Code",
         CLAUDE_ROOT, CLAUDE_ROOT / "skills",
         CLAUDE_ROOT / "agents", "claude_md", ".claude"),
    Tool("opencode", "opencode",
         HOME / ".config/opencode", HOME / ".config/opencode/skills",
         HOME / ".config/opencode/agents", "opencode_md", ".opencode"),
    Tool("kiro", "Kiro CLI",
         HOME / ".kiro", HOME / ".kiro/skills",
         HOME / ".kiro/agents", "kiro_json", ".kiro"),
    Tool("codex", "Codex",
         CODEX_ROOT, CODEX_ROOT / "skills",
         CODEX_ROOT / "agents", "roster_md", ".codex"),
    Tool("shared", "Shared (~/.agents — read by opencode + Codex)",
         HOME / ".agents", HOME / ".agents/skills",
         HOME / ".agents/agents", "roster_md", ".agents"),
]


def project_tool(tool: Tool, root: Path) -> Tool:
    """Retarget a tool at a project checkout instead of the user's home.

    Every supported tool reads a per-repo config dir, so the same rendering
    works — only the destination moves. Codex is the exception worth knowing:
    per-project it reads `AGENTS.md` from the REPO ROOT, not from inside
    `.codex/`, so the roster goes there."""
    base = root / tool.project_dir
    return replace(
        tool,
        label=f"{tool.label} — project {root.name}/",
        config_root=base,
        skills_dir=base / "skills",
        agents_dir=(base / "agents") if tool.agents_dir else None,
        roster_file=(root / "AGENTS.md") if tool.agent_style == "roster_md" else None,
    )

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
    """Find agents (dirs with AGENTS.md) and every skill (dirs with SKILL.md)."""
    agents: dict[str, Agent] = {}
    all_skills: list[Skill] = []

    for agents_md in sorted(catalog.glob("*/AGENTS.md")):
        agent_dir = agents_md.parent
        name = agent_dir.name
        skills = []
        for skill_md in sorted(agent_dir.glob("skills/*/SKILL.md")):
            sk = Skill(name=skill_md.parent.name, agent=name, path=skill_md.parent)
            skills.append(sk)
            all_skills.append(sk)
        agents[name] = Agent(name=name, path=agent_dir, agents_md=agents_md, skills=skills)

    # Also catch any skill folders not under a discovered agent (defensive).
    for skill_md in sorted(catalog.glob("skills/*/SKILL.md")):
        all_skills.append(Skill(name=skill_md.parent.name, agent=None, path=skill_md.parent))

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
def render_agent(tool: Tool, name: str, body: str, description: str,
                 skill_names: list, meta: dict = None) -> tuple:
    """Return (destination_path, file_contents) for the agent in this tool's
    format. `meta` is the catalog AGENTS.md frontmatter (description/model/…).
    Add a branch here only for a genuinely new file format."""
    meta = meta or {}
    desc = meta.get("description") or description
    if tool.agent_style == "claude_md":
        fm = ("---\n"
              f"name: {name}\n"
              f"{yaml_description(desc)}\n"
              f"model: {meta.get('model', 'inherit')}\n"
              f"memory: {meta.get('memory', 'user')}\n"
              "---\n\n")
        return tool.agents_dir / f"{name}.md", fm + body
    if tool.agent_style == "opencode_md":
        fm = f"---\n{yaml_description(desc)}\nmode: {meta.get('mode', 'primary')}\n---\n\n"
        return tool.agents_dir / f"{name}.md", fm + body
    if tool.agent_style == "kiro_json":
        obj = {
            "name": name,
            "description": desc,
            "prompt": body,
            # Kiro tool tags, not free-form names: `write` already covers editing
            # and deleting, and there is no `edit` tool — an unknown tag is a
            # config error, so keep this list in sync with USAGE.md's Kiro recipe.
            "tools": ["read", "write", "shell"],
            "allowedTools": ["read"],
            "resources": [f"skill://~/.kiro/skills/{s}/SKILL.md" for s in skill_names],
        }
        return tool.agents_dir / f"{name}.json", json.dumps(obj, indent=2, ensure_ascii=False)
    if tool.agent_style == "roster_md":
        # No frontmatter: nothing parses it here. The lead paragraph states what
        # the file is so a model that opens it knows immediately.
        head = (f"# `{name}` agent\n\n"
                f"Adopt this identity fully when the task matches its row in the "
                f"agent catalog (`../AGENTS.md`). Load the skills it references "
                f"when their triggers fire.\n\n---\n\n")
        return tool.agents_dir / f"{name}.md", head + body
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
def copy_skill(skill: Skill, tool: Tool, name: str, dry_run: bool):
    dest = tool.skills_dir / name
    print(f"    skill  → {dest}")
    if dry_run:
        return name
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(skill.path, dest)
    # keep frontmatter name in sync with the (possibly renamed) folder
    md = dest / "SKILL.md"
    if md.exists():
        md.write_text(rewrite_skill_name(md.read_text(), name))
    return name


def install_skill(skill: Skill, tool: Tool, policy: str, interactive: bool, dry_run: bool):
    final = resolve_name(tool.skills_dir, skill.name, "", policy, interactive)
    if final is None:
        return None
    return copy_skill(skill, tool, final, dry_run)


# Inheritance in this catalog is a documented convention (see root AGENTS.md):
# every agent inherits `generalist`'s reasoning; "peer" agents also adopt the
# `senior-dev` Peer Contract. A `../X/AGENTS.md` link counts as inheritance ONLY
# when X is one of these sources AND its trigger phrase sits near the link — so a
# "close peer of ux-ui" handoff mention is never mistaken for inheritance.
# To add an inheritance source: add "agent-name": "trigger phrase" here, and give
# that agent a CORE.md (curated always-on essence) that gets inlined into its
# children — without CORE.md the installer falls back to inlining the full body.
INHERIT_SOURCES = {
    "generalist": "reasoning model",
    "senior-dev": "peer contract",
}


def scan_refs(text: str):
    """Return (inherited_agent_names, skill_names) referenced in `text`.
    Skill links are matched by name (names are unique across the catalog)."""
    inherited = []
    for m in re.finditer(r"(?:\.\./)+([a-z][a-z-]*)/AGENTS\.md", text):
        trigger = INHERIT_SOURCES.get(m.group(1))
        if trigger and trigger in text[max(0, m.start() - 140):m.end() + 140].lower():
            inherited.append(m.group(1))
    skills = set(re.findall(r"skills/([a-z][a-z-]*)/SKILL\.md", text))
    return inherited, skills


def resolve_deps(agent: Agent, agents: dict, skills_by_name: dict):
    """Transitive closure of what `agent` needs: the ordered list of agents whose
    reasoning it inherits (to inline) and the set of skills to install."""
    inherited_order, seen = [], set()
    skill_names = set()

    def walk(ag: Agent):
        texts = [ag.agents_md.read_text()]
        for sk in ag.skills:
            skill_names.add(sk.name)
            texts.append((sk.path / "SKILL.md").read_text())
        for txt in texts:
            inh, sref = scan_refs(txt)
            skill_names.update(sref)
            for pname in inh:
                if pname in agents and pname not in seen and pname != ag.name:
                    seen.add(pname)
                    inherited_order.append(agents[pname])
                    walk(agents[pname])

    walk(agent)
    skills = [skills_by_name[n] for n in sorted(skill_names) if n in skills_by_name]
    return inherited_order, skills


def compose_agent(agent: Agent, inherited: list):
    """Build the agent body exactly as it gets installed: own body plus the
    inherited CORE.md sections. Shared with `--status`, which re-renders to
    detect drift — if the two ever diverged, the staleness report would lie."""
    meta, body = split_frontmatter(agent.agents_md.read_text())
    desc = meta.get("description") or agent_description(body)  # before inlining
    if inherited:
        parts = [body, "\n\n---\n\n# Inherited context (installed automatically)\n"]
        for pa in inherited:
            core = pa.path / "CORE.md"
            if core.exists():
                # curated, condensed essence — preferred over a full-file dump
                parts.append(f"\n{core.read_text().strip()}\n")
            else:
                _, pbody = split_frontmatter(pa.agents_md.read_text())
                parts.append(f"\n## Inherited from `{pa.name}` (full)\n\n{pbody}\n")
        body = "".join(parts)
    return meta, desc, body


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

    if tool.agents_dir is None:
        print(f"    note   → {tool.label} has nowhere to put an agent body. "
              f"Skills installed above.")
        return

    meta, desc, body = compose_agent(agent, inherited)

    final = resolve_name(tool.agents_dir, agent.name,
                         ".json" if tool.agent_style == "kiro_json" else ".md",
                         policy, interactive)
    if final is None:
        print("    · agent file skipped")
        return
    dest, contents = render_agent(tool, final, body, desc, installed_skill_names, meta)
    print(f"    agent  → {dest}")
    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(contents)

    # Tools with no named-agent concept only find the body through the roster,
    # so writing one without the other leaves a half-install. The suite path
    # passes roster=False and writes it once at the end instead.
    if roster and tool.agent_style == "roster_md":
        write_roster(tool, agents, [final], dry_run)


def short_description(agent: Agent) -> str:
    """One line for the roster: the curated frontmatter description up to its
    first sentence, or the body's opening sentence when there is no frontmatter."""
    meta, body = split_frontmatter(agent.agents_md.read_text())
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
    on_disk = {p.stem for p in tool.agents_dir.glob("*.md")} if tool.agents_dir.exists() else set()
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
        current = dest.read_text()
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
        dest.write_text(contents)


def install_suite(tool: Tool, policy: str, interactive: bool, dry_run: bool,
                  agents: dict, skills_by_name: dict):
    """Install the WHOLE catalog — every skill once, then every agent file with
    its inheritance inlined. This guarantees all cross-agent handoffs, shared
    skills, and orchestration references resolve, because everything is present."""
    print(f"\n  Installing the WHOLE SUITE ({len(agents)} agents, "
          f"{len(skills_by_name)} skills) → {tool.label}")

    print("  — skills (each installed once) —")
    for name in sorted(skills_by_name):
        install_skill(skills_by_name[name], tool, policy, interactive, dry_run)

    if tool.agents_dir is None:
        print(f"  — {tool.label} has no named-agent slot: skills above are the install. —")
        return

    print("  — agents (inheritance inlined; skills already installed above) —")
    for name in sorted(agents):
        install_agent(agents[name], tool, policy, interactive, dry_run,
                      agents, skills_by_name, with_deps=True, skip_skills=True,
                      roster=False)

    if tool.agent_style == "roster_md":
        print(f"  — roster ({tool.label} has no named-agent slot, so the bodies "
              f"above are indexed by hand) —")
        write_roster(tool, agents, sorted(agents), dry_run)


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


def interactive(agents, all_skills, skills_by_name, policy, dry_run, with_deps, project=None):
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
    if not tool.config_root.exists():
        ans = input(f"  {tool.label} doesn't look installed ({tool.config_root} "
                    f"missing). Install anyway? [y/N] ").strip().lower()
        if ans not in ("y", "yes"):
            return

    if mode == 0:
        install_suite(tool, policy, True, dry_run, agents, skills_by_name)
    elif mode == 1:
        names = sorted(agents)
        idx = choose("which agent", [f"{n}  ({len(agents[n].skills)} skills)" for n in names])
        if idx is None:
            return
        install_agent(agents[names[idx]], tool, policy, True, dry_run,
                      agents, skills_by_name, with_deps)
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


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def print_status(agents, skills_by_name, project=None):
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

        # --- skills: verbatim copies, so a byte comparison is exact ---
        present, foreign, stale = [], [], []
        if tool.skills_dir.exists():
            for d in sorted(p for p in tool.skills_dir.iterdir() if p.is_dir()):
                src = skills_by_name.get(d.name)
                if not src:
                    foreign.append(d.name)
                    continue
                present.append(d.name)
                a, b = src.path / "SKILL.md", d / "SKILL.md"
                if not b.exists() or a.read_text() != b.read_text():
                    stale.append(d.name)
        missing = sorted(set(skills_by_name) - set(present))
        print(f"    skills   {len(present)}/{len(skills_by_name)} from catalog"
              f"{f' · {len(stale)} stale' if stale else ''}"
              f"{f' · {len(missing)} missing' if missing else ''}"
              f"{f' · {len(foreign)} foreign (untouched)' if foreign else ''}")
        for label, items in (("stale", stale), ("missing", missing)):
            if items:
                print(f"      {label}: {', '.join(items[:8])}"
                      f"{f' +{len(items) - 8} more' if len(items) > 8 else ''}")

        # --- agents: rendered, so compare against a fresh render ---
        if tool.agents_dir is None:
            print("    agents   (this tool has no place for agent bodies)")
            continue
        suffix = ".json" if tool.agent_style == "kiro_json" else ".md"
        on_disk = ({p.stem for p in tool.agents_dir.glob(f"*{suffix}")}
                   if tool.agents_dir.exists() else set())
        a_present = sorted(on_disk & set(agents))
        a_foreign = sorted(on_disk - set(agents))
        a_missing = sorted(set(agents) - on_disk)
        a_stale = []
        for name in a_present:
            inherited, dep_skills = resolve_deps(agents[name], agents, skills_by_name)
            meta, desc, body = compose_agent(agents[name], inherited)
            dest, fresh = render_agent(tool, name, body, desc,
                                       sorted(s.name for s in dep_skills), meta)
            if not dest.exists() or dest.read_text() != fresh:
                a_stale.append(name)
        print(f"    agents   {len(a_present)}/{len(agents)} from catalog"
              f"{f' · {len(a_stale)} stale' if a_stale else ''}"
              f"{f' · {len(a_missing)} missing' if a_missing else ''}"
              f"{f' · {len(a_foreign)} foreign (untouched)' if a_foreign else ''}")
        for label, items in (("stale", a_stale), ("missing", a_missing)):
            if items:
                print(f"      {label}: {', '.join(items)}")

        if tool.agent_style == "roster_md":
            roster = tool.roster
            if not roster.exists():
                print("      roster: MISSING — the bodies above are unreachable "
                      "without it")
            else:
                rows = len(re.findall(r"^\| `[a-z-]+` \|", roster.read_text(), re.M))
                mark = "" if rows == len(a_present) else f" (≠ {len(a_present)} bodies)"
                print(f"      roster: {rows} rows in {roster.name}{mark}")

    scope = f" --project {project}" if project else ""
    print(f"\ncatalog: {len(agents)} agents, {len(skills_by_name)} skills — refresh with:"
          f"  ./install.py --all --tool <key>{scope} --on-conflict overwrite")


def print_list(agents, all_skills):
    print("\nAgents:")
    for n, a in sorted(agents.items()):
        print(f"  {n}  — {len(a.skills)} skills: {', '.join(s.name for s in a.skills)}")
    print(f"\nSkills: {len(all_skills)} total (address as agent:skill)")
    print("\nTools:")
    for t in TOOLS:
        mark = "available" if t.config_root.exists() else "not detected"
        agentcap = "agents+skills" if t.agents_dir else "skills only"
        print(f"  {t.key:9} {t.label:42} [{mark}, {agentcap}]")


def main():
    ap = argparse.ArgumentParser(description="Install catalog agents/skills into a tool's global config.")
    ap.add_argument("--catalog", type=Path, default=Path(__file__).resolve().parent,
                    help="catalog root (default: this script's directory)")
    ap.add_argument("--list", action="store_true", help="list agents, skills, tools and exit")
    ap.add_argument("--project", type=Path, nargs="?", const=Path("."), default=None,
                    metavar="PATH",
                    help="install into a project checkout (default: cwd) instead of "
                         "your home config, so the setup travels with the repo")
    ap.add_argument("--status", action="store_true",
                    help="show what is installed in each tool and whether it is current")
    ap.add_argument("--all", action="store_true", help="install the whole suite (all agents + skills)")
    ap.add_argument("--agent", action="append", default=[], help="agent name to install (repeatable)")
    ap.add_argument("--skill", action="append", default=[], help="skill as agent:skill or name (repeatable)")
    ap.add_argument("--tool", help="target tool key (claude, opencode, kiro, codex, shared)")
    ap.add_argument("--on-conflict", choices=["ask", "overwrite", "rename", "skip"], default="ask")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen, change nothing")
    ap.add_argument("--no-deps", action="store_true",
                    help="install only the agent's own skills; skip inherited/cross-agent deps")
    args = ap.parse_args()

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
        return project_tool(tool, project) if project else tool

    if args.list:
        print_list(agents, all_skills)
        return

    if args.status:
        print_status(agents, skills_by_name, project)
        return

    if args.dry_run:
        print("=== DRY RUN — no files will be written ===")

    # Non-interactive: whole suite
    if args.all:
        if not args.tool:
            sys.exit("--tool is required with --all")
        if args.tool not in TOOLS_BY_KEY:
            sys.exit(f"unknown tool '{args.tool}'. Known: {', '.join(TOOLS_BY_KEY)}")
        install_suite(target(TOOLS_BY_KEY[args.tool]), args.on_conflict, False, args.dry_run,
                      agents, skills_by_name)
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
        return

    # Interactive path
    interactive(agents, all_skills, skills_by_name, args.on_conflict,
                args.dry_run, with_deps=not args.no_deps, project=project)


if __name__ == "__main__":
    main()
