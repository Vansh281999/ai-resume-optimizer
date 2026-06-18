import re
import logging
from typing import List, Dict, Optional, Set

from ai_career_platform.models import ATSScoreReport

logger = logging.getLogger(__name__)

ATS_KEYWORDS = {
    "skills": ["skills", "technical skills", "competencies", "proficiencies"],
    "experience": ["experience", "work history", "employment", "professional experience"],
    "education": ["education", "academic", "qualifications"],
    "summary": ["summary", "profile", "objective", "about"],
    "contact": ["contact", "email", "phone", "linkedin", "address"],
}

FORMATTING_RISKS = [
    (r"\t{2,}", "Excessive tabs"),
    (r"  {3,}", "Multi-space indents"),
    (r"\|.*\|", "Table-like formatting"),
    (r"<[^>]{10,}>", "Long HTML/XML tags"),
    (r"[\u0080-\u00FF]{3,}", "Non-ASCII chars"),
]

ACTION_VERBS: List[str] = [
    "achieved", "improved", "led", "managed", "developed", "created",
    "increased", "reduced", "optimized", "delivered", "implemented",
]

STOP_WORDS: Set[str] = {
    "the", "and", "for", "with", "that", "this", "have", "from", "they",
    "will", "would", "could", "should", "been", "were", "was", "are", "not",
    "but", "can", "may", "might", "shall",
}

MAX_RESUME_LENGTH = 20_000
FORMATTING_RISK_UNIT = 18.0
KEYWORD_PATTERN = re.compile(r"[a-z0-9+#./-]{3,}")


class ATSScoringEngine:
    def score(self, text: str, job_keywords: Optional[List[str]] = None) -> ATSScoreReport:
        text = text or ""
        if not text.strip():
            return ATSScoreReport(
                overall_score=0,
                keyword_density_score=0,
                formatting_risk_score=0,
                missing_sections=list(ATS_KEYWORDS),
                found_sections=[],
                critical_issues=["Resume text is empty"],
                improvement_suggestions=["Add resume content before scoring"],
            )
        lower = text.lower()
        found_sections = [s for s, kws in ATS_KEYWORDS.items() if any(re.search(rf"\b{re.escape(k)}\b", lower) for k in kws)]
        missing_sections = [s for s in ATS_KEYWORDS if s not in found_sections]

        keywords = [str(k).strip().lower() for k in (job_keywords or []) if str(k).strip()]
        if not keywords:
            keywords = list({w for w in KEYWORD_PATTERN.findall(lower) if w not in STOP_WORDS})[:120]

        keyword_density_score = self._keyword_density(lower, keywords)
        formatting_risk_score = self._formatting_risk(text)
        section_score = ((len(found_sections) / max(len(ATS_KEYWORDS), 1)) * 100)

        overall = max(0, min(100, round(
            0.45 * keyword_density_score +
            0.25 * (100 - formatting_risk_score) +
            0.30 * section_score,
            2
        )))

        issues: List[str] = []
        suggestions: List[str] = []
        if len(text) > MAX_RESUME_LENGTH:
            issues.append("Resume too long; condense to <=2 pages")
            suggestions.append("Shorten resume length for ATS compatibility")
        if not re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text):
            issues.append("No email pattern detected")
            suggestions.append("Ensure contact email is present and readable")
        if not re.search(r"\+?\d[\d\s\-()]{8,}", text):
            issues.append("No phone pattern detected")
            suggestions.append("Ensure phone number is present and readable")
        if formatting_risk_score > 40:
            issues.append("High formatting risk")
            suggestions.append("Simplify formatting for ATS compatibility")
        if keyword_density_score < 50:
            suggestions.append("Increase keyword density aligned to job description")
        for section in missing_sections:
            suggestions.append(f"Add missing section: {section}")
        weak = [v for v in ACTION_VERBS if v not in lower]
        if weak:
            suggestions.append("Strengthen action verbs in experience bullets")

        return ATSScoreReport(
            overall_score=overall,
            keyword_density_score=keyword_density_score,
            formatting_risk_score=formatting_risk_score,
            missing_sections=missing_sections,
            found_sections=found_sections,
            critical_issues=issues,
            improvement_suggestions=suggestions,
            focus_areas=[
                {"name": "Keyword alignment", "score": keyword_density_score},
                {"name": "Section completeness", "score": round((len(found_sections) / max(len(ATS_KEYWORDS), 1)) * 100, 2)},
                {"name": "Role-specific impact", "score": round(0.6 * keyword_density_score + 0.4 * (100 - formatting_risk_score), 2)},
            ],
        )

    def _keyword_density(self, text: str, keywords: List[str]) -> float:
        if not keywords:
            return 75.0
        return round((sum(1 for k in keywords if k in text) / len(keywords)) * 100, 2)

    def _formatting_risk(self, text: str) -> float:
        score = 0.0
        for pattern, _ in FORMATTING_RISKS:
            if re.search(pattern, text):
                score += FORMATTING_RISK_UNIT
        if len(text) > MAX_RESUME_LENGTH:
            score += 25.0
        return min(100.0, score)