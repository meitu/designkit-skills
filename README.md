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

## Output Directory

电商套图在 `render_poll` 完成后会自动下载结果图，保存目录优先级如下：

1. `--input-json` 里的 `output_dir`
2. 环境变量 `DESIGNKIT_OUTPUT_DIR`
3. 当前工作目录存在 `openclaw.yaml` 时使用 `./output/`
4. `{OPENCLAW_HOME}/workspace/visual/output/designkit-ecommerce-product-kit/`，不存在时回退到 `~/.openclaw/workspace/visual/output/designkit-ecommerce-product-kit/`
5. `~/Downloads/`

脚本会自动创建目录，并拒绝将结果写入当前 skill 仓库内部。

## Install

安装前请先获取 API Key（AK）并设置环境变量：

1. 获取 AK：[https://www.designkit.cn/openclaw](https://www.designkit.cn/openclaw)
2. 设置环境变量：

```bash
export DESIGNKIT_OPENCLAW_AK="AK"
```

### 方式一：ClawHub

```bash
clawhub install designkit-skills
```

### 方式二：skills CLI

```bash
npx -y skills add https://github.com/meitu/designkit-skills
```

## License

MIT
