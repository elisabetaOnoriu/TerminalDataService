"""
This module provides API endpoints for managing devices in the system.

"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device_model import Device
from app.models.device_schema import DeviceCreate, DeviceRead
from app.helpers.database import get_db
from logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/devices",
    response_model=DeviceRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new device",
    response_description="The created device",
    responses={
        201: {"description": "Device created successfully"},
        400: {"description": "Invalid request data"},
        409: {"description": "Device with same unique fields already exists"},
        500: {"description": "Internal server error"},
    },
)
async def create_device(
    device: DeviceCreate,
    db: AsyncSession = Depends(get_db),
) -> DeviceRead:
    """
    Create a new device record in the system.

    This endpoint accepts device data via a request body,
    optionally serializes the `payload` field if it's a dictionary,
    then attempts to persist the device in the database.

    If the device already exists (based on unique constraints),
    a 409 Conflict is returned. In case of invalid JSON structure
    in the payload, a 400 Bad Request is triggered.
    """
    try:
        data = device.model_dump()

        if isinstance(data.get("payload"), dict):
            try:
                data["payload"] = json.dumps(data["payload"])
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid payload JSON: %s" % e
                ) from e

        new_device = Device(**data)
        db.add(new_device)

        await db.commit()
        await db.refresh(new_device)

        logger.info("Device created with ID: %s", new_device.device_id)
        return DeviceRead.model_validate(new_device)

    except IntegrityError as e:
        await db.rollback()
        logger.warning("Duplicate/constraint error while creating device: %s", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A device with these details already exists."
        ) from e

    except HTTPException:
        await db.rollback()
        raise

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error("Database error while creating device: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while creating the device."
        ) from e

    except Exception as e:
        await db.rollback()
        logger.error("Unexpected error while creating device: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while creating the device."
        ) from e
