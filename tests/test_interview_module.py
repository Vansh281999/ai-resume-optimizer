from ai_career_platform.interview.interview_module import InterviewPrepModule
from ai_career_platform.models import InterviewPrepReport

module = InterviewPrepModule()
report = module.generate(company="Acme", role="Backend Engineer", job_description="Python, Django, REST APIs")
assert isinstance(report, InterviewPrepReport)
assert report.company == "Acme"
assert report.role == "Backend Engineer"
