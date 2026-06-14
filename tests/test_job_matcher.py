from ai_career_platform.core.job_matcher import ResumeJobMatcher
from ai_career_platform.models import JobMatchReport

matcher = ResumeJobMatcher()
resume = "Python developer with FastAPI, Docker, Kubernetes, SQL, React"
job = "Looking for Python, FastAPI, Docker, Kubernetes, SQL, React, AWS"
out = matcher.match(resume, job)
assert isinstance(out, dict)
assert out["match_score"] >= 0
assert out["match_score"] <= 100
