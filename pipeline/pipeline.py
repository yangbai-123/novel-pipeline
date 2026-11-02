"""流水线编排：串联四个阶段，负责落盘与断点续跑。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import chapter as chapter_mod
from . import characters as characters_mod
from . import outline as outline_mod
from . import reviewer as reviewer_mod
from .llm import LLMClient

console = Console()


class Pipeline:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg
        self.novel = cfg["novel"]
        self.out_dir = Path(cfg.get("pipeline", {}).get("output_dir", "output"))
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.resume = bool(cfg.get("pipeline", {}).get("resume", True))

        llm_cfg = cfg["llm"]
        self.client = LLMClient(
            base_url=llm_cfg["base_url"],
            api_key=llm_cfg["api_key"],
            model=llm_cfg["model"],
            temperature=float(llm_cfg.get("temperature", 0.8)),
            max_tokens=int(llm_cfg.get("max_tokens", 4000)),
            timeout=int(llm_cfg.get("timeout", 120)),
        )

    # ── 落盘工具 ──
    def _path(self, name: str) -> Path:
        return self.out_dir / name

    def _read_json(self, name: str) -> Any | None:
        p = self._path(name)
        if self.resume and p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
        return None

    def _write_json(self, name: str, data: Any) -> None:
        self._path(name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _read_text(self, name: str) -> str | None:
        p = self._path(name)
        if self.resume and p.exists():
            return p.read_text(encoding="utf-8")
        return None

    def _write_text(self, name: str, text: str) -> None:
        self._path(name).write_text(text, encoding="utf-8")

    # ── 主流程 ──
    def run(self) -> None:
        console.rule(f"[bold cyan]📖 {self.novel['title']}")

        # ① 大纲
        outline = self._read_json("outline.json")
        if outline is None:
            with console.status("[yellow]① 生成大纲..."):
                outline = outline_mod.build_outline(self.client, self.novel)
            self._write_json("outline.json", outline)
            console.print("[green]✅ 大纲已生成[/green]")
        else:
            console.print("[dim]⏭️  大纲已存在，跳过[/dim]")

        # ② 角色
        chars = self._read_json("characters.json")
        if chars is None:
            with console.status("[yellow]② 设计角色..."):
                chars = characters_mod.build_characters(self.client, self.novel, outline)
            self._write_json("characters.json", chars)
            console.print("[green]✅ 角色已生成[/green]")
        else:
            console.print("[dim]⏭️  角色已存在，跳过[/dim]")

        # ③ 逐章生成
        n = int(self.novel["chapters"])
        chapter_texts: list[str] = []
        chapter_summaries: list[str] = []
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task("③ 生成章节...", total=n)
            for i in range(1, n + 1):
                name = f"chapter_{i:02d}.md"
                existing = self._read_text(name)
                if existing is not None:
                    text = existing
                    progress.update(task, description=f"③ 第 {i}/{n} 章（已存在）")
                else:
                    text = chapter_mod.build_chapter(
                        self.client, self.novel, outline, chars, i, chapter_summaries
                    )
                    self._write_text(name, f"# 第 {i} 章　{outline['chapters'][i-1].get('title', '')}\n\n{text}\n")
                    progress.update(task, description=f"③ 第 {i}/{n} 章")
                chapter_texts.append(text)
                # 生成摘要供下一章用（避免把全文塞进上下文）
                chapter_summaries.append(
                    f"第 {i} 章《{outline['chapters'][i-1].get('title', '')}》：{outline['chapters'][i-1].get('summary', '')}"
                )
                progress.advance(task)
        console.print("[green]✅ 所有章节已生成[/green]")

        # ④ 审校
        review_name = "review.md"
        review_text = self._read_text(review_name)
        if review_text is None:
            with console.status("[yellow]④ 一致性审校..."):
                outline_with_chars = dict(outline)
                outline_with_chars["_characters"] = chars
                review_text = reviewer_mod.review(self.client, self.novel, outline_with_chars, chapter_texts)
            self._write_text(review_name, f"# 审校报告\n\n{review_text}\n")
            console.print("[green]✅ 审校完成[/green]")
        else:
            console.print("[dim]⏭️  审校已存在，跳过[/dim]")

        # 合并全书
        full = self._compose_full(outline, chapter_texts, review_text)
        self._write_text("full.md", full)

        console.rule("[bold green]🎉 完成")
        console.print(f"输出目录：[cyan]{self.out_dir.resolve()}[/cyan]")
        console.print("  • outline.json     大纲")
        console.print("  • characters.json  角色")
        console.print("  • chapter_XX.md    各章正文")
        console.print("  • review.md        审校报告")
        console.print("  • full.md          合并全书")

    def _compose_full(self, outline: dict, chapters: list[str], review_text: str) -> str:
        parts = [
            f"# {outline.get('title') or self.novel['title']}",
            "",
            f"> {outline.get('logline', self.novel['premise'])}",
            "",
            f"**类型**：{self.novel['genre']}　**主题**：{outline.get('theme', '')}",
            "",
            "---",
            "",
        ]
        for i, text in enumerate(chapters, 1):
            title = outline["chapters"][i - 1].get("title", "")
            parts += [f"## 第 {i} 章　{title}", "", text, "", "---", ""]
        parts += ["## 审校报告", "", review_text, ""]
        return "\n".join(parts)
