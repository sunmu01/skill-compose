"""
Models API - List available LLM models and providers.
"""

from typing import List, Optional

from fastapi import APIRouter
from pydantic import BaseModel

from app.llm.models import SUPPORTED_MODELS, get_all_providers, get_provider_models


router = APIRouter(prefix="/models", tags=["Models"])


class ModelInfo(BaseModel):
    """Information about an available model."""
    key: str  # Full key: "provider/model"
    provider: str
    model_id: str
    display_name: str
    context_limit: int
    supports_tools: bool
    supports_vision: bool


class ProviderInfo(BaseModel):
    """Information about a provider."""
    name: str
    models: List[ModelInfo]


class ModelsListResponse(BaseModel):
    """Response for listing all models."""
    models: List[ModelInfo]
    total: int


class ProvidersListResponse(BaseModel):
    """Response for listing providers with their models."""
    providers: List[ProviderInfo]


@router.get("", response_model=ModelsListResponse)
async def list_models(provider: Optional[str] = None):
    """
    List all available LLM models.

    Optionally filter by provider.
    """
    models = []

    for key, info in SUPPORTED_MODELS.items():
        if provider and info["provider"] != provider:
            continue

        models.append(ModelInfo(
            key=key,
            provider=info["provider"],
            model_id=info["model_id"],
            display_name=info["display_name"],
            context_limit=info["context_limit"],
            supports_tools=info["supports_tools"],
            supports_vision=info["supports_vision"],
        ))

    return ModelsListResponse(
        models=models,
        total=len(models),
    )


@router.get("/providers", response_model=ProvidersListResponse)
async def list_providers():
    """
    List all providers with their available models.
    """
    providers = []

    for provider_name in get_all_providers():
        provider_models = get_provider_models(provider_name)
        models = [
            ModelInfo(
                key=m["key"],
                provider=m["provider"],
                model_id=m["model_id"],
                display_name=m["display_name"],
                context_limit=m["context_limit"],
                supports_tools=m["supports_tools"],
                supports_vision=m["supports_vision"],
            )
            for m in provider_models
        ]
        providers.append(ProviderInfo(
            name=provider_name,
            models=models,
        ))

    return ProvidersListResponse(providers=providers)
