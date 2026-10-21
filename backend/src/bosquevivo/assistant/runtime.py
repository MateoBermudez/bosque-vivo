from sqlalchemy.orm import Session

from bosquevivo.ai.agent import Agent, default_registry
from bosquevivo.ai.llm import GeminiProvider, LLMProvider
from bosquevivo.ai.llm.cache import ResponseCache
from bosquevivo.ai.llm.limits import RateLimiter
from bosquevivo.assistant.client import CloudApiClient, WhatsAppClient
from bosquevivo.assistant.service import AssistantService
from bosquevivo.core.config import Settings
from bosquevivo.satellite.provider import SatelliteProvider
from bosquevivo.satellite.service import SatelliteService

REQUESTS_PER_MINUTE = 10
REQUESTS_PER_DAY = 400


def build_llm(settings: Settings) -> LLMProvider:
    return GeminiProvider(
        settings.gemini_api_key,
        settings.gemini_model,
        light_model=settings.gemini_model_light or None,
        limiter=RateLimiter(REQUESTS_PER_MINUTE, REQUESTS_PER_DAY),
        cache=ResponseCache(settings.cache_dir / "llm"),
    )


def build_assistant(
    session: Session,
    settings: Settings,
    llm: LLMProvider,
    client: WhatsAppClient | None = None,
    satellite_provider: SatelliteProvider | None = None,
) -> AssistantService:
    satellite = (
        SatelliteService(session, satellite_provider, settings.images_dir)
        if satellite_provider
        else None
    )
    agent = Agent(session, llm, default_registry(), settings, satellite)
    resolved = client or CloudApiClient(settings.whatsapp_token, settings.whatsapp_phone_number_id)
    return AssistantService(session, agent, resolved, llm, settings)
