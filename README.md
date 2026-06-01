# narrativist

> A narratology-powered deep reading engine for Claude Code.
> 阅读引擎。不关心类型，只关心文本。带着问题，陪你读完。

[English](#english) | [中文](#中文)

---

## English

narrativist is a Claude Code skill that reads with you. It doesn't classify your book — it just cuts it into units, asks one good question per unit, and remembers what you thought.

### What it does

- **Unit-based reading** — TOC leaf nodes become reading units. No modes, no type labels. Just units.
- **Two structures** — single book or library (multi-book collection). That's the only distinction.
- **Smart question selection** — picks guiding questions based on what the text actually says, not what type of book it supposedly is.
- **L1/L2/L3 rotation** — questions cycle through plot anchors, narrative technique, and deep structure.
- **Incremental export** — every unit's notes are appended to a Markdown file immediately. No data loss.
- **Cross-session bookmarks** — pick up where you left off, even weeks later.
- **Character snapshots** — who's who at a glance, updated each unit.
- **ABC quizzes** — detail recall, narrative recognition, and image tracking. All optional.
- **Library navigation** — per-book isolation, completion tracking, cross-book summary.

### Install

```
/plugin marketplace add ShadowShenmo/narrativist
/plugin install narrativist@narrativist
```

Or manually:

```bash
git clone git@github.com:ShadowShenmo/narrativist.git ~/.claude/skills/narrativist
```

### Use

Drop an EPUB into Claude Code and say:

> "用 narrativist 读这本书"

That's it. The engine does the rest.

### How it works

1. `init_book.py` (<1s): extract EPUB, parse TOC, diagnose structure (single/library), generate unit plan
2. For library: show book list, user selects
3. Unit loop: progress bar → character snapshot → one guiding question → reference answer → quiz → state update
4. On completion: auto-generates reading journal (Markdown)

### Architecture

```
narrativist/
├── SKILL.md                    # Index & flow (v3.0)
├── README.md                   # This file
├── scripts/
│   ├── init_book.py            # SHA256 + extract + OPF + TOC → single/library
│   └── unit_slicer.py          # TOC leaves → unit plan (filter + merge + output)
├── references/
│   ├── guide-questions.md      # 11 templates (selected by text features)
│   ├── component-quiz.md       # ABC quiz engine
│   ├── component-progress-bar.md  # Progress display
│   ├── component-export.md     # Incremental + final export
│   ├── character-snapshot.md   # Character tracking
│   └── final-summary-template.md  # Book summary template
└── state/
    ├── {sha}-diagnosis.json    # Structure cache (single/library)
    ├── {sha}-unit-plan.json    # Reading unit plan
    ├── {sha}-progress.json     # Reading progress
    ├── {sha}-bookmark.json     # Session bookmark
    └── chapters/               # Extracted chapter text
```

---

## 中文

narrativist 是一个 Claude Code 阅读 Skill。它不分类你的书——它只把书切成单元，每个单元问一个好问题，记住你想到的东西。

### 功能

- **单元制阅读** — TOC 叶子节点就是阅读单元。没有模式，没有类型标签。只有单元。
- **两种结构** — 单书或多书合集。这是唯一的区分。
- **按文本选问题** — 根据当前单元的实际内容选引导问题，不按书类型选。
- **L1/L2/L3 轮换** — 问题在情节锚点、叙事技巧、深层结构之间轮换。
- **增量导出** — 每单元的笔记立即追加到 Markdown 文件。不丢数据。
- **跨会话书签** — 隔几周回来，直接接着读。
- **人物快照** — 每单元更新的出场人物表。
- **ABC 三级测验** — 细节复现、叙事识别、意象追踪。均可跳过。
- **Library 导航** — 每本书独立状态、完成追踪、跨书总结。

### 安装

```
/plugin marketplace add ShadowShenmo/narrativist
/plugin install narrativist@narrativist
```

或手动：

```bash
git clone git@github.com:ShadowShenmo/narrativist.git ~/.claude/skills/narrativist
```

### 使用

把 EPUB 拖进 Claude Code，说：

> "用 narrativist 读这本书"

就这样。引擎会处理剩下的事。

### 运行流程

1. `init_book.py`（<1秒）：解压 EPUB、解析 TOC、诊断结构（单书/多书）、生成单元计划
2. 多书合集：展示书单，用户选书
3. 单元循环：进度条 → 人物快照 → 一个引导问题 → 参考回答 → 测验 → 状态更新
4. 完成：自动生成阅读笔记（Markdown）

### 架构

```
narrativist/
├── SKILL.md                    # 索引与流程（v3.0）
├── README.md                   # 本文档
├── scripts/
│   ├── init_book.py            # SHA256 + 解压 + OPF + TOC → single/library
│   └── unit_slicer.py          # TOC 叶子 → 单元计划（过滤 + 合并 + 输出）
├── references/
│   ├── guide-questions.md      # 11 类模板（按文本特征选择）
│   ├── component-quiz.md       # ABC 测验引擎
│   ├── component-progress-bar.md  # 进度展示
│   ├── component-export.md     # 增量 + 完整导出
│   ├── character-snapshot.md   # 人物追踪
│   └── final-summary-template.md  # 全书总结模板
└── state/
    ├── {sha}-diagnosis.json    # 结构诊断缓存
    ├── {sha}-unit-plan.json    # 阅读单元计划
    ├── {sha}-progress.json     # 阅读进度
    ├── {sha}-bookmark.json     # 会话书签
    └── chapters/               # 提取的章节文本
```

---

Licensed under MIT.
