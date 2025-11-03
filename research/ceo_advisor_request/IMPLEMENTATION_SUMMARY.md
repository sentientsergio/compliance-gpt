# CEO Approach Implementation - Day 2 Summary

**Date**: 2025-11-03
**Status**: ⚠️ Discovery-first architecture working, but taxonomy coverage insufficient (36.1% success)

---

## What We Accomplished Today

### 1. ✅ Received Advisor Response 2 (Discovery-First Architecture)
After questioning whether the initial approach was "discovering structure or encoding it one transformation at a time," we obtained a complete architectural redesign:

**New Artifacts:**
- **ceo.struct_signature.schema.json** - 9 shape types for runtime pattern discovery
- **ceo.operators.json** - 4 generic operators (replicate, bind, gate, aggregate)
- **ceo.match_scoring.v0.2.json** - Updated weights (35% StructureSigSim, 15% DimensionMatch)
- **ceo.dimension_lexicon.json** - Contribution type phrases for detection

**Key Shift:**
- **OLD**: 11 hardcoded structural variants for 732 elections (1.5% coverage) - lookup table
- **NEW**: Runtime signature extraction + generic operators - discovery-first

### 2. ✅ Built Signature Extractor
**File**: `src/compilation/signature_extractor.py`
**Capability**: Discovers structural patterns from v5.2 extraction JSON

**Key Methods:**
- `_count_controls()` - Counts checkboxes, text fields, radios, grids from form_elements
- `_infer_shape()` - Detects 9 shape types (scalar_numeric, menu, checklist, etc.)
- `_detect_contribution_types()` - Uses lexicon to find dimensions in text
- `_detect_value_units_and_numbers()` - Finds age_years, percent, dollars, numeric literals
- `_detect_constraints_hints()` - Extracts max_implied, min_implied from "not to exceed" phrases

**Test Result - Relius Age 21**:
```json
{
  "shape": "scalar_numeric",
  "dimension_hits": {
    "contribution_type": ["matching", "nonelective", "pretax"]
  },
  "value_hints": ["age_years"],
  "constraints_hints": {"max_implied": 21},
  "label_tokens": ["eligibility", "conditions", "age", ...]
}
```

**Critical Fix**: v5.2 extraction doesn't always populate `form_elements`, so shape inference checks question_text patterns FIRST (e.g., "age 21", "not to exceed").

### 3. ✅ Built Discovery-First Compiler (CEOCompilerV2)
**File**: `src/compilation/ceo_compiler_v2.py`
**Architecture**: Signature → Domain → Candidates → Operators → Nodes

**Compilation Pipeline:**
1. Extract structural signature (via SignatureExtractor)
2. Infer domain from section_context keywords (eligibility, vesting, contributions, etc.)
3. Find canonical field candidates (score by value_type, units, label similarity, dimensions, constraints)
4. Choose best canonical field (highest scoring)
5. Apply generic operators to generate canonical nodes
6. Calculate confidence score

**4 Generic Operators Implemented:**
- **replicate_across_dimension**: Scalar value → N nodes (one per contribution type)
  - Example: Age 21 applies to [matching, nonelective, pretax] → 3 nodes
- **bind_dimension_value**: Array-by-dimension → bind each row to its contribution type
- **gate_by_toggle**: Toggle+detail → dependency bundle (parent controls children)
- **aggregate_or_cap**: "Maximum" or "cap" phrases → normalize to .max field

**Instrumentation/Metrics:**
- Compile success/failure rates
- Domain distribution
- Operator usage counts
- Signature families (shape + dimension count)
- Novel dimension tokens (for lexicon expansion)

### 4. ⚠️ Full Corpus Test Results (183 Relius Elections)

**Overall Metrics:**
- **Compile success**: 66/183 (36.1%) ❌ Below 80% target
- **Compile failure**: 117/183 (63.9%)
- **Failure cause**: "Unknown field" - no canonical match above 0.3 threshold

**Domain Inference Working:**
- Eligibility: 44.3%
- Contributions: 44.3%
- Distributions: 7.7%
- Vesting: 3.3%
- Loans: 0.5%

**Signature Families Discovered:**
- text_block+0contrib: 67
- menu+0contrib: 17
- menu_plus_other+0contrib: 15
- menu+2contrib: 14
- checklist+0contrib: 13
- scalar_numeric+3contrib: 6 ← Age 21 pattern

