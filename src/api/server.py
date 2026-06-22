import os
import sys
import json
import time
import uuid
import logging
import secrets
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Callable

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from pydantic import ValidationError as PydanticValidationError
from jose import JWTError, jwt, ExpiredSignatureError
import bcrypt
import bcrypt
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
try:
    import openai as _openai_pkg
    HAS_OPENAI = True
except Exception:
    HAS_OPENAI = False

from ai_career_platform.config import settings as _global_settings
from ai_career_platform.core.ats_engine import ATSScoringEngine
from ai_career_platform.core.job_matcher import JobMatcher
from ai_career_platform.interview.interview_module import InterviewPrepModule
from ai_career_platform.career.career_dashboard import CareerDashboard
from ai_career_platform.ai_providers.factory import get_llm_provider, get_multi_provider
from ai_career_platform.analytics.analytics_tracker import AnalyticsTracker
from ai_career_platform.security import SecretScanner
from ai_career_platform.utils.validators import redact, validate_input
from ai_career_platform.db.session import get_db, init_db as _init_db
from ai_career_platform.db.models import User, PasswordResetToken

OUTPUT_DIR = Path(__file__).resolve().parent.parent.parent / "output"


def _load_fallback(name: str) -> Dict[str, Any]:
    path = OUTPUT_DIR / name
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _extract_text(filename: str, ext: str, contents: bytes) -> str:
    from ai_career_platform.services.resume_parser import ResumeIngestionPipeline

    pipeline = ResumeIngestionPipeline()
    return pipeline.clean_text(pipeline.extract_text(contents, filename))


def _validate_resume_upload(filename: str, content: bytes, content_type: str, max_size: int) -> str:
    from ai_career_platform.services.resume_parser import ResumeFileValidationError, ResumeIngestionPipeline

    try:
        return ResumeIngestionPipeline().validate_file(filename, content, content_type, max_size)
    except ResumeFileValidationError:
        raise


logger = logging.getLogger("ai_career_platform")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    ))
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


def _make_rate_limiter():
    try:
        from slowapi import Limiter
        from slowapi.util import get_remote_address
        limiter = Limiter(key_func=get_remote_address)
        return limiter, True
    except ImportError:
        return None, False


