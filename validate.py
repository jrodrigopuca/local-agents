#!/usr/bin/env python3
"""validate.py — check catalog invariants and regenerate derived blocks.

Nine checks over the catalog, plus generation of the data-only blocks in
GRAPH.md (mermaid graphs and reference tables). Prose is never touched: the
generator only rewrites what sits between `<!-- BEGIN:x -->` / `<!-- END:x -->`.

Usage:
  ./validate.py                 # run every check, exit 1 on any failure
  ./validate.py --write         # regenerate derived blocks in place
  ./validate.py --list-checks   # show what runs

CI runs `--write` then `git diff --exit-code`, so a stale graph fails the build.

Requires PyYAML (`pip install pyyaml`). install.py stays dependency-free on
purpose — it runs on users' machines; this one runs on contributors' and in CI.
"""
from __future__ import annotations

import argparse
import glob
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("validate.py needs PyYAML — run: pip install pyyaml")

ROOT = Path(__file__).resolve().parent

# Mirrors install.py's INHERIT_SOURCES: a `../X/AGENTS.md` link counts as
# inheritance only when X is a known source AND its trigger phrase sits within
# 140 chars, so a handoff mention is never mistaken for inheritance.
INHERIT_SOURCES = {"generalist": "reasoning model", "senior-dev": "peer contract"}
PROXIMITY = 140

# Root AGENTS.md rule 6. Character-archetype agents speak Neutral Spanish;
# real-teammate agents speak Rioplatense; the generalist base stays neutral.
CHARACTER_AGENTS = {"visionary", "stark", "security"}
REGISTER_EXEMPT = {"generalist"}

# Paths that would be a lie in four of the five install targets.
HARNESS_PATTERNS = [
    (r"~/\.claude", "Claude Code config path"),
    (r"~/\.config/opencode", "opencode config path"),
    (r"~/\.kiro", "Kiro config path"),
    (r"~/\.codex", "Codex config path"),
    (r"`/[a-z][a-z-]*`", "harness slash command"),
]


# --------------------------------------------------------------------------- #
# Catalog model
# --------------------------------------------------------------------------- #
def _window(text: str, m) -> str:
    """Whitespace-normalised context around a link, for trigger matching.

    The trigger phrases are prose ("reasoning model"), and prose wraps: matching
    the raw text made inheritance detection depend on where a line happened to
    break. This mirrors install.py's scan_refs — they must agree, or the graph
    and the installer disagree about what an agent inherits."""
    lo, hi = max(0, m.start() - PROXIMITY), m.end() + PROXIMITY
    return " ".join(text[lo:hi].lower().split())


class Catalog:
    def __init__(self, root: Path):
        self.root = root
        self.agents = {}   # name -> text of AGENTS.md
        self.skills = {}   # skill-name -> (agent, path, text)
        for p in sorted(root.glob("*/AGENTS.md")):
            self.agents[p.parent.name] = p.read_text()
        for p in sorted(root.glob("*/skills/*/SKILL.md")):
            self.skills[p.parent.name] = (p.parent.parent.parent.name, p, p.read_text())

    def owner(self, skill: str):
        return self.skills[skill][0] if skill in self.skills else None

    def inheritance(self):
        """{child: {parents}} — the structural edges install.py inlines."""
        out = {}
        for name, text in self.agents.items():
            for m in re.finditer(r"(?:\.\./)+([a-z][a-z-]*)/AGENTS\.md", text):
                tgt = m.group(1)
                trig = INHERIT_SOURCES.get(tgt)
                if trig and trig in _window(text, m):
                    out.setdefault(name, set()).add(tgt)
        return out

    def handoffs(self):
        """{source: {targets}} — agent-level links that are NOT inheritance."""
        out = {}
        for name, text in self.agents.items():
            for m in re.finditer(r"(?:\.\./)+([a-z][a-z-]*)/AGENTS\.md", text):
                tgt = m.group(1)
                trig = INHERIT_SOURCES.get(tgt)
                if trig and trig in _window(text, m):
                    continue
                out.setdefault(name, set()).add(tgt)
        return out

    def skill_refs(self):
        """{(agent, skill) -> {(agent, skill)}} for CROSS-agent references."""
        out = {}
        for skill, (agent, _p, text) in self.skills.items():
            for m in re.finditer(r"\]\(((?:\.\./)+[^)]*?)([a-z][a-z-]*)/SKILL\.md\)", text):
                tgt = m.group(2)
                if tgt == skill or tgt not in self.skills:
                    continue
                towner = self.owner(tgt)
                if towner != agent:
                    out.setdefault((agent, skill), set()).add((towner, tgt))
        return out


