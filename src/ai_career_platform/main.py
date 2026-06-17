import sys

from ai_career_platform.core.ats_engine import ATSScoringEngine
from ai_career_platform.core.job_matcher import JobMatcher
from ai_career_platform.interview.interview_module import InterviewPrepModule
from ai_career_platform.career.career_dashboard import CareerDashboard


def main() -> int:
    resume = "Email: user@example.com\nPhone: +1-555-0199\nExperience\nSkills: Python, SQL"
    job = "Looking for Python, SQL, and data engineering experience."

    ats = ATSScoringEngine().score(resume)
    print(f"ATS overall: {ats.overall_score}")
    print(f"Missing sections: {ats.missing_sections}")

    match = JobMatcher().match(resume, job)
    print(f"Match overall: {match.overall_match_score}")
    print(f"Missing skills: {match.missing_skills[:5]}")

    prep = InterviewPrepModule(provider="openai")
    print(f"Interview provider: {prep.provider_name}")

    roadmap = CareerDashboard(provider="openai")
    print(f"Dashboard provider: {roadmap.provider_name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
