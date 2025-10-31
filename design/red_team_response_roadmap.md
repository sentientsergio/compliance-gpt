# Red Team Response Roadmap
**Date:** October 30, 2025
**Status:** Sprint 1 (0-48 hours) - IN PROGRESS
**Context:** Response to GPT-5 Pro Red Team Report identifying production blockers

---

## Executive Summary

The GPT-5 Pro Red Team review identified **three critical blockers** preventing production use:

1. **Missing section provenance** (54.9% Ascensus, 21.6% Relius matches lack section numbers)
2. **No durable provision IDs** (empty/unusable ID columns in CSVs)
3. **Granularity too coarse** (1k+ char merged blocks prevent atomic clause auditing)

**Verdict:** "Useful first pass, not audit-ready"
**Grade:** C- (shows POC capability, missing verification data)

**Path to Production:** Ship mechanical fixes → tighten acceptance gates → run review queues → achieve audit-credible status

---

## Implementation Roadmap

### Sprint 1: Unblock Verification (0-48 hours) ⚠️ IN PROGRESS

**Goal:** Enable reviewers to verify matches without manual PDF searches

**Tasks:**

1. ✅ **COMPLETE** - Create v4.2 extraction prompts
   - File: `prompts/provision_extraction_v4.2.txt`
   - File: `prompts/aa_extraction_v5.2.txt`
   - **New fields added:**
     - `section_path` - Normalized hierarchical path (e.g., "ARTICLE_I.1.01", "Q_1.04")
     - `evidence_snippet` - First 120-200 chars for quick verification
     - `line_span` - Visual line numbers on page ({"start": N, "end": M})
     - `section_anchor_method` - How section was identified (direct/fallback/none)
   - **Fallback anchoring:** When section missing, use "PAGE_{n}.UNK_{ordinal}"

2. ✅ **COMPLETE** - Implement deterministic provision ID generator
   - File: `src/utils/provision_ids.py`
   - **ID Recipe:** `vendor:doctype:section_path:sha1(provision_text[:512])`
   - **Examples:**
     - `relius:bpd:ARTICLE_I.1.01:a3f2b9c1`
     - `ascensus:aa:Q_1.04:d7e8f2a3`
   - **Features:**
     - Reproducible across re-extractions
     - Globally unique
     - Human-readable (contains semantic anchors)
     - Supports traceability (can parse back to components)
   - **Debug mode:** `generate_provision_id_debug()` exposes ingredients for reviewer trust

3. ⬜ **TODO** - Add reason_code + evidence_snippet to semantic mapper
   - File: `prompts/semantic_mapping_v2.txt` (create)
   - **New reason_code enum:**
     - `exact_text` - Identical wording
     - `paraphrase_equivalent` - Same meaning, different wording
     - `related_but_not_equivalent` - Related topic, different provisions
     - `structural_mismatch` - Different provision structure
     - `definition_vs_rule` - Definition matched to operational rule
     - `category_conflict` - Mismatched categories
   - **New evidence fields:**
     - `evidence_source` - 120-200 char snippet from source
     - `evidence_target` - 120-200 char snippet from target
   - **Update reasoning format:** "§X says..., §Y says..., therefore..."

4. ⬜ **TODO** - Remove `[Linked to N AA election(s)]` from CSV output
   - Files to update:
     - `scripts/generate_lauren_mapping_doc.py`
   - **Action:** Strip this text from provision_text before CSV export
   - **Rationale:** Confusing, unexplained, always shows "5" (hardcoded artifact)

5. ⬜ **TODO** - Update CSV schemas with new provenance columns
   - Files to update:
     - `scripts/generate_lauren_mapping_doc.py`
   - **New columns to add:**
     - `source_section_path`, `target_section_path`
     - `source_line_span`, `target_line_span`
     - `source_evidence_snippet`, `target_evidence_snippet`
     - `source_provision_id`, `target_provision_id`
     - `mapping_id`
     - `reason_code`
     - `evidence_source`, `evidence_target`
     - `section_anchor_method_source`, `section_anchor_method_target`

**Exit Criteria:**
- [ ] Re-extraction with v4.2 prompts complete (both BPD and AA)
- [ ] All provisions have deterministic IDs
- [ ] All CSV rows have section_path (or fallback anchor)
- [ ] Evidence snippets present for quick verification
- [ ] Reason codes populate in crosswalk output

---

### Sprint 2: Raise Trust (3-7 days) ⬜ NOT STARTED

**Goal:** Stop false positives, enable graduated acceptance gates

**Tasks:**

1. **Implement acceptance gates with decision boundary logging**
   - File: `src/mapping/acceptance_gates.py` (create)
   - **PASS criteria (all must be true):**
     - `confidence >= 0.93`
     - Both sections present
     - `reason_code ∈ {exact_text, paraphrase_equivalent}`
     - `category_align = true`
   - Everything else → **REVIEW**
   - **New field:** `decision_boundary_explanation` (which gate failed)

