"""阶段 1：生成故事大纲。

输出结构（JSON）：
{
  "title": "...",
  "logline": "一句话梗概",
  "theme": "主题",
  "acts": [{"name": "第一幕", "summary": "..."}],
  "chapters": [
    {"index": 1, "title": "...", "summary": "...", "beats": ["...", "..."]}
  ]
}
"""
from __future__ import annotations

from .llm import LLMClient

SYSTEM = """你是一位资深小说策划。你的任务是设计一个结构清晰、张力充足的故事大纲。

要求：
1. 严格输出 JSON，不要任何解释文字、不要 markdown 围栏
2. 章节数必须等于用户要求的数量
3. 每章要有一个"钩子"（读者为什么要翻下一章）
4. 章与章之间要有因果推进，不能是并列的流水账
"""


def build_outline(client: LLMClient, novel: dict) -> dict:
    user = f"""请为下面这部小说设计大纲。

标题：{novel['title']}
类型：{novel['genre']}
核心梗概：{novel['premise']}
风格：{novel['style']}
章数：{novel['chapters']}

请输出如下 JSON 结构（不要多余字段）：
{{
  "title": "最终标题（可以微调）",
  "logline": "一句话梗概（30 字以内）",
  "theme": "主题（10 字以内）",
  "acts": [
    {{"name": "第一幕：xxx", "summary": "这一幕发生什么"}}
  ],
  "chapters": [
    {{
      "index": 1,
      "title": "章节标题",
      "summary": "这一章发生什么（80 字以内）",
      "beats": ["关键情节 1", "关键情节 2"]
    }}
  ]
}}

注意：acts 可以 2-3 幕；chapters 必须正好 {novel['chapters']} 章。"""

    data = client.complete_json(SYSTEM, user)

    # 基本校验 + 补全
    if not isinstance(data, dict):
        raise ValueError(f"大纲格式异常：期望 dict，得到 {type(data).__name__}")
    chapters = data.get("chapters") or []
    if len(chapters) != int(novel["chapters"]):
        # 宽容处理：截断或补空
        if len(chapters) > int(novel["chapters"]):
            data["chapters"] = chapters[: int(novel["chapters"])]
        else:
            for i in range(len(chapters) + 1, int(novel["chapters"]) + 1):
                chapters.append(
                    {"index": i, "title": f"第 {i} 章", "summary": "（待补充）", "beats": []}
                )
            data["chapters"] = chapters
    return data
