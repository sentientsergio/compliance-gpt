# CLAUDE.md — Project Context for AI Assistants

This file provides context for AI assistants (Claude, GPT, etc.) working on the compliance-gpt project across multiple conversation sessions.

---

## Project Overview

**compliance-gpt** is an AI-assisted plan document compliance tool that automates the **manual reconciliation bottleneck** for qualified retirement plan conversions and IRS Cycle restatements.

**The Problem We Solve:**
Existing TPA platforms (FIS Relius, ASC, ftwilliam) automate **document generation** but NOT **document comparison**. Compliance teams today perform provision-by-provision reconciliation manually using Word redlines and Excel spreadsheets. This doesn't scale, requires extreme specialized knowledge, and is error-prone under deadline pressure.

**Our Differentiation:**
We are the **only AI tool focused on doc-to-doc comparison** — specifically semantic provision mapping across different vendor document formats and BPD revisions.

---

## Repository Structure

```
compliance-gpt/
├── README.md                    # Project overview, status, repo map
├── CLAUDE.md                    # This file - context for AI assistants
├── LICENSE                      # MIT License
│
├── process/                     # The compliance framework (the "spec")
│   ├── README.md               # Index of controls, templates, docs
│   ├── control_001_plan_qualification.md
│   ├── control_002_document_reconciliation.md
│   ├── control_003_exception_handling.md
│   ├── control_004_amendment_and_restated_plan_signoff.md
│   ├── templates/              # CSV/MD templates for artifacts
│   │   ├── plan_comparison_workbook.csv
│   │   ├── exception_log.csv
│   │   └── signoff_checklist.md
│   └── docs/
│       └── references.md       # Regulatory references (IRC, ERISA, Rev. Proc.)
│
├── requirements/                # Software requirements (informed by market research)
│   ├── README.md               # Requirements overview, MVP scope, traceability
│   └── functional_requirements.md  # 62 requirements organized by control
│
├── research/                    # Market research & competitive analysis
│   ├── README.md
│   └── market_research.pdf     # DeepResearch output on TPA tools, gaps, AI opportunities
│
├── design/                      # Technical design (Phase 1 complete)
│   ├── README.md               # Design philosophy, structure, roadmap
│   ├── architecture/
│   │   └── system_architecture.md  # Component diagram, data flow, tech stack
│   ├── data_models/
│   │   ├── provision_model.md      # Provision JSON schema
│   │   └── mapping_model.md        # Source→Target mapping structure
│   └── llm_strategy/
│       ├── README.md               # LLM strategy navigation
│       ├── model_selection.md      # Model selection rationale
│       ├── decision_matrix.md      # Quick reference scorecard
│       └── llm_research_report.md  # Comprehensive research findings
│
├── prompts/                     # LLM prompts (externalized, version controlled)
│   ├── README.md               # Prompt documentation and versioning guide
│   ├── provision_extraction_v1.txt  # Provision boundary detection prompt
│   └── semantic_mapping_v1.txt      # Provision comparison prompt (pending approval)
│
├── test_results/                # Red Team Sprint findings and quality validation
│   ├── red_team_YYYY-MM-DD.md  # Adversarial testing reports
│   ├── phase1_plan_provisions_poc_2025-10-30.md  # Phase 1 POC report
│   └── phase1.5_embedding_quality_2025-10-30.md  # Phase 1.5 quantitative validation
│
├── test_data/
│   └── golden_set/
│       └── phase1_merger_poc/  # Phase 1 POC test data
│           ├── relius_plan_provisions.json       # Relius Plan Provisions (BPD+AA)
│           ├── ascensus_plan_provisions.json     # Ascensus Plan Provisions (BPD+AA)
│           ├── comparison_inputs.json            # Embedding comparison inputs
│           └── embedding_comparison_results.json # Phase 1.5 quantitative results
│
└── src/                        # POC implementation (Python)
    ├── extraction/             # PDF and provision extraction
    ├── mapping/                # Semantic mapping and comparison
    ├── models/                 # Pydantic data models
    └── config.py               # Configuration management
```

---

## Project Status

**Phase:** Phase 2 Complete - Crosswalk Mapping Document Generated (Oct 30, 2025) ✅
**Previous:** Phase 1 + 1.5 - Plan Provisions Validated (Oct 30, 2025)
**Achievement:** Template-to-template crosswalk proves mapping document generation works WITHOUT filled values

**Major Milestones (Oct 30, 2025):**
✅ **ADR-001 APPROVED:** Merge-Then-Crosswalk strategy with formal decision record
✅ **Phase 1 POC COMPLETE:** Template-level Plan Provisions successfully created (100% linkage success)
✅ **Phase 1.5 COMPLETE:** Quantitative validation showing +6.2% embedding improvement (+11.1% for vesting)
✅ **Phase 2 POC COMPLETE:** Crosswalk mapping document generated (2 close matches, 1 no match, full variance analysis)

