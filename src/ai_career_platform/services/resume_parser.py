import io
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

from ai_career_platform.ai_providers.factory import get_multi_provider


class ResumeIngestionError(RuntimeError):
    pass


class ResumeFileValidationError(ResumeIngestionError):
    pass


KNOWN_SKILL_CATEGORIES = {
    "programming_languages": {"python", "java", "c++", "c#", "javascript", "typescript", "go", "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab", "perl", "lua", "dart", "objective-c", "sql", "html", "css"},
    "frameworks": {"react", "angular", "vue", "next.js", "nuxt", "svelte", "django", "flask", "fastapi", "spring", "express", "nestjs", "asp.net", ".net", "laravel", "rails", "gatsby", "ember", "backbone", "jquery", "bootstrap", "tailwind", "material-ui", "chakra", "redux", "mobx", "graphql", "rest"},
    "databases": {"postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb", "sqlite", "oracle", "mariadb", "neo4j", "couchdb", "firestore", "supabase", "prisma", "sqlalchemy", "sequelize", "mongoose"},
    "cloud_technologies": {"aws", "azure", "gcp", "google cloud", "heroku", "vercel", "netlify", "digitalocean", "linode", "cloudflare", "docker", "kubernetes", "terraform", "ansible", "jenkins", "circleci", "github actions", "gitlab ci"},
    "devops_tools": {"docker", "kubernetes", "terraform", "ansible", "jenkins", "git", "github", "gitlab", "bitbucket", "ci/cd", "linux", "nginx", "apache", "bash", "powershell", "prometheus", "grafana"},
    "ai_ml_technologies": {"tensorflow", "pytorch", "keras", "scikit-learn", "sklearn", "pandas", "numpy", "opencv", "huggingface", "langchain", "llm", "gpt", "bert", "transformers", "spacy", "nltk", "matplotlib", "seaborn", "plotly", "jupyter", "colab", "machine learning", "deep learning", "nlp", "computer vision"},
    "soft_skills": {"leadership", "communication", "teamwork", "problem solving", "critical thinking", "agile", "scrum", "project management", "time management", "adaptability", "creativity", "collaboration", "mentoring", "public speaking", "negotiation", "stakeholder management"},
}


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
        logger.info("resume_ingest_start filename=%s ext=%s size=%s", filename, ext, len(content))
        raw_text = ""
        cleaned_text = ""
        text_source = "none"
        try:
            raw_text = self.extract_text(content, filename)
            text_source = self.last_extraction_metadata.get("extraction_method", "unknown")
            cleaned_text = self.clean_text(raw_text)
            logger.info("resume_ingest_extracted filename=%s method=%s chars=%s", filename, text_source, len(cleaned_text))
        except Exception as exc:
            logger.error("resume_ingest_extraction_failed filename=%s error=%s", filename, exc, exc_info=True)
            raw_text = content.decode("utf-8", errors="ignore") if content else ""
            cleaned_text = self.clean_text(raw_text)
            text_source = f"raw_fallback_after_error:{type(exc).__name__}"
            logger.info("resume_ingest_raw_fallback filename=%s fallback_chars=%s", filename, len(cleaned_text))

        if not cleaned_text:
            logger.error("resume_ingest_no_text filename=%s ext=%s", filename, ext)
            raise ResumeIngestionError("Could not extract readable text from the uploaded resume. Ensure the file is not a scanned image-only PDF, and try a DOCX or TXT file instead.")

        try:
            parsed, parser_warning = self._parse_or_fallback(cleaned_text)
            logger.info("resume_ingest_parsed filename=%s warning=%s", filename, parser_warning)
        except Exception as exc:
            logger.error("resume_ingest_parse_failed filename=%s error=%s", filename, exc, exc_info=True)
            parsed = self._rule_based_extract(cleaned_text, f"Parsing failed: {exc}")
            parser_warning = "Both LLM and rule-based parsing failed; using minimal extraction."

        metadata = {
            "filename": Path(filename).name,
            "extension": ext,
            "text_chars": len(cleaned_text),
            "parser_model": self.model,
            "parser_warning": parser_warning,
            "extraction_method": text_source,
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
        logger.info("extract_text_start filename=%s suffix=%s", filename, suffix)
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
                logger.info("pdf_extract_try extractor=%s", name)
                text = extractor(content)
                if text and text.strip():
                    logger.info("pdf_extract_success extractor=%s chars=%s", name, len(text))
                    self.last_extraction_metadata = {"extraction_method": name, "ocr_used": False}
                    return text
                logger.warning("pdf_extract_empty extractor=%s", name)
                errors.append(f"{name}: no text")
            except Exception as exc:
                if self._is_password_error(exc):
                    logger.error("pdf_extract_password_protected")
                    raise ResumeIngestionError("PDF is password protected. Remove the password and upload again.") from exc
                logger.warning("pdf_extract_error extractor=%s error=%s", name, exc)
                errors.append(f"{name}: {exc}")
        logger.info("pdf_extract_ocr_fallback errors=%s", errors)
        ocr_text = self._ocr_pdf(content)
        if ocr_text and ocr_text.strip():
            logger.info("pdf_extract_ocr_success chars=%s", len(ocr_text))
            self.last_extraction_metadata = {"extraction_method": "ocr", "ocr_used": True}
            return ocr_text
        logger.error("pdf_extract_all_failed errors=%s", errors)
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
            result = "\n".join(parts)
            logger.info("docx_extract_success chars=%s", len(result))
            return result
        except Exception as exc:
            logger.error("docx_extract_error error=%s", exc, exc_info=True)
            raise ResumeIngestionError("DOCX extraction failed. The file may be corrupted or not a valid DOCX.") from exc

    def _extract_txt(self, content: bytes) -> str:
        for encoding in ("utf-8-sig", "utf-8", "utf-16", "cp1252"):
            try:
                text = content.decode(encoding)
                logger.info("txt_extract_success encoding=%s chars=%s", encoding, len(text))
                return text
            except UnicodeDecodeError:
                continue
        text = content.decode("utf-8", errors="ignore")
        logger.info("txt_extract_fallback chars=%s", len(text))
        return text

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

    # ------------------------------------------------------------------
    # Rule-based fallback extractor (used when LLM is unavailable/fails)
    # ------------------------------------------------------------------
    def _rule_based_extract(self, text: str, warning: str) -> Dict[str, Any]:
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        full_text = "\n".join(lines)

        personal = self._extract_personal_info(lines, full_text)
        education = self._extract_education(lines)
        experience = self._extract_experience(lines)
        projects = self._extract_projects(lines)
        skills_raw = self._extract_skills(lines)
        categorized_skills = self._categorize_skills(skills_raw)
        certifications = self._extract_certifications(lines)

        headline = self._extract_headline(lines, personal)
        summary = self._build_summary(lines)

        return self._normalize({
            "personal_info": personal,
            "headline": headline,
            "summary": summary,
            "career_objective": "",
            "education": education,
            "experience": experience,
            "projects": projects,
            "skills": categorized_skills,
            "certifications": certifications,
            "job_preferences": {},
        }) | {"parser_warning": f"Rule-based extraction used: {warning}"}

    def _extract_personal_info(self, lines: List[str], full_text: str) -> Dict[str, str]:
        info: Dict[str, str] = {
            "full_name": "", "email": "", "phone": "", "location": "",
            "linkedin_url": "", "github_url": "", "portfolio_url": ""
        }
        email_re = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        phone_re = r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}"
        linkedin_re = r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+/?"
        github_re = r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_.-]+/?"

        for line in lines[:5]:
            if not info["email"]:
                m = re.search(email_re, line)
                if m:
                    info["email"] = m.group(0)
            if not info["phone"]:
                m = re.search(phone_re, line)
                if m:
                    info["phone"] = m.group(0)
            if not info["linkedin_url"]:
                m = re.search(linkedin_re, line)
                if m:
                    info["linkedin_url"] = _clean_url(m.group(0))
            if not info["github_url"]:
                m = re.search(github_re, line)
                if m:
                    info["github_url"] = _clean_url(m.group(0))

        # Name: first non-empty line that is not contact info
        for line in lines:
            if not line:
                continue
            if re.search(email_re, line) or re.search(phone_re, line):
                continue
            if "linkedin" in line.lower() or "github" in line.lower():
                continue
            if len(line) < 60 and not any(kw in line.lower() for kw in ["university", "college", "skills", "experience", "education", "project", "summary", "objective", "profile"]):
                info["full_name"] = line
                break

        # Location: look for city/state/country patterns in first 3 lines only
        # Avoid matching "at <company>" patterns from experience lines
        company_after_at_re = r"^(?!.*(?:Engineer|Developer|Manager|Analyst|Intern|Director|Lead|Consultant|SDE|Architect)).*?(?:at|in|from)\s+([A-Za-z][A-Za-z\s]+,\s*[A-Za-z\s]+)$"
        for line in lines[:3]:
            if not info["location"]:
                m = re.search(company_after_at_re, line, re.IGNORECASE)
                if m:
                    info["location"] = m.group(1).strip()
                    break
        if not info["location"]:
            for line in lines[:3]:
                parts = re.split(r'\||,', line)
                for p in parts:
                    p = p.strip()
                    if re.match(r'^[A-Za-z\s]+,\s*[A-Za-z\s]+$', p) and len(p) < 50 and not re.search(email_re, p) and not re.search(phone_re, p):
                        info["location"] = p
                        break
                if info["location"]:
                    break

        return info

    def _extract_headline(self, lines: List[str], personal: Dict[str, str]) -> str:
        name = personal.get("full_name", "")
        for i, line in enumerate(lines):
            if line == name:
                if i + 1 < len(lines):
                    candidate = lines[i + 1]
                    if candidate and not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", candidate) and not re.search(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}", candidate):
                        return candidate
                break
        return ""

    def _build_summary(self, lines: List[str]) -> str:
        skip_patterns = [
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}",
            r"linkedin\.com/in/[A-Za-z0-9_-]+/?",
            r"github\.com/[A-Za-z0-9_.-]+/?",
            r"^(skills?|education|experience|projects?|certifications?|summary|objective|profile|contact|references?)\s*:?\s*$",
            r"^skills?\s*:",
        ]
        summary_lines = []
        for line in lines:
            if any(re.search(p, line, re.IGNORECASE) for p in skip_patterns):
                continue
            if re.match(r"^[A-Za-z\s]+,\s*[A-Za-z]{2}$", line.strip()):
                continue
            if len(line) > 5:
                summary_lines.append(line)
        summary = " ".join(summary_lines)
        sentences = re.split(r'(?<=[.!?])\s+', summary)
        return " ".join(sentences[:3])[:500]

    def _extract_education(self, lines: List[str]) -> List[Dict[str, str]]:
        results = []
        degree_keywords = r"(?:B\.?Tech|BE|BSc|B\.Sc|BTech|MCA|MBA|M\.?Tech|MTech|MSc|M\.Sc|PhD|Ph\.D|M\.E|ME|B\.E|BCA|MCA|Diploma|B\.Com|M\.Com|BBA|MBA|BA|MA)"
        year_re = r"(?:19|20)\d{2}"
        cgpa_re = r"(?:CGPA|GPA|CPI)[\s:]*([0-9](?:\.[0-9])?)"
        institution_keywords = r"(?:University|College|Institute|School|Academy|IIT|NIT|VIT|MIT|Bits|IIIT)"

        current_entry: Dict[str, str] = {}
        in_education = False

        for i, line in enumerate(lines):
            lower = line.lower()
            if re.search(r'\b(education|academic|qualification|academics?)\b', lower) and not current_entry:
                in_education = True
                continue
            if re.search(r'\b(experience|work|employment|internship|project|certification|skills?)\b', lower) and in_education:
                in_education = False
                if current_entry:
                    results.append(current_entry)
                    current_entry = {}
                continue

            if current_entry and not in_education:
                results.append(current_entry)
                current_entry = {}

            if not in_education:
                continue

            degree_m = re.search(degree_keywords, line, re.IGNORECASE)
            if degree_m:
                if current_entry:
                    results.append(current_entry)
                current_entry = {"degree": "", "specialization": "", "institution": "", "start_date": "", "end_date": "", "cgpa": "", "description": ""}
                degree_text = line[:degree_m.end()]
                current_entry["degree"] = _clean_string(degree_text)
                after_degree = line[degree_m.end():]
                inst_m = re.search(institution_keywords, after_degree, re.IGNORECASE)
                if inst_m:
                    spec = after_degree[:inst_m.start()].strip(" ,-")
                    current_entry["specialization"] = _clean_string(spec)
                    current_entry["institution"] = _clean_string(after_degree[inst_m.start():])
                else:
                    parts = after_degree.split(",")
                    if len(parts) >= 2:
                        current_entry["specialization"] = _clean_string(parts[0].strip(" -"))
                        current_entry["institution"] = _clean_string(",".join(parts[1:]))
                    else:
                        current_entry["specialization"] = _clean_string(after_degree)

            elif current_entry and (re.search(institution_keywords, line, re.IGNORECASE) or (not current_entry["institution"] and len(line) > 5)):
                if not current_entry["institution"]:
                    current_entry["institution"] = _clean_string(line)

            cgpa_m = re.search(cgpa_re, line, re.IGNORECASE)
            if cgpa_m:
                current_entry["cgpa"] = cgpa_m.group(1)

            years = re.findall(year_re, line)
            if len(years) >= 2:
                current_entry["start_date"] = years[0]
                current_entry["end_date"] = years[-1]
            elif len(years) == 1:
                if not current_entry["end_date"]:
                    current_entry["end_date"] = years[0]

        if current_entry:
            results.append(current_entry)

        for entry in results:
            if entry.get("institution"):
                inst = entry["institution"]
                inst = re.sub(r',\s*(?:19|20)\d{2}.*$', '', inst)
                inst = re.sub(r',\s*CGPA[\s:]*[\d.]+.*$', '', inst, flags=re.IGNORECASE)
                inst = re.sub(r',\s*GPA[\s:]*[\d.]+.*$', '', inst, flags=re.IGNORECASE)
                inst = re.sub(r',\s*(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*(?:19|20)\d{2}.*$', '', inst, flags=re.IGNORECASE)
                entry["institution"] = inst.strip(" ,-")

            if entry.get("degree") and entry.get("specialization") and entry["degree"].endswith(entry.get("specialization", "")):
                entry["degree"] = entry["degree"][: -len(entry["specialization"])].strip(" ,-")
            if entry.get("degree") and entry.get("institution") and entry["degree"].endswith(entry.get("institution", "")):
                entry["degree"] = entry["degree"][: -len(entry["institution"])].strip(" ,-")

        return results if results else []

    def _extract_experience(self, lines: List[str]) -> List[Dict[str, str]]:
        results = []
        title_keywords = r"(?:Engineer|Developer|SDE|Manager|Analyst|Designer|Architect|Consultant|Intern|Lead|Director|VP|Head|Specialist|Coordinator|Associate|Executive|Officer|Scientist|Researcher|Advisor|Strategist)"
        company_keywords = r"(?:Inc|LLC|Ltd|Corp|Company|Corporation|Technologies|Solutions|Systems|Services|Labs|Startup|Amazon|Google|Meta|Microsoft|Apple|Netflix|Uber|Airbnb|Spotify|Adobe|Oracle|Salesforce|IBM|Intel|AMD|NVIDIA|Tesla|SpaceX|Flipkart|Zomato|Swiggy|Paytm|Ola|Reliance|TCS|Infosys|Wipro|HCL|TechMahindra|Accenture|Deloitte|KPMG|EY|PwC)"
        duration_re = r"(?:19|20)\d{2}\s*[-–—]\s*(?:Present|(?:19|20)\d{2})"

        current_entry: Dict[str, str] = {}
        in_exp = False

        for i, line in enumerate(lines):
            lower = line.lower()
            if re.search(r'\b(experience|work|employment|professional|internship)\b', lower) and not current_entry:
                in_exp = True
                continue
            if re.search(r'\b(education|project|skill|certification|summary|objective|achievement)\b', lower) and in_exp:
                in_exp = False
                if current_entry:
                    results.append(current_entry)
                    current_entry = {}
                continue

            if current_entry and not in_exp:
                results.append(current_entry)
                current_entry = {}

            if not in_exp:
                continue

            role_company_m = re.search(r"^(.+?)\s+at\s+(.+?)(?:,\s*(.+))?$", line, re.IGNORECASE)
            if role_company_m:
                if current_entry:
                    results.append(current_entry)
                current_entry = {"title": "", "company": "", "location": "", "start_date": "", "end_date": "", "responsibilities": "", "achievements": ""}
                current_entry["title"] = _clean_string(role_company_m.group(1))
                current_entry["company"] = _clean_string(role_company_m.group(2))
                if role_company_m.group(3):
                    dates = role_company_m.group(3).strip()
                    years = re.findall(r"(19|20)\d{2}", dates)
                    if years:
                        current_entry["start_date"] = years[0]
                        current_entry["end_date"] = years[-1] if len(years) > 1 else ""
                continue

            if re.search(company_keywords, line, re.IGNORECASE):
                if not current_entry.get("company"):
                    current_entry["company"] = _clean_string(line)
                    continue

            if re.search(title_keywords, line, re.IGNORECASE) and not current_entry.get("title"):
                current_entry["title"] = _clean_string(line)
                continue

            dates_m = re.search(duration_re, line, re.IGNORECASE)
            if dates_m:
                years = re.findall(r"(19|20)\d{2}", dates_m.group(0))
                if len(years) >= 2:
                    current_entry["start_date"] = years[0]
                    current_entry["end_date"] = years[1]
                continue

            if current_entry and line.startswith(("-", "*", "\u2022", "\u00b7")):
                bullet = line.lstrip("-*\u2022\u00b7 ").strip()
                if bullet:
                    if not current_entry.get("responsibilities"):
                        current_entry["responsibilities"] = bullet
                    else:
                        current_entry["responsibilities"] += "\n" + bullet

        if current_entry:
            results.append(current_entry)

        return results if results else []

    def _extract_projects(self, lines: List[str]) -> List[Dict[str, str]]:
        results = []
        current_entry: Dict[str, str] = {}
        in_projects = False

        for i, line in enumerate(lines):
            lower = line.lower()
            if re.search(r'\b(projects?|portfolio|personal\s+project)\b', lower) and 'certification' not in lower:
                in_projects = True
                continue
            if re.search(r'\b(education|experience|skill|certification|summary|objective|achievement)\b', lower) and in_projects:
                in_projects = False
                if current_entry:
                    results.append(current_entry)
                    current_entry = {}
                continue

            if current_entry and not in_projects:
                results.append(current_entry)
                current_entry = {}

            if not in_projects:
                continue

            if not current_entry:
                if line and not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", line):
                    current_entry = {"project_name": _clean_string(line), "description": "", "technologies": "", "github_url": "", "live_url": "", "start_date": "", "end_date": ""}
                    continue

            github_m = re.search(r"github\.com/[A-Za-z0-9_.-]+/?", line)
            if github_m:
                current_entry["github_url"] = _clean_url(github_m.group(0))
                continue

            live_m = re.search(r"https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?", line)
            if live_m and "github" not in live_m.group(0).lower():
                current_entry["live_url"] = live_m.group(0)
                continue

            if current_entry and line:
                if not current_entry.get("description"):
                    current_entry["description"] = line
                elif not current_entry.get("technologies"):
                    current_entry["technologies"] = line
                else:
                    current_entry["description"] += " " + line

        if current_entry:
            results.append(current_entry)

        return results if results else []

    def _extract_skills(self, lines: List[str]) -> List[str]:
        skills: List[str] = []
        skill_section = False
        for line in lines:
            lower = line.lower()
            if re.search(r'^\s*skills?\s*:?\s*$', lower) or re.search(r'^\s*skills?\s*:\s*', lower):
                skill_section = True
                if ':' in line:
                    inline = line.split(':', 1)[1].strip()
                    if inline:
                        items = re.split(r'[,;|/\u00b7\u2022]+', inline)
                        for item in items:
                            item = item.strip()
                            if item and len(item) > 1 and not re.search(r'[^\x00-\x7F]', item):
                                skills.append(item)
                continue
            if skill_section and re.search(r'^\s*(education|experience|project|certification|summary|objective)\s*:?\s*$', lower):
                skill_section = False
                continue
            if not skill_section:
                continue
            if line:
                items = re.split(r'[,;|/\u00b7\u2022]+', line)
                for item in items:
                    item = item.strip()
                    if item and len(item) > 1 and not re.search(r'[^\x00-\x7F]', item):
                        skills.append(item)
        return skills

    def _categorize_skills(self, skills: List[str]) -> Dict[str, List[str]]:
        categorized: Dict[str, List[str]] = {k: [] for k in KNOWN_SKILL_CATEGORIES}
        uncategorized: List[str] = []
        for skill in skills:
            placed = False
            for category, keywords in KNOWN_SKILL_CATEGORIES.items():
                if skill.lower() in keywords or any(kw in skill.lower() for kw in keywords):
                    if skill not in categorized[category]:
                        categorized[category].append(skill)
                    placed = True
                    break
            if not placed and skill not in uncategorized:
                uncategorized.append(skill)
        if uncategorized:
            categorized.setdefault("general", [])
            categorized["general"].extend(uncategorized)
        return {k: v for k, v in categorized.items() if v}

    def _extract_certifications(self, lines: List[str]) -> List[Dict[str, str]]:
        results = []
        current: Dict[str, str] = {}
        cert_keywords = r"(?:certification|certificate|certified|license)"
        in_cert = False

        for line in lines:
            lower = line.lower()
            if re.search(cert_keywords, lower) and not current:
                in_cert = True
                continue
            if in_cert and re.search(r'^\s*(education|experience|skill|project|summary|objective)\s*:?\s*$', lower):
                in_cert = False
                if current:
                    results.append(current)
                    current = {}
                continue
            if not in_cert:
                continue
            if not current:
                current = {"certification_name": _clean_string(line), "issuer": "", "issue_date": "", "expiry_date": "", "credential_url": ""}
                continue
            issuer_m = re.search(r"(?:by|from|issued by|offered by)\s+(.+)", line, re.IGNORECASE)
            if issuer_m:
                current["issuer"] = _clean_string(issuer_m.group(1))
                continue
            date_m = re.search(r"(19|20)\d{2}", line)
            if date_m:
                if not current["issue_date"]:
                    current["issue_date"] = date_m.group(0)
                elif not current["expiry_date"]:
                    current["expiry_date"] = date_m.group(0)

        if current:
            results.append(current)
        return results


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
