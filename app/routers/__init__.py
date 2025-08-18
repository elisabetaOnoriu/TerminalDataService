from fastapi import APIRouter
from app.controllers import device_controller
from app.controllers import client_controller

router = APIRouter()

router.include_router(device_controller.router, prefix="/devices", tags=["Devices"])
router.include_router(client_controller.router, prefix="/client", tags=["Clients"])