**What's Done:**
1. ✅ Process framework defined (`/process`) - Updated for BPD+AA architecture
2. ✅ Market research completed (`/research/market_research.pdf`)
3. ✅ Functional requirements drafted (`/requirements/functional_requirements.md`)
4. ✅ Competitive analysis (PlanPort is only AI competitor, does single-doc analysis only)
5. ✅ **Phase 1 Design complete** (`/design`) - Architecture, data models, LLM strategy
6. ✅ **Model selection:** GPT-5-nano (extraction), GPT-5-Mini (semantic mapping), text-embedding-3-small (embeddings)
7. ✅ **POC extraction complete** - 4,901 provisions extracted (Relius + Ascensus BPDs + AAs)
8. ✅ **Document structure validation** - BPD+AA architecture confirmed
9. ✅ **Prompt engineering workflow** - Externalized prompts with approval process
10. ✅ **ADR-001: Merger Strategy** - Merge-then-crosswalk approach with data models, merge rules, evaluation plan
11. ✅ **Phase 1: Plan Provisions POC** - Template-level BPD+AA linkage (100% success on test cases)
12. ✅ **Phase 1.5: Quantitative Validation** - Embedding quality improvement measured (+6.2% average)
13. ✅ **Phase 2: Crosswalk Mapping** - Template-to-template provision mapping document generated

**Test Corpus:**
- **Source:** Relius BPD Cycle 3 + Adoption Agreement (623 provisions, 182 elections)
- **Target:** Ascensus BPD 05 + Adoption Agreement (426 provisions, 550 elections)
- **Scenario:** Cross-vendor conversion (validates hardest use case - different template structures)

**Phase 1 + 1.5 + 2 Results:**
1. ✅ **Plan Provision Data Model** - Complete schema for BPD+AA linkage ([design/data_models/plan_provision_model.md](design/data_models/plan_provision_model.md))
2. ✅ **Template Linkage Algorithm** - Keyword-based domain matching (100% success rate on test provisions)
3. ✅ **Relius Plan Provisions** - 3 provisions created (eligibility, compensation, vesting)
4. ✅ **Ascensus Plan Provisions** - 2 provisions created (eligibility, vesting)
5. ✅ **Embedding Quality Test** - +6.2% average improvement, +11.1% for vesting provisions
6. ✅ **Two-Phase Crosswalk Architecture** - Embeddings find candidates → LLM verifies (cost-effective, accurate)
7. ✅ **Crosswalk Mapping Document** - 2 close matches, 1 no match, full variance analysis with confidence scores
8. ✅ **Unmapped Provision Detection** - Compensation missing in target correctly identified

**Key Findings:**
- **Plan Provisions are complete semantic units** - BPD+AA linkage creates semantically richer representations than BPD-only
- **Template-level crosswalk works without values** - Mapping document generation requires only template structure, not filled elections
- **Two-phase architecture is effective** - Embeddings find semantically related candidates (0.841 similarity), LLM correctly verifies equivalence
- **Variance detection works** - LLM identifies key differences (eligibility conditions vs entry dates, general vesting vs top-heavy vesting)
- **No false positives** - LLM correctly rejected unrelated provisions with low confidence (0.2 for compensation → eligibility)

**The Product: Mapping Document**
The crosswalk JSON output is the core deliverable for TPAs:
```
Relius Section 3.1 (eligibility) ↔ Ascensus ENTRY DATES (eligibility) - CLOSE match
Relius Section 1.18 (compensation) → NO MATCH (missing in target)
Relius Section b (vesting) ↔ Ascensus Section 8.B (vesting) - CLOSE match
```

This mapping document will drive automated value transfer when filled plans arrive (Phase 3).

**Next Steps:**
1. **Scale to full corpus:** Run crosswalk on all 805 Relius → 976 Ascensus provisions
2. **Phase 3 (Future):** Automated value transfer using mapping rules

---

## Three-Phase Architecture (The Complete System)

### Phase 1: Plan Provisions (Template Merger)
**Input:** BPD templates + AA templates (blank forms)
**Process:** Link BPD provisions with related AA elections (keyword matching + domain categories)
**Output:** Plan Provisions = BPD + AA merged at template level (no values yet)
**Result:** Complete semantic units for comparison (+6.2% embedding improvement)

### Phase 2: Crosswalk Mapping Document (Current Phase)
**Input:** Source Plan Provisions (Relius) + Target Plan Provisions (Ascensus)
**Process:** Two-phase semantic comparison
  1. Generate embeddings → find top-k candidates via cosine similarity
  2. LLM verification → determine exact/close/none match with variance analysis
**Output:** Mapping document (JSON) with provision-to-provision rules
**Result:** Template-to-template transformation rules for automation

**Example Mapping Rules:**
```json
{
  "source": "Relius Section 3.1 (eligibility conditions)",
  "target": "Ascensus ENTRY DATES (when eligible employees can join)",
  "match_type": "close",
  "confidence": 0.7,
  "variance": "Related but govern different sub-features"
}
```

### Phase 3: Automated Value Transfer (Future)
**Input:** Filled source plan (Relius with actual elections) + Mapping rules from Phase 2
**Data Sources:** TPA system exports (structured data) OR vision-extracted PDFs (when locked/scanned)
**Process:** Apply mapping rules programmatically
  - Relius Q 1.04 age=21 → Ascensus Q A.3 age=21 (direct transfer)
  - Relius vesting option (b) → Ascensus vesting option (c) (transformed per mapping)
