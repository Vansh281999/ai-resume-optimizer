import logging
from typing import List, Dict, Optional
from ..ai_providers.factory import get_llm_provider
from ..models import InterviewPrepReport, InterviewQuestion
from ..utils.validators import validate_input

logger = logging.getLogger(__name__)


class InterviewPrepModule:
    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        self.provider_name = provider
        self.model = model

    def generate(self, company: str, role: str, job_description: str = "") -> InterviewPrepReport:
        validate_input("company", company)
        validate_input("role", role)
        prompt = (
            "Generate role-specific interview preparation content for a candidate applying to "
            f"{role} at {company}. "
            "Include separate lists of technical, behavioral, and company-specific interview questions, "
            "plus concise preparation tips. Return a compact JSON object with keys: "
            "technical_questions, behavioral_questions, company_specific_questions, preparation_tips. "
            "Each question should include category, difficulty, and optional tips.\n\n"
            f"Job description:\n{job_description}\n"
        )
        provider = get_llm_provider(self.provider_name, self.model)
        text = provider.generate([{"role": "user", "content": prompt}])
        payload = self._parse(text)
        return InterviewPrepReport(
            company=company,
            role=role,
            technical_questions=self._questions(payload.get("technical_questions", [])),
            behavioral_questions=self._questions(payload.get("behavioral_questions", [])),
            company_specific_questions=self._questions(payload.get("company_specific_questions", [])),
            preparation_tips=payload.get("preparation_tips", []) or [],
        )

    def _questions(self, items: List[Dict]) -> List[InterviewQuestion]:
        out: List[InterviewQuestion] = []
        for item in items:
            if isinstance(item, str):
                out.append(InterviewQuestion(question=item, category="general", difficulty="medium"))
            elif isinstance(item, dict):
                out.append(InterviewQuestion(
                    question=item.get("question") or item.get("q") or "",
                    category=item.get("category", "general"),
                    difficulty=item.get("difficulty", "medium"),
                    tips=item.get("tips"),
                ))
        return out

    def _parse(self, text: str) -> Dict:
        import json, re
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?", "", text).strip()
            if text.endswith("```"):
                text = text[:-3].strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}
