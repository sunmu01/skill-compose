"""
Model registry with capabilities and context limits for all supported LLM providers.
"""

from typing import Dict, List, Optional, TypedDict


class ModelInfo(TypedDict):
    """Model information."""
    provider: str
    model_id: str  # The ID used by the provider's API
    display_name: str
    context_limit: int
    supports_tools: bool
    supports_vision: bool


# Supported models by provider
# Format: "provider/model" -> ModelInfo
SUPPORTED_MODELS: Dict[str, ModelInfo] = {
    # Anthropic models (direct API)
    "anthropic/claude-sonnet-4-6": {
        "provider": "anthropic",
        "model_id": "claude-sonnet-4-6",
        "display_name": "Claude Sonnet 4.6",
        "context_limit": 200000,
        "supports_tools": True,
        "supports_vision": True,
    },
    "anthropic/claude-opus-4-6": {
        "provider": "anthropic",
        "model_id": "claude-opus-4-6",
        "display_name": "Claude Opus 4.6",
        "context_limit": 200000,
        "supports_tools": True,
        "supports_vision": True,
    },
    # OpenAI direct models
    "openai/gpt-5.2": {
        "provider": "openai",
        "model_id": "gpt-5.2",
        "display_name": "GPT-5.2",
        "context_limit": 400000,
        "supports_tools": True,
        "supports_vision": True,
    },
    "openai/gpt-5-mini": {
        "provider": "openai",
        "model_id": "gpt-5-mini",
        "display_name": "GPT-5 Mini",
        "context_limit": 400000,
        "supports_tools": True,
        "supports_vision": True,
    },
    # Google Gemini direct models
    "google/gemini-3.1-pro-preview": {
        "provider": "google",
        "model_id": "gemini-3.1-pro-preview",
        "display_name": "Gemini 3.1 Pro Preview",
        "context_limit": 200000,
        "supports_tools": True,
        "supports_vision": True,
    },
    "google/gemini-3-flash-preview": {
        "provider": "google",
        "model_id": "gemini-3-flash-preview",
        "display_name": "Gemini 3 Flash Preview",
        "context_limit": 200000,
        "supports_tools": True,
        "supports_vision": True,
    },
    # Kimi (Moonshot AI) models
    "kimi/kimi-k2.5": {
        "provider": "kimi",
        "model_id": "kimi-k2.5",
        "display_name": "Kimi K2.5",
        "context_limit": 256000,
        "supports_tools": True,
        "supports_vision": True,
    },
}

# Context limits by model (for backward compatibility)
MODEL_CONTEXT_LIMITS: Dict[str, int] = {
    info["model_id"]: info["context_limit"]
    for info in SUPPORTED_MODELS.values()
}

# Also add legacy model names for backward compatibility
MODEL_CONTEXT_LIMITS.update({
    "claude-sonnet-4-5-20250929": 200000,
})

DEFAULT_CONTEXT_LIMIT = 200000


def get_model_info(model_key: str) -> Optional[ModelInfo]:
    """Get model info by full key (provider/model)."""
    return SUPPORTED_MODELS.get(model_key)


def get_provider_models(provider: str) -> List[Dict]:
    """Get all models for a specific provider."""
    models = []
    for key, info in SUPPORTED_MODELS.items():
        if info["provider"] == provider:
            models.append({
                "key": key,
                **info,
            })
    return models


def get_all_providers() -> List[str]:
    """Get list of all supported providers."""
    providers = set()
    for info in SUPPORTED_MODELS.values():
        providers.add(info["provider"])
    return sorted(providers)


def get_context_limit(provider: str, model_name: str) -> int:
    """Get context limit for a model."""
    # Try full key first
    full_key = f"{provider}/{model_name}"
    if full_key in SUPPORTED_MODELS:
        return SUPPORTED_MODELS[full_key]["context_limit"]

    # Try model_id match
    if model_name in MODEL_CONTEXT_LIMITS:
        return MODEL_CONTEXT_LIMITS[model_name]

    return DEFAULT_CONTEXT_LIMIT


def supports_vision(provider: str, model_name: str) -> bool:
    """Check if a model supports vision/image input.

    Returns True for models with known vision support, and True by default
    for unknown models (optimistic — most modern models support vision).
    """
    # Try full key first
    full_key = f"{provider}/{model_name}"
    if full_key in SUPPORTED_MODELS:
        return SUPPORTED_MODELS[full_key]["supports_vision"]

    # Try matching by model_id across all entries
    for info in SUPPORTED_MODELS.values():
        if info["model_id"] == model_name:
            return info["supports_vision"]

    # Unknown model — optimistically assume vision support
    return True