**Output:** Filled target elections (Ascensus) - importable data format OR filled PDF
**Result:** Automated cross-vendor plan conversion

**Key Insight:** The mapping document (Phase 2) is vendor-agnostic transformation logic. Once generated, it can be reused for ANY Relius→Ascensus conversion, regardless of how source values are obtained (system API, PDF extraction, manual entry).

---

## Key Design Decisions

### 1. MVP Scope (MVP = Minimum Viable Product)

**In Scope:**
- Batch document ingestion (folder upload, PDF/Word, locked-PDF resilience via OCR/vision)
- **Semantic provision mapping** across vendor documents (core differentiator)
- **AI-powered variance detection** with classification (Administrative/Design/Regulatory)
- **Confidence scoring** (High 90-100%, Medium 70-89%, Low <70%)
- CSV output matching `/process/templates/` schema
- Human-in-loop approval workflow

**Out of Scope (Post-MVP):**
- Integration with TPA platforms (Relius API, ASC DGEM export)
- Real-time collaboration (multi-user editing)
- Automated approval workflows (e-signature integration)
- Amendment language drafting (detection only for MVP)

### 2. Human-in-the-Loop Philosophy

**Never fully autonomous, always reviewed.**
- Inspired by PlanPort's "70-90% of the way there" approach
- AI drafts, human approves
- Graduated confidence thresholds:
  - High (90-100%): Suggest bulk approval option
  - Medium (70-89%): Require individual review
  - Low (<70%): Abstain, mark "Requires Manual Review"

### 3. Locked PDF Handling

**Context:** Market research confirmed locked/encrypted PDFs are a "known issue" in the industry. Providers lock documents to prevent tampering, but this blocks programmatic text extraction.

**Solution:** Fallback strategy
1. Try standard PDF text extraction APIs first (PyPDF2, pdfplumber)
2. If locked/encrypted, fall back to vision-based extraction
3. Preserve document structure (sections, headers, tables) regardless of method

**Vision Model Research (Phase 2):** ✅ **COMPLETED**
- **GPT-5 vision (gpt-5-2025-08-07)** - **SELECTED** and working successfully
  - Successfully extracts provisions from BPDs (templates with "as elected in AA" language)
  - Successfully extracts election options from AAs (checkboxes, nested options, fill-in fields)
  - Handles complex nested structures (option d.1, d.2, d.3 under option d)
  - Requires `max_completion_tokens=16000` (not max_tokens, GPT-5-specific parameter)
  - User preference: "newer better more than 'safer'"
- **Deferred:** LandingAI DPT, Claude Sonnet 4.5 vision (GPT-5 working well)

### 4. Semantic Provision Mapping

**Context:** Plan documents vary in structure, section numbering, and phrasing:
- **Cross-vendor:** Different providers (Relius, ASC, ftwilliam, DATAIR) use different templates
- **Cross-edition:** Same vendor updates BPD language between Cycles
- **Cross-format:** BPDs vs AAs, standardized vs non-standardized

**Example from market research (cross-vendor case):**
- Relius: "forfeitures will be used to reduce employer contributions"
- ASC: "the Plan Administrator may apply forfeitures to future contribution obligations"
- **Must be recognized as semantically equivalent**

**Solution:** LLM-powered semantic understanding (not keyword matching or section number alignment)

**POC Validation:** Tested with Ascensus BPD 01 → BPD 05 (intra-vendor, cross-edition). Algorithm is vendor-agnostic.

### 5. Target User: Teams with "Just PDFs and Spreadsheets"

