"""阶段 2：生成角色设定。

输出结构（JSON）：
{
  "characters": [
    {
      "name": "...",
      "role": "主角/反派/配角",
      "age": "...",
      "appearance": "...",
      "personality": "...",
      "goal": "...",
      "conflict": "...",
      "arc": "角色弧光（从什么样变成什么样）",
      "voice": "说话风格（用一个短句示例）"
    }
  ]
}
"""
from __future__ import annotations

from .llm import LLMClient

SYSTEM = """你是一位角色设计师。你的任务是为故事设计有血有肉的角色。

要求：
1. 严格输出 JSON，不要解释、不要 markdown 围栏
2. 每个角色必须有"欲望"和"恐惧"——这是驱动行为的引擎
3. 至少一个角色与主角的目标直接冲突
4. 角色的说话风格要能一句话听出来
"""


def build_characters(client: LLMClient, novel: dict, outline: dict) -> dict:
    chapter_summaries = "\n".join(
        f"第 {c['index']} 章《{c['title']}》：{c['summary']}" for c in outline.get("chapters", [])
    )

    user = f"""请为下面这部小说设计角色（3-5 个主要角色）。

标题：{outline.get('title') or novel['title']}
类型：{novel['genre']}
核心梗概：{novel['premise']}
风格：{novel['style']}
主题：{outline.get('theme', '')}

故事大纲：
{chapter_summaries}

请输出如下 JSON（不要多余字段）：
{{
  "characters": [
    {{
      "name": "姓名",
      "role": "主角 | 反派 | 配角",
      "age": "年龄或年龄段",
      "appearance": "外貌（30 字以内）",
      "personality": "性格（30 字以内）",
      "goal": "想要什么",
      "fear": "害怕什么",
      "conflict": "与谁/什么冲突",
      "arc": "角色弧光：从 A 变成 B",
      "voice": "说话风格示例：「一句话」"
    }}
  ]
}}"""

    data = client.complete_json(SYSTEM, user)
    if not isinstance(data, dict) or not data.get("characters"):
        raise ValueError("角色设定格式异常")
    return data
