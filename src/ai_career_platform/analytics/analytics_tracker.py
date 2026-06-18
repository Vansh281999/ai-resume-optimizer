import json
import logging
import os
import statistics
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ai_career_platform.models import AnalyticsEvent, HistoryRecord

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    def __init__(self, storage_path: str = "logs/analytics.jsonl"):
        self.storage_path = storage_path
        os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)

    def record(self, event: AnalyticsEvent) -> None:
        try:
            line = json.dumps({
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
            }, default=str)
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except OSError:
            logger.debug("Analytics write skipped: %s", self.storage_path)

    def load(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        if not os.path.exists(self.storage_path):
            return events
        for line in self._lines():
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if not self._matches_filters(obj, filters or {}):
                continue
            events.append(obj)
        return events

    def ats_score_trend(self, days: int = 30, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.load(filters=filters)
        scores: List[float] = []
        for ev in events:
            if ev.get("event_type") != "ats_score":
                continue
            ts = ev.get("timestamp")
            try:
                when = datetime.fromisoformat(ts)
            except Exception:
                continue
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            if when < since:
                continue
            value = ((ev.get("data") or {}).get("overall_score"))
            if isinstance(value, (int, float)):
                scores.append(float(value))
        if not scores:
            return {"window_days": days, "count": 0, "average": 0.0, "min": 0.0, "max": 0.0}
        return {"window_days": days, "count": len(scores), "average": round(statistics.mean(scores), 2), "min": round(min(scores), 2), "max": round(max(scores), 2)}

    def match_score_trend(self, days: int = 30, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        events = self.load(filters=filters)
        scores: List[float] = []
        for ev in events:
            if ev.get("event_type") != "job_match":
                continue
            ts = ev.get("timestamp")
            try:
                when = datetime.fromisoformat(ts)
            except Exception:
                continue
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            if when < since:
                continue
            value = ((ev.get("data") or {}).get("match_score"))
            if isinstance(value, (int, float)):
                scores.append(float(value))
        if not scores:
            return {"window_days": days, "count": 0, "average": 0.0, "min": 0.0, "max": 0.0}
        return {"window_days": days, "count": len(scores), "average": round(statistics.mean(scores), 2), "min": round(min(scores), 2), "max": round(max(scores), 2)}

    def improvement_history(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        allowed = {"ats_score", "job_match", "resume_optimization"}
        return [ev for ev in self.load(filters=filters) if ev.get("event_type") in allowed]

    def _lines(self):
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                for line in f:
                    yield line
        except OSError:
            return []

    def get_latest_ats_score(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        events = self.load(filters=filters)
        for event in reversed(events):
            if event.get("event_type") == "ats_score":
                return event.get("data") or {}
        return {}

    @staticmethod
    def _matches_filters(event: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        for key, value in filters.items():
            if event.get(key) != value:
                return False
        return True