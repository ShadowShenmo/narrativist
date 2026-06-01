# 进度条

> 用途：各组/各章开始和结束时展示阅读进度 | 被引用：mode-standard-chapter, mode-grouped-epic, mode-anthology, mode-library

## 通用规则

- 进度条使用 █ 和 ░ 字符（20 格）
- 精确到组/章级别，不按字符数微调
- 百分比向下取整
- 已完成格数 = floor(N / total * 20)

## 各模式格式

### Standard Chapter Mode

```
[{第N部名} {████░░░░░░░░░░░░░░░░}] {N}/{total} 部
```

### Grouped Epic Mode

```
[{第N部名} {████░░░░░░░░░░░░░░░░}] {N}/{total} 部
```

### Anthology Mode

```
[{篇名} {N}/{total} 篇] — {合集名}·{辑名}
```

### Library Mode

```
[{合集名} {N}/{total} 本] | {书名}（{类型}·{部数}部）→ 开始
```
