#!/usr/bin/env bash
# The one command that means "done": format check, lint, types, tests.
# Claude, the owner and CI all run this. The bootstrap skill may replace the
# auto-detection below with the exact commands for this project.
set -euo pipefail
cd "$(dirname "$0")/.."

ran=0
no_project=0
steps=()
has() { command -v "$1" >/dev/null 2>&1; }

# Each step's exit code is kept for the check record. The first failure still stops the run.
step() {
  echo; echo "==> $*"
  local code=0
  "$@" || code=$?
  steps+=("$code"$'\t'"$*")
  ran=1
  [ "$code" -eq 0 ] || exit "$code"
}

# On exit, save .check/last-run.json, which `python3 scripts/check_record.py verify` reads before a push.
record() {
  local code=$?
  if has python3; then
    local flag=()
    [ "$no_project" -eq 1 ] && flag=(--no-project)
    python3 scripts/check_record.py write --exit-code "$code" ${flag[@]+"${flag[@]}"} \
      ${steps[@]+"${steps[@]}"} || echo "Warning: could not write the check record." >&2
  else
    echo "Warning: python3 not found, so no check record was written." >&2
  fi
  exit "$code"
}
trap record EXIT

# The template's own guardrail scripts (changelog, PR evidence, check record).
if has python3 && [ -d scripts/tests ]; then
  step python3 -m unittest discover -s scripts/tests
fi
ran=0 # from here, only the project's own steps count as "a project was found"

# Python (uv)
if [ -f pyproject.toml ]; then
  if has uv; then r="uv run"; else r=""; fi
  step $r ruff format --check .
  step $r ruff check .
  if grep -q mypy pyproject.toml 2>/dev/null; then step $r mypy .; fi
  step $r pytest -q
fi

# JavaScript / TypeScript (npm scripts, when defined)
if [ -f package.json ]; then
  for s in format:check lint typecheck test; do
    if node -e "process.exit(require('./package.json').scripts?.['$s'] ? 0 : 1)" 2>/dev/null; then
      if [ "$s" = test ]; then step npm test --silent; else step npm run --silent "$s"; fi
    fi
  done
fi

# Go
if [ -f go.mod ]; then
  gofmt_check() {
    local unformatted
    # `step` calls this on the left of ||, where set -e is off, so check gofmt's exit code by hand.
    unformatted=$(gofmt -l .) || return $?
    [ -z "$unformatted" ] || { echo "Not formatted:"; echo "$unformatted"; return 1; }
  }
  step gofmt_check
  step go vet ./...
  step go test ./...
fi

# Rust
if [ -f Cargo.toml ]; then
  step cargo fmt --check
  step cargo clippy --all-targets -- -D warnings
  step cargo test
fi

# Java / Kotlin (Gradle wrapper)
if [ -x gradlew ]; then step ./gradlew check; fi

# C# / .NET
if ls ./*.sln >/dev/null 2>&1 || ls ./*.csproj >/dev/null 2>&1; then
  step dotnet format --verify-no-changes
  step dotnet test
fi

if [ "$ran" -eq 0 ]; then
  echo "No project detected yet. Run the bootstrap skill (or edit scripts/check.sh)."
  no_project=1
  exit 1
fi
echo; echo "All checks passed."
