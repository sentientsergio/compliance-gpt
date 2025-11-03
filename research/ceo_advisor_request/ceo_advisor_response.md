Sergio — shipping a usable v0.1 now so you can wire the compiler this week.

---

## TL;DR

- **Artifacts below:**

  1. Canonical field taxonomy (JSON),
  2. Structural variant catalog (JSON),
  3. Compilation prompt template (LLM-ready),
  4. Starter scoring config (weights + rules).

- **Design stance:** Canonical-first, dimensioned by `contribution_type` and `participant_class`. Structural variants captured via `vendor_implementation` + `transformation_rules`.

- **Compiler approach:** **Hybrid**: rule-first for 95% (types/domains/constraints) with a **small LLM tie-breaker**. This keeps it deterministic, fast, and token-thin.

- **Granularity:** Keep canonical fields **domain-level** (e.g., `eligibility.age`) and push contribution-type granularity into **dimensions**. Do **not** explode the field path (avoid `eligibility.age.matching.pretax`).

- **Scope:** Start with **common fields only** (what’s in Relius/Ascensus) and mark rare/vendor‑specific as `vendor_extension.*`. Expand incrementally.

- **Why the pivot is right:** Embeddings plateaued on structure-heavy items (avg top sim ~0.796 on your v2 test), exactly where CEO shines.

---

## Actions (you can do today)

1. **Drop in** the JSON Schema + Taxonomy below as `ceo.schema.json` and `ceo.taxonomy.json`.
2. Wire the **Compiler Prompt** into your v5.2 extraction pipeline (same keys; deterministic mapping). Spec here matches your v5.2 format.
3. Implement the **scoring** function with provided weights.
4. Validate against the two concrete examples already in your samples:

   - Relius `f. Age 21` with applies-to checkboxes → `eligibility.age` + `single_age_with_applies_to`.
   - Ascensus `Age Requirement` per contribution type → `eligibility.age` + `age_per_contribution_type`.

---

## Context anchors (from your samples)

- **Relius – Age 21** under “Eligibility Conditions” with applies-to checkboxes (All Contributions, Elective Deferrals/SH, Matching, Nonelective). This is the classic **single age + applies-to** pattern.
- **Ascensus – Age Requirement** multi-select lists Pre‑Tax, Roth, Matching, Profit Sharing, Safe Harbor/QACA, QNEC — distinct per-type age settings. That’s **age per contribution type**.
- **Entry Date**: Relius toggles “same for all” vs “different dates apply.” Ascensus offers frequency presets and “Other” with text fields per contribution type.
- **Service/Vesting**: Relius includes Service Crediting method (elapsed time, hours, equivalency) and standard vesting presets (6‑year graded, 3‑year cliff, etc.). Ascensus expresses vesting and hardship availability with discrete election items (e.g., beneficiary hardship).
- **Loans**: Relius “A.01 Loan limitations” mirrors common knobs: min loan, count, home-loan term, account restrictions. Good anchors for the Loans domain.

---

# ARTIFACT 1 — Canonical JSON Schema (for CEO nodes)

> Save as `ceo.schema.json`

