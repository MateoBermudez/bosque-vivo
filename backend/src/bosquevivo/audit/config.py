from pydantic import BaseModel, Field, model_validator


class IndexConfig(BaseModel):
    version: str = "v0"
    weight_permanence: float = 0.50
    weight_trend: float = 0.25
    weight_stability: float = 0.25
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
        total = self.weight_permanence + self.weight_trend + self.weight_stability
        if abs(total - 1.0) > 1e-9:
            raise ValueError("los pesos deben sumar 1")
        return self


def default_config() -> IndexConfig:
    return IndexConfig()