def frontmatter(text: str):
    m = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return None, "no frontmatter block"
    try:
        data = yaml.safe_load(m.group(1))
    except Exception as exc:
        return None, f"invalid YAML: {exc}"
    if not isinstance(data, dict):
        return None, "frontmatter is not a mapping"
    return data, None


# --------------------------------------------------------------------------- #
# Checks — each returns a list of human-readable failures
# --------------------------------------------------------------------------- #
def check_links(cat: Catalog):
    errs = []
    files = ["AGENTS.md", "README.md", "GRAPH.md", "INSTALL.md", "USAGE.md",
             "INTEGRATION.md", "REFERENCE_.md"]
    files += [f"{a}/AGENTS.md" for a in cat.agents]
    files += [str(p.relative_to(cat.root)) for _a, p, _t in cat.skills.values()]
    for rel in files:
        src = cat.root / rel
        if not src.exists():
            continue
        for m in re.finditer(r"\]\(([^)\s]+?\.md)(?:#[^)]*)?\)", src.read_text()):
            link = m.group(1)
            if link.startswith(("http://", "https://", "/")) or link.startswith("~"):
                continue
            if not (src.parent / link).exists():
                errs.append(f"{rel}: broken link -> {link}")
    return errs


def check_frontmatter(cat: Catalog):
    errs = []
    for skill, (agent, path, text) in cat.skills.items():
        rel = path.relative_to(cat.root)
        data, err = frontmatter(text)
        if err:
            errs.append(f"{rel}: {err}")
            continue
        for key in ("name", "description", "license", "metadata"):
            if key not in data:
                errs.append(f"{rel}: missing `{key}` in frontmatter")
        if not str(data.get("description", "")).strip():
            errs.append(f"{rel}: empty description")
        # The Agent Skills spec puts author/version inside `metadata` in its
        # canonical example. Presence is checked, never the value: bumping is
        # nobody's chore here — provenance comes from the catalog's git history
        # (see install.py), and this only keeps new skills spec-shaped.
        meta = data.get("metadata") or {}
        for key in ("author", "version"):
            if not isinstance(meta, dict) or key not in meta:
                errs.append(f"{rel}: `metadata.{key}` missing — keep the spec's "
                            f"canonical metadata shape")
    for agent, text in cat.agents.items():
        data, err = frontmatter(text)
        if err:
            errs.append(f"{agent}/AGENTS.md: {err}")
        elif not str(data.get("description", "")).strip():
            errs.append(f"{agent}/AGENTS.md: empty or missing description")
    return errs


def check_skill_names(cat: Catalog):
    """install.py keys on both the folder and the frontmatter name."""
    errs = []
    for skill, (agent, path, text) in cat.skills.items():
        data, err = frontmatter(text)
        if err:
            continue
        if data.get("name") != skill:
            errs.append(f"{path.relative_to(cat.root)}: name `{data.get('name')}` "
                        f"!= folder `{skill}`")
    return errs


def check_harness_paths(cat: Catalog):
    """The catalog installs into five tools with five layouts — a hardcoded
    path to one of them is wrong in the other four."""
    errs = []
    targets = [(f"{a}/AGENTS.md", t) for a, t in cat.agents.items()]
    targets += [(str(p.relative_to(cat.root)), t) for _a, p, t in cat.skills.values()]
    for rel, text in targets:
        for pattern, label in HARNESS_PATTERNS:
            for m in re.finditer(pattern, text):
                line = text[:m.start()].count("\n") + 1
                errs.append(f"{rel}:{line}: {label} `{m.group(0)}` — "
                            f"reference skills by name, not by path")
    return errs


