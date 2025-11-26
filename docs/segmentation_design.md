# Segmentation Design (Draft)

Purpose: group layout atoms (sections/blocks/tables) into plan-level provisions aligned to the canonical schema. This sits between raw layout extraction and canonical field population.

## Inputs
- Normalized layout JSON (`docs/layout_schema.md`) from `scripts/extract_layout.py` (full-text preferred for this step).

## Outputs
- Provision candidates: chunks with IDs, text, tables, and provenance, suitable for mapping to canonical fields.

## Heuristics / rules
- **Heading-driven grouping**: start a new provision at headings/section numbers (e.g., “ARTICLE III ELIGIBILITY”, “3.5 REHIRED EMPLOYEES...”).
- **Subsection accumulation**: include subsequent blocks until the next heading of equal/higher level.
- **Table association**: attach tables whose page_range overlaps the provision; preserve row/col semantics and checkbox states.
- **Cross-page stitching**: if a heading starts near a page end, continue accumulation across pages until a new heading is hit.
- **TOC vs body**: ignore TOC pages for provision content; keep for navigation only.
- **BPD + AA pairing**: tag source doc type (`bpd` or `aa`) to support cross-document provisions later.

## Provision shape (intermediate)
```json
{
  "provision_id": "relius_bpd:3.5",
  "title": "REHIRED EMPLOYEES AND 1-YEAR BREAKS IN SERVICE",
  "doc_id": "relius_bpd",
  "breadcrumbs": ["Article III", "Eligibility", "3.5"],
  "page_range": [20, 22],
  "blocks": [...],   // merged text blocks
  "tables": [...],   // attached tables
  "provenance": {
    "section": "3.5",
    "page_range": [20,22]
  }
}
```

## Mapping to canonical schema (planned)
- For each canonical node, retrieve candidate provisions via:
  - heading/breadcrumb filters (e.g., Eligibility → Article III),
  - keyword + vector search for concepts (“vesting”, “hardship”, “loan”),
  - contribution-type cues (tables/grids with source columns).
- LLM extraction step (Phase 3) will consume these provision chunks to populate canonical fields.

## Open items
- Heading-level detection: refine role/heading levels from layout; may add regex for section numbers (e.g., `^\d+(\.\d+)*`).
- Many-to-many: support splitting a provision when a single heading contains multiple concepts.
- Adoption Agreement grids: ensure per-source columns carry through to canonical `applies_to` lists.