```json
{
  "$id": "https://ceo.sentientsergio/schema/ceo.schema.json",
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Canonical Election Ontology (CEO) Schema",
  "type": "object",
  "required": [
    "canonical_field",
    "description",
    "value_type",
    "units",
    "constraints",
    "applies_to_dimensions",
    "vendor_synonyms"
  ],
  "properties": {
    "canonical_field": {
      "type": "string",
      "pattern": "^(eligibility|vesting|contributions|loans|distributions)(\\.[a-zA-Z0-9_]+)+$",
      "description": "Dot-path of the canonical field (domain-scoped)."
    },
    "description": { "type": "string" },
    "domain": {
      "type": "string",
      "enum": [
        "eligibility",
        "vesting",
        "contributions",
        "loans",
        "distributions"
      ]
    },
    "value_type": {
      "type": "string",
      "enum": [
        "integer",
        "decimal",
        "percentage",
        "currency",
        "boolean",
        "enum",
        "string",
        "duration",
        "formula",
        "schedule",
        "object",
        "array"
      ]
    },
    "units": {
      "type": "string",
      "enum": [
        "years",
        "months",
        "days",
        "hours",
        "hours_of_service",
        "dollars",
        "percent",
        "N/A"
      ]
    },
    "constraints": {
      "type": "object",
      "properties": {
        "min": { "type": ["number", "integer"] },
        "max": { "type": ["number", "integer"] },
        "step": { "type": ["number", "integer"] },
        "allowed_enums": { "type": "array", "items": { "type": "string" } },
        "regex": { "type": "string" },
        "dependencies": { "type": "array", "items": { "type": "string" } },
        "notes": { "type": "string" }
      },
      "additionalProperties": true
    },
    "applies_to_dimensions": {
      "type": "array",
      "items": { "$ref": "#/$defs/dimensionName" }
    },
    "dimension_values": {
      "type": "object",
      "description": "Optional: bind a specific value for a dimension in this node.",
      "additionalProperties": true
    },
    "vendor_synonyms": { "type": "array", "items": { "type": "string" } },
    "examples": { "type": "array", "items": { "type": "string" } },
    "notes": { "type": "string" }
  },
  "$defs": {
    "dimensionName": {
      "type": "string",
      "enum": [
        "contribution_type",
        "participant_class",
        "employment_status",
        "union_status",
        "work_location"
      ]
    },
    "dimensions": {
      "type": "object",
      "properties": {
        "contribution_type": {
          "type": "string",
          "enum": [
            "all",
            "pretax",
            "roth",
            "matching",
            "nonelective",
            "profit_sharing",
            "safe_harbor",
            "qaca_safe_harbor",
            "qnec"
          ]
        },
        "participant_class": {
          "type": "string",
          "enum": [
            "all",
            "salaried",
            "hourly",
            "part_time",
            "seasonal",
            "temporary",
            "leased",
            "nonresident_alien",
            "collectively_bargained",
            "highly_compensated",
            "non_highly_compensated"
          ]
        },
        "employment_status": {
          "type": "string",
          "enum": ["active", "terminated", "disabled", "retired"]
        },
        "union_status": {
          "type": "string",
          "enum": ["union", "non_union"]
        },
        "work_location": {
          "type": "string",
          "enum": ["all", "us", "non_us", "state_specific"]
        }
      },
      "additionalProperties": false
    },
    "vestingSchedule": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": { "type": "string", "enum": ["cliff", "graded", "other"] },
        "cliff_years": { "type": "integer", "minimum": 0, "maximum": 7 },
        "graded": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["year", "percent_vested"],
            "properties": {
              "year": { "type": "integer", "minimum": 0, "maximum": 7 },
              "percent_vested": {
                "type": "number",
                "minimum": 0,
                "maximum": 100
              }
            }
          }
        },
        "text": { "type": "string" }
      }
    }
  },
  "additionalProperties": false
}
```

---

# ARTIFACT 2 — Canonical Field Taxonomy (v0.1)

> Save as `ceo.taxonomy.json`
> Scope: core, high-frequency AA elections across 5 domains. Constraints reflect common plan practice and Code guardrails (not legal advice).

