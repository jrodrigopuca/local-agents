#!/usr/bin/env python3
"""Bring the local-agents catalog, and every install made from it, up to date.

    ./update.py check                  # what is new upstream since you installed; writes nothing
    ./update.py update                 # bring the catalog, then refresh every install
    ./update.py install [ARGS...]      # install: clone the catalog the first time, then install.py ARGS
    ./update.py status [--verbose]     # what is installed on this machine, and whether it is current
    ./update.py list                   # what the catalog holds, and which tools were found
    ./update.py uninstall [ARGS...]    # remove what was installed, and only that
    ./update.py default [ARGS...]      # the agent a session starts with (default_agent.py)
    ./update.py --launcher-api         # the contract version launchers check (local-hero)

`status` is this machine against its own copy of the catalog, with no network;
`check` is that copy against the remote.

One door, with verbs. A person who came in through a launcher never sees
install.py or default_agent.py, so everything they can do has a verb here and
every command this catalog suggests comes back through it (LOCAL_AGENTS_FRONT;
see command() in install.py). Adding a verb needs no new launcher: launchers
hand their arguments over untouched.

Getting a new version and installing it are two jobs. `install.py` installs:
no network, same output for the same input, no dependencies — and validate.py,
the smoke suite and the harness all lean on that. Fetching needs the network
and git, which fail in ways an install should never inherit. So this script
owns the fetching and calls install.py through its command line, the same way
a user would. Python 3.9, standard library only, like install.py.

Exit codes: 0 done (or nothing to do) · 1 error · 2 refused, nothing touched ·
3 the remote could not be reached. `install` with arguments exits with
install.py's own code.
"""
import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

# Line-buffered, so a report printed here and install.py's output keep their
# order when both go to a pipe or a CI log; UTF-8 on Windows, as in install.py.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(line_buffering=True,
                            **({"encoding": "utf-8", "errors": "replace"}
                               if sys.platform == "win32" else {}))

OK, ERROR, REFUSED, OFFLINE = 0, 1, 2, 3

# What a launcher knows about this script, and all it knows: this number, and
# where managed_dir() keeps the clone (a launcher clones there when nothing
# exists yet, then runs update.py from it). Bump it when either changes — a
# subcommand renamed or removed, an argument dropped, the managed path moved.
# Adding a subcommand does not bump it: launchers pass their arguments through
# untouched. A launcher that sees a number it does not know tells the user to
# update the launcher instead of failing in some stranger way.
LAUNCHER_API = 1

# Overridable so the tests can point at a local bare repo instead of GitHub.
REPO_URL = os.environ.get("LOCAL_AGENTS_REPO",
                          "https://github.com/jrodrigopuca/local-agents.git")

HERE = Path(__file__).resolve().parent

# A bad https URL makes git ask for a username on the terminal and hang until
# the timeout; fail instead.
GIT_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0")


def managed_dir() -> Path:
    """Where `install` clones the catalog when the user never cloned it. Part
    of the launcher contract (see LAUNCHER_API). The XDG spec ignores a
    relative XDG_DATA_HOME — otherwise every working directory would get a
    clone of its own."""
    xdg = os.environ.get("XDG_DATA_HOME", "")
    base = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / ".local" / "share"
    return base / "local-agents"


# How a suggested command has to start for the person to be able to type it.
# install.py reads the same variable (see its command()): a launcher that knows
# its own name sets it; otherwise this script answers for itself.
FRONT_ENV = "LOCAL_AGENTS_FRONT"


def front() -> str:
    given = os.environ.get(FRONT_ENV, "").strip()
    if given:
        return given
    # Run from the managed clone, it was a launcher that started this and did
    # not say its name: the verb alone is all that can be said truthfully.
    if HERE == managed_dir().resolve():
        return "-"
    try:
        here = Path.cwd().resolve() == HERE
    except OSError:
        here = False
    return "./update.py" if here else str(HERE / "update.py")


