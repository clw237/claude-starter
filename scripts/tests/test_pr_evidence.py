"""Tests for scripts/check_pr_evidence.py. Standard library only."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_pr_evidence as ev

TABLE = "| Criterion | Proof | Result |\n|---|---|---|\n"
COUNTS = "Tests: 2 added, 0 failed, 0 skipped\n"


def body(rows: str, counts: str = COUNTS, issues: str = "Closes #4") -> str:
    return (
        f"## What changed\nStuff.\n\n## Issues\n{issues}\n\n"
        f"## How it was tested\n{TABLE}{rows}\n{counts}\n## Look closely at\nNothing special.\n"
    )


class Evidence(unittest.TestCase):
    def test_all_verified_passes(self) -> None:
        rows = "| Saves a draft | integration test | verified |\n| Lists drafts | app | **Verified** |\n"
        self.assertEqual(ev.problems(body(rows)), [])

    def test_outstanding_row_fails(self) -> None:
        rows = "| Saves a draft | integration test | verified |\n| Lists drafts | app | outstanding |\n"
        self.assertIn(
            "row 2 ('Lists drafts') is still outstanding", ev.problems(body(rows))
        )

    def test_missing_section_fails(self) -> None:
        self.assertEqual(
            ev.problems("## What changed\nx\n"),
            ["the body has no '## How it was tested' section"],
        )

    def test_missing_table_fails(self) -> None:
        text = "## How it was tested\nRan it, looked fine.\n" + COUNTS
        self.assertIn(
            "'How it was tested' has no 'Criterion | Proof | Result' table",
            ev.problems(text),
        )

    def test_table_without_rows_fails(self) -> None:
        self.assertIn("the evidence table has no rows", ev.problems(body("")))

    def test_unfilled_template_row_fails(self) -> None:
        rows = "| | | verified / outstanding |\n"
        self.assertIn(
            "row 1 needs both a criterion and its proof", ev.problems(body(rows))
        )

    def test_unknown_result_fails(self) -> None:
        problems = ev.problems(body("| Saves | test | probably |\n"))
        self.assertTrue(any("isn't verified" in p for p in problems), problems)

    def test_table_in_another_section_does_not_count(self) -> None:
        text = f"## What changed\n{TABLE}| a | b | verified |\n\n## How it was tested\n{COUNTS}"
        self.assertIn(
            "'How it was tested' has no 'Criterion | Proof | Result' table",
            ev.problems(text),
        )

    def test_table_inside_html_comment_does_not_count(self) -> None:
        text = f"## How it was tested\n<!--\n{TABLE}| a | b | verified |\n-->\n{COUNTS}"
        self.assertIn(
            "'How it was tested' has no 'Criterion | Proof | Result' table",
            ev.problems(text),
        )

    def test_after_deploy_passes_with_refs(self) -> None:
        rows = "| Emails arrive | checked in production | after deploy |\n"
        self.assertEqual(
            ev.problems(body(rows, issues="Refs #4 (email check after deploy)")), []
        )

    def test_after_deploy_fails_without_refs(self) -> None:
        rows = "| Emails arrive | checked in production | after deploy |\n"
        problems = ev.problems(body(rows, issues="Closes #4"))
        self.assertTrue(any("use 'Refs #N'" in p for p in problems), problems)

    def test_missing_counts_fail(self) -> None:
        problems = ev.problems(body("| a | b | verified |\n", counts=""))
        self.assertIn(
            "'How it was tested' needs 'Tests: <n> added, <n> failed, <n> skipped'",
            problems,
        )

    def test_failed_tests_fail(self) -> None:
        problems = ev.problems(
            body(
                "| a | b | verified |\n", counts="Tests: 3 added, 1 failed, 0 skipped\n"
            )
        )
        self.assertIn("1 test(s) failed", problems)

    def test_escaped_pipe_stays_inside_its_cell(self) -> None:
        rows = "| Filters by a \\| b | unit test | verified |\n"
        self.assertEqual(ev.problems(body(rows)), [])

    def test_a_later_table_is_not_read_as_evidence(self) -> None:
        rows = "| a | b | verified |\n\nOther notes:\n| Step | Took |\n|---|---|\n| build | 3s |\n"
        self.assertEqual(ev.problems(body(rows)), [])

    def test_windows_line_endings_pass(self) -> None:
        self.assertEqual(
            ev.problems(body("| a | b | verified |\n").replace("\n", "\r\n")), []
        )


if __name__ == "__main__":
    unittest.main()
