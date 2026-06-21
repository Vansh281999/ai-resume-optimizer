import json
import re
from typing import Any, Dict, List, Optional

from ai_career_platform.ai_providers.gemini_provider import GeminiProvider


class ResumeParser:
    def __init__(self, model: str = "gemini-2.0-flash"):
        self.provider = GeminiProvider(model=model)
        self.system_prompt = (
            "You are a resume parsing system. Extract structured career profile data from the resume text. "
            "Return ONLY a JSON object matching this exact structure. No markdown, no explanations, no preamble.\n\n"
            "{\n"
            '  "personal_info": {\n'
            '    "full_name": "",\n'
            '    "email": "",\n'
            '    "phone": "",\n'
            '    "location": "",\n'
            '    "linkedin_url": "",\n'
            '    "github_url": "",\n'
            '    "portfolio_url": ""\n'
            "  },\n"
            '  "headline": "",\n'
            '  "summary": "",\n'
            '  "career_objective": "",\n'
            '  "education": [\n'
            "    {\n"
            '      "degree": "",\n'
            '      "specialization": "",\n'
            '      "institution": "",\n'
            '      "start_date": "",\n'
            '      "end_date": "",\n'
            '      "cgpa": "",\n'
            '      "description": ""\n'
            "    }\n"
            "  ],\n"
            '  "experience": [\n'
            "    {\n"
            '      "title": "",\n'
            '      "company": "",\n'
            '      "location": "",\n'
            '      "start_date": "",\n'
            '      "end_date": "",\n'
            '      "responsibilities": "",\n'
            '      "achievements": ""\n'
            "    }\n"
            "  ],\n"
            '  "projects": [\n'
            "    {\n"
            '      "project_name": "",\n'
            '      "description": "",\n'
            '      "technologies": "",\n'
            '      "github_url": "",\n'
            '      "live_url": "",\n'
            '      "start_date": "",\n'
            '      "end_date": ""\n'
            "    }\n"
            "  ],\n"
            '  "skills": {\n'
            '    "programming_languages": [],\n'
            '    "frameworks": [],\n'
            '    "databases": [],\n'
            '    "cloud_technologies": [],\n'
            '    "devops_tools": [],\n'
            '    "ai_ml_technologies": [],\n'
            '    "soft_skills": []\n'
            "  },\n"
            '  "certifications": [\n'
            "    {\n"
            '      "certification_name": "",\n'
            '      "issuer": "",\n'
            '      "issue_date": "",\n'
            '      "expiry_date": "",\n'
            '      "credential_url": ""\n'
            "    }\n"
            "  ],\n"
            '  "job_preferences": {\n'
            '    "preferred_roles": "",\n'
            '    "preferred_locations": "",\n'
            '    "work_mode": "",\n'
            '    "expected_salary_min": null,\n'
            '    "expected_salary_max": null,\n'
            '    "years_of_experience": ""\n'
            "  }\n"
            "}"
        )

    def parse(self, resume_text: str) -> Dict[str, Any]:
        if not resume_text or not resume_text.strip():
            raise ValueError("Resume text is empty")
        try:
            prompt = (
                f"{self.system_prompt}\n\n"
                "Resume text to parse:\n"
                "--------------------\n"
                f"{resume_text.strip()}\n"
                "--------------------\n"
                "Parse the above resume and return the JSON object."
            )
            raw = self.provider.generate(
                [{"role": "user", "content": prompt}],
                timeout=120,
                retries=2,
            )
            data = self._extract_json(raw)
            return self._validate(data)
        except Exception:
            return self._fallback_parse(resume_text)

    def _fallback_parse(self, resume_text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        text = "\n".join(lines)
        email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
        phone_match = re.search(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}", text)
        linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+/?", text)
        github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_.-]+/?", text)
        portfolio_match = re.search(r"(?:https?://)?(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]*)?", text)

        personal_info = {
            "full_name": lines[0] if lines else "",
            "email": email_match.group(0) if email_match else "",
            "phone": phone_match.group(0) if phone_match else "",
            "location": "",
            "linkedin_url": linkedin_match.group(0) if linkedin_match else "",
            "github_url": github_match.group(0) if github_match else "",
            "portfolio_url": portfolio_match.group(0) if portfolio_match and portfolio_match.group(0).lower() not in {linkedin_match.group(0).lower() if linkedin_match else "", github_match.group(0).lower() if github_match else ""} else "",
        }
        section_headers = {
            "education", "experience", "projects", "skills", "certifications", "summary", "objective", "career objective", "profile", "about"
        }
        summary_lines = []
        for line in lines[1:]:
            normalized = line.lower().rstrip(":")
            if normalized in section_headers or normalized.endswith(" experience") or normalized.endswith(" education"):
                break
            summary_lines.append(line)
        summary = " ".join(summary_lines)[:1200]

        return self._validate({
            "personal_info": personal_info,
            "headline": lines[1] if len(lines) > 1 else "",
            "summary": summary,
            "career_objective": "",
            "education": [],
            "experience": [],
            "projects": [],
            "skills": {},
            "certifications": [],
            "job_preferences": {},
        })

    def _extract_json(self, raw: str) -> Dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n?", "", text)
            text = re.sub(r"\n?```$", "", text)
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError(f"Could not extract JSON from output: {text[:300]}")
        json_str = text[start : end + 1]
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON from parser: {exc}\nRaw: {json_str[:500]}") from exc

    def _validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValueError("Parsed output is not a JSON object")
        data.setdefault("personal_info", {})
        data.setdefault("education", [])
        data.setdefault("experience", [])
        data.setdefault("projects", [])
        data.setdefault("skills", {})
        data.setdefault("certifications", [])
        data.setdefault("job_preferences", {})
        return data
