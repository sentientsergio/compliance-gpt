#!/usr/bin/env python3
"""
Extract layout from a PDF using Azure AI Document Intelligence (prebuilt-layout)
and normalize it to the schema defined in docs/layout_schema.md.

Outputs are intended to stay local (e.g., under tmp/) and should not be committed.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from azure.ai.formrecognizer import DocumentAnalysisClient
    from azure.core.credentials import AzureKeyCredential
except ImportError as e:  # pragma: no cover - dependency may not be installed locally
    DocumentAnalysisClient = None
    AzureKeyCredential = None
    _IMPORT_ERROR = e
else:
    _IMPORT_ERROR = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract normalized layout JSON from a PDF.")
    parser.add_argument("--input", required=True, help="Path to PDF file.")
    parser.add_argument("--doc-id", help="Document ID to store in output (defaults to stem of input).")
    parser.add_argument("--out", required=True, help="Output path for normalized JSON.")
    parser.add_argument(
        "--endpoint",
        default=os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT"),
        help="Azure Form Recognizer endpoint (or set AZURE_FORM_RECOGNIZER_ENDPOINT).",
    )
    parser.add_argument(
        "--key",
        default=os.getenv("AZURE_FORM_RECOGNIZER_KEY"),
        help="Azure Form Recognizer key (or set AZURE_FORM_RECOGNIZER_KEY).",
    )
    parser.add_argument(
        "--redact-text",
        action="store_true",
        help="If set, redact text content in the output (keep structure/bboxes).",
    )
    return parser.parse_args()


def require_dependencies():
    if _IMPORT_ERROR:
        sys.stderr.write(
            "Missing dependency azure-ai-formrecognizer. Install with:\n"
            "  pip install azure-ai-formrecognizer==3.2.0\n"
        )
        sys.exit(1)


def maybe_redact(text: Optional[str], redact: bool) -> Optional[str]:
    if not text:
        return text
    return "[REDACTED]" if redact else text


def build_block(paragraph, redact: bool) -> Dict[str, Any]:
    region = paragraph.bounding_regions[0] if paragraph.bounding_regions else None
    bbox = region.polygon if region else None
    return {
        "id": f"blk-{paragraph.spans[0].offset}" if paragraph.spans else None,
        "type": paragraph.role or "paragraph",
        "text": maybe_redact(paragraph.content, redact),
        "page": region.page_number if region else None,
        "bbox": polygon_to_bbox(bbox),
        "style": None,
    }


def polygon_to_bbox(polygon: Optional[List[Any]]) -> Optional[List[float]]:
    if not polygon:
        return None
    xs = [p.x for p in polygon]
    ys = [p.y for p in polygon]
    return [min(xs), min(ys), max(xs), max(ys)]


def build_table(table, redact: bool) -> Dict[str, Any]:
    page_range = [table.bounding_regions[0].page_number, table.bounding_regions[-1].page_number] if table.bounding_regions else None
    rows: List[Dict[str, Any]] = []
    max_row = max(cell.row_index for cell in table.cells) if table.cells else -1
    # Initialize rows
    for _ in range(max_row + 1):
        rows.append({"cells": []})
    # Simple header propagation: first row and first column treated as headers
    col_headers = {}
    row_headers = {}
    for cell in table.cells:
        if cell.row_index == 0:
            col_headers[cell.column_index] = cell.content
        if cell.column_index == 0:
            row_headers[cell.row_index] = cell.content
    for cell in table.cells:
        region = cell.bounding_regions[0] if cell.bounding_regions else None
        bbox = region.polygon if region else None
        headers = []
        if cell.column_index in col_headers:
            headers.append(col_headers[cell.column_index])
        if cell.row_index in row_headers:
            headers.append(row_headers[cell.row_index])
        rows[cell.row_index]["cells"].append(
            {
                "row_index": cell.row_index,
                "col_index": cell.column_index,
                "text": maybe_redact(cell.content, redact),
                "page": region.page_number if region else None,
                "bbox": polygon_to_bbox(bbox),
                "checkbox_state": None,
                "headers": headers or None,
            }
        )
    return {
        "id": getattr(table, "id", None),
        "title": None,
        "page_range": page_range,
        "bbox": polygon_to_bbox(table.bounding_regions[0].polygon) if table.bounding_regions else None,
        "rows": rows,
    }


def build_sections(paragraphs, page_count: int, redact: bool) -> List[Dict[str, Any]]:
    """Heuristic: treat each heading as a new section; if none, fall back to one section."""
    sections: List[Dict[str, Any]] = []
    current = None
    for para in paragraphs:
        if para.role == "heading":
            if current:
                sections.append(current)
            current = {
                "id": para.content.strip(),
                "title": para.content.strip(),
                "breadcrumbs": [para.content.strip()],
                "page_range": [para.bounding_regions[0].page_number, para.bounding_regions[0].page_number]
                if para.bounding_regions
                else None,
                "blocks": [],
                "tables": [],
            }
        else:
            block = build_block(para, redact)
            if current:
                current["blocks"].append(block)
                # Update end page if needed
                if block["page"] and current["page_range"]:
                    current["page_range"][1] = max(current["page_range"][1], block["page"])
            else:
                # No heading seen yet; start a default section
                current = {
                    "id": "Section 1",
                    "title": "Untitled Section",
                    "breadcrumbs": ["Untitled Section"],
                    "page_range": [block["page"] or 1, block["page"] or page_count],
                    "blocks": [block],
                    "tables": [],
                }
    if current:
        sections.append(current)
    # If still empty, create a placeholder section
    if not sections:
        sections.append(
            {
                "id": "Section 1",
                "title": "Untitled Section",
                "breadcrumbs": ["Untitled Section"],
                "page_range": [1, page_count],
                "blocks": [],
                "tables": [],
            }
        )
    return sections


def attach_tables_to_sections(sections: List[Dict[str, Any]], tables: List[Dict[str, Any]]):
    """Assign tables to the first section whose page_range overlaps."""
    for table in tables:
        assigned = False
        for section in sections:
            pr = section.get("page_range")
            tpr = table.get("page_range")
            if not pr or not tpr:
                continue
            if tpr[0] <= pr[1] and tpr[1] >= pr[0]:
                section.setdefault("tables", []).append(table)
                assigned = True
                break
        if not assigned:
            # If no section match, append to a synthetic section
            sections.append(
                {
                    "id": "Unassigned Tables",
                    "title": "Unassigned Tables",
                    "breadcrumbs": ["Unassigned Tables"],
                    "page_range": tpr,
                    "blocks": [],
                    "tables": [table],
                }
            )


def analyze_document(
    client: DocumentAnalysisClient, pdf_path: Path, doc_id: str, endpoint: str, key: str, redact: bool
) -> Dict[str, Any]:
    with pdf_path.open("rb") as f:
        poller = client.begin_analyze_document("prebuilt-layout", document=f)
    result = poller.result()

    paragraphs = result.paragraphs or []
    tables = result.tables or []
    sections = build_sections(paragraphs, page_count=len(result.pages), redact=redact)
    tables_normalized = [build_table(t, redact=redact) for t in tables]
    attach_tables_to_sections(sections, tables_normalized)

    return {
        "document_id": doc_id,
        "file_name": pdf_path.name,
        "page_count": len(result.pages),
        "sections": sections,
        "tables": [],
        "extraction_metadata": {
            "tool": "azure_document_intelligence",
            "model": "prebuilt-layout",
            "run_at": result.created_on.isoformat() if getattr(result, "created_on", None) else None,
            "endpoint": endpoint,
        },
    }


def main():
    args = parse_args()
    require_dependencies()
    if not args.endpoint or not args.key:
        sys.stderr.write("Azure endpoint/key not provided. Set env vars or pass --endpoint/--key.\n")
        sys.exit(1)
    client = DocumentAnalysisClient(args.endpoint, AzureKeyCredential(args.key))

    pdf_path = Path(args.input)
    if not pdf_path.exists():
        sys.stderr.write(f"Input file not found: {pdf_path}\n")
        sys.exit(1)
    doc_id = args.doc_id or pdf_path.stem

    result = analyze_document(client, pdf_path, doc_id, args.endpoint, args.key, redact=args.redact_text)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2))
    print(f"Wrote normalized layout to {out_path}")


if __name__ == "__main__":
    main()
