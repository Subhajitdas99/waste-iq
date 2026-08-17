from fastapi import APIRouter

from app.api.routes import admin, context, evaluation, health, llm, review, webhooks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(webhooks.router)
api_router.include_router(context.router)
api_router.include_router(admin.router)
api_router.include_router(review.router)
api_router.include_router(llm.router)
api_router.include_router(evaluation.router)
