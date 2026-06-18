# Real-Time Career Intelligence Architecture

## Vision
Transform CareerOS from an AI wrapper into a genuine career intelligence platform powered by live market data, eliminating fake fallback data.

## Architecture Overview

```
┌─────────────────┐
│   Frontend UI   │
└────────┬────────┘
         │
┌────────▼────────┐
│   Backend API   │
└────────┬────────┘
         │
┌────────▼────────┐     ┌──────────────────┐
│  Intelligence   │────▶│  LLM Reasoning   │
│   Aggregation   │     │   Engine         │
└────────┬────────┘     └──────────────────┘
         │
┌────────▼────────┐
│  Cache Layer    │ (Redis)
└────────┬────────┘
         │
┌────────▼────────┐
│ Live Data Fetchers│
├──────────────────┤
│ • Salary Sources │
│ • Job Trends     │
│ • Skill Demand   │
│ • Learning       │
└────────┬────────┘
         │
┌────────▼────────┐
│  External APIs  │
└──────────────────┘
```

## Services Layer

### 1. Salary Intelligence Service
**Sources:**
| Source | API | Rate Limit | Notes |
|--------|-----|------------|-------|
| Levels.fyi | Unofficial API | 100/hr | Structured tech salary data |
| Glassdoor | No official API | Scraper | Terms: research use only |
| PayScale | API available | 1000/day paid | Commercial licensing required |
| Indeed | API available | 5000/day | Job/salary data |
| AmbitionBox | No API | Scraper | Indian market focus |

**Implementation:**
```python
# services/salary_service.py
class SalaryService:
    def get_salary_data(self, role: str, location: str = "US") -> SalaryIntelligence:
        cache_key = f"salary:{role}:{location}"
        cached = self.cache.get(cache_key)
        if cached: return cached
        
        # Aggregate from multiple sources
        levels = self._fetch_levels_fyi(role)
        glassdoor = self._fetch_glassdoor(role, location)
        payscale = self._fetch_payscale(role)
        
        result = self._normalize(levels, glassdoor, payscale)
        self.cache.set(cache_key, result, ttl=86400)  # 24h
        return result
```

### 2. Skill Demand Analysis Service
**Sources:**
| Source | API | Rate Limit | Notes |
|--------|-----|------------|-------|
| LinkedIn Jobs | No public API | Scraper | Job post frequency |
| Indeed API | REST | 5000/day | Skills from descriptions |
| Naukri | No API | Scraper | Indian market |
| GitHub | GraphQL | 5000/hr | Language trends |
| Stack Overflow | Survey data | Static | Annual survey |

### 3. Job Trend Service
Analyzes job market trends, role popularity, and geographic distribution.

### 4. Learning Resource Service
**Sources:**
- roadmap.sh (no API, scrape)
- Coursera (API available)
- FreeCodeCamp (no API, scrape)
- MDN (no API, scrape)
- Udemy (API available)

## API Layer

### Internal APIs (for LLM context)
```
GET /api/intelligence/salary/{role}
GET /api/intelligence/demand/{skill}
GET /api/intelligence/trends/{role}
GET /api/intelligence/learning/{skill}
```

### Response Format
```json
{
  "source": "Levels.fyi, Glassdoor",
  "date": "2026-06-18",
  "confidence": 0.85,
  "data": { ... },
  "fallback_used": false
}
```

## Caching Strategy

| Data Type | TTL | Storage |
|-----------|-----|---------|
| Salary data | 24 hours | Redis |
| Job trends | 12 hours | Redis |
| Skill demand | 12 hours | Redis |
| Learning resources | 7 days | Redis |

## Legal Considerations

1. **Rate Limiting:** All scrapers must respect robots.txt and rate limits
2. **Terms of Service:** Monitor ToS for each data source
3. **Attribution:** Display source attribution in UI
4. **Commercial Use:** PayScale/Indeed require commercial licensing for production

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Redis cache setup
- [ ] Salary service with Levels.fyi
- [ ] Error handling (no fake fallbacks)
- [ ] Source attribution UI

### Phase 2: Data Sources (Week 2-4)
- [ ] Add Glassdoor scraper (careful with ToS)
- [ ] Add Indeed integration
- [ ] Add GitHub trends
- [ ] Skill demand analysis

### Phase 3: Learning Resources (Week 3-5)
- [ ] roadmap.sh integration
- [ ] Coursera API
- [ ] FreeCodeCamp resources

### Phase 4: Intelligence Layer (Week 4-6)
- [ ] Aggregate multiple sources
- [ ] Confidence scoring
- [ ] AI insights from real data

## Estimated Development Effort

| Component | Hours |
|-----------|-------|
| Cache layer | 8 |
| Salary service (basic) | 16 |
| Salary service (full) | 32 |
| Trend service | 24 |
| Learning service | 20 |
| Integration testing | 16 |
| **Total** | **116 hours** |

## Current State

The system currently uses:
- OpenRouter (Claude) for AI generation
- Fallback static data when AI is unavailable

**Next Steps:**
1. Create `services/` directory
2. Implement `SalaryService` with Levels.fyi
3. Replace fallback data with "Data unavailable" state
4. Add Redis caching