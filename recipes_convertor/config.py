# -*- coding: utf-8 -*-
import os
import tomllib
from pathlib import Path
from typing import Optional


def get_gemini_api_key() -> Optional[str]:
    """
    Get the Gemini API key from environment variable or config file.
    Returns None if no API key is found.
    """
    # First try environment variable
    if api_key := os.getenv("GEMINI_API_KEY"):
        return api_key

    # Then try config file
    config_path = Path.home() / ".config" / "recipes-convertor" / "config.toml"
    if not config_path.exists():
        return None

    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
            return config.get("gemini", {}).get("api_key")
    except Exception:
        return None
