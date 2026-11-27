## What changed
<!-- A short summary, and why. -->

## Issues
<!-- One line per issue. "Closes #n" when this finishes it; "Refs #n" when it does part, and say what's left. -->
Closes #

## How it was tested
<!-- One row per "Done when" criterion of each issue, with the proof the issue names and what it
     showed. Result is verified, outstanding (blocks the merge) or after deploy (the issue line above
     must then say "Refs #n"). The pr-evidence check reads this table. -->
| Criterion | Proof | Result |
|---|---|---|
| | | verified / outstanding |

Tests: 0 added, 0 failed, 0 skipped

## Look closely at
<!-- Risky parts, design choices, trade-offs. Write "Nothing special" if there are none. -->

## Follow-ups
<!-- Things found along the way that are out of scope, to turn into issues. Or "none". -->

## Checklist
- [ ] `bash scripts/check.sh` passes
- [ ] Every row in "How it was tested" is verified (or after deploy, with `Refs #n`)
- [ ] Checked in the running app, not just in tests
- [ ] The `code-reviewer` subagent (or `/code-review`) was run on the diff and its findings fixed
- [ ] `CHANGELOG.md` has a line under `[Unreleased]` (or a commit says `Changelog: none`)
- [ ] `PLAN.md` updated if the design changed; a record in `docs/decisions/` for a significant choice
- [ ] CI is green on this pull request's current head, with the branch up to date with `main`
