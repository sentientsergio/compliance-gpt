# Layout Schema (Normalized Extract)

Purpose: a vendor-neutral representation of PDF structure used for provenance, segmentation, and downstream extraction. This schema is populated by the layout extractor and persists locally (not committed) for source/target documents.

## Top-level
- `document_id`: stable identifier (e.g., `relius_bpd`, `ascensus_aa`).
- `file_name`: original file name.
- `page_count`: integer.
- `sections`: array of section nodes (see below).
- `tables`: array of table objects not already nested under a section (optional if tables are embedded in sections).
- `extraction_metadata`: tool/version/config.

## Section node
- `id`: hierarchy key when available (e.g., `Article III`, `3.5`, `Section 2 Part A`).
- `title`: text of the heading.
- `breadcrumbs`: array of ancestor labels to support navigation/filtering.
- `page_range`: `[start_page, end_page]` inclusive.
- `blocks`: array of block objects contained in the section.
- `tables`: array of tables scoped to the section.
- `parent_id` / `children`: optional if a tree is maintained.

## Block
- `id`: stable within document.
- `type`: `paragraph` | `heading` | `list_item` | `footnote`.
- `text`: plain text.
- `bbox`: `[x0, y0, x1, y1]` in page coordinates (optional but preferred).
- `page`: page number (1-based).
- `style`: optional font/size/bold/indent cues.

## Table
- `id`: stable within document.
- `title`: optional label near the table.
- `page_range`: `[start_page, end_page]`.
- `bbox`: table bounding box (optional).
- `rows`: array of rows; each row has `cells`.

### Cell
- `row_index`, `col_index`.
- `text`: cell text (normalized left-to-right, top-to-bottom).
- `bbox`: cell bounding box (optional).
- `page`: page number.
- `checkbox_state`: `checked` | `unchecked` | `unknown` (for grids with boxes).
- `headers`: optional resolved header labels for the row/column to preserve semantics (e.g., contribution type).

## Checkbox / field (standalone, outside tables)
- `id`
- `label`: associated text.
- `page`
- `bbox`
- `state`: `checked` | `unchecked` | `unknown`

## Provenance helpers
- Every block/table/cell should carry `page`/`page_range` and `bbox` when available.
- `breadcrumbs` on sections carry through to nested content to anchor retrieval (e.g., `["Section 2", "Eligibility", "Part A", "Age Requirement"]`).

## Example (abridged)
```json
{
  "document_id": "ascensus_aa",
  "file_name": "ascensus_aa_profit_sharing.pdf",
  "page_count": 60,
  "extraction_metadata": {
    "tool": "azure_document_intelligence",
    "model": "prebuilt-layout",
    "run_at": "2024-XX-XXT00:00:00Z"
  },
  "sections": [
    {
      "id": "Section 2 Part A",
      "title": "Eligibility - Age Requirement",
      "breadcrumbs": ["Section 2", "Eligibility", "Part A", "Age Requirement"],
      "page_range": [2, 3],
      "blocks": [
        {
          "id": "blk-001",
          "type": "paragraph",
          "text": "Age requirement for eligibility applies as follows...",
          "page": 2,
          "bbox": [120, 240, 480, 320]
        }
      ],
      "tables": [
        {
          "id": "tbl-elig-age",
          "page_range": [2, 3],
          "rows": [
            {
              "cells": [
                {
                  "row_index": 0,
                  "col_index": 0,
                  "text": "Contribution Type",
                  "page": 2
                },
                {
                  "row_index": 0,
                  "col_index": 1,
                  "text": "Age",
                  "page": 2
                },
                {
                  "row_index": 1,
                  "col_index": 0,
                  "text": "Elective Deferrals",
                  "page": 2,
                  "headers": ["Contribution Type"]
                },
                {
                  "row_index": 1,
                  "col_index": 1,
                  "text": "21",
                  "page": 2,
                  "headers": ["Age"]
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```
