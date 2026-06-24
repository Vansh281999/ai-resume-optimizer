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

## Resume Parser Architecture

The parser uses a dual-strategy approach: **LLM-based parsing** (primary) with **rule-based fallback** for reliability.

### Flow

1. **File Validation** → MIME type, size, extension checks
2. **Text Extraction** → PDF (pdfplumber → pymupdf → pypdf), DOCX (python-docx), TXT
3. **Section Classification** → Regex-based boundary detection (`SectionClassifier`)
4. **Skill Categorization** → 7 categories via `CANONICAL_SKILLS` dictionary
5. **Confidence Scoring** → All fields wrapped with `{"value": str, "confidence": float}`

### Key Classes

| Class | Purpose |
|-------|---------|
| `SectionClassifier` | Detects section boundaries (education, skills, projects, etc.) to prevent bleed |
| `ConfidenceScorer` | Assigns 0.0-1.0 confidence to each extracted field |
| `ResumeIngestionPipeline` | Orchestrates extraction, parsing, and fallback |
| `ResumeParser` | High-level API wrapper |

### Section Bleed Prevention

- Uses `SECTION_BOUNDARIES` regex to identify section headers
- `classify()` maps lines to sections, preventing skills from bleeding into certifications
- Explicit boundary detection for project → certification transitions

### Skill Categories

- `programming_languages` (Python, Java, C++, etc.)
- `frameworks` (React, Django, FastAPI, etc.)
- `databases` (PostgreSQL, MongoDB, Redis, etc.)
- `cloud_technologies` (AWS, Azure, GCP, etc.)
- `devops_tools` (Docker, Kubernetes, Terraform, etc.)
- `ai_ml_technologies` (TensorFlow, PyTorch, LangChain, etc.)
- `soft_skills` (Leadership, Communication, etc.)

### Confidence Scores

| Field | Confidence |
|-------|------------|
| Email, Phone | 0.98, 0.92 |
| Name, Institution | 0.95, 0.92 |
| Experience | 0.85-0.92 |
| Skills, Projects | 0.75-0.88 |

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

## Running Tests

```bash
pytest
```

Coverage target: >= 70%