from fastapi import APIRouter
from app.controllers import device_controller

router = APIRouter()

router.include_router(device_controller.router, prefix="/devices", tags=["Devices"])
