# 电商商品套图 — brand_style 可选化改动报告

**日期**：2026-03-25
**版本**：1.7.0 → 1.8.0

---

## 一、改动背景

原流程中「爆款风格」为**硬性必选步骤**：必须先调用 `style_create` 接口获取风格方案 → 用户选定一套 → 再将 `brand_style` 对象传入 `render_submit` 出图。这导致：

1. 流程冗长，用户必须经历「等待风格生成 → 选择风格 → 再出图」三步
2. `brand_style` 为必填参数，不传会直接报错退出
3. 服务端本身具备自动匹配风格的能力，但客户端代码未开放这一路径

## 二、改动目标

将 `brand_style` 从**必填**改为**可选**，默认跳过爆款风格步骤，由服务端自动选择风格直接出图，缩短用户操作链路。

---

## 三、修改文件清单

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| `scripts/ecommerce_product_kit.py` | 代码逻辑 | `brand_style` 参数可选化 + 渲染进度增强 |
| `skills/designkit-ecommerce-product-kit/SKILL.md` | 流程文档 | 主版本 SKILL.md 更新 |
| `.well-known/agent-skills/designkit-ecommerce-product-kit/SKILL.md` | 流程文档 | 分发副本同步 |
| `.well-known/skills/designkit-ecommerce-product-kit/SKILL.md` | 流程文档 | 分发副本同步 |
| `.well-known/agent-skills/designkit-skills/skills/designkit-ecommerce-product-kit/SKILL.md` | 流程文档 | 分发副本同步 |
| `.well-known/skills/designkit-skills/skills/designkit-ecommerce-product-kit/SKILL.md` | 流程文档 | 分发副本同步 |

> 另外同步修改了**安装目录** `~/.claude/skills/designkit-ecommerce-product-kit/` 下的 `SKILL.md` 和 `scripts/ecommerce_product_kit.py`，确保运行时生效。

---

## 四、具体改动详情

### 4.1 Python 脚本 (`scripts/ecommerce_product_kit.py`)

#### 改动 1：`brand_style` 参数校验放宽

```python
# 改前（必填，不传即报错）
brand_style = inp.get("brand_style")
if not isinstance(brand_style, dict):
    _json_error(False, "PARAM_ERROR", "缺少 brand_style 对象", ...)

style_name = str(inp.get("style_name", brand_style.get("name", "")))

# 改后（可选，不传时跳过）
brand_style = inp.get("brand_style")
if brand_style is not None and not isinstance(brand_style, dict):
    _json_error(False, "PARAM_ERROR", "brand_style 须为对象或留空", ...)

style_name = str(inp.get("style_name", (brand_style or {}).get("name", "")))
```

#### 改动 2：请求体条件包含 `brand_style`

```python
# 改前（始终包含）
body_obj = {
    ...
    "brand_style": brand_style,
    ...
}

# 改后（仅在有值时包含）
body_obj = { ... }  # 不含 brand_style
if brand_style is not None:
    body_obj["brand_style"] = brand_style
```

#### 改动 3：渲染轮询进度增强（附带改进）

- 新增 `_check_render_items()` 辅助函数，解析子 item 完成状态
- 轮询期间通过 stderr 输出 `[PROGRESS] done/total` 进度信息
- 返回结果增加 `items` 字段，包含每张图的 `label` 和 `res_img`
- 超时提示增加 `progress` 字段，显示已完成/总数

### 4.2 SKILL.md（5 个副本统一更新）

| 项目 | 改前 | 改后 |
|------|------|------|
| 版本号 | 1.7.0 | 1.8.0 |
| 步骤 2 | 仅问卖点 | 卖点 + 风格偏好合并询问 |
| 步骤 3 | 上架配置 | 增加「快速通道」跳过机制 |
| 步骤 4 | 爆款风格（**硬性必须**） | 爆款风格（**可选，默认跳过**） |
| 步骤 5 | 简单出图 | 成图 + 自动下载 + 进度报告 + 换风格重跑 |
| 顺序约束 | 必须经过爆款风格步骤 | 爆款风格为可选插入步骤 |

---

## 五、验证结果

使用复古丝绒沙发椅商品图进行端到端测试：

- **配置**：淘宝 / 中国 / 中文 / 1:1
- **跳过风格步骤**：`render_submit` 不传 `brand_style`
- **结果**：服务端自动匹配风格，成功生成 **7 张**套图

| 序号 | 图片类型 | 文件名 |
|------|----------|--------|
| 1 | 场景氛围图：多场景适配展示 | `复古沙发_1_场景氛围图_多场景适配展示.jpg` |
| 2 | 场景氛围图：客厅角落展示 | `复古沙发_2_场景氛围图_客厅角落展示.jpg` |
| 3 | 细节卖点图：实木锥形椅腿 | `复古沙发_3_细节卖点图_实木锥形椅腿.jpg` |
| 4 | 结构卖点图：包裹式靠背贴合人体 | `复古沙发_4_结构卖点图_包裹式靠背贴合人体.jpg` |
| 5 | 材质卖点图：高密祖母绿丝绒 | `复古沙发_5_材质卖点图_高密祖母绿丝绒.jpg` |
| 6 | 图标卖点图：核心优势一览 | `复古沙发_6_图标卖点图_核心优势一览.jpg` |
| 7 | 主图：复古祖母绿丝绒休闲椅 | `复古沙发_7_主图_复古祖母绿丝绒休闲椅.jpg` |

**结论**：`brand_style` 可选化改动验证通过，服务端能正常自动匹配风格并完成出图。

---

## 六、新流程对比

```
改前流程（5 步）：
商品图 → 问卖点 → 问配置 → 爆款风格（必须） → 成图

改后流程（3~5 步）：
商品图 → 问卖点+风格偏好 → 问配置（或快速通道跳过） → 成图+自动下载
                                                        ↑
                                              用户主动要求时才插入「爆款风格」
```

**用户体验提升**：默认流程从 5 步缩减至 3~4 步，减少等待和决策成本。
