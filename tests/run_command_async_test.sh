#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

FAKE_BIN="$TMP_DIR/bin"
mkdir -p "$FAKE_BIN"

cat >"$FAKE_BIN/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

STATE_FILE="${FAKE_CURL_STATE_FILE:?}"
ARGS="$*"

if [[ "$ARGS" == *"/openclaw/sod_2c_async"* ]]; then
  printf '%s\n200' '{"code":0,"message":"success","data":{"msg_id":"msg-sod-1"}}'
  exit 0
fi

if [[ "$ARGS" == *"/openclaw/image_restoration_async"* ]]; then
  printf '%s\n200' '{"code":0,"message":"success","data":{"msg_id":"msg-ir-1"}}'
  exit 0
fi

if [[ "$ARGS" == *"/openclaw/mtlab/query"* ]]; then
  COUNT=0
  if [[ -f "$STATE_FILE" ]]; then
    COUNT="$(cat "$STATE_FILE")"
  fi
  COUNT=$((COUNT + 1))
  echo "$COUNT" >"$STATE_FILE"

  if (( COUNT == 1 )); then
    printf '%s\n200' '{"code":29901,"message":"NOT_RESULT"}'
  else
    printf '%s\n200' '{"code":0,"message":"success","data":{"msg_id":"done-msg","media_info_list":[{"media_data":"https://cdn.example.com/out.png"}]}}'
  fi
  exit 0
fi

printf '%s\n404' '{"code":11001,"message":"unknown path"}'
EOF
chmod +x "$FAKE_BIN/curl"

assert_action() {
  local action="$1"
  local expected_msg_id="$2"
  local state_file="$TMP_DIR/state-$action.txt"
  : >"$state_file"

  local output
  if ! output="$(
    PATH="$FAKE_BIN:$PATH" \
      FAKE_CURL_STATE_FILE="$state_file" \
      DESIGNKIT_OPENCLAW_AK="test-ak" \
      OPENCLAW_REQUEST_LOG=0 \
      OPENCLAW_ASYNC_MAX_WAIT_SEC=1 \
      OPENCLAW_ASYNC_INTERVAL_SEC=0.01 \
      bash "$ROOT_DIR/scripts/run_command.sh" "$action" --input-json '{"image":"https://example.com/input.jpg"}'
  )"; then
    echo "[FAIL] $action should succeed, but command failed"
    exit 1
  fi

  python3 - "$output" "$action" "$expected_msg_id" <<'PY'
import json
import sys

raw, action, expected_msg_id = sys.argv[1], sys.argv[2], sys.argv[3]
data = json.loads(raw)

assert data.get("ok") is True, f"ok should be true: {data}"
assert data.get("command") == action, f"unexpected command: {data.get('command')}"
assert data.get("msg_id") == expected_msg_id, f"unexpected msg_id: {data.get('msg_id')}"
urls = data.get("media_urls") or []
assert urls == ["https://cdn.example.com/out.png"], f"unexpected media_urls: {urls}"
print("ok")
PY
}

assert_action "sod" "msg-sod-1"
assert_action "image_restoration" "msg-ir-1"

echo "[PASS] run_command async flow tests passed"
