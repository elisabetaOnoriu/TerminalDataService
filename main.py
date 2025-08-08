from fastapi import FastAPI
from app.routers import router as all_routes
from dotenv import load_dotenv
from app.controllers.device_controller import router as device_router
load_dotenv()


app = FastAPI()

app.include_router(all_routes)
