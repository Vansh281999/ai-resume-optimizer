import logging
import os
import re
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ai_career_platform.models import AnalyticsEvent

logger = logging.getLogger(__name__)


class AnalyticsStore:
    def __init__(self, storage_path: str = "logs/analytics.jsonl"):
        self.storage_path = storage_path
        try:
            os.makedirs(os.path.dirname(self.storage_path) or ".", exist_ok=True)
        except OSError:
            pass

    def record(self, event: AnalyticsEvent) -> None:
        try:
            import json
            line = json.dumps({
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data": event.data,
                "session_id": event.session_id,
            }, default=str)
            with open(self.storage_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
            logger.info("Recorded analytics event: %s", event.event_type)
        except OSError:
            logger.debug("Analytics storage unavailable: %s", self.storage_path)

    def load_events(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        if not os.path.exists(self.storage_path):
            return records
        for line in self._iter_lines():
            try:
                obj = __import__("json").loads(line)
            except Exception:
                continue
            if not self._matches_filters(obj, filters or {}):
                continue
            records.append(obj)
        return records

    def ats_trend(self, days: int = 30, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        since = datetime.utcnow() - timedelta(days=days)
        events = self.load_events(filters=filters)
        scores: List[float] = []
        label: str = ""
        for event in events:
            if event.get("event_type") != "ats_score":
                continue
            ts = event.get("timestamp")
            try:
                when = datetime.fromisoformat(ts)
            except Exception:
                continue
            if when < since:
                continue
            value = event.get("data", {}).get("overall_score")
            if isinstance(value, (int, float)):
                scores.append(float(value))
        if not scores:
            return {"window_days": days, "count": 0, "average": 0.0, "min": 0.0, "max": 0.0}
        return {"window_days": days, "count": len(scores), "average": round(statistics.mean(scores), 2), "min": round(min(scores), 2), "max": round(max(scores), 2)}

    def match_score_trend(self, days: int = 30, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        since = datetime.utcnow() - timedelta(days=days)
        events = self.load_events(filters=filters)
        scores: List[float] = []
        for event in events:
            if event.get("event_type") != "job_match":
                continue
            ts = event.get("timestamp")
            try:
                when = datetime.fromisoformat(ts)
            except Exception:
                continue
            if when < since:
                continue
            value = event.get("data", {}).get("match_score")
            if isinstance(value, (int, float)):
                scores.append(float(value))
        if not scores:
            return {"window_days": days, "count": 0, "average": 0.0, "min": 0.0, "max": 0.0}
        return {"window_days": days, "count": len(scores), "average": round(statistics.mean(scores), 2), "min": round(min(scores), 2), "max": round(max(scores), 2)}

    def improvement_history(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        events = self.load_events(filters=filters)
        return [e for e in events if e.get("event_type") in {"ats_score", "job_match", "resume_optimization"}]

    def _iter_lines(self):
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                for line in f:
                    yield line
        except OSError:
            return []

    @staticmethod
    def _matches_filters(event: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        for key, value in filters.items():
            if event.get(key) != value:
                return False
        return True
