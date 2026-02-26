"""
Unified AI Service Layer
========================
Routes prompts through a configurable provider chain with automatic fallback.

Provider priority:
    1. Primary  → AI_PROVIDER env var (default: "huggingface")
    2. Fallback → AI_FALLBACK_PROVIDERS env var (comma-separated, optional)

Supported providers: huggingface | gemini | openai

All providers enforce:
    - Structured retry logic (configurable attempts)
    - Per-request timeout protection
    - Graceful error handling (no crash propagation to UI)
    - Production-grade structured logging
"""

import os
import time
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Logging — structured, production-grade
# ---------------------------------------------------------------------------
logger = logging.getLogger("ai_service")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "[AI] %(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# ---------------------------------------------------------------------------
# Configuration (all env-driven)
# ---------------------------------------------------------------------------
AI_PROVIDER = os.getenv("AI_PROVIDER", "huggingface").strip().lower()
AI_FALLBACK_PROVIDERS = [
    p.strip().lower()
    for p in os.getenv("AI_FALLBACK_PROVIDERS", "").split(",")
    if p.strip()
]

MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "3"))
RETRY_DELAY = int(os.getenv("AI_RETRY_DELAY", "2"))
REQUEST_TIMEOUT = int(os.getenv("AI_TIMEOUT", "60"))

# HuggingFace — uses OpenAI-compatible chat completions via router
_HF_BASE_URL = "https://router.huggingface.co/v1"
HF_MODEL = os.getenv("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")
_HF_FALLBACK_MODELS = [
    "meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/Meta-Llama-3-8B-Instruct",
    "google/gemma-2-9b-it",
    "microsoft/Phi-3.5-mini-instruct",
]


# ═══════════════════════════════════════════════════════════════════════════
#  PROVIDER IMPLEMENTATIONS
# ═══════════════════════════════════════════════════════════════════════════

def _call_huggingface(system_prompt: str, user_prompt: str) -> str:
    """
    Call HuggingFace Inference Providers via the OpenAI-compatible
    chat/completions endpoint at router.huggingface.co/v1.
    """
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
    if not hf_token:
        raise EnvironmentError(
            "HF_TOKEN is not set. "
            "Get a free token at https://huggingface.co/settings/tokens"
        )

    headers = {
        "Authorization": f"Bearer {hf_token}",
        "Content-Type": "application/json",
    }

    # Build messages in OpenAI chat format
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    # Try primary model, then fallbacks
    models_to_try = [HF_MODEL] + _HF_FALLBACK_MODELS
    api_url = f"{_HF_BASE_URL}/chat/completions"

    last_error = None
    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.7,
            "stream": False,
        }

        try:
            logger.info("Provider: huggingface | Model: %s | Sending request", model_name)
            resp = requests.post(api_url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT)

            # Handle 503 — model is loading
            if resp.status_code == 503:
                try:
                    body = resp.json()
                    wait = min(body.get("estimated_time", 20), 30)
                except Exception:
                    wait = 15
                logger.info(
                    "Provider: huggingface | Model: %s | Status: Loading | Wait: %.0fs",
                    model_name, wait,
                )
                time.sleep(wait)
                resp = requests.post(api_url, headers=headers, json=payload, timeout=REQUEST_TIMEOUT + 30)

            if resp.status_code == 200:
                data = resp.json()
                # OpenAI-compatible response format
                text = ""
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    msg = choice.get("message", {})
                    text = msg.get("content", "")
                elif "generated_text" in data:
                    text = data["generated_text"]
                elif isinstance(data, list) and len(data) > 0:
                    text = data[0].get("generated_text", "")

                text = text.strip()
                if text:
                    logger.info(
                        "Provider: huggingface | Model: %s | Status: Success | Length: %d chars",
                        model_name, len(text),
                    )
                    return text

            # Non-200 — log and try next model
            last_error = f"HTTP {resp.status_code} from {model_name}: {resp.text[:300]}"
            logger.warning(
                "Provider: huggingface | Model: %s | Status: Failed | Error: HTTP %d",
                model_name, resp.status_code,
            )

        except requests.exceptions.Timeout:
            last_error = f"Timeout calling {model_name} (>{REQUEST_TIMEOUT}s)"
            logger.warning("Provider: huggingface | Model: %s | Status: Timeout", model_name)
        except Exception as exc:
            last_error = str(exc)
            logger.warning(
                "Provider: huggingface | Model: %s | Status: Error | Detail: %s",
                model_name, exc,
            )

    raise RuntimeError(f"HuggingFace: all models failed. Last error: {last_error}")


