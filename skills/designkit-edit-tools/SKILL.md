---
name: designkit-edit-tools
description: >-
  美图设计室通用图片编辑工具集（AI 修图）。支持智能抠图（背景移除/透明底/白底图）
  和 AI 变清晰（画质修复/模糊修复/图片增强）。
  当用户提到抠图、去背景、背景移除、matting、SOD、画质修复、变清晰、
  图片增强、image restoration 时触发。
version: "1.0.0"
---

# DesignKit Edit Tools

## Overview

通用图片编辑能力集，属于 DesignKit 原子能力层。每项能力输入输出明确、路由简单，既可独立使用，也可被上层 workflow 复用。

## 能力清单

| 能力 | 操作标识 | 状态 | 描述 |
|------|---------|------|------|
| 智能抠图 | `sod` | ✅ 可用 | 把图片主体从背景里抠出来 |
| AI 变清晰 | `image_restoration` | ✅ 可用 | 提高图片清晰度 |

## 意图识别

| 用户说法 | 路由到 |
|----------|--------|
| 抠图、去背景、扣图、移除背景、透明底、background removal、matting、cutout | `sod` |
| 变清晰、画质修复、图片增强、超分、提升画质、修复低清、image restoration | `image_restoration` |

## 对话追问策略

### 智能抠图 (`sod`)

| 缺省信息 | 是否追问 | 追问话术 |
|---------|---------|---------|
| 没有图片 | 必须追问 | "请提供需要抠图的图片（本地路径或 URL）。" |
| 没有说背景色 | 不追问 | 默认按系统方案处理 |
| 没有说比例和尺寸 | 不追问 | 默认按原图尺寸返回 |

典型对话：
> 用户："帮我把这张图抠一下"
> Agent："请提供需要抠图的图片（本地路径或 URL）。"
> 用户：提供图片
> Agent："好的，我来帮你把这张图的主体抠出来。" → 执行

### AI 变清晰 (`image_restoration`)

| 缺省信息 | 是否追问 | 追问话术 |
|---------|---------|---------|
| 没有图片 | 必须追问 | "请提供需要变清晰的图片（本地路径或 URL）。" |
| 没说清晰度等级 | 不追问 | 默认高清 |

典型对话：
> 用户："这张图太模糊了，帮我变清晰"
> Agent：（用户已提供图片）"好的，我来帮你提升这张图的清晰度。" → 执行

## 执行

参数补齐后，调用统一执行器：

```bash
bash __SKILL_DIR__/../../scripts/run_command.sh <action> --input-json '<参数JSON>'
```

示例：

```bash
bash __SKILL_DIR__/../../scripts/run_command.sh sod --input-json '{"image":"https://example.com/photo.jpg"}'
```

```bash
bash __SKILL_DIR__/../../scripts/run_command.sh image_restoration --input-json '{"image":"/Users/me/photo.jpg"}'
```

`__SKILL_DIR__` 替换为本 SKILL.md 所在目录的绝对路径。脚本会自动处理本地图片上传。

## 结果处理

解析脚本输出的 JSON：
- `ok: true` → 从 `media_urls` 提取结果图 URL，用 `![结果图](url)` 展示给用户
- `ok: false` → 读取 `error_type` 和 `user_hint`，向用户展示可操作的指引

| `error_type` | 用户可见提示 |
|-------------|------------|
| `CREDENTIALS_MISSING` | 按 `user_hint` 引导用户配置 |
| `AUTH_ERROR` | 按 `user_hint` 引导用户核对 |
| `ORDER_REQUIRED` | 前往美图设计室获取美豆 |
| `PARAM_ERROR` | 按 `user_hint` 补齐参数 |
| `UPLOAD_ERROR` | 检查网络或换一张图片 |
| `API_ERROR` | 换一张图片试试 |

## Boundaries

本 skill 只做原子级图片编辑操作。以下场景应转交到对应 skill：

| 不做 | 转交 |
|------|------|
| 消除水印、去字、去路人、去眼镜反光等 AI 消除 | `designkit-ai-eraser` |
| 生成电商套图、电商套图、爆款风格套图等多步套图 | `designkit-ecommerce-product-kit` |
