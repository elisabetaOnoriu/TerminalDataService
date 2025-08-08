from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.device_model import Device
from app.models.device_schema import DeviceCreate
from app.helpers.database import get_db

router = APIRouter()


@router.post("/devices/")
def create_device(device: DeviceCreate, db: Session = Depends(get_db)):
    new_device = Device(**device.dict())

    db.add(new_device)
    db.commit()
    db.refresh(new_device)

    return new_device
