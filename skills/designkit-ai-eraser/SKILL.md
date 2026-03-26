---
name: designkit-ai-eraser
description: >-
  美图设计室 AI 消除子 skill。用于去掉图片里不想要的内容，如水印、文字、路人、
  眼镜或眼镜反光；当用户提到消除水印、去字、去路人、去眼镜、眼镜反光时触发。
version: "1.0.0"
---

# DesignKit AI Eraser

## Overview

AI 消除能力用于删除图片里不想保留的内容。当前优先支持：

| 能力 | 操作标识 | 状态 | 场景 |
|------|---------|------|------|
| 去水印 / 去文字 | `eraser_watermark_text` | ✅ 可用 | 水印、字幕、角标、画面文字 |
| 去眼镜 / 眼镜反光 | `eraser_eyeglasses` | ✅ 可用 | 人像眼镜、镜片反光 |
| 去路人 | `eraser_passerby` | ✅ 可用 | 路人、背景行人、干扰人物 |
| 去 Logo | `eraser_logo` | 预留 | logo、品牌标记 |

## 意图识别

| 用户说法 | 路由到 |
|----------|--------|
| 去水印、消除水印、去文字、删字、移除字幕 | `eraser_watermark_text` |
| 去眼镜、眼镜反光、镜片反光、消除反光 | `eraser_eyeglasses` |
| 去路人、消除路人、移除路人、删除背景行人 | `eraser_passerby` |
| 去 logo、移除 logo、去标志 | `eraser_logo`（预留） |

如果用户只说“帮我消除一下”“把多余东西去掉”，优先根据上下文猜测：

- 提到水印、文字、字样 → `eraser_watermark_text`
- 提到眼镜、镜片、反光 → `eraser_eyeglasses`
- 提到路人、行人、背景人物 → `eraser_passerby`
- 无法判断时，再追问一次要消除哪类内容

## 对话追问策略

| 缺省信息 | 是否追问 | 追问话术 |
|---------|---------|---------|
| 没有图片 | 必须追问 | "请提供需要消除的图片（支持一张或多张，本地路径或 URL）。" |
| 只说“消除一下”未说明对象 | 必须追问 | "你想去掉哪类内容？现在支持水印/文字、路人、眼镜或眼镜反光。" |
| 已明确对象 | 不追问 | 直接执行 |

典型对话：

> 用户："把这张图里的水印去掉"
> Agent："好的，我来帮你把这张图里的水印和文字内容消除掉。" → 执行

> 用户："帮我消除人物眼镜反光"
> Agent："好的，我来帮你处理这张图里的人物眼镜和反光。" → 执行

## 执行

参数补齐后，调用统一执行器：

```bash
bash __SKILL_DIR__/../../scripts/run_command.sh <action> --input-json '<参数JSON>'
```

示例：

```bash
bash __SKILL_DIR__/../../scripts/run_command.sh eraser_watermark_text --input-json '{"image":"https://example.com/photo.jpg"}'
```

```bash
bash __SKILL_DIR__/../../scripts/run_command.sh eraser_passerby --input-json '{"images":["/Users/me/a.jpg","/Users/me/b.jpg"]}'
```

`__SKILL_DIR__` 替换为本 SKILL.md 所在目录的绝对路径。脚本支持：

- `image`: 单张图片
- `images`: 多张图片数组

## 结果处理

解析脚本输出的 JSON：

- `ok: true` → 从 `media_urls` 提取结果图 URL，用 `![结果图](url)` 展示
- `ok: false` → 读取 `error_type` 和 `user_hint`，给出可操作提示

## Boundaries

以下类型先不直接承诺可用：

- 杂物、logo、泛化“自动消除”但没有明确对象
- 需要精细框选或局部区域编辑的复杂修图

遇到这些情况：

- 如果能根据用户话术准确归类到已支持能力，就直接路由
- 否则明确说明当前优先支持“水印/文字、路人、眼镜/眼镜反光”
