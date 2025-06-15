# -*- coding: utf-8 -*-
import sys
from os import getenv

from loguru import logger

# Remove default handler
logger.remove(0)

# Add new handler with extra fields
logger.add(
    sys.stdout,
    level=getenv("LOGGING_LEVEL", "DEBUG"),
    serialize=getenv("LOGGING_SERIALIZED", "false").lower() == "true",
)

__all__ = ["logger"]
