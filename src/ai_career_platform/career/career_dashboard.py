import logging
from typing import List, Dict, Optional
from ..ai_providers.factory import get_llm_provider
from ..models import CareerRoadmap, SkillProgression
from ..utils.validators import validate_input

logger = logging.getLogger(__name__)


class CareerDashboard:
    def __init__(self, provider: str = "openai", model: Optional[str] = None):
        self.provider_name = provider
        self.model = model

    def roadmap(self, current_skills: List[str], target_role: str, context: str = "") -> CareerRoadmap:
        validate_input("target_role", target_role)
        current_skills = [s.strip() for s in current_skills if s and str(s).strip()]
        prompt = (
            "Create a concise career roadmap JSON for transitioning into the target role. "
            "Include skill progressions, estimated timeline months, and salary progression estimates "
            "only if safely inferable. Do not invent precise salary data if uncertain. "
            "Return JSON with keys: current_role, target_role, estimated_timeline_months, "
            "skill_progressions, salary_progression. "
            "skill_progressions is a list of objects with keys: skill_name, current_level, target_level, "
            "learning_resources, estimated_months. Levels are 0-100.\n\n"
            f"Current candidate skills: {', '.join(current_skills)}\n"
            f"Target role: {target_role}\n"
            f"Context: {context}\n"
        )
        provider = get_llm_provider(self.provider_name, self.model)
        text = provider.generate([{"role": "user", "content": prompt}])
        payload = self._parse(text)
        skill_progressions: List[SkillProgression] = []
        for item in payload.get("skill_progressions", []) or []:
            if isinstance(item, dict):
                skill_progressions.append(SkillProgression(
                    skill_name=item.get("skill_name", "Unknown Skill"),
                    current_level=float(item.get("current_level", 70)),
                    target_level=float(item.get("target_level", 90)),
                    learning_resources=item.get("learning_resources", []) or [],
                    estimated_months=int(item.get("estimated_months", 6)),
                ))
        return CareerRoadmap(
            current_role=payload.get("current_role", "Unknown"),
            target_role=target_role,
            skill_progressions=skill_progressions,
            estimated_timeline_months=int(payload.get("estimated_timeline_months", 12)),
            salary_progression=payload.get("salary_progression", {}) or {},
        )

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