Market research validated this represents the **majority workflow**:
- Smaller TPAs without expensive Relius/ASC subscriptions
- Even teams WITH those tools reconcile manually (tools don't compare across providers)
- Current state: Word redlines, Excel comparison spreadsheets, email chains for approvals

---

## Critical Requirements (MVP Focus)

### REQ-021: Semantic Provision Mapping ⭐ CRITICAL - Core Differentiator
**Why Critical:** This is the #1 manual bottleneck confirmed by market research. No existing tools do this.

**What It Does:**
- Matches provisions semantically using LLM understanding (not just section numbers)
- Handles cross-vendor comparisons (e.g., Relius → ASC, ftwilliam → DATAIR)
- Handles cross-edition comparisons (e.g., BPD 01 → BPD 05 Cycle restatements)
- Recognizes equivalent provisions despite different wording/placement/formatting
- Assigns confidence score (0-100%) with reasoning
- Flags missing provisions (source → target omissions) as HIGH priority
- Flags new provisions (target additions) as MEDIUM priority

**POC Status:** ✅ Validated with Ascensus BPD 01 → BPD 05 (82 matches, 94% high confidence)

### REQ-022: Variance Detection and Classification
**Why Critical:** Prevents errors like the real-world Relius→ASC example from market research (see p.3) where a TPA inadvertently dropped the HCE inclusion in safe harbor contributions during a cross-vendor conversion (not caught until after year-end).

**What It Does:**
- Detects text differences, missing provisions, new provisions, default value changes
- Proposes classification: Administrative / Design / Regulatory
- Assigns impact level (High/Medium/Low) with justification
- Flags "None" (identical) as low-priority

### REQ-024: Confidence Scoring and Abstention
**Why Critical:** Enables the 70-90% automation target. AI must know when it's uncertain.

**What It Does:**
- Scores each mapping/classification (0-100%)
- Graduated thresholds (90/70/low)
- Displays reasoning with specific evidence
- Tracks accuracy over time (% of high-confidence mappings accepted vs rejected)

### REQ-030: Exception Log Auto-Population
**Why Critical:** Replaces manual Excel spreadsheet tracking (current industry practice).

**What It Does:**
- Auto-creates exception entries from variances (Design/Regulatory/HIGH impact)
- Populates structured fields (ID, description, category, risk, dates, status)
- Exports to CSV matching `/process/templates/exception_log.csv`
- Allows import of existing logs to merge with AI-generated exceptions

---

## Market Research Findings (Key Quotes)

### What's Automated Today:
✅ Document generation (Relius, ASC, ftwilliam) - creating new plan docs from templates
✅ Internal consistency checks - validation logic prevents incompatible elections
✅ Batch operations - mass restatements (ASC: "1,500 plans in a day")
✅ E-signature/distribution - DocuSign integration, client portals

### What's Still Manual (Our Opportunity):
❌ **"True document-to-document reconciliation remains largely manual. It relies on the expertise of compliance professionals to interpret and compare provisions."** — Market Research, p.4

❌ Provision-by-provision reconciliation - "determining how a new document differs from the old (in substance) is manual"

❌ Exception tracking - "Excel spreadsheets or Word tables that get circulated among the conversion team"

❌ Data entry for conversions - "someone re-enters it or maps it field by field"

### Competitive Landscape:
- **PlanPort (2025)** - Only AI competitor. Does single-doc analysis (extraction/summarization), NOT doc-to-doc comparison. Reports "70-90% of the way there" with human review. Positioned as "cyborg" tool.
- **DATAIR** - Limited reconciliation within own ecosystem (doc module ↔ admin module), not cross-provider
- **No other AI-first tools identified**

### Real-World Pain Example (Cross-Vendor Conversion):
> "During the recent Cycle 3 restatement, one TPA switched a client's document from a Relius volume submitter to an ASC prototype. A subtle plan provision was inadvertently dropped – Relius had automatically allowed a discretionary safe harbor contribution to include Highly Compensated Employees by default, whereas the new ASC document required checking a box to include HCEs, which the preparer missed. This oversight wasn't caught until after year-end." — Market Research, p.3

**This is the class of error REQ-022 must prevent.**

**Note:** This is a real-world cross-vendor example from market research. The POC validates the detection algorithm using Ascensus BPD 01 → BPD 05 (intra-vendor). The algorithm is vendor-agnostic and applies to both scenarios.

---

## Regulatory Context (From `/process`)

### The Four Controls:
1. **Control 001: Plan Qualification** - Anchor in IRC §401(a) / ERISA qualification requirements
2. **Control 002: Document Reconciliation** - Provision mapping & variance detection (⭐ MVP FOCUS)
3. **Control 003: Exception Handling** - Variance tracking to closure
4. **Control 004: Amendment & Sign-off** - Final execution, sign-off, archive

### Evidence Produced:
- Qualification Review Memo
- Plan Comparison Workbook (side-by-side provisions)
- Exception Log with approvals
- Executed Restated Plan Package (incl. Opinion Letter)

### Regulatory References:
- **IRC §401(a)** - Qualified plan requirements
- **ERISA §§101–404** - Fiduciary duties, disclosures, record retention
- **Rev. Proc. 2017-41** - Pre-Approved Plan Program (opinion letters, reliance)
- **Rev. Proc. 2021-30** - EPCRS (Employee Plans Correction System)
- **DOL Reg. §2520.104b-1** - Disclosure/recordkeeping requirements

---

## Important Terminology

**Plan Document Components:**
- **BPD** (Basic Plan Document) - IRS pre-approved template with legal language (often incomplete - references "as elected in AA")
- **Adoption Agreement (AA)** - Employer's elections/choices overlaid on BPD (incomplete - options without framework)
- **Plan Provision** - Complete semantic unit = BPD Provision + linked AA Election(s). The correct unit for cross-vendor comparison.
- **Amendment** - Modifications to plan over time (interim or restated)
- **Opinion Letter** - IRS letter confirming pre-approved document meets §401(a) qualification
- **SPD** (Summary Plan Description) - Participant-facing summary

**Key Terminology (ADR-001):**
- **BPD Provision** - Template text from BPD, often with conditional/placeholder language ("as elected in AA")
- **AA Election** - Election form with available options (no selected values at template level)
- **Plan Provision** - BPD Provision + linked AA Election(s) = complete semantic unit for comparison
- **Election-dependent provision** - BPD provision whose meaning requires AA elections to be complete (e.g., vesting schedules)
- **Template level** - BPD+AA structure and options, before any values selected (current phase)
- **Filled level** - BPD+AA with actual employer selections (future phase - requires value substitution)

**Provision Types (for extraction/mapping):**
- Eligibility (age, service requirements)
- Compensation (W-2, 415 safe harbor, etc.)
- Contributions (match, profit-sharing, safe harbor, QACA/EACA)
- Vesting (schedules, cliff, graded)
- Distributions (in-service, hardship, loans)
- Top-Heavy provisions
- Coverage/ADP/ACP testing parameters

**Variance Classification:**
- **Administrative** - Wording/formatting only, no substantive change
- **Design** - Employer election changed (requires sponsor approval)
- **Regulatory** - Required by Cycle/law change (informational, not optional)

**Impact Levels:**
- **High** - Affects participant rights, contribution calculations, or qualification
- **Medium** - Operational impact but correctable via amendment
- **Low** - Administrative clarification or formatting

**TPA** - Third-Party Administrator (firm that handles plan administration, compliance, testing for employers)

**Recordkeeper** - Platform that tracks participant accounts, contributions, investments

**Cycle 3 Restatement** - IRS requires periodic updates to pre-approved plan documents (Cycle 3 is recent/current)

---

## Working with This Project

### For AI Assistants:

**When starting a new conversation:**
1. Read this file first for context
2. Check `/requirements/README.md` for current MVP scope
3. Review `/research/market_research.pdf` findings (summarized above)
4. Reference `/process/control_002_document_reconciliation.md` - this is the core workflow we're automating

**When making changes:**
1. Update this file if design decisions change
2. Keep `/requirements/functional_requirements.md` as source of truth for "what"
3. Don't propose changes to `/process` (that's the regulatory framework, not the software)
4. Always maintain human-in-the-loop philosophy (never fully autonomous)

