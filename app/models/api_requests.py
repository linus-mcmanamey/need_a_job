"""
Pydantic models for API request validation.

This module defines request models to validate incoming API requests,
ensuring data integrity and security.
"""

from pydantic import BaseModel, Field, validator
from typing import Literal


class RetryJobRequest(BaseModel):
    """Request model for retrying a job."""

    job_id: str = Field(..., description="The job ID to retry", min_length=1, max_length=255)

    @validator("job_id")
    def validate_job_id(cls, v):
        """Validate job_id format."""
        if not v or not v.strip():
            raise ValueError("job_id cannot be empty")
        # Basic sanitization - remove potentially dangerous characters
        if any(char in v for char in ["<", ">", ";", "&", "|", "`", "$", "(", ")"]):
            raise ValueError("job_id contains invalid characters")
        return v.strip()


class ApproveJobRequest(BaseModel):
    """Request model for approving a pending job."""

    job_id: str = Field(..., description="The job ID to approve", min_length=1, max_length=255)

    @validator("job_id")
    def validate_job_id(cls, v):
        """Validate job_id format."""
        if not v or not v.strip():
            raise ValueError("job_id cannot be empty")
        if any(char in v for char in ["<", ">", ";", "&", "|", "`", "$", "(", ")"]):
            raise ValueError("job_id contains invalid characters")
        return v.strip()


class RejectJobRequest(BaseModel):
    """Request model for rejecting a pending job."""

    job_id: str = Field(..., description="The job ID to reject", min_length=1, max_length=255)
    reason: str = Field(default="User rejected", description="Reason for rejection", max_length=1000)

    @validator("job_id")
    def validate_job_id(cls, v):
        """Validate job_id format."""
        if not v or not v.strip():
            raise ValueError("job_id cannot be empty")
        if any(char in v for char in ["<", ">", ";", "&", "|", "`", "$", "(", ")"]):
            raise ValueError("job_id contains invalid characters")
        return v.strip()

    @validator("reason")
    def validate_reason(cls, v):
        """Validate reason field."""
        if not v:
            return "User rejected"
        # Limit length and sanitize
        sanitized = v.strip()[:1000]
        return sanitized if sanitized else "User rejected"


class HistoryFilterParams(BaseModel):
    """
    Query parameters for application history filtering.

    Validates and parses filter parameters for the /api/history endpoint.
    Includes pagination, sorting, and various filter criteria.
    """

    platform: list[str] | None = Field(default=None, description="Filter by platforms (linkedin, seek, indeed)")
    date_from: str | None = Field(default=None, description="Start date (ISO format: YYYY-MM-DD)")
    date_to: str | None = Field(default=None, description="End date (ISO format: YYYY-MM-DD)")
    min_score: int | None = Field(default=None, ge=0, le=100, description="Minimum match score (0-100)")
    max_score: int | None = Field(default=None, ge=0, le=100, description="Maximum match score (0-100)")
    status: list[str] | None = Field(default=None, description="Filter by status (completed, rejected, pending, etc.)")
    page: int = Field(default=1, ge=1, description="Page number (starts at 1)")
    page_size: int = Field(default=25, ge=1, le=100, description="Items per page (max 100)")
    sort_by: Literal["title", "company", "platform", "applied_date", "match_score", "status"] = Field(default="applied_date", description="Column to sort by")
    sort_order: Literal["asc", "desc"] = Field(default="desc", description="Sort order (ascending or descending)")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "platform": ["linkedin", "seek"],
                "date_from": "2025-01-01",
                "date_to": "2025-10-31",
                "min_score": 70,
                "max_score": 100,
                "status": ["completed"],
                "page": 1,
                "page_size": 25,
                "sort_by": "applied_date",
                "sort_order": "desc",
            }
        }
