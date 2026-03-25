# 预留 Skill 备份（2026-03-25）

> 此文件备份了上线前移除的所有预留 skill 和预留命令。
> 需要还原时，将此文件交给 AI 助手，说「按备份还原预留 skill」即可。

---

## 一、4 个预留 Skill 文件

### 1. skills/designkit-product-kit/SKILL.md

```markdown
---
name: designkit-product-kit
description: >-
  美图设计室电商商品图生产能力集。支持白底精修图、三视图生成、通用换背景、
  Listing 套图、A+ 详情页、图片商品替换、SKU 变体图。
  当用户提到白底图、三视图、换背景、Listing、A+、商品替换、SKU 变体时触发。
version: "1.0.0"
status: reserved
---

# DesignKit Product Kit（预留）

> ⚠️ 本 skill 尚未实现，以下为能力规划。如需使用，请前往 [美图设计室](https://www.designkit.cn/) 在线操作。

## Overview

电商商品图生产能力集，面向商品上新和 Listing 素材生产场景。

## 计划能力

| 子 Workflow | 描述 | 用户典型表达 |
|-------------|------|-------------|
| 白底精修图 | 生成适合电商上架的白底图或透明底精修图 | "帮我把这款产品做成白底精修图。" |
| 三视图生成 | 生成商品的多角度展示图（正面、侧面、背面） | "帮我给这个产品出三视图。" |
| 通用换背景 | 给图片主体替换背景，生成氛围感场景图 | "把这张图换成室内背景。" |
| Listing 套图 | 生成整套电商 Listing 图（主图、场景图、卖点图） | "给这款产品出一套亚马逊美国站 Listing 图。" |
| A+ 详情页 | 生成 A+ 详情页模块图 | "帮我生成这款产品的 A+ 详情页。" |
| 图片商品替换 | 保留原背景和构图，替换图中的商品 | "背景别动，只把商品换掉。" |
| SKU 变体图 | 生成同一商品的不同颜色、规格、尺寸版本 | "把这款包再出黑色和米色两个版本。" |

## 输入要求

- **必须追问**：用户是否已上传商品图；Listing/A+ 需要平台、语言、国家
- **可以默认**：背景色、比例、尺寸、风格方向、卖点（自动生成）

## 易混淆 Skill 对比

| Skill | 核心目标 | 什么保持不变 | 什么会变化 |
|-------|---------|------------|----------|
| 通用换背景 | 给主体换新背景 | 主体 | 背景、环境 |
| 图片商品替换 | 保留原图背景，换商品 | 背景、构图 | 商品主体 |
| SKU 变体图 | 同一商品出不同版本 | 商品类型、结构 | 颜色、尺寸等属性 |
```

### 2. skills/designkit-tryon-kit/SKILL.md

```markdown
---
name: designkit-tryon-kit
description: >-
  美图设计室穿戴与模特展示能力集。支持 AI 服装换色、平铺图上身、
  指定模特换装、模特姿势拓展、模特换场景。
  当用户提到试衣、穿搭、换模特、上身效果、服装换色、换场景时触发。
version: "1.0.0"
status: reserved
---

# DesignKit Tryon Kit（预留）

> ⚠️ 本 skill 尚未实现，以下为能力规划。如需使用，请前往 [美图设计室](https://www.designkit.cn/) 在线操作。

## Overview

穿戴与模特展示能力集，面向服饰电商的模特展示和试穿场景。

## 计划能力

| 子 Workflow | 描述 | 用户典型表达 |
|-------------|------|-------------|
| AI 服装换色 | 给服装快速生成新的颜色版本 | "把这件衣服换成黑色和米白色。" |
| 平铺图上身 | 把服装平铺图生成上身试穿效果 | "把这件衣服直接穿到模特身上。" |
| 指定模特换装 | 使用特定模特或指定人脸换装 | "把这件衣服换到这个模特身上。" |
| 模特姿势拓展 | 同一套服装生成多个展示姿势和角度 | "给这套穿搭多出几个姿势。" |
| 模特换场景 | 保留模特和服装，切换展示场景 | "把这套穿搭换到街景里。" |

## 输入要求

- **必须追问**：用户是否已上传服装图；换装需要目标模特信息；换色需要目标颜色
- **可以默认**：模特特征、姿势、场景（按系统推荐生成）
```

