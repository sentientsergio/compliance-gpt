# Agent Guide

Use this file to rehydrate context between sessions and keep lightweight notes as the project evolves.

## Quick start
- Read `README.md` for repo orientation and links to background.
- Read `docs/roadmap.md` for the current plan, phased milestones, and POC scope.
- Background prompts and prior model responses live in `context/` (files `1_...` through `5_...`).
- Sample PDFs for experiments live in `sample_docs/source/` (Relius) and `sample_docs/target/` (Ascensus).

## Working notes
- Add brief session notes here (date + what changed/decided) to keep future runs aligned.

## Phase rhythm and checkpoints
- At the start of each phase, define success criteria and tests (what evidence will count as “done”).
- During the phase, log findings, decisions, and deviations from plan.
- Before moving forward, review evidence against the criteria and record a short “phase exit” note.
- Capture per-phase learnings for the whitepaper (what worked, what broke, what we’d change).

## Phase 1 kick-off (Ingestion & Layout) – 2024-XX-XX
- Goals: choose a layout-extraction engine; define the normalized layout JSON (blocks, headings, tables, checkboxes, page/page-ranges); handle section stitching across pages.
- Success criteria:
  - Documented internal layout schema checked in.
  - Selected extractor(s) with a short rationale and runbook.
  - Dry run on local sample docs completes end-to-end to produce normalized output (kept local; not committed).
- Evidence to collect: schema file/path, extractor choice note, and a brief run log/summary in this AGENT file for phase exit.

## Phase 1 run log
- 2024-11-26: Extractor in place (Azure Document Intelligence prebuilt-layout). Redacted runs completed for Relius BPD/AA and Ascensus BPD; initial Ascensus AA failed on F0 size limit, then S0 upgrade resolved it. Full-text runs completed for all four PDFs to `tmp/layout_full/`. Endpoint: `formrecog-sd-dev.cognitiveservices.azure.com` (key kept local). Pending: spot-check outputs, then phase exit review.

## Phase 1 exit (Ingestion & Layout) – 2024-11-26
- Success criteria met:
  - Layout schema documented (`docs/layout_schema.md`).
  - Extractor chosen and runbook documented (Azure DI prebuilt-layout; `docs/extraction_runbook.md`).
  - Dry runs complete with normalized outputs (redacted and full text) in `tmp/layout/` and `tmp/layout_full/`.
- Notes:
  - Upgraded to S0 to bypass the 4MB limit on ascensus AA.
  - Provision-level units remain a next-phase task; current outputs are layout atoms with provenance.

## Phase 2 kick-off (Canonical Schema & Provision Segmentation) – 2024-11-26
- Goals: define the vendor-neutral canonical schema (with contribution-type granularity) and design the segmentation logic to group layout atoms into plan provisions.
- Success criteria:
  - Canonical schema documented and checked in (fields, IDs/breadcrumbs, contribution-type splits, ontology for the 10 POC provisions).
  - Segmentation approach documented (rules/heuristics for stitching blocks/tables into provision units; handling cross-page sections).
  - Optional: a small sample mapping from layout atoms → canonical schema for 1–2 provisions per document (to validate feasibility).
- Evidence to collect: schema file/path, segmentation notes, and a brief run/sample in `AGENT.md` when ready for phase exit.

## Phase 2 current state (2024-11-26)
- Added selection marks to layout schema/extraction (checkboxes/radios with state/bbox); reran AA layouts/segments/canonical drafts.
- Canonical extractor supports optional OpenAI embedding ranking; provenance still noisy on some fields; values null in blank templates.
- Research added in `research/` (form-field alignment, checkbox mapping) stressing: label–checkbox linkage, multi-field embeddings without numbering, structure-as-filter + semantic ranking, high-precision bias, AA electable focus.

## Next-session to-do
- Implement label association for selection marks (link checkboxes to nearby labels/table cells in layout JSON).
- Focus on AA electables: use cleaned question/option text for embeddings, strip numbering; keep structure as filter only.
- Tighten per-field filters (Eligibility/NRA/Comp/Vesting/Loans/Hardship/In-service) before semantic ranking; add low-confidence/gap reporting.
- Rerun AA pipeline after label-linking; spot-check provenance on key nodes.
