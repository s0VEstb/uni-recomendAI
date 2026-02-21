from starlette.middleware.cors import CORSMiddleware

from app.admin import setup_admin
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging.config
from app.core.config import settings
from app.utils.logging import LOGGING_CONFIG

from app.api.routes import router as health_router


logging.config.dictConfig(LOGGING_CONFIG)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Service is starting up...")
    
    yield
    
    logging.info("Service is shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    setup_admin(app)
    return app

app = create_app()
app.include_router(health_router, prefix="/api")