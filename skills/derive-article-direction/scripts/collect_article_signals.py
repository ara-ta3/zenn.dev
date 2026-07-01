#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass
class ArticleSignal:
    path: str
    title: str
    topics: list[str]
    article_type: str
    published: bool | None
    headings: list[str]
    lead: str
    score: int


HEADING_PATTERN = re.compile(r"^(#{1,3})\s+(.*)$")


def strip_inline_comment(value: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(value):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return value[:index].rstrip()
    return value.strip()


def parse_frontmatter_value(value: str):
    trimmed = strip_inline_comment(value).strip()
    if trimmed.startswith("[") and trimmed.endswith("]"):
        inner = trimmed[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip("\"'") for part in inner.split(",")]
    if trimmed.lower() == "true":
        return True
    if trimmed.lower() == "false":
        return False
    return trimmed.strip("\"'")


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    if not text.startswith("---\n"):
        return {}, text

    closing = text.find("\n---\n", 4)
    if closing == -1:
        return {}, text

    raw_frontmatter = text[4:closing]
    body = text[closing + 5 :]
    data: dict[str, object] = {}
    for line in raw_frontmatter.splitlines():
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        data[key.strip()] = parse_frontmatter_value(raw_value)
    return data, body


def extract_headings(body: str, limit: int) -> list[str]:
    headings: list[str] = []
    for line in body.splitlines():
        match = HEADING_PATTERN.match(line.strip())
        if not match:
            continue
        depth = len(match.group(1))
        label = match.group(2).strip()
        headings.append(f"H{depth}: {label}")
        if len(headings) >= limit:
            break
    return headings


def extract_lead(body: str) -> str:
    paragraph: list[str] = []
    in_code_block = False

    for raw_line in body.splitlines():
        line = raw_line.strip()
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if not line:
            if paragraph:
                break
            continue
        if line.startswith("#") or line.startswith(":::") or line.startswith(">"):
            if paragraph:
                break
            continue
        paragraph.append(line)

    return " ".join(paragraph)


def expand_paths(raw_paths: Iterable[str]) -> list[Path]:
    candidates = list(raw_paths) or ["articles", "hashnodes"]
    paths: list[Path] = []
    for raw_path in candidates:
        path = Path(raw_path)
        if path.is_dir():
            paths.extend(sorted(path.rglob("*.md")))
        elif path.is_file():
            paths.append(path)
    seen: set[Path] = set()
    unique_paths: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique_paths.append(path)
    return unique_paths


def compute_score(signal: ArticleSignal, queries: list[str]) -> int:
    if not queries:
        return 0

    haystacks = {
        "title": signal.title.lower(),
        "topics": " ".join(signal.topics).lower(),
        "headings": " ".join(signal.headings).lower(),
        "lead": signal.lead.lower(),
        "path": signal.path.lower(),
    }
    score = 0
    for query in queries:
        term = query.lower()
        if term in haystacks["title"]:
            score += 5
        if term in haystacks["topics"]:
            score += 4
        if term in haystacks["headings"]:
            score += 3
        if term in haystacks["lead"]:
            score += 2
        if term in haystacks["path"]:
            score += 1
    return score


def collect_signals(paths: Iterable[Path], queries: list[str], heading_limit: int) -> list[ArticleSignal]:
    signals: list[ArticleSignal] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(text)
        signal = ArticleSignal(
            path=str(path),
            title=str(frontmatter.get("title", path.stem)),
            topics=[str(topic) for topic in frontmatter.get("topics", [])],
            article_type=str(frontmatter.get("type", "")),
            published=frontmatter.get("published") if isinstance(frontmatter.get("published"), bool) else None,
            headings=extract_headings(body, heading_limit),
            lead=extract_lead(body),
            score=0,
        )
        signal.score = compute_score(signal, queries)
        signals.append(signal)
    return signals


def format_markdown(signals: list[ArticleSignal]) -> str:
    lines: list[str] = []
    for signal in signals:
        topics = ", ".join(signal.topics) if signal.topics else "-"
        headings = " / ".join(signal.headings) if signal.headings else "-"
        published = (
            "true"
            if signal.published is True
            else "false"
            if signal.published is False
            else "unknown"
        )
        lines.extend(
            [
                f"- {signal.title}",
                f"  path: {signal.path}",
                f"  score: {signal.score}",
                f"  topics: {topics}",
                f"  type: {signal.article_type or '-'}",
                f"  published: {published}",
                f"  headings: {headings}",
                f"  lead: {signal.lead or '-'}",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect frontmatter, headings, and lead paragraphs from markdown articles."
    )
    parser.add_argument("paths", nargs="*", help="Markdown files or directories. Defaults to articles/ and hashnodes/.")
    parser.add_argument("--query", action="append", default=[], help="Keyword used for simple relevance scoring.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum number of articles to print.")
    parser.add_argument(
        "--include-unpublished",
        action="store_true",
        help="Include articles with published: false.",
    )
    parser.add_argument(
        "--headings",
        type=int,
        default=6,
        help="Maximum number of headings to capture per file.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format.",
    )
    args = parser.parse_args()

    paths = expand_paths(args.paths)
    signals = collect_signals(paths, args.query, args.headings)
    if not args.include_unpublished:
        signals = [signal for signal in signals if signal.published is not False]

    signals.sort(key=lambda signal: (-signal.score, signal.path))
    limited = signals[: max(args.limit, 0)]

    if args.format == "json":
        print(json.dumps([asdict(signal) for signal in limited], ensure_ascii=False, indent=2))
        return

    print(format_markdown(limited))


if __name__ == "__main__":
    main()
