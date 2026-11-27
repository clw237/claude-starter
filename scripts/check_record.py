"""Record the result of ``scripts/check.sh`` and verify it before pushing.

- ``check_record.py write --exit-code N [--no-project] [STEP ...]``: ``check.sh`` calls this when it
  exits. Each STEP is ``<exit code><TAB><command>``. It saves ``.check/last-run.json`` with the time,
  the commit, a fingerprint of the working tree, each step's exit code and the overall result
  (``passed``, ``failed`` or ``no-project``).
- ``check_record.py verify``: exits 1 when the record is missing, unreadable, failed, or stale.

The fingerprint is the git tree id of the working tree as it stands: HEAD plus uncommitted changes
plus untracked files that ``.gitignore`` doesn't exclude. It is the same before and after that work
is committed, so running the check and then committing doesn't make the record stale, and it
changes with any change to the content. ``no-project`` (the bare template, before bootstrap) passes
only while no project files exist. Standard library only.
See docs/decisions/0004-evidence-for-done.md.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

RECORD = Path(".check") / "last-run.json"
PASSED, FAILED, NO_PROJECT = "passed", "failed", "no-project"
# The files scripts/check.sh looks for at the root to detect a project.
PROJECT_FILES = ("pyproject.toml", "package.json", "go.mod", "Cargo.toml", "gradlew")
PROJECT_GLOBS = ("*.sln", "*.csproj")
GIT = shutil.which("git") or "git"


def _git(root: Path, *args: str, env: dict[str, str] | None = None) -> str:
    # Fixed git subcommands built here; no user input reaches the command line.
    return subprocess.run(
        [GIT, *args],
        cwd=root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout.strip()


def _head(root: Path) -> str | None:
    try:
        return _git(root, "rev-parse", "--verify", "--quiet", "HEAD")
    except subprocess.CalledProcessError:  # no commits yet
        return None


def fingerprint(root: Path) -> str:
    """The git tree id of the working tree, untracked files included, ignored files excluded.

    Built in a copy of the index, so the real index (what's staged) is never touched.
    """
    # --git-path prints a path relative to root, or an absolute one; joining handles both.
    index = root / _git(root, "rev-parse", "--git-path", "index")
    with tempfile.TemporaryDirectory() as scratch:
        temp_index = Path(scratch) / "index"
        if index.exists():
            shutil.copyfile(
                index, temp_index
            )  # keeps git's stat cache, so this stays fast
        env = {**os.environ, "GIT_INDEX_FILE": str(temp_index)}
        if _head(root):
            _git(root, "read-tree", "HEAD", env=env)
        _git(root, "add", "--all", ".", env=env)
        return _git(root, "write-tree", env=env)


def has_project(root: Path) -> bool:
    return any((root / name).exists() for name in PROJECT_FILES) or any(
        next(root.glob(pattern), None) for pattern in PROJECT_GLOBS
    )


def parse_step(raw: str) -> dict[str, object]:
    code, sep, command = raw.partition("\t")
    if not sep or not code.strip().lstrip("-").isdigit():
        raise ValueError(f"a step must be '<exit code><TAB><command>', got {raw!r}")
    return {"command": command, "exit_code": int(code)}


def overall(steps: list[dict[str, object]], exit_code: int, no_project: bool) -> str:
    if any(step["exit_code"] != 0 for step in steps):
        return FAILED
    if no_project:
        return NO_PROJECT
    return PASSED if exit_code == 0 and steps else FAILED


def build_record(
    root: Path, steps: list[dict[str, object]], exit_code: int, no_project: bool
) -> dict[str, object]:
    return {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": _head(root),
        "fingerprint": fingerprint(root),
        "steps": steps,
        "exit_code": exit_code,
        "result": overall(steps, exit_code, no_project),
    }


def verify_problem(
    record: dict[str, object] | None, current_fingerprint: str, project_present: bool
) -> str | None:
    """Why the record doesn't prove the current tree passed the check, or None when it does."""
    if record is None:
        return "no check record. Run: bash scripts/check.sh"
    result = record.get("result")
    if result == FAILED:
        failed = [
            s.get("command") for s in record.get("steps", []) if s.get("exit_code") != 0
        ]
        detail = f" ({', '.join(map(str, failed))})" if failed else ""
        return f"the last check failed{detail}. Fix it and run: bash scripts/check.sh"
    if result == NO_PROJECT and project_present:
        return "the last check found no project, but there is one now. Run: bash scripts/check.sh"
    if result not in (PASSED, NO_PROJECT):
        return f"the check record has an unknown result {result!r}. Run: bash scripts/check.sh"
    if record.get("fingerprint") != current_fingerprint:
        return "the files changed since the last check. Run: bash scripts/check.sh"
    return None


def _load(path: Path) -> dict[str, object] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    write = commands.add_parser(
        "write", help="save the record (called by scripts/check.sh)"
    )
    write.add_argument("--exit-code", type=int, required=True)
    write.add_argument("--no-project", action="store_true")
    write.add_argument("steps", nargs="*", help="'<exit code><TAB><command>' per step")
    commands.add_parser("verify", help="exit 1 unless the record is a fresh pass")
    args = parser.parse_args(argv)

    root = Path(_git(Path.cwd(), "rev-parse", "--show-toplevel"))
    path = root / RECORD
    if args.command == "write":
        steps = [parse_step(raw) for raw in args.steps]
        record = build_record(root, steps, args.exit_code, args.no_project)
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        print(f"Check record: {record['result']} ({RECORD}).")
        return 0

    reason = verify_problem(_load(path), fingerprint(root), has_project(root))
    if reason:
        print(f"Check record: {reason}", file=sys.stderr)
        return 1
    print("Check record: fresh pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
