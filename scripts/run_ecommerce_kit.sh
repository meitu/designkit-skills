#!/usr/bin/env bash
# 电商套图 webapi 执行入口
#   鉴权：DESIGNKIT_OPENCLAW_AK（同 run_command.sh）
#   可选：DESIGNKIT_OPENCLAW_AK_URL（获取 AK 的页面，默认 https://www.designkit.cn/openclaw，用于错误提示）
#   可选：DESIGNKIT_WEBAPI_BASE（覆盖 WebAPI 根域名，默认 https://openclaw-designkit-api.meitu.com；不带 /v1，具体 path 跟随各接口定义）
# 用法:
#   bash run_ecommerce_kit.sh style_create --input-json '{"image":"...","product_info":"...","platform":"amazon","market":"US"}'
#   bash run_ecommerce_kit.sh style_poll --input-json '{"task_id":"..."}'
#   bash run_ecommerce_kit.sh render_submit --input-json '{"image":"...","brand_style":{...},...}'
#   bash run_ecommerce_kit.sh render_poll --input-json '{"batch_id":"..."}'
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$SCRIPT_DIR/ecommerce_product_kit.py" "$@"