### 3. skills/designkit-video-kit/SKILL.md

```markdown
---
name: designkit-video-kit
description: >-
  美图设计室商品与营销视频生产能力集。支持产品特写视频、360 商品视频、
  创意广告视频、电商视频复刻。
  当用户提到商品视频、产品视频、360 旋转视频、广告视频、视频复刻时触发。
version: "1.0.0"
status: reserved
---

# DesignKit Video Kit（预留）

> ⚠️ 本 skill 尚未实现，以下为能力规划。如需使用，请前往 [美图设计室](https://www.designkit.cn/) 在线操作。

## Overview

商品与营销视频生产能力集，面向高价值、高频的商品展示和营销视频场景。

## 计划能力

| 子 Workflow | 描述 | 用户典型表达 |
|-------------|------|-------------|
| 产品特写视频 | 基于商品图生成突出细节、质感的短视频 | "帮我把这款产品做一个特写视频。" |
| 360 商品视频 | 基于商品图生成旋转展示视频 | "给这款产品做一个 360 旋转视频。" |
| 创意广告视频 | 基于商品图和主题生成创意广告视频 | "帮我做一条新品广告视频。" |
| 电商视频复刻 | 基于某段视频 + 商品图片，复制视频脚本创作相似视频 | "帮我参考这个视频，将商品替换为我自己的。" |

## 输入要求

- **必须追问**：用户是否已上传商品图
- **可以默认**：镜头风格、时长、字幕、旋转方向、投放平台（按标准方式生成）
```

### 4. skills/designkit-marketing-kit/SKILL.md

```markdown
---
name: designkit-marketing-kit
description: >-
  美图设计室营销内容生产能力集。支持海报设计、小红书套组海报、修改图片文字。
  当用户提到海报、促销海报、小红书轮播图、修改图片文字时触发。
version: "1.0.0"
status: reserved
---

# DesignKit Marketing Kit（预留）

> ⚠️ 本 skill 尚未实现，以下为能力规划。如需使用，请前往 [美图设计室](https://www.designkit.cn/) 在线操作。

## Overview

营销内容生产能力集，面向海报设计和社媒内容生产场景。

## 计划能力

| 子 Workflow | 描述 | 用户典型表达 |
|-------------|------|-------------|
| 海报设计 | 生成各种风格的海报 | "帮我做一张春季促销海报。" |
| 小红书套组海报 | 生成轮播图套图（封面 + 内页），风格统一 | "帮我做一套小红书轮播图，主题是防晒科普。" |
| 修改图片文字 | 直接修改图片中的现有文字内容 | "把图上的'买一送一'改成'第二件半价'。" |

## 输入要求

- **必须追问**：海报主题；修改文字需要原文字和目标文字
- **可以默认**：文案、视觉风格（按主题自动联想）；比例（默认 4:3）；小红书页数（默认封面 + 3 页内页）
```

---

## 二、3 个预留命令（api/commands.json 中被移除的条目）