```json
{
  "version": "0.1",
  "updated": "2025-11-03",
  "fields": [
    {
      "canonical_field": "eligibility.age",
      "domain": "eligibility",
      "description": "Minimum age requirement to become eligible/enter the plan for the specified contribution(s).",
      "value_type": "integer",
      "units": "years",
      "constraints": {
        "min": 0,
        "max": 21,
        "notes": "Typical ceiling aligned with IRC 410(a). If shown as 'Age 21' line item, treat as max=21."
      },
      "applies_to_dimensions": ["contribution_type", "participant_class"],
      "vendor_synonyms": [
        "Age Requirement",
        "Minimum Age",
        "Attainment of Age",
        "Age 21"
      ]
    },
    {
      "canonical_field": "eligibility.service.method",
      "domain": "eligibility",
      "description": "Service crediting method used for eligibility.",
      "value_type": "enum",
      "units": "N/A",
      "constraints": {
        "allowed_enums": ["elapsed_time", "hours_of_service", "equivalency"]
      },
      "applies_to_dimensions": ["participant_class"],
      "vendor_synonyms": [
        "Service for eligibility basis",
        "Method of Determining Service (eligibility)"
      ]
    },
    {
      "canonical_field": "eligibility.service.years_required",
      "domain": "eligibility",
      "description": "Years (or periods) of service required to become eligible.",
      "value_type": "decimal",
      "units": "years",
      "constraints": {
        "min": 0,
        "max": 2,
        "step": 0.5,
        "notes": "Common cap ~2 years subject to vesting immediacy rules."
      },
      "applies_to_dimensions": ["contribution_type", "participant_class"],
      "vendor_synonyms": [
        "Years of Eligibility Service",
        "Period of Service required"
      ]
    },
    {
      "canonical_field": "eligibility.service.hours_required",
      "domain": "eligibility",
      "description": "Hours-of-Service threshold for a Year of Service (eligibility).",
      "value_type": "integer",
      "units": "hours_of_service",
      "constraints": { "min": 0, "max": 1000, "step": 1 },
      "applies_to_dimensions": ["participant_class"],
      "vendor_synonyms": [
        "Number of Hours of Service required",
        "Hours requirement for eligibility"
      ]
    },
    {
      "canonical_field": "eligibility.entry.frequency",
      "domain": "eligibility",
      "description": "Entry date frequency/pattern.",
      "value_type": "enum",
      "units": "N/A",
      "constraints": {
        "allowed_enums": [
          "monthly",
          "quarterly",
          "semi_annual",
          "annual",
          "other"
        ]
      },
      "applies_to_dimensions": ["contribution_type"],
      "vendor_synonyms": [
        "Entry Date",
        "Eligibility and Entry timing",
        "Entry date (select one)"
      ]
    },
    {
      "canonical_field": "eligibility.entry.other_text",
      "domain": "eligibility",
      "description": "Custom entry date definition when 'Other' is selected.",
      "value_type": "string",
      "units": "N/A",
      "constraints": { "regex": ".{0,500}" },
      "applies_to_dimensions": ["contribution_type"],
      "vendor_synonyms": ["Other entry date"]
    },
    {
      "canonical_field": "eligibility.exclusions.classes",
      "domain": "eligibility",
      "description": "Participant classes excluded from eligibility.",
      "value_type": "array",
      "units": "N/A",
      "constraints": {
        "allowed_enums": [
          "leased",
          "nonresident_alien",
          "collectively_bargained",
          "seasonal",
          "temporary",
          "part_time",
          "union",
          "other"
        ]
      },
      "applies_to_dimensions": ["participant_class"],
      "vendor_synonyms": ["Excluded Employees", "Exclusions"]
    },

    {
      "canonical_field": "vesting.schedule.matching",
      "domain": "vesting",
      "description": "Vesting schedule applicable to employer matching contributions.",
      "value_type": "schedule",
      "units": "N/A",
      "constraints": {
        "dependencies": [
          "vesting.service.method",
          "vesting.service.hours_threshold"
        ]
      },
      "applies_to_dimensions": [],
      "vendor_synonyms": [
        "Vesting schedule - matching",
        "Part B - Vesting Schedule for Employer Matching"
      ]
    },
    {
      "canonical_field": "vesting.schedule.nonelective",
      "domain": "vesting",
      "description": "Vesting schedule applicable to employer nonelective/profit sharing contributions.",
      "value_type": "schedule",
      "units": "N/A",
      "constraints": {
        "dependencies": [
          "vesting.service.method",
          "vesting.service.hours_threshold"
        ]
      },
      "applies_to_dimensions": [],
      "vendor_synonyms": [
        "Vesting schedule - nonelective",
        "Vesting of Participant's Interest"
      ]
    },
    {
      "canonical_field": "vesting.service.method",
      "domain": "vesting",
      "description": "Service crediting method for vesting.",
      "value_type": "enum",
      "units": "N/A",
      "constraints": {
        "allowed_enums": ["elapsed_time", "hours_of_service", "equivalency"]
      },
      "applies_to_dimensions": [],
      "vendor_synonyms": [
        "Service for vesting basis",
        "Service Required for Vesting"
      ]
    },
    {
      "canonical_field": "vesting.service.hours_threshold",
      "domain": "vesting",
      "description": "Hours defining a Year of Service for vesting.",
      "value_type": "integer",
      "units": "hours_of_service",
      "constraints": { "min": 0, "max": 1000 },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Hours requirement (vesting)"]
    },
    {
      "canonical_field": "vesting.waiver.effective_date_all",
      "domain": "vesting",
      "description": "Vesting waiver (100% vested) for participants employed as of a date (all contrib. sources).",
      "value_type": "string",
      "units": "N/A",
      "constraints": { "regex": "^[0-9\\-/]{0,10}$" },
      "applies_to_dimensions": [],
      "vendor_synonyms": [
        "Vesting waiver - all contributions",
        "100% vested if employed on"
      ]
    },
    {
      "canonical_field": "vesting.waiver.effective_date_by_source",
      "domain": "vesting",
      "description": "Vesting waiver dates keyed by contribution source.",
      "value_type": "object",
      "units": "N/A",
      "constraints": {},
      "applies_to_dimensions": ["contribution_type"],
      "vendor_synonyms": ["Vesting waiver - designated contributions"]
    },

    {
      "canonical_field": "contributions.match.formula.type",
      "domain": "contributions",
      "description": "Type of matching formula.",
      "value_type": "enum",
      "units": "N/A",
      "constraints": {
        "allowed_enums": [
          "fixed_uniform",
          "fixed_tiered",
          "fixed_by_yos",
          "discretionary_tiered",
          "other"
        ]
      },
      "applies_to_dimensions": [],
      "vendor_synonyms": [
        "Matching formula",
        "Fixed - uniform rate/amount",
        "Fixed - tiered",
        "Discretionary - tiered",
        "Years of Service based",
        "Other formula"
      ]
    },
    {
      "canonical_field": "contributions.match.formula.fixed_rate_percent",
      "domain": "contributions",
      "description": "Uniform match % of deferrals.",
      "value_type": "percentage",
      "units": "percent",
      "constraints": { "min": 0, "max": 200, "step": 0.01 },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Matching percentage", "Uniform match rate"]
    },
    {
      "canonical_field": "contributions.match.max.limit_type",
      "domain": "contributions",
      "description": "Type of match maximum limit.",
      "value_type": "enum",
      "units": "N/A",
      "constraints": {
        "allowed_enums": ["dollar", "percent_of_compensation", "none"]
      },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Maximum matching contribution"]
    },
    {
      "canonical_field": "contributions.match.max.dollar",
      "domain": "contributions",
      "description": "Dollar cap on match.",
      "value_type": "currency",
      "units": "dollars",
      "constraints": { "min": 0, "max": 1000000, "step": 1 },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Maximum match $"]
    },
    {
      "canonical_field": "contributions.match.max.percent_of_compensation",
      "domain": "contributions",
      "description": "Percent-of-comp cap on match.",
      "value_type": "percentage",
      "units": "percent",
      "constraints": { "min": 0, "max": 100, "step": 0.01 },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Maximum match % of Comp"]
    },
    {
      "canonical_field": "contributions.catch_up.match_applies",
      "domain": "contributions",
      "description": "Whether catch-up deferrals receive match.",
      "value_type": "boolean",
      "units": "N/A",
      "constraints": {},
      "applies_to_dimensions": [],
      "vendor_synonyms": [
        "Catch-up matched",
        "Matching Contributions re: Catch-up"
      ]
    },
    {
      "canonical_field": "contributions.safe_harbor.type",
      "domain": "contributions",
      "description": "Safe harbor design elected.",
      "value_type": "enum",
      "units": "N/A",
      "constraints": {
        "allowed_enums": [
          "none",
          "basic_match",
          "enhanced_match",
          "nonelective_3",
          "qaca_basic",
          "qaca_enhanced"
        ]
      },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Safe Harbor", "QACA Safe Harbor"]
    },
    {
      "canonical_field": "contributions.auto_enroll.default_rate",
      "domain": "contributions",
      "description": "Default deferral rate for automatic enrollment (where applicable).",
      "value_type": "percentage",
      "units": "percent",
      "constraints": { "min": 0, "max": 20, "step": 0.5 },
      "applies_to_dimensions": [],
      "vendor_synonyms": [
        "Automatic enrollment default rate",
        "QACA default rate"
      ]
    },
    {
      "canonical_field": "contributions.auto_enroll.auto_escalation.enabled",
      "domain": "contributions",
      "description": "Whether automatic escalation applies.",
      "value_type": "boolean",
      "units": "N/A",
      "constraints": {},
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Auto-escalation", "Automatic increase"]
    },
    {
      "canonical_field": "contributions.auto_enroll.auto_escalation.step",
      "domain": "contributions",
      "description": "Annual escalation step if enabled.",
      "value_type": "percentage",
      "units": "percent",
      "constraints": { "min": 0, "max": 10, "step": 0.5 },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Escalation increment"]
    },

    {
      "canonical_field": "loans.available",
      "domain": "loans",
      "description": "Whether participant loans are permitted.",
      "value_type": "boolean",
      "units": "N/A",
      "constraints": {},
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Loans permitted", "Participant loans"]
    },
    {
      "canonical_field": "loans.min_amount",
      "domain": "loans",
      "description": "Minimum loan amount.",
      "value_type": "currency",
      "units": "dollars",
      "constraints": { "min": 0, "max": 100000, "step": 1 },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Minimum loan $"]
    },
    {
      "canonical_field": "loans.max_outstanding_count",
      "domain": "loans",
      "description": "Max number of outstanding loans.",
      "value_type": "integer",
      "units": "N/A",
      "constraints": { "min": 0, "max": 10 },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Number of loans outstanding"]
    },
    {
      "canonical_field": "loans.home_loan_term_years",
      "domain": "loans",
      "description": "Term for primary residence loans.",
      "value_type": "integer",
      "units": "years",
      "constraints": { "min": 1, "max": 30 },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Home loan term", "Primary residence loan term"]
    },
    {
      "canonical_field": "loans.allowed_account_sources",
      "domain": "loans",
      "description": "Account sources eligible for loans.",
      "value_type": "array",
      "units": "N/A",
      "constraints": {
        "allowed_enums": [
          "pretax",
          "roth",
          "matching",
          "nonelective",
          "profit_sharing",
          "rollover",
          "qaca_safe_harbor",
          "qnec"
        ]
      },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Account restrictions for loans"]
    },
    {
      "canonical_field": "loans.hardship_or_necessity_only",
      "domain": "loans",
      "description": "Loans restricted to hardship/necessity.",
      "value_type": "boolean",
      "units": "N/A",
      "constraints": {},
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Loans only for hardship or necessity"]
    },

    {
      "canonical_field": "distributions.in_service.age_min",
      "domain": "distributions",
      "description": "Minimum age for in-service withdrawal (non-hardship).",
      "value_type": "decimal",
      "units": "years",
      "constraints": {
        "min": 0,
        "max": 70,
        "step": 0.5,
        "notes": "Commonly 59.5"
      },
      "applies_to_dimensions": ["contribution_type"],
      "vendor_synonyms": ["In-service at age 59½", "Age-based in-service"]
    },
    {
      "canonical_field": "distributions.hardship.allowed",
      "domain": "distributions",
      "description": "Whether hardship distributions are permitted.",
      "value_type": "boolean",
      "units": "N/A",
      "constraints": {},
      "applies_to_dimensions": ["contribution_type"],
      "vendor_synonyms": ["Hardship distributions permitted"]
    },
    {
      "canonical_field": "distributions.hardship.beneficiary_allowed",
      "domain": "distributions",
      "description": "Hardship due to primary beneficiary hardship allowed.",
      "value_type": "boolean",
      "units": "N/A",
      "constraints": {},
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Beneficiary hardship availability"]
    },
    {
      "canonical_field": "distributions.rmd.rule_source",
      "domain": "distributions",
      "description": "Indicates RMD is governed by statutory/plan defaults (no elective choice).",
      "value_type": "enum",
      "units": "N/A",
      "constraints": { "allowed_enums": ["by_law", "plan_specific"] },
      "applies_to_dimensions": [],
      "vendor_synonyms": ["Required Minimum Distributions"]
    }
  ]
}
```

