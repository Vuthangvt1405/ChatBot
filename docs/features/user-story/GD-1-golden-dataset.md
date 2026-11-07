# Epic: Golden Dataset Builder

> A separate app from the chatbot. One AI engineer collects raw data from public web pages and their own files, cleans it, reviews it item by item, and exports only the approved items as a versioned golden dataset for model evaluation or training.

**Raw requirement:** "i want create app for research get data and help handle data for AI Engineer training model, goal it's make golden data set"

**Answers so far:** the data is used to evaluate or train a model · raw data comes from public web pages and the user's own files · one reviewer (the user) approves each item · the only user is the AI engineer, no team roles.

## Requirement Analysis

| Item | Finding |
|---|---|
| Actors | **AI engineer** (the only user; collects, cleans, reviews and exports). No other people. |
| Goals | Collect raw data from web pages and own files → turn it into dataset items → clean it → approve or reject each item → export the approved items as a golden dataset |
| Business value | *(assumed)* A trusted, checked dataset gives model evaluation scores you can believe and better training results. Saves the time spent today on copy-paste and spreadsheets, and every item can be traced back to where it came from. |
| Rules & constraints | **Stated:** sources are public web pages and own files; one reviewer approves; single user. **Assumed:** each item = *input* + *expected output* (+ optional extra fields); only approved items reach the export; each dataset is marked as either *Evaluation* or *Training*; the app runs on the user's own computer, so no login |
| Data involved | Dataset (name, purpose), Source (web page or file: title, URL/file name, collected date, text), Item (input, expected output, extra fields, source link, status Draft/Approved/Rejected, reject reason), Export version (number, date, item count, note) |
| Ambiguities | "handle data" (which cleaning steps?), "own files" (ready-made rows or documents to read?), the exact item shape, whether duplicates include items that mean the same thing worded differently, whether evaluation and training data must be kept apart, and personal data in own files. See Open Questions. |

## Estimation Log

| Candidate story | Complexity | Uncertainty | Effort | Points | Action |
|---|---|---|---|---|---|
| Golden dataset app (everything) | High | High | High | 40+ | ✂️ Split by workflow step: set up → collect → write → clean → review → export |
| ↳ GD-1: Create a dataset and browse its items | Low | Low | Medium | 3 | ✅ Keep |
| ↳ Collect raw data from web pages and own files | High | Medium | High | 13 | ✂️ Split by source → GD-2, GD-3, GD-4 |
| ↳↳ GD-2: Import items from a spreadsheet or JSONL file | Medium | Low | Medium | 5 | ✅ Keep |
| ↳↳ GD-3: Save a public web page as a source | Medium | Medium | Medium | 5 | ✅ Keep |
| ↳↳ GD-4: Upload a document as a source | Low | Medium | Low | 3 | ✅ Keep (depends on Open Question 2) |
| ↳ GD-5: Write items from a source | Low | Low | Medium | 3 | ✅ Keep |
| ↳ Clean and review data | High | Medium | High | 13 | ✂️ Split by workflow step → GD-6, GD-7 |
| ↳↳ GD-6: Find duplicates and incomplete items | Medium | Medium | Medium | 5 | ✅ Keep (rises to 8 if "same meaning" duplicates are wanted, see Open Question 5) |
| ↳↳ GD-7: Approve or reject each item | Medium | Low | Medium | 5 | ✅ Keep |
| ↳ GD-8: Export approved items as a versioned golden dataset | Medium | Low | Medium | 5 | ✅ Keep |
| ↳ GD-9: Warn when evaluation and training data overlap | Low | Medium | Low | 3 | ✅ Keep (depends on Open Question 6) |

## Ticket Structure