```json
{
  "aieraser": {
    "name": "AI 消除",
    "description": "去掉图片里不想要的内容，如水印、文字、路人、杂物、反光等。",
    "endpoint": "/openclaw/aieraser",
    "skill": "designkit-edit-tools",
    "status": "reserved",
    "required": ["image"],
    "optional": ["erase_type"],
    "defaults": {},
    "body_template": {},
    "ask_if_missing": {
      "image": "请提供需要消除的图片（本地路径或 URL）。",
      "erase_type": "你想去掉的是水印、文字、路人，还是某个具体区域？"
    },
    "triggers": [
      "去水印",
      "去文字",
      "去路人",
      "去杂物",
      "去反光",
      "消除",
      "AI 消除"
    ]
  },
  "resize": {
    "name": "无损改尺寸",
    "description": "把图片改成指定比例或尺寸，用于适配平台规范。",
    "endpoint": "/openclaw/resize",
    "skill": "designkit-edit-tools",
    "status": "reserved",
    "required": ["image", "target_size"],
    "optional": ["fill_mode"],
    "defaults": {
      "fill_mode": "fill"
    },
    "body_template": {},
    "ask_if_missing": {
      "image": "请提供需要改尺寸的图片（本地路径或 URL）。",
      "target_size": "你想改成什么比例或尺寸？比如 1:1、4:3，或者平台标准尺寸。"
    },
    "triggers": ["改尺寸", "改比例", "适配尺寸", "1:1", "4:3"]
  },
  "image_translation": {
    "name": "图片翻译",
    "description": "把图片中的文字翻译成目标语言，并尽量保留排版结构。",
    "endpoint": "/openclaw/image_translation",
    "skill": "designkit-edit-tools",
    "status": "reserved",
    "required": ["image", "target_lang"],
    "optional": ["source_lang", "protect_subject"],
    "defaults": {
      "source_lang": "auto",
      "protect_subject": true
    },
    "body_template": {},
    "ask_if_missing": {
      "image": "请提供需要翻译的图片（本地路径或 URL）。",
      "target_lang": "你想翻译成哪种语言？比如英文、法语、日语。"
    },
    "triggers": ["翻译图片", "图片翻译", "翻译图中文字"]
  }
}
```

---

## 三、根 SKILL.md 中被移除的段落

### Purpose 段中被移除的行

```markdown
- 使用 `designkit-product-kit` 进行电商商品图规划能力（白底图、三视图、换背景、Listing、A+、商品替换、SKU 变体；尚未实现时引导官网）。
- 使用 `designkit-tryon-kit` 进行穿戴与模特展示（平铺图上身、换模特、姿势拓展、换场景、服装换色）。
- 使用 `designkit-video-kit` 进行商品与营销视频生产（产品特写视频、360 旋转视频、创意广告视频、电商视频复刻）。
- 使用 `designkit-marketing-kit` 进行营销内容生产（海报设计、小红书套组海报、修改图片文字）。
```

### Routing Rules 中被移除的段（Section 2, 4, 5, 6）

```markdown
### 2. `designkit-product-kit` — 电商商品图生产（预留）

当用户意图属于以下场景时路由到此 skill：

- 白底图、白底精修、商品主图
- 三视图、多角度展示
- 换背景、场景图、氛围图
- Listing 套图、整套上架图
- A+ 详情页
- 商品替换、图片换商品
- SKU 变体图、颜色变体、规格变体

### 4. `designkit-tryon-kit` — 穿戴与模特展示（预留）

当用户意图属于以下场景时路由到此 skill：

- 平铺图上身、服装试穿
- 换模特、指定模特换装
- 姿势拓展、多姿势展示
- 模特换场景
- 服装换色

### 5. `designkit-video-kit` — 商品与营销视频（预留）

当用户意图属于以下场景时路由到此 skill：

- 产品特写视频、商品短视频
- 360 旋转视频、全角度展示视频
- 创意广告视频、宣传视频
- 电商视频复刻

### 6. `designkit-marketing-kit` — 营销内容生产（预留）

当用户意图属于以下场景时路由到此 skill：

- 海报设计、促销海报
- 小红书套组海报、轮播图
- 修改图片文字、替换图中文案
```

### Routing Rules edit-tools 段中被移除的预留行

```markdown
- AI 消除、去水印、去文字、去路人、去杂物、去反光（预留）
- 改尺寸、改比例、适配平台尺寸（预留）
- 图片翻译、翻译图中文字（预留）
```

### 根 SKILL.md description frontmatter 中被移除的引用

原 description 中包含 `designkit-product-kit`、`designkit-tryon-kit`、`designkit-video-kit`、`designkit-marketing-kit` 的引用。

---

## 四、designkit-edit-tools SKILL.md 中被移除的预留段落

### 能力清单表中被移除的行

```markdown
| AI 消除 | `aieraser` | 🔜 预留 | 去掉图片里的水印、文字、路人等 |
| 无损改尺寸 | `resize` | 🔜 预留 | 改成指定比例或尺寸 |
| 图片翻译 | `image_translation` | 🔜 预留 | 翻译图片中的文字 |
```

