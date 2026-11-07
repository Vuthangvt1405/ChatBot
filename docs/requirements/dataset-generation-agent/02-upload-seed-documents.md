# Story 2: Upload and extract seed documents for dataset generation

[← Back to Epic Overview](./README.md)

**Summary:** Upload and extract seed documents for dataset generation  
**Type:** Story | **Epic:** AI-Assisted Dataset Generation & Curation Platform | **Priority:** High | **Labels:** `file-upload`, `document-parser`, `ingestion` | **Components:** `Storage-Service`, `Parser-Worker`  
**Story points (suggested):** 5 — Complexity [Medium], Uncertainty [Low], Effort [Medium] — File upload handling, format validation, and text extraction pipeline.

---

### User Story
As an **AI Engineer**, I want **to upload reference documents (PDF, TXT, Markdown, CSV) to my dataset job**, so that **the generation agent can ground synthetic examples in our proprietary domain data**.

### Background
Generative models produce generic outputs without domain context. Enabling engineers to upload internal documentation, manuals, API guides, or sample logs grounds synthetic training and evaluation data in actual company material.

### Acceptance Criteria

**AC1 — Upload supported file types**  
Given a dataset job in `DRAFT` status  
When the AI Engineer uploads files with extensions `.pdf`, `.txt`, `.md`, or `.csv` under 25 MB per file  
Then the system securely stores the files, displays them in the job's "Seed Files" list, and initiates background text extraction.

**AC2 — Rejection of unsupported formats or oversized files**  
Given the file upload dialog  
When a user uploads a file exceeding 25 MB or an unsupported format (e.g., `.exe`, `.zip`, `.png`)  
Then the system rejects the file immediately with message: `"Unsupported file format or size exceeds 25 MB limit. Please upload PDF, TXT, Markdown, or CSV."`

**AC3 — File count ceiling per job**  
Given a dataset job already has 5 uploaded seed files  
When the user attempts to upload an additional file  
Then the system disables further uploads and displays: `"Maximum limit of 5 seed files reached for this job."`

**AC4 — Text extraction status reporting**  
Given seed files have been uploaded  
When text parsing completes  
Then the UI updates each file's badge to `Ready` and displays extracted statistics (character/word count and snippet preview). If extraction fails, it displays `Extraction Failed` with an option to remove or re-upload.

**AC5 — Remove uploaded seed file**  
Given a seed file is attached to a draft job  
When the user clicks "Delete" on the file card  
Then the file and its parsed text are removed from the job and storage repository.

### Developer Notes
- **Context & Intent**: Extracted text chunks feed into the context window of the generation agent in Story 3.
- **Affected Areas**: `SeedFileUploadDropzone`, `DocumentIngestionService`, `TextExtractorWorker`, `FileStorageClient`.
- **Dev Decisions**:
  - Max file size: 25 MB per file, max 5 files per job.
  - Parsers: Standard headless PDF text parser (e.g., `pdf-parse`), CSV parser, and UTF-8 plain text readers.
  - Storage: Store files in an isolated project storage bucket with server-side encryption.
- **Security**: Sanitize original filenames to prevent path traversal; check MIME types against file content headers.

### Out of Scope
- Optical Character Recognition (OCR) for scanned image-only PDFs.
- Live web crawling or scraping URLs.

### Dependencies
- Story 1 (Dataset specification draft).

### Open Questions
- None.