```
Epic: Golden Dataset Builder  (total: 37 points)
├── GD-1: Create a dataset and browse its items           (3 pts, Must,   depends on: —)
├── GD-2: Import items from a spreadsheet or JSONL file   (5 pts, Must,   depends on: GD-1)
├── GD-3: Save a public web page as a source              (5 pts, Must,   depends on: GD-1)
├── GD-4: Upload a document as a source                   (3 pts, Should, depends on: GD-1)
├── GD-5: Write items from a source                       (3 pts, Must,   depends on: GD-3 or GD-4)
├── GD-6: Find duplicates and incomplete items            (5 pts, Must,   depends on: GD-1)
├── GD-7: Approve or reject each item                     (5 pts, Must,   depends on: GD-1)
├── GD-8: Export approved items as a versioned dataset    (5 pts, Must,   depends on: GD-7)
└── GD-9: Warn when evaluation and training data overlap  (3 pts, Should, depends on: GD-1, GD-7)
```

**Smallest useful first release (18 pts):** GD-1 → GD-2 → GD-7 → GD-8. With these four stories you can import your own rows, approve them and export a golden dataset. Web collection and cleaning come next.

---

## GD-1 Create a dataset and browse its items

**Summary:** Create a named dataset and browse its items by status
**Type:** Story | **Epic:** Golden Dataset Builder | **Priority:** Must | **Labels:** dataset, setup | **Components:** Datasets
**Story points (suggested):** 3 — Complexity L, Uncertainty L, Effort M — simple create/list/rename/delete screens; this is the base for every other story

### User Story
As an **AI engineer**, I want **to create a dataset for one purpose and see all its items in one place**, so that **I keep each golden dataset separate and always know how far along it is**.

### Background
Today the data sits in loose spreadsheets and copied text, so it is hard to tell what is checked and what is not. Every other story adds items to, or works on, a dataset.

### Acceptance Criteria
**AC1 — Create a dataset**
Given I am on the datasets page
When I enter the name "Customer-support eval v1", choose the purpose **Evaluation** (or **Training**), and click Create
Then the dataset appears in the list with its purpose, 0 items and the created date

**AC2 — Name rules**
Given I am creating or renaming a dataset
When the name is empty, longer than 100 characters, or the same as an existing dataset's name (ignoring upper/lower case)
Then I see "Enter a name (1–100 characters)" or "A dataset with this name already exists", and nothing is saved

**AC3 — See items and progress**
Given a dataset has items
When I open it
Then I see a table of items (input and expected output shortened to one line, source, status) and counts at the top: Draft, Approved, Rejected, Total

**AC4 — Empty state**
Given a dataset has no items
When I open it
Then I see "No items yet. Import a file or add a web page." with buttons for both

**AC5 — Filter and search**
Given a dataset has items in different statuses
When I filter by status or type text into the search box
Then only items that match the status and contain the text (in input or expected output) are shown

**AC6 — Data is kept**
Given I created datasets and items
When I close the app and open it again
Then all datasets, items and statuses are exactly as I left them

**AC7 — Delete needs confirmation**
Given I choose Delete on a dataset
When the confirmation asks me to type the dataset's name
Then the dataset and all its items are deleted only after I type the exact name and confirm; Cancel changes nothing

### Developer Notes
- **Context:** this is a new app, not part of the chatbot. The stack is a dev decision; reusing the Python/FastAPI setup from this repo is an option *(assumption)*.
- **Data:** single user, local, so a small embedded database is enough (dev decision). Store dates in UTC and show them in local time.
- **Statuses:** Draft (default), Approved and Rejected. "Incomplete" is a flag on a Draft item (from GD-2/GD-6), not a separate status.
- **Purpose** (Evaluation/Training) is used later by GD-9. It cannot be changed after items exist *(assumption)*, so an evaluation set can't quietly become training data.
- **Performance:** the item list should stay usable at 10,000+ items, so page it (dev decision on page size).
- **Testing hints:** seed one dataset per status mix, plus one empty dataset.

### Out of Scope
- Multiple users, logins and sharing
- Copying or merging datasets
- Undoing a delete (no trash bin)

### Dependencies
- None. This is the first story.

