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
