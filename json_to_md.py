#!/usr/bin/env python3

# Example usage:
# python json_to_md.py "/Users/username/audibleextractor/audiobooks/hold_on_to_your_kids/trancribed_clips/contents.json"

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Set


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract unique 'text' values from a JSON list and write a Markdown bullet list, ordered by 'position_seconds'."
    )
    parser.add_argument(
        "json_path",
        help="Path to the input JSON file (e.g., contents.json)."
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional path for the output .md file. Defaults to the same base name as the input JSON with a .md extension in the same directory."
    )
    return parser.parse_args()


def load_items(json_file: Path) -> List[Dict[str, Any]]:
    with json_file.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected top-level JSON array (list) of objects.")
    return [item for item in data if isinstance(item, dict)]


def get_position_seconds(item: Dict[str, Any]) -> float:
    value = item.get("position_seconds")
    if value is None:
        return float("inf")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("inf")


def normalize_text_key(value: str) -> str:
    """Return a normalized key for deduplication.

    - Unicode-normalize to NFKC
    - Lowercase
    - Remove punctuation/special chars (keep letters, digits, whitespace)
    - Collapse consecutive whitespace
    """
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.lower()
    normalized = re.sub(r"[^\w\s]", " ", normalized, flags=re.UNICODE)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def extract_unique_texts_sorted(items: List[Dict[str, Any]]) -> List[str]:
    sorted_items = sorted(items, key=get_position_seconds)
    seen_keys: Set[str] = set()
    unique_texts: List[str] = []
    for item in sorted_items:
        text = item.get("text")
        if not isinstance(text, str):
            continue
        cleaned = text.strip()
        # Ensure single line output: replace any newlines/tabs with single spaces and collapse whitespace
        cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            continue
        key = normalize_text_key(cleaned)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_texts.append(cleaned)
    return unique_texts


def write_markdown(output_file: Path, texts: List[str]) -> None:
    lines = [f"- {t}" for t in texts]
    content = "\n".join(lines) + "\n"
    output_file.write_text(content, encoding="utf-8")


def main() -> None:
    args = parse_arguments()
    input_path = Path(args.json_path).expanduser()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    try:
        items = load_items(input_path)
    except json.JSONDecodeError as e:
        raise SystemExit(f"Failed to parse JSON: {e}")
    except ValueError as e:
        raise SystemExit(str(e))

    texts = extract_unique_texts_sorted(items)

    output_path = Path(args.output).expanduser() if args.output else input_path.with_suffix(".md")
    write_markdown(output_path, texts)
    print(f"Wrote {len(texts)} bullet(s) to: {output_path}")


if __name__ == "__main__":
    main()