### Open Questions
- [ ] Will the app run only on your own computer, or must it be reachable from the internet? (If it's on the internet, a login story is needed.) (@PO)

---

## GD-2 Import items from a spreadsheet or JSONL file

**Summary:** Import dataset items from my own CSV, Excel or JSONL file
**Type:** Story | **Epic:** Golden Dataset Builder | **Priority:** Must | **Labels:** import, data-collection | **Components:** Import
**Story points (suggested):** 5 — Complexity M, Uncertainty L, Effort M — three file types, column mapping, preview and error summary

### User Story
As an **AI engineer**, I want **to import rows from my own files and choose which column is the input and which is the expected output**, so that **I can bring existing data into review without retyping it**.

### Background
The engineer already has data in spreadsheets, exported chat logs and JSONL files. Today it is cleaned by hand in Excel, and nothing records which rows were checked.

### Acceptance Criteria
**AC1 — Preview and map columns**
Given I open a dataset and choose Import file
When I upload a CSV, Excel (.xlsx) or JSONL file
Then I see the first 10 rows and pick which column is **Input**, which is **Expected output**, and which other columns to keep as extra fields

**AC2 — Suggested mapping**
Given the file has columns named like `question`/`prompt`/`input` and `answer`/`response`/`output`
When the preview opens
Then those columns are already selected as Input and Expected output; I can change them *(assumption)*

**AC3 — Import creates Draft items with their origin**
Given I confirm the mapping
When the import finishes
Then each row becomes one Draft item whose source shows the file name and row number (e.g. "support_logs.csv, row 42"), and I see "Imported 950 items"

**AC4 — Rows with missing parts**
Given some rows have an empty input or an empty expected output
When I import
Then those rows are imported but flagged **Incomplete**, and the summary says "12 items are incomplete" with a link to filter them. Rows where every mapped column is empty are skipped and counted as "skipped".

**AC5 — Unsupported or broken file**
Given I upload a file that is not CSV, .xlsx or JSONL, or a JSONL file with a broken line
When the upload is checked
Then I see "This file type isn't supported. Use CSV, Excel (.xlsx) or JSONL." or "Line 12 is not valid. Fix it and try again.", and **nothing** is imported

**AC6 — File too large**
Given the file is larger than the size limit (50 MB *(assumption: dev to confirm)*)
When I upload it
Then I see "This file is too large (max 50 MB)" and nothing is imported

**AC7 — Text is kept exactly**
Given a cell contains accented or non-Latin text (e.g. "Xin chào, bạn khỏe không?"), line breaks or emoji
When it is imported
Then the item shows exactly the same characters

**AC8 — Cancel**
Given I am on the preview
When I click Cancel
Then no items are created

### Developer Notes
- **Context:** one row = one item. Extra columns are kept so nothing from the original data is lost.
- **Edge cases:** CSV encoding (UTF-8 with or without BOM; dev decision whether to support others), commas and line breaks inside quoted cells, Excel files with several sheets (let the user pick the sheet, or use the first one; dev decision), and an empty file ("This file has no rows").
- **All-or-nothing:** a broken file imports nothing, so a dataset is never left half-imported *(assumption)*.
- **Performance:** a 100,000-row file should import without freezing the screen. Show progress (dev decision).
- **Security:** treat file contents as plain text. Never run formulas or macros from Excel files.
- **Testing hints:** sample files: clean CSV, CSV with a missing-answer row, .xlsx with 2 sheets, JSONL with one broken line, Vietnamese text, a file over the size limit.

### Out of Scope
- Documents such as PDF or Word (GD-4)
- Importing straight from databases, Google Sheets or APIs
- Re-importing a file to update items that already exist

### Dependencies
- GD-1

### Open Questions
- [ ] Are your own files spreadsheets with ready-made rows, documents you read and write items from, or both? (@PO)
- [ ] Do your files contain customer personal data (names, emails, phone numbers)? (@PO)

---

## GD-3 Save a public web page as a source

**Summary:** Save the readable text of a public web page as a source
**Type:** Story | **Epic:** Golden Dataset Builder | **Priority:** Must | **Labels:** web, data-collection | **Components:** Sources
**Story points (suggested):** 5 — Complexity M, Uncertainty M, Effort M — page fetching and text extraction vary from site to site, and there are several failure cases

### User Story
As an **AI engineer** researching a topic, I want **to paste a web page link and save its readable text, with where and when I got it**, so that **I can write dataset items from it later and prove where each fact came from**.

### Background
Today research means copying text from the browser into documents and losing the link. A saved source keeps the text, the link and the date together, and GD-5 turns it into items.

### Acceptance Criteria
**AC1 — Collect a page**
Given I open a dataset and choose Add web page
When I paste a public link (e.g. `https://en.wikipedia.org/wiki/Large_language_model`) and click Fetch
Then I see a preview with the page title, the link, and the main readable text, without menus, ads or footers

**AC2 — Edit before saving**
Given the preview is shown
When I delete parts of the text I don't need and click Save
Then the source is saved with my edited text, the title, the link and today's date, and appears in the dataset's Sources list

**AC3 — Bad link**
Given I enter text that is not a full web address (e.g. `wikipedia`) or uses something other than http/https
When I click Fetch
Then I see "Enter a full web address starting with http:// or https://"

**AC4 — Page can't be opened**
Given the page does not exist, the site doesn't respond in time, or the server returns an error
When I click Fetch
Then I see "Couldn't open this page: [not found / site didn't respond / site error]. Nothing was saved."

**AC5 — Login or blocked pages are not collected**
Given the page needs a login, or the site blocks automated access
When I click Fetch
Then I see "This page needs a login or blocks automated access, so it can't be collected", and the app does not try to get around it

**AC6 — No readable text**
Given the page has no readable text (e.g. only images or video)
When I click Fetch
Then I see "No readable text found on this page" and nothing is saved

**AC7 — Same page twice**
Given I already saved this link in this dataset
When I fetch it again
Then I see "You saved this page on 2026-11-05. Save it again as a new copy?" and can choose Save copy or Cancel

**AC8 — Private addresses are refused**
Given I enter an address on my own machine or local network (e.g. `http://localhost`, `http://192.168.1.10`)
When I click Fetch
Then I see "This address can't be collected" and no request is made

### Developer Notes
- **Context:** a source is raw research material, not a dataset item. Items are written from it in GD-5.
- **Dev decisions:** the text-extraction approach, the fetch timeout (around 15 s is a sensible default), the maximum page size, and the user agent. Pages that build their content with JavaScript may come back empty; handle that case with AC6 and note it for a later spike if it turns out to be common.
- **Security:** AC8 protects against the fetcher being used to reach local or internal services (SSRF). Check the address again after redirects. Treat page content as text only: never run its scripts or show raw HTML.
- **Respecting sites:** don't bypass logins, paywalls or CAPTCHAs. Whether to also honour robots.txt is Open Question 7.
- **Data:** store the link, final link after redirects, title, collected date (UTC) and the edited text.
- **Testing hints:** use a local test page for the happy path, plus a 404 link, a slow server, a login page, an image-only page and a private-address link.

### Out of Scope
- Crawling several pages or a whole site from one link
- Searching the web from inside the app
- PDFs or other files found at a link (only HTML pages for now)
- Re-checking a saved page later for changes

### Dependencies
- GD-1

### Open Questions
- [ ] Should the app skip sites that ask automated tools not to collect them, even if the page is public? (@PO)

---

## GD-4 Upload a document as a source

**Summary:** Upload a PDF, Word or text document and save its text as a source
**Type:** Story | **Epic:** Golden Dataset Builder | **Priority:** Should | **Labels:** import, data-collection | **Components:** Sources
**Story points (suggested):** 3 — Complexity L, Uncertainty M, Effort L — reuses the source preview from GD-3; text quality from PDFs varies

### User Story
As an **AI engineer**, I want **to upload my own documents and save their text as sources**, so that **I can write dataset items from internal material, not only from the web**.

### Background
Internal guides, policies and reports are often the best ground truth for an evaluation set, but they arrive as PDF or Word files rather than ready-made rows.

### Acceptance Criteria
**AC1 — Upload a document**
Given I open a dataset and choose Upload document
When I upload a .pdf, .docx or .txt file
Then I see a preview with the file name and its text, can edit it, and on Save it appears in the Sources list with the file name and today's date

**AC2 — Scanned PDF**
Given the PDF contains only scanned images and no text
When I upload it
Then I see "No text found. This looks like a scanned document, which isn't supported yet." and nothing is saved

**AC3 — Wrong type or too large**
Given the file is another type, or larger than the size limit (50 MB *(assumption)*)
When I upload it
Then I see "Use a PDF, Word (.docx) or text file up to 50 MB" and nothing is saved

**AC4 — Protected document**
Given the PDF is password-protected
When I upload it
Then I see "This document is password-protected. Remove the password and try again."

**AC5 — Text is kept exactly**
Given the document contains accented or non-Latin text
When it is saved
Then the source text shows the same characters

### Developer Notes
- **Context:** only build this if Open Question 2 confirms that you read documents as well as using ready-made rows.
- **Affected areas (likely):** the same Source model and preview screen as GD-3. Store the file name instead of a link.
- **Dev decisions:** the extraction libraries, and whether to keep the original file or only its text (only the text is enough for traceability *(assumption)*).
- **Testing hints:** a text PDF, a scanned PDF, a password-protected PDF, a .docx with a table, a Vietnamese .txt file.

### Out of Scope
- Reading text from scanned images (OCR)
- Keeping layout, tables or images from the document
- Old .doc files and other formats

### Dependencies
- GD-1. Shares its preview screen with GD-3.

### Open Questions
- [ ] Same as GD-2: do you need documents at all, or only ready-made rows? (@PO)

---

## GD-5 Write items from a source

**Summary:** Write dataset items next to a source's text, linked to that source
**Type:** Story | **Epic:** Golden Dataset Builder | **Priority:** Must | **Labels:** editing | **Components:** Items
**Story points (suggested):** 3 — Complexity L, Uncertainty L, Effort M — a two-panel editor with add/edit/delete; no new rules

### User Story
As an **AI engineer**, I want **to read a source and write items next to it**, so that **every item is based on real material and can be traced back to it**.

### Background
Web pages and documents (GD-3, GD-4) are raw text. This story turns them into the input + expected output items that make up the dataset.

### Acceptance Criteria
**AC1 — Side by side**
Given I open a saved source
When I click Add item
Then I see the source text on one side and an item form (Input, Expected output, extra fields) on the other

**AC2 — Copy from the source**
Given I select a passage in the source text
When I choose "Use as input" or "Use as expected output"
Then the selected text is placed in that field, and I can still edit it

**AC3 — Save an item**
Given I filled in Input and Expected output
When I click Save
Then a Draft item is created, linked to the source, and the source shows how many items were made from it (e.g. "3 items")

**AC4 — Save with a missing part**
Given I filled in only one of Input or Expected output
When I click Save
Then the item is saved as Draft and flagged **Incomplete**. If both are empty, I see "Enter an input or an expected output" and nothing is saved.

**AC5 — Edit and delete items**
Given an item exists
When I edit it and save, or choose Delete and confirm
Then the change is shown in the item list straight away; Cancel on delete changes nothing

**AC6 — Add an item without a source**
Given I am in a dataset
When I choose Add item manually
Then I can create an item with the source shown as "Written by hand"

### Developer Notes
- **Context:** the source link is what makes an item traceable ("where did this expected answer come from?"). Deleting a source should keep its items and show "Source deleted" *(assumption)*.
- **Editing an Approved item** follows the GD-7 rule: it goes back to Draft.
- **Edge cases:** very long sources (keep the panel scrollable), and selecting text across paragraphs.
- **Testing hints:** one web source and one hand-written item; check the item count on the source.

### Out of Scope
- AI suggesting items from a source (not chosen for now)
- Multi-turn conversations as one item (see Open Question 1)
- Bulk editing many items at once

### Dependencies
- GD-1; GD-3 or GD-4 for sources (manual items work without them)

### Open Questions
- [ ] Is every item an input plus its ideal answer, or do you also need other shapes, such as a text with a label, or a whole multi-turn conversation? (@PO)

---

## GD-6 Find duplicates and incomplete items

**Summary:** Check a dataset for duplicates and incomplete items and fix them
**Type:** Story | **Epic:** Golden Dataset Builder | **Priority:** Must | **Labels:** data-quality | **Components:** Cleaning
**Story points (suggested):** 5 — Complexity M, Uncertainty M, Effort M — several checks with bulk fixes; the definition of "duplicate" is still open

### User Story
As an **AI engineer**, I want **the app to find duplicate and incomplete items for me**, so that **my golden dataset has no repeated or broken examples that would skew evaluation scores or training**.

### Background
Duplicates make some cases count twice in evaluation scores and over-train the model on them. Incomplete items can't be used at all. Today these are found by eye in a spreadsheet.

### Acceptance Criteria
**AC1 — Run a check**
Given a dataset has items
When I click Check quality
Then I see a summary: "8 duplicate groups (19 items), 12 incomplete items, 30 items with extra spaces", each with a link to the affected items

**AC2 — What counts as a duplicate**
Given two items whose inputs differ only in upper/lower case, spaces or line breaks (e.g. "What is RAG?" and "what is  rag?")
When the check runs
Then they are listed together in one duplicate group

**AC3 — Resolve a duplicate group**
Given a duplicate group is shown
When I pick the item to keep and click Resolve
Then the other items in the group are marked **Rejected** with the reason "Duplicate", and the kept item is unchanged

**AC4 — Same input, different answers**
Given two items have the same input but different expected outputs
When the check runs
Then the group is labelled "Same input, different answers" so I decide which answer is right; nothing is changed automatically

**AC5 — Incomplete items**
Given some items have an empty input or expected output
When the check runs
Then they are listed as incomplete, and opening one lets me fill in the missing part, which removes the flag when saved

**AC6 — Tidy spaces**
Given items have spaces at the start or end, or repeated blank lines
When I click Tidy spaces and confirm
Then that whitespace is removed from those items only, and I see "Tidied 30 items"

**AC7 — Clean dataset**
Given no problems are found
When the check finishes
Then I see "No problems found"

### Developer Notes
- **Context:** never delete anything automatically. Resolving marks items Rejected, so they can still be restored by changing their status.
- **Business rule:** compare inputs after making them lower case, trimming them and collapsing repeated spaces/line breaks. Leave accents as they are ("chào" ≠ "chao") *(assumption)*.
- **Rejected and Approved items:** include them in the check, so a new Draft that duplicates an Approved item is caught.
- **Scope risk:** finding items that mean the same thing in different words is a larger feature (a similarity model plus a threshold). If the PO wants it, make it a separate story after a spike; this story would rise to 8 if it were included.
- **Performance:** the check should finish in a few seconds on 10,000 items (dev to tune).

### Out of Scope
- Finding items that mean the same thing but are worded differently (unless Open Question 5 says yes, then it becomes a new story)
- Spelling or grammar fixes
- Detecting personal data (see Open Question 4)

### Dependencies
- GD-1. Uses the Rejected status and reasons from GD-7.

### Open Questions
- [ ] Should "duplicate" also cover items that mean the same thing but are worded differently? (This adds noticeable work.) (@PO)

---

## GD-7 Approve or reject each item

**Summary:** Review Draft items one by one and approve or reject each with a reason
**Type:** Story | **Epic:** Golden Dataset Builder | **Priority:** Must | **Labels:** review | **Components:** Review
**Story points (suggested):** 5 — Complexity M, Uncertainty L, Effort M — review queue, status rules, reasons and keyboard shortcuts

### User Story
As an **AI engineer** acting as reviewer, I want **to go through Draft items one at a time and approve, fix or reject each one**, so that **only items I have personally checked become part of the golden dataset**.

### Background
Approval is what makes the data "golden". There is one reviewer: the engineer. The review must be fast enough to get through thousands of items.

### Acceptance Criteria
**AC1 — Review queue**
Given a dataset has Draft items
When I click Start review
Then I see one item at a time (input, expected output, extra fields, source link) and progress such as "120 of 500 reviewed"

**AC2 — Approve**
Given I'm reviewing a complete item
When I click Approve (or press **A**)
Then the item becomes **Approved** and the next Draft item is shown

**AC3 — Reject with a reason**
Given I'm reviewing an item
When I click Reject (or press **R**)
Then I must choose a reason: Wrong answer, Unclear question, Duplicate, Off-topic, or Other (with a note). The item becomes **Rejected** with that reason, and the next item is shown.

**AC4 — Fix, then approve**
Given the expected output has a mistake
When I edit it in the review screen and click Save & approve
Then the item is saved with my edit and becomes **Approved**

**AC5 — Incomplete items can't be approved**
Given the item is flagged Incomplete
When I try to approve it
Then I see "Fill in both input and expected output before approving", and the status stays Draft

**AC6 — Editing an approved item sends it back**
Given an item is Approved
When I change its input or expected output anywhere in the app
Then it goes back to **Draft**, and I see "Edited items go back to review"

**AC7 — Change my mind**
Given an item is Approved or Rejected
When I open it and choose Move back to Draft
Then it returns to the review queue

**AC8 — Queue finished**
Given there are no Draft items left
When I finish the last one
Then I see "All items reviewed: 430 approved, 70 rejected" with a button to export (GD-8)

### Developer Notes
- **Context:** AC6 is the key rule. Nothing can reach the export unless it was approved in its final form.
- **Data:** store the status, the reason, the note and when the status changed. A short change history per item is useful for traceability (dev decision on how much to keep).
- **Keyboard:** A / R shortcuts only work when the focus is not inside a text field.
- **Testing hints:** a dataset with complete, incomplete and already-approved items; check that the progress count matches the GD-1 counts.

### Out of Scope
- A second reviewer or reviewers having to agree (not needed: single user)
- Approving many items at once without looking at them
- Review statistics over time

### Dependencies
- GD-1

### Open Questions
- [ ] When an approved item is edited, should it go back to review (as written), or stay approved? (@PO)
- [ ] Should rejected items be kept with their reason (as written), or deleted? (@PO)

---

## GD-8 Export approved items as a versioned golden dataset

**Summary:** Export only approved items as a numbered, downloadable dataset version
**Type:** Story | **Epic:** Golden Dataset Builder | **Priority:** Must | **Labels:** export | **Components:** Export
**Story points (suggested):** 5 — Complexity M, Uncertainty L, Effort M — file generation, frozen versions and version history

### User Story
As an **AI engineer**, I want **to export the approved items as a numbered version I can download again later**, so that **I can run evaluations or training on an exact, unchanging dataset and repeat them**.

### Background
Evaluation results only mean something if you know exactly which data produced them. Each export is a frozen snapshot (v1, v2…), so "the model scored 82% on v3" can always be checked.

### Acceptance Criteria
**AC1 — Export approved items only**
Given a dataset has 430 Approved, 50 Draft and 70 Rejected items
When I click Export, add an optional note (e.g. "first full review"), and confirm
Then a new version **v1** is created containing exactly the 430 approved items and none of the others

**AC2 — What each record contains**
Given the export is created
When I open the file
Then each record has the item ID, input, expected output, extra fields, and the source (link or file name and row)

**AC3 — Formats**
Given I export
When I choose a format
Then I can download JSONL or CSV *(assumption: formats are a dev decision; JSONL is the usual default for model tools)*

**AC4 — Versions don't change**
Given v1 exists and I later approve 20 more items and export again
When I look at the version history
Then I see v1 (430 items) and v2 (450 items), each with its date and note, and downloading v1 still gives the original 430 items

**AC5 — Nothing to export**
Given no items are Approved
When I open Export
Then the button is disabled with the message "No approved items to export yet"

**AC6 — Text is kept exactly**
Given items contain accented or non-Latin text, quotes, commas or line breaks
When I export to JSONL or CSV and open the file
Then the text matches the app exactly, and CSV quoting keeps each item on one record

### Developer Notes
- **Context:** a version is a frozen copy. Later edits or deletes in the app must not change it, so store the snapshot rather than a live query.
- **Dev decisions:** the exact field names, UTF-8 encoding, and whether to add a small summary file per version (count, date, note, dataset purpose).
- **Edge cases:** very large exports (stream the file), and dataset names with characters that aren't allowed in file names.
- **Testing hints:** export, edit an approved item (it goes back to Draft, see GD-7), export again, and check that v1 is unchanged and v2 doesn't contain the edited item.

### Out of Scope
- Splitting the data into train/validation/test parts
- Pushing the dataset directly to Hugging Face, cloud storage or training tools
- Deleting old versions

### Dependencies
- GD-7

### Open Questions
- [ ] Should the export also split the data into training and test parts, or is that done outside the app? (@PO)

---

## GD-9 Warn when evaluation and training data overlap

**Summary:** Warn when an evaluation item also appears in a training dataset
**Type:** Story | **Epic:** Golden Dataset Builder | **Priority:** Should | **Labels:** data-quality | **Components:** Cleaning, Export
**Story points (suggested):** 3 — Complexity L, Uncertainty M, Effort L — reuses the GD-6 comparison across datasets; whether to warn or block is still open

### User Story
As an **AI engineer**, I want **to be warned when an item in my evaluation dataset is also in a training dataset**, so that **my evaluation scores aren't inflated by the model having seen the test questions during training**.

### Background
If test questions leak into training data, the model looks better than it really is. This is the most common way a "golden" evaluation set loses its value.

### Acceptance Criteria
**AC1 — Warning on export**
Given an Evaluation dataset has 5 approved items whose input also appears in a Training dataset
When I click Export
Then I see "5 items also appear in training dataset 'Support-train v2'" with a list of them, and can choose to continue or cancel

**AC2 — Shown on the item**
Given an item overlaps with a Training dataset
When I view it in the list or the review screen
Then it shows a label "Also in training: Support-train v2"

**AC3 — No overlap**
Given no inputs match any Training dataset
When I export
Then no warning is shown

**AC4 — Same rules as GD-6**
Given two inputs differ only in upper/lower case or spaces
When overlap is checked
Then they count as the same

### Developer Notes
- **Context:** uses each dataset's purpose (GD-1) and the comparison rule from GD-6.
- **Business rule:** only compare against Approved items in Training datasets *(assumption)*. Drafts there aren't training data yet.
- **Warn or block:** written as a warning; switch it to a block if the PO chooses that in Open Question 6.

### Out of Scope
- Checking against training data outside the app (e.g. public datasets the model was trained on)
- Overlap based on meaning rather than wording

### Dependencies
- GD-1, GD-6 (comparison rule), GD-7

### Open Questions
- [ ] If evaluation items also appear in training data, should the app only warn you (as written), or block the export until they're removed? (@PO)

---

## Open Questions (all stories)

Business questions for the PO (you), numbered so each one can be answered by number:

1. [ ] **Item shape (GD-5):** is every item an input plus its ideal answer, or do you also need other shapes, such as a text with a label, or a whole multi-turn conversation?
2. [ ] **Own files (GD-2, GD-4):** are your files spreadsheets with ready-made rows, documents you read and write items from, or both? (If only rows, GD-4 is dropped.)
3. [ ] **Where it runs (GD-1):** will the app run only on your own computer, or must it be reachable from the internet? (If it's on the internet, a login story is needed.)
4. [ ] **Personal data (GD-2, GD-6):** do your files contain customer names, emails or phone numbers? If yes, should the app warn you about them before items can be approved? (This would be a new story.)
5. [ ] **Duplicates (GD-6):** should "duplicate" also cover items that mean the same thing but are worded differently? (This adds noticeable work.)
6. [ ] **Evaluation vs training (GD-9):** if evaluation items also appear in training data, should the app only warn you, or block the export?
7. [ ] **Web collection (GD-3):** should the app skip sites that ask automated tools not to collect them, even when the page is public?
8. [ ] **Review rules (GD-7):** when an approved item is edited, should it go back to review? Should rejected items be kept with their reason, or deleted?
9. [ ] **Export (GD-8):** should the export also split the data into training and test parts, or is that done outside the app?