def create_app(overridden_settings=None) -> FastAPI:
    settings = overridden_settings or _global_settings

    if not settings.SECRET_KEY or settings.SECRET_KEY in ("replace-me-with-a-secure-secret", "dev-secret-change-me"):
        raise RuntimeError(
            "SECRET_KEY must be set. "
            "Generate: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )

    limiter, has_rate_limit = _make_rate_limiter()
    application = FastAPI(title="AI Career Intelligence Platform", version="2.0.0")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "https://vansh281999.github.io,https://ai-resume-optimizer-dium.onrender.com,http://localhost:5173,http://localhost:5174").split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    @application.on_event("startup")
    def _startup():
        _init_db()

    _oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)
    _secret = settings.SECRET_KEY
    _algorithm = "HS256"
    _access_hours = settings.get("ACCESS_TOKEN_EXPIRE_HOURS", 24) if isinstance(settings, dict) else getattr(settings, "ACCESS_TOKEN_EXPIRE_HOURS", 24) or 24
    _reset_hours = 1
    _max_upload = settings.MAX_UPLOAD_SIZE_BYTES if hasattr(settings, "MAX_UPLOAD_SIZE_BYTES") else 10 * 1024 * 1024
    _allowed_ext = settings.allowed_upload_extensions_set if hasattr(settings, "allowed_upload_extensions_set") else {".pdf", ".docx", ".txt"}

    def _hash_pw(password: str) -> str:
        return bcrypt.hashpw(password[:72].encode(), bcrypt.gensalt()).decode()

    def _verify_pw(plain: str, hashed: str) -> bool:
        try:
            return bcrypt.checkpw(plain.encode(), hashed.encode())
        except (ValueError, TypeError):
            return False

    def _create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        payload = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=int(_access_hours)))
        payload.update({"exp": expire.timestamp(), "iat": datetime.now(timezone.utc).timestamp()})
        return jwt.encode(payload, _secret, algorithm=_algorithm)

    def _create_reset_token(user_id: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(hours=_reset_hours)
        payload = {"sub": user_id, "type": "password_reset", "exp": expire.timestamp(), "iat": datetime.now(timezone.utc).timestamp()}
        return jwt.encode(payload, _secret, algorithm=_algorithm)

    def _decode_reset_token(token: str) -> Dict[str, Any]:
        try:
            payload = jwt.decode(token, _secret, algorithms=[_algorithm])
            if payload.get("type") != "password_reset":
                raise JWTError("Invalid token type")
            return payload
        except ExpiredSignatureError:
            raise HTTPException(status_code=400, detail="Reset token has expired")
        except JWTError:
            raise HTTPException(status_code=400, detail="Invalid reset token")

    async def _current_user(
        request: Request,
        token: Optional[str] = Depends(_oauth2_scheme),
        db: Session = Depends(get_db),
    ) -> Optional[Dict]:
        if not token:
            return None
        try:
            payload = jwt.decode(token, _secret, algorithms=[_algorithm])
            exp = payload.get("exp")
            if exp is not None and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return None
            user_id = payload.get("sub")
            if not user_id:
                return None
            user = db.get(User, user_id)
            if not user:
                return None
            return {"sub": user.id, "email": user.email, "name": user.name}
        except (ExpiredSignatureError, JWTError):
            return None

    def _require_auth(payload: Optional[Dict] = Depends(_current_user)) -> Dict:
        if payload is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return payload

    @application.middleware("http")
    async def _request_id_mw(request: Request, call_next: Callable) -> JSONResponse:
        rid = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-ID"] = rid
        return response

    @application.exception_handler(Exception)
    async def _generic_handler(request: Request, exc: Exception) -> JSONResponse:
        rid = getattr(request.state, "request_id", "unknown")
        logger.error("unhandled_exception request_id=%s error=%s", rid, exc, exc_info=True)
        return JSONResponse(status_code=500, content={"detail": "Internal server error", "request_id": rid})

    @application.exception_handler(PydanticValidationError)
    async def _validation_handler(request: Request, exc: PydanticValidationError) -> JSONResponse:
        rid = getattr(request.state, "request_id", "unknown")
        return JSONResponse(status_code=422, content={"detail": "Validation error", "errors": exc.errors(), "request_id": rid})

    # ---- Auth ----
    class _LoginReq(BaseModel):
        email: str
        password: str

    class _SignupReq(BaseModel):
        name: str
        email: str
        password: str = Field(min_length=8)

    class _TokenResp(BaseModel):
        access_token: str
        token_type: str = "bearer"
        user: Dict[str, Any]

    @application.post("/api/auth/signup", response_model=_TokenResp, status_code=201)
    def signup(req: _SignupReq, db: Session = Depends(get_db)):
        email = req.email.strip().lower()
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        user_id = f"user_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        user = User(id=user_id, name=req.name.strip(), email=email, password_hash=_hash_pw(req.password))
        db.add(user)
        db.commit()
        db.refresh(user)
        token = _create_access_token({"sub": user.id, "email": user.email, "name": user.name})
        return _TokenResp(access_token=token, user={"id": user.id, "name": user.name, "email": user.email})

    @application.post("/api/auth/login", response_model=_TokenResp)
    def login(req: _LoginReq, db: Session = Depends(get_db)):
        email = req.email.strip().lower()
        user = db.query(User).filter(User.email == email).first()
        if not user or not _verify_pw(req.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        token = _create_access_token({"sub": user.id, "email": user.email, "name": user.name})
        return _TokenResp(access_token=token, user={"id": user.id, "name": user.name, "email": user.email})

    @application.get("/api/auth/me")
    def get_me(payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        user = db.get(User, payload["sub"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.id, "name": user.name, "email": user.email, "created_at": user.created_at.isoformat()}

    class _UpdateProfileReq(BaseModel):
        name: Optional[str] = None
        email: Optional[str] = None

    @application.patch("/api/auth/me")
    def update_profile(req: _UpdateProfileReq, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        user = db.get(User, payload["sub"])
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if req.name is not None:
            user.name = req.name.strip()
        if req.email is not None:
            email = req.email.strip().lower()
            existing = db.query(User).filter(User.email == email, User.id != user.id).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")
            user.email = email
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"id": user.id, "name": user.name, "email": user.email, "created_at": user.created_at.isoformat()}

    class _ForgotPwReq(BaseModel):
        email: str

    @application.post("/api/auth/forgot-password")
    def forgot_password(req: _ForgotPwReq, db: Session = Depends(get_db)):
        email = req.email.strip().lower()
        user = db.query(User).filter(User.email == email).first()
        if user:
            raw_token = _create_reset_token(user.id)
            expires = datetime.now(timezone.utc) + timedelta(hours=_reset_hours)
            db.add(PasswordResetToken(id=f"rt_{uuid.uuid4().hex}", user_id=user.id, token=raw_token, expires_at=expires))
            db.commit()
        return {"message": "If the email exists, a password reset was initiated."}

    class _ResetPwReq(BaseModel):
        token: str
        new_password: str = Field(min_length=8)

    @application.post("/api/auth/reset-password")
    def reset_password(req: _ResetPwReq, db: Session = Depends(get_db)):
        payload = _decode_reset_token(req.token)
        user_id = payload.get("sub")
        from sqlalchemy import select
        now = datetime.now(timezone.utc)
        entry = db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token == req.token,
                PasswordResetToken.used == False,
                PasswordResetToken.expires_at > now,
                PasswordResetToken.user_id == user_id,
            )
        ).scalar_one_or_none()
        if not entry:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        user = db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.password_hash = _hash_pw(req.new_password)
        entry.used = True
        db.add(user)
        db.add(entry)
        db.commit()
        return {"message": "Password updated successfully"}

    class _ChangePwReq(BaseModel):
        current_password: str = Field(min_length=1)
        new_password: str = Field(min_length=8)

    @application.patch("/api/auth/change-password")
    def change_password(req: _ChangePwReq, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        user = db.get(User, payload["sub"])
        if not user or not _verify_pw(req.current_password, user.password_hash):
            raise HTTPException(status_code=401, detail="Current password is incorrect")
        user.password_hash = _hash_pw(req.new_password)
        db.add(user)
        db.commit()
        return {"message": "Password changed successfully"}

    # ---- ATS ----
    class _ATSReq(BaseModel):
        resume_text: str = Field(min_length=1, max_length=settings.MAX_INPUT_LENGTH if hasattr(settings, "MAX_INPUT_LENGTH") else 50000)
        job_keywords: Optional[List[str]] = None

    @application.post("/api/ats/score")
    def ats_score(req: _ATSReq, request: Request, payload: Optional[Dict] = Depends(_current_user)):
        engine = ATSScoringEngine()
        report = engine.score(req.resume_text, job_keywords=req.job_keywords)
        if payload:
            tracker = AnalyticsTracker()
            tracker.record(type("Event", (), {"event_type": "ats_score", "timestamp": datetime.now(timezone.utc),
                "data": {"overall_score": report.overall_score, "user_id": payload.get("sub"), "focus_areas": report.focus_areas}})())
        return report.model_dump()

    @application.post("/api/ats/upload")
    async def ats_upload(request: Request, file: UploadFile = File(...), keywords: str = "", additional_text: str = "", payload: Optional[Dict] = Depends(_current_user), db: Session = Depends(get_db)):
        from ai_career_platform.services.resume_parser import ResumeFileValidationError, ResumeIngestionError
        filename = file.filename or "uploaded"
        content_type = file.content_type or ""
        try:
            content = await file.read()
            _validate_resume_upload(filename, content, content_type, _max_upload)
            ext = os.path.splitext(filename)[1].lower()
            text = _extract_text(filename, ext, content)
        except ResumeFileValidationError as exc:
            raise HTTPException(status_code=415, detail=str(exc))
        except ResumeIngestionError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        if not text.strip():
            raise HTTPException(status_code=422, detail="Could not extract readable text from file")
        if additional_text.strip():
            text = text + "\n\n" + additional_text
        parsed_keywords = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else []
        engine = ATSScoringEngine()
        report = engine.score(text, job_keywords=parsed_keywords)
        if payload:
            tracker = AnalyticsTracker()
            tracker.record(type("Event", (), {"event_type": "ats_score", "timestamp": datetime.now(timezone.utc),
                "data": {"overall_score": report.overall_score, "user_id": payload.get("sub"), "focus_areas": report.focus_areas}})())
        return report.model_dump()

    # ---- Jobs ----
    class _JobMatchReq(BaseModel):
        resume_text: str = Field(min_length=1, max_length=settings.MAX_INPUT_LENGTH if hasattr(settings, "MAX_INPUT_LENGTH") else 50000)
        job_description: str = Field(min_length=1, max_length=settings.MAX_INPUT_LENGTH if hasattr(settings, "MAX_INPUT_LENGTH") else 50000)
        job_keywords: Optional[List[str]] = None

    @application.post("/api/jobs/match")
    def job_match(req: _JobMatchReq, request: Request, payload: Optional[Dict] = Depends(_current_user)):
        matcher = JobMatcher()
        try:
            report = matcher.match(req.resume_text, req.job_description, job_keywords=req.job_keywords)
            if payload:
                tracker = AnalyticsTracker()
                tracker.record(type("Event", (), {"event_type": "job_match", "timestamp": datetime.now(timezone.utc),
                    "data": {"overall_match_score": report.overall_match_score, "user_id": payload.get("sub")}})())
            return report.model_dump()
        except Exception as exc:
            logger.error("job_match_error error=%s", exc)
            raise HTTPException(status_code=502, detail="Job matching service error")

    # ---- Interview ----
    class _InterviewReq(BaseModel):
        company: str
        role: str
        job_description: str = ""

    class _InterviewAnswerReq(BaseModel):
        question: str
        category: str = "interview"
        context: str = ""

    @application.post("/api/interview/generate")
    def interview_generate(req: _InterviewReq, request: Request, payload: Optional[Dict] = Depends(_current_user)):
        validate_input("company", req.company)
        validate_input("role", req.role)
        try:
            module = InterviewPrepModule(provider="gemini")
            report = module.generate(req.company, req.role, req.job_description)
            return report.model_dump()
        except Exception as exc:
            logger.error("interview_error error=%s", exc)
            raise HTTPException(status_code=503, detail="Interview service temporarily unavailable")

    class _InterviewAnswerReq(BaseModel):
        question: str
        category: str = "interview"
        context: Dict[str, str] = Field(default_factory=dict)

    @application.post("/api/interview/answer")
    def interview_answer(req: _InterviewAnswerReq, request: Request, payload: Optional[Dict] = Depends(_current_user)):
        try:
            provider = get_llm_provider("gemini")
            context_lines = [f"{k}: {v}" for k, v in (req.context or {}).items() if v]
            context_text = "\n".join(context_lines) if context_lines else "None provided"
            prompt = (
                "You are an interview coach answering a candidate's question. "
                "Return a concise, actionable, personalized answer grounded in the provided context. "
                "If the question asks for code or an example, provide a short concrete example.\n\n"
                f"Question:\n{req.question}\n\n"
                f"Category:\n{req.category}\n\n"
                f"Context:\n{context_text}"
            )
            answer = provider.generate([{"role": "user", "content": prompt}], timeout=90, retries=2)
            return {"answer": answer}
        except Exception as exc:
            logger.error("interview_answer_error error=%s", exc)
            raise HTTPException(status_code=503, detail="Answer generation unavailable")

    # ---- Profile ----
    class _ProfileUpdateReq(BaseModel):
        full_name: Optional[str] = None
        email: Optional[str] = None
        phone: Optional[str] = None
        location: Optional[str] = None
        linkedin_url: Optional[str] = None
        github_url: Optional[str] = None
        portfolio_url: Optional[str] = None
        headline: Optional[str] = None
        summary: Optional[str] = None
        career_objective: Optional[str] = None

    class _ProfileEducationReq(BaseModel):
        id: Optional[str] = None
        degree: Optional[str] = None
        specialization: Optional[str] = None
        institution: Optional[str] = None
        start_date: Optional[str] = None
        end_date: Optional[str] = None
        cgpa: Optional[str] = None
        description: Optional[str] = None

    class _ProfileExperienceReq(BaseModel):
        id: Optional[str] = None
        title: Optional[str] = None
        company: Optional[str] = None
        location: Optional[str] = None
        start_date: Optional[str] = None
        end_date: Optional[str] = None
        responsibilities: Optional[str] = None
        achievements: Optional[str] = None

    class _ProfileProjectReq(BaseModel):
        id: Optional[str] = None
        project_name: Optional[str] = None
        description: Optional[str] = None
        technologies: Optional[str] = None
        github_url: Optional[str] = None
        live_url: Optional[str] = None
        start_date: Optional[str] = None
        end_date: Optional[str] = None

    class _ProfileSkillReq(BaseModel):
        category: Optional[str] = None
        skill_name: Optional[str] = None

    class _ProfileCertificationReq(BaseModel):
        id: Optional[str] = None
        certification_name: Optional[str] = None
        issuer: Optional[str] = None
        issue_date: Optional[str] = None
        expiry_date: Optional[str] = None
        credential_url: Optional[str] = None

    class _ProfileJobPrefReq(BaseModel):
        preferred_roles: Optional[str] = None
        preferred_locations: Optional[str] = None
        work_mode: Optional[str] = None
        expected_salary_min: Optional[float] = None
        expected_salary_max: Optional[float] = None

    class _EducationPatchReq(BaseModel):
        item: _ProfileEducationReq

    class _ExperiencePatchReq(BaseModel):
        item: _ProfileExperienceReq

    class _ProjectPatchReq(BaseModel):
        item: _ProfileProjectReq

    class _SkillPatchReq(BaseModel):
        item: _ProfileSkillReq

    class _CertificationPatchReq(BaseModel):
        item: _ProfileCertificationReq

    class _JobPrefPatchReq(BaseModel):
        item: _ProfileJobPrefReq

    class _OnboardingStatusReq(BaseModel):
        onboarded: bool

    @application.get("/api/profile")
    def get_profile(payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile, Education, Experience, Project, Skill, Certification, JobPreference
        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
        if not profile:
            return {
                "profile": None,
                "completeness": 0,
                "onboarded": False,
                "education": [],
                "experience": [],
                "projects": [],
                "skills": [],
                "certifications": [],
                "job_preferences": None,
            }
        def _row_to_dict(obj):
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        return {
            "profile": _row_to_dict(profile),
            "completeness": profile.completion_score,
            "onboarded": True,
            "education": [_row_to_dict(e) for e in db.query(Education).filter(Education.profile_id == profile.id).all()],
            "experience": [_row_to_dict(e) for e in db.query(Experience).filter(Experience.profile_id == profile.id).all()],
            "projects": [_row_to_dict(p) for p in db.query(Project).filter(Project.profile_id == profile.id).all()],
            "skills": [_row_to_dict(s) for s in db.query(Skill).filter(Skill.profile_id == profile.id).all()],
            "certifications": [_row_to_dict(c) for c in db.query(Certification).filter(Certification.profile_id == profile.id).all()],
            "job_preferences": _row_to_dict(db.query(JobPreference).filter(JobPreference.profile_id == profile.id).first()) if db.query(JobPreference).filter(JobPreference.profile_id == profile.id).first() else None,
        }

    @application.put("/api/profile")
    def update_profile(req: _ProfileUpdateReq, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile
        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
        if not profile:
            profile = UserProfile(id=f"profile_{uuid.uuid4().hex}", user_id=payload.get("sub"))
            db.add(profile)
        updates = req.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(profile, field, value)
        profile.completion_score = _calculate_completion(profile)
        db.commit()
        db.refresh(profile)
        return {"profile": _profile_to_dict(profile), "completeness": profile.completion_score, "onboarded": True}

    def _assert_profile_owner(profile_id: str, payload: Dict, db: Session):
        from ai_career_platform.db.models import UserProfile
        profile = db.get(UserProfile, profile_id)
        if not profile or profile.user_id != payload.get("sub"):
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

    @application.post("/api/profile/onboarding")
    def onboarding_status(req: _OnboardingStatusReq, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile
        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
        if not profile:
            profile = UserProfile(id=f"profile_{uuid.uuid4().hex}", user_id=payload.get("sub"))
            db.add(profile)
        return {"onboarded": bool(req.onboarded)}

    @application.post("/api/profile/education")
    def add_education(req: _ProfileEducationReq, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile, Education
        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Complete onboarding first")
        item = Education(id=f"edu_{uuid.uuid4().hex}", profile_id=profile.id, **req.model_dump(exclude_unset=True))
        db.add(item)
        db.commit()
        db.refresh(item)
        return _row_to_dict(item)

    @application.post("/api/profile/experience")
    def add_experience(req: _ProfileExperienceReq, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile, Experience
        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Complete onboarding first")
        item = Experience(id=f"exp_{uuid.uuid4().hex}", profile_id=profile.id, **req.model_dump(exclude_unset=True))
        db.add(item)
        db.commit()
        db.refresh(item)
        return _row_to_dict(item)

    @application.post("/api/profile/projects")
    def add_project(req: _ProfileProjectReq, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile, Project
        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Complete onboarding first")
        item = Project(id=f"proj_{uuid.uuid4().hex}", profile_id=profile.id, **req.model_dump(exclude_unset=True))
        db.add(item)
        db.commit()
        db.refresh(item)
        return _row_to_dict(item)

    @application.post("/api/profile/skills")
    def add_skill(req: _ProfileSkillReq, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile, Skill
        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Complete onboarding first")
        item = Skill(id=f"skill_{uuid.uuid4().hex}", profile_id=profile.id, **req.model_dump(exclude_unset=True))
        db.add(item)
        db.commit()
        db.refresh(item)
        return _row_to_dict(item)

    @application.post("/api/profile/certifications")
    def add_certification(req: _ProfileCertificationReq, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile, Certification
        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Complete onboarding first")
        item = Certification(id=f"cert_{uuid.uuid4().hex}", profile_id=profile.id, **req.model_dump(exclude_unset=True))
        db.add(item)
        db.commit()
        db.refresh(item)
        return _row_to_dict(item)

    @application.post("/api/profile/job-preferences")
    def add_job_preferences(req: _ProfileJobPrefReq, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile, JobPreference
        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Complete onboarding first")
        existing = db.query(JobPreference).filter(JobPreference.profile_id == profile.id).first()
        if existing:
            for field, value in req.model_dump(exclude_unset=True).items():
                setattr(existing, field, value)
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return _row_to_dict(existing)
        item = JobPreference(id=f"jp_{uuid.uuid4().hex}", profile_id=profile.id, **req.model_dump(exclude_unset=True))
        db.add(item)
        db.commit()
        db.refresh(item)
        return _row_to_dict(item)

    @application.post("/api/profile/upload-resume")
    async def upload_resume(request: Request, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile, ResumeVersion
        from ai_career_platform.services.resume_parser import ResumeFileValidationError, ResumeIngestionError
        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
        if not profile:
            raise HTTPException(status_code=400, detail="Complete onboarding first")
        try:
            form = await request.form()
            file = _get_uploaded_file(form)
            content = await file.read()
            _validate_resume_upload(getattr(file, "filename", "resume"), content, getattr(file, "content_type", ""), _max_upload)
            logger.info("resume_upload_received filename=%s content_type=%s size=%s", getattr(file, "filename", "resume"), getattr(file, "content_type", ""), len(content))
            version = ResumeVersion(
                id=f"rv_{uuid.uuid4().hex}",
                profile_id=profile.id,
                original_filename=getattr(file, "filename", "upload.bin"),
                storage_path=getattr(file, "filename", "upload.bin"),
                parsed_json=None,
                version_number=(db.query(ResumeVersion).filter(ResumeVersion.profile_id == profile.id).count() + 1),
            )
            db.add(version)
            db.commit()
            db.refresh(version)
            return {"version": _row_to_dict(version)}
        except HTTPException:
            raise
        except ResumeFileValidationError as exc:
            raise HTTPException(status_code=415, detail=str(exc))
        except ResumeIngestionError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        except Exception as exc:
            logger.error("resume_upload_error error=%s", exc)
            raise HTTPException(status_code=400, detail="Invalid upload")

    @application.post("/api/profile/parse-resume")
    async def parse_resume_endpoint(request: Request, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile, ResumeVersion
        from ai_career_platform.services.resume_parser import ResumeFileValidationError, ResumeIngestionError, ResumeIngestionPipeline
        rid = getattr(request.state, "request_id", "unknown")
        try:
            form = await request.form()
            file = _get_uploaded_file(form)
            filename = getattr(file, "filename", "resume")
            content = await file.read()
            logger.info("parse_resume request_id=%s filename=%s content_type=%s size=%s", rid, filename, getattr(file, "content_type", ""), len(content))
            _validate_resume_upload(filename, content, getattr(file, "content_type", ""), _max_upload)
            logger.info("parse_resume validated request_id=%s", rid)
            result = ResumeIngestionPipeline().ingest(content, filename, getattr(file, "content_type", ""), _max_upload)
            logger.info("parse_resume success request_id=%s text_chars=%s", rid, result.get("metadata", {}).get("text_chars"))
            profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
            if not profile:
                profile = UserProfile(id=f"profile_{uuid.uuid4().hex}", user_id=payload.get("sub"))
                db.add(profile)
            version = ResumeVersion(
                id=f"rv_{uuid.uuid4().hex}",
                profile_id=profile.id,
                original_filename=filename,
                storage_path=filename,
                parsed_json=json.dumps(result["structured_resume"], default=str),
                version_number=(db.query(ResumeVersion).filter(ResumeVersion.profile_id == profile.id).count() + 1),
            )
            db.add(version)
            db.commit()
            db.refresh(version)
            return {"parsed": result["parsed"], "structured_resume": result["structured_resume"], "version": _row_to_dict(version), "metadata": result["metadata"]}
        except HTTPException:
            logger.warning("parse_resume http_error request_id=%s", rid, exc_info=True)
            raise
        except ResumeFileValidationError as exc:
            logger.warning("parse_resume validation_error request_id=%s error=%s", rid, exc)
            raise HTTPException(status_code=415, detail=str(exc))
        except ResumeIngestionError as exc:
            logger.error("parse_resume ingestion_error request_id=%s error=%s", rid, exc, exc_info=True)
            raise HTTPException(status_code=503, detail=str(exc))
        except ValueError as exc:
            logger.error("parse_resume validation_error request_id=%s error=%s", rid, exc, exc_info=True)
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            logger.error("parse_resume unhandled_error request_id=%s error=%s", rid, exc, exc_info=True)
            raise HTTPException(status_code=503, detail="Resume parser service temporarily unavailable. Please try again later.")

    @application.post("/api/profile/compare-resume")
    async def compare_resume(request: Request, payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile
        from ai_career_platform.services.resume_parser import ResumeFileValidationError, ResumeIngestionError, ResumeIngestionPipeline
        try:
            form = await request.form()
            file = _get_uploaded_file(form)
            filename = getattr(file, "filename", "resume")
            content = await file.read()
            _validate_resume_upload(filename, content, getattr(file, "content_type", ""), _max_upload)
            logger.info("resume_compare_received filename=%s content_type=%s size=%s", filename, getattr(file, "content_type", ""), len(content))
            result = ResumeIngestionPipeline().ingest(content, filename, getattr(file, "content_type", ""), _max_upload)
            profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
            current_profile = _profile_to_dict(profile) if profile else None
            changes = _compare_parsed_profile(result["structured_resume"], profile) if profile else []
            return {"changes": changes, "parsed": result["structured_resume"], "current_profile": current_profile, "metadata": result["metadata"]}
        except HTTPException:
            raise
        except ResumeFileValidationError as exc:
            raise HTTPException(status_code=415, detail=str(exc))
        except ResumeIngestionError as exc:
            logger.error("resume_compare_error error=%s", exc)
            raise HTTPException(status_code=503, detail=str(exc))
        except Exception as exc:
            logger.error("resume_compare_error error=%s", exc)
            raise HTTPException(status_code=503, detail="Resume comparison service temporarily unavailable. Please try again later.")

    @application.get("/api/profile/resume-history")
    def resume_history(payload: Dict = Depends(_require_auth), db: Session = Depends(get_db)):
        from ai_career_platform.db.models import UserProfile, ResumeVersion
        profile = db.query(UserProfile).filter(UserProfile.user_id == payload.get("sub")).first()
        if not profile:
            return {"history": []}
        versions = db.query(ResumeVersion).filter(ResumeVersion.profile_id == profile.id).order_by(ResumeVersion.uploaded_at.desc()).all()
        return {"history": [_row_to_dict(v) for v in versions]}

    # ---- Career ----
    class _CareerReq(BaseModel):
        current_skills: List[str]
        target_role: str = Field(min_length=1, max_length=200)
        context: str = ""

    @application.post("/api/career/roadmap")
    def career_roadmap(req: _CareerReq, request: Request, payload: Optional[Dict] = Depends(_current_user)):
        validate_input("target_role", req.target_role)
        current_skills = [s.strip() for s in req.current_skills if s and str(s).strip()][:20]
        try:
            dashboard = CareerDashboard(provider="gemini")
            roadmap = dashboard.roadmap(current_skills, req.target_role, req.context)
            return roadmap.model_dump()
        except Exception as exc:
            logger.error("career_error error=%s", exc)
            raise HTTPException(status_code=503, detail="Career roadmap service temporarily unavailable")

    # ---- Market Intelligence ----
    from dataclasses import asdict

    @application.get("/api/market/jobs")
    def market_jobs(title: str = ""):
        from ai_career_platform.services.job_collector import job_collector
        if not title:
            return {"source": [], "fetched_at": datetime.now(timezone.utc).isoformat(), "confidence": 0, "data": [], "error": "Title parameter required"}
        try:
            jobs = job_collector.collect_jobs(title)
            return {"source": ["remoteok"], "fetched_at": datetime.now(timezone.utc).isoformat(), "confidence": 0.8 if jobs else 0, "data": [asdict(j) for j in jobs], "error": None if jobs else "No jobs found"}
        except Exception as e:
            logger.error("market_jobs error=%s", e)
            return {"source": [], "fetched_at": datetime.now(timezone.utc).isoformat(), "confidence": 0, "data": [], "error": "Market data service unavailable"}

    @application.get("/api/market/skills")
    def market_skills(title: str = ""):
        from ai_career_platform.services.job_collector import job_collector
        from ai_career_platform.services.skill_demand import skill_demand_service
        if not title:
            return {"source": [], "fetched_at": datetime.now(timezone.utc).isoformat(), "confidence": 0, "data": {}, "error": "Title parameter required"}
        try:
            jobs = job_collector.collect_jobs(title)
            demand = skill_demand_service.analyze_demand(jobs)
            return {"source": ["remoteok"], "fetched_at": datetime.now(timezone.utc).isoformat(), "confidence": 0.8 if demand else 0, "data": {k: asdict(v) for k, v in demand.items()}, "error": None}
        except Exception as e:
            logger.error("market_skills error=%s", e)
            return {"source": [], "fetched_at": datetime.now(timezone.utc).isoformat(), "confidence": 0, "data": {}, "error": "Market data service unavailable"}

    @application.get("/api/market/trends")
    def market_trends(title: str = ""):
        from ai_career_platform.services.job_collector import job_collector
        from ai_career_platform.services.skill_demand import market_trend_service
        if not title:
            return {"source": [], "fetched_at": datetime.now(timezone.utc).isoformat(), "confidence": 0, "data": None, "error": "Title parameter required"}
        try:
            jobs = job_collector.collect_jobs(title)
            trend = market_trend_service.analyze_trends(jobs, title)
            return {"source": ["remoteok"], "fetched_at": datetime.now(timezone.utc).isoformat(), "confidence": 0.8 if jobs else 0, "data": asdict(trend), "error": None}
        except Exception as e:
            logger.error("market_trends error=%s", e)
            return {"source": [], "fetched_at": datetime.now(timezone.utc).isoformat(), "confidence": 0, "data": None, "error": "Market data service unavailable"}

    # ---- Analytics ----
    class _AnalyticsEventReq(BaseModel):
        event_type: str = Field(min_length=1, max_length=100)
        data: Dict[str, Any] = Field(default_factory=dict)

    @application.get("/api/analytics/trends")
    def analytics_trends(payload: Dict = Depends(_require_auth)):
        tracker = AnalyticsTracker()
        return {"ats": tracker.ats_score_trend(days=30), "match": tracker.match_score_trend(days=30), "history": tracker.improvement_history()}

    @application.get("/api/analytics/focus-areas")
    def analytics_focus_areas(payload: Dict = Depends(_require_auth)):
        tracker = AnalyticsTracker()
        return {"focus_areas": tracker.get_latest_ats_score(filters={"user_id": payload.get("sub")}).get("focus_areas") or []}

    @application.post("/api/analytics/event")
    def analytics_event(req: _AnalyticsEventReq, request: Request, payload: Dict = Depends(_require_auth)):
        tracker = AnalyticsTracker()
        tracker.record(type("Event", (), {"event_type": req.event_type, "timestamp": datetime.now(timezone.utc), "data": req.data})())
        return {"recorded": True}

    # ---- Security ----
    @application.post("/api/security/scan")
    def security_scan(request: Request, text: Dict[str, str], payload: Dict = Depends(_require_auth)):
        raw = text.get("text", "") or ""
        if len(raw) > (settings.MAX_INPUT_LENGTH if hasattr(settings, "MAX_INPUT_LENGTH") else 50000):
            raise HTTPException(status_code=413, detail="Input too large")
        findings = SecretScanner.scan(raw)
        redacted = redact(raw)
        return {"findings_count": len(findings), "redacted_length": len(redacted)}

    # ---- Health ----
    _has_openai = bool(HAS_OPENAI and settings.OPENAI_API_KEY)

    @application.get("/api/health")
    def health():
        return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

    @application.get("/api/health/ai")
    def ai_health():
        _output = Path(__file__).resolve().parent.parent.parent / "output"
        return {
            "openai": {"installed": HAS_OPENAI, "configured": bool(settings.OPENAI_API_KEY), "status": "ok" if HAS_OPENAI and settings.OPENAI_API_KEY else "unavailable"},
            "anthropic": {"installed": True, "configured": bool(settings.ANTHROPIC_API_KEY), "status": "ok" if settings.ANTHROPIC_API_KEY else "unavailable"},
            "gemini": {"installed": True, "configured": bool(settings.GEMINI_API_KEY), "status": "ok" if settings.GEMINI_API_KEY else "unavailable"},
            "ollama": {"installed": True, "configured": True, "status": "ok"},
            "openrouter": {"installed": True, "configured": bool(getattr(settings, "OPENROUTER_API_KEY", "")), "status": "ok" if getattr(settings, "OPENROUTER_API_KEY", "") else "unavailable"},
            "groq": {"installed": True, "configured": bool(getattr(settings, "GROQ_API_KEY", "")), "status": "ok" if getattr(settings, "GROQ_API_KEY", "") else "unavailable"},
        }

    # ---- Static ----
    frontend_dist = Path(__file__).resolve().parent.parent.parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        application.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")

    return application


# Module-level app for uvicorn / docker
app = create_app()


def _row_to_dict(obj):
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def _get_uploaded_file(form) -> Any:
    for value in form.values():
        if hasattr(value, "filename") and value.filename:
            return value
    raise HTTPException(status_code=400, detail="No file uploaded")


def _profile_to_dict(profile) -> Optional[Dict[str, Any]]:
    if not profile:
        return None
    return {
        "full_name": profile.full_name,
        "email": profile.email,
        "phone": profile.phone,
        "location": profile.location,
        "linkedin_url": profile.linkedin_url,
        "github_url": profile.github_url,
        "portfolio_url": profile.portfolio_url,
        "headline": profile.headline,
        "summary": profile.summary,
        "career_objective": profile.career_objective,
        "education": [_row_to_dict(item) for item in profile.education],
        "experience": [_row_to_dict(item) for item in profile.experience],
        "projects": [_row_to_dict(item) for item in profile.projects],
        "skills": [_row_to_dict(item) for item in profile.skills],
        "certifications": [_row_to_dict(item) for item in profile.certifications],
    }


def _compare_parsed_profile(parsed: Dict[str, Any], profile) -> List[str]:
    changes: List[str] = []
    current_skills = {str(item.skill_name).lower(): item for item in profile.skills if item.skill_name}
    for names in (parsed.get("skills") or {}).values():
        for name in names or []:
            if name and str(name).lower() not in current_skills:
                changes.append(f"✓ Added Skill: {name}")

    current_projects = {str(item.project_name).lower(): item for item in profile.projects if item.project_name}
    for project in parsed.get("projects") or []:
        project_name = project.get("project_name")
        if project_name and str(project_name).lower() not in current_projects:
            changes.append(f"✓ New Project: {project_name}")

    current_education = {(item.degree or "").lower(), (item.institution or "").lower(), (item.cgpa or "").lower()}
    for education in parsed.get("education") or []:
        cgpa = education.get("cgpa")
        if cgpa and str(cgpa).lower() not in current_education:
            changes.append(f"✓ Updated Education: {education.get('degree') or 'Degree'} at {education.get('institution') or 'Institution'} CGPA {cgpa}")

    personal_fields = {
        "full_name": "Name",
        "email": "Email",
        "phone": "Phone",
        "location": "Location",
        "linkedin_url": "LinkedIn",
        "github_url": "GitHub",
        "portfolio_url": "Portfolio",
    }
    for key, label in personal_fields.items():
        old_value = getattr(profile, key, "") or ""
        new_value = (parsed.get("personal_info") or {}).get(key) or ""
        if new_value and str(old_value).lower() != str(new_value).lower():
            changes.append(f"✓ Updated {label}: {old_value} → {new_value}")

    return changes or ["No changes detected"]
