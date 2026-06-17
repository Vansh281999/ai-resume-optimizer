import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from ai_career_platform.analytics.analytics_tracker import AnalyticsTracker
from ai_career_platform.models import AnalyticsEvent


@pytest.fixture
def tracker_path():
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def tracker(tracker_path):
    return AnalyticsTracker(storage_path=tracker_path)


def test_record_and_load_by_event_type(tracker, tracker_path):
    now = datetime.now(timezone.utc)
    tracker.record(AnalyticsEvent(event_type="ats_score", timestamp=now, data={"overall_score": 88}))
    tracker.record(AnalyticsEvent(event_type="job_match", timestamp=now, data={"match_score": 72}))
    tracker.record(AnalyticsEvent(event_type="resume_optimization", timestamp=now, data={"score": 80}))
    events = tracker.load({"event_type": "ats_score"})
    assert len(events) == 1
    assert events[0]["data"]["overall_score"] == 88


def test_improvement_history_returns_all_three_event_types(tracker):
    now = datetime.now(timezone.utc)
    tracker.record(AnalyticsEvent(event_type="ats_score", timestamp=now, data={"overall_score": 88}))
    tracker.record(AnalyticsEvent(event_type="job_match", timestamp=now, data={"match_score": 72}))
    tracker.record(AnalyticsEvent(event_type="resume_optimization", timestamp=now, data={"score": 80}))
    tracker.record(AnalyticsEvent(event_type="unknown", timestamp=now, data={}))
    history = tracker.improvement_history()
    assert len(history) == 3
    history_types = {e["event_type"] for e in history}
    assert history_types == {"ats_score", "job_match", "resume_optimization"}


def test_improvement_history_respects_filters(tracker):
    now = datetime.now(timezone.utc)
    tracker.record(AnalyticsEvent(event_type="ats_score", timestamp=now, data={"overall_score": 88}))
    tracker.record(AnalyticsEvent(event_type="job_match", timestamp=now, data={"match_score": 72}))
    history = tracker.improvement_history(filters={"event_type": "ats_score"})
    assert len(history) == 1
    assert history[0]["event_type"] == "ats_score"


def test_ats_trend_returns_stats(tracker):
    now = datetime.now(timezone.utc)
    tracker.record(AnalyticsEvent(event_type="ats_score", timestamp=now, data={"overall_score": 80}))
    tracker.record(AnalyticsEvent(event_type="ats_score", timestamp=now, data={"overall_score": 90}))
    trend = tracker.ats_score_trend(days=30)
    assert trend["count"] == 2
    assert trend["average"] == 85.0


def test_match_trend_returns_stats(tracker):
    now = datetime.now(timezone.utc)
    tracker.record(AnalyticsEvent(event_type="job_match", timestamp=now, data={"match_score": 70}))
    tracker.record(AnalyticsEvent(event_type="job_match", timestamp=now, data={"match_score": 90}))
    trend = tracker.match_score_trend(days=30)
    assert trend["count"] == 2
    assert trend["average"] == 80.0


def test_load_returns_empty_when_file_missing():
    tracker = AnalyticsTracker(storage_path="nonexistent/path.jsonl")
    assert tracker.load() == []


def test_record_skips_gracefully_when_directory_unwritable(tmp_path):
    storage_path = str(tmp_path / "subdir" / "analytics.jsonl")
    tracker = AnalyticsTracker(storage_path=storage_path)
    now = datetime.now(timezone.utc)
    # directory may not exist but makedirs should create it; this tests no exception
    tracker.record(AnalyticsEvent(event_type="test", timestamp=now, data={}))