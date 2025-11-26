# Compliance-GPT Roadmap

This document captures the current working plan for building an AI-assisted mapper for 401(k) Basic Plan Documents (BPD) and Adoption Agreements (AA). It consolidates takeaways from the prior POC discussions in `context/`.

## Purpose and Scope
- Goal: produce analyst-ready mappings from source (e.g., Relius) to target (e.g., Ascensus) with provenance, similarity ratings, and notes.
- Key challenges: provisions span BPD+AA, one-to-many splits by contribution type, grids/checkboxes, and page-straddled sections.
- Design posture: vendor-neutral canonical schema so new vendors can plug in later.

## Guiding Principles
- Treat a “provision” as a plan-level concept: often BPD text + AA elections together.
- Use structure before semantics: headings/sections/grids anchor retrieval.
- Robust layout first: table/checkbox extraction is a hard requirement; plain text alone is insufficient.
- Hybrid retrieval: hierarchy filters + keyword/BM25 + vectors; LLMs for extraction and comparison, not blind search.
- Provenance everywhere: doc, section, page range, and coordinates where available.
- Human-in-the-loop: confidence scoring, low-confidence prioritization, and editable mappings.

## Phased Roadmap
1. **Alignment**
   - Lock success criteria (Exact/Close/Fuzzy/Gap agreement vs human).
   - Fix the initial POC scope to ~10 canonical provisions.
   - Define required provenance fields.
2. **Ingestion & Layout**
   - Stand up a pluggable document-AI layer (e.g., Azure Document Intelligence, Google DocAI, Textract).
   - Normalize output to a common layout JSON (blocks, headings, tables, checkboxes, page ranges).
   - Stitch logical sections across page breaks.
   - Phase success criteria: schema file checked in; extractor choice and runbook documented; dry run on local sample docs producing normalized output (kept local).
   - Status: completed (Azure DI prebuilt-layout, schema/runbook in docs, runs in `tmp/layout*`).
3. **Canonical Schema**
   - Define a vendor-neutral JSON schema with explicit contribution-type granularity (deferral/match/profit sharing) and clear IDs/breadcrumbs.
   - Phase success criteria: schema file checked in; contribution-type splits defined; ontology covers the initial 10 POC provisions.
   - Include segmentation design to stitch layout atoms into provision units (section/subsection grouping, cross-page handling).
4. **Extraction to Canonical (per vendor)**
   - Retrieval: hierarchy/vision anchors + hybrid search to gather candidates.
   - LLM extraction: fill canonical fields from text/table cells with provenance.
5. **Mapping & Scoring**
   - Compare source vs target canonical nodes; support one-to-many and partial overlaps.
   - Output categories: Exact, Close, Fuzzy/Partial, Gap, with short difference notes and confidence.
6. **Outputs & UX**
   - Spreadsheet export: one row per canonical node with source/target snippets, provenance, similarity, notes, confidence.
   - Audit UI: side-by-side PDF highlights via stored coordinates; filters for low confidence, Fuzzy, and Gap; analyst edits/overrides.
7. **Evaluation**
   - Hand-label gold mappings for the POC set.
   - Metrics: Recall@K for retrieval, category agreement vs gold, analyst time saved; regression tests for prompts/pipelines.
8. **Scale & Ops**
   - Add more provisions/vendors; cache embeddings/layouts; observability and cost controls.
   - Privacy/PII handling and model/service swap points.

## POC Provision Set (initial target)
1. Eligibility: age (per contribution type)
2. Eligibility: service
3. Eligibility: entry dates
4. Normal retirement age
5. Compensation: base definition
6. Compensation: exclusions
7. Vesting schedule
8. Loans: enabled + basics
9. Distributions: hardship
10. Distributions: in-service

## Near-Term Actions
- Choose the layout extraction engine and finalize the internal layout JSON contract.
- Draft and review the canonical schema (with IDs) for the 10 POC provisions.
- Run ingestion on `sample_docs/source/*` and `sample_docs/target/*`, persisting normalized output.
- Label a gold-standard mapping for the POC set to anchor evaluation.
