from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
from app.routers import router as all_routes
from app.controllers.device_controller import router as device_router
from logging_config import setup_logging
import logging
from app.models.base import Base

setup_logging()
logger=logging.getLogger(__name__)
try:
    app = FastAPI()
    app.include_router(all_routes)
#    print(app.routes)

    logger.info(" FastAPI app and routes initialized")
except Exception as e:
    logger.error(f" Error during app setup: {e}")
    raise