# Phase 2 Notes (Canonical Schema & Mapping)

Working log of experiments, issues, and decisions for Phase 2.

## What we tried
- Segmentation (`scripts/segment_provisions.py`): heading-driven grouping of layout atoms into provision chunks; TOC skip defaulted to 3 pages; filtered numeric-only headings.
- Heuristic canonical extraction (`scripts/extract_canonical.py`): keyword/regex-based selection for POC nodes (eligibility, NRA, compensation, vesting, loans, hardship, in-service).

## Issues observed
- High false-positive rates: keyword hits pulled provenance from unrelated sections (e.g., eligibility age from “Prevailing Wage”, NRA from hardship/forfeiture sections, compensation base from HCE definitions).
- “All hits” in reports are misleading; presence of a match ≠ correctness.
- TOC bleed-through reduced but not eliminated by simple skips/heading rules.

## Decisions / next steps
- Extend extraction to capture selection marks (checkboxes/radios) and form fields; normalize in layout schema.
- Focus mapping on AA documents first (electable items); BPDs mainly provide context.
- Add semantic retrieval on top of structural filters:
  - Use structure (headings/breadcrumbs/page range) only as a filter, not in embeddings.
  - Embed cleaned provision text (title/body/table text without numbering) and canonical queries; rank by cosine.
  - Keep provenance from the selected provision chunk.
  - Hybrid scoring: structure filter → keyword filter → cosine ranking; flag low-similarity ties as “needs review”.
- Refine per-node filters:
  - Eligibility: prefer Article/Section Eligibility headings; prioritize AA for age/service values.
  - NRA: require “Normal Retirement Age” concept and reasonable age range.
  - Compensation: anchor to AA “Compensation” section.
  - Loans: require “loan” in heading; avoid unrelated sections.
  - Hardship vs in-service: enforce concept-specific keywords to avoid cross-contamination.

## Pending
- Implement semantic scoring in `scripts/extract_canonical.py` with a small embedding model (local or API).
- Add a gap/miss report highlighting weak/ambiguous matches.
