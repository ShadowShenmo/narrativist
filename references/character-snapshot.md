---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: af2ae0d909977d8eac6fd5fada00fc05_48c67a135cf011f1a4845254007bceed
    ReservedCode1: oPVol0wcX/gRd7PcKVOFL1FLhAi9l0lQu+mczfaDcL+6tF2hnUGMEch6O8Clp/Ysgy6nCvv1fHZAhLGtG4JFKZHBOPIpWTzLva35QBJnjjvwJy/wNRKjm1W1kDmWiD4Kt90FXmYldPR21hLW6y4pKtEwACS0huziNf9CiXM5G5tqM0Q33hjqRD/ruto=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: af2ae0d909977d8eac6fd5fada00fc05_48c67a135cf011f1a4845254007bceed
    ReservedCode2: oPVol0wcX/gRd7PcKVOFL1FLhAi9l0lQu+mczfaDcL+6tF2hnUGMEch6O8Clp/Ysgy6nCvv1fHZAhLGtG4JFKZHBOPIpWTzLva35QBJnjjvwJy/wNRKjm1W1kDmWiD4Kt90FXmYldPR21hLW6y4pKtEwACS0huziNf9CiXM5G5tqM0Q33hjqRD/ruto=
---

# 人物快照

## 格式规则

人物快照在每章开始前展示，帮读者记住"谁是谁"。只记录**静态身份信息**，绝对不涉及情节发展和人物关系演变。

### 每条记录包含

| 字段 | 说明 | 示例 |
|------|------|------|
| 名字 | 角色名称 | 贾宝玉 |
| 标签 | 一句话身份定位 | 贾府的少年公子 |
| 一句话 | 一个让人记住这个角色的特征点 | 衔玉而生，在脂粉堆里长大的叛逆者 |
| 首次登场 | 第几章 | 第3章 |

### 关系图（可选）

仅在角色之间已经明确建立了静态关系时展示（如家族、国籍、职业组织）。使用简单的缩进结构：

```
贾府
  ├── 贾母（老祖宗）
  ├── 贾政（二房老爷）
  │   ├── 贾宝玉（衔玉而生的公子）
  │   └── 贾环（庶出）
  └── 贾赦（大房老爷）
      └── 贾琏（大爷）
          └── 王熙凤（琏二奶奶，管家媳妇）
```

### 严格禁止

- ❌ 写"后来背叛了XX"——情节关系，禁止
- ❌ 写"最终嫁给XX"——结局信息，禁止
- ❌ 写"其实是反派"——剧透判断，禁止
- ❌ 写"XXX的幕后黑手"——反转信息，禁止
- ✅ 写"XX家族的继承人"——静态身份
- ✅ 写"来自北方的佣兵"——出身背景
- ✅ 写"说话刻薄但眼神温和"——性格特征（不涉及情节推演）

### 展示格式

每章开始时，如果人物列表非空，输出：

```
---
## 👥 已登场人物

| 名字 | 身份 | 记忆点 |
|------|------|--------|
| 贾宝玉 | 贾府少年公子 | 衔玉而生，在脂粉堆里长大 |
| 林黛玉 | 贾母外孙女 | 从苏州来投亲，体弱多病，心思极细 |
| 王熙凤 | 琏二奶奶 | 笑声先于人到，贾府的实权管家 |

（关系图，如果角色 ≥5 人）

---
```

### 更新时机

- 每章读取后扫描是否有新角色
- 新角色 → 添加记录，标注首次登场章节
- 已有角色 → 如果身份信息在本章有明确补充（如"原来是XX的儿子"），更新标签，但**不删除旧的首次登场信息**
- 角色死亡 → 标注 †，但保留记录
*（内容由AI生成，仅供参考）*
