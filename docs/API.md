# API Documentation

## Settings

`config.Settings()`

Loads environment variables from `.env` and defaults:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `OLLAMA_BASE_URL`
- `DATABASE_URL`
- `SECRET_KEY`
- `DEBUG`
- `LOG_LEVEL`

## LLM Provider Factory

`get_llm_provider(provider, model=None, **kwargs)`

Supported providers:

- `openai` -> `OpenAIProvider(model="gpt-4o-mini")`
- `anthropic` -> `AnthropicProvider(model="claude-3-5-haiku-20241022")`
- `gemini` or `google` -> `GeminiProvider(model="gemini-2.0-flash")`
- `ollama` -> `OllamaProvider(model="llama3", base_url="http://localhost:11434")`

## ATSScoringEngine

`score(text, job_keywords=None) -> ATSScoreReport`

## ResumeJobMatcher

`match(resume_text, job_description, job_keywords=None) -> JobMatchReport`

## InterviewPrepModule

`generate(company, role, job_description="") -> InterviewPrepReport`

## CareerDashboard

`roadmap(current_skills, target_role, context="") -> CareerRoadmap`

## AnalyticsTracker

- `record(event)`
- `load(filters=None)`
- `ats_score_trend(days=30)`
- `match_score_trend(days=30)`
- `improvement_history()`

## AnalyticsStore

- `record(event)`
- `load_events(filters=None)`
- `ats_trend(days=30, filters=None)`
- `match_score_trend(days=30, filters=None)`
- `improvement_history(filters=None)`

## Security

`SecretScanner.scan(text) -> list[str]`

## Validators

- `validate_input(name, value)`
- `validate_company(name)`
- `validate_file_path(path)`
- `redact(text)`

## Text Utilities

- `normalize_text(text)`
- `tokenize(text)`
- `compute_file_fingerprint(path)`
- `validate_input_text(text, max_length=50000)`
- `validate_company_name(name)`
- `sanitize_filename(name)`
- `redact_secrets(text)`
