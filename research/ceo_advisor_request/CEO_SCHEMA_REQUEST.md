# Request to Advisor: Canonical Election Ontology (CEO) Schema

**Date**: 2025-11-03
**Context**: Following advisor feedback on CEO approach, we're pivoting from prose-based embeddings to canonical schema compilation
**Goal**: Obtain starter CEO schema and compilation guidance for retirement plan Adoption Agreement elections

---

## What We're Building

**Architectural shift**:
```
OLD: Relius AA → embed(text) → cosine_sim → Ascensus AA
NEW: Relius AA → compile_to_CEO → match on canonical_field → Ascensus AA
```

**Key insight**: Pivot through canonical intermediate representation instead of direct vendor-to-vendor comparison.

This solves:
1. **Pairwise explosion**: N vendors = N mappings (to/from canonical), not N² mappings (all vendor pairs)
2. **Structural transformations**: Relius (1 age field + applies-to checkboxes) ↔ Ascensus (N age fields) both map to `eligibility.age`
3. **Token efficiency**: Canonical schema is shorter than prose (~20 tokens vs ~40-400 tokens)
4. **Deterministic matching**: 95% of score is structural (field type, domain, constraints), 5% is LLM tie-breaking

---

## What We Need from Advisor

### 1. Canonical Field Taxonomy (The Schema Itself)

**Request**: Define the canonical field hierarchy for core retirement plan domains.

**Domains to cover**:
- Eligibility (age, service, entry dates, excluded classes)
- Vesting (schedules, service crediting, cliff vs graded)
- Contributions (employer match, profit sharing, safe harbor, QACA/EACA, catch-up)
- Loans (availability, limits, repayment terms)
- Distributions (in-service, hardship, age 59½, required minimum distributions)

**For each canonical field, specify**:
- **Field path** (e.g., `eligibility.age`, `eligibility.service.years`, `vesting.schedule.cliff`)
- **Value type** (integer, enum, duration, percentage, boolean, formula)
- **Units** (years, months, hours, dollars, percent, N/A)
- **Typical constraints** (min/max ranges, allowed enums, dependencies)
- **Common synonyms** (vendor jargon variations that map to same canonical field)

**Example format** (illustrative):
```json
{
  "canonical_field": "eligibility.age",
  "description": "Minimum age requirement for plan participation",
  "value_type": "integer",
  "units": "years",
  "constraints": {
    "min": 0,
    "max": 21,
    "note": "IRC 410(a)(1)(A)(i) limits to age 21"
  },
  "applies_to_dimensions": ["contribution_type", "participant_class"],
  "vendor_synonyms": [
    "Age Requirement",
    "Minimum Age",
    "Age 21",
    "Attainment of Age"
  ]
}
```

### 2. Structural Variant Catalog (How Vendors Differ)

**Request**: Document known vendor implementation patterns for the same canonical field.

**Why this matters**: Same canonical field can have different UI/form structures across vendors.

**Example**: `eligibility.age`

**Relius implementation**:
- Single age value (textbox or checkbox for "Age 21")
- Separate "applies to" checkboxes (All Contributions, Elective Deferrals, Matching, Nonelective)
- Structure: 1 age field + 4 contribution-type checkboxes

**Ascensus implementation**:
- Multiple age fields, one per contribution type
- Each field is a combo (checkbox + textbox)
- Structure: N combo fields (Pre-Tax Age, Roth Age, Matching Age, Employer Age)

**Both map to**: `eligibility.age` with metadata:
- Relius: `vendor_implementation = "single_age_with_applies_to"`
- Ascensus: `vendor_implementation = "age_per_contribution_type"`

**Request format**:
```json
{
  "canonical_field": "eligibility.age",
  "structural_variants": [
    {
      "variant_id": "single_age_with_applies_to",
      "vendors": ["Relius", "ftwilliam"],
      "structure": "1 age field + N contribution-type checkboxes",
      "transformation_rules": "Replicate age value across selected contribution types"
    },
    {
      "variant_id": "age_per_contribution_type",
      "vendors": ["Ascensus"],
      "structure": "N combo fields (checkbox + age textbox per contribution type)",
      "transformation_rules": "Each contribution type has independent age value"
    }
  ]
}
```

### 3. Compilation Prompt Template (LLM Instructions)

**Request**: Prompt template for compiling v5.2 extraction JSON → canonical schema tags.

**Input format** (what we have):
```json
{
  "section_path": "Q_1.03",
  "question_text": "f. Age 21",
  "section_context": "Eligibility Conditions",
  "kind": "single_select",
  "form_elements": [
    {"element_type": "checkbox", "element_sequence": 1},
    {"element_type": "checkbox", "element_sequence": 2}
  ],
  "options": [
    {"label": "a", "option_text": "All Contributions"},
    {"label": "b", "option_text": "Elective Deferrals/SH"},
    {"label": "c", "option_text": "Matching"}
  ]
}
```

