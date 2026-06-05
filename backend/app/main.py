"""FastAPI entrypoint. Phase 0: serves the contract from an in-memory store,
seeded with sample data when PTV_MOCK_MODE=true. Phase 1 wires the crawler +
scheduler into the lifespan below."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import settings
from .routes import router
from .sample_data import sample_matches
from .store import store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("pimpletv")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.mock_mode:
        store.replace_all(sample_matches())
        log.info("MOCK_MODE: seeded %d sample matches", store.count())
        yield
    else:
        from .scheduler import scheduler  # local import: avoids httpx/apscheduler in mock runs
        await scheduler.start()
        log.info("LIVE mode: crawler + resolver scheduler running")
        try:
            yield
        finally:
            await scheduler.stop()


app = FastAPI(title="PimpleTV TV Launcher API", version="0.1.0", lifespan=lifespan)

# TV app is a LAN client; permissive CORS is fine for a private Pi deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(router)


# Normalize errors to the contract envelope: {"error": {"code", "message"}}.
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and "code" in detail:
        body = {"error": detail}
    else:
        body = {"error": {"code": str(exc.status_code), "message": str(detail)}}
    return JSONResponse(status_code=exc.status_code, content=body)


@app.exception_handler(RequestValidationError)
async def validation_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": str(exc.errors())}},
    )


@app.get("/")
def root():
    return {"name": "PimpleTV TV Launcher API", "version": "0.1.0", "docs": "/docs"}
