"""
Database Models
SQLAlchemy ORM models for the application
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, 
    ForeignKey, Enum, JSON, Boolean
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum


Base = declarative_base()


# ==========================================
# Enums
# ==========================================

class JobStatus(enum.Enum):
    """Job status enumeration"""
    ACTIVE = "active"
    CLOSED = "closed"
    DRAFT = "draft"


class AnalysisStatus(enum.Enum):
    """Analysis status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ==========================================
# Models
# ==========================================

class Job(Base):
    """
    Job Model
    Stores job descriptions and requirements
    """
    __tablename__ = "jobs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Job Information
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(Text, nullable=True)
    
    # Additional Details
    location = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    employment_type = Column(String(100), nullable=True)  # Full-time, Part-time, Contract
    experience_level = Column(String(100), nullable=True)  # Entry, Mid, Senior
    salary_range = Column(String(100), nullable=True)
    
    # Status
    status = Column(
        Enum(JobStatus),
        default=JobStatus.ACTIVE,
        nullable=False,
        index=True
    )
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    created_by = Column(String(255), nullable=True)
    
    # Relationships
    candidates = relationship(
        "Candidate",
        back_populates="job",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Job(id={self.id}, title='{self.title}', status='{self.status.value}')>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "requirements": self.requirements,
            "location": self.location,
            "department": self.department,
            "employment_type": self.employment_type,
            "experience_level": self.experience_level,
            "salary_range": self.salary_range,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "candidate_count": len(self.candidates) if self.candidates else 0
        }


class Candidate(Base):
    """
    Candidate Model
    Stores candidate information and parsed resume text
    """
    __tablename__ = "candidates"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign Key
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Candidate Information
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    
    # File Information
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)
    file_type = Column(String(10), nullable=False)  # pdf, docx, txt
    file_size = Column(Integer, nullable=True)  # Size in bytes
    
    # Parsed Resume
    parsed_text = Column(Text, nullable=False)
    
    # Metadata
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    job = relationship("Job", back_populates="candidates")
    analysis_result = relationship(
        "AnalysisResult",
        back_populates="candidate",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<Candidate(id={self.id}, name='{self.name}', job_id={self.job_id})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "parsed_text": self.parsed_text[:200] + "..." if len(self.parsed_text) > 200 else self.parsed_text,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "has_analysis": self.analysis_result is not None
        }


class AnalysisResult(Base):
    """
    Analysis Result Model
    Stores LLM analysis results for each candidate
    """
    __tablename__ = "analysis_results"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Foreign Key
    candidate_id = Column(
        Integer,
        ForeignKey("candidates.id"),
        nullable=False,
        unique=True,
        index=True
    )
    
    # Analysis Results
    relevance_score = Column(Float, nullable=False, index=True)  # 0-100
    matched_skills = Column(JSON, nullable=True)  # List of matched skills
    missing_skills = Column(JSON, nullable=True)  # List of missing skills
    feedback = Column(Text, nullable=True)  # LLM generated feedback
    
    # Additional Analysis
    strengths = Column(JSON, nullable=True)  # List of candidate strengths
    weaknesses = Column(JSON, nullable=True)  # List of areas for improvement
    experience_match = Column(Float, nullable=True)  # Experience level match (0-100)
    education_match = Column(Float, nullable=True)  # Education match (0-100)
    
    # Status
    status = Column(
        Enum(AnalysisStatus),
        default=AnalysisStatus.PENDING,
        nullable=False,
        index=True
    )
    
    # Error Handling
    error_message = Column(Text, nullable=True)
    
    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    analysis_duration = Column(Float, nullable=True)  # Duration in seconds
    
    # LLM Details
    llm_model = Column(String(100), nullable=True)  # Model used for analysis
    llm_tokens_used = Column(Integer, nullable=True)  # Tokens consumed
    
    # Relationships
    candidate = relationship("Candidate", back_populates="analysis_result")
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, candidate_id={self.candidate_id}, score={self.relevance_score})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "relevance_score": self.relevance_score,
            "matched_skills": self.matched_skills,
            "missing_skills": self.missing_skills,
            "feedback": self.feedback,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "experience_match": self.experience_match,
            "education_match": self.education_match,
            "status": self.status.value,
            "error_message": self.error_message,
            "analyzed_at": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "analysis_duration": self.analysis_duration,
            "llm_model": self.llm_model,
            "llm_tokens_used": self.llm_tokens_used
        }