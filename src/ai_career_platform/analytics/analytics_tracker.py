import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional
from ..models import AnalyticsEvent, HistoryRecord

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

    def load(self, filters: Optional[Dict] = None) -> List[Dict]:
        events: List[Dict] = []
        if not os.path.exists(self.storage_path):
            return events
        for line in self._lines():
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if not self._match(obj, filters or {}):
                continue
            events.append(obj)
        return events

    def ats_score_trend(self, days: int = 30) -> Dict:
        since = datetime.utcnow().timestamp() - days * 86400
        scores = []
        for ev in self.load({"event_type": "ats_score"}):
            try:
                ts = datetime.fromisoformat(ev["timestamp"]).timestamp()
            except Exception:
                continue
            if ts < since:
                continue
            value = ((ev.get("data") or {}).get("overall_score"))
            if isinstance(value, (int, float)):
                scores.append(float(value))
        if not scores:
            return {"count": 0, "average": 0.0, "min": 0.0, "max": 0.0}
        import statistics
        return {"count": len(scores), "average": round(statistics.mean(scores), 2), "min": min(scores), "max": max(scores)}

    def match_score_trend(self, days: int = 30) -> Dict:
        since = datetime.utcnow().timestamp() - days * 86400
        scores = []
        for ev in self.load({"event_type": "job_match"}):
            try:
                ts = datetime.fromisoformat(ev["timestamp"]).timestamp()
            except Exception:
                continue
            if ts < since:
                continue
            value = ((ev.get("data") or {}).get("match_score"))
            if isinstance(value, (int, float)):
                scores.append(float(value))
        if not scores:
            return {"count": 0, "average": 0.0, "min": 0.0, "max": 0.0}
        import statistics
        return {"count": len(scores), "average": round(statistics.mean(scores), 2), "min": min(scores), "max": max(scores)}

    def improvement_history(self) -> List[Dict]:
        return self.load({"event_type": {"$in": ["ats_score", "job_match", "resume_optimization"]}})

    def _lines(self):
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                for line in f:
                    yield line
        except OSError:
            return []

    @staticmethod
    def _match(obj: Dict, filters: Dict) -> bool:
        for key, value in filters.items():
            if isinstance(value, dict) and "$in" in value:
                if obj.get(key) not in value["$in"]:
                    return False
                continue
            if obj.get(key) != value:
                return False
        return True
