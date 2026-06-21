import io
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ai_career_platform.ai_providers.factory import get_multi_provider


class ResumeIngestionError(RuntimeError):
    pass


class ResumeIngestionPipeline:
    def __init__(self, providers: Optional[List[str]] = None, model: str = "gemini-2.0-flash", max_text_chars: int = 30000):
        self.model = model
        self.max_text_chars = max_text_chars
        self.provider = get_multi_provider(providers=providers or ["gemini", "openrouter", "ollama"], model=model)
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

    def ingest(self, content: bytes, filename: str) -> Dict[str, Any]:
        raw_text = self.extract_text(content, filename)
        cleaned_text = self.clean_text(raw_text)
        if not cleaned_text:
            raise ResumeIngestionError("Could not extract readable text from the uploaded resume. Try a PDF, DOCX, or TXT file with selectable text.")
        parsed = self.parse(cleaned_text)
        return {
            "cleaned_text": cleaned_text,
            "parsed": parsed,
            "metadata": {
                "filename": Path(filename).name,
                "text_chars": len(cleaned_text),
                "parser_model": self.model,
            },
        }

    def extract_text(self, content: bytes, filename: str) -> str:
        suffix = Path(filename).suffix.lower()
        if suffix == ".pdf":
            return self._extract_pdf(content)
        if suffix == ".docx":
            return self._extract_docx(content)
        if suffix == ".txt":
            return content.decode("utf-8", errors="ignore")
        if suffix == ".doc":
            raise ResumeIngestionError("Legacy .doc files are not supported. Convert the resume to DOCX, PDF, or TXT and upload again.")
        raise ResumeIngestionError(f"Unsupported file type: {suffix or 'no extension'}. Upload PDF, DOCX, or TXT.")

    def clean_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\u00a0", " ")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        lines = [line for line in lines if line]
        return "\n".join(lines)[: self.max_text_chars]

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
        try:
            import fitz

            with fitz.open(stream=content, filetype="pdf") as doc:
                return "\n".join(page.get_text("text") or "" for page in doc)
        except Exception as exc:
            raise ResumeIngestionError("PDF extraction failed. Try exporting the resume as a text-based PDF.") from exc

    def _extract_docx(self, content: bytes) -> str:
        try:
            from docx import Document

            doc = Document(io.BytesIO(content))
            parts = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text for cell in row.cells if cell.text)
                    if row_text:
                        parts.append(row_text)
            return "\n".join(parts)
        except Exception as exc:
            raise ResumeIngestionError("DOCX extraction failed. Try saving the resume as DOCX or PDF.") from exc

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
