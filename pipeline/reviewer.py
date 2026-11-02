"""阶段 4：一致性审校。

检查：
- 人名/地名是否前后一致
- 时间线是否矛盾
- 角色性格是否跑偏
- 有没有明显的情节漏洞

输出：Markdown 审校报告（带严重程度分级）
"""
from __future__ import annotations

from .llm import LLMClient

SYSTEM = """你是一位严格的文学编辑。你的任务是找出稿件里的问题，而不是夸奖作者。

要求：
1. 直接输出 Markdown 审校报告
2. 按严重程度分级：🔴 硬伤 / 🟡 建议 / 🟢 细节
3. 每条问题必须指明"在哪一章 / 哪一句"
4. 不要编造问题；没有问题就说"未发现明显问题"
"""


def review(client: LLMClient, novel: dict, outline: dict, chapters: list[str]) -> str:
    chapter_blocks = "\n\n".join(
        f"=== 第 {i + 1} 章 ===\n{text}" for i, text in enumerate(chapters)
    )

    cast = "\n".join(
        f"- {c['name']}（{c.get('role', '')}）"
        for c in outline.get("_characters", {}).get("characters", [])
    )

    user = f"""请审校下面这部小说。

标题：{outline.get('title') or novel['title']}
类型：{novel['genre']}
风格：{novel['style']}

【角色表】
{cast or '（未提供）'}

【全书正文】
{chapter_blocks}

请输出审校报告，包含：
1. 一句话总评
2. 问题清单（分级）
3. 修改建议（针对最严重的 3 个问题）"""

    return client.complete(SYSTEM, user, temperature=0.4).strip()
