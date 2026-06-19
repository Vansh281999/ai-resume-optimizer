import os
import sys
import json
import io
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
from passlib.context import CryptContext
from passlib.exc import UnknownHashError
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
    try:
        if ext == ".pdf":
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(contents)) as pdf:
                    return "\n".join(page.extract_text() or "" for page in pdf.pages)
            except Exception:
                return ""
        if ext == ".docx":
            try:
                import docx
                doc = docx.Document(io.BytesIO(contents))
                return "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                return ""
        return contents.decode("utf-8", errors="ignore")
    except Exception:
        return ""


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
        allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:5174").split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )

    @application.on_event("startup")
    def _startup():
        _init_db()

    _pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    _oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)
    _secret = settings.SECRET_KEY
    _algorithm = "HS256"
    _access_hours = settings.get("ACCESS_TOKEN_EXPIRE_HOURS", 24) if isinstance(settings, dict) else getattr(settings, "ACCESS_TOKEN_EXPIRE_HOURS", 24) or 24
    _reset_hours = 1
    _max_upload = settings.MAX_UPLOAD_SIZE_BYTES if hasattr(settings, "MAX_UPLOAD_SIZE_BYTES") else 10 * 1024 * 1024
    _allowed_ext = settings.allowed_upload_extensions_set if hasattr(settings, "allowed_upload_extensions_set") else {".pdf", ".docx", ".txt"}

    def _hash_pw(password: str) -> str:
        return _pwd_context.hash(password)

    def _verify_pw(plain: str, hashed: str) -> bool:
        try:
            return _pwd_context.verify(plain, hashed)
        except UnknownHashError:
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
        filename = file.filename or "uploaded"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in _allowed_ext:
            raise HTTPException(status_code=415, detail=f"Unsupported file type: {ext}")
        content_type = file.content_type or ""
        allowed_content_types = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain", "text/markdown"}
        if content_type not in allowed_content_types:
            raise HTTPException(status_code=415, detail=f"Unsupported content type: {content_type}")
        content = await file.read()
        if len(content) > _max_upload:
            raise HTTPException(status_code=413, detail=f"File exceeds max size of {_max_upload // (1024*1024)} MB")
        text = _extract_text(filename, ext, content)
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