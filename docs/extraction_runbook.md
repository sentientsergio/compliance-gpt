# Extraction Runbook (Phase 1)

Purpose: choose and operate a layout-aware extractor to produce normalized layout JSON (see `docs/layout_schema.md`). Outputs stay local; do not commit extracted JSON or client PDFs.

## Extractor choice
- **Primary:** Azure AI Document Intelligence (Form Recognizer) — prebuilt layout model.
  - Rationale: strong table/checkbox detection, reliable reading order, stable API/SDK.
- **Fallback options:** Google Document AI (Layout or Form Parser) or AWS Textract (AnalyzeDocument).
- **Local-only stub:** If cloud access is unavailable, use `pytesseract`/`pdfplumber` plus `layoutparser` as a placeholder, but expect weaker table/checkbox fidelity; use only for smoke tests.

## Required inputs (local)
- Source PDFs: `sample_docs/source/*.pdf` (kept local; not tracked).
- Target PDFs: `sample_docs/target/*.pdf` (kept local; not tracked).
- Azure resources: endpoint + key with access to `prebuilt-layout`.

## Workflow (Azure prebuilt layout)
1. Set env vars: `AZURE_FORM_RECOGNIZER_ENDPOINT`, `AZURE_FORM_RECOGNIZER_KEY`.
2. Install deps (example):
   - `pip install azure-ai-formrecognizer==3.2.0 pdfplumber`
3. Run extraction script (pseudo-CLI):
   - `python scripts/extract_layout.py --input sample_docs/source/relius_bpd_cycle3.pdf --doc-id relius_bpd --out tmp/layout/relius_bpd.json`
   - Repeat for other PDFs.
4. Output: JSON conforming to `docs/layout_schema.md` stored under `tmp/layout/` (git-ignored).

## Script
- `scripts/extract_layout.py` (uses Azure prebuilt layout):
  - Loads the PDF.
  - Calls `begin_analyze_document("prebuilt-layout", ...)`.
  - Normalizes output to `docs/layout_schema.md` (sections via headings, blocks with bbox/page, tables with rows/cells and optional checkbox states).
  - Writes JSON to the provided `--out` path (e.g., `tmp/layout/<doc_id>.json`).
  - Optional `--redact-text` flag to strip text content while preserving structure for publishable examples.

## Verification
- Spot-check a few sections:
  - Headings and breadcrumbs present.
  - Tables preserve row/column semantics; checkboxes have states when present.
  - Page ranges and bboxes populated where available.

## Notes
- Keep outputs in `tmp/` or similar; ensure paths are git-ignored.
- If using a fallback extractor, note the model/version and known gaps in a short log in `AGENT.md`.
- Publishing hygiene:
  - Do not commit raw client PDFs.
  - For shareable artifacts, prefer `--redact-text` or use synthetic docs; avoid committing full-text outputs containing client language or PII.
