import logging
import re
from typing import Any, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class SalaryExtractor:
    BASE_URL = "https://salarybyrole.com/api/salary"
    
    ROLE_MAPPINGS = {
        "software engineer": ["software engineer", "software developer", "sde", "sde ii", "sde 1", "sde 1"],
        "frontend developer": ["frontend developer", "react developer", "ui developer", "web developer"],
        "backend developer": ["backend developer", "api developer", "server developer"],
        "full stack developer": ["full stack developer", "fullstack developer", "full-stack developer"],
        "data scientist": ["data scientist", "ml engineer", "machine learning engineer", "ai engineer"],
        "devops engineer": ["devops engineer", "site reliability engineer", "sre", "cloud engineer"],
        "product manager": ["product manager", "technical product manager"],
        "designer": ["ui designer", "ux designer", "product designer", "graphic designer"],
        "qa engineer": ["qa engineer", "test engineer", "quality assurance engineer"],
        "mobile developer": ["mobile developer", "android developer", "ios developer", "flutter developer"],
    }
    
    COUNTRY_CODE_MAP = {
        "india": "india",
        "usa": "united-states",
        "us": "united-states",
        "united states": "united-states",
        "uk": "united-kingdom",
        "united kingdom": "united-kingdom",
        "canada": "canada",
        "australia": "australia",
        "germany": "germany",
        "netherlands": "netherlands",
        "singapore": "singapore",
    }

    @staticmethod
    def _normalize_role(role: str) -> str:
        role_lower = role.lower().strip()
        for normalized, variants in SalaryExtractor.ROLE_MAPPINGS.items():
            if role_lower in variants:
                return normalized
        slug = re.sub(r"[^a-z0-9]+", "-", role_lower)
        slug = re.sub(r"-+/-+", "-", slug)
        return slug.strip("-")

    @staticmethod
    def _normalize_country(location: str) -> str:
        if not location:
            return "united-states"
        loc_lower = location.lower().strip()
        for key, value in SalaryExtractor.COUNTRY_CODE_MAP.items():
            if key in loc_lower:
                return value
        return "united-states"

    def _fetch_salary(self, role_slug: str, country_slug: str) -> Optional[Dict[str, Any]]:
        try:
            params = {"role": role_slug, "country": country_slug}
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(self.BASE_URL, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    return data
            logger.warning("salary_api_no_data role=%s country=%s", role_slug, country_slug)
        except Exception as exc:
            logger.error("salary_api_error role=%s error=%s", role_slug, exc)
        return None

    def get_salary_insights(self, role: str, location: str = "") -> Dict[str, Any]:
        role_slug = self._normalize_role(role)
        country_slug = self._normalize_country(location)
        data = self._fetch_salary(role_slug, country_slug)
        
        if not data:
            return {
                "role": role,
                "location": location or "United States",
                "salaries": [],
                "source": "api_unavailable",
            }
        
        return {
            "role": data.get("role", {}).get("title", role),
            "location": data.get("country", {}).get("name", location or "United States"),
            "currency": data.get("country", {}).get("currency", "USD"),
            "salaries": data.get("salaries", []),
            "source": "salarybyrole.com",
            "generated_at": data.get("generated_at"),
        }