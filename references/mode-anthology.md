# Anthology Mode

> 用途：合集模式 — 独立短篇集合逐篇微循环 | 被引用：SKILL.md 路由表

适用：序言或内容检测判定为独立短篇集合。目录信息来自 `progress.json.anthology_index`。

**初始化后行为**：
1. 展示完整目录树（按卷分组，含篇名列表）
2. 用户选择单篇 → 该篇独立走微循环
3. 每篇读完存记录，不设跨篇追踪
4. 按卷/按全书做总结时，提炼跨篇共性主题

**单篇微循环**（每篇独立，类似 Standard Chapter Mode 但范围限定为该篇）：

进度条格式 → 详见 `references/component-progress-bar.md`（Anthology Mode）

1. **类型声明（迷你版）**：一句话风格定性 + ★ 难度 + 一句话阅读建议
2. **人物快照（该篇范围）**：扫描该篇文本，识别出场人物，不继承前篇
3. **引导问题**：基于该篇文本生成 1 个引导问题（模板选择同 Standard Chapter Mode，Template 4 限制改为 max 1 use per story）
4. **等待用户**：读完后回答或跳过
5. **参考回答**（三段式：证据 + 分析 + 延伸，→ 详见 `references/guide-questions.md`）+ 读者信号提取（同 Standard Chapter Mode Step 4.5）
6. **读后一问**（可跳过）：1 个开放式回顾问题，格式同 Standard Chapter Mode
7. **快速回顾测验**：每篇结束后 2 道单选题。格式与规则 → 详见 `references/component-quiz.md`
8. **保存记录**：`output/{book_slug}/story-{story_slug}.md`，格式同 chapter record
9. **更新 anthology_index**：`current_story` 指向下一篇，标记已读

**跨篇总结**（用户说"总结"或全部读完时）：
- 已读篇目列表 + 各篇引导角度回顾
- 跨篇共性主题提炼（不依赖跨篇人物追踪，聚焦风格、母题、技法）
- 共性主题从各篇的实际引导角度和读者信号中归纳，不凭空生成
