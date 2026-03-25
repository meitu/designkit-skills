# designkit-skills

AI 图片处理与电商商品图生成技能包（美图设计室 DesignKit）。

这个仓库提供一个根 Skill（`designkit-skills`）和两个子 Skill，可在对话中直接调用：

- 抠图去背景（透明底/白底图）
- AI 变清晰（画质修复/模糊修复/图片增强）
- 电商商品套图（Listing 主图/详情图）

## Included Skills

- `designkit-skills`（根路由）
- `designkit-edit-tools`（图片编辑：抠图、变清晰）
- `designkit-ecommerce-product-kit`（电商套图多步工作流）

## Repository Structure

- `SKILL.md`：根 Skill 入口
- `claw.json`：包元信息与触发词配置
- `api/commands.json`：编辑能力动作定义
- `skills/designkit-edit-tools/SKILL.md`：图片编辑子 Skill
- `skills/designkit-ecommerce-product-kit/SKILL.md`：电商套图子 Skill
- `scripts/run_command.sh`：通用图片编辑执行脚本
- `scripts/run_ecommerce_kit.sh`：电商套图执行入口
- `scripts/ecommerce_product_kit.py`：电商套图核心逻辑

## Install

### 1) 从 Git 仓库安装（推荐）

```bash
npx -y skills add meitu/designkit-skills --full-depth
```

只安装某个子 Skill：

```bash
npx -y skills add meitu/designkit-skills --skill designkit-edit-tools --full-depth
```

### 2) ClawHub 安装

在 ClawHub 填写仓库地址：

- `https://github.com/meitu/designkit-skills`

> 如果平台出现安全提示，通常是因为该 Skill 需要 `shell + network + API Key` 才能调用图像服务，可在确认来源可信后继续安装。

## Required Environment Variables

- `DESIGNKIT_OPENCLAW_AK`（必填）
- `DESIGNKIT_OPENCLAW_AK_URL`（可选，默认 `https://www.designkit.cn/openClaw`）

## Quick Local Check

```bash
python3 -m json.tool claw.json >/dev/null
python3 -m json.tool api/commands.json >/dev/null
```

## License

MIT
