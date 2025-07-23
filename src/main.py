import structlog
import logging

from sentry_sdk import init as sentry_init
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pathlib import Path
from fastapi.staticfiles import StaticFiles

from core.config import settings
from core.paths import ASSETS_DIR
from utils.log_sender import LogSender
from routes.routes import router as rest_router


logging.basicConfig(level=logging.INFO, format="%(message)s")

sentry_init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=1.0,
)

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

log = structlog.get_logger(__name__)

log_sender = LogSender(
    log_api=settings.LOG_API,
    project_id=settings.LOG_PROJECT_ID,
    upload_delay=120
)


app = FastAPI()
app.add_middleware(SentryAsgiMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajustar conforme política de produção
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")

app.include_router(rest_router)
