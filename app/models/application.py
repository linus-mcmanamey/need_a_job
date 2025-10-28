"""
Application tracking domain model.

Represents the application workflow state for a job.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal
from uuid import uuid4


@dataclass
class Application:
    """
    Domain model for application tracking.

    Tracks the progress of job application through the agent pipeline.

    Attributes:
        application_id: Unique identifier
        job_id: Reference to job
        status: Current application status
        current_stage: Current agent processing the application
        completed_stages: List of agents that have completed processing
        stage_outputs: Output data from each agent
        error_info: Error information if processing failed
        cv_file_path: Path to generated CV file
        cl_file_path: Path to generated cover letter file
        submission_method: How application will be submitted
        submitted_timestamp: When application was submitted
        contact_person_name: Contact person for application
        created_at: When application record was created
        updated_at: When application record was last updated
    """

    job_id: str
    status: Literal["discovered", "queued", "matched", "documents_generated", "ready_to_send", "sending", "completed", "pending", "failed", "rejected", "duplicate"] = "discovered"
    application_id: str = field(default_factory=lambda: str(uuid4()))
    current_stage: str | None = None
    completed_stages: list[str] = field(default_factory=list)
    stage_outputs: dict[str, Any] = field(default_factory=dict)
    error_info: dict[str, Any] | None = None
    cv_file_path: str | None = None
    cl_file_path: str | None = None
    submission_method: Literal["email", "web_form"] | None = None
    submitted_timestamp: datetime | None = None
    contact_person_name: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """
        Convert Application to dictionary for database insertion.

        Returns:
            Dictionary representation of the application
        """
        return {
            "application_id": self.application_id,
            "job_id": self.job_id,
            "status": self.status,
            "current_stage": self.current_stage,
            "completed_stages": json.dumps(self.completed_stages),
            "stage_outputs": json.dumps(self.stage_outputs),
            "error_info": json.dumps(self.error_info) if self.error_info else None,
            "cv_file_path": self.cv_file_path,
            "cl_file_path": self.cl_file_path,
            "submission_method": self.submission_method,
            "submitted_timestamp": self.submitted_timestamp,
            "contact_person_name": self.contact_person_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_db_row(cls, row: tuple) -> "Application":
        """
        Create Application instance from database row.

        Args:
            row: Tuple containing application data from database

        Returns:
            Application instance
        """
        if row is None:
            return None

        return cls(
            application_id=row[0],
            job_id=row[1],
            status=row[2],
            current_stage=row[3],
            completed_stages=json.loads(row[4]) if row[4] else [],
            stage_outputs=json.loads(row[5]) if row[5] else {},
            error_info=json.loads(row[6]) if row[6] else None,
            cv_file_path=row[7],
            cl_file_path=row[8],
            submission_method=row[9],
            submitted_timestamp=row[10],
            contact_person_name=row[11],
            created_at=row[12],
            updated_at=row[13],
        )

    def add_completed_stage(self, stage_name: str, output: dict[str, Any]) -> None:
        """
        Mark a stage as completed and store its output.

        Args:
            stage_name: Name of the agent/stage
            output: Output data from the stage
        """
        if stage_name not in self.completed_stages:
            self.completed_stages.append(stage_name)
        self.stage_outputs[stage_name] = output
        self.updated_at = datetime.now()

    def set_error(self, stage: str, error_type: str, error_message: str) -> None:
        """
        Record error information for a failed stage.

        Args:
            stage: Stage where error occurred
            error_type: Type of error
            error_message: Error message
        """
        self.error_info = {"stage": stage, "error_type": error_type, "error_message": error_message, "timestamp": datetime.now().isoformat()}
        self.status = "failed"
        self.updated_at = datetime.now()
