# Manual Match Examples (Human Analysis)

**Date**: 2025-11-03
**Analyst**: Sergio DuBois (domain expert)
**Context**: Cross-vendor conversion (Relius → Ascensus)

These are real matches identified during manual review of test elections. They illustrate why canonical schema compilation is needed over prose-based embeddings.

---

## Match 1: Sole Proprietorship Election (Simple/Exact Match)

### Source (Relius)
- **Question**: Unknown (not provided in notes)
- **Election Text**: "Sole Proprietorship"
- **Structure**: Single checkbox or selection

### Target (Ascensus)
- **Question**: Unknown (not provided in notes)
- **Election Text**: "Sole Proprietorship"
- **Structure**: Single checkbox or selection

### Analysis
- **Match Type**: Exact match
- **Difficulty**: Simple - same text, same structure, same meaning
- **AA-Only Sufficient**: Yes - question text alone is enough
- **Structural Transformation**: None

### Human Insight
> "Both documents have same election, same structure. Easy case for AA-only matching."

**Implication for CEO approach**: This would be trivial - both compile to same canonical field with identical structure.

---

## Match 2: Age 21 Eligibility (Complex/Structural Transformation)

### Source (Relius Q 1.03)
```json
{
  "question_number": "1.03",
  "question_text": "f. Age 21",
  "section_context": "Eligibility Conditions",
  "kind": "single_select",
  "options": [
    {"label": "a", "option_text": "All Contributions"},
    {"label": "b", "option_text": "Elective Deferrals/SH"},
    {"label": "c", "option_text": "Matching"},
    {"label": "d", "option_text": "Nonelective"}
  ]
}
```

**Structure**:
- 1 age value (Age 21)
- 4 checkboxes for contribution types (apply age requirement to selected types)
- Pattern: Single field + "applies to" checkboxes

### Target (Ascensus - Multiple Questions)
**Ascensus has SEPARATE age fields per contribution type:**

- Q 1.01: "The following age shall apply (select and complete all that apply):"
- Q 2.03: "Age Requirement"
- Possibly others for Roth, Matching, Employer contributions

**Structure**:
- N age fields (one per contribution type)
- Each field is a combo: checkbox + textbox (can specify different age per type)
- Pattern: Array of (checkbox + age value) combos

### Analysis
- **Match Type**: Close match with structural transformation
- **Difficulty**: Complex - different hierarchies, same intent
- **Structural Difference**:
  - Relius: 1 age → apply to selected contribution types
  - Ascensus: N ages (could be different values per contribution type)
- **Semantic Equivalence**: When all Ascensus age fields = 21, functionally equivalent to Relius Age 21 selected for all types
- **AA-Only Sufficient**: Yes, BUT requires option structure, not just question text

### Human Insight
> "AA-only CAN identify the match but needs option structure, not just question text. Different structural hierarchies but same intent."

### Why Prose-Based Embeddings Struggle
**V1 embedding (basic)**:
```
"[DOMAIN: Eligibility Conditions] f. Age 21"
```
- Only 40 chars of semantic content
- No structural information (1 field vs N fields)
- Misses "applies to" dimension entirely

**V2 embedding (hybrid)**:
```
"[DOMAIN: Eligibility Conditions] | Age 21 | Options: All Contributions, Elective Deferrals/SH, Matching, Nonelective"
```
- Adds option structure (120 chars)
- Improved similarity from 0.787 → 0.837
- Still doesn't capture structural transformation (1 field + checkboxes vs N combo fields)

### Why CEO Approach Would Work

**Relius compilation**:
```json
{
  "canonical_field": "eligibility.age",
  "vendor_implementation": "single_age_with_applies_to",
  "field_type": "integer+checkboxes",
  "value_type": "integer",
  "units": "years",
  "constraints": {"max": 21},
  "applies_to_dimensions": ["contribution_type"],
  "options": [
    {"dimension": "contribution_type", "values": ["all", "elective", "matching", "nonelective"]}
  ]
}
```

**Ascensus compilation** (for each age field):
```json
[
  {
    "canonical_field": "eligibility.age",
    "vendor_implementation": "age_per_contribution_type",
    "field_type": "combo[]",
    "value_type": "integer",
    "units": "years",
    "constraints": {"max": 21},
    "applies_to_dimensions": ["contribution_type"],
    "contribution_type": "elective"
  },
  {
    "canonical_field": "eligibility.age",
    "vendor_implementation": "age_per_contribution_type",
    "field_type": "combo[]",
    "value_type": "integer",
    "units": "years",
    "constraints": {"max": 21},
    "applies_to_dimensions": ["contribution_type"],
    "contribution_type": "matching"
  }
  // ... more for roth, employer, etc.
]
```

**Matching logic**:
1. Filter by `canonical_field == "eligibility.age"` → deterministic match
2. Detect structural transformation: `single_age_with_applies_to` ↔ `age_per_contribution_type`
3. Property test (counterfactual probe):
   - Input: age=21, applies_to=[elective, matching]
   - Relius result: Age 21 for elective, Age 21 for matching
   - Ascensus result: Age 21 for elective combo, Age 21 for matching combo
   - Functional equivalence: ✅ TRUE

**Transformation rule**:
```
Relius Q 1.03 (age=21, selected=[elective, matching])
  → Ascensus Q 2.03.elective (age=21, checked=true)
  → Ascensus Q 2.03.matching (age=21, checked=true)
  → Ascensus Q 2.03.roth (unchecked)
  → Ascensus Q 2.03.employer (unchecked)
```

---

## Key Lessons for Advisor

### 1. Structural Variants Exist in Production
- Same canonical concept (eligibility.age) implemented differently across vendors
- Need catalog of known structural patterns (single field + applies-to, N combo fields, etc.)

### 2. Option Structure is Critical
- Question text alone is insufficient ("Age 21" vs "Age Requirement")
- Options define the domain space (contribution types, participant classes, etc.)
- Options reveal structural patterns (checkboxes vs combos vs hierarchical)

### 3. Terse Text Limits Embeddings
- AA elections average 40-120 chars of semantic content
- Embeddings trained on paragraphs (300+ chars)
- Prose-based approach plateaus at ~0.80-0.84 similarity (below 0.85 threshold)

### 4. Deterministic Matching is Possible
- When both sides compile to same `canonical_field`, match is deterministic
- Structural transformation can be detected via `vendor_implementation` metadata
- Property tests validate functional equivalence (not just textual similarity)

---

## Success Criteria for CEO Approach

Based on these manual matches, the CEO approach should:

1. ✅ **Match 1**: Trivially match Sole Proprietorship elections (exact canonical field + structure)
2. ✅ **Match 2**: Detect Age 21 eligibility across structural transformation
3. ✅ **Structural catalog**: Document "single_age_with_applies_to" vs "age_per_contribution_type" patterns
4. ✅ **Transformation rules**: Generate mapping logic (replicate age across selected contribution types)
5. ✅ **Confidence scoring**: 95%+ confidence for deterministic matches (vs 80-84% for prose-based)

---

**Bottom Line**: These examples prove that structure matters more than prose. The CEO schema should prioritize typed fields, constraints, and vendor implementation patterns over textual similarity.
