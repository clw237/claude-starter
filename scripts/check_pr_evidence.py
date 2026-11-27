"""Check that a pull request records evidence for every acceptance criterion.

CI runs ``check_pr_evidence.py`` with the pull request body in the ``PR_BODY`` environment variable
(or ``--file <path>`` locally). It fails unless the "How it was tested" section has:

- a table with the columns ``Criterion | Proof | Result`` and at least one row, where every Result
  is ``verified``, or ``after deploy`` when the body also has a ``Refs #N`` line (the issue stays
  open until the criterion is proven after deploy). ``outstanding`` or anything else fails;
- a line ``Tests: <n> added, <n> failed, <n> skipped`` with 0 failed.

Standard library only. See docs/decisions/0004-evidence-for-done.md.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

SECTION = re.compile(r"^##[ \t]+How it was tested[ \t]*$", re.IGNORECASE | re.MULTILINE)
NEXT_SECTION = re.compile(r"^##[ \t]", re.MULTILINE)
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
SEPARATOR_CELL = re.compile(r"^:?-+:?$")
UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")
COUNTS = re.compile(
    r"^\s*Tests:\s*(\d+)\s+added,\s*(\d+)\s+failed,\s*(\d+)\s+skipped\b",
    re.IGNORECASE | re.MULTILINE,
)
REFS = re.compile(r"^\s*Refs\s+#\d+", re.IGNORECASE | re.MULTILINE)
COLUMNS = ("criterion", "proof", "result")
VERIFIED, OUTSTANDING, AFTER_DEPLOY = "verified", "outstanding", "after deploy"


def _section(body: str) -> str | None:
    start = SECTION.search(body)
    if not start:
        return None
    end = NEXT_SECTION.search(body, start.end())
    return body[start.end() : end.start() if end else len(body)]


def _cells(line: str) -> list[str]:
    # Markdown writes a literal pipe inside a cell as \|, so split only on unescaped ones.
    return [cell.strip() for cell in UNESCAPED_PIPE.split(line.strip().strip("|"))]


def _plain(cell: str) -> str:
    """A cell without markdown emphasis or code marks, lower-cased."""
    return re.sub(r"[`*_]", "", cell).strip().lower()


def _rows(section: str) -> list[list[str]] | None:
    """The table's data rows, or None when there's no Criterion | Proof | Result table."""
    lines = section.splitlines()
    for index, line in enumerate(lines):
        if tuple(_plain(cell) for cell in _cells(line)) != COLUMNS:
            continue
        rows = []
        for row in lines[index + 1 :]:
            if not row.strip().startswith("|"):
                break  # the table ends at its first non-table line
            cells = _cells(row)
            if not all(SEPARATOR_CELL.match(cell) for cell in cells):
                rows.append(cells)
        return rows
    return None


def _row_problem(number: int, row: list[str], has_refs: bool) -> str | None:
    if len(row) != len(COLUMNS):
        return f"row {number} has {len(row)} cells, not 3"
    criterion, proof, result = row
    if not criterion or not proof:
        return f"row {number} needs both a criterion and its proof"
    status = _plain(result)
    if status == VERIFIED:
        return None
    if status == AFTER_DEPLOY:
        if has_refs:
            return None
        return f"row {number} is '{AFTER_DEPLOY}', so the issue must stay open: use 'Refs #N'"
    if status == OUTSTANDING:
        return f"row {number} ('{criterion}') is still outstanding"
    return (
        f"row {number} result '{result}' isn't verified, outstanding or {AFTER_DEPLOY}"
    )


def problems(body: str) -> list[str]:
    """Everything missing or unproven in the pull request body; empty when it passes."""
    body = COMMENT.sub("", body.replace("\r\n", "\n"))
    section = _section(body)
    if section is None:
        return ["the body has no '## How it was tested' section"]
    found: list[str] = []
    rows = _rows(section)
    if rows is None:
        found.append("'How it was tested' has no 'Criterion | Proof | Result' table")
    elif not rows:
        found.append("the evidence table has no rows")
    else:
        has_refs = bool(REFS.search(body))
        found += [
            p
            for n, row in enumerate(rows, 1)
            if (p := _row_problem(n, row, has_refs)) is not None
        ]
    counts = COUNTS.search(section)
    if not counts:
        found.append(
            "'How it was tested' needs 'Tests: <n> added, <n> failed, <n> skipped'"
        )
    elif int(counts.group(2)) > 0:
        found.append(f"{counts.group(2)} test(s) failed")
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--file", help="read the body from this file instead of $PR_BODY"
    )
    args = parser.parse_args(argv)
    if args.file:
        with open(args.file, encoding="utf-8") as file:
            body = file.read()
    else:
        body = os.environ.get("PR_BODY", "")
    found = problems(body)
    if found:
        for item in found:
            print(f"::error::Pull request evidence: {item}.")
        return 1
    print("Pull request evidence check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
