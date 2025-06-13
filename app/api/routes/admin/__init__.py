from fastapi import APIRouter

from .barbers import router as barbers_router
from .users import router as users_router

admin_router = APIRouter()

admin_router.include_router(barbers_router, prefix="/barbers")
admin_router.include_router(users_router, prefix="/users")
