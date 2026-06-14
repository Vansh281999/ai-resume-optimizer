# Architecture

## Core Modules

- `config.py`: Loads runtime settings from environment variables via `pydantic-settings`, including API keys, database URL, secret key, debug mode, and log level.
- `models.py`: Defines Pydantic reports for ATS scoring, job matching, interview preparation, career roadmaps, analytics events, and history records.
- `security.py`: Provides `SecretScanner` patterns for detecting common API tokens, private keys, cloud credentials, database URLs, and password-like values.
- `ai_providers/`: Multi-model LLM provider selection through `factory.py`, with OpenAI, Anthropic, Gemini, and Ollama implementations.
- `core/ats_engine.py`: ATS scoring, section detection, formatting risk, keyword density, and improvement suggestions.
- `core/job_matcher.py`: Resume-job keyword matching, skill gap analysis, and score composition using ATS components.
- `interview/interview_module.py`: Generates interview preparation JSON through an LLM provider and parses question/tip payloads into Pydantic reports.
- `career/career_dashboard.py`: Builds career roadmap JSON through an LLM provider and parses skill progression and salary progression payloads.
- `analytics/analytics_tracker.py`: JSONL event persistence, filtering, ATS score trends, job match trends, and improvement history.
- `analytics/job_process_tracker.py`: Alternate analytics store with event recording, filtering, ATS trend, match-score trend, and improvement history helpers.
- `utils/validators.py`: Input, company name, file extension, and secret-redaction helpers.
- `utils/text.py`: Text normalization, tokenization, file fingerprinting, input validation, filename sanitization, and secret redaction.

## Data Flow

1. Input: resume text, job description, optional keywords, company, role, and context.
2. ATS engine scores resume content and reports sections, risks, issues, and suggestions.
3. Job matcher computes keyword overlap, missing skills, recommended keywords, and match scores.
4. Interview module generates prep content and normalizes it into `InterviewPrepReport`.
5. Career module generates roadmap content and normalizes it into `CareerRoadmap`.
6. Analytics modules persist and query `ats_score`, `job_match`, and `resume_optimization` events.
