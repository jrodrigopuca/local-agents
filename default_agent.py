#!/usr/bin/env python3
"""default_agent.py — make a catalog agent the one a session starts with.

A session started without an agent loads none of the catalog: the host's own
default assistant answers, with the host's own instructions (ESTADO-DEL-ARTE
§3, "Qué dice cada host cuando no hay agente"). This sets the host's
default-agent setting to an installed catalog agent, so the CORE is there from
the first turn. Picking another agent when a session starts still works — that
is why this is the gentle way in, and why it is the only one automated here.

It is NOT part of install.py, on purpose: which agent a session starts with is
the user's preference, not the catalog's. Run it yourself, or don't.

    ./default_agent.py --status                    # what each host starts with now
    ./default_agent.py --set generalist            # every supported host that is installed
    ./default_agent.py --set generalist --tool claude,kiro
    ./default_agent.py --set generalist --dry-run  # show, change nothing
    ./default_agent.py --restore                   # put back what was there before

Supported: Claude Code (`agent` in settings.json), opencode (`default_agent` in
opencode.json; the agent must be a primary one) and Kiro CLI
(`chat.defaultAgent` in settings/cli.json). Codex and Antigravity have no such
setting (read 2026-11-15): there the only way is the global rules file, which
loads in every session and every agent, so it stays a manual, documented step.

The way back is recorded when the change is made: the value that was there
before goes to `.local-agents-default-agent.json` beside the setting. --restore
puts it back only if the setting is still the one this script wrote; a value
you changed afterwards is yours and is left alone.

Standard library only.
"""
import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Importing install.py must not leave a __pycache__ in the catalog: with no global git
# excludes (CI, a throwaway HOME) it would read as a dirty tree in every install stamp.
sys.dont_write_bytecode = True
from install import TOOLS_BY_KEY  # noqa: E402

STATE = ".local-agents-default-agent.json"
ABSENT = "absent"     # the setting did not exist; `None` would also be a legal JSON value


@dataclass(frozen=True)
class Host:
    key: str             # install.py's tool key
    settings: str        # the settings file, relative to the tool's config root
    setting: str         # the key inside it
    agent_file: str      # the installed agent, relative to the agents dir; {name} is replaced
    override: str        # how to start a session with another agent

    @property
    def tool(self):
        return TOOLS_BY_KEY[self.key]

    @property
    def path(self) -> Path:
        return self.tool.config_root / self.settings

    @property
    def state(self) -> Path:
        return self.path.parent / STATE


HOSTS = {
    "claude": Host("claude", "settings.json", "agent", "{name}.md", "claude --agent NAME"),
    "opencode": Host("opencode", "opencode.json", "default_agent", "{name}.md", "Tab, or `opencode --agent NAME`"),
    "kiro": Host("kiro", "settings/cli.json", "chat.defaultAgent", "{name}.json", "kiro-cli chat --agent NAME"),
}
UNSUPPORTED = {"codex": "Codex", "antigravity": "Antigravity CLI"}


class Refused(Exception):
    """A change this script will not make; the message says why and what to do."""


def read_json(path: Path) -> dict:
    """The settings as a dict; {} when the file does not exist. A file that is
    not plain JSON (comments, a trailing comma) is refused, never rewritten:
    writing it back would drop what the parser skipped."""
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as e:
        raise Refused(f"{path} is not plain JSON ({e}); add the setting by hand") from None
    if not isinstance(data, dict):
        raise Refused(f"{path} does not hold a JSON object; add the setting by hand")
    return data


def write_json(path: Path, data: dict, like: str = "") -> None:
    """Write through a temp file and a rename, keeping the file's own indent."""
    m = re.search(r"\n([ \t]+)\"", like)
    indent = m.group(1) if m else "  "
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def installed(host: Host, name: str) -> Optional[str]:
    """Why `name` cannot be this host's default, or None when it can."""
    agents = host.tool.agents_dir
    f = agents / host.agent_file.format(name=name)
    if not f.is_file():
        return f"`{name}` is not installed there ({f}); run ./install.py --agent {name} --tool {host.key}"
    if host.key == "opencode":
        # opencode falls back to `build` without a word when the agent is not a primary one
        head = f.read_text(encoding="utf-8", errors="replace").split("\n---", 1)[0]
        mode = re.search(r"(?m)^mode:\s*(\S+)", head)
        if mode and mode.group(1) not in ("primary", "all"):
            return f"`{name}` is a `{mode.group(1)}` agent in opencode; its default must be a primary one"
    return None


