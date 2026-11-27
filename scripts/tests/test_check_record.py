"""Tests for scripts/check_record.py. Standard library only; uses throwaway local git repos."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import ClassVar

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_record as cr

SCRIPT = Path(__file__).resolve().parents[1] / "check_record.py"


def git(root: Path, *args: str) -> str:
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t",
        "GIT_AUTHOR_EMAIL": "t@example.invalid",
        "GIT_COMMITTER_NAME": "t",
        "GIT_COMMITTER_EMAIL": "t@example.invalid",
        "GIT_CONFIG_GLOBAL": os.devnull,
    }
    return subprocess.run(
        ["git", *args], cwd=root, env=env, check=True, capture_output=True, text=True
    ).stdout


class Repo(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.root = Path(self._dir.name)
        git(self.root, "init", "-q")
        (self.root / ".gitignore").write_text(".check/\nignored.txt\n")
        (self.root / "app.py").write_text("print('hi')\n")
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", "first")

    def tearDown(self) -> None:
        self._dir.cleanup()

    def run_script(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,  # the tests assert on the exit code
        )


class Fingerprint(Repo):
    def test_same_content_gives_the_same_fingerprint(self) -> None:
        self.assertEqual(cr.fingerprint(self.root), cr.fingerprint(self.root))

    def test_editing_a_tracked_file_changes_it(self) -> None:
        before = cr.fingerprint(self.root)
        (self.root / "app.py").write_text("print('bye')\n")
        self.assertNotEqual(cr.fingerprint(self.root), before)

    def test_adding_an_untracked_file_changes_it(self) -> None:
        before = cr.fingerprint(self.root)
        (self.root / "new.py").write_text("x = 1\n")
        self.assertNotEqual(cr.fingerprint(self.root), before)

    def test_deleting_a_tracked_file_changes_it(self) -> None:
        before = cr.fingerprint(self.root)
        (self.root / "app.py").unlink()
        self.assertNotEqual(cr.fingerprint(self.root), before)

    def test_ignored_files_do_not_change_it(self) -> None:
        before = cr.fingerprint(self.root)
        (self.root / "ignored.txt").write_text("scratch\n")
        self.assertEqual(cr.fingerprint(self.root), before)

    def test_committing_the_work_keeps_it(self) -> None:
        (self.root / "app.py").write_text("print('bye')\n")
        before = cr.fingerprint(self.root)
        git(self.root, "commit", "-q", "-am", "second")
        self.assertEqual(cr.fingerprint(self.root), before)

    def test_it_leaves_the_staged_changes_alone(self) -> None:
        (self.root / "new.py").write_text("x = 1\n")
        cr.fingerprint(self.root)
        self.assertEqual(git(self.root, "status", "--porcelain"), "?? new.py\n")


class Overall(unittest.TestCase):
    ok: ClassVar[dict[str, object]] = {"command": "pytest", "exit_code": 0}
    bad: ClassVar[dict[str, object]] = {"command": "pytest", "exit_code": 1}

    def test_all_steps_passing_is_passed(self) -> None:
        self.assertEqual(cr.overall([self.ok], 0, no_project=False), cr.PASSED)

    def test_a_failed_step_is_failed(self) -> None:
        self.assertEqual(
            cr.overall([self.ok, self.bad], 1, no_project=False), cr.FAILED
        )

    def test_no_steps_is_failed(self) -> None:
        self.assertEqual(cr.overall([], 0, no_project=False), cr.FAILED)

    def test_nonzero_exit_without_a_failed_step_is_failed(self) -> None:
        self.assertEqual(cr.overall([self.ok], 130, no_project=False), cr.FAILED)

    def test_no_project_with_passing_steps_is_no_project(self) -> None:
        self.assertEqual(cr.overall([self.ok], 1, no_project=True), cr.NO_PROJECT)

    def test_no_project_with_a_failed_step_is_failed(self) -> None:
        self.assertEqual(cr.overall([self.bad], 1, no_project=True), cr.FAILED)

    def test_bad_step_text_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            cr.parse_step("pytest")


class VerifyProblem(unittest.TestCase):
    def record(self, result: str = cr.PASSED, fp: str = "abc") -> dict[str, object]:
        return {
            "result": result,
            "fingerprint": fp,
            "steps": [{"command": "pytest", "exit_code": 1}],
        }

    def test_fresh_pass_is_fine(self) -> None:
        self.assertIsNone(cr.verify_problem(self.record(), "abc", project_present=True))

    def test_missing_record_fails(self) -> None:
        self.assertIn("no check record", cr.verify_problem(None, "abc", True) or "")

    def test_failed_record_fails_and_names_the_step(self) -> None:
        reason = cr.verify_problem(self.record(cr.FAILED), "abc", True) or ""
        self.assertIn("failed (pytest)", reason)

    def test_stale_record_fails(self) -> None:
        self.assertIn(
            "changed since", cr.verify_problem(self.record(), "def", True) or ""
        )

    def test_no_project_passes_only_without_a_project(self) -> None:
        self.assertIsNone(cr.verify_problem(self.record(cr.NO_PROJECT), "abc", False))
        self.assertIn(
            "there is one now",
            cr.verify_problem(self.record(cr.NO_PROJECT), "abc", True) or "",
        )

    def test_unknown_result_fails(self) -> None:
        self.assertIn(
            "unknown result", cr.verify_problem(self.record("maybe"), "abc", True) or ""
        )


class CommandLine(Repo):
    def test_write_then_verify_passes(self) -> None:
        self.assertEqual(
            self.run_script("write", "--exit-code", "0", "0\tpytest").returncode, 0
        )
        record = json.loads((self.root / ".check" / "last-run.json").read_text())
        self.assertEqual(record["result"], cr.PASSED)
        self.assertEqual(record["commit"], git(self.root, "rev-parse", "HEAD").strip())
        self.assertEqual(self.run_script("verify").returncode, 0)

    def test_verify_fails_without_a_record(self) -> None:
        result = self.run_script("verify")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no check record", result.stderr)

    def test_verify_fails_after_a_failed_run(self) -> None:
        self.run_script("write", "--exit-code", "1", "1\tpytest")
        self.assertEqual(self.run_script("verify").returncode, 1)

    def test_verify_fails_after_an_edit(self) -> None:
        self.run_script("write", "--exit-code", "0", "0\tpytest")
        (self.root / "app.py").write_text("print('changed')\n")
        self.assertEqual(self.run_script("verify").returncode, 1)

    def test_verify_fails_on_a_corrupt_record(self) -> None:
        (self.root / ".check").mkdir()
        (self.root / ".check" / "last-run.json").write_text("{not json")
        self.assertEqual(self.run_script("verify").returncode, 1)


if __name__ == "__main__":
    unittest.main()
