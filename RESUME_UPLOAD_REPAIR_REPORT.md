# RESUME_UPLOAD_REPAIR_REPORT

## Bugs found

- Frontend routing used `BrowserRouter` with a GitHub Pages project path, causing reloads to duplicate `/ai-resume-optimizer/` in the URL.
- The previous GitHub Pages `404.html` redirect prepended `/ai-resume-optimizer/` even when the path already contained it.
- Resume upload parsing used a single PDF parser path and returned generic failures for extraction/parser issues.
- `.doc` was advertised inconsistently even though the server could not reliably parse legacy binary Word files.
- Multipart upload errors could surface raw provider errors, including sensitive provider URLs.
- Upload validation was split across frontend/backend and did not consistently validate extension, MIME, size, empty files, or unsafe filenames.
- Profile resume parsing stored parsed JSON but did not consistently return raw extracted text plus structured resume metadata.

## Fixes applied

- Switched frontend routing to `HashRouter` with `/ai-resume-optimizer` basename.
- Replaced the GitHub Pages fallback with a hash-route redirect that strips duplicate repo path segments.
- Added `ResumeDropzone` for drag/drop upload, file preview, and processing state.
- Added robust backend validation for filename safety, empty files, extension, MIME/content sniffing, and 10MB size limit.
- Rebuilt resume ingestion as a pipeline:
  - validation
  - PDF/DOCX/TXT extraction
  - text cleaning
  - LLM parsing
  - deterministic fallback structured extraction for review when LLM parsing is unavailable
  - metadata response
- Added PDF parser fallback chain:
  - primary `pdfplumber`
  - secondary `PyMuPDF`
  - tertiary `pypdf`
- Added optional OCR path for scanned PDFs using `pytesseract` when available.
- Added DOCX paragraph/table/header/footer extraction.
- Added TXT encoding fallback for UTF-8, UTF-16, and Windows encodings.
- Added structured resume schema normalization for profile, education, experience, projects, skills, certifications, and preferences.
- Added comparison changes for added skills, new projects, education updates, and profile field updates.
- Added resume ingestion tests.

## Parsers and extraction stack

- PDF: `pdfplumber`, `PyMuPDF`, `pypdf`
- DOCX: `python-docx`
- TXT: built-in decoding fallback
- OCR: `pytesseract` + `PyMuPDF` + `Pillow` when the server has OCR binaries available
- LLM: `get_multi_provider()` with Gemini/OpenRouter/Ollama fallback order

## Supported formats

- `.pdf`
- `.docx`
- `.doc` accepted for validation, but legacy `.doc` returns a user-friendly conversion error because reliable binary DOC parsing requires external conversion tools.
- `.txt`

Rejected:
- empty files
- unsafe filenames
- oversized files
- unsupported extensions such as `.exe`, `.js`, `.php`, `.zip`, `.rar`
- files whose content does not match the declared extension

## Test results

Passed:

```bash
python -m pytest tests/test_resume_ingestion.py -v
python -m py_compile src/api/server.py src/ai_career_platform/services/resume_parser.py src/ai_career_platform/ai_providers/factory.py
npm run typecheck
npm run build
```

Targeted resume ingestion tests passed:

- unsupported extension rejection
- empty file rejection
- UTF-16 TXT extraction
- sample PDF extraction
- corrupted PDF friendly error
- structured fallback extraction

Full backend test suite was not run successfully in this environment because existing local dependencies are incomplete (`psycopg2` missing), unrelated to this resume pipeline change.

## Extraction accuracy notes

- Text-based PDFs and DOCX files extract reliably through the parser chain.
- Scanned PDFs require server-side OCR binaries. The code attempts OCR when available and returns a clear message when OCR is unavailable.
- LLM parsing is preferred for structured extraction. If all LLM providers fail, the backend returns a deterministic fallback structure so the user can review/edit before saving instead of seeing a blank failure.

## Remaining operational notes

- Set Render environment variables for the desired LLM providers: `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, or local `OLLAMA_BASE_URL`.
- If scanned PDF OCR is required on Render, install/provision Tesseract or use EasyOCR-compatible infrastructure.
- Actual binary file storage/file URLs are not implemented yet; `storage_path` currently stores the sanitized original filename. Object storage integration is the next backend storage improvement.
