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
- **命令行工具** — `mindset init`、`validate`、`preview`、`list`、`generate`、`run`
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

## mindset generate — 编译与注入

`mindset generate` 将一个或多个角色的思维方式编译成可注入的系统提示词块。纯编译器：确定性输出，无网络请求。

### 单角色

```bash
mindset generate sun-tzu
```

### 多角色融合（带权重）

```bash
# 权重自动归一化（6,4 → 60%、40%）
mindset generate sun-tzu marcus-aurelius --weights 6,4
```

### 输出格式

```bash
# 纯文本（默认）— 直接粘贴到任意系统提示词
mindset generate sun-tzu

# Anthropic API content block — 可直接追加到 system 数组
mindset generate sun-tzu --format anthropic-json

# 带元数据的 debug JSON
mindset generate sun-tzu marcus-aurelius --weights 6,4 --format debug-json
```

### 融合策略

```bash
mindset generate sun-tzu marcus-aurelius --strategy blend       # 默认
mindset generate sun-tzu marcus-aurelius --strategy dominant
```

### 其他选项

```bash
--explain          # 将结构化 YAML 打印到 stderr（包含 personas、merged 决策策略、removed_conflicts）
--output <path>    # 输出到文件而非 stdout
--registry <path>  # 覆盖角色注册表路径
```

### `--explain` 输出示例

```yaml
personas:
- sun-tzu: 0.6
- marcus-aurelius: 0.4
merged:
  decision_policy: sun-tzu-dominant
  risk_tolerance: high
  time_horizon: long-term
removed_conflicts:
- 'Precision (intensity 0.95): ...'
```

### Python 集成示例（Anthropic API）

```python
import anthropic, subprocess, json

block = json.loads(subprocess.run(
    ["mindset", "generate", "sun-tzu", "--format", "anthropic-json"],
    capture_output=True, text=True
).stdout)

client = anthropic.Anthropic()
resp = client.messages.create(
    model="claude-opus-4-6",
    max_tokens=1024,
    system=[
        {"type": "text", "text": "你是我的助手。"},
        block,   # 注入的思维方式
    ],
    messages=[{"role": "user", "content": "我该如何处理这次谈判？"}]
)
print(resp.content[0].text)
```

---

## Character Pack 结构

每个角色是一个包含六个 YAML 文件的目录：

```
sun-tzu/
├── meta.yaml          # 身份信息、类型、Schema 版本
├── mindset.yaml       # 核心原则、决策框架、心智模型
├── personality.yaml   # 性格特质、情绪倾向、驱动力
├── behavior.yaml      # 工作模式、决策速度、冲突风格（可选：anti_patterns 反模式列表）
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
| `sequential` | 按列表顺序依次叠加，忽略权重值（仅 preview 支持；`generate` v0 不支持） |

---

## 标准人物库

**历史人物：**

| ID | 姓名 | 标签 |
|---|---|---|
| `sun-tzu` | 孙子 | 战略、军事、哲学 |
| `marcus-aurelius` | 马可·奥勒留 | 斯多葛主义、哲学、领导力 |
| `confucius` | 孔子 | 哲学、伦理、教育 |
| `seneca` | 塞涅卡 | 斯多葛主义、哲学、写作 |
| `nikola-tesla` | 尼古拉·特斯拉 | 科学、发明、工程 |
| `napoleon-bonaparte` | 拿破仑·波拿巴 | 战略、领导力、军事 |
| `leonardo-da-vinci` | 列奥纳多·达·芬奇 | 创造力、科学、艺术 |

**虚构角色：**

| ID | 姓名 | 标签 |
|---|---|---|
| `sherlock-holmes` | 夏洛克·福尔摩斯 | 推理、逻辑、观察 |
| `odysseus` | 奥德修斯 | 战略、韧性、智谋 |
| `atticus-finch` | 阿提克斯·芬奇 | 正义、诚信、同理心 |
| `naruto-uzumaki` | 漩涡鸣人 | 坚持、成长、领导力 |
| `levi-ackermann` | 利威尔·阿克曼 | 纪律、精准、责任感 |
| `gojo-satoru` | 五条悟 | 自信、极致、创造力 |

---

## mindset run — 编译并注入 Claude

`mindset run` 将思维方式编译后，通过 `--append-system-prompt-file` 直接注入 Claude CLI 会话。

```bash
# 单次查询
mindset run claude --persona sun-tzu -- "分析竞争对手策略"

# 多角色融合（带权重）
mindset run claude --persona sun-tzu --persona marcus-aurelius --weights 6,4 -- "如何处理这次谈判？"

# 交互模式（省略 -- QUERY）
mindset run claude --persona sun-tzu

# 启动前打印结构化 YAML 摘要
mindset run claude --persona sun-tzu --explain -- "query"
```

### inject 格式

默认 `--format inject` 生成**行为指令块** — 对 Agent 的具体行为指令，而非角色描述：

```
You embody a synthesized mindset drawing from: Sun Tzu (100%).

DECISION POLICY:
- Strategic deception: Misdirect before committing.
- Approach: Win before the battle begins.

UNCERTAINTY HANDLING:
- risk_tolerance: high | time_horizon: long-term
- Stress response: retreat to preparation, reassess terrain.

INTERACTION RULES:
- Communication: indirect, layered
- Leadership: leads through positioning
- Under conflict: avoidant of direct confrontation

STYLE:
- Tone: measured, aphoristic
- Preferred: position, terrain, advantage
- Avoided: rush, obvious
- Sentence style: short aphorisms
```

使用 `--format text` 可获得原有的角色描述格式。

### `mindset run` 选项

| 选项 | 默认值 | 说明 |
|---|---|---|
| `<runtime>` | 必填 | 运行时名称（v0：仅支持 `claude`） |
| `--persona` | 必填 | 角色 ID，可重复使用以指定多个角色 |
| `--weights 6,4` | 等权重 | 各角色权重（自动归一化） |
| `--strategy` | `blend` | `blend` \| `dominant` |
| `--format` | `inject` | `inject`（行为指令块）\| `text`（角色描述） |
| `--explain` | 关闭 | 将结构化 YAML 打印到 stderr |
| `--registry <path>` | 自动解析 | 覆盖角色注册表路径 |
| `-- QUERY` | 无 | 单次查询内容，省略则进入交互模式 |

---

## CLI 命令参考

```bash
mindset init <id> --type historical|fictional    # 创建新角色脚手架
mindset validate <path>                          # 验证 Schema 合规性
mindset preview <path>                           # 预览 Context Block 输出
mindset preview --fusion <fusion.yaml>           # 预览融合结果
mindset list                                     # 列出可用角色
mindset generate <id> [id ...]                   # 将思维方式编译成可注入的提示词块
mindset run <runtime> --persona <id>             # 编译并注入到 Agent 运行时
```

### `mindset generate` 选项

| 选项 | 默认值 | 说明 |
|---|---|---|
| `--weights 6,4` | 等权重 | 各角色权重（自动归一化） |
| `--strategy` | `blend` | `blend` \| `dominant` |
| `--format` | `text` | `text` \| `anthropic-json` \| `debug-json` |
| `--output <path>` | stdout | 输出到文件而非 stdout |
| `--explain` | 关闭 | 将结构化 YAML 打印到 stderr |
| `--registry <path>` | 自动解析 | 覆盖角色注册表路径 |

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
