#!/usr/bin/env python3
"""
DesignKit 电商套图 — webapi 基址默认正式环境，鉴权与 run_command.sh 一致。

环境变量：
- DESIGNKIT_OPENCLAW_AK：请求头 X-Openclaw-AK（必填）
- DESIGNKIT_OPENCLAW_AK_URL：获取/核对 AK 的页面地址，默认 https://www.designkit.cn/openClaw（用于错误提示文案）
- DESIGNKIT_WEBAPI_BASE：仅域名基址（不含版本前缀）；默认 https://openclaw-designkit-api.meitu.com
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
import time
import uuid
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

# 可通过 DESIGNKIT_WEBAPI_BASE 覆盖；仅域名，不自动拼版本前缀
_webapi_base_raw = os.environ.get(
    "DESIGNKIT_WEBAPI_BASE",
    "https://openclaw-designkit-api.meitu.com",
).rstrip("/")
WEBAPI_BASE = re.sub(r"/v1/?$", "", _webapi_base_raw)

DEFAULT_OPENCLAW_AK_URL = "https://www.designkit.cn/openClaw"


def _openclaw_ak_url() -> str:
    return os.environ.get("DESIGNKIT_OPENCLAW_AK_URL", DEFAULT_OPENCLAW_AK_URL).strip() or DEFAULT_OPENCLAW_AK_URL


def _request_log_enabled() -> bool:
    return os.environ.get("OPENCLAW_REQUEST_LOG", "1") != "0"


def _request_log(message: str) -> None:
    if _request_log_enabled():
        print(f"[REQUEST] {message}", file=sys.stderr)


def _request_log_as_curl(
    method: str,
    url: str,
    headers: Dict[str, str],
    data: Optional[bytes] = None,
) -> None:
    if not _request_log_enabled():
        return
    parts: List[str] = ["curl", "-s", "--max-time", "120"]
    m = method.upper()
    if m not in ("GET", "HEAD"):
        parts.extend(["-X", m])
    for k, v in headers.items():
        parts.extend(["-H", f"{k}: {v}"])
    if data:
        parts.extend(["-d", data.decode("utf-8", errors="replace")])
    parts.append(url)
    print("[REQUEST] " + shlex.join(parts), file=sys.stderr)


def _request_log_as_curl_multipart(
    upload_url: str,
    fname: str,
    file_path: str,
    mime: str,
) -> None:
    if not _request_log_enabled():
        return
    parts: List[str] = [
        "curl",
        "-s",
        "--max-time",
        "120",
        "-X",
        "POST",
        "-H",
        "Origin: https://www.designkit.cn",
        "-H",
        "Referer: https://www.designkit.cn/editor/",
        "-F",
        "token=<redacted>",
        "-F",
        "key=<redacted>",
        "-F",
        f"fname={fname}",
        "-F",
        f"file=@{file_path};type={mime}",
        upload_url,
    ]
    print("[REQUEST] " + shlex.join(parts), file=sys.stderr)


def _request_log_response_json(
    label: str,
    text: str,
    http_code: Optional[int] = None,
) -> None:
    if not _request_log_enabled():
        return
    try:
        max_len = int(os.environ.get("OPENCLAW_REQUEST_LOG_BODY_MAX", "20000"))
    except ValueError:
        max_len = 20000
    if len(text) > max_len:
        text = text[:max_len] + "...(truncated)"
    try:
        body_obj: Any = json.loads(text)
        if http_code is not None:
            envelope: Any = {"http_code": http_code, "body": body_obj}
        else:
            envelope = body_obj
    except json.JSONDecodeError:
        if http_code is not None:
            envelope = {"http_code": http_code, "_raw": text}
        else:
            envelope = {"_raw": text}
    pretty = json.dumps(envelope, ensure_ascii=False, indent=2)
    print(f"[REQUEST] {label} (JSON):", file=sys.stderr)
    print(pretty, file=sys.stderr)

# 爆款风格 prompt：仅替换 [输入] 三节；市场审美段默认美国，可用 market_zh 覆盖标题
STYLE_PROMPT_HEAD = (
    "\n你是电商视觉美术指导，精通品类视觉定调与风格一致性控制。\n\n[输入]\n"
    "- 产品: {product_info}\n- 平台: {platform}\n- 目标市场: {market}\n\n[市场审美参考]\n\n"
    "        [目标市场：{market_zh}]\n"
    "        - **视觉审美偏好**：高对比度、鲜艳有冲击力、商业感强、直接明快\n"
    "        - **环境风格参考**：现代美式、工业风、开放式空间、充足自然光\n"
    "        - **色彩调性**：明亮饱和、温暖色调、\"商业流行风\"\n"
    "    \n\n[平台风格]\n"
    "- **中国电商**（淘宝/京东/抖音/拼多多）：视觉冲击力强，可用彩色底/渐变底，强调吸睛转化\n"
    "- **海外电商**（amazon/temu/tiktok/Shopee/Aliexpress/Alibaba/OZON/shopify）：克制高级，强调真实感品质感\n\n[任务]\n"
    "为该产品生成 **4 套视觉差异明显** 的商业摄影风格方案，每套可复用于7张图集。\n\n[品类风格参考]\n"
    "根据产品品类灵活调整，不要机械套用：\n"
    "- 科技产品 → 均匀柔光，干净留白，中性色调\n"
    "- 游戏设备 → 侧光透射，暗色背景，冷峻力量感\n"
    "- 家居产品 → 自然暖光，柔和通透，生活气息\n"
    "- 运动装备 → 自然光，明快清晰，阳光活力\n"
    "- 服饰配件 → 柔和侧光，质感细腻，优雅克制\n"
    "- 美妆护肤 → 均匀柔光，干净透亮，精致感\n\n[核心规则]\n"
    "1. **仅限真实摄影风格**：严禁油画/水彩/动漫/素描等插画风格\n"
    "2. **globalStyleNote 格式**：\n"
    "   - 仅含光影+氛围关键词，15-25词\n"
    "   - ✅ 允许：\"自然暖光，45度柔和漫射光，柔和通透，生活气息\"\n"
    "   - ❌ 禁止：任何场景、物体、背景、道具描述\n"
    "3. **产品颜色真实**：禁止极端色温（<2700K或>6500K）和浓重滤镜\n"
    "4. **colorPalette 首位**：必须是产品固有色（如绿色沙发→绿色）\n"
    "5. **字体红线**：严禁细字体/书法体/手写体，禁止输出具体字体名\n"
    "6. **全局风格可复用性**：每套风格必须能作为基调应用到7张商品图中，仅需调整场景细节即可保持视觉语言统一\n"
    "7. **转化导向**：风格必须提升产品感知价值，建立买家信任\n\n[输出格式]\n"
    "直接输出纯JSON数组，中文输出。每个对象包含以下字段：\n\n"
    "| 字段 | 描述 | 示例 |\n"
    "|------|------|------|\n"
    "| name | 风格名称（2-4词，通俗易懂） | \"温馨居家\" \"简约专业\" |\n"
    "| reasoning | 选择理由（≤15词，口语化） | \"让沙发看起来更舒适温馨\" |\n"
    "| globalStyleNote | 光影+氛围关键词（15-25词） | \"自然暖光，45度柔和漫射光，柔和通透\" |\n"
    "| fontStyleDescription | 字体视觉特征描述 | \"粗壮无衬线体，中等字重，现代商业感\" |\n"
    "| colorPalette | 3个hex色值（产品色+背景色+强调色） | \"#2ECC71, #F8F9FA, #FF6B6B\" |\n"
    "| colorDescription | 颜色用途说明 | \"森林绿（产品原色），云雾白（背景），珊瑚红（强调）\" |\n"
    "| iconStyle | 图标风格描述 | \"粗线性极简风格\" |\n\n[输出前自检]\n"
    "- [ ] globalStyleNote 包含光影+氛围词，不包含场景/物体/背景描述，15-25词\n"
    "- [ ] 光影设置不会导致产品颜色失真\n"
    "- [ ] fontStyleDescription 是描述性语言，不包含具体字体名称\n"
    "- [ ] colorPalette 第一个颜色是产品固有色\n"
    "- [ ] 4 个风格方案视觉上有明显差异\n"
    "- [ ] name 和 reasoning 简洁易懂\n"
)

MARKET_ZH = {
    "US": "美国",
    "CN": "中国",
    "UK": "英国",
    "JP": "日本",
    "DE": "德国",
    "FR": "法国",
    "AU": "澳大利亚",
}


def _json_error(
    ok: bool,
    error_type: str,
    message: str,
    user_hint: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    out: Dict[str, Any] = {
        "ok": ok,
        "error_type": error_type,
        "message": message,
        "user_hint": user_hint,
    }
    if extra:
        out.update(extra)
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(1 if not ok else 0)


def _require_ak() -> str:
    ak = os.environ.get("DESIGNKIT_OPENCLAW_AK", "").strip()
    if not ak:
        _json_error(
            False,
            "CREDENTIALS_MISSING",
            "缺少 DESIGNKIT_OPENCLAW_AK",
            f"请先前往 {_openclaw_ak_url()} 获取 API Key，然后执行: export DESIGNKIT_OPENCLAW_AK=你的AK",
        )
    return ak


def _query_params() -> Dict[str, str]:
    return {
        "client_id": os.environ.get("DESIGNKIT_OPENCLAW_CLIENT_ID", "2288866677"),
        "client_language": os.environ.get("DESIGNKIT_CLIENT_LANGUAGE", "zh-Hans"),
        "channel": "",
        "country_code": os.environ.get("DESIGNKIT_COUNTRY_CODE", "CN"),
        "ts_random_id": str(uuid.uuid4()),
        "client_source": "pc",
        "client_timezone": os.environ.get("DESIGNKIT_CLIENT_TIMEZONE", "Asia/Shanghai"),
        "operate_source": "web",
    }


def _headers_json() -> Dict[str, str]:
    ak = _require_ak()
    return {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "Origin": "https://www.designkit.cn",
        "Referer": "https://www.designkit.cn/product-kit/?from=home",
        "X-Openclaw-AK": ak,
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }


def _headers_get() -> Dict[str, str]:
    h = _headers_json()
    del h["Content-Type"]
    return h


def _url(path: str, extra: Optional[Dict[str, str]] = None) -> str:
    from urllib.parse import urlencode

    q = _query_params()
    if extra:
        q = {**q, **extra}
    return f"{WEBAPI_BASE}{path}?{urlencode(q)}"


def _http_request(
    method: str,
    url: str,
    body: Optional[bytes] = None,
    json_mode: bool = True,
) -> Tuple[int, Any]:
    headers = _headers_json() if json_mode and body else _headers_get()
    if body and "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    _request_log_as_curl(method, url, headers, body)
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            code = resp.getcode() or 200
            _request_log_response_json("response_body", raw, code)
            try:
                return code, json.loads(raw)
            except json.JSONDecodeError:
                return code, {"_raw": raw}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        _request_log_response_json("response_body", raw, e.code)
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, {"_raw": raw, "_http_message": str(e)}


def _suffix_mime(path: str) -> Tuple[str, str]:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    if ext in ("jpg", "jpeg"):
        return "jpeg", "image/jpeg"
    if ext == "png":
        return "png", "image/png"
    if ext == "webp":
        return "webp", "image/webp"
    return "jpeg", "image/jpeg"


def upload_local_image(file_path: str) -> str:
    if not os.path.isfile(file_path):
        _json_error(False, "PARAM_ERROR", f"文件不存在: {file_path}", "请检查图片路径")

    _, mime = _suffix_mime(file_path)
    fname = os.path.basename(file_path)

    getsign_url = f"{WEBAPI_BASE}/maat/getsign?type=openclaw"
    getsign_code, getsign_resp = _http_request("GET", getsign_url, json_mode=False)
    if getsign_code < 200 or getsign_code >= 300 or not isinstance(getsign_resp, dict):
        _json_error(False, "UPLOAD_ERROR", "获取上传签名失败", "请检查网络连接或 API Key 后重试")
    if getsign_resp.get("code") != 0:
        _request_log(f"maat getsign rejected: {json.dumps(getsign_resp, ensure_ascii=False)}")
        _json_error(False, "UPLOAD_ERROR", "获取上传签名失败", "请检查网络连接或 API Key 后重试")

    policy_url_full = str((getsign_resp.get("data") or {}).get("upload_url") or "").strip()
    if not policy_url_full:
        _request_log(f"maat getsign missing upload_url: {json.dumps(getsign_resp, ensure_ascii=False)}")
        _json_error(False, "UPLOAD_ERROR", "获取上传签名失败", "请检查网络连接或 API Key 后重试")

    _request_log_as_curl(
        "GET",
        policy_url_full,
        {
            "Origin": "https://www.designkit.cn",
            "Referer": "https://www.designkit.cn/editor/",
        },
        None,
    )
    policy_req = urllib.request.Request(policy_url_full)
    policy_req.add_header("Origin", "https://www.designkit.cn")
    policy_req.add_header("Referer", "https://www.designkit.cn/editor/")
    try:
        with urllib.request.urlopen(policy_req, timeout=30) as resp:
            code = resp.getcode() or 200
            raw_policy = resp.read().decode()
            _request_log_response_json("policy_response_body", raw_policy, code)
            if code < 200 or code >= 300:
                _json_error(False, "UPLOAD_ERROR", "获取上传策略失败", "请检查网络连接后重试")
            arr = json.loads(raw_policy)
    except Exception as e:
        _json_error(False, "UPLOAD_ERROR", str(e), "获取上传策略失败，请检查网络")

    provider = arr[0]["order"][0]
    p = arr[0][provider]
    token, key, up_url, up_data = p["token"], p["key"], p["url"], p["data"]

    boundary = uuid.uuid4().hex.encode()
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    def part(name: str, value: str) -> bytes:
        return (
            b"--"
            + boundary
            + b'\r\nContent-Disposition: form-data; name="'
            + name.encode()
            + b'"\r\n\r\n'
            + value.encode()
            + b"\r\n"
        )

    post_body = (
        part("token", token)
        + part("key", key)
        + part("fname", fname)
        + b"--"
        + boundary
        + b'\r\nContent-Disposition: form-data; name="file"; filename="'
        + fname.encode()
        + b'"\r\nContent-Type: '
        + mime.encode()
        + b"\r\n\r\n"
        + file_bytes
        + b"\r\n--"
        + boundary
        + b"--\r\n"
    )

    upload_target = f"{up_url}/"
    _request_log_as_curl_multipart(upload_target, fname, file_path, mime)
    up_req = urllib.request.Request(upload_target, data=post_body, method="POST")
    up_req.add_header("Content-Type", f"multipart/form-data; boundary={boundary.decode()}")
    up_req.add_header("Origin", "https://www.designkit.cn")
    up_req.add_header("Referer", "https://www.designkit.cn/editor/")
    try:
        with urllib.request.urlopen(up_req, timeout=120) as resp:
            ucode = resp.getcode() or 200
            raw_up = resp.read().decode()
            _request_log_response_json("upload_response_body", raw_up, ucode)
            up_json = json.loads(raw_up)
    except Exception as e:
        _json_error(False, "UPLOAD_ERROR", str(e), "上传失败，请换图或稍后重试")

    cdn = up_json.get("data") or up_data
    if not cdn:
        _request_log("upload response: no CDN URL in body")
        _json_error(False, "UPLOAD_ERROR", "无 CDN URL", "上传响应异常")
    _request_log(f"upload ok, cdn_url={cdn}")
    return str(cdn)


def resolve_image_url(image: str) -> str:
    image = (image or "").strip()
    if not image:
        _json_error(False, "PARAM_ERROR", "缺少 image", "请提供商品图 URL 或本地路径")
    if re.match(r"^https?://", image, re.I):
        return image
    return upload_local_image(image)


def extract_task_id(resp: Any) -> Optional[str]:
    if not isinstance(resp, dict):
        return None
    for path in (
        ("data", "task_id"),
        ("data", "id"),
        ("task_id",),
        ("id",),
    ):
        cur: Any = resp
        for k in path:
            if isinstance(cur, dict):
                cur = cur.get(k)
            else:
                cur = None
                break
        if isinstance(cur, str) and cur:
            return cur
    return None


def k2_done(resp: Any) -> Tuple[bool, Optional[str]]:
    """返回 (是否已结束, 文本/结果串用于解析风格)."""
    if not isinstance(resp, dict):
        return False, None
    data = resp.get("data")
    if not isinstance(data, dict):
        return False, None
    st = data.get("status")
    st_str = str(st).lower() if st is not None else ""
    if st in (0, 1, "0", "1") or st_str in ("pending", "running", "processing", "queue", "queued"):
        return False, None
    # 在 data 的直属字段中查找文本结果
    for key in ("result", "content", "text", "output", "message", "answer"):
        v = data.get(key)
        if isinstance(v, str) and v.strip():
            return True, v
    # 在嵌套的 result 对象中查找文本字段（如 data.result.message）
    result_obj = data.get("result")
    if isinstance(result_obj, dict):
        for key in ("message", "content", "text", "output", "answer"):
            v = result_obj.get(key)
            if isinstance(v, str) and v.strip():
                return True, v
    # result 为 None 表示尚无结果产出，即使 status >= 2 也继续等待
    if result_obj is None:
        return False, None
    # result 非空但无可识别的文本字段，序列化整个 data 返回
    is_terminal = (isinstance(st, int) and st >= 2) or st_str in (
        "2", "3", "success", "complete", "done", "finished",
    )
    if is_terminal:
        return True, json.dumps(data, ensure_ascii=False)
    return False, None


def extract_batch_media(resp: Any) -> List[str]:
    urls: List[str] = []
    if not isinstance(resp, dict):
        return urls
    data = resp.get("data") or resp

    def collect(obj: Any) -> None:
        if isinstance(obj, str) and obj.startswith("http"):
            urls.append(obj)
        elif isinstance(obj, dict):
            for k in ("url", "media_url", "image_url", "src"):
                v = obj.get(k)
                if isinstance(v, str) and v.startswith("http"):
                    urls.append(v)
            for v in obj.values():
                collect(v)
        elif isinstance(obj, list):
            for v in obj:
                collect(v)

    collect(data)
    return list(dict.fromkeys(urls))


def cmd_style_create(inp: Dict[str, Any]) -> None:
    image = resolve_image_url(str(inp.get("image", "")))
    product_info = str(inp.get("product_info", inp.get("selling_points", ""))).strip() or "商品"
    platform = str(inp.get("platform", "amazon")).strip()
    market = str(inp.get("market", "US")).strip()
    market_zh = str(inp.get("market_zh", "") or MARKET_ZH.get(market.upper(), "美国"))
    api_engine = str(inp.get("api_engine", "doubao-seed-2.0-lite"))

    prompt = STYLE_PROMPT_HEAD.format(
        product_info=product_info,
        platform=platform,
        market=market,
        market_zh=market_zh,
    )
    body = json.dumps(
        {"api_engine": api_engine, "prompt": prompt, "images": image},
        ensure_ascii=False,
    ).encode()

    url = _url("/v1/mtlab/ai_text")
    code, resp = _http_request("POST", url, body)
    if code != 200:
        _json_error(
            False,
            "API_ERROR",
            f"HTTP {code}",
            f"创建风格任务失败，请前往 {_openclaw_ak_url()} 检查 DESIGNKIT_OPENCLAW_AK 是否有效",
            {"http_code": code, "result": resp},
        )

    task_id = extract_task_id(resp)
    out = {
        "ok": True,
        "command": "ecommerce_style_create",
        "task_id": task_id,
        "result": resp,
        "user_hint": "若 task_id 为空，请从 result 内自行查找任务 id 后轮询 k2_query",
    }
    print(json.dumps(out, ensure_ascii=False))


def cmd_style_poll(inp: Dict[str, Any]) -> None:
    task_id = str(inp.get("task_id", "")).strip()
    if not task_id:
        _json_error(False, "PARAM_ERROR", "缺少 task_id", "请先执行 style_create 或从创建响应取 task_id")

    max_wait = float(inp.get("max_wait_sec", 180))
    interval = float(inp.get("interval_sec", 2))
    deadline = time.time() + max_wait

    while time.time() < deadline:
        url = _url("/v1/mtlab/k2_query", {"task_id": task_id})
        code, resp = _http_request("GET", url)
        if code != 200:
            _json_error(
                False,
                "API_ERROR",
                f"HTTP {code}",
                "查询风格任务失败",
                {"http_code": code, "result": resp},
            )

        done, text = k2_done(resp)
        if done and text:
            styles: Any = None
            try:
                # 模型可能输出 ```json ... ```
                m = re.search(r"\[[\s\S]*\]", text)
                if m:
                    styles = json.loads(m.group(0))
            except json.JSONDecodeError:
                styles = None
            out = {
                "ok": True,
                "command": "ecommerce_style_poll",
                "done": True,
                "styles": styles,
                "styles_raw": text,
                "result": resp,
            }
            print(json.dumps(out, ensure_ascii=False))
            return

        time.sleep(interval)

    print(
        json.dumps(
            {
                "ok": False,
                "error_type": "TEMPORARY_UNAVAILABLE",
                "message": "轮询超时",
                "user_hint": f"在 {max_wait}s 内未完成，可增大 max_wait_sec 后重试",
                "task_id": task_id,
            },
            ensure_ascii=False,
        )
    )
    sys.exit(1)


def cmd_render_submit(inp: Dict[str, Any]) -> None:
    transfer_id = str(inp.get("transfer_id", "") or str(uuid.uuid4()).upper())
    image_urls = inp.get("image_urls")
    if not image_urls:
        one = inp.get("image")
        if one:
            image_urls = [resolve_image_url(str(one))]
    if not isinstance(image_urls, list) or not image_urls:
        _json_error(False, "PARAM_ERROR", "缺少 image_urls", "请传 image_urls 数组或单个 image")

    resolved = [resolve_image_url(str(u)) if not re.match(r"^https?://", str(u), re.I) else str(u) for u in image_urls]

    brand_style = inp.get("brand_style")
    if brand_style is not None and not isinstance(brand_style, dict):
        _json_error(False, "PARAM_ERROR", "brand_style 须为对象或留空", "请传入风格 JSON 或省略此字段由服务端自动选择")

    style_name = str(inp.get("style_name", (brand_style or {}).get("name", "")))
    product_info = str(inp.get("product_info", "")).strip() or "商品"
    aspect_ratio = str(inp.get("aspect_ratio", "1:1"))
    language = str(inp.get("language", "English"))
    platform = str(inp.get("platform", "amazon"))
    market = str(inp.get("market", "US"))
    is_pro = bool(inp.get("is_pro", True))

    burial = inp.get("burial_point")
    if burial is None:
        burial = {
            "first_func": "product_kit",
            "page_name": "commerce",
            "target_platform": platform,
            "target_market": market,
            "language": language,
            "proportion": aspect_ratio,
            "fileName": "openclaw",
            "productInfo": product_info,
            "core_point_type": "customize",
            "is_pro": is_pro,
        }
    burial_str = burial if isinstance(burial, str) else json.dumps(burial, ensure_ascii=False)

    body_obj = {
        "image_urls": resolved,
        "style_name": style_name,
        "product_info": product_info,
        "aspect_ratio": aspect_ratio,
        "language": language,
        "platform": platform,
        "market": market,
        "is_pro": is_pro,
        "burial_point": burial_str,
    }
    if brand_style is not None:
        body_obj["brand_style"] = brand_style
    body = json.dumps(body_obj, ensure_ascii=False).encode()
    url = _url("/v1/hackathon/ai_product/task_submit", {"transfer_id": transfer_id})
    code, resp = _http_request("POST", url, body)
    if code != 200:
        _json_error(
            False,
            "API_ERROR",
            f"HTTP {code}",
            "提交生图任务失败",
            {"http_code": code, "result": resp},
        )

    batch_id = None
    if isinstance(resp, dict):
        batch_id = (
            resp.get("data", {}).get("batch_id")
            if isinstance(resp.get("data"), dict)
            else None
        ) or resp.get("batch_id")

    out = {
        "ok": True,
        "command": "ecommerce_render_submit",
        "transfer_id": transfer_id,
        "batch_id": batch_id,
        "result": resp,
        "user_hint": "若 batch_id 为空，请从 result.data 查找后轮询 render_poll",
    }
    print(json.dumps(out, ensure_ascii=False))


def _check_render_items(resp: Any) -> Tuple[int, int, List[str], List[Dict[str, Any]]]:
    """解析渲染结果中子 item 的完成状态。
    返回 (total, done_count, res_img_urls, items_list)。
    """
    items_list: List[Dict[str, Any]] = []
    res_urls: List[str] = []
    if not isinstance(resp, dict):
        return 0, 0, res_urls, items_list
    data = resp.get("data", {})
    if not isinstance(data, dict):
        return 0, 0, res_urls, items_list
    items_map = data.get("items", {})
    if not isinstance(items_map, dict):
        return 0, 0, res_urls, items_list
    for batch_val in items_map.values():
        if not isinstance(batch_val, dict):
            continue
        sub_items = batch_val.get("items", [])
        if not isinstance(sub_items, list):
            continue
        for item in sub_items:
            if not isinstance(item, dict):
                continue
            items_list.append(item)
            res_img = (item.get("res_img") or "").strip()
            if res_img.startswith("http"):
                res_urls.append(res_img)
    return len(items_list), len(res_urls), res_urls, items_list


def cmd_render_poll(inp: Dict[str, Any]) -> None:
    batch_id = str(inp.get("batch_id", "")).strip()
    if not batch_id:
        _json_error(False, "PARAM_ERROR", "缺少 batch_id", "请先执行 render_submit")

    max_wait = float(inp.get("max_wait_sec", 600))
    interval = float(inp.get("interval_sec", 3))
    deadline = time.time() + max_wait
    last_done = -1
    last_total = 0
    last_done_count = 0

    while time.time() < deadline:
        url = _url("/v1/hackathon/query", {"batch_id": batch_id})
        code, resp = _http_request("GET", url)
        if code != 200:
            _json_error(
                False,
                "API_ERROR",
                f"HTTP {code}",
                "查询生图结果失败",
                {"http_code": code, "result": resp},
            )

        total, done_count, res_urls, items_list = _check_render_items(resp)
        last_total, last_done_count = total, done_count

        # 输出渲染进度
        if total > 0 and done_count != last_done:
            last_done = done_count
            done_labels = [
                it.get("label", "")
                for it in items_list
                if isinstance(it, dict) and (it.get("res_img") or "").startswith("http")
            ]
            hint = "（" + "、".join(done_labels[-3:]) + "）" if done_labels else ""
            print(f"[PROGRESS] {done_count}/{total}{hint}", file=sys.stderr)

        if total > 0 and done_count >= total:
            out = {
                "ok": True,
                "command": "ecommerce_render_poll",
                "done": True,
                "media_urls": res_urls,
                "items": items_list,
                "result": resp,
            }
            print(json.dumps(out, ensure_ascii=False))
            return

        time.sleep(interval)

    print(
        json.dumps(
            {
                "ok": False,
                "error_type": "TEMPORARY_UNAVAILABLE",
                "message": "生图轮询超时",
                "user_hint": f"在 {max_wait}s 内未拿到全部图片，可增大 max_wait_sec",
                "batch_id": batch_id,
                "progress": f"{last_done_count}/{last_total}",
            },
            ensure_ascii=False,
        )
    )
    sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(description="DesignKit 电商套图 webapi 执行器")
    p.add_argument(
        "command",
        choices=("style_create", "style_poll", "render_submit", "render_poll"),
    )
    p.add_argument("--input-json", required=True, help="JSON 参数字符串")
    args = p.parse_args()
    try:
        inp = json.loads(args.input_json)
    except json.JSONDecodeError as e:
        _json_error(False, "PARAM_ERROR", str(e), "--input-json 必须是合法 JSON")

    if not isinstance(inp, dict):
        _json_error(False, "PARAM_ERROR", "根节点须为 JSON 对象", "")

    if args.command == "style_create":
        cmd_style_create(inp)
    elif args.command == "style_poll":
        cmd_style_poll(inp)
    elif args.command == "render_submit":
        cmd_render_submit(inp)
    else:
        cmd_render_poll(inp)


if __name__ == "__main__":
    main()
