# CEO Schema Request - Context Package for Advisor

**Date**: 2025-11-03
**Project**: compliance-gpt (retirement plan document reconciliation)
**Request**: Canonical Election Ontology (CEO) schema design

---

## What's in This Package

This directory contains all context needed to design the CEO schema and compilation approach.

### 1. Primary Request Document
- **CEO_SCHEMA_REQUEST.md** - Detailed request with deliverables, success criteria, timeline

### 2. Real Extraction Data (CRITICAL)
- **relius_aa_elections_sample.json** - 10 sample Relius elections showing actual v5.2 extraction output
- **ascensus_aa_elections_sample.json** - 10 sample Ascensus elections for comparison

*Full datasets available at*:
- `/test_data/extracted/relius_aa_elections.json` (182 elections)
- `/test_data/extracted/ascensus_aa_elections.json` (550 elections)

### 3. Manual Match Analysis (CRITICAL)
- **MANUAL_MATCH_EXAMPLES.md** - Human expert analysis of 2 real cross-vendor matches
  - Match 1: Sole Proprietorship (simple/exact)
  - Match 2: Age 21 eligibility (complex/structural transformation)

### 4. Technical Context
- **aa_extraction_v5.2.txt** - Prompt that generates the extraction JSON
- **v2_embedding_test_results.json** - Prose-based baseline (80% similarity, need 90%+)

---

## Quick Start for Advisor

### 1. Read This First
1. CEO_SCHEMA_REQUEST.md (the ask)
2. MANUAL_MATCH_EXAMPLES.md (shows real-world complexity)

### 2. Examine Real Data
3. relius_aa_elections_sample.json (what we extract from Relius docs)
4. ascensus_aa_elections_sample.json (what we extract from Ascensus docs)

### 3. Understand Current Limitations
5. v2_embedding_test_results.json (shows prose-based approach plateaus at 80%)

### 4. See What You'll Build On
6. aa_extraction_v5.2.txt (our extraction already captures structure, form_elements, provenance)

---

## The Core Question

**How do we compile this extraction JSON into canonical schema tags that enable deterministic matching?**

**Current**: Direct prose comparison (Relius text ↔ Ascensus text) → 80% similarity
**Proposed**: Pivot through canonical (Relius → CEO → Ascensus) → 90%+ via structure

**Key insight from Match 2**: Same canonical field (`eligibility.age`) with different vendor implementations:
- Relius: 1 age field + "applies to" checkboxes
- Ascensus: N age fields (one per contribution type)

Both should compile to `canonical_field: "eligibility.age"` with structural metadata.

---

## What We're Asking For

See CEO_SCHEMA_REQUEST.md for full details, but in summary:

1. **Canonical field taxonomy** (the schema hierarchy for 5 domains)
2. **Structural variant catalog** (how vendors differ for same canonical field)
3. **Compilation prompt template** (LLM instructions for v5.2 JSON → canonical schema)
4. **Starter scoring config** (weights for TypeMatch, LabelSim, etc.)

---

## Contact

Questions? sergio.dubois@gmail.com

**Timeline**: No rush, but ideally within 1 week to maintain project momentum.
