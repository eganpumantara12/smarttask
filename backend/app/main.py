import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, text

from .config import settings
from .database import Base, SessionLocal, engine, ensure_columns
from .logging_conf import log_event, setup_logging
from .models import User
from .routers import admin, auth, courses, me, tasks
from .security import hash_password

setup_logging(settings.log_level)
log = logging.getLogger("smarttask")


def seed_admin() -> None:
    if not (settings.admin_email and settings.admin_password):
        return
    with SessionLocal() as db:
        email = settings.admin_email.lower()
        if db.scalar(select(User).where(User.email == email)) is None:
            db.add(
                User(
                    name=settings.admin_name,
                    email=email,
                    password_hash=hash_password(settings.admin_password),
                    role="admin",
                )
            )
            db.commit()
            log.info("akun admin awal dibuat")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    ensure_columns()
    seed_admin()
    yield


app = FastAPI(
    title="SmartTask API",
    description="Sistem Pengelolaan Tugas Mahasiswa (Komputasi Awan, Kelompok 7).",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def access_log(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path != "/api/health":
        log_event(
            logging.getLogger("smarttask.access"),
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            ms=round((time.perf_counter() - start) * 1000, 1),
        )
    return response


@app.get("/api/health", tags=["system"])
def health():
    """Health check untuk Docker/monitoring: memastikan API hidup dan database dapat dijangkau."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        log.exception("health check database gagal")
        from fastapi.responses import JSONResponse

        return JSONResponse({"status": "error", "database": "down"}, status_code=503)
    return {"status": "ok", "database": "up"}


app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(tasks.router)
app.include_router(me.router)
app.include_router(admin.router)
