from fastapi import APIRouter

from .appointments import router as appointment_router
from .barbers import router as barbers_router
from .reviews import router as review_router
from .users import router as users_router

admin_router = APIRouter()

admin_router.include_router(users_router, prefix="/users")
admin_router.include_router(barbers_router, prefix="/barbers")
admin_router.include_router(appointment_router, prefix="/appointments")
admin_router.include_router(review_router, prefix="/reviews")