**Operators Used:**
- replicate_across_dimension: 6
- aggregate_or_cap: 5

---

## What This Proves

### ✅ Discovery Architecture Works
- Signature extractor correctly identifies shapes, dimensions, constraints
- Generic operators successfully transform elections (Age 21 → 3 nodes)
- Instrumentation tracks patterns for future learning

### ✅ Age 21 Test Case - Perfect
Relius Age 21 compiled to 3 canonical nodes:
```json
{
  "canonical_field": "eligibility.age",
  "dimension_values": {"contribution_type": "matching"},
  "constraints": {"max": 21},
  "confidence": 1.00
}
```
Replicated for nonelective and pretax with identical constraints.

### ❌ Taxonomy Coverage Insufficient
**Problem**: 39 canonical fields insufficient for 183 distinct elections

**Successful Elections** (36.1%):
- Mapped to: `eligibility.age`, `eligibility.entry.other_text`, `eligibility.service.years_required`, `vesting.schedule.nonelective`
- Mostly simple scalar elections (age, service, entry dates)

**Failed Elections** (63.9%):
- **SERVICE CREDITING METHOD** - no "service.crediting_method" field
- **CURRENT CONTRIBUTIONS** - no "contributions.enabled" meta-election
- **Catch-Up Contribution effective date** - no "contributions.catchup.effective_date"
- **Automatic Deferral provisions** - no "contributions.auto_enrollment.*" fields
- **Disability continuation payments** - no "compensation.disability_continuation" field

---

## Root Cause Analysis

### Issue 1: Taxonomy Designed for Simple Fields
The 39 canonical fields from advisor response 1 cover basic elections:
- eligibility.age
- eligibility.service.years_required
- vesting.schedule.*
- contributions.match.rate.*

But AAs contain **meta-elections** (feature enablement, effective dates, crediting methods) that aren't in the taxonomy.

### Issue 2: Threshold Too Strict?
Match threshold set at 0.3 - candidates below this score are rejected.

**Example**: "SERVICE CREDITING METHOD" probably scores low on label_similarity with all 39 fields, gets rejected with "unknown field."

### Issue 3: text_block Dominant (67 elections)
67 elections detected as `text_block` shape - these are likely effective dates, free-text entries, or conditional language that don't map cleanly to structured fields.

---

## Comparison: Discovery vs Lookup Table

| Metric | Lookup Table (Response 1) | Discovery-First (Response 2) | Analysis |
|--------|---------------------------|------------------------------|----------|
| **Coverage** | 11 variants for 732 elections (1.5%) | Discovered 10 signature families | Discovery found patterns ✅ |
| **Generalization** | Vendor-specific hardcoded rules | Generic operators work across vendors | Generalizable ✅ |
| **Success Rate** | Untested (assumed <20%) | 36.1% (66/183) | Better but insufficient ❌ |
| **Failure Mode** | Unknown variant → fail | Unknown canonical field → fail | Same problem, different layer |

**Key Insight**: Discovery architecture successfully identifies **structural patterns**, but fails at **semantic mapping** because the canonical taxonomy is too narrow.

---

## Next Steps (Decision Point)

### Option 1: Expand Taxonomy (Supervised)
**Approach**: Manually add missing canonical fields based on failed elections

**Pros:**
- Fast to implement (human review + JSON editing)
- Maintains semantic control (human decides canonical names)
- Can reach 80%+ with 20-30 new fields

**Cons:**
- Doesn't scale to new vendor documents
- Requires domain expertise for each new field
- Still vendor-specific in disguise (just encoding Relius AA structure)

**Examples of fields to add:**
```json
{
  "canonical_field": "service.crediting_method",
  "domain": "eligibility",
  "value_type": "string",
  "units": "N/A",
  "vendor_synonyms": ["service crediting method", "hours counting method", "elapsed time"]
},
{
  "canonical_field": "contributions.enabled",
  "domain": "contributions",
  "value_type": "enum",
  "units": "N/A",
  "allowed_enums": ["pretax", "roth", "matching", "nonelective", "profit_sharing", "safe_harbor"]
},
{
  "canonical_field": "contributions.catchup.effective_date",
  "domain": "contributions",
  "value_type": "string",
  "units": "N/A"
}
```

