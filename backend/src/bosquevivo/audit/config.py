from typing import Literal

from pydantic import BaseModel, Field, model_validator


class IndexConfig(BaseModel):
    version: str = "v0"
    weight_permanence: float = 0.50
    weight_trend: float = 0.25
    weight_stability: float = 0.25
    # v1: peso de la evolución de la pérdida (antes/después de T0); en v0 no se usa
    weight_evolution: float = 0.0
    # «acumulada»: % de bosque aún en pie (v0). «tasa_anual»: pérdida anual en % del inicial
    permanence_scoring: Literal["acumulada", "tasa_anual"] = "acumulada"
    # v1: pérdida anual (% del bosque inicial) en la que la permanencia llega a 0
    permanence_zero_rate_pct: float = 1.0
    # v1: cociente pérdida anual después/antes de T0: hasta `full` puntúa 100, en `zero` llega a 0
    evolution_full_ratio: float = 1.0
    evolution_zero_ratio: float = 3.0
    min_years_pre: int = 3
    # pérdida anual (% del bosque inicial) por debajo de la cual se considera despreciable
    negligible_rate_pct: float = 0.01
    loss_last_year: int = 2024
    trend_zero_slope_per_year: float = -0.05
    stability_full_drop: float = 0.05
    stability_zero_drop: float = 0.30
    category_high: float = 75.0
    category_medium: float = 50.0
    min_confidence: float = Field(default=0.30, ge=0.0, le=1.0)
    min_valid_fraction: float = Field(default=0.15, ge=0.0, le=1.0)
    min_valid_months_post: int = 12
    min_valid_months_pre: int = 6
    confidence_high: float = 0.70
    confidence_medium: float = 0.40
    significance_level: float = 0.05
    sensitivity_delta: float = 0.10

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "IndexConfig":
        total = (
            self.weight_permanence
            + self.weight_trend
            + self.weight_stability
            + self.weight_evolution
        )
        if abs(total - 1.0) > 1e-9:
            raise ValueError("los pesos deben sumar 1")
        return self


def default_config() -> IndexConfig:
    return IndexConfig()


def config_v1() -> IndexConfig:
    """Índice v1 (propuesta pendiente de aprobación): la permanencia se mide como tasa anual de
    pérdida y se añade cómo cambió esa pérdida respecto a antes de T0."""
    return IndexConfig(
        version="v1",
        weight_permanence=0.35,
        weight_evolution=0.35,
        weight_trend=0.15,
        weight_stability=0.15,
        permanence_scoring="tasa_anual",
    )


def config_for(version: str) -> IndexConfig:
    configs = {"v0": default_config, "v1": config_v1}
    if version not in configs:
        raise ValueError(
            f"versión de índice desconocida: {version} (válidas: {', '.join(configs)})"
        )
    return configs[version]()
