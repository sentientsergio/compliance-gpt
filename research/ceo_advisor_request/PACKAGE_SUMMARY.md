# CEO Advisor Request Package - Summary

**Created**: 2025-11-03
**Purpose**: Provide advisor with all context needed to design Canonical Election Ontology (CEO) schema

---

## What's Included

### 📄 Core Request
1. **README.md** - Start here (quick navigation)
2. **CEO_SCHEMA_REQUEST.md** - Detailed request with deliverables and success criteria

### 🎯 Critical Context
3. **MANUAL_MATCH_EXAMPLES.md** - Human expert analysis of 2 real matches
   - Match 1: Sole Proprietorship (simple/exact)
   - Match 2: Age 21 eligibility (complex structural transformation) ⭐

### 📊 Real Data Samples
4. **relius_aa_elections_sample.json** - 10 diverse Relius elections
5. **ascensus_aa_elections_sample.json** - 9 diverse Ascensus elections

Coverage: Eligibility, Vesting, Contributions, Loans, Hardship, Top-Heavy, Safe Harbor

### 🔧 Technical Reference
6. **aa_extraction_v5.2.txt** - Prompt that generates extraction JSON
7. **v2_embedding_test_results.json** - Prose-based baseline (80% similarity)

---

## Key Files to Review

### For Quick Understanding (15 min)
1. README.md
2. MANUAL_MATCH_EXAMPLES.md (especially Match 2)
3. CEO_SCHEMA_REQUEST.md sections 1-2

### For Schema Design (1 hour)
1. relius_aa_elections_sample.json - see actual Relius structure
2. ascensus_aa_elections_sample.json - see actual Ascensus structure
3. CEO_SCHEMA_REQUEST.md section 3 (compilation prompt requirements)

### For Full Context (2 hours)
- All files above
- v2_embedding_test_results.json (shows why prose-based plateaus)
- aa_extraction_v5.2.txt (what fields we already extract)

---

## The Core Challenge

**Problem**: Cross-vendor matching with structural transformations

**Example (Match 2)**:
- Relius: 1 age field (Age 21) + 4 "applies to" checkboxes (contribution types)
- Ascensus: N age fields (one per contribution type, each with checkbox + textbox)
- **Same intent, different structure**

**Current approach**: Prose-based embeddings → 80% similarity (need 90%+)

**Proposed approach**: Canonical schema compilation → deterministic matching on `canonical_field`

---

## What We Need from Advisor

See CEO_SCHEMA_REQUEST.md for details, but in summary:

1. **Canonical field taxonomy** - Schema hierarchy for 5 domains (Eligibility, Vesting, Contributions, Loans, Distributions)

2. **Structural variant catalog** - How vendors implement same canonical field differently
   - Example: `eligibility.age` has 2 variants:
     - Relius: `single_age_with_applies_to` (1 field + checkboxes)
     - Ascensus: `age_per_contribution_type` (N combo fields)

3. **Compilation prompt template** - LLM instructions to convert extraction JSON → canonical schema tags

4. **Starter scoring config** - Weights for field-level scoring (TypeMatch, LabelSim, etc.)

---

## Expected Outcomes

### With CEO Schema (Predicted)
- ✅ Match deterministic on `canonical_field` (95% of cases)
- ✅ Structural transformations detected via `vendor_implementation` metadata
- ✅ Property tests validate functional equivalence
- ✅ 90%+ confidence scores (vs 80% prose-based)
- ✅ 10× token reduction (structure is shorter than prose)

### Validation Plan
1. Compile Match 2 example (Age 21 eligibility)
2. Verify both sides → `canonical_field: "eligibility.age"`
3. Detect structural transformation
4. Validate functional equivalence via property tests
5. Measure confidence (expect 95%+ vs current 83.7%)

---

## Questions for Advisor

See CEO_SCHEMA_REQUEST.md section "Questions for Advisor", but key ones:

1. Should compiler be LLM-based (flexible) or rule-based (deterministic)?
2. How granular should canonical fields be? (`eligibility.age` vs `eligibility.age.matching.pretax`)
3. Should we handle rare/vendor-specific fields or focus on common fields first?
4. What's the right balance between schema coverage (exhaustive) vs compilation complexity (practical)?

---

## Next Steps After Advisor Response

1. Implement CEO compiler (v5.2 extraction → canonical schema tags)
2. Test on 4 test cases from embedding quality test
3. Validate on Match 2 (Age 21 structural transformation)
4. Measure improvement (expect 80% → 90%+ accuracy)
5. Scale to full corpus (182 Relius + 550 Ascensus elections)

**Timeline**: 1-2 weeks after receiving schema

---

## Contact

Questions? sergio.dubois@gmail.com

**No rush**, but ideally within 1 week to maintain project momentum.

---

## Appendix: Why We Pivoted from Prose-Based

### V1 Results (Baseline)
- Average similarity: 0.719
- High confidence (≥0.85): 0/4 (0%)
- Service Crediting: FALSE NEGATIVE (matched to wrong domain)

### V2 Results (Hybrid: Cleaning + Option Structure)
- Average similarity: 0.796 (+10.7%)
- High confidence (≥0.85): 0/4 (0%)
- Service Crediting: FIXED (+30% improvement)

### Analysis
✅ Cleaning helped (removed noise)
✅ Service Crediting fixed (was 0.627 → 0.817)
❌ Still below 0.85 threshold
❌ Structural transformations not captured

### Conclusion
Prose-based has fundamental ceiling (~0.80-0.84) due to:
- Terse text (40-120 chars vs embeddings optimized for 300+ chars)
- No structural information (1 field vs N fields)
- Semantic similarity doesn't capture functional equivalence

**CEO approach addresses all three limitations.**
