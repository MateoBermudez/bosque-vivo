from bosquevivo.ai.llm import LLMProvider, MediaPart, Message
from bosquevivo.core.errors import ExternalServiceError

SYSTEM = (
    "Transcribe fielmente el audio en español. Responde solo con la transcripción, sin "
    "comentarios. Si no se entiende, responde exactamente: NO_ENTENDIDO."
)


def transcribe_audio(llm: LLMProvider, audio: MediaPart) -> str | None:
    response = llm.generate(
        SYSTEM, [Message(role="user", text="Transcribe este audio.", media=[audio])], light=True
    )
    if response.blocked:
        raise ExternalServiceError("el modelo no pudo procesar el audio")
    text = (response.text or "").strip()
    return None if not text or text == "NO_ENTENDIDO" else text