def current(host: Host):
    return read_json(host.path).get(host.setting, ABSENT)


def set_default(host: Host, name: str, dry_run: bool = False) -> str:
    if not host.tool.config_root.is_dir():
        return f"not installed ({host.tool.config_root}): skipped"
    why = installed(host, name)
    if why:
        raise Refused(why)
    data = read_json(host.path)
    before = data.get(host.setting, ABSENT)
    if before == name:
        return f"already `{name}`"
    state = read_json(host.state)
    # The way back is the value from before OUR first change: setting twice
    # must not record our own value as the one to restore.
    ours = state.get("set") is not None and before == state.get("set")
    record = {"setting": host.setting, "previous": state["previous"] if ours else before,
              "set": name, "created_file": state.get("created_file", False) if ours else not host.path.exists()}
    was = "nothing" if before == ABSENT else f"`{before}`"
    if dry_run:
        return f"would set `{host.setting}` to `{name}` in {host.path} (was {was})"
    like = host.path.read_text(encoding="utf-8") if host.path.exists() else ""
    write_json(host.state, record)
    data[host.setting] = name
    write_json(host.path, data, like)
    return f"`{host.setting}` = `{name}` in {host.path} (was {was}); another agent for one session: {host.override}"


def restore(host: Host, dry_run: bool = False) -> str:
    if not host.state.exists():
        return "nothing recorded: this script did not change it"
    state = read_json(host.state)
    data = read_json(host.path)
    now = data.get(host.setting, ABSENT)
    if now != state.get("set"):
        # Changed since: it is the user's now. Forget our record, touch nothing.
        if not dry_run:
            host.state.unlink()
        return (f"left alone: `{host.setting}` is {'unset' if now == ABSENT else f'`{now}`'}, "
                f"not the `{state.get('set')}` this script wrote")
    previous = state.get("previous", ABSENT)
    back = "unset" if previous == ABSENT else f"`{previous}`"
    if dry_run:
        return f"would put `{host.setting}` back to {back} in {host.path}"
    like = host.path.read_text(encoding="utf-8")
    if previous == ABSENT:
        data.pop(host.setting, None)
    else:
        data[host.setting] = previous
    if not data and state.get("created_file"):
        host.path.unlink()          # the file existed only for this setting
    else:
        write_json(host.path, data, like)
    host.state.unlink()
    return f"`{host.setting}` back to {back} in {host.path}"


def status(host: Host) -> str:
    if not host.tool.config_root.is_dir():
        return "not installed"
    try:
        now = current(host)
    except Refused as e:
        return str(e)
    ours = host.state.exists() and read_json(host.state).get("set") == now
    shown = "the host's own default assistant" if now == ABSENT else f"`{now}`"
    return f"starts with {shown}" + (" (set by this script)" if ours else "")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    what = ap.add_mutually_exclusive_group(required=True)
    what.add_argument("--status", action="store_true", help="show what each host starts with")
    what.add_argument("--set", metavar="AGENT", help="make this installed agent the default")
    what.add_argument("--restore", action="store_true", help="put back what was there before --set")
    ap.add_argument("--tool", default="", help=f"comma-separated subset of: {', '.join(HOSTS)} (default: all)")
    ap.add_argument("--dry-run", action="store_true", help="show what would happen, change nothing")
    args = ap.parse_args(argv)
    keys = [k.strip() for k in args.tool.split(",") if k.strip()] or list(HOSTS)
    for k in keys:
        if k in UNSUPPORTED:
            ap.error(f"{UNSUPPORTED[k]} has no default-agent setting; see INSTALL.md, \"Starting every session with an agent\"")
        if k not in HOSTS:
            ap.error(f"unknown tool `{k}`; choose from: {', '.join(HOSTS)}")
    failed = False
    for k in keys:
        host = HOSTS[k]
        try:
            line = (status(host) if args.status else
                    set_default(host, args.set, args.dry_run) if args.set else restore(host, args.dry_run))
        except Refused as e:
            line, failed = f"REFUSED — {e}", True
        print(f"{host.tool.label:12} {line}")
    if args.status:
        for label in UNSUPPORTED.values():
            print(f"{label:12} no default-agent setting: a session without an agent uses the host's own assistant")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
