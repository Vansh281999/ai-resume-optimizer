import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ai_career_platform.ai_providers.factory import get_multi_provider


class ResumeIngestionError(RuntimeError):
    pass


class ResumeFileValidationError(ResumeIngestionError):
    pass


class ResumeIngestionPipeline:
    allowed_extensions = {".pdf", ".docx", ".doc", ".txt"}
    allowed_mime_types = {
        ".pdf": {"application/pdf"},
        ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        ".doc": {"application/msword", "application/vnd.ms-word"},
        ".txt": {"text/plain", "text/markdown", "application/octet-stream", ""},
    }

    def __init__(self, providers: Optional[List[str]] = None, model: str = "gemini-2.0-flash", max_text_chars: int = 30000):
        self.model = model
        self.max_text_chars = max_text_chars
        self.provider = get_multi_provider(providers=providers or ["gemini", "openrouter", "ollama"], model=model)
        self.last_extraction_metadata: Dict[str, Any] = {}
        self.system_prompt = (
            "You are an expert resume parser. Extract all information from the resume and return ONLY valid JSON. "
            "Do not include markdown, explanations, or comments. If a field is not present, use an empty string, null, or an empty array.\n\n"
            "Schema:\n"
            "{\n"
            '  "personal_info": {"full_name": "", "email": "", "phone": "", "location": "", "linkedin_url": "", "github_url": "", "portfolio_url": ""},\n'
            '  "headline": "",\n'
            '  "summary": "",\n'
            '  "career_objective": "",\n'
            '  "education": [{"degree": "", "specialization": "", "institution": "", "start_date": "", "end_date": "", "cgpa": "", "description": ""}],\n'
            '  "experience": [{"title": "", "company": "", "location": "", "start_date": "", "end_date": "", "responsibilities": "", "achievements": ""}],\n'
            '  "projects": [{"project_name": "", "description": "", "technologies": "", "github_url": "", "live_url": "", "start_date": "", "end_date": ""}],\n'
            '  "skills": {"programming_languages": [], "frameworks": [], "databases": [], "cloud_technologies": [], "devops_tools": [], "ai_ml_technologies": [], "soft_skills": []},\n'
            '  "certifications": [{"certification_name": "", "issuer": "", "issue_date": "", "expiry_date": "", "credential_url": ""}],\n'
            '  "job_preferences": {"preferred_roles": "", "preferred_locations": "", "work_mode": "", "expected_salary_min": null, "expected_salary_max": null, "years_of_experience": ""}\n'
            "}"
        )

    def validate_file(self, filename: str, content: bytes, content_type: str = "", max_size_bytes: int = 10 * 1024 * 1024) -> str:
        if not filename:
            raise ResumeFileValidationError("No filename was provided.")
        if "\x00" in filename or ".." in filename or filename.replace("\\", "/").startswith("/"):
            raise ResumeFileValidationError("Unsafe filename rejected.")
        if not content:
            raise ResumeFileValidationError("Uploaded file is empty.")
        if len(content) > max_size_bytes:
            raise ResumeFileValidationError(f"File exceeds max size of {max_size_bytes // (1024 * 1024)} MB.")
        ext = Path(filename).suffix.lower()
        if ext not in self.allowed_extensions:
            raise ResumeFileValidationError(f"Unsupported file type: {ext or 'no extension'}. Upload PDF, DOCX, DOC, or TXT.")
        detected = self._detect_mime_type(content, ext)
        expected = self.allowed_mime_types.get(ext, set())
        submitted = (content_type or "").split(";")[0].strip().lower()
        if submitted and submitted not in expected and detected not in expected:
            raise ResumeFileValidationError(f"File content does not match extension {ext}. Upload a valid {ext.upper()} file.")
        return ext

    def ingest(self, content: bytes, filename: str, content_type: str = "", max_size_bytes: int = 10 * 1024 * 1024) -> Dict[str, Any]:
        ext = self.validate_file(filename, content, content_type, max_size_bytes)
        raw_text = self.extract_text(content, filename)
        cleaned_text = self.clean_text(raw_text)
        if not cleaned_text:
            raise ResumeIngestionError("Could not extract readable text from the uploaded resume. For scanned PDFs, enable OCR or upload a text-based resume.")
        parsed, parser_warning = self._parse_or_fallback(cleaned_text)
        metadata = {
            "filename": Path(filename).name,
            "extension": ext,
            "text_chars": len(cleaned_text),
            "parser_model": self.model,
            "parser_warning": parser_warning,
            **self.last_extraction_metadata,
        }
        return {
            "raw_text": cleaned_text,
            "structured_resume": parsed,
            "parsed": parsed,
            "metadata": metadata,
        }

    def extract_text(self, content: bytes, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        self.last_extraction_metadata = {"extraction_method": suffix.lstrip(".") or "unknown"}
        if suffix == ".pdf":
            return self._extract_pdf(content)
        if suffix == ".docx":
            return self._extract_docx(content)
        if suffix == ".txt":
            return self._extract_txt(content)
        if suffix == ".doc":
            raise ResumeIngestionError("Legacy .doc files are accepted but cannot be parsed reliably by this server. Convert the resume to DOCX, PDF, or TXT and upload again.")
        raise ResumeIngestionError(f"Unsupported file type: {suffix or 'no extension'}. Upload PDF, DOCX, DOC, or TXT.")

    def clean_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        lines = [line for line in lines if line]
        cleaned = []
        previous_blank = False
        for line in lines:
            if not line:
                if not previous_blank:
                    cleaned.append("")
                previous_blank = True
            else:
                cleaned.append(line)
                previous_blank = False
        return "\n".join(cleaned).strip()[: self.max_text_chars]

    def _parse_or_fallback(self, cleaned_text: str) -> Tuple[Dict[str, Any], str]:
        try:
            return self.parse(cleaned_text), ""
        except ResumeIngestionError as exc:
            return self._rule_based_extract(cleaned_text, str(exc)), "LLM parsing unavailable; deterministic fallback was used for review."

    def parse(self, resume_text: str) -> Dict[str, Any]:
        prompt = (
            f"{self.system_prompt}\n\n"
            "Resume text:\n"
            "--------------------\n"
            f"{resume_text}\n"
            "--------------------\n"
            "Return ONLY the JSON object matching the schema."
        )
        try:
            raw = self.provider.generate(
                [{"role": "user", "content": prompt}],
                timeout=120,
                retries=1,
            )
            data = self._extract_json(raw)
            return self._normalize(data)
        except Exception as exc:
            raise ResumeIngestionError("Resume parser service temporarily unavailable. Please try again later.") from exc

    def _extract_pdf(self, content: bytes) -> str:
        errors = []
        extractors = [
            ("pdfplumber", self._extract_pdf_pdfplumber),
            ("pymupdf", self._extract_pdf_pymupdf),
            ("pypdf", self._extract_pdf_pypdf),
        ]
        for name, extractor in extractors:
            try:
                text = extractor(content)
                if text and text.strip():
                    self.last_extraction_metadata = {"extraction_method": name, "ocr_used": False}
                    return text
                errors.append(f"{name}: no text")
            except Exception as exc:
                if self._is_password_error(exc):
                    raise ResumeIngestionError("PDF is password protected. Remove the password and upload again.") from exc
                errors.append(f"{name}: {exc}")
        ocr_text = self._ocr_pdf(content)
        if ocr_text and ocr_text.strip():
            self.last_extraction_metadata = {"extraction_method": "ocr", "ocr_used": True}
            return ocr_text
        raise ResumeIngestionError("PDF extraction failed. Upload a text-based PDF or enable OCR support on the server.")

    def _extract_pdf_pdfplumber(self, content: bytes) -> str:
        import pdfplumber

        with pdfplumber.open(io.BytesIO(content)) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)

    def _extract_pdf_pymupdf(self, content: bytes) -> str:
        import fitz

        with fitz.open(stream=content, filetype="pdf") as doc:
            return "\n".join(page.get_text("text") or "" for page in doc)

    def _extract_pdf_pypdf(self, content: bytes) -> str:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(content))
        return "\n".join((page.extract_text() or "") for page in reader.pages)

    def _ocr_pdf(self, content: bytes) -> str:
        try:
            import fitz
            import pytesseract
            from PIL import Image
        except Exception:
            return ""
        parts = []
        try:
            with fitz.open(stream=content, filetype="pdf") as doc:
                for page in doc[: min(len(doc), 10)]:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    image = Image.open(io.BytesIO(pix.tobytes("png")))
                    text = pytesseract.image_to_string(image)
                    if text and text.strip():
                        parts.append(text)
        except Exception:
            return ""
        return "\n".join(parts)

    def _extract_docx(self, content: bytes) -> str:
        try:
            from docx import Document

            doc = Document(io.BytesIO(content))
            parts = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]
            for section in doc.sections:
                for paragraph in section.header.paragraphs + section.footer.paragraphs:
                    if paragraph.text:
                        parts.append(paragraph.text)
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text for cell in row.cells if cell.text)
                    if row_text:
                        parts.append(row_text)
            return "\n".join(parts)
        except Exception as exc:
            raise ResumeIngestionError("DOCX extraction failed. The file may be corrupted or not a valid DOCX.") from exc

    def _extract_txt(self, content: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp1252"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content.decode("utf-8", errors="ignore")

    def _detect_mime_type(self, content: bytes, ext: str) -> str:
        if ext == ".pdf" and content.startswith(b"%PDF"):
            return "application/pdf"
        if ext == ".docx" and content[:2] == b"PK":
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if ext == ".doc" and content[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            return "application/msword"
        if ext == ".txt":
            try:
                content.decode("utf-8")
                return "text/plain"
            except UnicodeDecodeError:
                return "application/octet-stream"
        return ""

    def _is_password_error(self, exc: Exception) -> bool:
        message = str(exc).lower()
        return "encrypt" in message or "password" in message or "permission" in message

    def _extract_json(self, raw: str) -> Dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("LLM response did not contain a JSON object")
        json_str = text[start : end + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise ValueError("LLM response was not valid JSON") from exc

    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValueError("Parsed output is not a JSON object")
        info = data.get("personal_info") or {}
        if not isinstance(info, dict):
            info = {}
        skills = data.get("skills") or {}
        if isinstance(skills, list):
            skills = {"general": skills}
        if not isinstance(skills, dict):
            skills = {}
        return {
            "personal_info": {
                "full_name": _clean_string(info.get("full_name") or info.get("name")),
                "email": _clean_string(info.get("email")),
                "phone": _clean_string(info.get("phone")),
                "location": _clean_string(info.get("location")),
                "linkedin_url": _clean_url(info.get("linkedin_url") or info.get("linkedin")),
                "github_url": _clean_url(info.get("github_url") or info.get("github")),
                "portfolio_url": _clean_url(info.get("portfolio_url") or info.get("portfolio")),
            },
            "headline": _clean_string(data.get("headline")),
            "summary": _clean_string(data.get("summary")),
            "career_objective": _clean_string(data.get("career_objective")),
            "education": [_normalize_dict(item) for item in _as_list(data.get("education"))],
            "experience": [_normalize_dict(item) for item in _as_list(data.get("experience"))],
            "projects": [_normalize_dict(item) for item in _as_list(data.get("projects"))],
            "skills": {str(key): _as_string_list(value) for key, value in skills.items()},
            "certifications": [_normalize_dict(item) for item in _as_list(data.get("certifications"))],
            "job_preferences": _normalize_dict(data.get("job_preferences") or {}),
        }

    def _rule_based_extract(self, text: str, warning: str) -> Dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        full_text = "\n".join(lines)
        email = _first_match(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", full_text)
        phone = _first_match(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}", full_text)
        linkedin = _first_match(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+/?", full_text)
        github = _first_match(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_.-]+/?", full_text)
        full_name = _first_match(r"(?:full\s*name|name)\s*:\s*(.+)", full_text, flags=re.IGNORECASE) or (lines[0] if lines else "")
        headline = _first_match(r"(?:headline|title|professional\s*title)\s*:\s*(.+)", full_text, flags=re.IGNORECASE) or (lines[1] if len(lines) > 1 and not lines[1].lower().startswith(("email", "phone", "skills")) else "")
        summary_lines = [line for line in lines if not re.match(r"^(name|full name|email|phone|location|skills)\s*:", line, flags=re.IGNORECASE)]
        summary_lines = [line for line in summary_lines if line not in {full_name, headline}][:8]
        skills = self._extract_skill_lines(lines)
        return self._normalize({
            "personal_info": {
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "location": "",
                "linkedin": linkedin,
                "github": github,
            },
            "headline": headline,
            "summary": " ".join(summary_lines)[:1200],
            "skills": skills,
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "job_preferences": {},
        }) | {"parser_warning": warning}

    def _extract_skill_lines(self, lines: List[str]) -> Dict[str, List[str]]:
        skills: Dict[str, List[str]] = {"general": []}
        for line in lines:
            lowered = line.lower()
            if lowered.startswith("skills") or "skills:" in lowered:
                raw = line.split(":", 1)[-1]
                skills["general"] = _as_string_list(raw)
                break
        return skills


class ResumeParser:
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.pipeline = ResumeIngestionPipeline(model=model)

    def parse(self, resume_text: str) -> Dict[str, Any]:
        return self.pipeline.parse(resume_text)


def _clean_string(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()[:2000]


def _clean_url(value: Any) -> str:
    text = _clean_string(value)
    if not text:
        return ""
    if not re.match(r"^https?://", text, flags=re.IGNORECASE):
        return f"https://{text}"
    return text


def _first_match(pattern: str, text: str, flags: int = 0) -> str:
    match = re.search(pattern, text, flags=flags)
    return match.group(1) if match and match.lastindex else (match.group(0) if match else "")


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _as_string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in re.split(r"[,;\n]", value) if item.strip()]
    if isinstance(value, list):
        return [_clean_string(item) for item in value if _clean_string(item)]
    return [_clean_string(value)] if _clean_string(value) else []


def _normalize_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return {str(key): _clean_string(val) for key, val in value.items()}
    return {}
