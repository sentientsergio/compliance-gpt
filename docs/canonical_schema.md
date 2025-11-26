# Canonical Schema (Draft)

Purpose: vendor-neutral representation of plan provisions for comparison. This draft focuses on the initial 10 POC provisions and is structured to handle contribution-type granularity (deferral, match, profit_sharing) where applicable.

## Conventions
- IDs: dot-delimited paths, e.g., `eligibility.age.deferrals`.
- Contribution-type splits: fields that vary by source use a map with keys `deferrals`, `match`, `profit_sharing` (can extend to `qaca`, `safe_harbor`, etc.).
- Provenance: each populated node should carry source metadata (doc_id, section/heading, page_range, bbox refs).
- Values: raw text plus normalized/typed value when possible (e.g., integers for ages, enums for schedules).

## Top-level shape (conceptual)
```json
{
  "plan": {
    "eligibility": {
      "age": {"deferrals": {}, "match": {}, "profit_sharing": {}},
      "service": {"deferrals": {}, "match": {}, "profit_sharing": {}},
      "entry_dates": {}
    },
    "retirement": {
      "normal_age": {}
    },
    "compensation": {
      "base_definition": {},
      "exclusions": {}
    },
    "vesting": {
      "schedule": {
        "match": {},
        "profit_sharing": {},
        "qaca": {}
      }
    },
    "loans": {
      "enabled": {},
      "parameters": {}
    },
    "distributions": {
      "hardship": {},
      "in_service": {}
    }
  }
}
```

## Nodes (POC scope)

### 1) `eligibility.age`
- Shape:
```json
{
  "deferrals": {"value": "21", "unit": "years", "provenance": {...}},
  "match": {"value": "21", "unit": "years", "provenance": {...}},
  "profit_sharing": {"value": "21", "unit": "years", "provenance": {...}}
}
```
- Notes: if a uniform age applies, all three may be identical; allow “N/A” where a source doesn’t apply.

### 2) `eligibility.service`
- Shape: same contribution-type split; support `computation_period`, `required_hours`, `years_required`.

### 3) `eligibility.entry_dates`
- Shape:
```json
{
  "pattern": "first_of_month | quarterly | semi_annual | annual | per_payroll | custom",
  "lead_time_days": null,
  "provenance": {...}
}
```
- Notes: may differ by contribution type; extend with per-type keys if needed.

### 4) `retirement.normal_age`
- Shape: `{ "age": 65, "service_years": 5, "provenance": {...} }`
- Notes: allow variants (e.g., age-only, age+service).

### 5) `compensation.base_definition`
- Shape: `{ "definition": "W2 | 3401 | 415_safe_harbor | other", "provenance": {...} }`
- Notes: consider per-contribution-type variants if present.

### 6) `compensation.exclusions`
- Shape:
```json
{
  "items": [
    {"name": "bonus", "applies_to": ["deferrals","match"], "provenance": {...}},
    {"name": "overtime", "applies_to": ["deferrals","match","profit_sharing"], "provenance": {...}}
  ]
}
```
- Notes: grid/matrix sources map naturally here.

### 7) `vesting.schedule`
- Shape:
```json
{
  "match": {"type": "graded|cliff|immediate|custom", "schedule": {"0":0,"1":0,"2":20,"...":100}, "provenance": {...}},
  "profit_sharing": {...},
  "qaca": {...}
}
```

### 8) `loans.enabled` and `loans.parameters`
- Shape: `{"enabled": true/false, "provenance": {...}, "parameters": {"max_loans": null, "policy_ref": null}}`
- Notes: start simple; extend as needed.

### 9) `distributions.hardship`
- Shape:
```json
{
  "allowed_sources": ["deferrals","match","profit_sharing"],
  "definition": "safe_harbor | other",
  "beneficiary_hardship_allowed": true/false,
  "provenance": {...}
}
```

### 10) `distributions.in_service`
- Shape: `{ "age_threshold": 59.5, "vesting_threshold_pct": null, "sources": ["match","profit_sharing"], "provenance": {...} }`
- Notes: often varies by source; extend to per-type if needed.

## Provenance structure (for any node)
```json
{
  "doc_id": "relius_bpd",
  "section": "Article III 3.1",
  "breadcrumbs": ["Article III", "Eligibility", "3.1"],
  "page_range": [20, 21],
  "bbox": [x0, y0, x1, y1]  // optional, if narrowed to a specific cell/block
}
```

## Extension points
- Additional contribution sources (e.g., QACA safe harbor vs non-safe-harbor).
- Parameters for loans, hardship conditions, auto-enrollment, escalation.
- Statutory cites: optional array of detected code references to aid comparison.
