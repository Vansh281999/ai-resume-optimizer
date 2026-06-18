# Market Intelligence Implementation Plan

## Phase 1: Job Intelligence Engine

### Architecture
```
┌─────────────────┐
│   Frontend UI   │
└────────┬────────┘
         │
┌────────▼────────┐
│   Backend API   │
└────────┬────────┘
         │
┌────────▼────────┐
│  Cache Layer    │ (Redis in-memory)
│  (jobs: 12h)   │
└────────┬────────┘
         │
┌────────▼────────┐
│ Job Intelligence  │
│     Engine        │
├──────────────────┤
│ • Job Collector   │
│ • Skill Demand    │
│ • Market Trends   │
└────────┬────────┘
         │
┌────────▼────────┐
│  External APIs  │
│ • RemoteOK      │
│ • Wellfound     │
│ • Adzuna        │
│ • USAJobs       │
└──────────────────┘
```

### Schemas

#### JobPosting Schema
```typescript
interface JobPosting {
  id: string;
  source: string;        // "remoteok", "wellfound", etc.
  title: string;         // Job title
  company: string;       // Company name
  location: string;      // "Remote", "San Francisco, CA"
  salary_min?: number;
  salary_max?: number;
  currency?: string;
  skills: string[];      // Extracted skills
  experience_level?: string; // "entry", "mid", "senior"
  remote: boolean;
  posted_at: string;     // ISO timestamp
  url: string;         // Original posting URL
}
```

#### SkillDemand Schema
```typescript
interface SkillDemand {
  skill: string;
  demand_score: number;  // 0-100 percentage
  job_count: number;
  sources: string[];
  period: string;        // "2026-06"
  trend: "growing" | "stable" | "declining";
}
```

#### MarketTrend Schema
```typescript
interface MarketTrend {
  role: string;
  avg_salary: number;
  demand_score: number;
  growth_rate: number;
  sample_size: number;
}
```

### Services

#### 1. JobCollectorService
```python
# services/job_collector.py
class JobCollectorService:
    def collect_jobs(self, query: str, limit: int = 100) -> List[JobPosting]:
        jobs = []
        jobs.extend(self._collect_remoteok(query))
        jobs.extend(self._collect_wellfound(query))
        jobs.extend(self._collect_adzuna(query))
        return self._deduplicate(jobs)[:limit]
    
    def _collect_remoteok(self, query: str) -> List[JobPosting]:
        # GET https://remoteok.io/api?tags={query}
        pass
    
    def _collect_wellfound(self, query: str) -> List[JobPosting]:
        # Public endpoint: https://wellfound.com/jobs
        pass
    
    def _collect_adzuna(self, query: str) -> List[JobPosting]:
        # GET https://api.adzuna.com/v1/api/jobs/{country}/search/10
        pass
```

#### 2. SkillDemandService
```python
# services/skill_demand.py
class SkillDemandService:
    def analyze_demand(self, jobs: List[JobPosting]) -> Dict[str, SkillDemand]:
        skill_counts = Counter(skill for job in jobs for skill in job.skills)
        total_jobs = len(jobs)
        return {
            skill: SkillDemand(
                skill=skill,
                demand_score=round(count / total_jobs * 100, 1),
                job_count=count,
                sources=list(set(s for j in jobs for s in j.skills if s == skill)),
                period=datetime.now().strftime("%Y-%m"),
                trend=self._calculate_trend(skill)
            )
            for skill, count in skill_counts.items()
        }
```

#### 3. MarketTrendService
```python
# services/market_trend.py
class MarketTrendService:
    def get_trends(self, role: str) -> MarketTrend:
        # Analyze job growth, salary changes, demand patterns
        pass
```

### API Endpoints

```
GET /api/market/jobs?title=developer&location=remote
GET /api/market/skills?title=developer
GET /api/market/trends?title=developer
GET /api/market/salaries?title=developer&location=SF
```

Response format:
```json
{
  "source": ["remoteok", "wellfound"],
  "fetched_at": "2026-06-18T09:57:07Z",
  "confidence": 0.85,
  "data": [...],
  "error": null
}
```

### Database Design

Using SQLite with tables:

```sql
CREATE TABLE job_postings (
    id TEXT PRIMARY KEY,
    source TEXT,
    title TEXT,
    company TEXT,
    location TEXT,
    salary_min REAL,
    salary_max REAL,
    skills TEXT,  -- JSON array
    experience_level TEXT,
    remote INTEGER,
    posted_at TEXT,
    url TEXT,
    collected_at TEXT
);

CREATE TABLE skill_demand (
    skill TEXT PRIMARY KEY,
    demand_score REAL,
    job_count INTEGER,
    period TEXT,
    trend TEXT
);

CREATE INDEX idx_job_title ON job_postings(title);
CREATE INDEX idx_job_skills ON job_postings(skills);
```

### Caching Strategy

| Data | TTL | Strategy |
|------|-----|----------|
| Job postings | 12 hours | Invalidate on new collection |
| Skill demand | 12 hours | Recalculate from fresh jobs |
| Market trends | 24 hours | Slow-changing metrics |
| Salaries | 24 hours | Daily updates sufficient |

### Implementation Effort

| Task | Hours |
|------|-------|
| JobCollectorService (3 sources) | 24 |
| SkillDemandService | 12 |
| MarketTrendService | 16 |
| Database layer | 8 |
| API endpoints | 8 |
| Frontend dashboards | 16 |
| Testing & error handling | 12 |
| **Total** | **80 hours** |

### Legal Considerations

1. **RemoteOK**: Public API, commercial use allowed with attribution
2. **Wellfound**: Public website, scraper must respect rate limits
3. **Adzuna**: Requires API key, free tier available
4. **USAJobs**: Public US government API, no restrictions

All scrapers must:
- Respect `robots.txt`
- Include appropriate `User-Agent` headers
- Implement exponential backoff
- Include attribution in responses