def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Call Google Gemini API."""
    import google.generativeai as genai

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY is not set.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    combined = f"{system_prompt}\n\n{user_prompt}" if system_prompt else user_prompt

    logger.info("Provider: gemini | Model: gemini-2.0-flash | Sending request")
    response = model.generate_content(
        combined,
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=4096,
            temperature=0.7,
        ),
    )
    text = response.text
    logger.info("Provider: gemini | Status: Success | Length: %d chars", len(text))
    return text


def _call_openai(system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI ChatCompletion API."""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    logger.info("Provider: openai | Model: gpt-4o-mini | Sending request")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=4096,
        temperature=0.7,
    )
    text = response.choices[0].message.content
    logger.info("Provider: openai | Status: Success | Length: %d chars", len(text))
    return text


# ═══════════════════════════════════════════════════════════════════════════
#  PROVIDER REGISTRY
# ═══════════════════════════════════════════════════════════════════════════

_PROVIDERS = {
    "huggingface": _call_huggingface,
    "hf":          _call_huggingface,
    "gemini":      _call_gemini,
    "openai":      _call_openai,
}


def _resolve_provider(name: str):
    """Resolve a provider name to its callable, or None."""
    fn = _PROVIDERS.get(name)
    if fn is None:
        logger.warning("Unknown provider '%s' — skipping", name)
    return fn


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

def call_ai(system_prompt: str, user_prompt: str) -> str:
    """
    Send a prompt to the AI provider chain with retry + fallback logic.

    Flow:
        1. Try PRIMARY provider (AI_PROVIDER) up to MAX_RETRIES times
        2. If all retries fail, try each FALLBACK provider once
        3. If everything fails, raise a structured RuntimeError

    Returns the generated text string.
    """
    # Build ordered provider chain: [primary, fallback1, fallback2, ...]
    chain = [AI_PROVIDER] + [
        fb for fb in AI_FALLBACK_PROVIDERS if fb != AI_PROVIDER
    ]

    errors: list[str] = []

    for provider_name in chain:
        provider_fn = _resolve_provider(provider_name)
        if provider_fn is None:
            continue

        # Retry logic for the primary provider only
        attempts = MAX_RETRIES if provider_name == AI_PROVIDER else 1

        for attempt in range(1, attempts + 1):
            try:
                logger.info(
                    "Provider: %s | Attempt: %d/%d | Status: Calling",
                    provider_name, attempt, attempts,
                )
                result = provider_fn(system_prompt, user_prompt)
                if result and result.strip():
                    return result.strip()
                raise ValueError("Empty response from provider")

            except EnvironmentError:
                # Missing API key — skip to next provider immediately
                logger.warning(
                    "Provider: %s | Status: Skipped | Reason: API key not configured",
                    provider_name,
                )
                errors.append(f"{provider_name}: API key not configured")
                break  # Don't retry, move to next provider

            except Exception as exc:
                error_msg = str(exc)[:200]
                logger.warning(
                    "Provider: %s | Attempt: %d/%d | Status: Failed | Error: %s",
                    provider_name, attempt, attempts, error_msg,
                )
                errors.append(f"{provider_name} (attempt {attempt}): {error_msg}")

                if attempt < attempts:
                    delay = RETRY_DELAY * attempt
                    logger.info("Provider: %s | Retrying in %ds...", provider_name, delay)
                    time.sleep(delay)

    # All providers exhausted
    error_summary = "; ".join(errors[-3:])
    logger.error("All AI providers failed | Errors: %s", error_summary)
    raise RuntimeError(
        f"AI service unavailable. Tried providers: {', '.join(chain)}. "
        f"Last errors: {error_summary}"
    )
