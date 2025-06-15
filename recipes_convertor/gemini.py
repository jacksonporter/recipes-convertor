# -*- coding: utf-8 -*-
from typing import Optional

import google.generativeai as genai
from recipes_convertor.logger import logger

from .config import get_gemini_api_key


def initialize_gemini() -> Optional[genai.GenerativeModel]:
    """
    Initialize the Gemini client with the API key.

    Returns:
        Optional[genai.GenerativeModel]: The initialized model if successful,
            None if no API key is found or initialization fails.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        logger.error("No Gemini API key found")
        return None

    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel("gemini-pro")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini: {e}")
        return None


def generate_text(prompt: str, model: Optional[genai.GenerativeModel] = None) -> Optional[str]:
    """
    Generate text using the Gemini model.

    Args:
        prompt: The text prompt to send to the model
        model: Optional pre-initialized model. If None, will initialize a new one.

    Returns:
        Optional[str]: The generated text if successful, None if there was an error
    """
    if model is None:
        model = initialize_gemini()
        if model is None:
            return None

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating text: {e}")
        return None
