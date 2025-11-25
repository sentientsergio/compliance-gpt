This is a complex and high-value use case. Cycle 3 Restatements and Plan Conversions involve high liability; missing a provision or mapping it incorrectly can result in plan disqualification or operational failures.

I have performed a Proof of Concept (POC) analysis using the provided source (`Relius`) and target (`Ascensus`) documents. Below are the results of the mapping exercise, followed by my technical feedback and a proposed design architecture for building a robust AI solution.

### Part 1: POC Mapping Results (Sample of 10 Provisions)

I have mapped 10 common provisions from the **Source (Relius)** to the **Target (Ascensus)**.

- **Similarity Scale:**
  - **Exact:** Meaning is identical; legal effect is the same.
  - **Fuzzy:** Concepts match, but granularity or options differ (requires Analyst review).
  - **Gap:** Provision exists in Source but has no direct equivalent in Target, or vice versa.

| Provision                     | Source (Relius AA)                    | Target (Ascensus AA)                      | Provenance (Page/Sec)    | Similarity | Notes                                                                                                                                                                        |
| :---------------------------- | :------------------------------------ | :---------------------------------------- | :----------------------- | :--------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Eligibility Age**        | Q14.g (Conditions of Eligibility)     | Sec 2, Part A, 1 (Age Requirement)        | Rel: Pg 5<br>Asc: Pg 2   | **Exact**  | Both allow specification of age (max 21). Relius breaks it down by sub-option; Ascensus lists contribution types individually.                                               |
| **2. Eligibility Service**    | Q14.i (Year of Service)               | Sec 2, Part A, 2 (Eligibility Service)    | Rel: Pg 5<br>Asc: Pg 3   | **Fuzzy**  | Relius uses a single selection for "1 Year". Ascensus separates the service duration (1 year) from the contribution type it applies to.                                      |
| **3. Entry Date**             | Q15 (Effective Date of Participation) | Sec 2, Part C (Entry Dates)               | Rel: Pg 6<br>Asc: Pg 8   | **Fuzzy**  | Relius separates "Entry Date" options (Q15) from the definition of those dates. Ascensus combines the definition (e.g., "Semi-Annual") with the contribution type selection. |
| **4. Normal Retirement Age**  | Q20 (Normal Retirement Age)           | Sec 6, Part J, 2 (Normal Retirement Age)  | Rel: Pg 10<br>Asc: Pg 45 | **Exact**  | Both allow specific age (e.g., 65) or Age + Participation anniversary (e.g., 5th anniversary).                                                                               |
| **5. Comp. Definition**       | Q23 (Compensation)                    | Sec 6, Part A (Compensation...)           | Rel: Pg 11<br>Asc: Pg 40 | **Fuzzy**  | Relius asks for the "Base Definition" (W-2, 3401, etc.). Ascensus asks the same but requires selection _per contribution type_ (Deferrals vs Match vs Profit Sharing).       |
| **6. Exclusions from Comp**   | Q23.j-v (Adjustments)                 | Sec 6, Part A, 5 (Exclusion...)           | Rel: Pg 11<br>Asc: Pg 41 | **Fuzzy**  | Relius lists exclusions (Bonus, Overtime) linearly. Ascensus uses a matrix grid to exclude items specific to contribution types. _High fragmentation risk here._             |
| **7. Vesting Schedule**       | Q18 (Vesting)                         | Sec 4, Part B (Vesting... Profit Sharing) | Rel: Pg 9<br>Asc: Pg 33  | **Exact**  | Both offer standard 6-year graded, 3-year cliff, etc. The visual layouts of the tables differ significantly but the mathematical logic is identical.                         |
| **8. Loans**                  | Q42 (Loans to Participants)           | Sec 5, Part F (Loans)                     | Rel: Pg 32<br>Asc: Pg 39 | **Exact**  | Binary toggle (Yes/No). Note: Ascensus places specific loan rules in the BPD or a separate policy, whereas Relius puts some loan params in the AA.                           |
| **9. Hardship Distributions** | Q37 (Hardship)                        | Sec 5, Part A, 2, b (Hardship...)         | Rel: Pg 28<br>Asc: Pg 36 | **Fuzzy**  | Relius asks "Are hardships permitted?". Ascensus asks granularly: "Hardship for Deferrals? For Match? For Profit Sharing?". Target is more granular.                         |
| **10. In-Service Distrib.**   | Q38 (In-Service Distributions)        | Sec 5, Part A, 2, a (In-Service...)       | Rel: Pg 29<br>Asc: Pg 35 | **Fuzzy**  | Ascensus uses a complex grid to determine eligibility (Age 59.5, Normal Retirement Age, Vesting %) per contribution type. Relius uses a simpler list.                        |

---

### Part 2: POC Feedback & Challenges

During the execution of this manual POC (simulating an AI), several specific technical hurdles emerged that will dictate your system design:

**1. Structural Hierarchy vs. Visual Layout**