def typed(verb: str) -> str:
    """One of this script's verbs as the person can type it."""
    return f"`{verb}`" if front() == "-" else f"{front()} {verb}"


def _say(prefix: str, what: str, detail: tuple, closing: str = "") -> None:
    import textwrap

    def fold(text: str, first: str) -> str:
        if any(len(w) > 50 for w in text.split()):      # a path cannot be folded
            return first + text
        return textwrap.fill(text, width=78, initial_indent=first, subsequent_indent="  ",
                             break_long_words=False, break_on_hyphens=False)

    lines = [fold(what, prefix)] + [fold(d, "  ") for d in detail if d]
    if closing:
        lines.append(f"  {closing}")
    print("\n".join(lines), file=sys.stderr)


def refuse(what: str, *detail: str) -> int:
    """Something that could be done and is not safe to: exit 2, nothing touched."""
    _say("refused: ", what, detail, "Nothing was changed.")
    return REFUSED


def error(what: str, *detail: str, code: int = 0) -> int:
    _say("error: ", what, detail)
    return code or ERROR


def plural(n: int, one: str) -> str:
    return f"{n} {one}{'' if n == 1 else 's'}"


def git(repo: Optional[Path], *args, timeout: int = 120) -> subprocess.CompletedProcess:
    """Never raises: a timeout comes back as a failed command with the reason
    in stderr, so every caller handles one kind of failure."""
    cmd = ["git", *(("-C", str(repo)) if repo else ()), *args]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                              stdin=subprocess.DEVNULL, env=GIT_ENV)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, "", f"git {args[0]} timed out after {timeout}s")


def git_out(repo: Path, *args) -> Optional[str]:
    proc = git(repo, *args)
    return proc.stdout.strip() if proc.returncode == 0 else None


def load_installer(catalog: Path):
    """install.py already knows where every host keeps its config, env
    overrides included (CLAUDE_CONFIG_DIR, CODEX_HOME). Importing it keeps one
    copy of that knowledge; installing still goes through its command line."""
    spec = importlib.util.spec_from_file_location("local_agents_installer",
                                                  catalog / "install.py")
    mod = importlib.util.module_from_spec(spec)
    # dataclasses resolves annotations through sys.modules (Python 3.9).
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def read_stamps(installer, project: Optional[Path] = None) -> List[Tuple[str, dict]]:
    found = []
    for tool in installer.TOOLS:
        here = tool
        if project:
            here = installer.project_tool(tool, project)
            # Run from $HOME, a "project" dir IS the global one (~/.claude):
            # that is a global install, not a project's.
            if here.config_root.resolve() == tool.config_root.resolve():
                continue
        man = installer.read_manifest(here)
        if man and man.get("catalog_commit"):
            found.append((tool.key, man))
    return found


def stamped_path(man: dict) -> Optional[Path]:
    """install.py writes an absolute, resolved path; anything else did not come
    from it and cannot name a clone."""
    p = man.get("catalog_path")
    return Path(p).resolve() if p and Path(p).is_absolute() else None


def resolve_catalog(installer) -> Tuple[Optional[Path], List[Tuple[str, dict]], str]:
    """The clone to update is the one the installs were made FROM — on a
    developer's machine that is their working clone, not this file's folder.
    Two installs stamped from two different clones is a question only the user
    can answer, so it is refused rather than guessed."""
    stamps = read_stamps(installer)
    paths: Dict[Path, List[str]] = {}
    for key, man in stamps:
        p = stamped_path(man)
        if p:
            paths.setdefault(p, []).append(key)
    if len(paths) > 1:
        where = "; ".join(f"{', '.join(keys)} from {p}" for p, keys in paths.items())
        return None, stamps, (f"your installs come from different clones ({where}). "
                              f"Refresh them all from one clone (its install.py --refresh), "
                              f"then run this again.")
    if paths:
        cat = next(iter(paths))
        if not (cat / "install.py").is_file():
            return None, stamps, (f"the clone your installs came from is gone ({cat}). "
                                  f"To reinstall from a fresh clone: "
                                  f"{typed('install --all --tool <tool>')}")
        return cat, stamps, ""
    return HERE, stamps, ""


