from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy. orm import Session
from app.models.client_model import Client
from app.models.client_schema import ClientCreate
from app.helpers.database import get_db
import logging

router=APIRouter()
logger = logging.getLogger(__name__)

@router.post("/clients", status_code=200)
def create_client(client: ClientCreate, bd:  Session = Depends(get_db)):
    try:
        new_client = Client(name=client.name)
        bd.add(new_client)
        bd.commit()
        bd.refresh(new_client)
        logger.info(f"Created new client with id: {new_client.client_id}")
        return {"client_id" : new_client.client_id, "name" : new_client.name}
    except Exception as e:
        bd.rollback()
        logger.error(f"Error while trying to create client {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error at the time of creating the client"
        )