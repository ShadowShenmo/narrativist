# 进度条

> 用途：展示阅读进度 | 被引用：SKILL.md

## 格式

```
📖 {当前单元}/{总单元数}「{单元标题}」
```

## 规则

- 单元数从 unit_plan.json 的 total_units 读取
- 单元标题从 unit_plan.json 的 units[current_unit].title 读取
- Library 模式额外展示：`（{书名} · {书序}/{总书数}）`