**Output format** (what we need):
```json
{
  "canonical_field": "eligibility.age",
  "vendor_implementation": "single_age_with_applies_to",
  "field_type": "integer+checkboxes",
  "value_type": "integer",
  "units": "years",
  "constraints": {"max": 21},
  "applies_to_dimensions": ["contribution_type"],
  "dependency_bundle": {
    "parent": "Q_1.03",
    "required_children": ["contribution_type_selection"]
  },
  "provenance": {
    "vendor": "relius",
    "section_path": "Q_1.03",
    "question_text": "f. Age 21"
  }
}
```

**Prompt should cover**:
- How to infer `canonical_field` from `section_context` + `question_text` + `options`
- How to detect structural variants (single field vs array, checkbox vs combo, etc.)
- How to extract constraints from question text ("not more than 21" → max=21)
- How to identify dependency bundles (parent elections with required children)
- When to assign high confidence vs low confidence (ambiguous cases)
- Examples of edge cases (e.g., "Age 21" vs "Entry Date" - both eligibility but different canonical fields)

**Ambiguous cases to address**:
1. `eligibility.age` vs `eligibility.entry_date` (both govern when someone can join)
2. `vesting.schedule` vs `vesting.service_crediting` (both affect vesting, different canonical fields)
3. `contributions.match_formula` vs `contributions.match_limit` (related but distinct)

---

## How We'll Use This

### Step 1: Compile Both Vendors to Canonical
```
Relius AA (182 elections) → CEO Compiler → 182 canonical fields
Ascensus AA (550 elections) → CEO Compiler → 550 canonical fields
```

### Step 2: Match on Canonical Field (Deterministic)
```
Filter: canonical_field == "eligibility.age"
→ Relius: 1 election (Q_1.03)
→ Ascensus: 4 elections (Q_2.01.pretax, Q_2.01.roth, Q_2.01.matching, Q_2.01.employer)
```

### Step 3: Compare Structural Variants
```
Relius: vendor_implementation = "single_age_with_applies_to"
Ascensus: vendor_implementation = "age_per_contribution_type"
→ Structural transformation detected
→ Transformation rule: Replicate Relius age across selected Ascensus contribution types
```

### Step 4: Property Tests (Counterfactual Probes)
```
Probe: age=21, applies_to=[elective, matching]

Relius result: Age 21 for elective deferrals, Age 21 for matching
Ascensus result: Age 21 for pre-tax, Age 21 for matching

Match: TRUE (functional equivalence confirmed)
```

---

## Success Criteria

**We'll know the CEO approach works if**:
1. ✅ Compiler correctly tags 90%+ of elections with canonical fields (10% ambiguous/low confidence is acceptable)
2. ✅ Structural variants are detected and documented
3. ✅ Match 2 example (Age 21 eligibility) correctly identifies structural transformation
4. ✅ Property tests validate functional equivalence
5. ✅ Token usage reduced by 10× (from ~40-400 tokens to ~20-40 tokens per election)
6. ✅ Match accuracy improves from 75% (current) to 90%+ (CEO approach)

---

## Timeline

**Week 1** (with advisor's schema):
- Day 1-2: Implement CEO compiler (LLM-based with advisor's prompt template)
- Day 3-4: Compile test corpus (182 Relius + 550 Ascensus elections)
- Day 5: Validate on 4 test cases from embedding quality test

**Week 2**:
- Day 6-7: Implement field-level scoring (TypeMatch, LabelSim, DomainSim, ConstraintCompat)
- Day 8-9: Add global alignment solver (Hungarian algorithm)
- Day 10: Property tests (counterfactual probes) on matched pairs

**Exit Criteria**:
- Match 2 (Age 21) correctly identified as structural transformation
- 90%+ accuracy on 4 test cases (vs 75% current)
- Token reduction validated (measure before/after)

---

## Deliverables Requested from Advisor

1. **Canonical field taxonomy JSON** (5 domains: Eligibility, Vesting, Contributions, Loans, Distributions)
2. **Structural variant catalog** (known vendor implementation patterns per canonical field)
3. **Compilation prompt template** (LLM instructions for v5.2 JSON → canonical schema)
4. **Starter scoring config** (weights for TypeMatch, LabelSim, DomainSim, etc.)

**Format**: JSON schema + markdown documentation + prompt template (text file)

**Timeline**: No rush, but ideally within 1 week to maintain momentum

---

## Questions for Advisor

1. Should the compiler be LLM-based (flexible, handles ambiguity) or rule-based (deterministic, faster)?
2. How granular should the canonical field taxonomy be? (e.g., `eligibility.age` vs `eligibility.age.matching` vs `eligibility.age.matching.pretax`)
3. Should we handle rare/vendor-specific fields (e.g., DATAIR-only elections) or focus on common fields first?
4. What's the right balance between canonical schema coverage (exhaustive) vs compilation complexity (practical)?

---

**Thank you for this breakthrough insight. The pivot through canonical schema is exactly what we need to solve the pairwise explosion and structural transformation problems.**