def check_language_register(cat: Catalog):
    """Root AGENTS.md rule 6."""
    errs = []
    for agent, text in cat.agents.items():
        if agent in REGISTER_EXEMPT:
            if not re.search(r"user's language", text, re.I):
                errs.append(f"{agent}/AGENTS.md: base agent should stay "
                            f"register-neutral (respond in the user's language)")
            continue
        want = "neutral spanish" if agent in CHARACTER_AGENTS else "rioplatense"
        if not re.search(re.escape(want), text, re.I):
            kind = "character archetype" if agent in CHARACTER_AGENTS else "real teammate"
            errs.append(f"{agent}/AGENTS.md: {kind} must declare "
                        f"'{want.title()}' (rule 6)")
    return errs


def check_agent_rows(cat: Catalog):
    """Root AGENTS.md rule 4: every agent gets a row in the index table."""
    rows = set(re.findall(r"^\| `([a-z-]+)`", (cat.root / "AGENTS.md").read_text(), re.M))
    errs = [f"AGENTS.md: no index row for agent `{a}`" for a in sorted(set(cat.agents) - rows)]
    errs += [f"AGENTS.md: index row `{r}` has no agent directory"
             for r in sorted(rows - set(cat.agents))]
    return errs


def check_section_scope(cat: Catalog):
    """Root AGENTS.md rule 11. `## External skills` is about skills that ship
    outside the catalog; routing between agents belongs in `## Handoffs`. The
    two drifted together once already."""
    errs = []
    for agent, text in cat.agents.items():
        m = re.search(r"^## External skills.*$", text, re.M)
        if not m:
            continue
        nxt = re.search(r"^## ", text[m.end():], re.M)
        body = text[m.end():m.end() + nxt.start()] if nxt else text[m.end():]
        for link in re.finditer(r"(?:\.\./)+([a-z][a-z-]*)/AGENTS\.md", body):
            line = text[:m.end() + link.start()].count("\n") + 1
            errs.append(f"{agent}/AGENTS.md:{line}: `## External skills` links to "
                        f"agent `{link.group(1)}` — agent routing belongs in "
                        f"`## Handoffs` (rule 11)")
    return errs


def check_link_identity(cat: Catalog):
    """Every internal link must name its target somewhere a reader can recover.

    Relative paths do not survive installation: the catalog is a tree, an
    installed copy is flat, so `../qa/AGENTS.md` resolves to nothing once
    copied. The link TEXT is what carries the meaning across, so it has to
    identify the target — by name, or by a phrase the target's own description
    contains (which is how a host's skill discovery finds it)."""
    errs = []
    descriptions = {}
    for skill, (_a, _p, text) in cat.skills.items():
        data, _err = frontmatter(text)
        descriptions[skill] = str((data or {}).get("description", "")).lower()

    targets = [(f"{a}/AGENTS.md", t) for a, t in cat.agents.items()]
    targets += [(str(p.relative_to(cat.root)), t) for _a, p, t in cat.skills.values()]
    for rel, body in targets:
        for m in re.finditer(r"\[([^\]]+)\]\(((?:\.\./)+[^)]+?)\)", body):
            text, path = m.group(1), m.group(2)
            agent = re.search(r"\.\./([a-z][a-z-]*)/AGENTS\.md$", path)
            skill = re.search(r"([a-z][a-z-]*)/SKILL\.md$", path)
            target = agent.group(1) if agent else (skill.group(1) if skill else None)
            if not target:
                continue
            # Sibling skill links keep working: installed skills are siblings too.
            if rel.endswith("SKILL.md") and re.fullmatch(r"\.\./[a-z][a-z-]*/SKILL\.md", path):
                continue
            low = text.lower()
            if target in low or target.replace("-", " ") in low:
                continue
            if skill and low in descriptions.get(target, ""):
                continue
            line = body[:m.start()].count("\n") + 1
            errs.append(f"{rel}:{line}: link text \"{text}\" does not name its target "
                        f"`{target}` — the path dies on install, so add the name "
                        f"(e.g. \"{text} (`{target}`)\")")
    return errs


