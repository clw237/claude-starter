# 0005. Few, whole commits and squash merges

- Status: Accepted
- Date: 2026-11-27

## Context
A project built from this template ended up with far more commits than changes. Three things in the
template caused it: `add-feature` said to commit after every red-green slice; the changelog line,
review fixes and CI fixes each landed as a commit of their own (the changelog Stop hook only looks
at committed work, so it always asks after the code commit); and the ruleset allowed merge commits,
which copy every branch commit onto `main`.

## Options
1. Keep per-slice commits: fine-grained undo / history is noise, and review is harder.
2. Commit per reviewable unit, fold fixes before the first push, squash-merge: `main` has one commit
   per change and branches show units of work / the branch's fine-grained steps aren't on `main`.
3. Squash merge only: fixes `main` alone / branch history on the pull request stays noisy.

## Decision
Option 2:
- Run `bash scripts/check.sh` after every slice, but commit once per reviewable unit (an issue, or a
  step of an approved plan). Each commit is green and carries its tests, docs and changelog line.
- Before the first push, fold review and check fixes into their commit with `git commit --fixup` and
  an autosquash rebase. After the push, add new commits; force-pushing stays denied (decision 0002).
- The `main` ruleset allows squash merges only.

## Consequences
- `main` has one commit per pull request, which also makes reverting a change one step.
- The finer steps of a branch live only on its pull request. Bisecting `main` lands on a whole
  pull request, not a slice.
- The owner re-imports the ruleset (Settings → Rules → Rulesets) for squash-only to take effect.
- The `code-challenge` skill keeps small commits on `main`, because there the history is part of what's evaluated.
