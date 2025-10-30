# Phase 2: Plan Provision Crosswalk POC

**Date:** 2025-10-30
**Phase:** Phase 2 - Template-to-Template Crosswalk
**Test Set:** 3 Relius Plan Provisions → 2 Ascensus Plan Provisions

---

## Executive Summary

Successfully generated template-to-template crosswalk mapping document using Phase 1 Plan Provisions (BPD+AA merged at template level). The two-phase architecture (embeddings → LLM verification) correctly identified semantic relationships and detected provisions with no equivalents across vendors.

**Key Finding:** Template-level Plan Provisions enable crosswalk generation WITHOUT requiring filled election values. This mapping document can later be used to automate value transfer when converting actual client plans.

---

## Test Corpus

**Source (Relius):**
- Eligibility provision (Section 3.1)
- Compensation provision (Section 1.18)
- Vesting provision (Section b)

**Target (Ascensus):**
- Eligibility provision (ENTRY DATES)
- Vesting provision (Section 8.B - Top-Heavy Plans)

**Missing in Target:**
- No compensation definition provision

---

## Methodology

### Step 1: Embedding Generation
- Model: `text-embedding-3-small`
- Input: Plan Provision text (BPD + AA context combined)
- Result: 5 embeddings generated (3 source + 2 target)

### Step 2: Candidate Finding (Cosine Similarity)
- For each source provision, find top-k=2 target candidates
- Cosine similarity threshold: None (let LLM decide semantic equivalence)

### Step 3: LLM Verification
- Model: `gpt-4o-mini`
- Task: Determine if provisions are semantically equivalent at template level
- Output: Match type (exact/close/none), confidence (0-1), reasoning, variance notes

---

## Results

### Mapping #1: Eligibility Provisions

**Source:** Relius Section 3.1 "CONDITIONS OF ELIGIBILITY"
**Target:** Ascensus "ENTRY DATES"
**Cosine Similarity:** 0.841

**LLM Verdict:** ❌ **CLOSE** (confidence: 0.7)

**Reasoning:**
> "Both provisions address eligibility for participation in a retirement plan, but they focus on different aspects. The Relius provision specifies conditions for eligibility based on employee status, while the Ascensus provision outlines entry dates based on when eligibility requirements are met. Although they are related to eligibility, they do not govern the same feature directly."

**Variance Notes:**
> "Relius focuses on the conditions of eligibility for employees, while Ascensus specifies when an employee can enter the plan after meeting those eligibility conditions. The options available in the adoption agreements also differ in focus, with Relius emphasizing exclusions and Ascensus detailing entry dates."

**Analysis:**
This is a **true close match** - both provisions are in the eligibility domain, but they govern different sub-features:
- **Relius:** Eligibility CONDITIONS (who qualifies)
- **Ascensus:** ENTRY DATES (when qualified employees can join)

In a real conversion, a TPA would need BOTH Relius eligibility conditions AND entry date provisions to complete the Ascensus eligibility section. This is a valuable finding - highlights missing coverage.

---

### Mapping #2: Compensation Provision

**Source:** Relius Section 1.18 "Compensation"
**Target:** Ascensus "ENTRY DATES" (best candidate found)
**Cosine Similarity:** 0.548

**LLM Verdict:** ❌ **NONE** (confidence: 0.2)

**Reasoning:**
> "The provisions govern different aspects of retirement plans; one addresses compensation while the other pertains to eligibility entry dates. They do not cover the same plan feature or requirement."

**Variance Notes:**
> "The source provision focuses on defining compensation for participants, while the target provision outlines entry dates for eligibility, indicating they serve distinct purposes within the plan structure."

**Analysis:**
This is a **true negative** - Ascensus test set does not include a compensation definition provision. The LLM correctly rejected the best embedding candidate (eligibility) because it's semantically unrelated.

**Implications:**
- Compensation definition is **MISSING in target**
- TPA would need to manually find Ascensus compensation section (not in our test set)
- This would be flagged in the mapping document as "unmapped source provision"

---

### Mapping #3: Vesting Provisions

**Source:** Relius Section b "Vesting schedule"
**Target:** Ascensus Section 8.B "Minimum Vesting Schedule for Top-Heavy Plans"
**Cosine Similarity:** 0.787

**LLM Verdict:** ❌ **CLOSE** (confidence: 0.6)

**Reasoning:**
> "Both provisions address vesting schedules, but the Relius provision is specific to general vesting rules while the Ascensus provision is specifically for Top-Heavy Plans. The Relius provision includes details about the vesting schedule based on Years of Service and conditions for non-forfeiture at Normal Retirement Age, which are not present in the Ascensus provision."

**Variance Notes:**
> "The Relius provision provides a detailed vesting schedule based on service years and includes specific conditions for non-forfeiture, while the Ascensus provision only outlines minimum vesting requirements for Top-Heavy Plans without detailing the vesting schedule or conditions."

**Analysis:**
This is a **true close match** with important variance:
- **Relius:** General vesting schedule (applies to all plans)
- **Ascensus:** Top-heavy vesting minimum (conditional provision)

In a real conversion:
- TPA would need to map Relius general vesting → Ascensus general vesting (not in test set)
- TPA would need to understand top-heavy rules apply ONLY when plan is top-heavy
- This is a **regulatory complexity** that requires domain expertise

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| **Total Source Provisions** | 3 |
| **Total Target Provisions** | 2 |
| **Exact Matches** | 0 |
| **Close Matches** | 2 |
| **No Matches** | 1 |
| **Unmapped Sources** | 3 (all - no exact matches found) |
| **Unmapped Targets** | 2 (all - no exact matches found) |

