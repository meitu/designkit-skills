#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:-18126}"
LOG_FILE="$(mktemp)"
OUT_FILE="$(mktemp)"

cleanup() {
  rm -f "$LOG_FILE" "$OUT_FILE"
  if [[ -n "${SERVER_PID:-}" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$ROOT_DIR" >"$LOG_FILE" 2>&1 &
SERVER_PID=$!
sleep 1

npx -y skills add "http://127.0.0.1:${PORT}" --list --full-depth >"$OUT_FILE"
grep -q "Found 7 skills" "$OUT_FILE"
grep -q "designkit-skills" "$OUT_FILE"
grep -q "designkit-edit-tools" "$OUT_FILE"

echo "PASS: well-known URL smoke test"
