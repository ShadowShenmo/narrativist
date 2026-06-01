# Library Mode（嵌套合集）

> 用途：图书馆模式 — 多书合集，逐书运行完整流程 | 被引用：SKILL.md 路由表

适用：EPUB 包含多本独立作品（如"理想国精选集9册"）。TOC 结构通常为 L0=书名、L1=章节，或更深层嵌套。

## 数据结构

```
state/{sha}-progress.json           # 主文件：books 列表、current_book、完成状态
state/{sha}_book{N}-progress.json   # 每本书独立状态：chapters、characters、signals
state/chapters/book{N}_ch{M}.txt    # 每本书的章节文本
output/{sha}/book{N}/chapter-{M}.md # 每本书的章节记录（不冲突）
```

## 初始化（阶段一）

```bash
python init_book.py "book.epub"
```

生成主 progress.json：
```json
{
  "mode": "library",
  "books": [
    {"index": 1, "title": "盲视", "type": "multi_chapter", "chapters_count": 6, "status": "pending"},
    {"index": 2, "title": "海边的房间", "type": "multi_chapter", "chapters_count": 15, "status": "pending"}
  ],
  "current_book": 0
}
```

## 图书馆视图

初始化完成后，展示所有书籍列表（含类型、字数），让用户选择。

## 选书后（阶段二）

```bash
python init_book.py "book.epub" --extract N
```

生成该书的独立状态文件 `{sha}_book{N}-progress.json`，不覆盖主文件。

该书按 standard_chapter 模式运行完整章节循环。

## 书完成后

```bash
python init_book.py "book.epub" --complete N
```

标记该书为 completed，更新主 progress.json：
```json
{
  "books": [{"index": 1, "title": "盲视", "status": "completed"}, ...],
  "current_book": 1
}
```

Claude 运行时展示图书馆进度，提示下一本。

## 书间导航

当一本书的所有章节完成后（current_chapter == total_chapters）：

1. 调用 `--complete N` 标记完成
2. 展示图书馆进度：`[精选集 ████████░░░░░░░░░░░░] 1/9 本`
3. 提示："下一本？" 或展示剩余书单
4. 用户选择后调用 `--extract M` 提取下一本
5. 重复直到所有书完成

## 最终总结

所有书完成后，触发 Final Summary：
- 汇总所有书的 chapter-{M}.md 记录
- 跨书人物长廊（从各书的 characters 合并）
- 跨书主题脉络
- 阅读感想留白

## 跨书总结

当用户读完一本书并完成总结后：
1. 展示图书馆进度："你已经读了 3/9 本"
2. 可选择进入跨书总结：
   - 同一作家读完 ≥2 本 → 提炼作家风格共性
   - 读完整个合集 → 全集总结
3. 跨书总结格式：
   - 作家印象：你在这些书里反复被打动的点
   - 下一本推荐：合集内未读的、与已读偏好最匹配的
