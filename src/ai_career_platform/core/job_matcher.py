import logging
from typing import List, Dict, Optional
from .ats_engine import ATSScoringEngine
from ..models import JobMatchReport

logger = logging.getLogger(__name__)


class JobMatcher:
    def __init__(self):
        self.ats = ATSScoringEngine()

    def match(self, resume_text: str, job_description: str, job_keywords: Optional[List[str]] = None) -> JobMatchReport:
        ats = self.ats.score(resume_text, job_keywords=job_keywords)
        job_lower = (job_description or "").lower()
        resume_lower = (resume_text or "").lower()
        job_words = [w for w in __import__("re").findall(r"[a-z0-9+#./-]{3,}", job_lower)]
        resume_words = set(__import__("re").findall(r"[a-z0-9+#./-]{3,}", resume_lower))

        present = [w for w in job_words if w in resume_words]
        missing = [w for w in job_words if w not in resume_words]
        keyword_match = round((len(present) / max(len(job_words), 1)) * 100, 2) if job_words else 75.0

        skill_score = round(
            0.55 * keyword_match + 0.45 * (ats.keyword_density_score * 0.6 + (100 - ats.formatting_risk_score) * 0.4), 2)
        experience_score = ats.keyword_density_score
        overall = round(
            0.40 * skill_score + 0.35 * (100 - ats.formatting_risk_score) + 0.25 * ((len(ats.found_sections) / max(len(ats.found_sections) + len(ats.missing_sections), 1)) * 100), 2)

        return JobMatchReport(
            overall_match_score=max(0.0, min(100.0, overall)),
            skill_match_score=skill_score,
            experience_match_score=experience_score,
            missing_skills=missing[:20],
            recommended_keywords=missing[:15],
            match_details={
                "keyword_match": keyword_match,
                "present_keywords": len(present),
                "missing_keywords": len(missing),
                "ats_overall": ats.overall_score,
            },
        )