### Option 2: Enable Pattern Mining (Unsupervised)
**Approach**: Use k-modes clustering or HDBSCAN on signature vectors to discover canonical field clusters automatically

**Pros:**
- Truly vendor-agnostic (learns from data)
- Scales to new documents without human intervention
- Discovers patterns humans might miss

**Cons:**
- Complex to implement (need clustering + label generation)
- Requires large corpus (183 elections may be too small)
- Generated canonical names may not be human-readable
- Harder to audit/validate

**Advisor's Guidance** (from response 2):
> "Run on all 732; if compile success ≥80%, keep iterating. If not, enable unsupervised pattern mining (k‑modes/HDBSCAN) to learn new shapes automatically."

---

## Recommendation

**Test Option 1 first (expand taxonomy) because:**
1. **Fast validation** - can test in 1-2 hours vs days for pattern mining
2. **Advisor provided examples** - Match 1 & Match 2 suggest taxonomy expansion is expected
3. **36.1% → 80% gap is addressable** - ~50 new fields probably sufficient
4. **De-risks pattern mining** - if expansion works, pattern mining becomes optional optimization

**If Option 1 succeeds:**
- Validate with Ascensus corpus (550 elections)
- If cross-vendor success ≥80%, proceed to crosswalk matching
- Pattern mining becomes future enhancement (not blocker)

**If Option 1 fails (<80% even with expanded taxonomy):**
- Confirms taxonomy enumeration is brittle (advisor's concern validated)
- Enables pattern mining with clear success criteria (what manual expansion couldn't solve)

---

## Open Questions for Advisor

1. **Taxonomy scope**: Should canonical fields cover meta-elections (feature enablement, effective dates) or just data elections (age, rates, schedules)?

2. **text_block handling**: 67 elections detected as text_block (36% of corpus). Should these:
   - Map to generic "other_text" fields (current behavior)?
   - Be excluded from compilation (mark as "requires manual review")?
   - Trigger LLM-based field generation?

3. **Match threshold**: 0.3 score threshold rejected all candidates for 117 elections. Should we:
   - Lower threshold to 0.2?
   - Use adaptive threshold (lower for text_block, higher for structured)?
   - Abstain with low confidence instead of failing?

4. **Pattern mining trigger**: Advisor said "if <80%, enable pattern mining." Should we try taxonomy expansion first, or go straight to pattern mining?

---

## Artifacts Created

### Code
- `src/compilation/signature_extractor.py` - Runtime pattern discovery engine
- `src/compilation/ceo_compiler_v2.py` - Discovery-first compiler with operator engine

### Schemas
- `schemas/ceo/ceo.struct_signature.schema.json` - 9 shape types
- `schemas/ceo/ceo.operators.json` - 4 generic operators
- `schemas/ceo/ceo.match_scoring.v0.2.json` - Updated scoring weights
- `schemas/ceo/ceo.dimension_lexicon.json` - Contribution type phrases

### Documentation
- `research/ceo_advisor_request/ceo_advisor_response_2.md` - Discovery-first architecture spec
- `research/ceo_advisor_request/IMPLEMENTATION_SUMMARY.md` - This document

---

## Success Metrics (From Advisor Response 2)

### Day 2 (Current)
- [x] Add Signature Extractor - DONE
- [x] Add Operator Engine with 4 primitives - DONE
- [x] Swap scorer to include StructureSigSim + DimensionMatch - DONE
- [x] Instrument compile to log discovery metrics - DONE
- [ ] **Run on all 732 elections** - Only ran 183 (Relius), need Ascensus too
- [ ] **If compile success ≥80%, keep iterating** - Got 36.1%, below target ❌
- [ ] **If <80%, enable pattern mining** - Decision point reached

### Week 1 (Target)
- [ ] Compile Match 2 examples (Relius + Ascensus Age 21)
- [ ] Both map to `eligibility.age` with correct structural variants
- [ ] Confidence ≥0.9
- [ ] 10× token reduction measured
- [ ] 90%+ accuracy on 4 test cases

---

**Bottom Line**: Discovery architecture works perfectly for **structure detection** (shapes, dimensions, operators), but fails at **semantic mapping** (canonical field matching) due to narrow taxonomy. Need decision: expand taxonomy manually (fast), or enable pattern mining (scalable)?
