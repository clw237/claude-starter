# Contributing

Most changes here are made by Claude Code sessions for the owner. The same rules are in `CLAUDE.md`
and the skills under `.claude/skills/`. This file is the human-readable overview.

| Question | Where the answer lives |
|---|---|
| What should it do and how is it built? | `PLAN.md` |
| Why was it built that way? | `docs/decisions/` (one short record per significant choice) |
| What's left to do? | GitHub Issues (or `PLAN.md` §5 for a small project) |
| What changed? | `CHANGELOG.md` and the git history |

## How work flows
1. **Plan.** Update `PLAN.md` (or the issue) with what will change and how it will be tested.
2. **Branch.** Use `feature/<name>`, `fix/<name>` or `chore/<name>`. Never commit to `main`.
3. **Build in slices.** For each slice, write a test, make it pass, run `bash scripts/check.sh`, then commit.
4. **Review.** Run the `code-reviewer` subagent (or `/code-review`) on the diff and fix what it finds.
5. **Pull request.** Fill in `.github/pull_request_template.md`. CI runs the same `scripts/check.sh`.
   The owner reviews and merges.

## Commit messages
A short imperative title (`Add CSV parser`, `Fix off-by-one in pager`). Below it, say what changed
and why. For a pull request the owner would notice, add a line under `## [Unreleased]` in `CHANGELOG.md`.

## Working with Claude Code
- Keep `CLAUDE.md` short. Detail belongs in skills (loaded on demand) and `.claude/rules/` (scoped by path).
- Plan mode (Shift+Tab) is for anything non-trivial. Approve the plan before any edits.
- Start a fresh session (the `handoff` skill) instead of dragging a long one into unrelated work.
- Read every line Claude writes before it's committed. If you can't explain it, ask Claude to explain it or simplify it.