**When adding requirements:**
1. Use REQ-XXX numbering (next available in range)
2. Map to specific control (001-004) or mark as cross-cutting
3. Include user story, acceptance criteria, and context from market research where applicable
4. Update traceability table in `/requirements/functional_requirements.md`

**When discussing architecture/design:**
1. This is LLM-first by design (semantic understanding is core capability)
2. Consider locked PDF handling (vision fallback required)
3. Target 70-90% automation (inspired by PlanPort benchmark)
4. Output must match `/process/templates/` CSV schema for compatibility

**When developing LLM prompts:** ⭐ CRITICAL WORKFLOW
1. **NEVER hardcode prompts in Python code** - Always externalize to `/prompts` directory
2. **ALWAYS seek Sergio's approval** before implementing new prompts or modifying existing ones
3. **Slow down and review** - Prompt engineering is a collaborative, iterative process
4. **Present draft prompts** for discussion before implementation
5. **Document prompt rationale** - Explain why specific instructions/examples were included
6. **Version prompts** - Use descriptive filenames (e.g., `provision_extraction_v1.txt`)

**Prompt Development Workflow:**
1. AI proposes draft prompt with rationale
2. Sergio reviews and provides feedback
3. Iterate on prompt design together
4. Once approved, externalize to `/prompts` directory
5. Python code loads prompt from file at runtime
6. Track prompt versions and changes in git

**Why this matters:**
- Prompts are the core "business logic" of LLM-first applications
- Small prompt changes can have large impacts on output quality
- Domain expertise (ERISA/retirement plans) is critical for prompt accuracy
- Sergio owns the regulatory/compliance requirements that prompts must enforce

**When conducting Red Team Sprints:** ⭐ CRITICAL QUALITY ASSURANCE
Red Team Sprints are adversarial testing sessions conducted after major milestones to validate claims about accuracy, performance, and quality before proceeding to the next phase.

**Purpose:**
- Validate LLM output quality claims (e.g., "94% high confidence," "19% match rate")
- Identify false positives (incorrect matches) and false negatives (missed matches)
- Test edge cases and unusual document structures
- Calibrate confidence scoring thresholds
- Prevent costly errors in high-stakes compliance domain

**When to Conduct:**
- After completing major milestones (e.g., "BPD crosswalk complete," "AA extraction complete")
- Before declaring a component "production-ready"
- When introducing new prompts or model versions
- When accuracy claims will inform product/architecture decisions

**Sprint Structure:**
1. **Define Test Scope** (15 min)
   - Identify specific claims to validate
   - Select representative sample size (typically 10-20 items per category)
   - Define pass/fail criteria

2. **Execute Adversarial Testing** (2-4 hours)
   - Manual verification of random samples
   - Targeted testing of edge cases
   - Cross-reference with domain expertise
   - Document all failures with evidence

3. **Document Findings** (30 min)
   - Create `/test_results/red_team_YYYY-MM-DD.md`
   - Record validated claims vs. discrepancies
   - Classify failures by severity (Critical/High/Medium/Low)
   - Propose corrective actions

4. **Update Project Artifacts** (30 min)
   - Adjust accuracy claims in CLAUDE.md if needed
   - Update requirements if targets unrealistic
   - Iterate on prompts based on failures
   - Add defensive measures to architecture