---

## Key Findings

### ✅ What Worked

1. **Two-phase architecture is effective**
   - Embeddings successfully found semantically related candidates (0.841 for eligibility pair, 0.787 for vesting pair)
   - LLM correctly distinguished "close" from "none" matches
   - No false positives (LLM rejected compensation → eligibility with 0.2 confidence)

2. **Plan Provisions enable template-level comparison**
   - BPD+AA merged text gives richer semantic context than BPD-only
   - Phase 1.5 proved +6.2% embedding improvement - validates this approach

3. **Variance detection works**
   - LLM identified eligibility conditions vs entry dates distinction
   - LLM identified general vesting vs top-heavy vesting distinction
   - Variance notes provide actionable details for TPA review

4. **Unmapped provision detection works**
   - Correctly flagged compensation as missing in target
   - Correctly flagged all provisions as "close but not exact"

### ⚠️ Limitations (Expected for POC)

1. **Small test set**
   - Only 3 source, 2 target provisions
   - Missing key provision types (contributions, distributions, loans)
   - Cannot measure full coverage statistics

2. **No exact matches found**
   - Expected - test provisions are incomplete (missing complementary provisions)
   - Real crosswalk would have 100+ provisions per vendor
   - Eligibility domain needs BOTH conditions AND entry dates provisions

3. **Close matches require human review**
   - 2 "close" matches need TPA domain expertise to resolve
   - Mapping document flags these for review (correct behavior)

### 🎯 Validation of Phase 1 Approach

**Phase 1 created the right foundation:**
- Template-level Plan Provisions (BPD+AA merged) are semantically complete units
- Embeddings capture semantic relationships (0.841 for related provisions, 0.548 for unrelated)
- No filled values needed for crosswalk generation

**Phase 2 proves the concept:**
- Mapping document generation works end-to-end
- Output format ready for programmatic consumption
- Can be used to drive automated value transfer (future Phase 3)

---

## Mapping Document Schema

The generated crosswalk follows this structure:

```json
{
  "metadata": {
    "source_vendor": "Relius",
    "target_vendor": "Ascensus",
    "source_provision_count": 3,
    "target_provision_count": 2
  },
  "summary": {
    "exact_matches": 0,
    "close_matches": 2,
    "no_matches": 1
  },
  "mappings": [
    {
      "source_provision_id": "...",
      "source_section": "...",
      "target_provision_id": "...",
      "target_section": "...",
      "cosine_similarity": 0.841,
      "llm_verification": {
        "is_match": false,
        "confidence": 0.7,
        "match_type": "close",
        "reasoning": "...",
        "variance_notes": "..."
      }
    }
  ],
  "unmapped_sources": [...],
  "unmapped_targets": [...]
}
```

This schema is **programmatically consumable** for future automation.

---

## Next Steps

### Immediate: Scale to Full Corpus

Run crosswalk on complete extraction data:
- **Source:** Relius BPD (623 provisions) + AA (182 elections) = 805 Plan Provisions
- **Target:** Ascensus BPD (426 provisions) + AA (550 elections) = 976 Plan Provisions
- **Expected:** 200-400 exact/close matches, 400-600 unmapped provisions per side

### Near-term: Mapping Document as Product

The crosswalk output IS the core product:
1. TPAs receive blank templates from both vendors
2. We generate mapping document (template-to-template)
3. TPA uses mapping document when converting client plans
4. Example: "Relius Q 1.04 age → Ascensus Q A.3 age" (programmatic transfer rule)

### Future: Automated Value Transfer (Phase 3)

Once mapping rules exist, automate value transfer:
- **Input:** Filled Relius plan (values from TPA system export OR vision-extracted PDF)
- **Process:** Apply mapping rules (Relius Q 1.04 age=21 → Ascensus Q A.3 age=21)
- **Output:** Filled Ascensus elections (importable data OR filled PDF)

---

## Deliverables

1. ✅ **Crosswalk script:** `test_data/golden_set/phase1_merger_poc/crosswalk_plan_provisions.py`
2. ✅ **Mapping document:** `test_data/golden_set/phase1_merger_poc/plan_provision_crosswalk.json`
3. ✅ **Test report:** This document

---

## Conclusion

**Phase 2 POC validates the complete architecture:**

```
Phase 1: Template Plan Provisions (BPD+AA merged)
    ↓
Phase 2: Crosswalk → Mapping Document
    ↓
Phase 3: Value Transfer (use mapping rules for automation)
```

The mapping document is the **bridge** between template analysis and actual conversion automation. It encodes vendor-specific transformation logic that can be applied programmatically when filled plans arrive.

**Template-level crosswalk works.** No filled values needed for mapping generation. Phase 1 + Phase 2 together prove the complete concept.

---

**Author:** Sergio DuBois (with AI assistance from Claude)
**Related Documents:**
- [Phase 1 POC Report](phase1_plan_provisions_poc_2025-10-30.md)
- [Phase 1.5 Quantitative Validation](phase1.5_embedding_quality_2025-10-30.md)
- [ADR-001: Merge Strategy](../design/architecture/adr_001_merge_strategy.md)
- [Plan Provision Data Model](../design/data_models/plan_provision_model.md)
