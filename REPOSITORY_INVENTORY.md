# Repository Inventory

## Structure Overview

```
ai-resume-optimizer/
├── .github/                    # GitHub workflows (4)
│   └── workflows/
│       ├── pages.yml           # GitHub Pages deployment
│       ├── lint.yml            # Linting workflow
│       ├── frontend-build.yml  # Frontend build workflow
│       └── backend-tests.yml   # Backend tests workflow
├── alembic/                    # Database migrations
├── frontend/                   # React frontend application
├── src/
│   ├── ai_career_platform/     # Main Python package
│   │   ├── ai_providers/       # LLM provider integrations
│   │   ├── core/               # ATS engine, job matcher
│   │   ├── services/           # Resume parser, job collector
│   │   ├── db/                 # Database models
│   │   ├── analytics/          # Analytics tracking
│   │   ├── career/             # Career dashboard
│   │   ├── interview/          # Interview prep
│   │   └── canvas/             # Career canvas data
│   ├── api/                    # FastAPI backend
│   ├── resume_crew/            # CrewAI integration (legacy)
│   └── ai_career_platform.db   # SQLite database (gitignored)
├── tests/                      # Test suite
├── knowledge/                  # Test artifacts
├── alembic.ini                 # Migration configuration
├── docker-compose.yml          # Docker compose
├── Dockerfile                  # Development container
├── Dockerfile.prod             # Production container
├── nginx.conf                  # Nginx configuration
├── pyproject.toml              # Python package config
├── README.md                   # Project documentation
└── PARSER_V2_QUALITY_REPORT.md # Parser quality report
```

## File Categories

### KEEP (Production Essential)
- `.github/workflows/*.yml` - CI/CD pipelines
- `frontend/` - React application source
- `src/` - Python backend source
- `tests/` - Test suite
- `alembic/` - Database migrations
- `Dockerfile`, `Dockerfile.prod` - Container definitions
- `docker-compose.yml` - Service orchestration
- `nginx.conf` - Web server config
- `pyproject.toml` - Package configuration
- `README.md` - Documentation
- `.gitignore` - Git ignore rules
- `.env.example`, `frontend/.env.example` - Environment templates

### DELETE (Removed)
- `CLEANUP_REPORT.md` - Generated cleanup report (deleted)

### ARCHIVE (Future)
- `src/resume_crew/` - CrewAI integration (not currently in active use)

## Production Verification

- All tests pass: `pytest tests/`
- No hardcoded secrets in committed code
- Environment variables properly configured in `.env.example`
- GitHub Pages deployment configured
- TypeScript config present in `frontend/`