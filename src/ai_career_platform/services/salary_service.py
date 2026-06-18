import httpx
import logging
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SalaryData:
    role: str
    location: str
    entry: Optional[float] = None
    mid: Optional[float] = None
    senior: Optional[float] = None
    currency: str = "USD"
    sources: List[str] = None
    date_fetched: str = None
    confidence: float = 0.0

    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.date_fetched is None:
            self.date_fetched = datetime.now(timezone.utc).isoformat()

class SalaryService:
    """Fetches real-time salary data for roles via web search."""

    def __init__(self, cache=None):
        self.cache = cache
        try:
            from ai_career_platform.config import settings
            self.serper_key = getattr(settings, "SERPER_API_KEY", "")
        except:
            self.serper_key = ""

    def get_salary_data(self, role: str, location: str = "US") -> SalaryData:
        cache_key = f"salary:{role.lower()}:{location.lower()}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached:
                return SalaryData(**cached)
        
        try:
            return self._fetch_via_serper(role, location)
        except Exception as e:
            logger.warning(f"Salary fetch failed for {role}: {e}")
            return SalaryData(role=role, location=location, confidence=0.0)

    def _fetch_via_serper(self, role: str, location: str) -> SalaryData:
        """Use Serper API to search for salary data."""
        if not self.serper_key:
            raise ValueError("SERPER_API_KEY not configured")
        
        query = f"salary {role} {location} site:glassdoor.com OR site:levels.fyi OR site:payscale.com"
        response = httpx.post(
            "https://google.serper.dev/search",
            json={"q": query, "num": 5},
            headers={"X-API-KEY": self.serper_key, "Content-Type": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        results = response.json()
        
        # Extract salary numbers from snippets
        snippets = " ".join(r.get("snippet", "") for r in results.get("organic", []))
        import re
        numbers = [float(m) for m in re.findall(r'\$([0-9]{1,3}(?:,[0-9]{3})*|\d{1,6})[Kk]?', snippets)]
        
        if len(numbers) >= 3:
            return SalaryData(
                role=role,
                location=location,
                entry=min(numbers),
                mid=sorted(numbers)[len(numbers)//2],
                senior=max(numbers),
                sources=["Serper Search"],
                confidence=min(0.9, len(numbers) * 0.1),
            )
        
        raise ValueError("No salary data found in search results")

salary_service = SalaryService()