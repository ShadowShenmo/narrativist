# Grouped Epic Mode

> 用途：分组史诗模式 — 按分组粒度引导（一组一个引导问题） | 被引用：SKILL.md 路由表

适用：TOC 多层级，或章节 >20 的连续叙事。分组信息来自 `progress.json.grouping`（type 为 `toc_level` 或 `content_break`）。

**核心行为**：
- 按分组粒度循环：每个 group 一个引导问题（不是逐章）
- 组与组之间展示人物快照更新
- 组内每章提供可选的人物/地点更新（不强制逐章引导）

For each group G in progress.json.grouping.groups:

## Step G1: Group-Level Character Snapshot

Output current character table from progress.json. Highlight characters newly introduced in the previous group.

## Step G2: Group-Level Pre-Reading Hook & Guiding Question

进度条格式 → 详见 `references/component-progress-bar.md`（Grouped Epic Mode 开始时）

输出读前提示（叙事焦点 + 意象预告）：

```
读前：
类型：{类型声明} | 难度：{★级}
叙事焦点：{本组叙事焦点提示——视角/时间结构/叙述声音等最突出的叙事特征}
主要意象：{本组出现的核心意象，如有}
```

Read the text of the first chapter and last chapter within this group.
Generate **one** guiding question that spans the group's narrative arc:

问题层级策略 → 详见 `references/guide-questions.md`（引导问题生成策略）。每组第一个问题从 L1 开始，后续按 L1→L2→L3 轮换。

- Template selection follows the same priority order as Standard Chapter Mode (templates 1-12), applied to the group's combined scope
- **关键词**：{1-2 evocative words spanning the group}
- **引导问题**：{focus on the narrative arc or thematic thread of this group, not a single chapter}
- Append the mid-read invitation as in Standard Chapter Mode.

## Step G3: Per-Chapter Optional Updates

For each chapter within the group, read the text and:
- Scan for new characters. If found, add to progress.json characters array
- Save chapter record to `output/{book_slug}/chapter-{N}.md` with the group's guiding question
- Do NOT generate a new question per chapter
- If significant setting/location/POV change detected, offer as an optional note:
  > "(可选) 本章场景切换到 {location}，视角人物变为 {character}"

## Step G4: Wait for User

User reads the group, then either:
- Answers the group's guiding question in their own words
- Says "看答案" / "直接看答案" / "跳过" to skip

## Step G5: Group-Level Reference Answer

参考回答采用三段式（→ 详见 `references/guide-questions.md` 各模板 AI 参考）：

```
> 证据：{从本组原文中提取1句关键引文}
> 分析：{基于该证据的分析，100-150字}
> 延伸：{结合外部知识注入的背景，1句延伸}
```

Extract reader signals (same as Standard Chapter Mode Step 4.5).

**读后一问**（可跳过）：每组结束后生成 1 个开放式回顾问题。角度轮流切换：人物印象反转 / 最出乎意料的情节 / 哪段描写让你停下来 / 如果换一个视角来写会怎样 / 这一部的高潮真的是你以为的那个吗。不追问，不评价。格式极简，一行。

> 读后一问（可跳过）：{基于本组内容生成的问题}

## 快速回顾测验

每组结束后生成 3 道单选题（按 2:1:1 比例分配 A/B/C 类）。格式与规则 → 详见 `references/component-quiz.md`

**进度更新**：进度条格式 → 详见 `references/component-progress-bar.md`（Grouped Epic Mode 结束时）

## Step G6: Update State & Next Group

Update progress.json (increment across the group, update counters and signals). Prompt: "下一部？" (or the appropriate label from grouping).