def changed_units(installer, cat: Path, old: str, new: str) -> List[str]:
    """What an install would change, named the way a user thinks of it: agents,
    skills, CORE files. Only install inputs count — a README edit moves the
    commit but changes no installed file. `--no-renames`: rename detection
    reads file contents, which a blob:none clone would download — network and
    writes inside a command that promises neither."""
    out = git_out(cat, "diff", "--name-only", "--no-renames", old, new, "--",
                  *installer.INSTALL_INPUTS) or ""
    units = []
    for path in out.splitlines():
        parts = path.split("/")
        in_skill = "skills" in parts[:-1] and parts.index("skills") + 1 < len(parts) - 1
        if parts == ["install.py"]:
            unit = "the installer"
        elif in_skill:
            unit = f"skill {parts[parts.index('skills') + 1]}"
        elif len(parts) == 2 and parts[1] == "CORE.md":
            unit = f"{parts[0]}/CORE.md (every agent that inherits it)"
        elif len(parts) == 2 and parts[1] == "AGENTS.md":
            unit = f"agent {parts[0]}"
        else:
            unit = path
        if unit not in units:
            units.append(unit)
    return units


class Standing(NamedTuple):
    behind: int      # commits the clone lacks
    ahead: int       # local commits the remote lacks
    stale: bool      # some install was made from another commit than the remote's
    units: list      # what bringing the remote would change in an install, by name
    waiting: list    # the tools those changes reach


