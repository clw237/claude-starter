# claude-starter

A small, language-agnostic starting template for projects built with
[Claude Code](https://code.claude.com/docs). It gives every new project the same guardrails, so sessions
plan before coding, test as they go, share one definition of "done", and don't waste tokens.

> When you start a real project, replace this README with the project's own.
> The `code-challenge` skill writes a challenge README for you.

## Start a new project
1. On GitHub: **Use this template → Create a new repository**, then clone it.
2. Open Claude Code in the folder (`claude`).
3. Say what you're building and in which language, then run **`/bootstrap`**. It scaffolds the
   minimal project, makes `bash scripts/check.sh` pass, and fills in `CLAUDE.md`.
4. For each change, run **`/add-feature`**.

### Code challenge or interview
```text
/code-challenge
Time limit: 60 minutes. Here is the prompt: <paste>
```
The skill timeboxes the work: understand → set up → plan → build in tested slices → wrap up with a
README covering the approach, trade-offs and how AI was used. Skim
[`.claude/skills/code-challenge/SKILL.md`](.claude/skills/code-challenge/SKILL.md) beforehand so you know the flow.

## What's inside
| Path | What it does | Loaded |
|---|---|---|
| `CLAUDE.md` | Project memory: what this is, the commands, the rules that always apply | every turn (keep it short) |
| `.claude/rules/*.md` | Coding style, security, testing (testing is scoped to test files via `paths:`) | automatically, by path |
| `.claude/skills/bootstrap` | Choose a stack, scaffold it, wire up the check, fill in the placeholders | on demand |
| `.claude/skills/add-feature` | Plan → branch → test first → check → review → pull request | on demand |
| `.claude/skills/code-challenge` | Timed challenge workflow and final README | on demand |
| `.claude/skills/handoff` | When and how to start a fresh, cheaper session | on demand |
| `.claude/agents/planner` | Read-only implementation plan for larger changes | when delegated |
| `.claude/agents/code-reviewer` | Read-only review with an evidence gate (no noise findings) | when delegated |
| `.claude/agents/build-fixer` | Smallest fix for a red check, never loosens tests | when delegated |
| `.claude/settings.json` | Allows the check and git basics; asks before installs and pushes; denies force-push, `rm -rf`, reading secrets | always |
| `.claude/hooks/format.sh` | Formats each file after Claude edits it, if a formatter is installed | after every edit |
| `scripts/check.sh` | **The** definition of done: format check, lint, types, tests. Auto-detects Python, JS/TS, Go, Rust, Gradle and .NET | Claude, you and CI |
| `PLAN.md` | Design doc: goal, requirements, edge cases, approach, build order | |
| `docs/decisions/` | Short records of significant choices | |
| `docs/claude-code-cheatsheet.md` | Keys, commands and token-saving habits | |
| `.github/` | CI that runs `scripts/check.sh`, and a pull request template | |

Personal, uncommitted overrides go in `CLAUDE.local.md` and `.claude/settings.local.json`, which are gitignored.
Hooks use bash, which on Windows means Git Bash (Claude Code uses it there by default).

## Principles
1. **One definition of done.** `scripts/check.sh` is run by Claude, by you and by CI.
2. **Plan, then test-first slices.** Small, reviewable, always-green commits.
3. **Lean context.** `CLAUDE.md` holds only what's needed every turn. Everything else loads on demand.
4. **Guardrails over reminders.** Permissions and hooks enforce what prose can only ask for.
5. **Corrections stick.** When you correct Claude twice, edit the rule, skill or `CLAUDE.md` in place.
6. **Grow it only when needed.** Add a skill, agent or rule after the same need has come up twice.

## Credits
Patterns adapted from [affaan-m/ECC](https://github.com/affaan-m/ECC) (MIT): lean memory plus modular
rules, scoped read-only subagents, the reviewer's confidence gate, format-on-edit hooks, and
compacting at strategic moments. This template deliberately keeps a small core rather than ECC's full catalogue.
