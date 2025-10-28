"""
Pydantic validation models for configuration.

Provides type-safe configuration access with validation.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class LocationsConfig(BaseModel):
    """Location preferences configuration."""

    primary: str
    acceptable: str
    exclude: list[str] = []


class KeywordsConfig(BaseModel):
    """Job keywords configuration."""

    primary: list[str]
    secondary: list[str]
    exclude: list[str] = []


class TechnologiesConfig(BaseModel):
    """Technology requirements configuration."""

    must_have: list[str]
    strong_preference: list[str]
    nice_to_have: list[str]


class SalaryExpectationsConfig(BaseModel):
    """Salary expectations configuration."""

    minimum: int = Field(ge=0)
    target: int = Field(ge=0)
    maximum: int = Field(ge=0)

    @field_validator("target")
    @classmethod
    def target_ge_minimum(cls, v: int, info) -> int:
        """Validate target >= minimum."""
        if "minimum" in info.data and v < info.data["minimum"]:
            raise ValueError("target must be >= minimum")
        return v

    @field_validator("maximum")
    @classmethod
    def maximum_ge_target(cls, v: int, info) -> int:
        """Validate maximum >= target."""
        if "target" in info.data and v < info.data["target"]:
            raise ValueError("maximum must be >= target")
        return v


class SearchConfig(BaseModel):
    """Search criteria configuration with validation."""

    job_type: Literal["contract", "permanent", "casual"]
    duration: str
    locations: LocationsConfig
    keywords: KeywordsConfig
    technologies: TechnologiesConfig
    salary_expectations: SalaryExpectationsConfig


class ScoringWeightsConfig(BaseModel):
    """Scoring weights for job matching."""

    must_have_present: float = Field(ge=0.0, le=1.0)
    strong_preference_present: float = Field(ge=0.0, le=1.0)
    nice_to_have_present: float = Field(ge=0.0, le=1.0)
    location_match: float = Field(ge=0.0, le=1.0)


class AgentConfigBase(BaseModel):
    """Base configuration for agents."""

    model: str
