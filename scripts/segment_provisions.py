#!/usr/bin/env python3
"""
Segment normalized layout JSON into provision-sized chunks using heading heuristics.
This is a structural pass: it groups blocks/tables into provision candidates with provenance.
See docs/segmentation_design.md for intent and docs/layout_schema.md for input shape.
"""

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List


HEADING_PATTERNS = [
    re.compile(r"^ARTICLE\b", re.IGNORECASE),
    re.compile(r"^\d+(\.\d+)*\b"),  # numbered sections like 3, 3.1, 3.1(a)
    re.compile(r"^Section\b", re.IGNORECASE),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Segment layout JSON into provision candidates.")
    parser.add_argument("--input", required=True, help="Path to normalized layout JSON (full text).")
    parser.add_argument("--out", required=True, help="Output path for provision JSON.")
    parser.add_argument(
        "--toc-pages",
        type=int,
        default=2,
        help="Number of initial pages to treat as TOC and skip content grouping.",
    )
    return parser.parse_args()


def is_heading(block: Dict[str, Any]) -> bool:
    text = (block.get("text") or "").strip()
    btype = (block.get("type") or "").lower()
    if btype in {"title", "sectionheading", "heading"}:
        return True
    return any(pat.search(text) for pat in HEADING_PATTERNS)


def flatten_blocks(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for section in sections:
        blocks.extend(section.get("blocks", []))
    return sorted(blocks, key=lambda b: (b.get("page") or 0, b.get("bbox") or [0, 0, 0, 0]))


def collect_tables(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tables: List[Dict[str, Any]] = []
    for section in sections:
        tables.extend(section.get("tables", []))
    return tables


def provision_id(doc_id: str, idx: int, heading_text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", heading_text.strip()).strip("_").lower() or f"section_{idx}"
    return f"{doc_id}:{idx:04d}:{slug}"


def segment(layout: Dict[str, Any], toc_pages: int) -> List[Dict[str, Any]]:
    doc_id = layout.get("document_id") or Path(layout.get("file_name", "")).stem
    sections = layout.get("sections", [])
    blocks = [b for b in flatten_blocks(sections) if (b.get("page") or 0) > toc_pages]
    tables = collect_tables(sections)

    provisions: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}
    for blk in blocks:
        if is_heading(blk):
            if current:
                provisions.append(current)
            current = {
                "provision_id": provision_id(doc_id, len(provisions) + 1, blk.get("text", "")),
                "title": blk.get("text"),
                "doc_id": doc_id,
                "breadcrumbs": [blk.get("text")],
                "page_range": [blk.get("page"), blk.get("page")],
                "blocks": [],
                "tables": [],
                "provenance": {
                    "section": blk.get("text"),
                    "page_range": [blk.get("page"), blk.get("page")],
                },
            }
        else:
            if not current:
                # Skip content before first heading after TOC
                continue
            current["blocks"].append(blk)
            page = blk.get("page")
            if page and current.get("page_range"):
                current["page_range"][1] = max(current["page_range"][1], page)

    if current:
        provisions.append(current)

    # Attach tables by page overlap
    for tbl in tables:
        pr = tbl.get("page_range")
        if not pr:
            continue
        for prov in provisions:
            ppr = prov.get("page_range")
            if ppr and pr[0] <= ppr[1] and pr[1] >= ppr[0]:
                prov.setdefault("tables", []).append(tbl)
                break

    return provisions


def main():
    args = parse_args()
    layout_path = Path(args.input)
    data = json.loads(layout_path.read_text())
    provisions = segment(data, toc_pages=args.toc_pages)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"provisions": provisions, "source_layout": layout_path.name}, indent=2))
    print(f"Wrote {len(provisions)} provisions to {out_path}")


if __name__ == "__main__":
    main()
