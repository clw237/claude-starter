# 0004. "Done" rests on recorded evidence

- Status: Accepted
- Date: 2026-11-27

## Context
"Done" depended on a session saying so: a "Done when" with no stated proof, a free-text "How it was
tested", and a check run nobody could confirm afterwards. Criteria slipped through unproven, tests
mocked the very boundary a criterion was about, and a check could pass on files that were later
changed. The ideas below are adapted from an article on evaluating Claude Code work by its evidence.

## Options
1. Trust the session's summary: no cost / nothing to check it against.
2. Record evidence where the work already flows (issue, pull request, check run) and gate the merge
   on it in CI: a little writing per criterion / catches unproven criteria before merge.
3. Also gate every session stop with a hook that re-checks the record: catches it earlier / costs
   tokens on every stop for little extra evidence (decision 0003).

## Decision
Option 2:
- **Proof up front.** Each "Done when" criterion is one line, `what works → how it's proven` (test,
  running app, database or person). The Definition of Ready requires it; the Definition of Done
  requires every criterion verified. A criterion that crosses a boundary (frontend → API → database)
  needs at least one test or check on the real path, not only mocks.
- **Evidence table and merge gate.** The pull request's "How it was tested" is a
  `Criterion | Proof | Result` table plus test counts. The `pr-evidence` workflow
  (`scripts/check_pr_evidence.py`) fails on a missing table, an `outstanding` row or failed tests, and
  the `main` ruleset requires it. A criterion that can only be proven after deploy is marked
  `(after deploy)` in the issue and `after deploy` in the table; the pull request then says `Refs #N`,
  so the issue stays open until it's proven.
- **Reviewer checks the criteria.** `code-reviewer` reports criteria the diff doesn't meet and starts
  with `Review: completed` or `Review: incomplete (reason)`. The pull request records the first
  verdict, fix rounds and final verdict.
- **Security pass when it matters.** `add-feature` runs `/security-review` when the diff touches auth,
  user input, secrets, file paths, queries or dependencies. No new agent (decision 0003).
- **Check record.** `scripts/check.sh` records each step's exit code, and `scripts/check_record.py`
  writes `.check/last-run.json` (time, commit, working-tree fingerprint, steps, result).
  `check_record.py verify` runs once, before the push, and fails if the record is missing, failed or
  stale. The fingerprint is the git tree of the working tree, untracked files included and ignored
  ones excluded, so committing checked work keeps the record fresh and any content change makes it
  stale. The bare template records `no-project`, accepted only while no project files exist.

## Consequences
- Each issue and pull request takes a few more lines to write, and an unproven criterion can't merge
  quietly. `pr-evidence` becomes required once the owner re-imports the ruleset
  (Settings → Rules → Rulesets).
- The table is self-reported: CI checks that evidence is recorded, not that it's true. The reviewer
  and the owner's read of the pull request still matter.
- `check.sh` needs `python3` to write the record; without it, it warns and `verify` fails.
- Not adopted: a Stop-hook gate on the check record (token cost, decision 0003), capturing headless
  runs, telemetry, cost tracking and file budgets.
