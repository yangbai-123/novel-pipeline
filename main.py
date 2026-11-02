#!/usr/bin/env python3
"""Novel Pipeline 命令行入口。

用法：
    python main.py                        # 读 config.yaml
    python main.py --config my.yaml       # 指定配置
    python main.py --dry-run              # 只校验配置，不调用 API
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("缺少依赖：pip install PyYAML", file=sys.stderr)
    raise SystemExit(1)

from pipeline import Pipeline


def load_config(path: Path) -> dict:
    if not path.exists():
        print(f"配置文件不存在：{path}", file=sys.stderr)
        print("提示：先复制 config.example.yaml 为 config.yaml 并填入 API Key", file=sys.stderr)
        raise SystemExit(1)
    with path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    # 基础校验
    missing = []
    for section, keys in {
        "llm": ["base_url", "api_key", "model"],
        "novel": ["title", "genre", "premise", "style", "chapters", "words_per_chapter"],
    }.items():
        if section not in cfg:
            missing.append(section)
            continue
        for k in keys:
            if not cfg[section].get(k):
                missing.append(f"{section}.{k}")
    if missing:
        print("配置缺少字段：" + ", ".join(missing), file=sys.stderr)
        raise SystemExit(1)

    if "your-key-here" in str(cfg["llm"]["api_key"]):
        print("⚠️  API Key 还是模板占位符，请填入真实 Key", file=sys.stderr)
        raise SystemExit(1)

    return cfg


def main() -> int:
    parser = argparse.ArgumentParser(description="AI 小说生成流水线")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--dry-run", action="store_true", help="只校验配置")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))

    if args.dry_run:
        print("✅ 配置校验通过")
        print(f"   书名：{cfg['novel']['title']}")
        print(f"   章数：{cfg['novel']['chapters']}")
        print(f"   模型：{cfg['llm']['model']} @ {cfg['llm']['base_url']}")
        return 0

    pipeline = Pipeline(cfg)
    pipeline.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
