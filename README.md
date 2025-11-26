# Compliance-GPT

AI-assisted tooling to map 401(k) Basic Plan Documents (BPD) and Adoption Agreements (AA) between vendors (e.g., Relius → Ascensus) with provenance, similarity ratings, and analyst review.

## Context and design inputs
- Project background and prior LLM analyses live in `context/`:
  - `context/1_context_prompt.md` (problem statement)
  - `context/2_GPT_5_1_Pro_response.md` (initial GPT-5.1 Pro POC + design)
  - `context/3_Gemini_3_Pro_response.md` (Gemini POC + design)
  - `context/4_followup_prompt.md` (follow-up prompt)
  - `context/5_GPT_5_1_Pro_review_response.md` (consolidated review)
- These drive the current architecture assumptions (canonical schema, layout-aware ingestion, hybrid retrieval, human-in-the-loop review).

## Plan and roadmap
- The working plan is in `docs/roadmap.md` (phases, guiding principles, POC scope, and near-term actions).

## Sample materials
- Example source/target plan documents for experiments live under:
  - `sample_docs/source/` (e.g., Relius BPD/AA)
  - `sample_docs/target/` (e.g., Ascensus BPD/AA)
- These are client-provided artifacts and are **not tracked in git**; keep them local.

## Getting oriented
1) Skim `docs/roadmap.md` for the current plan.
2) Read the `context/` files if you need the rationale and POC findings.
3) Use the PDFs in `sample_docs/` to test ingestion, extraction, and mapping pipelines.***
