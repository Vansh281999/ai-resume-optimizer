from ai_career_platform.career.career_dashboard import CareerDashboard
from ai_career_platform.models import CareerRoadmap

dash = CareerDashboard()
roadmap = dash.roadmap(["Python", "SQL"], "Data Engineer", "Python, SQL, Airflow")
assert isinstance(roadmap, CareerRoadmap)
assert roadmap.target_role == "Data Engineer"