### 意图识别表中被移除的行

```markdown
| 去水印、去文字、去路人、去杂物、去反光、消除、AI 消除 | `aieraser`（预留） |
| 改尺寸、改比例、适配尺寸、1:1、4:3 | `resize`（预留） |
| 翻译图片文字、图片翻译、把图中文字翻成xx | `image_translation`（预留） |
```

### 对话追问策略中被移除的段

```markdown
### AI 消除 (`aieraser`) — 预留

| 缺省信息 | 是否追问 | 追问话术 |
|---------|---------|---------|
| 没有图片 | 必须追问 | "请提供需要消除的图片（本地路径或 URL）。" |
| 没说要去掉什么 | 必须追问 | "你想去掉的是水印、文字、路人、眼镜、反光？" |

### 无损改尺寸 (`resize`) — 预留

| 缺省信息 | 是否追问 | 追问话术 |
|---------|---------|---------|
| 没有图片 | 必须追问 | "请提供需要改尺寸的图片（本地路径或 URL）。" |
| 没说目标尺寸 | 必须追问 | "你想改成什么比例或尺寸？比如 1:1、4:3，或者平台标准尺寸。" |

### 图片翻译 (`image_translation`) — 预留

| 缺省信息 | 是否追问 | 追问话术 |
|---------|---------|---------|
| 没有图片 | 必须追问 | "请提供需要翻译的图片（本地路径或 URL）。" |
| 没说目标语言 | 必须追问 | "你想翻译成哪种语言？比如英文、法语、日语。" |
```

### edit-tools description frontmatter 中被移除的引用

原 description 最后一行 `AI 消除、无损改尺寸、图片翻译能力预留待实现。` 被移除。

---

## 五、index.json 中被移除的条目

以下 4 个条目从 `.well-known/skills/index.json` 和 `.well-known/agent-skills/index.json` 中移除：

```json
{
  "name": "designkit-product-kit",
  "description": "电商商品图生产能力规划（白底图、三视图、换背景、A+、SKU 等）。",
  "files": ["SKILL.md"]
},
{
  "name": "designkit-tryon-kit",
  "description": "穿搭/换模特/换场景等试衣与模特展示能力规划。",
  "files": ["SKILL.md"]
},
{
  "name": "designkit-video-kit",
  "description": "商品与营销视频能力规划（特写、360、广告、视频复刻）。",
  "files": ["SKILL.md"]
},
{
  "name": "designkit-marketing-kit",
  "description": "营销内容能力规划（海报、小红书套图、改图中文字）。",
  "files": ["SKILL.md"]
}
```

同时 `designkit-skills` 条目中的 `files` 数组移除了：
```
"skills/designkit-marketing-kit/SKILL.md",
"skills/designkit-product-kit/SKILL.md",
"skills/designkit-tryon-kit/SKILL.md",
"skills/designkit-video-kit/SKILL.md"
```

---

## 六、被删除的 .well-known 文件/目录列表

```
.well-known/skills/designkit-product-kit/
.well-known/skills/designkit-tryon-kit/
.well-known/skills/designkit-video-kit/
.well-known/skills/designkit-marketing-kit/
.well-known/skills/designkit-skills/skills/designkit-product-kit/
.well-known/skills/designkit-skills/skills/designkit-tryon-kit/
.well-known/skills/designkit-skills/skills/designkit-video-kit/
.well-known/skills/designkit-skills/skills/designkit-marketing-kit/
.well-known/agent-skills/designkit-product-kit/
.well-known/agent-skills/designkit-tryon-kit/
.well-known/agent-skills/designkit-video-kit/
.well-known/agent-skills/designkit-marketing-kit/
.well-known/agent-skills/designkit-skills/skills/designkit-product-kit/
.well-known/agent-skills/designkit-skills/skills/designkit-tryon-kit/
.well-known/agent-skills/designkit-skills/skills/designkit-video-kit/
.well-known/agent-skills/designkit-skills/skills/designkit-marketing-kit/
```
