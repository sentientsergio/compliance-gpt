Here’s what I did:

- Pulled text from the four PDFs you gave me.
- Chose ~10 “provisions” from the **Relius** BPD + AA.
- Looked for the closest analogs in the **Ascensus** BPD + AA.
- Judged similarity (exact / close / fuzzy / no clear analog) and wrote short notes.

You’ll see the sample mapping first, then what I learned, then a suggested system design / requirements for a real solution.

---

## 1. Sample mapping (~10 provisions)

> **Important note on provenance:**
> I can reliably identify **sections / headings** and which document they come from. The snippets I see also include PDF page indices (like “PARSED TEXT FOR PAGE: 25 / 98”), so in a production system, page numbers can be captured programmatically. Here I’ll focus on **section-level provenance** and describe where the page info would come from.

### 1) Conditions of Eligibility (age / service)

**Source (Relius)**

- **Doc:** `relius_bpd_cycle3.pdf` – Basic Plan Document
- **Section:** Article III, **§3.1 CONDITIONS OF ELIGIBILITY** – Employee becomes eligible once they satisfy the age / service conditions elected in the Adoption Agreement; administrator may treat months as 30-day months.

**Target (Ascensus)**

- **Doc:** `ascensus_bpd.pdf` – Basic Plan Document (#3000)
- **Section:** **§2.01 ELIGIBILITY TO PARTICIPATE** – Employee is eligible once they satisfy age and eligibility service requirements specified in the Adoption Agreement; classes of excluded employees are also set there (e.g., union, non-resident aliens, acquired employees).

**Similarity judgment:** **Essentially exact**
Both documents:

- Defer the actual age/service criteria to the **Adoption Agreement**.
- Use the same overall structure (BPD defines framework, AA fills in numbers / classes).

**Notes:** In practice, the mapping is **Relius BPD §3.1 + Relius AA Section Two (age/service elections)** → **Ascensus BPD §2.01 + Ascensus AA Section Two, Part A**. The analytical “work” here is mostly aligning the section numbers and AA question numbering.

---

### 2) Effective Date of Participation / Plan Entry

**Source (Relius)**

- **Doc:** `relius_bpd_cycle3.pdf`
- **Section:** **§3.2 EFFECTIVE DATE OF PARTICIPATION** – after meeting eligibility, an Employee becomes a Participant as of the date elected in the Adoption Agreement; in all cases, the Plan must allow entry no later than 6 months or the first Plan Year following satisfaction of max age/service limits. Also includes rehire rule cross-referencing §3.5.

**Target (Ascensus)**

- **Doc:** `ascensus_bpd.pdf`
- **Sections:**

  - **§2.02 PLAN ENTRY** – continues participation from prior plan and defines entry for initial adopters and ongoing employees once §2.01 eligibility is satisfied.
  - **§2.03 TRANSFER TO OR FROM AN INELIGIBLE CLASS** – immediate participation upon rejoining eligible class (provided break rules not triggered).

**Similarity judgment:** **Very close / effectively equivalent**
Both BPDs:

- Tie participation start to **meeting eligibility requirements + entry date elected in AA**.
- Preserve IRS maximum delay rules.

**Notes:** This mapping is almost 1:1 at the BPD level. The **Adoption Agreement** in both systems carries the actual “entry date” elections (first of month / Plan Year quarter / etc.). The comparison engine needs to understand **“Participant” start is not just text but a function of BPD+AA together.**

---

### 3) Rehired Employees & Break in Eligibility Service (eligibility)

**Source (Relius)**

- **Doc:** `relius_bpd_cycle3.pdf`
- **Section:** **§3.5 REHIRED EMPLOYEES AND 1‑YEAR BREAKS IN SERVICE**, subsections (a)–(c).

  - (a) **Rehired Participant** – immediate re-entry unless excluded or prior service is disregarded.
  - (b) **Rehired Eligible Employee who had satisfied eligibility but never entered** – enters as of reemployment date or the entry date they would have had absent severance.
  - (c) **Rehired Employee who had not satisfied eligibility** – eligibility determined under current rules; treatment of computation periods when service is disregarded.

**Target (Ascensus)**

- **Doc:** `ascensus_bpd.pdf`
- **Section:** **§2.04 ELIGIBILITY TO PARTICIPATE AFTER A BREAK IN ELIGIBILITY SERVICE OR UPON REHIRE** –

  - (A) For someone not yet a Participant: pre‑break eligibility service is disregarded.
  - (B) For someone already a Participant: they remain a Participant / re‑enter on reemployment, subject to break rules.

**Similarity judgment:** **Very close / essentially equivalent**
Both:

- Distinguish between **people who were already Participants** vs **those who weren’t yet Participants** when the break occurred.
- Use the same conceptual split: **Participant continues** vs **non‑Participant’s prior service may be disregarded**.

**Notes:** This mapping is a nice example where the **language is different but the logic is almost identical.** A cosine-similarity / embedding step should pick up the conceptual overlap around “Break in Eligibility Service,” “rehire,” and “prior service disregard.”

---

### 4) Rule of Parity & One‑Year Hold‑Out (Breaks in Service)

**Source (Relius)**

- **Doc:** `relius_bpd_cycle3.pdf`
- **Section:** **§3.5(d)–(f)** – “rule of parity” and **One‑Year Hold‑Out Rule**.

  - **Rule of parity:** for Former Employees with no nonforfeitable Employer-derived interest, pre‑break service is ignored if consecutive 1‑year breaks ≥ max(5, pre‑break YOS).
  - **One-year hold-out:** if elected, the plan temporarily disregards pre‑break service until the Participant completes a Year of Service after the break.

**Target (Ascensus)**

- **Doc:** `ascensus_bpd.pdf`
- **Section:** **§4. Vesting Breaks in Service** (e.g., paragraphs D.1–D.2) –

  - Describes **ignoring post‑break vesting service** after 5 consecutive Breaks in Vesting Service for pre‑break accruals, and conditions for restoration.

**Similarity judgment:** **Close but not perfect**

- Both implement **five consecutive breaks** logic and pre‑ vs post‑break accounts.
- Relius explicitly tags this as “rule of parity” and allows **applicability elections** for eligibility and/or vesting in the AA.
- The Ascensus BPD snippet is focused on vesting consequences and restoration.

**Notes:**
This is a **good “fuzzy match”**:

- Conceptual structure is the same (5 breaks, disregarded service, separate pre‑/post‑break accounts).
- Implementation details and where elections appear differ.
  The matching engine should mark this as “Similar – rule of parity / vesting break alignment; see notes” and surface the differences (e.g., Relius lets the AA turn off the rule for eligibility).

---

### 5) Hardship Withdrawals – Safe Harbor Events

**Source (Relius)**

- **Doc:** `relius_bpd_cycle3.pdf`
- **Section:** Hardship withdrawal section (late Article XII): enumerates **immediate and heavy financial need events**: medical expenses, purchase of principal residence, tuition / education, prevention of eviction/foreclosure, funeral expenses, casualty damage to home; plus references to Reg. §1.401(k)-1(d)(3)(iii)(B).

**Target (Ascensus)**

- **Doc:** `ascensus_bpd.pdf`
- **Section:** **§5.01(C)(2)(a)-(b) – Hardship Withdrawals** for Employer contributions and Elective Deferrals.

  - Uses essentially the same enumerated list of safe harbor events, plus requirements to first take other distributions/loans, and to suspend Elective Deferrals for 6 months (for the classic safe harbor).

**Similarity judgment:** **Essentially exact**
The phrases and ordering of events are extremely close; it appears to be the same underlying pre‑approved text.

**Notes:**
For mapping, you’d basically mark this as **“Exact safe harbor hardship language”** and then attach the AA’s elections on:

- Whether hardship is available from which sources, and
- Whether to use safe harbor or a looser definition.

---

### 6) Hardship Based on Primary Beneficiary’s Hardship

**Source (Relius)**

- **Doc:** `relius_bpd_cycle3.pdf`
- **Section:** Hardship section, **Beneficiary-based distribution** – participant’s hardship event can include immediate and heavy financial need of the **“primary Beneficiary under the Plan”**, limited to specific categories like education, funeral, and certain medical expenses, if elected in the Adoption Agreement.

**Target (Ascensus)**

- **Doc:** `ascensus_aa_profit_sharing.pdf` – Adoption Agreement
- **Section:** Section Five, Part A, item **(2)(b)(iii) “Hardship Availability Due to Beneficiary Hardship”** – simple yes/no option on whether hardship distributions are also permitted because of hardship incurred by the Primary Beneficiary.

**Similarity judgment:** **Conceptually exact, structurally split**

- Relius puts the rule text in the BPD and toggles it via AA elections.
- Ascensus splits: the BPD defines the concept; the AA gives a concise election “Allow beneficiary hardship? Y/N”.

**Notes:**
The mapping engine needs to understand **cross-document dependency**:

- Source “provision” is **(BPD language + AA switch)**.
- Target “provision” is **(BPD language + AA switch)**, but the AA part is a one-line option.

---

### 7) Vesting of Employer Nonelective / Profit Sharing Contributions

**Source (Relius)**

- **Doc:** `relius_aa_cycle3.pdf`
- **Section:** Question **18 – VESTING OF PARTICIPANT'S INTEREST**, sub‑section “Vesting for Employer Nonelective Contributions” – options:

  - N/A,
  - 100% immediate vesting, or
  - standard vesting schedules: 6‑year graded, 4‑year graded, 5‑year graded, 3‑year cliff, or “Other” schedule (subject to being at least as liberal as required).

**Target (Ascensus)**

- **Doc:** `ascensus_aa_profit_sharing.pdf`
- **Section:** **Section Four, Part B – Vesting Schedule for Employer Profit Sharing Contributions** – table with “Profit Sharing Option 1–5” listing percentages at years 0–6; Option 1 is immediate 100%; Options 2–3 match the standard IRS 3‑year cliff / 6‑year graded patterns; Options 4–5 allow custom schedules subject to minimums.

**Similarity judgment:** **Exact schedules with cosmetic differences**

- The available schedules and constraints align almost exactly.
- Naming of “Option 1/2/3” vs numeric list 1–5 in Relius is slightly different.

**Notes:**
A good mapping row in a spreadsheet would capture, for example:

- **Source:** Relius AA Q18(e)(1) “6 Year Graded”
- **Target:** Ascensus AA Section Four, Part B, Option 3 (6‑year graded)
- **Similarity:** Exact – same percentages by year.

---

### 8) Vesting of Matching Contributions

**Source (Relius)**

- **Doc:** `relius_aa_cycle3.pdf`
- **Section:** Question 18 – “Vesting for Employer matching contributions” –

  - Can be N/A,
  - Same schedule as nonelective,
  - 100% immediate, or
  - separate standard schedule (6‑year, 4‑year, 5‑year, 3‑year, or custom).

**Target (Ascensus)**

- **Doc:** `ascensus_aa_profit_sharing.pdf`
- **Section:** **Section Four, Part A – Vesting Schedule for Matching Contributions** – table with Options 1–5 having the same structure and percentages as the Employer Profit Sharing vesting table.

**Similarity judgment:** **Exact**
Again, this is essentially the same parameterized vesting engine with slightly different naming.

**Notes:**
The tool would want to:

- Read the **chosen option** on Relius side (e.g., 6‑year graded).
- Map it to the **equivalent target table option**.
- Call this “Exact” and move on.

---

### 9) QACA Safe Harbor Vesting

**Source (Relius)**

- **Doc:** `relius_aa_cycle3.pdf`
- **Section:** Q18 “Vesting for QACA safe harbor contributions” –

  - Option for 100% immediate vesting, or
  - 2‑year cliff schedule (0% then 100% at 2 years), or
  - custom, but must be as liberal as required.

**Target (Ascensus)**

- **Doc:** `ascensus_aa_profit_sharing.pdf`
- **Section:** **Section Four, Part C – Vesting Schedule for QACA ADP Test Safe Harbor Contributions**, with options:

  - Option 1 – 100% from start;
  - Option 2 – 2‑year vesting;
  - Option 3 – custom, subject to limits.

**Similarity judgment:** **Exact / trivial mapping**

**Notes:**
The more interesting part here is cross‑linking to the **BPD** statement that QACA contributions must vest within 2 years and are fully vested upon NRA / plan termination, etc.

---

### 10) Elective Deferral Procedures (Commencement, Changes, Escalation)

**Source (Relius)**

- **Doc:** `relius_aa_cycle3.pdf`
- **Section:** **F. Elective Deferral procedures** – includes:

  - Optional initial date other than effective participation date.
  - How often deferrals can be modified (per payroll, monthly, quarterly, twice per year, etc.).
  - Optional automatic **escalation** (amount, max %, timing),
  - Treatment of **suspension** and resumption of deferrals,
  - Re‑enrollment / lapse of affirmative elections,
  - Special rule for **rehired Employees** under automatic deferral provisions.

**Target (Ascensus)**
This functionality is **more distributed** on the Ascensus side:

- **BPD:** salary deferral election procedures & automatic contribution arrangements (e.g., plan‑imposed limits on deferral %, re‑enrollment, automatic escalation rules).
- **AA:** sections dealing with **Automatic Deferral**, re‑enrollment, and annual change dates (those are present elsewhere in the Ascensus AA, though we’re not seeing the exact “F. Elective Deferral procedures” heading in the snippets I have).

**Similarity judgment:** **Fuzzy / structurally different, conceptually similar**

**Notes:**
This is exactly the sort of mapping that **won’t be a simple 1:1 section match**:

- Relius AA has a neat, self‑contained **“F. Elective Deferral procedures”** block.
- Ascensus splits the same ideas into **BPD generic procedures** + **AA elections in several parts** (automatic enrollment, change dates, etc.).

The mapping system would likely produce something like:

> **Match Type:** Many‑to‑many (Relius AA F ↔ Ascensus BPD deferral procedures + Ascensus AA automatic deferral elections)
> **Similarity:** Conceptually aligned; structural differences; manual review required.

---

## 2. What I learned from this POC

### 2.1 Text access & structure

- All four PDFs expose **readable text** (they’re not locked/scanned), so I could work directly with the extracted text.

- The BPDs clearly share a **common vendor / template** – both Relius and Ascensus BPDs show “Defined Contribution Pre‑Approved Plan © 2020 Ascensus, LLC or its suppliers”.

  - That means BPD‑to‑BPD mapping in this particular example is almost trivial – often **identical paragraphs** with different wrapper branding.
  - In real conversions (Relius → _different_ vendor), the BPDs could diverge more.

- The AAs are also clearly based on the **same master AA** (“MASTER AA – Non‑Standardized Defined Contribution”), but present elections differently (e.g., question numbering, grouping).

### 2.2 Where the “real work” is

- **BPD level**: For these documents, most provisions are **exact or near-exact**; a simple **string / embedding similarity** finds them easily.
- **Adoption Agreement level**:

  - This is where **choices** live (vesting schedules, eligibility service, sources for hardship, auto‑deferral parameters).
  - Provisions are expressed as **tables / checkboxes / option lists** rather than full prose.
  - Vendors rearrange and regroup questions, so e.g.:

    - Relius has a single “Elective Deferral procedures” block.
    - Ascensus spreads that logic across automatic deferral questions, in‑service / hardship rules, and the BPD’s general deferral procedures.

**Conclusion:** The hard problem isn’t “find this sentence in another PDF,” it’s:

> “Given a **conceptual provision** (e.g., ‘how often can participants change elective deferrals?’), find all the relevant text + elections in **both** the BPD and AA of the target system and decide whether they implement the same real‑world behavior.”

### 2.3 Cross‑document provisions

- Many provisions are **split across BPD + AA**:

  - Hardship due to beneficiary: BPD defines the rule; AA toggles Y/N.
  - QACA vesting: BPD states “must vest within 2 years” and circumstances of full vesting; AA chooses the actual schedule.

- A useful comparison unit is therefore **“Plan-level provision”**, which often equals:

  > BPD legal text + one or more AA elections.

The mapping system needs to re‑assemble these “composite provisions” before it compares source vs target.

### 2.4 Pagination & straddling

- Provisions frequently **run across pages** (e.g., hardship list starts on one page, finishes on the next).
- The extraction I see already surfaces a single page at a time, so any naive “page‑by‑page” comparison will fragment provisions.
- To get good mapping units, you want **semantic chunks**, not pages:

  - Entire section (“§3.5 Rehired Employees”),
  - Sub‑section (3.5(a)–(c)), or
  - A table/question plus its explanatory footnotes.

### 2.5 Similarity categories

From this small sample, reasonable categories feel like:

1. **Exact underlying provision** – same text or same template (mostly BPDs here).
2. **Semantically equivalent with structural differences** – e.g., Relius “Elective Deferral procedures” vs distributed Ascensus elections.
3. **Partially overlapping** – e.g., a rule of parity provision that in one system applies to eligibility + vesting, in the other only to vesting.
4. **No clear analog / missing** – genuinely absent or implemented via plan‑specific addenda.

These categories map nicely to how human reviewers already think about the mapping spreadsheets.

---

## 3. Proposed design & requirements for a real solution

Here’s how I’d design an AI‑assisted mapping system for this problem.

### 3.1 Overall goals

- Input:

  - Source: BPD + AA pair (Relius)
  - Target: BPD + AA pair (Ascensus or other vendor)

- Output:

  - A **structured mapping** of plan‑level provisions with, for each mapping:

    - Source doc, section, (PDF page), and text snippet.
    - Target doc, section, (PDF page), and text snippet.
    - **Similarity rating** (Exact / Close / Partial / None).
    - **Short explanation of differences**.
    - Possibly a risk/impact tag (“behaviorally identical”, “could change participant outcomes”, etc.)

### 3.2 Ingestion & OCR layer

**Requirements**

1. **Robust PDF ingestion**:

   - Extract text with bounding boxes and style (font size, bold, numbering).
   - Handle both **BPD** and **AA**, which often have tables / checkboxes.

2. **OCR / vision fallback**:

   - For vendor‑locked or image‑only PDFs, run OCR + **layout analysis** (e.g., table recognition for grids of elections).
   - Preserve relationship between **labels** and **check boxes / values**.

3. **Canonical structure**:

   - Identify document type (BPD vs AA) and major headings (Article/Section numbers, question numbers).

### 3.3 Provision segmentation

This is critical: define what a “provision” is.

**Approach**

- Use a combination of:

  - **Rule‑based heuristics**: detect patterns like:

    - “ARTICLE X / SECTION X.Y / §X.Y.Z”
    - Numbered questions in the AA (“18. VESTING OF PARTICIPANT’S INTEREST”).
    - Indented lists (1., 2., (a), (b)) and tables.

  - **LLM assistance**: given a chunk, ask the model to split it into **legal sub‑provisions** (each with a distinct “if X then Y” meaning).

- Each provision gets:

  - A **hierarchical ID** (e.g., `BPD 3.5(d)(1)` or `AA Q18.e.1`).
  - Its **raw text + normalized paraphrase** (“plain English” summary).
  - Links to **all page spans** it covers.

This segmentation also solves the **straddling pages** issue: the provision is the aggregation of the relevant pages, not one page slice.

### 3.4 Embeddings & candidate retrieval (cosine similarity)

Once you have provision units, you can do **semantic search**.

**Embedding strategy**

- For each provision, create one or more embeddings:

  - **Full provision** embedding.
  - Possibly separate embeddings for **the header** (“Rehired Employees and 1-Year Breaks in Service”) and **the body logically summarized**.

- Use a model appropriate for legal/financial text (e.g., an OpenAI embeddings model tuned for long legal content).

**Cosine similarity**

- Store embeddings for:

  - All source provisions.
  - All potential target provisions (BPD + AA).

- For each source provision:

  1. Use cosine similarity to **retrieve the top N candidate provisions** in the target space.
  2. Optionally combine with **lexical signals** (shared section numbers, terms like “QACA,” “Hardship,” “Vesting,” “Break in Service”).

This gives a **candidate mapping set** for each source provision.

### 3.5 LLM-based alignment & scoring

Embeddings alone are not enough, especially for:

- Many‑to‑many mappings.
- Provisions split across BPD + AA.

So, for each source provision and its candidate targets:

1. **LLM comparison prompt**:

   - Feed the **source provision (text + normalized summary)**.
   - Feed the **candidate target provision(s)**.
   - Ask the model to:

     - Decide if they are about the **same concept** (e.g., hardship, QACA vesting, eligibility service).
     - Rate semantic similarity (e.g., 0–1 or discrete categories).
     - Identify **key differences** (e.g., “target requires 2 years of participation for in-service distribution; source requires only 1”).

2. **Cross‑document reasoning**:

   - The prompt should allow **multiple target snippets** at once (BPD + AA) so the model can see that e.g. hardness due to beneficiary is BPD+AA in both systems, even if the sentences live in different sections.

3. **Classification schema**:

   - Exact / functionally identical.
   - Equivalent but narrower or broader.
   - Partially overlapping (some scenarios differ).
   - No meaningful match.

4. **Structured output**:

   - JSON‑like structure with:

     - `source_provision_id`
     - `target_provision_ids`
     - `similarity_score`
     - `category` (exact/close/partial/none)
     - `difference_summary` (2–3 sentences)
     - Potential **impact tag** (“could reduce vesting periods,” “changes hardship availability for Matching Contributions,” etc.).

### 3.6 Handling BPD + AA pairs explicitly

We should **model the plan as a whole**, not just documents:

- Define **Plan Concept Types** (ontology), e.g.:

  - Eligibility, Plan Entry, Service Crediting, Vesting, Contributions (Elective Deferral / Matching / Profit Sharing / QACA), Hardship, Loans, In‑Service Distributions, Rollover Acceptance, Top‑Heavy Rules, etc.

- For each concept:

  - Link all relevant BPD and AA provisions on the **source** side.
  - Link all relevant BPD and AA provisions on the **target** side.

This allows the system to say:

> “Source ‘Hardship on Beneficiary need’ lives in BPD §12.10(b) + AA QXX. Target lives in BPD §5.01(C)(2) + AA Section Five, Part A(2)(b)(iii).”

…and then compare **concept-to-concept**, not just section-to-section.

### 3.7 Provenance, pages, and traceability

Requirements:

- For every provision, capture:

  - **Document name**
  - **Section / question IDs**
  - **PDF page ranges** (from the extraction step)
  - **Coordinates** on the page (bounding boxes), if you want to highlight them visually later.

- For every mapping row, store:

  - The **source and target provenance** (doc + section + pages).
  - The **exact text snippet** or a short excerpt.
  - The LLM’s **explanation** and **confidence**.

This is exactly what your mapping spreadsheet calls “provenance.”

### 3.8 UX for compliance analysts

The end user (compliance analyst) should be able to:

1. See a **grid**: one row per source provision, showing:

   - Source description
   - Target description
   - Similarity category
   - Short difference note

2. Click a row to open:

   - Side‑by‑side **document view**, highlighting the relevant BPD+AA locations (with page, section, maybe a mini PDF viewer).

3. Edit:

   - Override similarity category (e.g., mark something as “No mapping—removed feature”).
   - Add free‑form comments.
   - Merge / split mappings (e.g., one‑to‑many situations).

4. Export:

   - **Excel / CSV** mapping that matches your existing format.

### 3.9 Technical & process aspects

- **Model choice**

  - Strong general LLM for legal reasoning (for alignment and difference explanation).
  - Good embeddings model for long, technical text.

- **Performance**

  - Precompute embeddings and segmentation so that only the **comparison** is done interactively.
  - Use a vector database for candidate retrieval.

- **Evaluation**

  - Build a **gold standard**: a set of real mapping spreadsheets created by analysts for a handful of conversions.
  - Metrics:

    - Recall @K (does the correct match appear in top K candidates).
    - Agreement between AI similarity category and human classification.
    - Time saved per mapping (how many rows needed manual work).

- **Phased rollout**

  1. Start with **BPD‑to‑BPD** mapping where the language is very similar (like this example) to validate the pipeline.
  2. Add **AA‑to‑AA** mapping for straightforward numeric tables (vesting schedules, eligibility service, etc.).
  3. Tackle **hard composite provisions** (hardship, auto‑deferral, loans) with more advanced multi‑chunk comparison.
  4. Eventually handle **cross‑vendor** conversions where BPD templates really differ.

---

## 4. Quick recap

- On your sample documents, many BPD provisions are **essentially the same text**, so AI can very confidently mark them “Exact” once segmented correctly.

- Most of the real complexity is:

  - In the **Adoption Agreements**,
  - In **how provisions are split** across BPD & AA,
  - And in matching **composite behaviors** rather than just paragraphs.

- A robust solution will:

  - Parse & segment both BPD and AA into **concept-level provisions**,
  - Use **embeddings + cosine similarity** to find candidate matches,
  - Let an **LLM do deep comparison and explanation**,
  - And surface all of this in a **reviewable spreadsheet / UI** with strong provenance (doc, section, pages).

If you’d like, next step could be: pick one concept (e.g., hardship or loans) and design the **exact JSON/provision schema and prompts** we’d use for that end‑to‑end pipeline.