**Anchors to your samples:**

- `eligibility.age` patterns and dimensioning map directly from Relius “f. Age 21” (applies-to options) and Ascensus “Age Requirement” per source.
- `eligibility.entry.frequency`/`other_text` align to both vendors’ entry-date structures (same-for-all vs per-source fill-ins).
- `vesting.schedule.*` reflect Relius preset menus and per-source vesting chunks; Ascensus expresses similar schedules via part-based items.
- `loans.*` derived from Relius “A.01 Loan limitations” options.
- `distributions.hardship.beneficiary_allowed` mirrors Ascensus’ explicit yes/no on beneficiary hardship.

---

# ARTIFACT 3 — Structural Variant Catalog (v0.1)

> Save as `ceo.structural_variants.json`

```json
{
  "version": "0.1",
  "updated": "2025-11-03",
  "variants": [
    {
      "canonical_field": "eligibility.age",
      "structural_variants": [
        {
          "variant_id": "single_age_with_applies_to",
          "vendors": ["Relius", "ftwilliam"],
          "structure": "One age line (often 'Age 21') plus N checkboxes for contribution types.",
          "detection_rules": [
            "question_text contains 'Age' and numeric (e.g., 21) OR a single numeric entry",
            "options include contribution-type labels",
            "kind includes checkboxes"
          ],
          "transformation_rules": "Replicate the age value across selected contribution types; absent checkbox ⇒ no mapping for that type.",
          "evidence": "Relius ‘f. Age 21’ with All/Elective/Matching/Nonelective checkboxes.",
          "citations": ["turn0file0"]
        },
        {
          "variant_id": "age_per_contribution_type",
          "vendors": ["Ascensus"],
          "structure": "A separate age selection per contribution type (checkbox + textbox or per-type items).",
          "detection_rules": [
            "Parent/section labeled 'Age Requirement'",
            "Per-type rows: Pre-Tax, Roth, Matching, Profit Sharing, Safe Harbor/QACA, QNEC"
          ],
          "transformation_rules": "Each contribution type maps to an independent age node (same canonical field + dimension binding).",
          "evidence": "Ascensus ‘Age Requirement’ multi-select by source.",
          "citations": ["turn0file1"]
        }
      ]
    },
    {
      "canonical_field": "eligibility.entry.frequency",
      "structural_variants": [
        {
          "variant_id": "single_entry_toggle",
          "vendors": ["Relius"],
          "structure": "Single radio: 'Entry date same for all' vs 'different dates apply'.",
          "transformation_rules": "If 'same for all' → apply one frequency to contribution_type=all; else spawn child entries per type.",
          "citations": ["turn0file0"]
        },
        {
          "variant_id": "preset_or_other_per_type",
          "vendors": ["Ascensus"],
          "structure": "Preset frequencies (Monthly/Quarterly/…) plus 'Other' with per-type text fill-ins.",
          "transformation_rules": "Preset → direct enum. 'Other' → set frequency=other and pull per-type strings into eligibility.entry.other_text with dimension bindings.",
          "citations": ["turn0file1"]
        }
      ]
    },
    {
      "canonical_field": "eligibility.service.method",
      "structural_variants": [
        {
          "variant_id": "eligibility_service_menu",
          "vendors": ["Relius"],
          "structure": "Multi-select menu: elapsed time, hours of service (with alternatives), equivalency, numeric hours.",
          "transformation_rules": "Normalize to enum; if numeric hours present, set eligibility.service.hours_required.",
          "citations": ["turn0file0"]
        }
      ]
    },
    {
      "canonical_field": "vesting.schedule.nonelective",
      "structural_variants": [
        {
          "variant_id": "preset_schedule_catalog",
          "vendors": ["Relius"],
          "structure": "Checkboxes for '6-year graded', '4-year graded', '3-year cliff', or 'Other' with free grid.",
          "transformation_rules": "Map presets to schedule.type and graded/cliff parameters; Other → schedule.text.",
          "citations": ["turn0file0"]
        },
        {
          "variant_id": "part_based_vesting",
          "vendors": ["Ascensus"],
          "structure": "Part B with option sets per contribution source.",
          "transformation_rules": "Bind schedule objects per source (matching vs profit sharing) to the appropriate canonical fields.",
          "citations": ["turn0file1"]
        }
      ]
    },
    {
      "canonical_field": "contributions.match.formula.type",
      "structural_variants": [
        {
          "variant_id": "formula_family_with_fill_ins",
          "vendors": ["Relius"],
          "structure": "One-of formula family (fixed, tiered, YOS, discretionary) with optional 'Other: text'.",
          "transformation_rules": "Set enum; capture supplemental percentages/tiers into adjacent canonical fields.",
          "citations": ["turn0file0"]
        }
      ]
    },
    {
      "canonical_field": "contributions.catch_up.match_applies",
      "structural_variants": [
        {
          "variant_id": "explicit_yes_no",
          "vendors": ["Ascensus"],
          "structure": "Single-select Yes/No question tied to catch-up matching.",
          "transformation_rules": "Map Yes→true, No→false.",
          "citations": ["turn0file1"]
        }
      ]
    },
    {
      "canonical_field": "loans.available",
      "structural_variants": [
        {
          "variant_id": "loan_program_switch_with_limits",
          "vendors": ["Relius"],
          "structure": "Menu with suboptions (min $, max loans, home loan term, account restrictions, hardship-only).",
          "transformation_rules": "Set loans.available=true if menu present; map each suboption to respective canonical fields.",
          "citations": ["turn0file0"]
        }
      ]
    },
    {
      "canonical_field": "distributions.hardship.beneficiary_allowed",
      "structural_variants": [
        {
          "variant_id": "beneficiary_hardship_yes_no",
          "vendors": ["Ascensus"],
          "structure": "Single-select permitting hardship due to primary beneficiary.",
          "transformation_rules": "Yes→true, No→false.",
          "citations": ["turn0file1"]
        }
      ]
    }
  ]
}
```

