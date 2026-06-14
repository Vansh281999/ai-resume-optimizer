from ai_career_platform.analytics.analytics_tracker import AnalyticsTracker
from ai_career_platform.models import AnalyticsEvent
from datetime import datetime

tracker = AnalyticsTracker()
tracker.record(AnalyticsEvent(event_type="ats_score", timestamp=datetime.utcnow(), data={"overall_score": 88}))
tracker.record(AnalyticsEvent(event_type="job_match", timestamp=datetime.utcnow(), data={"match_score": 72}))
events = tracker.load({"event_type": "ats_score"})
assert len(events) == 1
assert events[0]["data"]["overall_score"] == 88
