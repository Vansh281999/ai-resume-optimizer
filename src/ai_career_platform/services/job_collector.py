import httpx
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class JobPosting:
    id: str
    source: str
    title: str
    company: str
    location: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = "USD"
    skills: List[str] = None
    experience_level: Optional[str] = None
    remote: bool = False
    posted_at: Optional[str] = None
    url: str = ""
    collected_at: str = ""

    def __post_init__(self):
        if self.skills is None:
            self.skills = []
        if not self.collected_at:
            self.collected_at = datetime.now(timezone.utc).isoformat()

class JobCollectorService:
    REMOTEOK_BASE = "https://remoteok.io/api"
    
    def __init__(self, cache=None):
        self.cache = cache
        try:
            from ai_career_platform.config import settings
            self.adzuna_key = getattr(settings, "ADZUNA_API_KEY", "")
        except:
            self.adzuna_key = ""

    def collect_jobs(self, query: str, limit: int = 50) -> List[JobPosting]:
        cache_key = f"jobs:{query.lower()}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return [JobPosting(**j) for j in cached]
        
        jobs = []
        try:
            jobs.extend(self._collect_remoteok(query))
        except Exception as e:
            logger.warning(f"RemoteOK collection failed: {e}")
        
        if self.cache and jobs:
            self.cache.set(cache_key, [asdict(j) for j in jobs], ttl=43200)  # 12h
        return jobs[:limit]

    def _collect_remoteok(self, query: str) -> List[JobPosting]:
        """Fetch jobs from RemoteOK public API."""
        response = httpx.get(
            f"{self.REMOTEOK_BASE}",
            params={"tags": query.replace(" ", "")},
            timeout=15,
            headers={"User-Agent": "CareerOS/1.0 (+https://github.com/CareerOS)"},
        )
        if response.status_code != 200:
            return []
        
        jobs = []
        for item in response.json() or []:
            if not isinstance(item, dict):
                continue
            job = JobPosting(
                id=str(item.get("id", item.get("slug", ""))),
                source="remoteok",
                title=item.get("title", ""),
                company=item.get("company", ""),
                location="Remote" if item.get("location") == "Anywhere" else item.get("location", ""),
                salary_min=self._parse_salary(item.get("salary_min")),
                salary_max=self._parse_salary(item.get("salary_max")),
                currency=item.get("currency", "USD"),
                skills=self._extract_skills(item.get("tags", [])),
                experience_level=self._extract_experience(item.get("tags", [])),
                remote=item.get("location") == "Anywhere",
                posted_at=item.get("date", ""),
                url=item.get("url", ""),
            )
            jobs.append(job)
        return jobs

    def _parse_salary(self, salary: Any) -> Optional[float]:
        if not salary:
            return None
        if isinstance(salary, (int, float)):
            return float(salary)
        # Parse "$100k - $150k" format
        import re
        nums = re.findall(r'\d+', str(salary))
        if nums:
            return float(nums[0]) * 1000 if len(nums) == 1 else float(nums[0])
        return None

    def _extract_skills(self, tags: List[str]) -> List[str]:
        skill_keywords = [
            "javascript", "typescript", "react", "vue", "angular", "node.js", "python",
            "java", "aws", "docker", "kubernetes", "sql", "nosql", "mongodb",
            "postgresql", "redis", "graphql", "rest", "api", "frontend", "backend",
        ]
        return [t for t in tags if t.lower() in skill_keywords]

    def _extract_experience(self, tags: List[str]) -> Optional[str]:
        experience_tags = {"junior": "entry", "mid": "mid", "senior": "senior", "lead": "senior"}
        for tag in tags:
            if tag.lower() in experience_tags:
                return experience_tags[tag.lower()]
        return None

job_collector = JobCollectorService()