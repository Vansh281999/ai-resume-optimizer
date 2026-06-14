from ai_career_platform.core.ats_engine import ATSScoringEngine
from ai_career_platform.models import ATSScoreReport

engine = ATSScoringEngine()
report = engine.score("Email: user@example.com\nPhone: +1-555-0199\nExperience\nSkills")
assert report.overall_score >= 0 and report.overall_score <= 100
assert "experience" in report.found_sections
assert "skills" in report.found_sections
