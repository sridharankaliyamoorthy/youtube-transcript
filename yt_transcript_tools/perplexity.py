"""Lightweight Perplexity Sona wrapper.

This module provides `summarize_text` which will call a configurable
Perplexity (Sona) endpoint using an API key provided via the environment
variable `PPLX_API_KEY` (do NOT commit your key into the repo).

Because Perplexity's public API details may change, this wrapper is robust
and allows overriding the target URL via `PPLX_API_URL` environment variable.
It expects a JSON response containing a `summary` field; if the real API
returns a different shape you may adjust the parsing accordingly.
"""
from typing import Optional
import os
import requests

PPLX_API_KEY_ENV = "PPLX_API_KEY"
PPLX_API_URL_ENV = "PPLX_API_URL"

# Default URL placeholder; set PPLX_API_URL env var if actual endpoint differs.
DEFAULT_PPLX_URL = "https://api.perplexity.ai/sona/summarize"


def summarize_text(text: str, api_key: Optional[str] = None, api_url: Optional[str] = None, timeout: int = 30) -> str:
    """Summarize `text` using Perplexity Sona API.

    - `api_key`: optional; if not provided, the function will read from `PPLX_API_KEY` env var.
    - `api_url`: optional; if not provided, use `PPLX_API_URL` env var or a default placeholder.

    Returns the summary string on success or raises `RuntimeError` on failure.
    """
    key = api_key or os.environ.get(PPLX_API_KEY_ENV)
    if not key:
        raise RuntimeError("Perplexity API key not configured. Set the PPLX_API_KEY env var.")

    url = api_url or os.environ.get(PPLX_API_URL_ENV) or DEFAULT_PPLX_URL

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {"text": text}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
    except Exception as e:
        raise RuntimeError(f"Perplexity API request failed: {e}")

    if resp.status_code != 200:
        raise RuntimeError(f"Perplexity API returned status {resp.status_code}: {resp.text}")

    try:
        data = resp.json()
    except Exception as e:
        raise RuntimeError(f"Perplexity response JSON parse error: {e}")

    # Expecting a `summary` field — adapt if your Sona API returns different shape
    if isinstance(data, dict) and "summary" in data:
        return data["summary"]

    # Try common alternatives
    if isinstance(data, dict) and "result" in data and isinstance(data["result"], dict) and "summary" in data["result"]:
        return data["result"]["summary"]

    # If nothing matched, try to stringify some sensible fallback
    # but raise so caller knows the shape was unexpected
    raise RuntimeError(f"Perplexity API returned unexpected response shape: {data}")
