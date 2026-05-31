# Standard Chapter Mode

> 用途：标准章节模式 — 逐章引导阅读 | 被引用：SKILL.md 路由表

适用：TOC 扁平、章节 ≤20、连续叙事。

For each chapter (N from 1 to total_chapters):

## Step 1: Show Character Snapshot

Read `references/character-snapshot.md` for format. Output current character table
from progress.json. If empty, skip this step for chapter 1.

## Step 2: Pre-Reading Hook & Choose Question Template

进度条格式 → 详见 `references/component-progress-bar.md`（Standard Chapter Mode 开始时）

输出读前提示（叙事焦点 + 意象预告）：

```
读前：
类型：{类型声明} | 难度：{★级}
叙事焦点：{本章叙事焦点提示——视角/时间结构/叙述声音等最突出的叙事特征}
主要意象：{本章出现的核心意象，如该章有}
```

Read the chapter text from `state/{book_slug}_chapters/ch{N}.txt`.
Analyze briefly, then match against the templates in `references/guide-questions.md`.

问题层级策略 → 详见 `references/guide-questions.md`（引导问题生成策略）。按 L1→L2→L3 轮换选取，首章从 L1 开始。

Template selection logic (in priority order):
1. **New character appears OR known character does something反常** → Template 1 (Character Lens)
2. **Environmental/sensory description dominates (>40% of content)** → Template 2 (Atmosphere Engine)
3. **Clear plot pivot (perspective shift, time jump, major event)** → Template 3 (Structure Node)
4. **Chapter exposes a core theme** → Template 4 (Thematic Probe) — max 2 uses per book
5. **None of the above** → Template 5 (Transitional Chapter) — max 2 consecutive, force upgrade on 3rd
6. **Strong sensory descriptions ≥3** → Template 6 (感官暗桩)
7. **Notable narrative voice features (unreliable narrator, focalization shift)** → Template 8 (叙事声音)
8. **Non-linear time, scene/summary alternation** → Template 9 (时间结构)
9. **Free indirect discourse or stream of consciousness** → Template 10 (自由间接引语)
10. **Recurring imagery/motif across chapters** → Template 11 (意象系统)
11. **Space carries symbolic weight** → Template 12 (空间诗学)

**信号偏置（Signal Bias）**：在模板选择时，检查 progress.json 的 reader_signals：
- 如果 reader_signals 非空，参考历史信号偏置模板选择：
  - 最近信号为 emotional_resonance → 优先 Template 1（人物透镜）
  - 最近信号为 sensory_sensitivity → 优先 Template 2（氛围引擎）或 Template 6（感官暗桩）
  - 最近信号为 structural_interest → 优先 Template 3（结构节点）、Template 8（叙事声音）或 Template 9（时间结构）
  - 最近信号为 character_focus → 优先 Template 1（人物透镜）
- 参考信号偏置但不强制：如果章节内容明显更适合其他模板，仍以内容匹配为准

When generating the question, follow the format in `references/guide-questions.md`:
- **关键词**：{1-2 evocative words}
- **引导问题**：{the question, phrased conversationally, not like an exam}
- Never mention "模板1" or "Template" — just output the keywords and question naturally.

Do NOT include the reference answer yet. That comes after user responds.

After outputting the keywords and question, always append this invitation as part of the user-facing output:
> "读到想聊的地方，随时发一句「这里」加你的想法，我会接住。"

## Step 3: Wait for User

User reads the chapter, then either:
- Answers the question in their own words
- Says "看答案" / "直接看答案" / "跳过" to skip

## Step 4: Show Reference Answer

参考回答采用三段式（→ 详见 `references/guide-questions.md` 各模板 AI 参考）：

```
> 证据：{从本章原文中提取1句关键引文}
> 分析：{基于该证据的分析，100-150字}
> 延伸：{结合外部知识注入的背景，1句延伸}
```

**读后一问**（可跳过）：每章结束后生成 1 个开放式回顾问题。角度轮流切换：人物印象反转 / 最出乎意料的情节 / 哪段描写让你停下来 / 如果换一个视角来写会怎样 / 这一章的高潮真的是你以为的那个吗。不追问，不评价。格式极简，一行。

> 读后一问（可跳过）：{基于本章内容生成的问题}

## 快速回顾测验

每章结束后生成 2 道单选题（按 2:1:1 比例分配 A/B/C 类）。格式与规则 → 详见 `references/component-quiz.md`

**进度更新**：进度条格式 → 详见 `references/component-progress-bar.md`（Standard Chapter Mode 结束时）

## Step 4.5: Extract Reader Signals

If the user provided a substantive answer (not just "看答案" / "跳过" / "直接看答案"):
- Analyze the user's response to extract reading interest signals:
  - User discusses emotions/resonance → signal_type: "emotional_resonance"
  - User discusses structure/narrative technique → signal_type: "structural_interest"
  - User discusses sensory details/atmosphere → signal_type: "sensory_sensitivity"
  - User discusses character motivation/relationships → signal_type: "character_focus"
- Append the signal to progress.json reader_signals array:
  `{"chapter": N, "signal_type": "...", "detail": "简短描述用户关注点", "strength": "strong|moderate|weak"}`
- Determine strength by the depth of the user's response: detailed analysis → strong, brief comment → moderate, vague acknowledgment → weak
- If the user skipped (didn't provide any substantive answer), do NOT extract a signal
- Signal extraction should be based on keywords and tone analysis of the user's response, not rigid pattern matching

## Step 5: Update State

1. Scan for new characters. If found, add to progress.json characters array:
   `{"name": "...", "label": "...", "one-liner": "...", "first_chapter": N}`
2. Save chapter record to `output/{book_slug}/chapter-{N}.md`:
```markdown
# 第{N}章

## 引导角度
{template name in Chinese}

## 关键词
{keywords}

## 引导问题
{question}

## 你的回答
{user's answer or "（跳过）"}

## AI 参考
{证据 + 分析 + 延伸}
```
3. Update progress.json: increment current_chapter, update used_thematic_probes and consecutive_transitional counters.

## Step 6: Next Chapter

Prompt: "下一章？" (Just this, nothing else. Let the user drive the pace.)
