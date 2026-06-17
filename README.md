# AI Career Intelligence Platform

An end-to-end career intelligence system that scores resumes against job descriptions, matches candidates to roles, generates interview prep content, and tracks career growth with analytics.

## Features

- ATS Scoring Engine (`ai_career_platform.core.ats_engine`)
- Resume vs Job Matching (`ai_career_platform.core.job_matcher`)
- Interview Preparation Module (`ai_career_platform.interview.interview_module`)
- Career Growth Dashboard (`ai_career_platform.career.career_dashboard`)
- Analytics System (`ai_career_platform.analytics.analytics_tracker`)
- Multi-Model AI Support (`ai_career_platform.ai_providers.factory`)
- Secret Scanning & Input Validation (`ai_career_platform.security`, `ai_career_platform.utils.validators`)

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
cp .env.example .env
# set at least one AI provider key in .env
python -m ai_career_platform.main
```

## Configuration

See `.env.example` for all supported environment variables:

- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` / `OLLAMA_API_KEY` + `OLLAMA_BASE_URL`
- `SERPER_API_KEY` (for CrewAI tools if using `resume_crew`)
- `SECRET_KEY` — must be set to a secure random value
- `DATABASE_URL` — defaults to `sqlite:///./career_platform.db`
- `DEBUG` / `LOG_LEVEL`

## Architecture

Modular Python package under `src/ai_career_platform`.

Key modules:

- `core/ats_engine.py` — deterministic ATS scoring with section detection, keyword density, and formatting risk.
- `core/job_matcher.py` — keyword overlap scoring with skill gap analysis.
- `interview/interview_module.py` — LLM-driven interview prep generation with JSON fallback parsing.
- `career/career_dashboard.py` — LLM-driven career roadmap generation with JSON fallback parsing.
- `analytics/analytics_tracker.py` — JSONL persistence for ATS/job-match/resume-optimization events with trend queries.
- `ai_providers/` — `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, `OllamaProvider` behind `get_llm_provider()` factory.
- `security.py` — `SecretScanner` with precompiled regex patterns for common token leakage.
- `utils/validators.py` — input validation, filename sanitization, secret redaction.

The `resume_crew` CrewAI integration remains available under `src/resume_crew/` for crew-based resume optimization workflows.

## Running Tests

```bash
pytest
```

Coverage target: >= 70%.