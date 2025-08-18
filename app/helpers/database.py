import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from logging_config import setup_logging
import logging

setup_logging()
logger=logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    logger.info("Creating new DB session")
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Eroare: {e} ")
        raise
    finally:
        logger.info("Closing current DB session")
        db.close()
