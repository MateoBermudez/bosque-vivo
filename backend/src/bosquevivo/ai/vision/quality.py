import json
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel

from bosquevivo.ai.llm import LLMProvider, MediaPart, Message
from bosquevivo.core.errors import ExternalServiceError

Level = Literal["bajo", "medio", "alto"]
YesNo = Literal["si", "no"]


class SceneQuality(BaseModel):
    nubes: Level
    humo: YesNo
    sombras: YesNo
    utilizable: YesNo
    motivo: str


QUALITY_SYSTEM = (
    "Eres un revisor de calidad de imágenes satelitales. Describes únicamente lo que ves: "
    "nubes, humo, sombras y si la escena sirve para comparar vegetación. No cuantificas "
    "áreas ni porcentajes. Responde solo con el JSON pedido."
)

COMPARE_SYSTEM = (
    "Eres un analista que compara dos imágenes satelitales del mismo lugar, antes y después. "
    "Describe en lenguaje sencillo qué diferencias visibles hay (claros, cambios de textura, "
    "zonas quemadas) y dónde, usando puntos cardinales. No des cifras ni porcentajes. "
    "Presenta todo como interpretación, nunca como acusación. Máximo 60 palabras."
)

PHOTO_SYSTEM = (
    "Describe brevemente qué se ve en esta foto enviada por una persona de la comunidad "
    "(vegetación, claros, troncos cortados, humo, quemas). No identifiques personas ni "
    "placas. No des cifras. Es evidencia no verificada. Máximo 50 palabras."
)


def quality_schema() -> dict[str, Any]:
    return SceneQuality.model_json_schema()


def assess_scene_quality(llm: LLMProvider, image: MediaPart) -> SceneQuality:
    response = llm.generate(
        QUALITY_SYSTEM,
        [Message(role="user", text="Evalúa la calidad de esta escena.", media=[image])],
        json_schema=quality_schema(),
        light=True,
    )
    if response.blocked or not response.text:
        raise ExternalServiceError("el modelo no devolvió una evaluación de la escena")
    try:
        return SceneQuality.model_validate(json.loads(response.text))
    except (ValueError, json.JSONDecodeError) as exc:
        raise ExternalServiceError("evaluación de escena con formato inválido") from exc


def describe_change(llm: LLMProvider, before: MediaPart, after: MediaPart) -> str:
    response = llm.generate(
        COMPARE_SYSTEM,
        [
            Message(
                role="user",
                text="Primera imagen: antes. Segunda imagen: después.",
                media=[before, after],
            )
        ],
    )
    if response.blocked or not response.text:
        raise ExternalServiceError("el modelo no pudo comparar las imágenes")
    return response.text


def describe_user_photo(llm: LLMProvider, image: MediaPart) -> str:
    response = llm.generate(
        PHOTO_SYSTEM, [Message(role="user", text="Describe la foto.", media=[image])]
    )
    if response.blocked or not response.text:
        raise ExternalServiceError("el modelo no pudo describir la foto")
    return response.text


@dataclass(frozen=True)
class QualityVerdict:
    quality: SceneQuality

    @property
    def usable(self) -> bool:
        return self.quality.utilizable == "si"
