Here’s the synthesis, tight and usable.

# Compliance-GPT Crosswalk (Relius C3 → Ascensus PS)

**Red-Team Report — Oct 30, 2025**

## TL;DR

- **Useful first pass, not audit-ready.** Main blockers: missing **section paths**, **no durable IDs**, and **coarse “provisions.”**
- Confidence skews mid (0.61–0.75). Only **2/450** “exact” matches. Treat as **review queues**, not source of truth.
- “New Ascensus” looks **inflated** by segmentation; many rows lack sections.
- Fix the mechanics (sections, IDs, atomic splits, evidence snippets, reason codes) and your review cost drops fast.

## Actions (now)

1. **Backfill section paths** on both sides for all rows (Matched + New + Unmapped).
2. Emit **deterministic provision IDs** (`relius_provision_id`, `ascensus_provision_id`).
3. **Split** long blocks into **atomic** clauses/elections; add `fragment_position` + `parent_section`.
4. Add **evidence snippets** (≤200 chars per side) + **reason codes** (e.g., `topic_mismatch`, `election_conflict`, `needs_split`).
5. Gate “auto-accept” to **(confidence ≥ 0.93 AND match_quality ∈ {exact, near}) AND section paths present**; everything else → review queue.

---

## What’s solid

- Side-by-side texts with **variance notes** on every match.
- Categories are broadly coherent (Contribution/Match/Eligibility present on both).

## What blocks verification

- **Provenance holes:** Missing sections in **247/450 Ascensus** matches; **97/450 Relius** matches; **131/271 New Ascensus**. Pages aren’t enough for an audit trail.
- **No durable IDs:** `*_provision_id` columns are empty → weak traceability.
- **Granularity:** Provision strings are long (often >1k chars) → likely merged subclauses.
- **Cardinality looks unrealistically 1:1** (no one-to-many seen), which is likely a segmentation artifact, not reality.
- **Unmapped “closest”** rationales are generic; not actionable without a pinpoint target and reason code.

---

## Evidence snapshot (what we saw)

- Files: `matched` **450**, `unmapped_relius` **115**, `new_ascensus` **271**.
- **Coverage (proxy, row-based):** Relius ≈ **79.6%** matched; Ascensus ≈ **62.4%** matched / **37.6%** “new”.
- **Confidence bands (matches):** ≤0.60: **80** | 0.61–0.75: **236** | 0.76–0.85: **49** | 0.86–0.93: **68** | >0.93: **17**.
- **Match quality:** **448 “close”**, **2 “exact.”**
- **Category counts (matched):** Contribution 169 | Match 86 | Eligibility 83 | Distribution 28 | Compensation 21 | Vesting 10 | Top-Heavy 5 | Testing 2 | Unknown 46.

---

## Category notes (targeted)

**Eligibility** (83 matched | 16 unmapped | 7 new)

- Most matches sit in **0.61–0.75**; 15 low-confidence, 8 high-confidence.
- Spot checks show small age/term token differences, but the real risk is hidden in **method** and **entry frequency** (elapsed time vs hours; immediate/monthly/quarterly; first-of-month rules; rehires/bridging).
- **Takeaway:** Needs atomic splits + explicit extraction of method, thresholds, entry cadence, and rehire rules.

**Match** (86 matched | 1 unmapped | 49 new)

- Many high-confidence rows still have variance notes.
- A naive formula parser found **no step diffs**, which likely means the phrasing isn’t standardized (not that formulas match).
- **Takeaway:** Normalize **match step formulas**, caps, comp base, true-up presence/timing, and catch-up treatment as structured fields.

**Vesting** (10 matched | 1 unmapped | 5 new)

- Small sample; mostly mid-confidence.
- **Takeaway:** Normalize **schedule type** (cliff/graded) + ladder, year-of-service method, and event-based vesting (death/disability/top-heavy/safe harbor).

---

## Temporary acceptance gates

- **Accept (PASS)** only if: sections present **and** evidence snippets align **and** confidence ≥ **0.86**.
- Everything else: **REVIEW** with a reason code.
- “New Ascensus” rows: **TRIAGE** until section paths + parent headings are present; then de-dupe within parent sections.

---

## Reviewer workflow (lean)

1. Work these queues in order:

   - **Low-confidence matches (≤0.60)** → [CSV](low_confidence_matches.csv)
   - **High-confidence + variance** → [CSV](flagged_high_confidence_variance.csv)
   - **New Ascensus missing sections (top-50)** → [CSV](reviewer_queue_new_ascensus_missing_section_top50.csv)

2. Focus high-impact categories first: **Eligibility, Match, Vesting**.
3. Use decisions we logged for Eligibility “first 10 each queue” as a pattern: [CSV](eligibility_first10_review.csv).
4. Feed pass/fail + reason codes back to the tool to calibrate thresholds and fix the top failure modes.

---

## Tooling changes (clear asks to the dev team)

- **Provenance:** Fill `section_path` for every row; include filename + doc type (BPD/AA) + edition.
- **IDs:** Emit deterministic `*_provision_id`.
- **Granularity:** Atomic clause/election rows; include `fragment_position` + `parent_section`.
- **Explainability:** Add `evidence_source` / `evidence_target` snippets; standardize `reasoning` (“§X says…, §Y says…, therefore…”).
- **Reason codes:** `topic_mismatch | level_mismatch | election_conflict | definition_only | needs_split | needs_provenance`.
- **Match scale:** Use `exact | near | partial | related | no_match` with definitions; gate auto-accept at **≥0.93** + sections present.

---

## Open questions to settle

- Do we treat **pages without section paths** as unreviewable, or permit conditional acceptance if evidence snippets and confidence are high?
- What’s our **compensation base** canon for comparisons (plan comp vs §415 vs §401(a)(17) limits)?
- Should **true-up** be a required structured field (Y/N + timing)?
- Eligibility: do we prioritize **elapsed-time** vs **hours** method alignment over minor age/waiting-period deltas?

---

## Working artifacts (for reference)

- Low-confidence matches: [CSV](low_confidence_matches.csv)
- High-confidence with variance: [CSV](flagged_high_confidence_variance.csv)
- Missing-provenance matches: [CSV](missing_provenance_in_matches.csv)
- New Ascensus — missing sections (top-50): [CSV](reviewer_queue_new_ascensus_missing_section_top50.csv)
- Diff samples by category: Eligibility [CSV](eligibility_diff_samples.csv), Match [CSV](match_diff_samples.csv), Vesting [CSV](vesting_diff_samples.csv)
- Category tallies: Unmapped Relius [CSV](unmapped_relius_by_category.csv), New Ascensus [CSV](new_ascensus_by_category.csv)

---

Short version: ship the mechanical fixes, keep the acceptance gates tight, and run the queues in that order. You’ll get to “audit-credible” faster than trying to argue the mid-confidence blob into being right.
