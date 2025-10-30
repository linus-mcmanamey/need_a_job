"""
Pydantic models for API request validation.

This module defines request models to validate incoming API requests,
ensuring data integrity and security.
"""

from pydantic import BaseModel, Field, validator


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
