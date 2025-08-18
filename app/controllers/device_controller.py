from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.device_model import Device
from app.models.device_schema import DeviceCreate
from app.helpers.database import get_db
from logging_config import setup_logging
import logging

setup_logging()
logger=logging.getLogger(__name__)
router = APIRouter()


@router.post("/devices/")
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
   try:
     new_device = Device(**device.dict())

     db.add(new_device)
     db.commit()
     db.refresh(new_device)
     logger.info(f" Device creat cu ID: {new_device.device_id}")
     return new_device
   except Exception as e:
       db.rollback()
       logger.error(f" Error: {e}")
       raise HTTPException(
           status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
           detail="Internal error"
       )




