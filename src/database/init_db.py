from .db import engine
from .models import Base
from src.utils.logger import get_logger

logger = get_logger(__name__)

logger.info("Creating database tables...")
Base.metadata.create_all(engine)
logger.info("Database initialized successfully!")
