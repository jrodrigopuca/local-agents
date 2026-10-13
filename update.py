#!/usr/bin/env python3
"""Bring the local-agents catalog, and every install made from it, up to date.

    ./update.py check                  # what changed upstream since you installed — writes nothing
    ./update.py update                 # fast-forward the clone, then install.py --refresh
    ./update.py bootstrap [ARGS...]    # first time: clone the catalog, then install.py ARGS
    ./update.py --launcher-api         # the contract version launchers check (local-hero)

Getting a new version and installing it are two jobs. `install.py` installs:
no network, same output for the same input, no dependencies — and validate.py,
the smoke suite and the harness all lean on that. Fetching needs the network
and git, which fail in ways an install should never inherit. So this script
owns the fetching and calls install.py through its command line, the same way
a user would. Python 3.9, standard library only, like install.py.

Exit codes: 0 done (or nothing to do) · 1 error · 2 refused, nothing touched ·
3 the remote could not be reached. `bootstrap` with install arguments exits
with install.py's own code.
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
    """Where bootstrap clones the catalog when the user never cloned it. Part
    of the launcher contract (see LAUNCHER_API)."""
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "local-agents"


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
                              f"Reinstall them from one clone with install.py --refresh, "
                              f"then run this again.")
    if paths:
        cat = next(iter(paths))
        if not (cat / "install.py").is_file():
            return None, stamps, (f"the clone your installs came from is gone ({cat}). "
                                  f"Run `update.py bootstrap --all --tool <tool>` to "
                                  f"reinstall from a fresh clone.")
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
    behind: int     # commits the clone lacks
    ahead: int      # local commits the remote lacks
    stale: bool     # some install is not at the remote's commit


def report(installer, cat: Path, stamps, upstream: str, target: str) -> Standing:
    """Print where the clone and the installs stand against the remote."""
    behind = int(git_out(cat, "rev-list", "--count", "HEAD..@{u}") or 0)
    ahead = int(git_out(cat, "rev-list", "--count", "@{u}..HEAD") or 0)
    print(f"catalog  {cat}")
    print(f"remote   {upstream} @ {target[:7]}")
    state = "up to date" if not behind else f"{behind} commit{'s' * (behind != 1)} behind"
    if ahead:
        state += f", {ahead} local commit{'s' * (ahead != 1)} not on the remote"
    print(f"clone    {state}")

    stale = False
    if not stamps:
        print("installs none — install with `install.py --all --tool <tool>`")
    by_commit: Dict[str, List[str]] = {}
    for key, man in stamps:
        by_commit.setdefault(man["catalog_commit"], []).append(key)
    for commit, keys in by_commit.items():
        who = ", ".join(keys)
        if commit == target:
            print(f"installs {who}: up to date")
            continue
        stale = True
        if git(cat, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            print(f"installs {who}: from {commit[:7]}, which is not in this history "
                  f"— update will reinstall them")
            continue
        n = int(git_out(cat, "rev-list", "--count", f"{commit}..{target}") or 0)
        units = changed_units(installer, cat, commit, target)
        print(f"installs {who}: from {commit[:7]}, {n} commit{'s' * (n != 1)} behind")
        for u in units or ["no installed file changes (docs only)"]:
            print(f"           · {u}")
    return Standing(behind, ahead, stale)


def prepare(installer) -> Tuple[Optional[Path], list, str, str, int]:
    """Find the clone, fetch, and only then resolve the upstream: a fetch that
    prunes a deleted remote branch leaves `@{u}` pointing at nothing."""
    cat, stamps, why = resolve_catalog(installer)
    if not cat:
        print(f"refusing: {why}", file=sys.stderr)
        return None, stamps, "", "", REFUSED
    branch = git_out(cat, "symbolic-ref", "--quiet", "--short", "HEAD")
    if not branch or not git_out(cat, "config", f"branch.{branch}.remote"):
        print(f"refusing: {cat} is not on a branch that tracks a remote "
              f"(git checkout main?)", file=sys.stderr)
        return None, stamps, "", "", REFUSED
    # No remote name here: git takes it from the branch's config, which also
    # covers remotes whose names contain a slash.
    fetch = git(cat, "fetch", "--quiet")
    if fetch.returncode != 0:
        print(f"could not reach the remote from {cat}: {fetch.stderr.strip()[-200:]}",
              file=sys.stderr)
        return None, stamps, "", "", OFFLINE
    upstream = git_out(cat, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    target = git_out(cat, "rev-parse", "@{u}")
    if not upstream or not target:
        merge = git_out(cat, "config", f"branch.{branch}.merge") or "its upstream"
        print(f"refusing: {branch} tracks {merge}, which the remote no longer has. "
              f"Point it at a branch that exists (git branch -u <remote>/<branch>).",
              file=sys.stderr)
        return None, stamps, "", "", REFUSED
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
        print(f"\nThis repo has a project install ({', '.join(mine)}). It is not updated "
              f"automatically; when you want it:\n  {cat / 'install.py'} --refresh --project {cwd}")


def cmd_check(installer) -> int:
    cat, stamps, upstream, target, code = prepare(installer)
    if code:
        return code
    report(installer, cat, stamps, upstream, target)
    return OK


def cmd_update(installer) -> int:
    cat, stamps, upstream, target, code = prepare(installer)
    if code:
        return code
    state = report(installer, cat, stamps, upstream, target)
    changes = dirty(installer, cat)
    if changes:
        shown = ", ".join(changes[:5]) + (" …" if len(changes) > 5 else "")
        print(f"\nrefusing: {cat} has uncommitted changes ({shown}). Commit or "
              f"discard them; nothing was touched.", file=sys.stderr)
        return REFUSED
    if state.ahead:
        print(f"\nrefusing: {cat} has commits that are not on {upstream}. Push or "
              f"rebase them yourself; nothing was touched.", file=sys.stderr)
        return REFUSED
    if not state.behind and not state.stale:
        print("\nNothing to do.")
        return OK
    before = git_out(cat, "rev-parse", "HEAD")
    if state.behind:
        merge = git(cat, "merge", "--ff-only", "--quiet", "@{u}")
        if merge.returncode != 0:
            print(f"\nrefusing: could not fast-forward {cat}: "
                  f"{merge.stderr.strip()[-200:]}", file=sys.stderr)
            return REFUSED
    after = git_out(cat, "rev-parse", "HEAD")
    print(f"\nclone    {before[:7]} → {after[:7]}")
    if not stamps:
        print("Nothing installed yet — install with "
              f"`{cat / 'install.py'} --all --tool <tool>`.")
        return OK
    print("refresh  install.py --refresh\n")
    proc = subprocess.run([sys.executable, str(cat / "install.py"), "--refresh"],
                          stdin=subprocess.DEVNULL)
    if proc.returncode != 0:
        print(f"\ninstall.py --refresh exited {proc.returncode}; the clone is at "
              f"{after[:7]}, run it again once the error above is fixed.", file=sys.stderr)
        return ERROR
    project_hint(installer, cat)
    return OK


def cmd_bootstrap(install_args: List[str]) -> int:
    """First run on a machine: clone where the user never has to look, then
    hand the install over to install.py. `--filter=blob:none` keeps the whole
    history (install.py --status counts commits) without downloading old file
    contents; `--depth 1` would break that count."""
    dest = managed_dir()
    if (dest / ".git").exists():
        print(f"catalog already cloned at {dest} — use `update` to bring it up to date")
    elif dest.exists() and any(dest.iterdir()):
        print(f"refusing: {dest} exists, is not empty and is not a clone. Move it "
              f"away, or set XDG_DATA_HOME to clone somewhere else.", file=sys.stderr)
        return REFUSED
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"cloning {REPO_URL} → {dest}")
        proc = git(None, "clone", "--quiet", "--filter=blob:none", REPO_URL, str(dest),
                   timeout=300)
        if proc.returncode != 0:
            print(f"could not clone {REPO_URL}: {proc.stderr.strip()[-200:]}",
                  file=sys.stderr)
            return OFFLINE
    if not install_args:
        print(f"Next: {dest / 'install.py'} --list, then --all --tool <tool>")
        return OK
    return subprocess.run([sys.executable, str(dest / "install.py"), *install_args]).returncode


class Parser(argparse.ArgumentParser):
    """A usage error is an error (1), not a refusal (2) — argparse's own exit
    code would collide with REFUSED."""
    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"{self.prog}: error: {message}", file=sys.stderr)
        sys.exit(ERROR)


def main(argv: Optional[List[str]] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not shutil.which("git"):
        print("update.py needs git, and it is not on PATH — install git and run it again.",
              file=sys.stderr)
        return ERROR
    # bootstrap hands everything after it to install.py untouched. argparse's
    # REMAINDER drops a leading `--option` inside a subcommand, so the split
    # happens before argparse sees the line.
    if argv[:1] == ["bootstrap"]:
        return cmd_bootstrap(argv[1:])
    ap = Parser(description=__doc__.split("\n")[0])
    ap.add_argument("--launcher-api", action="store_true",
                    help="print the launcher contract version and exit")
    sub = ap.add_subparsers(dest="command", parser_class=Parser)
    sub.add_parser("check", help="show what changed upstream since you installed; writes nothing")
    sub.add_parser("update", help="fast-forward the clone, then reinstall with install.py --refresh")
    sub.add_parser("bootstrap", help="clone the catalog, then run install.py with every "
                                     "argument that follows, as it is")
    args = ap.parse_args(argv)

    if args.launcher_api:
        print(LAUNCHER_API)
        return OK
    if args.command not in ("check", "update"):
        ap.print_help()
        return ERROR
    if not (HERE / "install.py").is_file():
        print(f"no install.py next to {Path(__file__).name}: run `bootstrap` first",
              file=sys.stderr)
        return ERROR
    # The installer is loaded from HERE only to find where each host keeps its
    # stamps; the clone that gets updated, and whose install.py runs, is the
    # one those stamps name.
    installer = load_installer(HERE)
    return cmd_check(installer) if args.command == "check" else cmd_update(installer)


if __name__ == "__main__":
    sys.exit(main())
