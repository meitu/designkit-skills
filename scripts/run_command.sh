#!/usr/bin/env bash
set -euo pipefail

# DesignKit OpenClaw 统一执行器
# 用法: run_command.sh <action> --input-json '<json>'
# 从 api/commands.json 读取 API 定义，自动构造请求体并调用

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMMANDS_FILE="$PROJECT_ROOT/api/commands.json"

AK="${DESIGNKIT_OPENCLAW_AK:-}"
# 引导用户获取/核对 AK 的页面（Skill 与错误提示中与此一致）
DESIGNKIT_OPENCLAW_AK_URL="${DESIGNKIT_OPENCLAW_AK_URL:-https://www.designkit.cn/openClaw}"
API_BASE="${OPENCLAW_API_BASE:-https://openclaw-designkit-api.meitu.com}"
DESIGNKIT_WEBAPI_BASE="${DESIGNKIT_WEBAPI_BASE:-}"
DEBUG="${OPENCLAW_DEBUG:-0}"
# 测试阶段默认开启：所有对外 HTTP 请求/响应摘要打到 stderr；正式环境可设 OPENCLAW_REQUEST_LOG=0
REQUEST_LOG="${OPENCLAW_REQUEST_LOG:-1}"
ASYNC_MAX_WAIT_SEC="${OPENCLAW_ASYNC_MAX_WAIT_SEC:-180}"
ASYNC_INTERVAL_SEC="${OPENCLAW_ASYNC_INTERVAL_SEC:-2}"
ASYNC_QUERY_ENDPOINT_DEFAULT="${OPENCLAW_ASYNC_QUERY_ENDPOINT:-/openclaw/mtlab/query}"