---

# ARTIFACT 4 — Compiler Prompt Template (LLM-ready)

> Save as `ceo.compiler.prompt.txt`
> Input objects are your **v5.2 extraction** nodes (same keys as your spec). The mapping below assumes one provision/election at a time. Spec reference: “AA Extraction v5.2 — Provisions + Form Elements (Enhanced Provenance)”.

```
SYSTEM
You are the Canonical Election Ontology (CEO) compiler. Your job is to convert one extracted Adoption Agreement provision into a canonical field record.

PRINCIPLES
- Favor structure over prose. 95% of correctness comes from field type, domain, options, and constraints; only 5% from label text.
- Use CEO taxonomy and dimensions. Field paths are stable (e.g., eligibility.age). Granularity by contribution type and participant class goes into dimensions, NOT the field path.
- Detect vendor structural variants and set vendor_implementation accordingly.
- Extract constraints numerically when the text indicates maxima/minima (e.g., “Age 21” → max=21; “not to exceed 1,000” → max=1000).
- Build clear provenance.

INPUT
A single JSON object from the v5.2 extractor with (at least) these keys:
- pdf_page, section_number, section_title, section_path, parent_section, provision_text, section_context, kind, form_elements (array), options (array on same-level sibling if present).
If your input is a simplified upstream format, the keys may be: section_path, question_text, section_context, kind, form_elements, options. Handle either.

OUTPUT (JSON ONLY)
{
  "canonical_field": "<domain.path>",
  "vendor_implementation": "<variant_id or 'unknown'>",
  "field_type": "<one of: text|checkbox|checkboxes|radio|combo|grid|derived>",
  "value_type": "<from taxonomy>",
  "units": "<from taxonomy>",
  "constraints": { ... },
  "applies_to_dimensions": [ ... ],
  "dimension_values": { "<dimension>": "<value>" },   // include only if determinable here
  "dependency_bundle": {
    "parent": "<section_path or null>",
    "required_children": [ "<semantic child id(s) if any>" ]
  },
  "confidence": 0.0-1.0,
  "provenance": {
    "vendor": "<'relius'|'ascensus'|... if inferable>",
    "section_path": "<from input>",
    "section_context": "<from input>",
    "section_number": "<from input>",
    "evidence": "<first 120-200 chars of provision_text or option text>"
  }
}

DECISION STEPS

1) DOMAIN CANDIDATES
- Use section_context + section_title + provision_text to choose domain:
  * Eligibility: age, service, entry date, excluded classes.
  * Vesting: schedule presets, service for vesting, waiver.
  * Contributions: match, safe harbor, catch-up, auto-enroll.
  * Loans: availability, limits, terms.
  * Distributions: in-service age 59½, hardship (incl. beneficiary), RMD.
- If multiple domains present, pick the one the user can actually elect on this line (atomic field rule).

2) CANONICAL FIELD MATCH
- Match against taxonomy by synonyms and structure:
  * “Age 21”, “Age Requirement” → eligibility.age.
  * “Entry Date … Monthly/Quarterly/Semi-Annually/Annually/Other” → eligibility.entry.frequency (+ eligibility.entry.other_text if 'Other').
  * “Service … elapsed time/hours/equivalency” → eligibility.service.method or vesting.service.method based on context.
  * “Vesting … 6 year graded / 3 year cliff” → vesting.schedule.* for the applicable source.
  * “Matching contributions … fixed/tiered/other” → contributions.match.formula.type (+ related fields).
  * “Hardship due to primary beneficiary” → distributions.hardship.beneficiary_allowed.
  * “Loans … minimum loan / number of loans / home loan term” → loans.*.
- Prefer matches whose value_type + units align with visible controls (e.g., checkbox→boolean, textbox→integer/decimal).

3) STRUCTURAL VARIANT DETECTION
- Age eligibility:
  * One age + contribution-type checkboxes ⇒ vendor_implementation = "single_age_with_applies_to".
  * Separate per-type rows/items ⇒ "age_per_contribution_type".
- Entry dates:
  * Single toggle same/different ⇒ "single_entry_toggle".
  * Presets + 'Other' per type ⇒ "preset_or_other_per_type".
- Vesting:
  * Preset catalog ⇒ "preset_schedule_catalog".
  * Part-based per source ⇒ "part_based_vesting".
- Loans/hardship as described in the variant catalog.

4) CONSTRAINTS
- Parse comparators:
  * “Age 21” ⇒ {"max":21}
  * “not to exceed 1,000 Hours of Service” ⇒ {"max":1000}
  * Currency blanks: treat as numeric dollars with no commas if filled.
- If a numeric value is implied by a named line (e.g., “Age 21” line w/ checkbox), set the value via constraints rather than requiring a free number.

5) DIMENSIONS
- If the line includes contribution-type checkboxes or per-type rows, set `applies_to_dimensions` to ["contribution_type"] and:
  * For “single_age_with_applies_to”: DO NOT set dimension_values; value will be replicated across checked types upstream.
  * For “age_per_contribution_type”: set dimension_values for the specific type handled by this line if inferable (e.g., {"contribution_type":"matching"}).

6) DEPENDENCIES
- If this election controls whether child entries are required (e.g., “Entry date same for all” vs “different dates apply”), set `dependency_bundle` with the parent and semantic child tokens (e.g., "entry_date_detail_by_type").

7) CONFIDENCE
- High (≥0.9) when: domain + value_type + units + structural variant are all deterministically matched.
- Medium (0.6–0.89) when: domain and value_type match but synonyms ambiguous.
- Low (<0.6) when: multiple plausible canonical fields remain or provision is instructional only.

EDGE DISAMBIGUATION
- eligibility.age vs eligibility.entry:
  * “Age 21”, “Attainment of Age” → eligibility.age
  * “Entry Date (Monthly/Quarterly/…)” → eligibility.entry.frequency
- vesting.schedule vs vesting.service_crediting:
  * Schedules list year/percent grids or named presets ⇒ vesting.schedule.*
  * “Service Required for Vesting” / “Hours defining Year of Service” ⇒ vesting.service.*
- contributions.match_formula vs contributions.match_limit:
  * Formula answers “how to compute the match.”
  * Limit caps the outcome (dollar or % of comp) ⇒ contributions.match.max.*

STRICTNESS
- Output JSON only. No prose. Use keys exactly as specified.
```

