import sys
import logging
from loguru import logger
from starlette.config import Config
from starlette.datastructures import Secret
from core.logging import InterceptHandler

config = Config(".env")

API_PREFIX = "/api"
VERSION = "0.1.0"
DEBUG: bool = config("DEBUG", cast=bool, default=False)
MAX_CONNECTIONS_COUNT: int = config("MAX_CONNECTIONS_COUNT", cast=int, default=10)
MIN_CONNECTIONS_COUNT: int = config("MIN_CONNECTIONS_COUNT", cast=int, default=10)
PROJECT_NAME: str = config("PROJECT_NAME", default="blog-backend")

# logging configuration
LOGGING_LEVEL = logging.DEBUG if DEBUG else logging.INFO
logging.basicConfig(
    handlers=[InterceptHandler(level=LOGGING_LEVEL)], level=LOGGING_LEVEL
)
logger.configure(handlers=[{"sink": sys.stderr, "level": LOGGING_LEVEL}])

MODEL_PATH = config("MODEL_PATH", default="./ml/model/")
MODEL_NAME = config("MODEL_NAME", default="model.pkl")
HOST = config("HOST", default="")
PORT = config("PORT", default="")
DB_HOST = config("DB_HOST", default="")
DB_PORT = config("DB_PORT", default="")
DB_USERNAME = config("DB_USERNAME", default="")
DB_PASSWORD = config("DB_PASSWORD", default="")
DB_TARGETDB = config("DB_TARGETDB", default="")
MODEL_HOST = config("MODEL_HOST", default="")
MODEL_PORT = config("MODEL_PORT", default="")