def standing(installer, cat: Path, stamps, target: str) -> Standing:
    """Where the clone and the installs stand against the remote. What is new
    upstream is not downloaded yet, so it cannot be compared by content the
    way --status does: it is read from the remote's diff of install inputs. A
    commit that touches none of them is not an update."""
    behind = int(git_out(cat, "rev-list", "--count", "HEAD..@{u}") or 0)
    ahead = int(git_out(cat, "rev-list", "--count", "@{u}..HEAD") or 0)
    stale, units, waiting = False, [], []
    by_commit: Dict[str, List[str]] = {}
    for key, man in stamps:
        by_commit.setdefault(man["catalog_commit"], []).append(key)
    for commit, keys in by_commit.items():
        if commit == target:
            continue
        stale = True
        if git(cat, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            # Installed from a commit this history lacks: nothing to diff against.
            units += [u for u in ["everything: installed from a commit this history does not have"]
                      if u not in units]
            waiting += keys
            continue
        mine = changed_units(installer, cat, commit, target)
        units += [u for u in mine if u not in units]
        if mine:
            waiting += keys
    return Standing(behind, ahead, stale, units, waiting)


def local_states(installer, cat: Path) -> list:
    """Each tool's state against the clone on disk, as --status computes it."""
    agents, skills = installer.discover(cat)
    by_name = {}
    for s in skills:
        by_name.setdefault(s.name, s)
    return [installer.tool_state(t, agents, by_name, None, cat) for t in installer.TOOLS]


def print_check(installer, cat: Path, upstream: str, target: str, st: Standing) -> None:
    """`check`: the answer first — is there something to bring? — then one row
    per tool that holds an install, in the words --status uses."""
    states = [s for s in local_states(installer, cat) if s.installed]
    if not states:
        print(f"Nothing from this catalog is installed yet.\n\n"
              f"Next: {typed('install --all --tool <tool>')}")
        return
    behind_here = [s for s in states if s.behind]
    if st.waiting:
        print("An update is available.\n")
        print(f"  upstream    {upstream} @ {target[:7]}")
        print(f"              your catalog is {plural(st.behind, 'commit')} behind" if st.behind
              else "              your catalog already has it; the installs do not")
        print(installer.wrapped(", ".join(st.units), 14, "  changes     "))
        print()
    elif behind_here:
        print(f"{len(behind_here)} of {plural(len(states), 'tool')} "
              f"{'is' if len(behind_here) == 1 else 'are'} out of date.\n")
    else:
        print("Everything installed is up to date.\n")
    for s in states:
        key = s.tool.key
        if key in st.waiting:
            print(f"  {key:<13} update available")
        elif s.behind:
            print(installer.wrapped(f"{len(s.behind)} out of date".ljust(15) + " "
                                    + installer.names(s.behind), 16, f"  {key:<13} "))
        else:
            print(f"  {key:<13} {'up to date':<15} "
                  f"{len(s.agents['present'])} agents, {len(s.skills['present'])} skills")
    print()
    if st.waiting or behind_here:
        print(f"Next: {typed('update')}")
    elif st.behind:
        print(f"{upstream} has {plural(st.behind, 'newer commit')}; none changes an installed file.")
    else:
        print(f"Catalog {target[:7]}, same as {upstream}.")
    if st.ahead:
        print(f"Your catalog has {plural(st.ahead, 'local commit')} that "
              f"{'is' if st.ahead == 1 else 'are'} not on {upstream}.")


def prepare(installer) -> Tuple[Optional[Path], list, str, str, int]:
    """Find the clone, fetch, and only then resolve the upstream: a fetch that
    prunes a deleted remote branch leaves `@{u}` pointing at nothing."""
    cat, stamps, why = resolve_catalog(installer)
    if not cat:
        return None, stamps, "", "", refuse(why)
    branch = git_out(cat, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not branch or not git_out(cat, "config", f"branch.{branch}.remote"):
        return None, stamps, "", "", refuse(
            f"{cat} is not on a branch that tracks a remote.", "Try: git checkout main")
    # No remote name here: git takes it from the branch's config, which also
    # covers remotes whose names contain a slash.
    fetch = git(cat, "fetch", "--quiet")
    if fetch.returncode != 0:
        return None, stamps, "", "", error(
            f"could not reach the remote from {cat}.", fetch.stderr.strip()[-200:], code=OFFLINE)
    upstream = git_out(cat, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    target = git_out(cat, "rev-parse", "@{u}")
    if not upstream or not target:
        merge = git_out(cat, "config", f"branch.{branch}.merge") or "its upstream"
        return None, stamps, "", "", refuse(
            f"{branch} tracks {merge}, which the remote no longer has.",
            "Point it at a branch that exists: git branch -u <remote>/<branch>")
    return cat, stamps, upstream, target, OK


def dirty(installer, cat: Path) -> List[str]:
    """Tracked changes anywhere, plus untracked files that would be installed —
    a new skill folder is installed before it is committed."""
    # Raw stdout, not git_out: porcelain lines start with a status column that
    # may be a space, and stripping the output eats it from the first line.
    tracked = git(cat, "status", "--porcelain", "--untracked-files=no").stdout
    untracked = git(cat, "status", "--porcelain", "--untracked-files=all",
                    "--", *installer.INSTALL_INPUTS).stdout
    lines = tracked.splitlines() + [l for l in untracked.splitlines() if l.startswith("??")]
    return [l[3:] for l in lines]


def project_hint(installer, cat: Path):
    """A project install lives in the team's repo and changes there on purpose,
    so it is named, never touched."""
    cwd = Path.cwd()
    mine = [k for k, man in read_stamps(installer, cwd) if stamped_path(man) == cat]
    if mine:
        print(f"\nNote: this repo has a project install ({', '.join(mine)}). It is not updated "
              f"automatically; when you want it:\n  {typed(f'install --refresh --project {cwd}')}")


def cmd_check(installer) -> int:
    cat, stamps, upstream, target, code = prepare(installer)
    if code:
        return code
    print_check(installer, cat, upstream, target, standing(installer, cat, stamps, target))
    return OK


def cmd_update(installer) -> int:
    cat, stamps, upstream, target, code = prepare(installer)
    if code:
        return code
    state = standing(installer, cat, stamps, target)
    changes = dirty(installer, cat)
    if changes:
        shown = ", ".join(changes[:5]) + (" ..." if len(changes) > 5 else "")
        return refuse(f"{cat} has uncommitted changes ({shown}).",
                      "Commit or discard them, then run this again.")
    if state.ahead:
        return refuse(f"{cat} has commits that are not on {upstream}.",
                      "Push or rebase them yourself, then run this again.")
    if not state.behind and not state.stale and not any(
            s.behind for s in local_states(installer, cat) if s.installed):
        print("Everything installed is up to date. Nothing to do.")
        return OK
    before = git_out(cat, "rev-parse", "HEAD")
    if state.behind:
        merge = git(cat, "merge", "--ff-only", "--quiet", "@{u}")
        if merge.returncode != 0:
            return refuse(f"could not fast-forward {cat}.", merge.stderr.strip()[-200:])
        after = git_out(cat, "rev-parse", "HEAD")
        # The catalog's part ends here; what install.py prints next is the rest
        # of the same answer, not another program's output.
        print(f"Catalog updated: {before[:7]} -> {after[:7]} ({plural(state.behind, 'commit')})\n")
    after = git_out(cat, "rev-parse", "HEAD")
    if not stamps:
        print(f"Nothing from this catalog is installed yet.\n"
              f"Next: {typed('install --all --tool <tool>')}")
        return OK
    proc = subprocess.run([sys.executable, str(cat / "install.py"), "--refresh"],
                          stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        return error("the update did not finish (see above).",
                     f"The catalog is already at {after[:7]}; only the installs are behind.",
                     f"Try: {typed('update')}")
    project_hint(installer, cat)
    return OK


def cmd_install(install_args: List[str]) -> int:
    """`install`. The first run on a machine clones where the user never has
    to look; every run hands the install over
    to install.py. `--filter=blob:none` keeps the whole history (the install
    record is a commit, and `check` counts from it) without downloading old
    file contents; `--depth 1` would break that count."""
    dest = managed_dir()
    if (dest / ".git").exists():
        # A clone interrupted half way has a .git and no commit checked out.
        if git(dest, "rev-parse", "--verify", "--quiet", "HEAD").returncode != 0 \
                or not (dest / "install.py").is_file():
            return refuse(f"{dest} is an incomplete clone (an interrupted first run?).",
                          "Delete it and run this again.")
    elif dest.exists() and any(dest.iterdir()):
        return refuse(f"{dest} exists, is not empty and is not a clone.",
                      "Move it away, or set XDG_DATA_HOME to clone somewhere else.")
    else:
        # Into a side folder, renamed only once git is done: a Ctrl-C mid-clone
        # must not leave something that looks like a clone.
        dest.parent.mkdir(parents=True, exist_ok=True)
        partial = dest.with_name(f"{dest.name}.partial-{os.getpid()}")
        print(f"Cloning the catalog into {dest}")
        proc = git(None, "clone", "--quiet", "--filter=blob:none", REPO_URL, str(partial),
                   timeout=300)
        if proc.returncode != 0:
            shutil.rmtree(partial, ignore_errors=True)
            return error(f"could not clone {REPO_URL}.", proc.stderr.strip()[-200:], code=OFFLINE)
        if dest.exists():
            dest.rmdir()  # empty, checked above
        partial.rename(dest)
    if not install_args:
        # install.py with no arguments is its interactive menu (the whole
        # catalog, an agent or skills; which tool; what to do on conflict).
        # Without a person at the keyboard it would only wait on input, so a
        # script gets the commands.
        if sys.stdin.isatty() and sys.stdout.isatty():
            return subprocess.run([sys.executable, str(dest / "install.py")]).returncode
        print(f"Next: {typed('list')}\n"
              f"      then {typed('install --all --tool <tool>')}")
        return OK
    return subprocess.run([sys.executable, str(dest / "install.py"), *install_args]).returncode


def cmd_script(script: str, args: List[str]) -> int:
    """A verb that is one of the catalog's scripts with its flags: `status` is
    install.py --status, `default` is default_agent.py. Run from this clone."""
    if not (HERE / script).is_file():
        return error(f"there is no {script} next to {Path(__file__).name}.",
                     f"Try: {typed('install')}")
    code = subprocess.run([sys.executable, str(HERE / script), *args]).returncode
    if code == OK and args[:1] == ["--uninstall"] and "--dry-run" not in args \
            and HERE == managed_dir().resolve() and not read_stamps(load_installer(HERE)):
        # Through a launcher the clone is the one thing the person never saw.
        where = str(HERE)
        if os.name != "nt" and where.startswith(str(Path.home()) + os.sep):
            where = "~" + where[len(str(Path.home())):]
        print(f"The catalog copy remains at {where}\nDelete that folder to remove it completely.")
    return code


# A verb, and what it runs. Handled before argparse: what follows the verb is
# the script's own arguments, and argparse would eat a leading `--option`.
SCRIPT_VERBS = {"status": ("install.py", ["--status"]), "list": ("install.py", ["--list"]),
                "uninstall": ("install.py", ["--uninstall"]), "default": ("default_agent.py", [])}


class Parser(argparse.ArgumentParser):
    """A usage error is an error (1), not a refusal (2) — argparse's own exit
    code would collide with REFUSED."""
    def error(self, message):
        print(f"error: {message}\n  Try: {typed('--help')}", file=sys.stderr)
        sys.exit(ERROR)


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not shutil.which("git"):
        print("update.py needs git, and it is not on PATH — install git and run it again.",
              file=sys.stderr)
        return ERROR
    # Whatever runs from here on — install.py included — suggests commands the
    # way this person came in.
    os.environ[FRONT_ENV] = front()
    # `install` hands everything after it to install.py untouched. argparse's
    # REMAINDER drops a leading `--option` inside a subcommand, so the split
    # happens before argparse sees the line.
    # `bootstrap` is what this verb was called until 2026-11. Nothing says it
    # any more — it read as a step before installing, not as the install — but
    # it still runs: removing a verb is a new LAUNCHER_API, and every launcher
    # installed globally would stop until it was reinstalled, for a word.
    if argv[:1] in (["install"], ["bootstrap"]):
        return cmd_install(argv[1:])
    if argv[:1] and argv[0] in SCRIPT_VERBS:
        script, flags = SCRIPT_VERBS[argv[0]]
        rest = argv[1:] or (["--status"] if argv[0] == "default" else [])
        return cmd_script(script, flags + rest)
    # The heading of --help is the command this person typed, not a file name
    # they may never have seen.
    ap = Parser(prog=None if front() == "-" else front(), description=__doc__.split("\n")[0])
    ap.add_argument("--launcher-api", action="store_true",
                    help="print the launcher contract version and exit")
    sub = ap.add_subparsers(dest="command", parser_class=Parser)
    sub.add_parser("check", help="what is new upstream since you installed; writes nothing")
    sub.add_parser("update", help="bring the catalog, then refresh every install")
    sub.add_parser("install", help="install: clone the catalog the first time, then run "
                                   "install.py with every argument that follows, as it is")
    sub.add_parser("status", help="what is installed on this machine, and whether it is "
                                  "current (--verbose for every tool in full)")
    sub.add_parser("list", help="what the catalog holds, and which tools were found")
    sub.add_parser("uninstall", help="remove what was installed, and only that")
    sub.add_parser("default", help="the agent a session starts with: --set NAME, --restore")
    args = ap.parse_args(argv)

    if args.launcher_api:
        print(LAUNCHER_API)
        return OK
    if args.command not in ("check", "update"):
        ap.print_help()
        return ERROR
    if not (HERE / "install.py").is_file():
        return error(f"there is no install.py next to {Path(__file__).name}.",
                     f"Try: {typed('install')}")
    # The installer is loaded from HERE only to find where each host keeps its
    # stamps; the clone that gets updated, and whose install.py runs, is the
    # one those stamps name.
    installer = load_installer(HERE)
    return cmd_check(installer) if args.command == "check" else cmd_update(installer)


if __name__ == "__main__":
    sys.exit(main())
