# 进度条

> 用途：各组/各章开始和结束时展示阅读进度 | 被引用：mode-standard-chapter, mode-grouped-epic, mode-anthology, mode-library

## 通用规则

- 进度条使用 █ 和 ░ 字符
- 精确到组/章级别，不按字符数微调
- 百分比向下取整
- 字数统计从 reading_schedule 中取

## 各模式格式

### Standard Chapter Mode

开始时：
```
[{第N章} ██████████░░░░░░░░░░] {N}/{total} 章 | 已读 {X.X}万/{Y.Y}万字 | 预计还需 {Z} 周
```

结束时（测验之后）：
```
[{第N章} ██████████░░░░░░░░░░] {N}/{total} 章 | 已完成 {percent}%
```

### Grouped Epic Mode

开始时：
```
[{第N部} ██████████░░░░░░░░░░] {N}/{total} 部 | 已读 {X.X}万/{Y.Y}万字 | 预计还需 {Z} 周
```

结束时：
```
[{第N部} ██████████░░░░░░░░░░] {N}/{total} 部 | 已完成 {percent}%
```

### Anthology Mode

```
[{篇名} {N}/{total} 篇] — {合集名}·{辑名}
```

### Library Mode

```
[{合集名} {N}/{total} 本] | {书名}（{类型}·{部数}部）→ 开始
```
