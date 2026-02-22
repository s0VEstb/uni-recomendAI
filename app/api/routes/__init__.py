from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.survey import router as survey_router
from app.api.routes.tags import router as tags_router
from app.api.routes.chat import router as chat_router
from app.api.routes.programs import router as programs_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(tags_router, prefix="/tags", tags=["Tags"])
router.include_router(survey_router, prefix="/survey", tags=["Survey"])
router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(programs_router, tags=["Programs"])