normalize_api_base_for_openclaw() {
  local base="${1:-}"
  local endpoint="${2:-}"
  local query_endpoint="${3:-}"
  local normalized="${base%/}"

  if [[ "$endpoint" == /openclaw/* || "$query_endpoint" == /openclaw/* ]]; then
    normalized="${normalized%/v1}"
  fi

  echo "$normalized"
}

normalize_webapi_base_for_maat() {
  local base="${1:-}"
  local normalized no_v1_suffix
  if [ -z "$base" ]; then
    base="$API_BASE"
  fi
  normalized="${base%/}"
  no_v1_suffix="${normalized%/v1}"
  no_v1_suffix="${no_v1_suffix%/v1/}"
  echo "${no_v1_suffix%/}"
}

# ---------- 输出辅助 ----------
json_output() {
  echo "$1"
}

json_error() {
  local error_type="${1:-UNKNOWN_ERROR}"
  local message="${2:-请求失败}"
  local hint="${3:-请稍后重试}"
  echo "{\"ok\":false,\"error_type\":\"${error_type}\",\"message\":\"${message}\",\"user_hint\":\"${hint}\"}"
}

debug_log() {
  if [ "$DEBUG" = "1" ]; then
    echo "[DEBUG] $*" >&2
  fi
}

request_log() {
  if [ "$REQUEST_LOG" != "0" ]; then
    echo "[REQUEST] $*" >&2
  fi
}

# 响应以 JSON 格式化输出到 stderr（与 [REQUEST] 同通道）；超长截断后尽量解析
REQUEST_LOG_BODY_MAX="${OPENCLAW_REQUEST_LOG_BODY_MAX:-20000}"
request_log_response_json() {
  local label="${1:-response_body}"
  local http_code="${2:-}"
  if [ "$REQUEST_LOG" = "0" ]; then
    cat >/dev/null 2>&1 || true
    return 0
  fi
  python3 -c "
import sys, json
label = sys.argv[1]
max_len = int(sys.argv[2])
hc_raw = sys.argv[3] if len(sys.argv) > 3 else ''
try:
    http_code = int(hc_raw) if str(hc_raw).strip() else None
except ValueError:
    http_code = None
s = sys.stdin.read()
if len(s) > max_len:
    s = s[:max_len] + '...(truncated)'
try:
    body = json.loads(s)
    if http_code is not None:
        env = {'http_code': http_code, 'body': body}
    else:
        env = body
except json.JSONDecodeError:
    if http_code is not None:
        env = {'http_code': http_code, '_raw': s}
    else:
        env = {'_raw': s}
pretty = json.dumps(env, ensure_ascii=False, indent=2)
print('[REQUEST] ' + label + ' (JSON):', file=sys.stderr)
print(pretty, file=sys.stderr)
" "$label" "${REQUEST_LOG_BODY_MAX}" "${http_code}"
}

# 将 OpenClaw 请求以可复制 curl 单行打印（header 含完整 X-Openclaw-AK，注意勿泄露日志）
request_log_openclaw_curl() {
  local url="$1"
  if [ "$REQUEST_LOG" = "0" ]; then
    cat >/dev/null 2>&1 || true
    return 0
  fi
  python3 -c "
import os, sys, shlex
url = sys.argv[1]
body = sys.stdin.read()
ak = os.environ.get('DESIGNKIT_OPENCLAW_AK', '') or ''
parts = [
    'curl', '-s', '-w', '\\n%{http_code}', '-X', 'POST',
    '-H', 'Content-Type: application/json',
    '-H', 'X-Openclaw-AK: ' + ak,
    '-d', body,
    '--max-time', '120',
    url,
]
print('[REQUEST] ' + shlex.join(parts), file=sys.stderr)
" "$url"
}

# ---------- 参数解析 ----------
ACTION="${1:-}"
shift || true

INPUT_JSON=""
while [ $# -gt 0 ]; do
  case "$1" in
    --input-json)
      INPUT_JSON="${2:-}"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

# ---------- 前置检查 ----------
if [ -z "$AK" ]; then
  json_error "CREDENTIALS_MISSING" \
    "DESIGNKIT_OPENCLAW_AK 环境变量未设置" \
    "请先前往 ${DESIGNKIT_OPENCLAW_AK_URL} 获取 API Key，然后执行: export DESIGNKIT_OPENCLAW_AK=你的AK"
  exit 1
fi

if [ -z "$ACTION" ]; then
  json_error "PARAM_ERROR" "缺少操作类型参数" \
    "用法: run_command.sh <action> --input-json '{\"image\":\"...\"}'"
  exit 1
fi

if [ ! -f "$COMMANDS_FILE" ]; then
  json_error "RUNTIME_ERROR" "API 注册表文件不存在: ${COMMANDS_FILE}" "请检查项目完整性"
  exit 1
fi

# ---------- 从 commands.json 读取 API 定义 ----------
read_command_field() {
  local action="$1"
  local field="$2"
  python3 -c "
import sys, json
with open('${COMMANDS_FILE}') as f:
    cmds = json.load(f)
if '${action}' not in cmds:
    sys.exit(1)
val = cmds['${action}'].get('${field}', '')
if isinstance(val, (dict, list)):
    print(json.dumps(val))
else:
    print(val)
" 2>/dev/null
}

CMD_STATUS=$(read_command_field "$ACTION" "status" || echo "")
if [ -z "$CMD_STATUS" ]; then
  json_error "PARAM_ERROR" "未知操作类型: ${ACTION}" \
    "请使用 api/commands.json 中定义的操作类型"
  exit 1
fi

if [ "$CMD_STATUS" = "reserved" ]; then
  CMD_NAME=$(read_command_field "$ACTION" "name")
  json_error "NOT_IMPLEMENTED" \
    "${CMD_NAME}（${ACTION}）功能正在开发中" \
    "该能力尚未上线，请前往 https://www.designkit.cn/ 直接使用"
  exit 1
fi

ENDPOINT=$(read_command_field "$ACTION" "endpoint")
BODY_TEMPLATE=$(read_command_field "$ACTION" "body_template")
REQUIRED_FIELDS=$(read_command_field "$ACTION" "required")
RESPONSE_MODE=$(read_command_field "$ACTION" "response_mode")
QUERY_ENDPOINT=$(read_command_field "$ACTION" "query_endpoint")
if [ -z "$QUERY_ENDPOINT" ]; then
  QUERY_ENDPOINT="$ASYNC_QUERY_ENDPOINT_DEFAULT"
fi

API_BASE_NORMALIZED="$(normalize_api_base_for_openclaw "$API_BASE" "$ENDPOINT" "$QUERY_ENDPOINT")"

debug_log "Action: ${ACTION}, Endpoint: ${ENDPOINT}"

# ---------- 解析输入参数 ----------
if [ -z "$INPUT_JSON" ]; then
  json_error "PARAM_ERROR" "缺少 --input-json 参数" \
    "用法: run_command.sh ${ACTION} --input-json '{\"image\":\"图片路径或URL\"}'"
  exit 1
fi

IMAGE_INPUT=$(python3 -c "
import sys, json
try:
    d = json.loads('''${INPUT_JSON}''')
    print(d.get('image', ''))
except:
    print('')
" 2>/dev/null)

if [ -z "$IMAGE_INPUT" ]; then
  ASK_MSG=$(python3 -c "
import json
with open('${COMMANDS_FILE}') as f:
    cmds = json.load(f)
ask = cmds.get('${ACTION}', {}).get('ask_if_missing', {})
print(ask.get('image', '请提供图片'))
" 2>/dev/null)
  json_error "PARAM_ERROR" "缺少必填参数: image" "$ASK_MSG"
  exit 1
fi

# ---------- 推断文件后缀 & MIME ----------
get_suffix() {
  local ext
  ext=$(echo "$1" | sed 's/.*\.//' | tr '[:upper:]' '[:lower:]')
  case "$ext" in
    jpg|jpeg) echo "jpeg" ;;
    png) echo "png" ;;
    webp) echo "webp" ;;
    gif) echo "gif" ;;
    *) echo "jpeg" ;;
  esac
}

get_mime() {
  case "$1" in
    jpeg) echo "image/jpeg" ;;
    png) echo "image/png" ;;
    webp) echo "image/webp" ;;
    gif) echo "image/gif" ;;
    *) echo "image/jpeg" ;;
  esac
}

# ---------- 上传本地图片 → 返回 CDN URL ----------
upload_image() {
  local FILE_PATH="$1"

  if [ ! -f "$FILE_PATH" ]; then
    json_error "PARAM_ERROR" "文件不存在: ${FILE_PATH}" "请检查文件路径是否正确"
    exit 1
  fi

  local SUFFIX MIME FNAME
  SUFFIX=$(get_suffix "$FILE_PATH")
  MIME=$(get_mime "$SUFFIX")
  FNAME=$(basename "$FILE_PATH")

  debug_log "上传文件: ${FILE_PATH} (suffix=${SUFFIX}, mime=${MIME})"

  local WEBAPI_BASE_MAAT GETSIGN_URL GETSIGN_RESP GETSIGN_HTTP_CODE GETSIGN_BODY
  local GETSIGN_CODE GETSIGN_MESSAGE POLICY_SIGNED_URL
  WEBAPI_BASE_MAAT=$(normalize_webapi_base_for_maat "$DESIGNKIT_WEBAPI_BASE")
  GETSIGN_URL="${WEBAPI_BASE_MAAT}/maat/getsign?type=openclaw"

  if [ "$REQUEST_LOG" != "0" ]; then
    python3 -c "
import shlex, sys
url = sys.argv[1]
ak = sys.argv[2]
parts = [
    'curl', '-s', '--max-time', '30', '-X', 'GET',
    '-H', 'Accept: application/json, text/plain, */*',
    '-H', 'X-Openclaw-AK: ' + ak,
    '-H', 'Origin: https://www.designkit.cn',
    '-H', 'Referer: https://www.designkit.cn/editor/',
    url,
]
print('[REQUEST] ' + shlex.join(parts), file=__import__('sys').stderr)
" "$GETSIGN_URL" "$AK"
  fi
  GETSIGN_RESP=$(curl -s -w "\n%{http_code}" -X GET "$GETSIGN_URL" \
    -H "Accept: application/json, text/plain, */*" \
    -H "X-Openclaw-AK: ${AK}" \
    -H "Origin: https://www.designkit.cn" \
    -H "Referer: https://www.designkit.cn/editor/" \
    --max-time 30)
  GETSIGN_HTTP_CODE=$(echo "$GETSIGN_RESP" | tail -n1)
  GETSIGN_BODY=$(echo "$GETSIGN_RESP" | sed '$d')
  printf '%s' "$GETSIGN_BODY" | request_log_response_json maat_getsign_response_body "$GETSIGN_HTTP_CODE"

  if [ "$GETSIGN_HTTP_CODE" -lt 200 ] || [ "$GETSIGN_HTTP_CODE" -ge 300 ]; then
    request_log "maat getsign failed with http=${GETSIGN_HTTP_CODE}"
    json_error "UPLOAD_ERROR" "获取上传签名失败" "请检查网络连接或 API Key 后重试"
    exit 1
  fi

  GETSIGN_CODE=$(echo "$GETSIGN_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('code',''))" 2>/dev/null)
  GETSIGN_MESSAGE=$(echo "$GETSIGN_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message',''))" 2>/dev/null)
  POLICY_SIGNED_URL=$(echo "$GETSIGN_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print((d.get('data') or {}).get('upload_url',''))" 2>/dev/null)

  if [ "$GETSIGN_CODE" != "0" ] || [ -z "$POLICY_SIGNED_URL" ]; then
    request_log "maat getsign rejected: code=${GETSIGN_CODE}, message=${GETSIGN_MESSAGE}"
    json_error "UPLOAD_ERROR" "获取上传签名失败" "请检查网络连接或 API Key 后重试"
    exit 1
  fi

  if [ "$REQUEST_LOG" != "0" ]; then
    python3 -c "
import shlex, sys
url = sys.argv[1]
parts = [
    'curl', '-s', '--max-time', '30', '-X', 'GET',
    '-H', 'Origin: https://www.designkit.cn',
    '-H', 'Referer: https://www.designkit.cn/editor/',
    url,
]
print('[REQUEST] ' + shlex.join(parts), file=__import__('sys').stderr)
" "$POLICY_SIGNED_URL"
  fi
  local POLICY_RAW POLICY_HTTP_CODE POLICY_RESP
  POLICY_RAW=$(curl -s -w "\n%{http_code}" "$POLICY_SIGNED_URL" \
    -H "Origin: https://www.designkit.cn" \
    -H "Referer: https://www.designkit.cn/editor/" \
    --max-time 30)
  POLICY_HTTP_CODE=$(echo "$POLICY_RAW" | tail -n1)
  POLICY_RESP=$(echo "$POLICY_RAW" | sed '$d')

  printf '%s' "$POLICY_RESP" | request_log_response_json policy_response_body "$POLICY_HTTP_CODE"
  if [ "$POLICY_HTTP_CODE" -lt 200 ] || [ "$POLICY_HTTP_CODE" -ge 300 ]; then
    request_log "policy request failed with http=${POLICY_HTTP_CODE}"
    json_error "UPLOAD_ERROR" "获取上传策略失败" "请检查网络连接后重试"
    exit 1
  fi

  local PROVIDER
  PROVIDER=$(echo "$POLICY_RESP" | python3 -c "import sys,json; arr=json.load(sys.stdin); print(arr[0]['order'][0])" 2>/dev/null)
  if [ -z "$PROVIDER" ]; then
    request_log "policy response: parse failed or empty body"
    json_error "UPLOAD_ERROR" "获取上传策略失败" "请检查网络连接后重试"
    exit 1
  fi

  local UP_TOKEN UP_KEY UP_URL UP_DATA
  UP_TOKEN=$(echo "$POLICY_RESP" | python3 -c "import sys,json; arr=json.load(sys.stdin); print(arr[0]['${PROVIDER}']['token'])")
  UP_KEY=$(echo "$POLICY_RESP" | python3 -c "import sys,json; arr=json.load(sys.stdin); print(arr[0]['${PROVIDER}']['key'])")
  UP_URL=$(echo "$POLICY_RESP" | python3 -c "import sys,json; arr=json.load(sys.stdin); print(arr[0]['${PROVIDER}']['url'])")
  UP_DATA=$(echo "$POLICY_RESP" | python3 -c "import sys,json; arr=json.load(sys.stdin); print(arr[0]['${PROVIDER}']['data'])")

  debug_log "上传策略: provider=${PROVIDER}, url=${UP_URL}, key=${UP_KEY}"
  if [ "$REQUEST_LOG" != "0" ]; then
    python3 -c "
import shlex, sys
up, fp, fn, mi = sys.argv[1:5]
parts = [
    'curl', '-s', '--max-time', '120', '-X', 'POST',
    '-H', 'Origin: https://www.designkit.cn',
    '-H', 'Referer: https://www.designkit.cn/editor/',
    '-F', 'token=<redacted>',
    '-F', 'key=<redacted>',
    '-F', 'fname=' + fn,
    '-F', 'file=@' + fp + ';type=' + mi,
    up,
]
print('[REQUEST] ' + shlex.join(parts), file=__import__('sys').stderr)
" "${UP_URL}/" "$FILE_PATH" "$FNAME" "$MIME"
  fi

  local UPLOAD_RESP
  UPLOAD_RESP=$(curl -s -X POST "${UP_URL}/" \
    -H "Origin: https://www.designkit.cn" \
    -H "Referer: https://www.designkit.cn/editor/" \
    -F "token=${UP_TOKEN}" \
    -F "key=${UP_KEY}" \
    -F "fname=${FNAME}" \
    -F "file=@${FILE_PATH};type=${MIME}" \
    --max-time 120)

  printf '%s' "$UPLOAD_RESP" | request_log_response_json upload_response_body ""

  local CDN_URL
  CDN_URL=$(echo "$UPLOAD_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data'])" 2>/dev/null)
  if [ -z "$CDN_URL" ] || [ "$CDN_URL" = "None" ]; then
    CDN_URL="$UP_DATA"
  fi

  if [ -z "$CDN_URL" ] || [ "$CDN_URL" = "None" ]; then
    request_log "upload response: no CDN URL in body"
    json_error "UPLOAD_ERROR" "上传失败，无法获取图片 URL" "请换一张图片或检查网络后重试"
    exit 1
  fi

  request_log "upload ok, cdn_url=${CDN_URL}"
  debug_log "上传完成, CDN URL: ${CDN_URL}"
  echo "$CDN_URL"
}

# ---------- 确定图片 URL ----------
IMAGE_URL=""
if echo "$IMAGE_INPUT" | grep -qE '^https?://'; then
  IMAGE_URL="$IMAGE_INPUT"
else
  IMAGE_URL=$(upload_image "$IMAGE_INPUT")
fi

# ---------- 用模板构造请求体 ----------
BODY=$(python3 -c "
import json, sys

with open('${COMMANDS_FILE}') as f:
    cmds = json.load(f)

template = cmds['${ACTION}']['body_template']
body_str = json.dumps(template)
body_str = body_str.replace('{{image}}', '${IMAGE_URL}')
print(body_str)
" 2>/dev/null)

if [ -z "$BODY" ]; then
  json_error "RUNTIME_ERROR" "构造请求体失败" "请检查 api/commands.json 中的 body_template 配置"
  exit 1
fi

debug_log "请求: POST ${API_BASE_NORMALIZED}${ENDPOINT}"
debug_log "Body: ${BODY}"
printf '%s' "$BODY" | request_log_openclaw_curl "${API_BASE_NORMALIZED}${ENDPOINT}"

emit_http_error() {
  local action_name="$1"
  local http_code="$2"
  local raw_body="$3"
  printf '%s' "$raw_body" | python3 -c "
import json, sys
action = sys.argv[1]
http_code = int(sys.argv[2])
raw = sys.stdin.read()[:2000]
error_type = 'UNKNOWN_ERROR'
hint = '请稍后重试'

if http_code in (401, 403):
    error_type = 'AUTH_ERROR'
    hint = '鉴权失败，请前往 ${DESIGNKIT_OPENCLAW_AK_URL} 检查 AK 是否有效'
elif http_code == 429:
    error_type = 'QPS_LIMIT'
    hint = '请求频率超限，请稍后重试'
elif http_code >= 500:
    error_type = 'TEMPORARY_UNAVAILABLE'
    hint = '服务暂时不可用，请稍后重试'
elif http_code == 402:
    error_type = 'ORDER_REQUIRED'
    hint = '美豆不足，请前往 https://www.designkit.cn/ 获取美豆'

try:
    resp = json.loads(raw)
    msg = resp.get('message', f'HTTP {http_code}')
except json.JSONDecodeError:
    msg = f'HTTP {http_code}'

out = {
    'ok': False,
    'command': action,
    'error_type': error_type,
    'http_code': http_code,
    'message': msg,
    'user_hint': hint,
}
print(json.dumps(out, ensure_ascii=False))
" "$action_name" "$http_code"
}

extract_resp_code() {
  printf '%s' "$1" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except json.JSONDecodeError:
    print('')
    raise SystemExit(0)
print(d.get('code', ''))
"
}

extract_resp_message() {
  printf '%s' "$1" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except json.JSONDecodeError:
    print('')
    raise SystemExit(0)
print(d.get('message', ''))
"
}

extract_resp_msg_id() {
  printf '%s' "$1" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except json.JSONDecodeError:
    print('')
    raise SystemExit(0)

msg_id = ''
data = d.get('data')
if isinstance(data, dict):
    for key in ('msg_id', 'task_id', 'id'):
        val = data.get(key)
        if isinstance(val, str) and val:
            msg_id = val
            break
if not msg_id:
    for key in ('msg_id', 'task_id', 'id'):
        val = d.get(key)
        if isinstance(val, str) and val:
            msg_id = val
            break
print(msg_id)
"
}

extract_media_urls_json() {
  printf '%s' "$1" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except json.JSONDecodeError:
    print('[]')
    raise SystemExit(0)

urls = []
data = d.get('data') if isinstance(d.get('data'), dict) else {}
for item in data.get('media_info_list') or []:
    if isinstance(item, dict):
        url = item.get('media_data')
        if isinstance(url, str) and url:
            urls.append(url)
print(json.dumps(urls, ensure_ascii=False))
"
}

emit_api_error_from_body() {
  local action_name="$1"
  local raw_body="$2"
  printf '%s' "$raw_body" | python3 -c "
import json, sys
action = sys.argv[1]
raw = sys.stdin.read()
try:
    resp = json.loads(raw)
except json.JSONDecodeError:
    resp = {'_raw': raw}

msg = resp.get('message', '处理失败') if isinstance(resp, dict) else '处理失败'
code = resp.get('code', -1) if isinstance(resp, dict) else -1
out = {
    'ok': False,
    'command': action,
    'error_type': 'API_ERROR',
    'error_code': code,
    'message': msg,
    'user_hint': msg,
    'result': resp,
}
print(json.dumps(out, ensure_ascii=False))
" "$action_name"
}

# ---------- 调用 OpenClaw API（提交任务） ----------
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE_NORMALIZED}${ENDPOINT}" \
  -H "Content-Type: application/json" \
  -H "X-Openclaw-AK: ${AK}" \
  -d "$BODY" \
  --max-time 120)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY_RESPONSE=$(echo "$RESPONSE" | sed '$d')

printf '%s' "$BODY_RESPONSE" | request_log_response_json openclaw_response_body "$HTTP_CODE"
debug_log "响应: HTTP ${HTTP_CODE}"
debug_log "Body: ${BODY_RESPONSE}"

if [ "$HTTP_CODE" -lt 200 ] || [ "$HTTP_CODE" -ge 300 ]; then
  emit_http_error "$ACTION" "$HTTP_CODE" "$BODY_RESPONSE"
  exit 1
fi

RESP_CODE=$(extract_resp_code "$BODY_RESPONSE")
if [ "$RESP_CODE" != "0" ]; then
  emit_api_error_from_body "$ACTION" "$BODY_RESPONSE"
  exit 0
fi

# ---------- 异步模式：提交后轮询 ----------
if [ "$RESPONSE_MODE" = "async" ]; then
  MSG_ID=$(extract_resp_msg_id "$BODY_RESPONSE")
  if [ -z "$MSG_ID" ]; then
    json_error "API_ERROR" "异步任务提交成功但缺少 msg_id" "请稍后重试或联系管理员"
    exit 1
  fi

  MAX_POLLS=$(python3 -c "
import math, sys
try:
    max_wait = float(sys.argv[1])
    interval = float(sys.argv[2])
except Exception:
    print(90)
    raise SystemExit(0)
if max_wait <= 0:
    max_wait = 1
if interval <= 0:
    interval = 1
print(max(1, int(math.ceil(max_wait / interval))))
" "$ASYNC_MAX_WAIT_SEC" "$ASYNC_INTERVAL_SEC" 2>/dev/null)

  if [ -z "$MAX_POLLS" ]; then
    MAX_POLLS=90
  fi

  QUERY_URL_BASE="${API_BASE_NORMALIZED}${QUERY_ENDPOINT}"
  for ((i=1; i<=MAX_POLLS; i++)); do
    QUERY_URL="${QUERY_URL_BASE}?msg_id=${MSG_ID}"
    request_log "poll ${i}/${MAX_POLLS}: ${QUERY_URL}"

    QUERY_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${QUERY_URL}" \
      -H "X-Openclaw-AK: ${AK}" \
      --max-time 120)

    QUERY_HTTP_CODE=$(echo "$QUERY_RESPONSE" | tail -n1)
    QUERY_BODY_RESPONSE=$(echo "$QUERY_RESPONSE" | sed '$d')
    printf '%s' "$QUERY_BODY_RESPONSE" | request_log_response_json openclaw_query_response_body "$QUERY_HTTP_CODE"

    if [ "$QUERY_HTTP_CODE" -lt 200 ] || [ "$QUERY_HTTP_CODE" -ge 300 ]; then
      emit_http_error "$ACTION" "$QUERY_HTTP_CODE" "$QUERY_BODY_RESPONSE"
      exit 1
    fi

    QUERY_CODE=$(extract_resp_code "$QUERY_BODY_RESPONSE")
    QUERY_MSG=$(extract_resp_message "$QUERY_BODY_RESPONSE")
    QUERY_MSG_UPPER=$(echo "$QUERY_MSG" | tr '[:lower:]' '[:upper:]')

    if [ "$QUERY_CODE" = "0" ]; then
      MEDIA_URLS_JSON=$(extract_media_urls_json "$QUERY_BODY_RESPONSE")
      if [ "$MEDIA_URLS_JSON" != "[]" ]; then
        printf '%s' "$QUERY_BODY_RESPONSE" | python3 -c "
import json, sys
action = sys.argv[1]
msg_id = sys.argv[2]
media_urls = json.loads(sys.argv[3])
raw = sys.stdin.read()
try:
    resp = json.loads(raw)
except json.JSONDecodeError:
    resp = {'_raw': raw}
out = {
    'ok': True,
    'command': action,
    'msg_id': msg_id,
    'media_urls': media_urls,
    'result': resp,
}
print(json.dumps(out, ensure_ascii=False))
" "$ACTION" "$MSG_ID" "$MEDIA_URLS_JSON"
        exit 0
      fi
    elif [ "$QUERY_CODE" = "29901" ] || [ "$QUERY_MSG_UPPER" = "NOT_RESULT" ]; then
      :
    else
      emit_api_error_from_body "$ACTION" "$QUERY_BODY_RESPONSE"
      exit 0
    fi

    if [ "$i" -lt "$MAX_POLLS" ]; then
      sleep "$ASYNC_INTERVAL_SEC"
    fi
  done

  echo "{\"ok\":false,\"command\":\"${ACTION}\",\"error_type\":\"TEMPORARY_UNAVAILABLE\",\"message\":\"异步任务轮询超时\",\"user_hint\":\"在 ${ASYNC_MAX_WAIT_SEC}s 内未获取到处理结果，请稍后重试\",\"msg_id\":\"${MSG_ID}\"}"
  exit 0
fi

# ---------- 同步模式 ----------
MEDIA_URLS_JSON=$(extract_media_urls_json "$BODY_RESPONSE")
MSG_ID=$(extract_resp_msg_id "$BODY_RESPONSE")
printf '%s' "$BODY_RESPONSE" | python3 -c "
import json, sys
action = sys.argv[1]
msg_id = sys.argv[2]
media_urls = json.loads(sys.argv[3])
raw = sys.stdin.read()
try:
    resp = json.loads(raw)
except json.JSONDecodeError:
    resp = {'_raw': raw}
out = {
    'ok': True,
    'command': action,
    'media_urls': media_urls,
    'result': resp,
}
if msg_id:
    out['msg_id'] = msg_id
print(json.dumps(out, ensure_ascii=False))
" "$ACTION" "$MSG_ID" "$MEDIA_URLS_JSON"
