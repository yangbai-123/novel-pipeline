"""阶段 3：逐章生成正文。

策略：
- 每章调用一次 LLM，输入包含：全书大纲 + 角色卡 + 前面章节的摘要（不是全文，省 token）
- 输出纯 Markdown 文本
- 保证"上一章结尾"和"这一章开头"连续
"""
from __future__ import annotations

from .llm import LLMClient

SYSTEM = """你是一位小说家。你的任务是根据大纲和角色设定，写出具体的章节正文。

写作要求：
1. 直接输出正文，不要标题、不要"第 X 章"、不要任何解释
2. 用 Markdown 段落，对话用中文引号「」
3. 场景要有五感细节（不只是视觉）
4. 对话要有潜台词，不要让人物把话说透
5. 章节结尾要留钩子
6. 严格遵守给定的字数（允许 ±20%）
"""


def build_chapter(
    client: LLMClient,
    novel: dict,
    outline: dict,
    characters: dict,
    chapter_index: int,
    previous_summaries: list[str],
) -> str:
    """生成第 chapter_index 章（1-based）。"""
    chapters = outline.get("chapters", [])
    if chapter_index < 1 or chapter_index > len(chapters):
        raise IndexError(f"章节索引越界：{chapter_index}（共 {len(chapters)} 章）")
    this_chapter = chapters[chapter_index - 1]

    cast = "\n".join(
        f"- {c['name']}（{c.get('role', '')}）：{c.get('personality', '')}；"
        f"目标：{c.get('goal', '')}；语气：{c.get('voice', '')}"
        for c in characters.get("characters", [])
    )

    prev_text = "\n".join(previous_summaries) if previous_summaries else "（这是第一章）"

    user = f"""请写《{outline.get('title') or novel['title']}》的第 {chapter_index} 章。

类型：{novel['genre']}
风格：{novel['style']}
主题：{outline.get('theme', '')}

【角色】
{cast}

【已发生的情节（前情摘要）】
{prev_text}

【本章大纲】
标题：{this_chapter.get('title', '')}
梗概：{this_chapter.get('summary', '')}
关键节拍：
{chr(10).join('- ' + b for b in this_chapter.get('beats', [])) or '（无）'}

【要求】
- 字数约 {novel['words_per_chapter']} 字
- 直接输出正文，不要章节标题
- 结尾留一个让人想继续读的钩子"""

    return client.complete(SYSTEM, user, temperature=0.9).strip()