2. **Implement priority scoring for review queues**
   - File: `src/mapping/priority_scoring.py` (create)
   - **Formula:**
     ```python
     priority = (
         regulatory_weight +
         section_missing * 2 +
         category_mismatch * 1 +
         (0.9 - confidence) * 3 +
         "different"_in_reasoning * 1
     )
     ```
   - **Regulatory weights:**
     - testing: 5 (ADP/ACP/coverage failures = IRS audit triggers)
     - distribution: 4 (RMDs, in-service, hardship)
     - eligibility: 3
     - match: 3 (safe harbor formulas)
     - contribution: 3 (nonelective, profit sharing)
     - vesting: 2
     - compensation: 2 (415 limits, W-2 definitions)
     - top_heavy: 2
     - loan: 1
     - hardship: 1
     - unknown: 1
     - administrative: 1

3. **Generate Excel workbook with review queue tabs**
   - File: `scripts/generate_review_workbook.py` (create)
   - **Tabs:**
     - `PASS` - Auto-accepted matches (confidence ≥0.93, all gates passed)
     - `Review-High` - High priority (priority score ≥10)
     - `Review-Med` - Medium priority (5 ≤ priority < 10)
     - `Review-Low` - Low priority (priority < 5)
     - `Unmapped` - Relius provisions without matches
     - `New-Ascensus` - Ascensus provisions not in Relius
     - `New-Ascensus-Grouped` - **NEW:** Grouped by parent section (segmentation diagnostic)
     - `Diagnostics` - Summary statistics
   - **Features:**
     - Slicers on reason_code, category, mapping_cardinality, flags
     - Clickable section references (if available)
     - Sortable by priority score
   - **New-Ascensus-Grouped diagnostic:**
     - Groups unmapped Ascensus provisions by parent_section
     - Shows count per parent (e.g., "ARTICLE III: 12 provisions")
     - Flags parents with >5 children as likely segmentation noise
     - Purpose: Distinguish extraction issues from genuinely new provisions

