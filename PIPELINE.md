# Pipeline (Current State)

This document traces the pipeline as currently implemented, with inputs, scripts, and outputs. It will evolve as new stages (segmentation, canonical mapping, LLM prompts) come online.

## Inputs
- PDFs (kept local, not tracked): `sample_docs/source/*.pdf`, `sample_docs/target/*.pdf`.
- Azure Document Intelligence (prebuilt-layout) endpoint/key (env vars `AZURE_FORM_RECOGNIZER_ENDPOINT`, `AZURE_FORM_RECOGNIZER_KEY`).

## Layout extraction (Phase 1)
- Script: `scripts/extract_layout.py`
  - Model: Azure prebuilt-layout (document analysis).
  - CLI:
    - Full text: `python scripts/extract_layout.py --input <pdf> --doc-id <id> --out tmp/layout_full/<id>.json`
    - Redacted (structure only): add `--redact-text` to produce shareable artifacts in `tmp/layout/`.
  - Output schema: `docs/layout_schema.md` (sections, blocks, tables, checkboxes, provenance).
- Runbook: `docs/extraction_runbook.md` (setup, env vars, verification, hygiene).

## Outputs (current)
- Full-text normalized layout JSON (git-ignored): `tmp/layout_full/*.json`
- Redacted normalized layout JSON (git-ignored): `tmp/layout/*.json` (for publishing examples).

## Next steps (planned)
- Provision segmentation: group layout atoms into plan-level provisions, stitch across pages.
- Canonical mapping: populate vendor-neutral schema and compare source vs target.
- LLM prompts: for extraction-to-canonical and comparison once segmentation is defined.
