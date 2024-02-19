from fastapi import APIRouter

from api.routes import predictor, user

router = APIRouter()
router.include_router(predictor.router, tags=["predictor"], prefix="/v1")
router.include_router(user.router, tags=["user"], prefix='/user')