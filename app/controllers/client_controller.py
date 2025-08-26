"""
This module handles API endpoints related to clients:
- Creating a new client (POST /clients)
- Assigning a device to a client (PUT /clients/{client_id}/devices/{device_id})
"""

import logging
from sqlite3 import IntegrityError

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from app.helpers.database import get_db
from app.models.client_model import Client
from app.models.client_schema import ClientCreate, ClientRead
from app.models.device_model import Device
from app.models.device_schema import DeviceRead

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/clients",
    response_model=ClientRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new client",
    response_description="The created client",
    responses={
        201: {"description": "Client created successfully"},
        400: {"description": "Invalid request data"},
        409: {"description": "Client already exists"},
        500: {"description": "Internal server error"},
    },
)
async def create_client(client: ClientCreate, db: AsyncSession = Depends(get_db)) -> ClientRead:
    """
    Create a new client in the system.
    """
    try:
        new_client = Client(name=client.name)
        db.add(new_client)
        await db.commit()
        await db.refresh(new_client)

        logger.info("Created new client with id: %s", new_client.client_id)
        return ClientRead.model_validate(new_client)

    except IntegrityError as e:
        await db.rollback()
        logger.warning("Duplicate/constraint error while creating client: %s", e)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A client with these details already exists."
        ) from e

    except Exception as e:
        await db.rollback()
        logger.error("Error while trying to create client: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while creating the client."
        ) from e


@router.put(
    "/clients/{client_id}/devices/{device_id}",
    response_model=DeviceRead,
    status_code=status.HTTP_200_OK,
    summary="Assign a device to a client",
    response_description="The updated device",
    responses={
        204: {"description": "Device assigned"},
        404: {"description": "Client or device not found"},
        409: {"description": "Device already assigned to another client"},
        500: {"description": "Internal server error"},
    },
)
async def assign_device_to_client(
    client_id: int,
    device_id: int,
    db: AsyncSession = Depends(get_db),
) -> DeviceRead:
    """
    Assign a device to a specific client.
    """
    try:
        client = await db.get(Client, client_id)
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")

        device = await db.get(Device, device_id)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

        if device.client_id == client_id:
            logger.info("Device %s already assigned to client %s", device_id, client_id)
            return DeviceRead.model_validate(device)

        if device.client_id is not None and device.client_id != client_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Device is already assigned to client {device.client_id}",
            )

        device.client_id = client_id
        await db.commit()
        await db.refresh(device)

        logger.info("Assigned device %s to client %s", device_id, client_id)
        return DeviceRead.model_validate(device)

    except HTTPException:
        await db.rollback()
        raise

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(
            "DB error while assigning device %s to client %s: %s",
            device_id, client_id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error while assigning the device",
        ) from e

    except Exception as e:
        await db.rollback()
        logger.error(
            "Unexpected error while assigning device %s to client %s: %s",
            device_id, client_id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error while assigning the device",
        ) from e
