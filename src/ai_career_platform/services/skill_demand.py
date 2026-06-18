import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from collections import Counter
from dataclasses import dataclass

from .job_collector import JobPosting

logger = logging.getLogger(__name__)

@dataclass
class SkillDemand:
    skill: str
    demand_score: float  # 0-100 percentage
    job_count: int
    sources: List[str]
    period: str
    trend: str = "stable"  # "growing", "stable", "declining"

@dataclass
class MarketTrend:
    role: str
    avg_salary: Optional[float]
    demand_score: float
    growth_rate: float
    sample_size: int

class SkillDemandService:
    def analyze_demand(self, jobs: List[JobPosting]) -> Dict[str, SkillDemand]:
        if not jobs:
            return {}
        
        skill_jobs: Dict[str, List[JobPosting]] = {}
        for job in jobs:
            for skill in job.skills or []:
                if skill not in skill_jobs:
                    skill_jobs[skill] = []
                skill_jobs[skill].append(job)
        
        total_jobs = len(jobs)
        results = {}
        
        for skill, skill_job_list in skill_jobs.items():
            demand_score = round(len(skill_job_list) / total_jobs * 100, 1)
            results[skill] = SkillDemand(
                skill=skill,
                demand_score=min(100, demand_score),
                job_count=len(skill_job_list),
                sources=list(set(j.source for j in skill_job_list)),
                period=datetime.now(timezone.utc).strftime("%Y-%m"),
                trend="growing" if demand_score > 50 else "stable" if demand_score > 20 else "declining"
            )
        
        return dict(sorted(results.items(), key=lambda x: x[1].demand_score, reverse=True))

class MarketTrendService:
    def analyze_trends(self, jobs: List[JobPosting], role: str) -> MarketTrend:
        if not jobs:
            return MarketTrend(role=role, avg_salary=None, demand_score=0, growth_rate=0, sample_size=0)
        
        salaries = [j.salary_max for j in jobs if j.salary_max]
        avg_salary = sum(salaries) / len(salaries) if salaries else None
        
        return MarketTrend(
            role=role,
            avg_salary=avg_salary,
            demand_score=min(100, len(jobs) / 10),  # Simple scoring
            growth_rate=0,  # Would need historical data
            sample_size=len(jobs)
        )

skill_demand_service = SkillDemandService()
market_trend_service = MarketTrendService()