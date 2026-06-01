# Standard Chapter Mode

> 用途：标准章节模式 — 逐章引导阅读 | 被引用：SKILL.md 路由表

适用：TOC 扁平、章节 ≤20、连续叙事。

**执行原则**：以下每一步都是**必选**。除非明确标注"可跳过"，否则不得省略。

---

For each chapter (N from 1 to total_chapters):

## Step 1: 读前准备

### 1a. 进度条（开始时）

进度条按字数加权计算（不按章节数均分）→ 详见 `references/component-progress-bar.md`

格式：`[{第N部名} {进度条}] {N}/{total} 部`

### 1b. 人物快照

从 progress.json.characters 读取当前人物表并展示。

**第 1 章特殊处理**：characters 为空时，先读取章节文本扫描主要人物（叙述者、核心家庭成员、关键配角），写入 progress.json.characters，再展示快照。不要跳过。

格式 → 详见 `references/character-snapshot.md`

### 1c. 读前提示

输出以下格式的读前 hook（**必选，不得省略**）：

```
读前：
类型：{类型声明} | 难度：{★级}
叙事焦点：{本章叙事焦点提示——视角/时间结构/叙述声音等最突出的叙事特征}
主要意象：{本章出现的核心意象，如该章有}
```

- 类型声明：基于全书判断（如"现代主义·意识流""现实主义·社会小说"）
- 难度：★ 到 ★★★★★
- 叙事焦点：本章最值得关注的叙事特征
- 主要意象：本章出现的核心意象（可选，无则省略此行）

### 1d. 读取章节文本

从 `state/chapters/{chapters[N-1].file}` 读取章节纯文本。
注意：文件名从 progress.json 的 chapters 数组中获取（如 part1.txt, ch01.txt）。

## Step 2: 生成引导问题

### 2a. 模板选择

分析章节文本，按以下优先级选择模板（→ 详见 `references/guide-questions.md`）：

1. 新角色出场或已有角色反常行为 → Template 1（人物透镜）
2. 环境/感官描写 >40% → Template 2（氛围引擎）
3. 明确叙事转折 → Template 3（结构节点）
4. 暴露核心主题 → Template 4（主题探针）— 全书最多 2 次
5. 以上皆非 → Template 5（平常章）— 最多连续 2 次
6. 强感官描写 ≥3 处 → Template 6（感官暗桩）
7. 叙事声音值得关注 → Template 8（叙事声音）
8. 非线性时间 → Template 9（时间结构）
9. 自由间接引语/意识流 → Template 10（自由间接引语）
10. 重复意象/母题 → Template 11（意象系统）
11. 空间承载象征意义 → Template 12（空间诗学）

**层级轮换**：首章 L1，然后 L2→L3→L1 循环。检查 progress.json.used_thematic_probes 和 consecutive_transitional 约束。

**信号偏置**：如果 progress.json.reader_signals 非空，参考最近信号偏置模板选择（但不强制）。

### 2b. 输出引导问题（必选）

按 `references/guide-questions.md` 中对应模板的格式输出：

> **关键词**：{1-2 个意象词}
>
> **引导问题**：{口语化的问题，不要像考试题}

### 2c. 输出邀请语（必选，紧跟引导问题之后）

> 读到想聊的地方，随时发一句「这里」加你的想法，我会接住。

## Step 3: 等待用户

用户读完章节后，会：
- 用自己的话回答引导问题
- 说"看答案"/"直接看答案"/"跳过" 来跳过
- 发"这里"加想法来讨论某个片段

## Step 4: 展示参考回答

### 4a. 三段式参考回答（必选）

```
> 证据：{从本章原文中提取1句关键引文}
> 分析：{基于该证据的分析，100-150字}
> 延伸：{结合外部知识的1句延伸}
```

### 4b. 读后一问（必选）

生成 1 个开放式回顾问题（可跳过但必须输出）。角度轮流切换：
- 人物印象反转
- 最出乎意料的情节
- 哪段描写让你停下来
- 如果换一个视角来写会怎样
- 这一章的高潮真的是你以为的那个吗

格式：
> 读后一问（可跳过）：{问题}

### 4c. 快速回顾测验（必选）

生成 2 道单选题。格式与规则 → 详见 `references/component-quiz.md`

```
> 来两道快问快答（可跳过）：
> 1. [细节/叙事/意象] {问题}
>    A. ...  B. ...  C. ...  D. ...
>    → 正确答案：__。说明：___
> 2. ...
```

### 4d. 进度条（结束时）

格式：`[{第N部名} {进度条}] {N}/{total} 部`

（进度条绘制规则 → `references/component-progress-bar.md`）

## Step 5: 更新状态

以下更新全部**必选**，写入 progress.json：

### 5a. 提取读者信号

如果用户提供了实质性回答（非"跳过"）：
- 分析用户回答，提取阅读兴趣信号
- 追加到 progress.json.reader_signals 数组：
  `{"chapter": N, "signal_type": "emotional_resonance|structural_interest|sensory_sensitivity|character_focus", "detail": "简短描述", "strength": "strong|moderate|weak"}`

### 5b. 扫描新角色

扫描章节文本，识别新出场角色。如有，追加到 progress.json.characters 数组：
`{"name": "角色名", "label": "身份标签", "one-liner": "一句话特征", "first_chapter": N}`

### 5c. 保存章节记录

写入 `output/{book_sha}/chapter-{N}.md`，格式：

```markdown
# 第{N}章：{章节名}

## 引导角度
{模板中文名}

## 关键词
{关键词}

## 引导问题
{问题}

## 你的回答
{用户回答，或"（跳过）"}

## AI 参考
> 证据：...
> 分析：...
> 延伸：...
```

### 5d. 更新计数器

- `current_chapter` → N
- `chapters[N-1].status` → "completed"
- 如果使用了 Template 4：`used_thematic_probes` += 1
- 如果使用了 Template 5：`consecutive_transitional` += 1，否则重置为 0

## Step 6: 下一章

输出：下一章？

（仅此一句，不追问，让用户控制节奏。）
