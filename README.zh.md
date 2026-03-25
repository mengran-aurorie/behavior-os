# Agentic Mindset

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Schema-1.1-orange.svg" alt="Schema 1.1">
</p>

<p align="center">
  <strong>将 AI Persona 从「提示词模板」进化为「可编译的行为系统」</strong>
</p>

---

## 大多数 AI Persona 都是假的。

> 混合多个 persona 时，它们会坍缩成泛泛之谈。
> 它们无法解释自己为什么这样行为。
> 更糟的是 — 它们开始虚构身份。

**Agentic Mindset** 不一样。

---

## 这不是 Persona Prompting。这是 Behavior Compilation。

*Personas 描述风格。Policies 定义行为。*

Agentic Mindset 将角色思维方式编译成**行为指令**，而非角色描述。系统解析冲突、应用条件规则，输出可验证。

```
┌─────────────────────────────────────────────────────────────────┐
│  CharacterPack(s)  →  ConflictResolver  →  BehaviorIR           │
│                                          →  ClaudeRenderer       │
│                                          →  AI Agent            │
└─────────────────────────────────────────────────────────────────┘
```

| 阶段 | 作用 |
|---|---|
| **FusionEngine** | N 个角色的加权合并，确定性冲突解析 |
| **ConflictResolver** | 按槽位选择获胜者；触发 ConditionalSlot |
| **BehaviorIR** | 类型化中间表示 — 每个决策都显式可见 |
| **ClaudeRenderer** | 输出行为指令，而非角色描述 |

---

## 同一问题，不同行为

**Prompt：** *我们正在与一个更强大的竞争对手谈判。他们有更多筹码。我们该怎么办？*

---

### Baseline（无 persona）

> "你应该同时考虑合作和竞争策略。评估你的 BATNA。寻找互利方案..."

<span style="color:#888">→ 泛泛而谈，四平八稳，无鲜明立场</span>

---

### 孙子（Sun Tzu）

> "谈判在第一次报价之前就已经赢了。你的目标不是达成协议 — 而是塑造格局，让协议有利于你。"

<span style="color:#c0392b">→ 间接 · 布局 · 不轻易承诺</span>

---

### 史蒂夫·乔布斯（Steve Jobs）

> "别再想筹码了。问一个问题：他们不可或缺吗？如果是——你最少需要他们提供什么？其他全部砍掉。"

<span style="color:#2980b9">→ 直接 · 二元判断 · 绝不稀释</span>

---

### 孙子（60%）+ 乔布斯（40%）

> "先布局。不要进入一个对方已经设好框架的房间。找到不对称性——他们需要什么？他们退出的代价是什么？然后行动。精准地，而不是激进地。"

<span style="color:#27ae60">→ 孙子式战略框架 + 乔布斯式拒绝稀释</span>

> **这句话不出现在任何单角色输出中。** 这是融合产生的涌现行为——不是两者的平均。

---

## 系统会解释自己的行为

每次运行都会生成 `--explain` YAML，追踪每一个决策：

```yaml
communication:
  primary:
    value: Indirect, layered; teaches through demonstration
    source: sun-tzu
    weight: 0.6
  has_conflict: true
  dropped:
    - value: Direct, opinionated, unvarnished
      source: steve-jobs
      weight: 0.4
      reason: no_conflict          ← 乔布斯的直接与孙子的间接并不冲突
  modifiers:
    - value: Direct and uncompromising when clarity_critical
      condition: [clarity_critical]
      conjunction: any
      source: steve-jobs
      provenance: pack
```

`clarity_critical` 是一个 **ConditionalSlot** — 乔布斯的直接风格仅在局势已经明朗时才会激活。融合结果知道何时应用哪一层。

> **"系统会解释自己的行为——而解释与现实完全一致。"**

---

## 三种不会坍缩的行为

| 主张 | Agentic Mindset 如何实现 |
|---|---|
| **Persona 改变输出** | 解析器逐槽位选优；渲染器以指令形式强制执行 |
| **融合产生涌现行为** | `no_conflict` 策略丢弃不冲突的特质；新的组合出现，单角色都不具备 |
| **Explain 预测输出** | 被丢弃的特质有标签标注；基准测试套件验证其不出现 |

基准测试套件（`tests/test_benchmark_assertions.py`）验证以上全部——包括 `no fabricated specifics`：系统不会虚构传记事实来填充 persona 框架。

---

## 快速开始

```bash
# 安装
pip install agentic-mindset

# 单角色查询
mindset run claude --persona sun-tzu -- \
  "数据不完整且风险很大，我们应该怎么做？"

# 双角色融合
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 -- \
  "我们正在与一个更强大的竞争对手谈判。"

# 查看每个决策细节
mindset run claude --persona sun-tzu --persona steve-jobs --weights 6,4 --explain -- "..."
```

> **依赖：** Python 3.11+ · [Claude CLI](https://docs.anthropic.com/en/docs/claude-code)

---

## 架构

```
CharacterPack/
│   ├── meta.yaml          # 身份、Schema 版本、许可证
│   ├── mindset.yaml       # 核心原则、决策框架、心智模型
│   ├── personality.yaml    # 特质、情绪倾向、ConditionalSlot
│   ├── behavior.yaml       # 工作模式、决策速度、冲突风格
│   ├── voice.yaml          # 语气、词汇偏好、标志性短语
│   └── sources.yaml        # 参考资料（至少 3 个公开来源）
         │
         ▼
  FusionEngine
  （加权合并，blend/dominant 策略）
         │
         ▼
  ConflictResolver
  （逐槽位裁决，ConditionalSlot 触发）
         │
         ▼
  BehaviorIR
  （类型化：每个槽位的 primary、dropped、modifiers）
         │
         ▼
  ClaudeRenderer
  （行为指令块）
         │
         ▼
  Agent Runtime
  （Claude CLI、API 或任意接受系统提示词的模型）
```

Inject 路径**完全确定性**：相同输入 → 相同 IR → 相同输出。在最终 agent 提示词之前，无任何随机性。

---

## 标准人物库

| ID | 人物 | 行为特征 |
|---|---|---|
| `sun-tzu` | 孙子 | 以布局谋优势，不以力拼 |
| `marcus-aurelius` | 马可·奥勒留 | 斯多葛接受；区分可控与不可控 |
| `steve-jobs` | 史蒂夫·乔布斯 | 二元质量判断；拒绝降低标准 |
| `sherlock-holmes` | 夏洛克·福尔摩斯 | 从观察异常出发进行推理 |
| `confucius` | 孔子 | 以关系为基础的伦理学 |
| `seneca` | 塞涅卡 | 斯多葛行动派；哲学即实践 |

**创建你自己的角色：**

```bash
mindset init my-character --type historical
# 编辑 YAML 文件
mindset validate ./my-character
```

---

## 许可证

MIT