**Example Test Categories:**
- Semantic mapping accuracy (false positive/negative rates)
- Vision extraction completeness (missed provisions, hallucinations)
- Variance classification correctness (Administrative vs Design vs Regulatory)
- Impact level assessment (High vs Medium vs Low)
- Confidence score calibration (90%+ scores should be 90%+ accurate)
- Edge case handling (unusual formatting, handwritten amendments, corrupted PDFs)

**Exit Criteria:**
- Either: Claims validated with documented evidence
- Or: Specific issues documented with corrective action plan
- Never: Proceed with unvalidated claims

**Integration with Development:**
- Red Team findings may require prompt iteration
- Failed tests block progression to next milestone
- All findings tracked in version control (`/test_results/`)
- Lessons learned inform future prompt engineering

---

## Git Workflow

**Main branch:** `main`
**Commit style:** Descriptive messages with context

**Example commits from this project:**
- `cd76fdb` - "first commit"
- `3c60579` - "Restructure repo as software project with process spec"

**When committing:**
- Use conventional format with context (see existing commits)
- Include `🤖 Generated with [Claude Code](https://claude.com/claude-code)` footer
- Include `Co-Authored-By: Claude <noreply@anthropic.com>` when AI-assisted

---

## Open Questions / Future Decisions

### Technical Architecture (Resolved/Updated):
1. **LLM Strategy:** ✅ GPT-5 vision for extraction, GPT-4.1 for semantic mapping (Claude deferred due to rate limits)
2. **Data Models:** ✅ Provision, mapping, variance, crosswalk models complete
3. **Storage:** ✅ SQLite for structured storage (local-first compliant)
4. **Tech Stack:** ✅ Python + OpenAI SDK + PyMuPDF + Pydantic

### User Testing Priorities:
1. **Cross-vendor validation:** Obtain Relius, ftwilliam, DATAIR samples for cross-vendor testing
2. **Accuracy baseline:** Red Team Sprint validating 94% high-confidence claim (in progress)
3. **Confidence calibration:** Do users trust 90% threshold for bulk approval?
4. **Production pilot:** Test with real TPA on actual client conversion

### Post-MVP Integration:
1. **Relius/ASC APIs:** Can we export directly to their platforms?
2. **Workflow tools:** Should we integrate with PensionPro (industry-standard TPA CRM)?
3. **E-signature:** DocuSign vs other providers?

---

## Resources

**Market Research:** `/research/market_research.pdf` (12 pages, sources cited)
**Process Framework:** `/process/README.md` (control flow, templates, references)
**Functional Requirements:** `/requirements/functional_requirements.md` (62 requirements)

**External References:**
- IRC §401(a) - https://www.law.cornell.edu/uscode/text/26/401
- ERISA - https://www.dol.gov/general/topic/retirement/erisa
- Rev. Proc. 2017-41 - https://www.irs.gov/pub/irs-drop/rp-17-41.pdf
- Industry forums - BenefitsLink, ASPPA, NAPA (for practitioner insights)

---

## Project History / Changelog

