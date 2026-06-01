# narrativist

> A narratology-powered deep reading engine for Claude Code.  
> 叙事学深度阅读引擎。四模式自诊断，十二类引导问题，三层外部知识注入。

[English](#english) | [中文](#中文)

---

## English

narrativist is a Claude Code skill that transforms how you read novels. It doesn't just ask "what do you think" — it shows you *how the text works*, from narrative voice to temporal structure, from image systems to spatial poetics.

### What it does

- **4-mode self-diagnosis engine** — detects EPUB structure automatically: Standard Chapter / Grouped Epic (War and Peace) / Anthology (Chekhov) / Library (70-volume collections)
- **12 professional question templates** — covering plot anchors, narrative voice, temporal structure, free indirect discourse, image systems, spatial poetics, and more
- **3-tier knowledge injection** — searches literary history, critical tradition, and author background before each session
- **Cross-session bookmarks** — pick up exactly where you left off, even weeks later
- **ABC quizzes** — detail recall, narrative recognition, and image tracking, all optional
- **Reading schedules** — estimated hours per section with suggested pacing
- **Auto-export** — full reading journal exported as Markdown on completion

### Install

```
/plugin marketplace add ShadowShenmo/narrativist
/plugin install narrativist@narrativist
```

Or manually:

```bash
git clone https://github.com/ShadowShenmo/narrativist.git ~/.agents/skills/narrativist
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

#### Interactive Use

That's it. The engine diagnoses the book's structure, injects literary context, shows you the cast and a progress bar, then serves one guiding question per chapter — always with a skip option.

#### Cross-Platform Support

This skill supports Mac, Linux, and Windows (Git Bash):
- ✅ Mac / Linux: Native support
- ✅ Windows: Optimized for Git Bash with path and encoding compatibility
- ✅ All file operations use Python to avoid platform differences

### Architecture

```
narrativist/
├── SKILL.md                         # Index & router (133 lines)
├── README.md                        # This file
├── .claude-plugin/plugin.json       # Marketplace manifest
├── scripts/
│   └── init_book.py                 # Cross-platform initialization script
├── references/
│   ├── guide-questions.md           # 12 templates + L1/L2/L3 strategy
│   ├── mode-standard-chapter.md     # ≤20 chapters, flat TOC
│   ├── mode-grouped-epic.md         # Multi-volume epics
│   ├── mode-anthology.md            # Short story collections
│   ├── mode-library.md              # Nested anthologies (3+ TOC layers)
│   ├── mode-short-form.md           # Ultra-short works
│   ├── component-quiz.md            # ABC quiz engine (shared)
│   ├── component-progress-bar.md    # Progress visualization (shared)
│   ├── component-export.md          # Reading journal export (shared)
│   ├── character-snapshot.md        # Character snapshot rules
│   └── final-summary-template.md    # Book summary template
└── state/                           # Runtime (gitignored)
```

Component-based: every mode and shared utility lives in its own file. To change how quizzes work, edit one file.

---

## 中文

narrativist 是一个 Claude Code 阅读 Skill。它不只问"你怎么想"——它告诉你**文本怎么运作**，从叙事声音到时间结构，从意象系统到空间诗学。

### 功能

- **四模式自诊断引擎** — 自动识别 EPUB 结构：标准章节 / 大部头分组（战争与和平）/ 短篇合集（契诃夫）/ 嵌套合集（70册丛书）
- **12 类专业引导问题模板** — 覆盖情节锚点、叙事声音、时间结构、自由间接引语、意象系统、空间诗学等
- **三层外部知识注入** — 每次会话前检索文学史定位、评论传统、创作背景
- **跨会话书签** — 隔几周回来，直接接着读
- **ABC 三级测验** — 细节复现、叙事识别、意象追踪，均可跳过
- **阅读周期表** — 每部分预估阅读时长，建议节奏
- **自动导出** — 全书读完后自动生成 Markdown 阅读笔记

### 安装

```
/plugin marketplace add ShadowShenmo/narrativist
/plugin install narrativist@narrativist
```

或手动：

```bash
git clone https://github.com/ShadowShenmo/narrativist.git ~/.agents/skills/narrativist
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

#### 交互式使用

引擎会自动诊断书的结构、注入文学背景、展示人物表和进度条，然后每章一个引导问题——永远可以跳过。

#### 跨平台支持

本 skill 支持 Mac、Linux、Windows（Git Bash）三种平台：
- ✅ Mac / Linux：原生支持
- ✅ Windows：通过 Git Bash 运行，已优化路径和编码兼容性
- ✅ 所有文件操作统一使用 Python，避免平台差异

### 架构

```
narrativist/
├── SKILL.md                         # 索引总纲（133行）
├── README.md                        # 本文档
├── .claude-plugin/plugin.json       # 市场元数据
├── scripts/
│   └── init_book.py                 # 跨平台初始化脚本
├── references/
│   ├── guide-questions.md           # 12类模板 + L1/L2/L3策略
│   ├── mode-standard-chapter.md     # 标准章节（≤20章）
│   ├── mode-grouped-epic.md         # 大部头分组
│   ├── mode-anthology.md            # 短篇合集
│   ├── mode-library.md              # 嵌套合集（≥3层TOC）
│   ├── mode-short-form.md           # 超短篇
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
