# designkit-skills

美图设计室 DesignKit 能力集合技能仓库，包含根路由与多个子技能（编辑、电商套图、商品图规划、试衣、视频、营销）。

## Repository Layout

- `SKILL.md`: 根技能入口（`designkit-skills`）
- `skills/*/SKILL.md`: 子技能定义
- `api/commands.json`: 编辑能力 API 定义
- `scripts/`: 执行脚本（OpenClaw/DesignKit 调用）
- `.well-known/`: URL 安装协议目录（自动生成）

## Local Validation

```bash
python3 scripts/build_well_known.py --check
bash tests/run_command_async_test.sh
python3 tests/well_known_layout_test.py
bash tests/well_known_url_smoke.sh
```

## Install (Git Source)

公开 GitHub 仓库推荐用法：

```bash
npx -y skills add <owner>/<repo> --full-depth
```

或指定某个技能：

```bash
npx -y skills add <owner>/<repo> --skill designkit-edit-tools --full-depth
```

> 注意：`skills add https://host/path` 会走 well-known 协议，不会自动当作 git clone。

## Install (Well-Known URL)

当你把仓库静态托管到可公开访问域名后（无登录跳转），可直接：

```bash
npx -y skills add https://<your-domain>/<path>
```

CLI 会读取以下任一路径：

- `/.well-known/agent-skills/index.json`
- `/.well-known/skills/index.json`

## Publishing Checklist

1. 生成并提交 well-known 产物：
   ```bash
   python3 scripts/build_well_known.py
   ```
2. 执行校验：
   ```bash
   python3 scripts/build_well_known.py --check
   bash tests/run_command_async_test.sh
   python3 tests/well_known_layout_test.py
   ```
3. 确认公开地址可匿名访问：
   - `https://<domain>/.well-known/skills/index.json`
   - `https://<domain>/.well-known/agent-skills/index.json`
4. 在 Claw Hub 填写仓库地址并验证解析结果。

## Runtime Env

核心鉴权环境变量：

- `DESIGNKIT_OPENCLAW_AK`（必填）
- `DESIGNKIT_OPENCLAW_AK_URL`（可选，默认 `https://www.designkit.cn/openClaw`）

常用可选环境变量：

- `OPENCLAW_API_BASE`（默认 `https://openclaw-designkit-api.meitu.com`）
- `DESIGNKIT_WEBAPI_BASE`（电商套图脚本，默认 `https://openclaw-designkit-api.meitu.com/v1`）
- `OPENCLAW_ASYNC_MAX_WAIT_SEC`
- `OPENCLAW_ASYNC_INTERVAL_SEC`
- `OPENCLAW_ASYNC_QUERY_ENDPOINT`