- **The Problem:** Relius uses a linear Question Numbering system (Q1, Q2, Q3). Ascensus uses a nested Hierarchy (Article \> Section \> Part \> Item).
- **Impact:** An LLM trying to map "Q14" to "Section 2 Part A" will hallucinate if it relies solely on text. It needs to understand that "Section 2" is the parent container for "Age" and "Service."
- **Recommendation:** You cannot rely on simple text extraction. You must use a **Hierarchical Document Parser** that rebuilds the document tree (e.g., `{"Section 2": {"Part A": {"Item 1": "Age"}}}`) before attempting comparison.

**2. "One-to-Many" Mapping Complexity**

- **The Problem:** The Source (Relius) often asks a global question: "What is the Eligibility Age?" The Target (Ascensus) often asks: "What is the Eligibility Age for Deferrals? For Match? For Profit Sharing?"
- **Impact:** A simple 1:1 cosine similarity search will fail. The system needs logic to recognize that one source provision must explode into three target fields.

**3. The "Grid/Matrix" Problem (Vision Capability)**

- **The Problem:** Ascensus (Target) makes heavy use of grids (Rows = Conditions, Columns = Contribution Types). Standard OCR reads this left-to-right, destroying the column logic.
- **Impact:** Text-only LLMs will read this as gibberish.
- **Requirement:** You generally _must_ use a multimodal model (like GPT-4o or Claude 3.5 Sonnet) capable of "vision" to interpret the X/Y coordinates of checkboxes within grids, OR use a specialized document layout analysis tool (like Azure Document Intelligence or Amazon Textract) configured for tables.

**4. Page Fragmentation (The "Straddle" Issue)**

- **The Problem:** In `ascensus_aa_profit_sharing.pdf`, Part A (Age) starts on Page 2 and continues to Page 3.
- **Impact:** If you feed the LLM one page at a time, it loses context.
- **Requirement:** The ingestion pipeline must support **logical chunking**, not page-based chunking. It must identify that "Part A" has not closed before moving to the next page.

---

### Part 3: Solution Design & Requirements

To move from POC to a working solution for Compliance Analysts, I recommend the following architecture.

#### 1\. Data Ingestion & Structure Extraction (The Critical Step)

Do not treat the PDF as a stream of text. Treat it as a structured object.

- **Tool:** Use **Azure AI Document Intelligence** (formerly Form Recognizer) or **Google Cloud Document AI**. These tools are trained to recognize key-value pairs and checkboxes in forms.
- **De-fragmentation Logic:** Write a pre-processing script that stitches pages together. If a "Section" header is found, all content following it is associated with that section until a new header of equal weight is found, ignoring page breaks.

#### 2\. The "Canonical Schema" Approach

Directly mapping Relius to Ascensus is brittle because you might eventually add a third vendor (e.g., Fidelity or Voya).

- **Strategy:** Define an intermediate **Canonical Data Model (JSON)** representing a standard 401(k).
  - _Example JSON Node:_ `Plan.Eligibility.AgeRequirement`
- **Process:**
  1.  Map Source (Relius) -\> Canonical Model.
  2.  Map Target (Ascensus) -\> Canonical Model.
  3.  Compare Canonical A to Canonical B.
      This creates a "Rosetta Stone" for plan documents.

#### 3\. Hybrid Retrieval (RAG + Keyword)

Cosine similarity (Vector search) is good for finding "fuzzy" concepts, but bad for exact legal terms (e.g., "401(a)(4)").

- **Design:** Use a hybrid search.
  - _Vector Search:_ To find "Eligibility" concepts.
  - _Keyword Search:_ To find specific Code references (e.g., "411(d)(6)").
  - _Vision Anchor:_ Use the visual headers extracted in Step 1 to limit the search scope (e.g., "Only look for Vesting provisions within Section 4").

#### 4\. The LLM "Analyst" (Comparison Logic)

Once the relevant chunks from Source and Target are retrieved, pass them to the LLM with a strict prompt.

- **Model:** GPT-4o (for vision/text handling) or Claude 3.5 Sonnet (excellent at following complex instructions).
- **Prompt Strategy:**
  > "You are a Compliance Analyst. Compare Provision A (Source) and Provision B (Target).
  >
  > 1.  Do they govern the same rule?
  > 2.  Is the Target more granular (asking for specific contribution types) than the Source?
  > 3.  Rate similarity: EXACT, FUZZY, or GAP.
  > 4.  If Fuzzy, explain the difference in legal effect."

#### 5\. Output & Human-in-the-Loop Interface

The output cannot just be a spreadsheet; it must be an auditing tool.

- **UI Requirement:** Split screen. Left side = Source PDF (highlighted). Right side = Target PDF (highlighted). Center = The AI's generated mapping.
- **Confidence Scores:** Flag low-confidence mappings (e.g., \< 85%) for human review.
- **Provenance Links:** Clicking a row in the spreadsheet must jump to the specific page/coordinate in the PDF.

### Summary Recommendation

Start with **Azure Document Intelligence** to crack the "checkbox/grid" problem. Without solving the extraction of tabular/form data, an LLM will hallucinate the mapping. Build the **Canonical Schema** to future-proof the application for other vendors.
