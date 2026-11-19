---
name: add-feature
description: Use when starting, building or finishing any code change (feature, fix, refactor), including work on a GitHub issue. Covers planning, branching, tests, the check, review, changelog and the pull request.
---

# Adding a feature or fix

## 1. Understand and plan
- Read the issue or request in full. If it's unclear, too big, or conflicts with `PLAN.md`, say so and
  ask. Don't silently narrow it.
- For anything beyond a one-file change, write a short plan (use plan mode, or the `planner` subagent
  when the codebase is large): files to touch, tests to add, risks. **Wait for the owner's approval.**
- If the work changes the design, update `PLAN.md` in the same branch. For a significant choice, add a
  record in `docs/decisions/`.
- Ideas outside the scope become follow-up issues, not extra code.

## 2. Branch
`git checkout main && git pull`, then `feature/<name>`, `fix/<name>` or `chore/<name>`. Start the name with the
issue number when there is one (`fix/42-empty-input`). If the session assigns a branch, use it.

## 3. Build: test first, small steps
1. Write a failing test that describes the behavior (Arrange, Act, Assert).
2. Write the simplest code that passes it.
3. Refactor while green.
4. Run `bash scripts/check.sh`, then commit. Repeat for each slice.
- Fix the code, not the test, unless the test is wrong. Never skip, disable or loosen a check.
- Don't let tests touch the network. Use fakes and fixtures.

## 4. Review
- Run the `code-reviewer` subagent (or `/code-review`) on the branch diff and fix what it finds.
- Re-read the diff yourself: no debug output, no commented-out code, no unrelated changes.

## 5. Finish
- If the owner would notice the change, add a line under `## [Unreleased]` in `CHANGELOG.md`.
- Push with `git push -u origin <branch>` and open a pull request. Fill in every section of the template
  and put `Closes #N` for each issue it closes.
- Wait for CI to go green. If it fails, reproduce it locally with `bash scripts/check.sh`, fix it and push.
- Never merge your own pull request unless the owner says to.