**Why this aligns with your extractor:** It references the **v5.2 keys** (`section_path`, `form_elements`, `options`, etc.), and the **Atomic Field Rule** mirrors your extraction guidance.

---

# ARTIFACT 5 — Starter Scoring Config

> Save as `ceo.match_scoring.json`

```json
{
  "version": "0.1",
  "weights": {
    "TypeMatch": 0.45,
    "DomainSim": 0.15,
    "LabelSim": 0.15,
    "ConstraintCompat": 0.15,
    "VariantCompat": 0.05,
    "SynonymBoost": 0.05
  },
  "components": {
    "TypeMatch": {
      "rule": "1.0 if value_type matches exactly; -0.25 penalty if units mismatch; 0.5 if compatible numeric (integer vs decimal/percentage requires unit normalization). Floor at 0."
    },
    "DomainSim": {
      "rule": "1.0 if domain identical; 0.5 if adjacent (eligibility↔vesting service crediting); else 0."
    },
    "LabelSim": {
      "rule": "Normalized token overlap of canonical name + synonyms vs vendor label; stop-words removed; cap at 1.0.",
      "note": "Use a cheap char-trigram Jaccard; avoid LLM here."
    },
    "ConstraintCompat": {
      "rule": "1.0 if source constraints are within target bounds; 0.5 if overlapping ranges; 0 if disjoint."
    },
    "VariantCompat": {
      "rule": "1.0 if structural variants map with a defined transformation; 0.5 if unknown but not contradictory; 0 if contradictory (e.g., array vs scalar with no rule)."
    },
    "SynonymBoost": {
      "rule": "+0.1 for strong curated synonym hit (e.g., 'Age 21' ↔ eligibility.age), capped at weight."
    }
  },
  "tie_breaker": {
    "llm_enabled": true,
    "max_effect": 0.05,
    "prompt": "Given two near-equal canonical matches, select the one whose constraints and dimensions better preserve participant-level behavior; explain in 1 sentence.",
    "usage": "Only when absolute score delta < 0.03."
  },
  "thresholds": {
    "auto_accept": 0.85,
    "review": 0.7,
    "reject": 0.5
  },
  "normalization": {
    "percentage_as_decimal": "Normalize % to decimal when comparing numeric types.",
    "age_line_as_max": "Treat named 'Age 21' lines as constraint max=21 for structural matching."
  }
}
```