**2025-10-30** - Phase 2 Complete: Crosswalk Mapping Document Generated
- **Afternoon (continued):** Phase 2 POC - Template-to-Template Crosswalk
  - Clarified complete three-phase architecture with user (key breakthrough)
  - **User correction:** We receive templates → generate mapping document → automate value transfer (when filled plans arrive)
  - **Phase 2 IS the mapping document** - NOT value substitution (that's Phase 3)
  - Built crosswalk script: embeddings + cosine similarity + LLM verification
  - Tested on 3 Relius → 2 Ascensus Plan Provisions
  - **Results:** 2 close matches, 1 no match (compensation missing in target)
  - LLM correctly identified variances (eligibility conditions vs entry dates, general vesting vs top-heavy)
  - No false positives (compensation → eligibility rejected with 0.2 confidence)
- **Deliverables:**
  1. [test_data/golden_set/phase1_merger_poc/crosswalk_plan_provisions.py](test_data/golden_set/phase1_merger_poc/crosswalk_plan_provisions.py)
  2. [test_data/golden_set/phase1_merger_poc/plan_provision_crosswalk.json](test_data/golden_set/phase1_merger_poc/plan_provision_crosswalk.json)
  3. [test_results/phase2_plan_provision_crosswalk_2025-10-30.md](test_results/phase2_plan_provision_crosswalk_2025-10-30.md)
- **Key Learnings:**
  - Mapping document is the PRODUCT (not intermediate step)
  - TPAs use mapping document to guide manual conversions today
  - Mapping rules will drive automated value transfer in future (Phase 3)
  - Template-level crosswalk works - no filled values needed
  - Two-phase architecture (embeddings → LLM) is cost-effective and accurate
  - Real-world workflow: Templates → Mapping Doc → Value Transfer (3 separate phases)

**2025-10-30** - Phase 1 + 1.5 Complete: Plan Provisions Validated
- **Morning:** ADR-001 approved with advisor feedback (merge-then-crosswalk decision)
- **Afternoon:** Phase 1 POC - Template-level Plan Provisions
  - Created Plan Provision data model ([design/data_models/plan_provision_model.md](design/data_models/plan_provision_model.md))
  - Implemented keyword-based linkage algorithm (100% success on 5 test provisions)
  - Generated Relius Plan Provisions (eligibility, compensation, vesting) with BPD+AA linkage
  - Generated Ascensus Plan Provisions (eligibility, vesting) for cross-vendor comparison
  - **Key finding:** Plan Provisions are complete semantic units (BPD incomplete, AA incomplete, Plan Provision complete)
- **Evening:** Phase 1.5 - Quantitative Validation
  - Tested embedding quality improvement hypothesis
  - **Result:** +6.2% average cosine similarity improvement (BPD-only vs Plan Provision)
  - **Election-dependent provisions:** Vesting showed +11.1% improvement (highest impact)
  - **Moderate election-dependence:** Eligibility showed +2.1% improvement
  - Validated two-phase crosswalk architecture (embeddings → top-k candidates → LLM verification)
- **Deliverables:**
  1. [test_data/golden_set/phase1_merger_poc/relius_plan_provisions.json](test_data/golden_set/phase1_merger_poc/relius_plan_provisions.json)
  2. [test_data/golden_set/phase1_merger_poc/ascensus_plan_provisions.json](test_data/golden_set/phase1_merger_poc/ascensus_plan_provisions.json)
  3. [test_data/golden_set/phase1_merger_poc/embedding_comparison_results.json](test_data/golden_set/phase1_merger_poc/embedding_comparison_results.json)
  4. [test_results/phase1_plan_provisions_poc_2025-10-30.md](test_results/phase1_plan_provisions_poc_2025-10-30.md)
  5. [test_results/phase1.5_embedding_quality_2025-10-30.md](test_results/phase1.5_embedding_quality_2025-10-30.md)
  6. [design/architecture/phase2_value_substitution_plan.md](design/architecture/phase2_value_substitution_plan.md)
- **Key Learnings:**
  - Template-level linkage proves concept without needing filled forms (derisked approach)
  - Embedding improvement correlates with election-dependence (vesting > eligibility > definitions)
  - Plan Provisions enable option-space comparison even without selected values
  - Keyword matching sufficient for POC (80% confidence), can enhance with explicit references later
  - Phase 2 ready to proceed: value substitution patterns documented and scoped

**2025-10-30** - ADR-001: Merge Strategy Decision
- **Morning:** Architectural decision session with advisor feedback
  - Question: Should we merge-then-crosswalk or crosswalk-then-merge?
  - Created formal ADR with decision hygiene (scope, risks, KPIs, rollback criteria)
  - Defined crisp terminology (BPD, AA, election-dependent provision, merge, crosswalk)
  - Specified merge mechanics (anchor finding, substitution, normalization, provenance)
  - Documented data models (MergedProvision, CrosswalkResult with full audit trail)
  - Catalogued 10 merge rule patterns (direct anchor, conditionals, vendor synonyms, etc.)
  - Hardened exit criteria per phase (precision/recall targets, coverage %, timing benchmarks)
  - Built evaluation plan (golden set, metrics, ablations)
  - Added reporting precedence rules (primary: merged, secondary: template diffs)
- **Decision:** Merge-Then-Crosswalk with phased implementation (proof-of-concept → MVP → pipeline)
- **Rationale:** Election-dependent provisions require merged comparison for semantic accuracy
- **Next:** Phase 1 proof-of-concept with 20-provision golden set
- **Key Learnings:**
  - Advisor feedback transformed initial analysis into production-ready ADR
  - Decision hygiene (assumptions, boundaries, metrics, risks) prevents scope creep
  - Data models and merge rules catalogue make "merge" concrete (not black box)
  - Phased approach derisks "merger is too hard" concern

**2025-10-21** - Embedding Research & False Positive Fix
- **Morning:** Vendor identity correction (Lauren Leneis meeting)
  - Source = Relius Cycle 3, Target = Ascensus (cross-vendor, not intra-vendor)
  - This validates algorithm on hardest use case (cross-vendor conversion)
  - File reorganization: `test_data/raw/relius/` and `test_data/raw/ascensus/`
  - Re-ran both crosswalks with correct direction: BPD (623→426, 92 matches), AA (182→550, 22 matches)
- **Afternoon:** Critical false positive discovered in AA crosswalk
  - **Finding:** Age eligibility (Q 1.04) matched to State address (Q 1.04) with 92% confidence
  - **Root cause:** Embeddings included question numbers → 1.0 cosine similarity for unrelated elections
  - GPT-5-Mini hallucinated semantic connection ("State" = "state the age")
- **Evening:** Research-driven fix for embedding pollution
  - Generated comprehensive research paper on semantic matching in legal documents
  - **Key insight:** "If we include non-semantics in the string we are going to skew cosine similarity"
  - Implemented Priority 1 & 2 fixes:
    1. Stripped question numbers from embeddings, added section context and election kind
    2. Added chain-of-thought prompting, negative example (Age→State), explicit warnings
  - **Result:** Embedding similarity drops to 47% (was 100% for false matches), LLM correctly rejects with 99% confidence
- **Key Learnings:**
  - Question numbers are provenance metadata only, must NOT influence semantic similarity
  - Embedding input must be "semantically clean" - only meaningful content, no structural artifacts
  - Chain-of-thought prompting prevents LLM hallucination
  - This is basic research - "boldly going where others have not yet gone"

**2025-10-20** - Documentation Correction & Red Team Sprint Framework
- **Morning:** Red Team Sprint framework introduced
  - Comprehensive adversarial testing methodology for validating LLM claims
  - 40-sample validation template for BPD crosswalk (ready for manual review)
  - Exit criteria: validate claims OR document corrective actions (never proceed unvalidated)
- **Afternoon:** Test corpus identity correction (GPT-5 Pro validation)
  - **Critical finding:** All test documents are Ascensus (not Relius → ASC as previously stated)
  - Corrected: "POC validates with Ascensus BPD 01 → BPD 05 (intra-vendor Cycle 3 restatement)"
  - Algorithm is vendor-agnostic; cross-vendor validation requires obtaining Relius/ftwilliam samples
  - Updated all documentation to distinguish "system capability" from "current test data"
- **Key Learnings:**
  - Intra-vendor BPD edition comparison is actually HARDER than cross-vendor (more subtle deltas)
  - 19% match rate for template comparisons validates correct detection of edition-specific changes
  - Real-world cross-vendor examples (market research) remain valid use cases for production

**2025-10-19** - POC Parallel Crosswalk Complete
- **Morning-Afternoon:** Vision extraction with GPT-5-nano (all 4 documents, 328 pages, 18 minutes)
  - Tested GPT-5-mini vs GPT-5-nano: nano proved more thorough (26 items vs 17 on same 5 pages)
  - Parallel extraction implemented (16 workers, batch size 1 to avoid JSON parse failures)
  - Enhanced prompts to preserve full provision text (user feedback-driven iteration)
- **Evening:** Parallel semantic crosswalk implementation
  - Added ThreadPoolExecutor to SemanticMapper (16 workers)
  - Completed BPD crosswalk: 2,125 verifications in 11 minutes (6x speedup)
  - Results: 82 matches (19.3%), 94% high confidence, 186 high-impact variances
  - CSV export working with confidence scores and variance classification
- **Key Learnings:**
  - Batch size 1 prevents JSON parse failures (88% failure rate with batch size 5)
  - GPT-5-nano more thorough than mini for structured extraction
  - GPT-5-Mini better for semantic reasoning than nano
  - 19% match rate on templates is expected/correct (election-dependent provisions can't match)

**2025-10-17** - Phase 1 Design Complete
- **Morning:** Created `/process` framework (four controls, templates, references)
- **Morning:** Ran DeepResearch on TPA compliance tools landscape
- **Morning:** Drafted functional requirements (62 requirements organized by control)
- **Afternoon:** Created `/design` structure (architecture, data models, LLM strategy)
- **Afternoon:** Comprehensive LLM research (Claude Sonnet 4.5 vs GPT-5 comparison)
- **Evening:** Phase 1 design review and key decisions:
  - ✅ SQLite for structured storage (not just JSON)
  - ✅ 10-15 minute processing acceptable (95%+ time savings vs manual)
  - ✅ CLI-first UI for POC (Web UI for MVP)
  - ✅ Docker for production deployment
  - ✅ Hybrid embeddings + LLM architecture (95% cost reduction)
  - ✅ No alternative matches stored (abstain when ambiguous)
  - ✅ Sequential multi-reviewer workflow (CLI limitation)
  - ✅ LandingAI DPT identified for vision fallback research

**2025-10-19** - POC Architecture Pivot & Vision Extraction
- **Critical Discovery:** Plan documents are BPD+AA pairs (not standalone docs)
  - BPDs contain template provisions with "as elected in AA" language
  - Adoption Agreements contain election options (structure) + elections (values when filled)
  - Need separate BPD and AA crosswalks for complete conversion mapping
- **Vision Extraction Strategy:**
  - Text parsing failed for complex AA forms (nested options, checkboxes)
  - Pivoted to vision-first extraction using GPT-5 (gpt-5-2025-08-07)
  - Successfully tested on single AA page - perfect structure capture
- **BPD Crosswalk Generated:**
  - Extracted 55 source + 234 target provisions using text extraction
  - Built semantic mapper with hybrid embeddings + LLM
  - Generated crosswalk: 15 high-confidence 1:1 matches (27% match rate on templates)
  - Validated semantic mapping algorithm works correctly
- **GPT-5 Vision Technical Findings:**
  - Model name: gpt-5-2025-08-07 (confirmed available)
  - Requires `max_completion_tokens=16000` (not `max_tokens`)
  - Successfully extracts nested option structures (d.1, d.2, d.3 under option d)
  - Handles fill-in fields, checkboxes, section context
  - User preference: "newer better more than 'safer'"
- **Current Status:** Running full vision extraction on all 4 documents

**Previous Work:**
- Sergio had explored PDF text extraction issues in earlier project
- Learned some PDFs are locked → required vision-based approach (informed REQ-002)

---

## Contact / Ownership

**Project Owner:** Sergio DuBois (sergio.dubois@gmail.com)
**GitHub:** https://github.com/sentientsergio/compliance-gpt
**License:** MIT

---

*Last Updated: 2025-10-30*
*Next Review: Before Phase 2 value substitution implementation*
