# 📖 Novel Pipeline

> 用 AI 从一句话梗概生成完整小说的流水线 —— **大纲 → 角色 → 逐章 → 审校**

一个展示"AI Agent 式工作流"的小项目：把写小说拆成可组合的流水线阶段，每阶段独立可测、可替换、可续跑。

## ✨ 特性

- **四阶段流水线**：大纲 → 角色设定 → 章节生成 → 一致性审校
- **可续跑**：每阶段产出落盘，中断后从断点继续
- **可配置**：题材、风格、章数、每章字数、语气都能在 `config.yaml` 里调
- **多模型支持**：任何 OpenAI 兼容接口（DeepSeek / OpenAI / 本地 Ollama / vLLM）
- **纯 Markdown 输出**：方便直接发布到博客、GitHub Pages

## 🚀 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置（复制模板并填入 API Key）
cp config.example.yaml config.yaml
# 编辑 config.yaml，填入你的 API Key

# 3. 生成小说
python main.py --config config.yaml

# 4. 查看结果
ls output/
```

## 📁 项目结构

```
novel-pipeline/
├── main.py                 # 命令行入口
├── config.example.yaml     # 配置模板
├── requirements.txt
├── pipeline/
│   ├── __init__.py
│   ├── llm.py              # LLM 客户端（OpenAI 兼容）
│   ├── outline.py          # 阶段 1：生成大纲
│   ├── characters.py       # 阶段 2：生成角色设定
│   ├── chapter.py          # 阶段 3：逐章生成
│   ├── reviewer.py         # 阶段 4：一致性审校
│   └── pipeline.py         # 流水线编排
├── output/                 # 生成结果（git 忽略）
└── examples/               # 示例输出
```

## 🔧 配置说明

```yaml
# config.yaml
llm:
  base_url: "https://api.deepseek.com/v1"   # 或 http://localhost:11434/v1
  api_key: "sk-xxxxx"
  model: "deepseek-chat"
  temperature: 0.8

novel:
  title: "星海拾荒者"
  genre: "科幻"
  premise: "一个在废弃空间站捡垃圾的少年，意外唤醒了一台失忆的军用 AI"
  style: "冷峻克制，带一点黑色幽默"
  chapters: 5
  words_per_chapter: 1200
  language: "zh-CN"

pipeline:
  resume: true              # 断点续跑
  output_dir: "output"
```

## 📖 流水线原理

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  ① 大纲生成  │───▶│ ② 角色设定   │───▶│ ③ 逐章生成   │───▶│ ④ 一致性审校 │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     ↓                   ↓                   ↓                   ↓
  outline.json      characters.json    chapter_1..N.md      review.md
```

每个阶段的产物都会落盘，所以：
- 中断后可以 `--resume` 从上次失败的章节继续
- 想改风格只需重跑对应阶段，不用从头来

## 🧪 示例

`examples/` 目录里有一份完整生成的示例（3 章），可以直接看效果。

## 🛠️ 技术栈

- **Python 3.10+**
- **httpx**：异步 HTTP（调 LLM 接口）
- **PyYAML**：配置
- **rich**：终端进度显示
- **tenacity**：API 重试

## 📝 License

MIT

---

> 这个项目是「用 AI（Agent）做一个属于自己的小东西」的一个实例：
> 把大任务拆成小阶段，让每个阶段都能被单独验证 —— 这正是 Agent 工程的核心思路。
