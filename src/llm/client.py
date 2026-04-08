import os
import requests
import logging
from google import genai
import json

from src.core.config import LLM_PROVIDER, LLM_MODEL, LLM_BASE_URL, GEMINI_API_KEY

logger = logging.getLogger(__name__)


def generate_response(system_prompt: str, user_content: str, temperature: float = 0.3) -> str:
    """
    A unified interface for generating LLM responses, seamlessly routing traffic 
    to either a self-hosted Ollama LXC container or Google Gemini API fallback.
    """
    if LLM_PROVIDER == "ollama":
        return _generate_ollama(system_prompt, user_content, temperature)
    elif LLM_PROVIDER == "gemini":
        return _generate_gemini(system_prompt, user_content, temperature)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER configured: {LLM_PROVIDER}")


def _generate_ollama(system_prompt: str, user_content: str, temperature: float) -> str:
    """Invokes self-hosted Ollama model via raw HTTP POST with deep timeouts."""
    # Ollama's /api/generate endpoint expects:
    # { "model": "mistral-nemo", "system": "...", "prompt": "...", "stream": false, "options": { "temperature": 0.3 } }
    payload = {
        "model": LLM_MODEL,
        "system": system_prompt,
        "prompt": user_content,
        "stream": False,
        "options": {
            "temperature": temperature
        }
    }

    try:
        logger.info(f"Ollama -> Base URL: {LLM_BASE_URL} | Model: {LLM_MODEL}")
        # High timeout because an N100 CPU might take several minutes to generate 
        # a long weekly or monthly report
        response = requests.post(LLM_BASE_URL, json=payload, timeout=900)
        response.raise_for_status()
        
        data = response.json()
        if "response" in data:
            return data["response"].strip()
        else:
            raise ValueError(f"Ollama response missing 'response' field: {list(data.keys())}")
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Ollama HTTP request failed: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Ollama returned invalid JSON: {e}")
        raise


def _generate_gemini(system_prompt: str, user_content: str, temperature: float) -> str:
    """Invokes Google's hosted Gemini API natively."""
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info(f"Gemini -> Model: {LLM_MODEL}")
        
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=user_content,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature
            )
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini generation failed: {e}")
        raise
