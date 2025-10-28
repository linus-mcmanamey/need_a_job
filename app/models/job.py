"""
Job domain model.

Represents a job posting with all associated metadata.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID, uuid4


@dataclass
class Job:
    """
    Domain model for a job posting.

    Attributes:
        job_id: Unique identifier for the job
        platform_source: Platform where job was found
        company_name: Company offering the job
        job_title: Title of the position
        job_url: URL to the job posting
        salary_aud_per_day: Daily rate in AUD (if available)
        location: Job location
        posted_date: Date job was posted
        job_description: Full job description
        requirements: Job requirements
        responsibilities: Job responsibilities
        discovered_timestamp: When job was discovered by system
        duplicate_group_id: ID linking duplicate job postings
    """

    company_name: str
    job_title: str
    job_url: str
    platform_source: Literal["linkedin", "seek", "indeed"]
    job_id: str = field(default_factory=lambda: str(uuid4()))
    salary_aud_per_day: Optional[Decimal] = None
    location: Optional[str] = None
    posted_date: Optional[date] = None
    job_description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    discovered_timestamp: datetime = field(default_factory=datetime.now)
    duplicate_group_id: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert Job to dictionary for database insertion.

        Returns:
            Dictionary representation of the job
        """
        return {
            "job_id": self.job_id,
            "platform_source": self.platform_source,
            "company_name": self.company_name,
            "job_title": self.job_title,
            "job_url": self.job_url,
            "salary_aud_per_day": float(self.salary_aud_per_day) if self.salary_aud_per_day else None,
            "location": self.location,
            "posted_date": self.posted_date,
            "job_description": self.job_description,
            "requirements": self.requirements,
            "responsibilities": self.responsibilities,
            "discovered_timestamp": self.discovered_timestamp,
            "duplicate_group_id": self.duplicate_group_id,
        }

    @classmethod
    def from_db_row(cls, row: tuple) -> "Job":
        """
        Create Job instance from database row.

        Args:
            row: Tuple containing job data from database

        Returns:
            Job instance
        """
        if row is None:
            return None

        return cls(
            job_id=row[0],
            platform_source=row[1],
            company_name=row[2],
            job_title=row[3],
            job_url=row[4],
            salary_aud_per_day=Decimal(str(row[5])) if row[5] is not None else None,
            location=row[6],
            posted_date=row[7],
            job_description=row[8],
            requirements=row[9],
            responsibilities=row[10],
            discovered_timestamp=row[11],
            duplicate_group_id=row[12],
        )
