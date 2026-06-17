# Backend Architecture - Complete Documentation

## Overview

The AI Career Intelligence Platform backend is a FastAPI application with SQLAlchemy for persistence. It provides resume analysis, job matching, interview preparation, and career roadmap features. AI features gracefully fall back to predefined JSON data when providers are unavailable.

## Directory Structure

```
src/
├── api/
│   └── server.py              # FastAPI application, routes, middleware
├── ai_career_platform/
│   ├── config.py              # Pydantic settings (env vars)
│   ├── models.py              # Pydantic response schemas
│   ├── security.py            # SecretScanner for credential detection
│   ├── core/
│   │   ├── ats_engine.py      # Deterministic ATS scoring engine
│   │   └── job_matcher.py     # Resume vs job description matching
│   ├── ai_providers/
│   │   ├── factory.py         # Provider selection factory
│   │   ├── openai_provider.py # OpenAI integration
│   │   ├── anthropic_provider.py # Anthropic integration
│   │   ├── gemini_provider.py # Gemini integration
│   │   └── ollama_provider.py # Ollama integration
│   ├── analytics/
│   │   └── analytics_tracker.py # JSONL event persistence
│   ├── interview/
│   │   └── interview_module.py # Interview prep generation
│   ├── career/
│   │   └── career_dashboard.py # Career roadmap generation
│   └── utils/
│       └── validators.py      # Input validation, redaction
└── ai_career_platform/db/
    ├── base.py                # SQLAlchemy declarative base
    ├── models.py              # User, PasswordResetToken ORM models
    └── session.py             # Database engine + session factory
```

## Configuration (config.py)

`Settings` class using `pydantic_settings.BaseSettings`:

```python
OPENAI_API_KEY: str = ""
ANTHROPIC_API_KEY: str = ""
GEMINI_API_KEY: str = ""
OLLAMA_BASE_URL: str = "http://localhost:11434"
DATABASE_URL: str = "sqlite:///./career_platform.db"
SECRET_KEY: str = ""            # Required - fails startup if insecure/empty
DEBUG: bool = False
LOG_LEVEL: str = "INFO"
MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10MB
ALLOWED_UPLOAD_EXTENSIONS: str = ".pdf,.docx,.txt"
ACCESS_TOKEN_EXPIRE_HOURS: int = 24
```

## API Endpoints

### Authentication
- `POST /api/auth/signup` - Register user, returns JWT token
- `POST /api/auth/login` - Authenticate, returns JWT token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/forgot-password` - Initiate password reset
- `POST /api/auth/reset-password` - Reset password using token

### ATS Scoring
- `POST /api/ats/score` - Score resume text with optional keywords
- `POST /api/ats/upload` - Upload resume file (PDF/DOCX/TXT), optional additional_text and keywords

### Job Matching
- `POST /api/jobs/match` - Match resume against job description

### Interview/Career
- `POST /api/interview/generate` - Generate interview questions (AI or fallback)
- `POST /api/career/roadmap` - Generate career plan (AI or fallback)

### Analytics
- `GET /api/analytics/trends` - Get ATS/job match trends
- `POST /api/analytics/event` - Record custom events

### Security/Health
- `POST /api/security/scan` - Scan text for secrets
- `GET /api/health` - System health check
- `GET /api/health/ai` - AI provider status

## Response Models

### ATSScoreReport
- `overall_score`: 0-100 aggregate score
- `keyword_density_score`: Job keyword match percentage
- `formatting_risk_score`: Risk from complex formatting
- `missing_sections`: List of missing resume sections
- `found_sections`: List of found sections
- `critical_issues`: List of blocking issues
- `improvement_suggestions`: List of actionable improvements

### JobMatchReport
- `overall_match_score`: 0-100 overall match
- `skill_match_score`: Skill overlap percentage
- `experience_match_score`: Experience alignment
- `missing_skills`: Skills to add
- `recommended_keywords`: Keywords to include
- `match_details`: Detailed breakdown

### InterviewPrepReport
- `company`, `role`: Target context
- `technical_questions`, `behavioral_questions`, `company_specific_questions`: Question lists
- `preparation_tips`: Actionable tips

### CareerRoadmap
- `current_role`, `target_role`: Career transition
- `skill_progressions`: Skills to develop with targets
- `estimated_timeline_months`: Duration estimate
- `salary_progression`: Salary range estimates

## Security Features

- Mandatory SECRET_KEY validation at startup
- JWT tokens use numeric `.timestamp()` for expiration
- Password reset tokens stored in DB with expiration check
- File upload size limits (10MB)
- File extension and content-type validation
- Input validation and sanitization
- CORS from environment-based origins
- Secret scanning for credential leakage

## AI Providers

All providers support timeout (default 60s) and retries (default 2):
- `openai` (gpt-4o-mini)
- `anthropic` (claude-3-5-haiku-20241022)
- `gemini` (gemini-2.0-flash)
- `ollama` (llama3)

Fallback to JSON data in `output/` when providers unavailable.

## Testing

Run with: `SECRET_KEY=test-key python -m pytest tests/ -v`

74 tests covering auth, ATS, upload, security, analytics, and API integration.