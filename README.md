# AI Career Intelligence Platform

## Project Structure

```
src/ai_career_platform/
├── __init__.py
├── config.py
├── models.py
├── security.py
├── ai_providers/
│   ├── __init__.py
│   ├── base.py
│   ├── factory.py
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   ├── gemini_provider.py
│   └── ollama_provider.py
├── core/
│   ├── __init__.py
│   ├── ats_engine.py
│   └── job_matcher.py
├── interview/
│   ├── __init__.py
│   └── interview_module.py
├── career/
│   ├── __init__.py
│   └── career_dashboard.py
├── analytics/
│   ├── __init__.py
│   ├── analytics_tracker.py
│   └── job_process_tracker.py
└── utils/
    ├── __init__.py
    ├── text.py
    └── validators.py

src/resume_crew/
├── __init__.py
├── main.py
├── crew.py
├── models.py
├── config/
│   ├── agents.yaml
│   └── tasks.yaml
└── tools/
    └── custom_tool.py

tests/
├── test_ats_engine.py
├── test_job_matcher.py
├── test_interview_module.py
├── test_career_dashboard.py
├── test_analytics_tracker.py
└── test_security.py
```

## Installation

```bash
pip install -e ".[dev]"
```

## Environment

Copy `.env.example` to `.env` and set provider keys and runtime settings.

## Usage

- Use `ai_career_platform` as the core library for ATS scoring, resume-job matching, interview preparation, career roadmaps, analytics, validation, and LLM provider selection.
- Use `resume_crew` for the CrewAI-based resume optimization workflow.

## Testing

```bash
pytest
```

## License

MIT
