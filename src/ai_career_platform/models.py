from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

class ATSScoreReport(BaseModel):
    overall_score: float = Field(ge=0, le=100)
    keyword_density_score: float = Field(ge=0, le=100)
    formatting_risk_score: float = Field(ge=0, le=100)
    missing_sections: List[str] = Field(default_factory=list)
    found_sections: List[str] = Field(default_factory=list)
    critical_issues: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    focus_areas: List[Dict[str, Any]] = Field(default_factory=list)

class JobMatchReport(BaseModel):
    overall_match_score: float = Field(ge=0, le=100)
    skill_match_score: float = Field(ge=0, le=100)
    experience_match_score: float = Field(ge=0, le=100)
    missing_skills: List[str] = Field(default_factory=list)
    recommended_keywords: List[str] = Field(default_factory=list)
    match_details: Dict[str, float] = Field(default_factory=dict)

class InterviewQuestion(BaseModel):
    question: str
    category: str
    difficulty: str = "medium"
    tips: Optional[str] = None

class InterviewPrepReport(BaseModel):
    company: str
    role: str
    technical_questions: List[InterviewQuestion] = Field(default_factory=list)
    behavioral_questions: List[InterviewQuestion] = Field(default_factory=list)
    company_specific_questions: List[InterviewQuestion] = Field(default_factory=list)
    preparation_tips: List[str] = Field(default_factory=list)

class SkillProgression(BaseModel):
    skill_name: str
    current_level: float = Field(ge=0, le=100)
    target_level: float = Field(ge=0, le=100)
    learning_resources: List[str] = Field(default_factory=list)
    estimated_months: int = 3

class CareerRoadmap(BaseModel):
    current_role: str
    target_role: str
    skill_progressions: List[SkillProgression] = Field(default_factory=list)
    estimated_timeline_months: int = 12
    salary_progression: Dict[str, Optional[float]] = Field(default_factory=lambda: {"entry": None, "mid": None, "senior": None})

class AnalyticsEvent(BaseModel):
    event_type: str
    timestamp: datetime = Field(default_factory=_utcnow)
    data: Dict = Field(default_factory=dict)

class HistoryRecord(BaseModel):
    id: str
    event_type: str
    timestamp: datetime = Field(default_factory=_utcnow)
    data: Dict = Field(default_factory=dict)

ATSScoreReport.model_rebuild()
JobMatchReport.model_rebuild()
InterviewQuestion.model_rebuild()
InterviewPrepReport.model_rebuild()
SkillProgression.model_rebuild()
CareerRoadmap.model_rebuild()
AnalyticsEvent.model_rebuild()
HistoryRecord.model_rebuild()
