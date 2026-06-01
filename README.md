# narrativist

> A narratology-powered deep reading engine for Claude Code.  
> 叙事学深度阅读引擎。五模式自诊断，十一类引导问题，四层类型检测。

[English](#english) | [中文](#中文)

---

## English

narrativist is a Claude Code skill that transforms how you read novels. It doesn't just ask "what do you think" — it shows you *how the text works*, from narrative voice to temporal structure, from image systems to spatial poetics.

### What it does

- **Two-phase initialization** — Phase 1 (<1s): parse TOC, build book list. Phase 2 (<1s/book): extract selected book on-demand. No wasted time on unselected books.
- **5-mode self-diagnosis engine** — Standard Chapter / Grouped Epic / Anthology / Short-Novella / Library
- **11 professional question templates** — covering plot anchors, atmosphere, narrative voice, temporal structure, free indirect discourse, sensory triggers, image systems, spatial poetics, and more
- **L1/L2/L3 level rotation** — questions cycle through plot anchors, narrative technique, and deep structure
- **Cross-session bookmarks** — pick up exactly where you left off, even weeks later
- **Character snapshots** — who's who at a glance, updated each chapter
- **ABC quizzes** — detail recall, narrative recognition, and image tracking, all optional
- **Auto-export** — full reading journal exported as Markdown on completion

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

#### Quick Start (Recommended)

1. **Ensure Python is installed** (3.8+)
   - Mac: `brew install python3` or download from python.org
   - Linux: `sudo apt-get install python3`
   - Windows: Download from https://www.python.org/downloads/, check "Add Python to PATH"

2. **One-click initialization**

   ```bash
   cd ~/.claude/skills/narrativist
   python scripts/init_book.py "path/to/your/book.epub"
   ```

3. **Start reading**

   Drop an EPUB into Claude Code and say:

   > "用 narrativist 读这本书"

#### How it works

1. `init_book.py` extracts the EPUB, parses metadata and TOC, diagnoses mode
2. Claude searches the web to confirm/refine the book type (4-layer fallback)
3. Each chapter: progress bar → character snapshot → pre-reading hook → one guiding question → reference answer → quiz → state update
4. On completion: auto-generates a final summary with character gallery, chapter anchors, and thematic threads

#### Cross-Platform Support

- ✅ Mac / Linux: Native support
- ✅ Windows: Optimized for Git Bash with path and encoding compatibility
- ✅ All file operations use Python to avoid platform differences

### Architecture

```
narrativist/
├── SKILL.md                         # Index & router
├── README.md                        # This file
├── .claude-plugin/plugin.json       # Marketplace manifest
├── scripts/
│   └── init_book.py                 # Cross-platform initialization script
├── references/
│   ├── guide-questions.md           # 11 templates + L1/L2/L3 strategy
│   ├── mode-standard-chapter.md     # Standard chapter mode (≤20 chapters)
│   ├── mode-grouped-epic.md         # Multi-volume epics (>20 chapters)
│   ├── mode-anthology.md            # Short story collections
│   ├── mode-library.md              # Collected works (3+ TOC layers)
│   ├── mode-short-form.md           # Short stories & novellas (scaled by length)
│   ├── component-quiz.md            # ABC quiz engine (shared)
│   ├── component-progress-bar.md    # Progress visualization (shared)
│   ├── component-export.md          # Reading journal export (shared)
│   ├── character-snapshot.md        # Character snapshot rules
│   └── final-summary-template.md    # Book summary template
└── state/                           # Runtime data (gitignored)
```

---

## 中文

narrativist 是一个 Claude Code 阅读 Skill。它不只问"你怎么想"——它告诉你**文本怎么运作**，从叙事声音到时间结构，从意象系统到空间诗学。

### 功能

- **两阶段初始化** — 阶段一（<1秒）：解析 TOC，生成书籍列表。阶段二（<1秒/书）：按需提取选中书籍。不浪费时间在未选择的书上。
- **五模式自诊断引擎** — 标准章节 / 大部头分组 / 短篇合集 / 短篇中篇 / 嵌套合集
- **11 类专业引导问题模板** — 覆盖情节锚点、氛围引擎、叙事声音、时间结构、自由间接引语、感官暗桩、意象系统、空间诗学等
- **L1/L2/L3 层级轮换** — 问题在情节锚点、叙事技巧、深层结构之间轮换
- **跨会话书签** — 隔几周回来，直接接着读
- **人物快照** — 每章更新的出场人物表
- **ABC 三级测验** — 细节复现、叙事识别、意象追踪，均可跳过
- **自动导出** — 全书读完后自动生成 Markdown 阅读笔记

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

#### 快速开始（推荐）

1. **确保 Python 已安装**（3.8+）
   - Mac: `brew install python3` 或从 python.org 下载
   - Linux: `sudo apt-get install python3`
   - Windows: 从 https://www.python.org/downloads/ 下载，勾选 "Add Python to PATH"

2. **一键初始化**

   ```bash
   cd ~/.claude/skills/narrativist
   python scripts/init_book.py "path/to/your/book.epub"
   ```

3. **开始阅读**

   把 EPUB 拖进 Claude Code，说：

   > "用 narrativist 读这本书"

#### 运行流程

1. `init_book.py` 解压 EPUB、解析元数据和目录、诊断模式
2. Claude 搜索网络确认/修正作品类型（四层兜底）
3. 逐章循环：进度条 → 人物快照 → 读前提示 → 一个引导问题 → 参考回答 → 测验 → 状态更新
4. 全书读完：自动生成总结（人物长廊、章节锚点、主题脉络）

#### 跨平台支持

- ✅ Mac / Linux：原生支持
- ✅ Windows：通过 Git Bash 运行，已优化路径和编码兼容性
- ✅ 所有文件操作统一使用 Python，避免平台差异

### 架构

```
narrativist/
├── SKILL.md                         # 索引总纲
├── README.md                        # 本文档
├── .claude-plugin/plugin.json       # 市场元数据
├── scripts/
│   └── init_book.py                 # 跨平台初始化脚本
├── references/
│   ├── guide-questions.md           # 11类模板 + L1/L2/L3策略
│   ├── mode-standard-chapter.md     # 标准章节模式（≤20章）
│   ├── mode-grouped-epic.md         # 大部分组模式（>20章）
│   ├── mode-anthology.md            # 短篇合集模式
│   ├── mode-library.md              # 嵌套合集模式（≥3层TOC）
│   ├── mode-short-form.md           # 短篇中篇模式（按字数分级）
│   ├── component-quiz.md            # 测验组件（共享）
│   ├── component-progress-bar.md    # 进度条（共享）
│   ├── component-export.md          # 笔记导出（共享）
│   ├── character-snapshot.md        # 人物快照规则
│   └── final-summary-template.md    # 全书总结模板
└── state/                           # 运行时数据（已忽略）
```

组件化架构：每个模式和共享功能独立文件，改测验规则只动一个文件。

---

Licensed under MIT.