4. **Create "Ground Truth" validation set (50 matches)** ⭐ NEW
   - **Goal:** Establish objective quality baseline and regression test suite
   - **Method:**
     - You + Lauren manually curate 50 correct matches across all categories
     - Mix of categories: eligibility (10), match (10), vesting (5), contribution (10), distribution (5), compensation (5), testing (2), other (3)
     - Document WHY each is correct (semantic equivalence, regulatory requirement, etc.)
     - Store as `test_data/ground_truth/curated_matches_v1.json`
   - **Output:**
     - Ground truth dataset with rationale
     - Test harness that runs crosswalk against ground truth
     - Precision/recall metrics published with each release
   - **Value:**
     - Objective quality measurement (not vibes)
     - Confidence to make changes (you'll know if you break something)
     - Credibility with stakeholders ("here's our test coverage")

5. **Expert validation study (100 pairs)**
   - **Goal:** Calibrate confidence thresholds to human judgment
   - **Method:**
     - Select 100 random matches across confidence bands
     - Two compliance experts rate independently
     - Measure inter-rater agreement
     - Compute ROC curve for threshold tuning
   - **Output:** Updated acceptance gate thresholds based on data

**Exit Criteria:**
- [ ] Acceptance gates implemented and tested
- [ ] Review queues prioritized by regulatory risk
- [ ] Excel workbook generated with filterable tabs
- [ ] Ground truth validation set created (50 matches with rationale)
- [ ] Test harness runs and reports precision/recall
- [ ] 100-pair expert validation complete
- [ ] Confidence thresholds calibrated to ≥85% expert agreement

---

### Sprint 3: Structural Fix (1-2 weeks) ⬜ NOT STARTED

**Goal:** Enable atomic clause auditing while preserving merged context

**Tasks:**

1. **Design atomic clause architecture**
   - File: `design/architecture/atomic_clause_model.md` (create)
   - **Three-layer model:**
     - **Atomic layer** (provisions_atomic.csv) - Individual clauses/sub-clauses
     - **Container layer** (containers.csv) - Merged "Plan Provisions" (BPD + AA)
     - **Membership layer** (container_membership.csv) - Links atomic ↔ container
   - **Crosswalk operates on atomic layer** (allows 1:many mappings)
   - **Reports show containers for context** (atomic for audit)

2. **Implement atomic clause extraction**
   - Files to update:
     - `prompts/provision_extraction_v4.3.txt` (add atomic splitting rules)
     - `prompts/aa_extraction_v5.3.txt` (add atomic splitting rules)
   - **Splitting rules:**
     - Labeled subparts (a), (b), (i), (ii) → separate provisions
     - Sentences with distinct "shall/must/may" → separate if standalone
     - Nested options in AA → separate provisions
   - **New fields:**
     - `fragment_position` - Position within container (1, 2, 3...)
     - `parent_section` - Container section reference

3. **Update crosswalk to handle one-to-many mappings**
   - Files to update:
     - `src/mapping/semantic_mapper.py`
   - **New logic:**
     - Allow multiple target provisions per source
     - Require explicit `mapping_cardinality` ∈ {1:1, 1:n, n:1}
     - Require `reason_code` when not 1:1
   - **Example:**
     - Relius "Vesting Schedule" (single provision) →
     - Ascensus "Cliff Vesting" + "Graded Vesting" (two provisions)

4. **Feature flag for atomic mode**
   - **CLI flag:** `--atomic` (default: False)
   - **Default behavior:** Continue using merged Plan Provisions
   - **Atomic mode:** Generate atomic crosswalk + container membership
   - **Goal:** Test atomic layer without breaking existing workflows

**Exit Criteria:**
- [ ] Atomic clause model designed and documented
- [ ] Extraction prompts emit atomic provisions + containers
- [ ] Crosswalk supports one-to-many mappings
- [ ] `--atomic` flag implemented and tested
- [ ] Side-by-side comparison (merged vs atomic) validates quality

---

## Decision Points (Resolved)

### 1. Acceptance Gates
**Decision:** ✅ Adopt exactly as written by Red Team
```
PASS if ALL of:
  - confidence >= 0.93
  - both sections present
  - reason_code ∈ {exact_text, paraphrase_equivalent}
  - category_align = true
Everything else → REVIEW
```
**Rationale:** Aligns with "human-in-loop, 70-90% automation" design philosophy

### 2. Priority Weights
**Decision:** ✅ Keep suggested with one tweak (testing = 5, was 4)
**Rationale:** ADP/ACP/coverage test failures are IRS audit triggers (highest regulatory risk)

### 3. Atomic Model
**Decision:** ✅ Stage now with feature flag, promote after provenance stabilizes
**Rationale:** Red Team is correct - audit requires atomic clauses. But rushing risks breaking what works. Parallel tracks = safer.

### 4. Elections Linkage
**Decision:** ✅ Kill for now, revisit in Phase 3
**Rationale:** Confusing, unexplained, always "5" (hardcoded artifact). Underlying data structure stays, just don't surface it yet.

---

## Red Team Findings Summary

### What Works
- ✅ Side-by-side texts with variance notes on every match
- ✅ Categories broadly coherent (Contribution/Match/Eligibility present)
- ✅ Volume processing (1,286 provisions across four documents)
- ✅ Semantic understanding capability (when it works well)

### Critical Blockers
- ❌ **Missing sections:** 247/450 (54.9%) Ascensus, 97/450 (21.6%) Relius
- ❌ **No durable IDs:** Provision ID columns empty/unusable
- ❌ **Granularity too coarse:** 1k+ char blocks, unrealistic 1:1 cardinality
- ❌ **Cardinality looks unrealistic:** No one-to-many seen (segmentation artifact)

### Moderate Issues
- ⚠️ `[Linked to 5 AA election(s)]` mystery (72.5% of provisions, always "5")
- ⚠️ Category mismatches (8.4% of matches)
- ⚠️ Self-contradicting reasoning (71% say "different" but match anyway)
- ⚠️ **"New Ascensus" inflation (37.6%)** - This is a data quality signal, not a tool failure
  - Interpretation: Either Ascensus is genuinely more detailed, OR extraction segmented differently
  - **Diagnostic needed:** Group "new" provisions by parent section
  - If 10 "new" provisions under same parent → segmentation noise (extraction prompt issue)
  - If distributed across parents → genuinely new provisions (legitimate finding)

### Statistical Evidence
- **Coverage:** Relius 79.6% matched, Ascensus 62.4% matched / 37.6% "new"
- **Confidence bands:** ≤0.60: 80 | 0.61-0.75: 236 | 0.76-0.85: 49 | 0.86-0.93: 68 | >0.93: 17
- **Match quality:** 448 "close", 2 "exact" (everything is "close" - label is meaningless)
- **Category counts:** Contribution 169 | Match 86 | Eligibility 83 | Distribution 28 | Compensation 21

### Category-Specific Insights

**Eligibility (83 matched | 16 unmapped | 7 new)**
- Most matches 0.61-0.75 confidence (medium)
- Real risk hidden in: method (elapsed time vs hours), entry frequency, rehire rules
- **Recommendation:** Needs atomic extraction of method, thresholds, entry cadence, rehire treatment

**Match (86 matched | 1 unmapped | 49 new)**
- Many high-confidence rows still have variance notes
- No step diffs found (formulas not standardized, not that they match)
- **Recommendation:** Normalize step formulas, caps, comp base, true-up timing, catch-up as structured fields

**Vesting (10 matched | 1 unmapped | 5 new)**
- Small sample, mostly mid-confidence
- **Recommendation:** Normalize schedule type (cliff/graded), year-of-service method, event-based triggers

---

## Success Criteria

### Minimum Acceptable Performance (Production Ready)
- ✅ Section number extraction: >90% complete
- ✅ Verification rate: >80% of matches have references
- ✅ Expert validation: >85% agreement on high-confidence matches
- ✅ Time savings: >50% reduction in manual review time
- ✅ False positive rate: <10% for matches >0.80 confidence

### Current Performance (Baseline)
- ❌ Section extraction: 45% complete (BLOCKER)
- ❌ Verification rate: 45% have complete references (BLOCKER)
- ❓ Expert validation: Not yet tested
- ❓ Time savings: Likely negative (tool creates more work than it saves)
- ❓ False positive rate: Unknown (suspect high based on 0.60 matches accepted)

---

## Implementation Status

### ✅ Complete
1. v4.2 extraction prompts (provision_extraction_v4.2.txt, aa_extraction_v5.2.txt)
2. Deterministic provision ID generator (src/utils/provision_ids.py)

### 🔄 In Progress
3. Semantic mapping v2 prompt (reason_code + evidence_snippet)

### ⬜ Not Started
4. Remove elections linkage from CSV output
5. Update CSV schemas with provenance columns
6. Re-run extraction with v4.2 prompts
7. Sprint 2 tasks (acceptance gates, priority scoring, review workbook)
8. Sprint 3 tasks (atomic clause model)

---

## Next Actions (Immediate)

1. **Complete Sprint 1 remaining tasks** (3-5 hours)
   - Finish semantic_mapping_v2.txt prompt
   - Update generate_lauren_mapping_doc.py to use new schemas
   - Remove elections linkage artifact

2. **Re-run extraction pipeline** (4-6 hours)
   - Run v4.2 prompts on all 4 documents (Relius BPD/AA, Ascensus BPD/AA)
   - Verify section_path, evidence_snippet, line_span populated
   - Add provision IDs using provision_ids.py utility

3. **Re-generate crosswalk with v2 semantic mapper** (1-2 hours)
   - Run full crosswalk with reason_code output
   - Generate updated lauren_view CSVs with new schema

4. **Validate Sprint 1 exit criteria** (1 hour)
   - Check section_path coverage (target: >90%)
   - Verify provision IDs populated (target: 100%)
   - Spot-check evidence snippets for accuracy

5. **Red Team Sprint 2** (2-3 hours)
   - Manual review of 20-30 random matches
   - Validate reason_code accuracy
   - Test evidence snippet usability

---

## Open Questions

1. **Pages without section paths** - Do we treat as unreviewable, or permit conditional acceptance if evidence snippets + confidence high?
2. **Compensation base canon** - What's our standard for comparisons (plan comp vs §415 vs §401(a)(17) limits)?
3. **True-up required field?** - Should this be a structured field (Y/N + timing)?
4. **Eligibility method priority** - Do we prioritize elapsed-time vs hours method alignment over minor age/waiting-period deltas?

---

## Files Created/Modified

### Created (Sprint 1)
- `design/red_team_response_roadmap.md` (this file)
- `prompts/provision_extraction_v4.2.txt`
- `prompts/aa_extraction_v5.2.txt`
- `src/utils/provision_ids.py`

### To Modify (Sprint 1)
- `prompts/semantic_mapping_v2.txt` (create from v1)
- `scripts/generate_lauren_mapping_doc.py` (CSV schema updates)

### To Create (Sprint 2)
- `src/mapping/acceptance_gates.py`
- `src/mapping/priority_scoring.py`
- `scripts/generate_review_workbook.py`
- `test_data/ground_truth/curated_matches_v1.json` ⭐ NEW
- `scripts/run_ground_truth_validation.py` ⭐ NEW

### To Create (Sprint 3)
- `design/architecture/atomic_clause_model.md`
- `prompts/provision_extraction_v4.3.txt`
- `prompts/aa_extraction_v5.3.txt`

---

## References

- **Red Team Report:** `test_data/crosswalks/lauren_view/Red Team Reviews/GPT 5 Pro Review/gpt5_red_team_report.md`
- **Red Team Sprint Framework:** `CLAUDE.md` (section: "When conducting Red Team Sprints")
- **Current Extraction:** `test_data/extracted_vision_v4.1/` (BPD), `test_data/extracted_vision_v5.1/` (AA)
- **Current Crosswalk:** `test_data/crosswalks/full_plan_provision_crosswalk.json`
- **Current Lauren View:** `test_data/crosswalks/lauren_view/*.csv`

---

**Last Updated:** October 30, 2025
**Next Review:** After Sprint 1 completion (re-extraction with v4.2 prompts)