---

## Answers to your four design questions

1. **LLM vs rule-based?**
   **Hybrid**. Hard-type and domain rules drive the mapping; LLM is a bounded tie‑breaker (≤5% of score) and a parser when text must be interpreted (e.g., “not to exceed”). This keeps the compiler deterministic and quick.

2. **Granularity of taxonomy?**
   Keep the **field path coarse** (`eligibility.age`), and carry granularity via **dimensions** (`contribution_type`, `participant_class`). This avoids path explosion but still models Ascensus’ per-type knobs and Relius’ applies-to checkboxes.

3. **Rare/vendor-specific fields?**
   Defer. Add a namespaced `vendor_extension.<vendor>.<slug>` when you encounter material impact on behavior. Index it but **exclude** from alignment scoring until it appears across ≥2 vendors.

4. **Coverage vs compilation complexity?**
   Optimize for **compilation reliability first**. The taxonomy above covers the high-frequency elections already present in your samples (Eligibility, Entry, Service, Vesting, Matching, Loans, Hardship/RMD). Expand only when compile accuracy stays ≥90%.

---

## Quick sanity passes you can run (property probes)

- **Age 21, applies_to=[elective, matching]**
  Relius → replicate age=21 to `pretax/roth` as applicable for elective and to `matching`; Ascensus → read each per-type field. Expected functional equivalence holds (your Week 1 success check). Anchors: Relius Age 21; Ascensus Age Requirement.

- **Entry date split**
  Relius toggle “same for all vs different” ⇒ dependency bundle triggers child entries; Ascensus preset/other per-type ⇒ map `frequency` and `other_text`. Anchors: both vendor samples.

---

If you want, I can hold these artifacts steady while you wire the compiler, and we can add a minimal set of unit tests around the Age/Entry/Vesting/Loans cases using the sample JSON you dropped.
