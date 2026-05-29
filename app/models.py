"""
Database models for the Job Application Tracker.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from .database import Base


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(200), nullable=False, index=True)
    role = Column(String(200), nullable=False)
    status = Column(String(50), default="Applied", index=True)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    location = Column(String(200), nullable=True)
    job_type = Column(String(50), default="Full-time")
    url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    contact_name = Column(String(200), nullable=True)
    contact_email = Column(String(200), nullable=True)
    interview_date = Column(DateTime(timezone=True), nullable=True)
    priority = Column(String(20), default="Medium")  # Low, Medium, High
    applied_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_date = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Valid statuses
    STATUSES = [
        "Saved",
        "Applied",
        "Phone Screen",
        "Technical Interview",
        "Final Interview",
        "Offer Received",
        "Accepted",
        "Rejected",
        "Withdrawn"
    ]

    JOB_TYPES = [
        "Full-time",
        "Part-time",
        "Contract",
        "Remote",
        "Hybrid",
        "Internship"
    ]

    PRIORITIES = ["Low", "Medium", "High"]