def check_kiro_contract(cat: Catalog):
    """The Kiro agent JSON the installer emits must match the recipe in USAGE.md.

    These drifted once: USAGE.md documented `["read","write","shell"]` while the
    installer emitted an `edit` tag that does not exist in Kiro, and nothing
    compared them. Kiro's tool tags are a closed set — an unknown one is a config
    error, not a no-op — so doc and code have to agree."""
    errs = []
    usage = (cat.root / "USAGE.md").read_text()
    install = (cat.root / "install.py").read_text()

    def tools_of(text, label):
        m = re.search(r'"tools":\s*(\[[^\]]*\])', text)
        if not m:
            errs.append(f"{label}: no `tools` array found for the Kiro agent config")
            return None
        return [t.strip().strip('"') for t in m.group(1).strip("[]").split(",") if t.strip()]

    documented = tools_of(usage, "USAGE.md")
    emitted = tools_of(install, "install.py")
    if documented and emitted and documented != emitted:
        errs.append(f"install.py emits Kiro tools {emitted} but USAGE.md documents "
                    f"{documented} — they must agree; an unknown tag is a Kiro config error")
    return errs


def check_inheritance(cat: Catalog):
    """Every agent but `generalist` must declare that it inherits the reasoning
    model, and detection must actually see it.

    This exists because the failure is silent: the trigger phrase is prose, and
    when a line wrapped mid-phrase the link stopped counting as inheritance.
    Nothing broke loudly — `install.py` just produced an agent without its
    parent's CORE inlined. A missing base loop is not something to discover in
    conversation with a lobotomised agent."""
    errs = []
    inh = cat.inheritance()
    for name in sorted(cat.agents):
        if name == "generalist":
            continue
        if "generalist" not in inh.get(name, set()):
            errs.append(f"{name}/AGENTS.md: does not declare inheritance from "
                        f"`generalist` — link ../generalist/AGENTS.md with the "
                        f"phrase \"reasoning model\" beside it")
    return errs


def check_orchestration_roster(cat: Catalog):
    """`eng-manager`'s orchestration skill routes to every agent.

    It is the only place that knows the whole roster, so an agent missing from
    its table is unreachable by the one component whose job is routing —
    including agents nothing else hands off to."""
    text = cat.skills["orchestration"][2] if "orchestration" in cat.skills else ""
    rows = set(re.findall(r"^\|[^|]+\|\s*`([a-z-]+)`", text, re.M))
    missing = sorted(set(cat.agents) - rows)
    return [f"eng-manager/skills/orchestration/SKILL.md: no routing row for "
            f"`{a}` — the orchestrator must know every agent" for a in missing]


# Prose that assumes the host can *invoke* another agent. Handoffs are written
# as ownership ("belongs to X", "goes to X") because that reads correctly
# everywhere: Claude Code and Kiro have named agents, Codex has none and reaches
# identities through a roster file. "Delegate to the X agent" describes a button
# that does not exist in every target.
INVOCATION_PATTERNS = [
    r"\buse the [a-z-]+ agent\b",
    r"\bdelegate to\b",
    r"\b(invoke|spawn|launch) (the )?[a-z-]+ agent\b",
    r"\bswitch to the [a-z-]+ agent\b",
    r"\bcall the [a-z-]+ agent\b",
]


def check_agent_invocation(cat: Catalog):
    """No BODY may assume a mechanism for running another agent.

    Frontmatter `<example>` blocks are exempt on purpose: there, "I'll use the
    qa agent" is the delegation signal the description exists to teach, and
    install.py strips those examples for hosts that have no named agents."""
    errs = []
    targets = [(f"{a}/AGENTS.md", t) for a, t in cat.agents.items()]
    targets += [(str(p.relative_to(cat.root)), t) for _a, p, t in cat.skills.values()]
    for rel, text in targets:
        body = re.sub(r"^---\n.*?\n---\n", "", text, flags=re.DOTALL)
        for pattern in INVOCATION_PATTERNS:
            for m in re.finditer(pattern, body, re.I):
                line = body[:m.start()].count("\n") + 1
                errs.append(f"{rel}:~{line}: \"{m.group(0)}\" assumes the host can "
                            f"invoke an agent — say where work BELONGS instead "
                            f"(\"belongs to X\", \"goes to X\")")
    return errs


