# Agentic Mindset

<p align="center">
  <a href="./README.md">English</a> | <a href="./README.zh.md">中文</a>
</p>

<p align="center">
  将历史人物和虚构角色的思维方式加载到任意 AI Agent 上 — 即插即用。
</p>

---

## 这是什么？

Agentic Mindset 是一个与语言无关的开源框架，用于构建、管理并将**历史人物**和**虚构角色**的思维方式与性格加载到 AI Agent 上。

你只需定义一个 Character Pack（一个包含结构化 YAML 文件的目录），框架会将一个或多个角色融合成一个 Context Block，注入到任意 Agent 的系统提示词中。

```
孙子（60%）+ 马可·奥勒留（40%）  →  Context Block  →  AI Agent
```

---

## 主要特性

- **Character Pack** — 结构化 YAML 档案，涵盖思维方式、性格、行为、声音风格和来源
- **融合引擎** — 支持加权混合（blend）、主导（dominant）、顺序（sequential）三种策略
- **命令行工具** — `mindset init`、`validate`、`preview`、`list`
- **标准人物库** — 精选历史人物和虚构角色，开箱即用
- **语言无关的核心** — 附带 Python SDK；数据格式适用于任何语言

---

## 安装

```bash
pip install agentic-mindset
```

需要 Python 3.11+。

---

## 快速开始

### 使用标准库中的角色

```python
from agentic_mindset import CharacterRegistry, FusionEngine

engine = FusionEngine(CharacterRegistry())

context = engine.fuse([
    ("sun-tzu", 0.6),
    ("marcus-aurelius", 0.4),
])

system_prompt = context.to_prompt()
# 注入到你的 Agent：
messages = [{"role": "system", "content": system_prompt}, ...]
```

### 通过 CLI 预览

```bash
mindset preview characters/sun-tzu/
mindset preview --fusion examples/sun-tzu-aurelius.yaml
```

---

## Character Pack 结构

每个角色是一个包含六个 YAML 文件的目录：

```
sun-tzu/
├── meta.yaml          # 身份信息、类型、Schema 版本
├── mindset.yaml       # 核心原则、决策框架、心智模型
├── personality.yaml   # 性格特质、情绪倾向、驱动力
├── behavior.yaml      # 工作模式、决策速度、冲突风格
├── voice.yaml         # 语气、词汇偏好、标志性短语
└── sources.yaml       # 来源材料引用
```

创建新角色脚手架：

```bash
mindset init my-character --type historical
```

---

## 融合引擎

通过 `fusion.yaml` 配置文件融合多个角色：

```yaml
characters:
  - id: sun-tzu
    weight: 0.6
  - id: marcus-aurelius
    weight: 0.4

fusion_strategy: blend      # blend | dominant | sequential
output_format: plain_text   # plain_text | xml_tagged
```

```bash
mindset preview --fusion my-blend.yaml
```

### 融合策略说明

| 策略 | 行为 |
|---|---|
| `blend` | 所有属性按权重加权合并 |
| `dominant` | 最高权重角色主导，其他角色补充缺失字段 |
| `sequential` | 按列表顺序依次叠加，忽略权重值 |

---

## 标准人物库

**历史人物：**

| ID | 姓名 | 标签 |
|---|---|---|
| `sun-tzu` | 孙子 | 战略、军事、哲学 |
| `marcus-aurelius` | 马可·奥勒留 | 斯多葛主义、哲学、领导力 |

**虚构角色**（即将推出）：
- `naruto-uzumaki`、`levi-ackermann`、`sherlock-holmes`、`odysseus` 等

---

## CLI 命令参考

```bash
mindset init <id> --type historical|fictional   # 创建新角色脚手架
mindset validate <path>                          # 验证 Schema 合规性
mindset preview <path>                           # 预览 Context Block 输出
mindset preview --fusion <fusion.yaml>           # 预览融合结果
mindset list                                     # 列出可用角色
```

---

## 贡献

欢迎提交历史人物（已故）和虚构角色的 Character Pack。

**要求：**
- `sources.yaml` 中至少 3 个不同的、公开可访问的来源材料
- 五个内容文件齐全，并通过 `mindset validate` 验证
- 不接受在世人物

详见 [CONTRIBUTING.md](./CONTRIBUTING.md)。

---

## 许可证

MIT