# Vendor technology names. Not exhaustive and doesn't need to be — it exists to
# catch an agent scoping ITSELF to a stack, which is a small, deliberate act.
VENDOR_TECH = (r"\b(TypeScript|JavaScript|React|Next\.?js|Vue|Angular|Svelte|"
               r"Python|Django|Flask|Rails|Golang|Rust|Kotlin|Swift|SwiftUI|"
               r"UIKit|Objective-C|Xcode|iOS|macOS|Android|Flutter|Docker|"
               r"Kubernetes|Terraform|AWS|GCP|Azure|Postgres|MySQL|MongoDB|"
               r"Redis|Figma|Sketch|Tailwind|Zod|Playwright|Pytest|Jest)\b")

# Agents whose whole reason to exist IS a platform. The distinction that matters
# is name-vs-scope: `senior-dev` was a generic name hiding a JS-only agent, which
# is the failure. `apple-dev` says what it is, so its description should name the
# platform — that is the routing signal working, not a leak.
PLATFORM_AGENTS = {"apple-dev"}


def check_identity_neutrality(cat: Catalog):
    """An agent's routing description must not scope it to a technology.

    Judged on the description with `<example>` blocks stripped: inside an
    example, naming a stack is how the delegation signal is taught ("I started
    JavaScript yesterday..."), and in the body a concrete illustration beats an
    abstract one. What must stay clean is the sentence that says what the agent
    IS — the stack belongs in its skills, which can be swapped per project."""
    errs = []
    for name in sorted(cat.agents):
        if name in PLATFORM_AGENTS:
            continue
        data, err = frontmatter(cat.agents[name])
        if err:
            continue
        desc = re.sub(r"<example>.*?</example>", "",
                      str(data.get("description", "")), flags=re.DOTALL)
        for hit in sorted({m.group(0) for m in re.finditer(VENDOR_TECH, desc, re.I)}):
            errs.append(f"{name}/AGENTS.md: description scopes the agent to "
                        f"`{hit}` — identity is stack-agnostic, the stack comes "
                        f"from skills (add to PLATFORM_AGENTS if that is wrong)")
    return errs


def check_reference_roster(cat: Catalog):
    """The Spanish quick guide lists every agent, with the right skill count.

    Its previous incarnation summarised every agent and skill in prose — 729
    lines duplicating the catalog — and nothing tied it to reality, so it drifted
    into describing agents that no longer existed. The rewrite keeps only what
    can't be derived (the criollo one-liner) and this check keeps the roster
    honest: the deep content lives in the agent files, where it maintains
    itself."""
    text = (cat.root / "REFERENCE_.md").read_text()
    rows = {m[0]: int(m[1]) for m in
            re.findall(r"\[`([a-z-]+)`\]\([a-z-]+/AGENTS\.md\).*?\|\s*(\d+)\s*\|", text)}
    errs = []
    for name in sorted(cat.agents):
        real = sum(1 for a, _p, _t in cat.skills.values() if a == name)
        if name not in rows:
            errs.append(f"REFERENCE_.md: agent `{name}` missing from the roster table")
        elif rows[name] != real:
            errs.append(f"REFERENCE_.md: `{name}` claims {rows[name]} skills, has {real}")
    for extra in sorted(set(rows) - set(cat.agents)):
        errs.append(f"REFERENCE_.md: roster lists `{extra}`, which is not an agent")
    return errs


def check_readme_counts(cat: Catalog):
    """The README roster mixes curated prose with counts, so it is validated
    rather than generated — generation would overwrite the prose."""
    text = (cat.root / "README.md").read_text()
    claimed = {m[0]: int(m[1]) for m in
               re.findall(r"\[`([a-z-]+)`\]\([a-z-]+/AGENTS\.md\).*?\|\s*(\d+)\s*\|", text)}
    errs = []
    for agent in sorted(cat.agents):
        real = sum(1 for a, _p, _t in cat.skills.values() if a == agent)
        if agent not in claimed:
            errs.append(f"README.md: agent `{agent}` missing from the roster table")
        elif claimed[agent] != real:
            errs.append(f"README.md: `{agent}` claims {claimed[agent]} skills, has {real}")
    return errs


def check_installer(cat: Catalog):
    """Smoke test: the installer must still discover and render everything."""
    errs = []
    runs = [["--list"]] + [["--all", "--tool", t, "--dry-run"]
                           for t in ("claude", "opencode", "kiro", "codex", "shared")]
    for args in runs:
        proc = subprocess.run([sys.executable, str(cat.root / "install.py"), *args],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            errs.append(f"install.py {' '.join(args)} exited {proc.returncode}: "
                        f"{proc.stderr.strip()[:200]}")
    return errs


# --------------------------------------------------------------------------- #
# Derived blocks — pure data, safe to generate
# --------------------------------------------------------------------------- #
LAYER_BLURBS = {
    "Inheritance": ("#1-inheritance",
                    "Structural. `install.py` inlines the parent's `CORE.md` into the child."),
    "Agent handoffs": ("#2-agent-handoffs",
                       "Editorial. An agent names who takes over when a problem "
                       "stops being its own."),
    "Skill references": ("#3-skill-references",
                         "Compositional. A skill points at another skill instead "
                         "of duplicating it."),
}


def gen_summary(cat: Catalog) -> str:
    """The counts in the opening table drift the moment an edge is added — the
    generated graphs stay right but the prose around them silently lies."""
    counts = {
        "Inheritance": sum(len(v) for v in cat.inheritance().values()),
        "Agent handoffs": sum(len(v) for v in cat.handoffs().values()),
        "Skill references": sum(len(v) for v in cat.skill_refs().values()),
    }
    out = ["| Layer | Edges | What it means |", "|-------|------:|---------------|"]
    for layer, (anchor, blurb) in LAYER_BLURBS.items():
        out.append(f"| [{layer}]({anchor}) | {counts[layer]} | {blurb} |")
    return "\n".join(out)


def gen_isolated(cat: Catalog) -> str:
    """Who nothing points at. Measured on BOTH levels on purpose: an agent with
    no inbound handoff can still be well connected through its skills, and
    reporting only one level makes a healthy agent look orphaned."""
    inbound_h = {t for v in cat.handoffs().values() for t in v}
    inbound_s = {ta for tgts in cat.skill_refs().values() for ta, _t in tgts}
    orphans = sorted(set(cat.agents) - inbound_h - inbound_s)
    handoff_only = sorted(set(cat.agents) - inbound_h - set(orphans))

    def names(xs):
        marked = [f"`{x}`" for x in xs]
        return marked[0] if len(marked) == 1 else \
            " and ".join([", ".join(marked[:-1]), marked[-1]])

    if orphans:
        one = len(orphans) == 1
        lead = (f"{names(orphans)} {'is' if one else 'are'} unreachable: nothing "
                f"hands off to {'it' if one else 'them'} and no skill cites "
                f"{'its' if one else 'their'} work. `eng-manager`'s "
                f"[`orchestration`](eng-manager/skills/orchestration/SKILL.md) skill "
                f"still routes to {'it' if one else 'them'}, so the suite works — "
                f"but peer-to-peer, {'it is' if one else 'they are'} a leaf.")
    else:
        lead = ("Every agent is reachable: each one is either handed work by "
                "another or has its skills cited by another.")

    if handoff_only:
        one = len(handoff_only) == 1
        lead += (f" {names(handoff_only)} {'receives' if one else 'receive'} no "
                 f"peer-to-peer handoff but {'is' if one else 'are'} cited heavily "
                 f"at the skill level — reached through what "
                 f"{'it teaches' if one else 'they teach'}, not through routing.")
    return lead


def gen_inheritance(cat: Catalog) -> str:
    inh = cat.inheritance()
    peers = sorted(a for a, p in inh.items() if "senior-dev" in p)
    plain = sorted(a for a, p in inh.items()
                   if "senior-dev" not in p and a != "senior-dev")
    out = ["```mermaid", "flowchart TD",
           '    G["generalist — reasoning loop"]',
           '    SD["senior-dev — + peer contract"]', "",
           "    G --> SD"]
    out += [f"    G --> {a}" for a in plain]
    out.append("")
    out += [f"    SD --> {a}" for a in peers]
    out.append("```")
    return "\n".join(out)


def gen_handoffs(cat: Catalog) -> str:
    hand = cat.handoffs()
    out = ["```mermaid", "flowchart LR"]
    for src in sorted(hand):
        for tgt in sorted(hand[src]):
            out.append(f"    {src} --> {tgt}")
        out.append("")
    while out and out[-1] == "":
        out.pop()
    out.append("```")
    return "\n".join(out)


def _ref_counts(cat: Catalog):
    refs = cat.skill_refs()
    inb, outb = {}, {}
    for (sa, _s), tgts in refs.items():
        outb[sa] = outb.get(sa, 0) + len(tgts)
        for ta, _t in tgts:
            inb[ta] = inb.get(ta, 0) + 1
    return inb, outb


def gen_refcounts(cat: Catalog) -> str:
    inb, outb = _ref_counts(cat)
    rows = sorted(cat.agents, key=lambda a: (-inb.get(a, 0), outb.get(a, 0), a))
    out = ["| Agent | Referenced by others | References others |",
           "|-------|---------------------:|------------------:|"]
    for a in rows:
        i = inb.get(a, 0)
        cell = f"**{i}**" if i and i == max(inb.values()) else str(i)
        out.append(f"| `{a}` | {cell} | {outb.get(a, 0)} |")
    return "\n".join(out)


def gen_hubs(cat: Catalog) -> str:
    refs = cat.skill_refs()
    consumers = {}
    for (sa, _s), tgts in refs.items():
        for ta, t in tgts:
            consumers.setdefault((ta, t), set()).add(sa)
    top = sorted(consumers.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:6]
    out = ["| Skill | Consumed by | Consumers |",
           "|-------|------------:|-----------|"]
    for (ta, t), cons in top:
        link = f"[`{ta}/{t}`]({ta}/skills/{t}/SKILL.md)"
        out.append(f"| {link} | {len(cons)} agents | {', '.join(sorted(cons))} |")
    return "\n".join(out)


def gen_orphan_skills(cat: Catalog) -> str:
    refs = cat.skill_refs()
    consumed = {f"{ta}/{t}" for tgts in refs.values() for ta, t in tgts}
    orphans = sorted(f"{a}/{s}" for s, (a, _p, _t) in cat.skills.items()
                     if f"{a}/{s}" not in consumed)
    by_agent = {}
    for o in orphans:
        a, s = o.split("/")
        by_agent.setdefault(a, []).append(s)
    width = max(len(a) for a in by_agent) + 1
    lines = [f"{(a + '/').ljust(width)} {' · '.join(sorted(s))}"
             for a, s in sorted(by_agent.items())]
    return "```\n" + "\n".join(lines) + "\n```"


GENERATORS = {
    "summary": gen_summary,
    "isolated": gen_isolated,
    "inheritance": gen_inheritance,
    "handoffs": gen_handoffs,
    "refcounts": gen_refcounts,
    "hubs": gen_hubs,
    "orphan-skills": gen_orphan_skills,
}


def apply_blocks(cat: Catalog, write: bool):
    """Replace every marked block in GRAPH.md. Returns list of stale block names."""
    path = cat.root / "GRAPH.md"
    if not path.exists():
        return ["GRAPH.md: file missing"]
    text = original = path.read_text()
    stale = []
    for name, fn in GENERATORS.items():
        pattern = re.compile(
            rf"(<!-- BEGIN:{re.escape(name)} -->\n)(.*?)(\n<!-- END:{re.escape(name)} -->)",
            re.DOTALL)
        m = pattern.search(text)
        if not m:
            stale.append(f"GRAPH.md: missing markers for block `{name}`")
            continue
        fresh = fn(cat)
        if m.group(2).strip() != fresh.strip():
            stale.append(f"GRAPH.md: block `{name}` is stale — run ./validate.py --write")
        text = text[:m.start()] + m.group(1) + fresh + m.group(3) + text[m.end():]
    if write and text != original:
        path.write_text(text)
        return []
    return [] if write else stale


def check_installed_skills(cat: Catalog):
    """Every link inside an INSTALLED skill must resolve or name its target.

    Skills are copied through install.py's `render_skill`, which turns
    cross-agent skill paths into sibling paths (installed skills are flat) and
    agent links into names. This renders every skill the way the installer
    would and checks the result: no path climbs out of the skills directory,
    no `AGENTS.md` link survives, and every sibling link points at a skill that
    exists. Guards the installer as much as the catalog — a new link shape
    that `render_skill` doesn't know would surface here, not in a user's trace."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("local_agents_install", cat.root / "install.py")
    installer = importlib.util.module_from_spec(spec)
    # Python 3.9 dataclasses resolve `from __future__ import annotations` types
    # through sys.modules[cls.__module__]; register before executing or 3.9 —
    # the floor install.py promises — fails with AttributeError on NoneType.
    sys.modules[spec.name] = installer
    spec.loader.exec_module(installer)

    errs = []
    for skill, (agent, path, text) in cat.skills.items():
        rendered = installer.render_skill(text, agent, skill)
        rel = str(path.relative_to(cat.root))
        for m in re.finditer(r"\]\(([^)]+)\)", rendered):
            target = m.group(1)
            if target.startswith(("http://", "https://", "#")):
                continue
            line = rendered[:m.start()].count("\n") + 1
            sib = re.fullmatch(r"\.\./([a-z][a-z-]*)/SKILL\.md", target)
            if sib and sib.group(1) in cat.skills:
                continue
            if sib:
                errs.append(f"{rel}:{line}: installed link `{target}` names a skill "
                            f"that is not in the catalog")
            elif target.endswith("AGENTS.md") or target.startswith("../"):
                errs.append(f"{rel}:{line}: link `{target}` is dead once installed — "
                            f"install.py's render_skill does not know this shape")
    return errs


CHECKS = [
    ("links", "relative markdown links resolve", check_links),
    ("installed-skills", "skills carry no dead links once installed", check_installed_skills),
    ("frontmatter", "YAML parses and required keys present", check_frontmatter),
    ("skill-names", "frontmatter `name` matches folder", check_skill_names),
    ("harness-paths", "no tool-specific paths in agent/skill bodies", check_harness_paths),
    ("language-register", "rule 6 — neutral vs Rioplatense", check_language_register),
    ("agent-rows", "rule 4 — every agent indexed in AGENTS.md", check_agent_rows),
    ("inheritance", "every agent declares the generalist reasoning model", check_inheritance),
    ("orchestration-roster", "the orchestrator routes to every agent", check_orchestration_roster),
    ("agent-invocation", "no body assumes a way to invoke another agent", check_agent_invocation),
    ("identity-neutrality", "agent identity is stack-agnostic (skills carry the stack)", check_identity_neutrality),
    ("section-scope", "rule 11 — External skills holds no agent routing", check_section_scope),
    ("link-identity", "link text names its target (paths die on install)", check_link_identity),
    ("kiro-contract", "Kiro agent JSON matches the recipe in USAGE.md", check_kiro_contract),
    ("readme-counts", "README roster matches reality", check_readme_counts),
    ("reference-roster", "REFERENCE_.md lists every agent (Spanish guide)", check_reference_roster),
    ("installer", "install.py --list and --dry-run succeed", check_installer),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true",
                    help="regenerate derived blocks in GRAPH.md instead of checking them")
    ap.add_argument("--list-checks", action="store_true", help="list checks and exit")
    args = ap.parse_args()

    if args.list_checks:
        for name, desc, _ in CHECKS:
            print(f"  {name:19} {desc}")
        print(f"  {'derived-blocks':19} GRAPH.md generated blocks are current "
              f"({', '.join(GENERATORS)})")
        return 0

    cat = Catalog(ROOT)
    print(f"catalog: {len(cat.agents)} agents, {len(cat.skills)} skills\n")

    failed = 0
    for name, desc, fn in CHECKS:
        errs = fn(cat)
        print(f"{'FAIL' if errs else ' ok '}  {name:19} {desc}")
        for e in errs:
            print(f"        {e}")
        failed += bool(errs)

    errs = apply_blocks(cat, args.write)
    label = "regenerated" if args.write else "derived-blocks"
    print(f"{'FAIL' if errs else ' ok '}  {label:19} GRAPH.md data blocks")
    for e in errs:
        print(f"        {e}")
    failed += bool(errs)

    print()
    if failed:
        print(f"{failed} check(s) failed")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
