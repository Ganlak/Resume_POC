"""
Analysis Service
Orchestrates the complete candidate analysis workflow
Combines document parsing, LLM analysis, and database storage
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from typing import Dict, Optional, List
from datetime import datetime

from app.database import DatabaseSession, Candidate, AnalysisResult, Job, AnalysisStatus
from app.services.document_parser import parse_resume
from app.services.llm_analyzer import analyze_candidate
from app.utils.helpers import format_file_size, get_time_ago

logger = logging.getLogger(__name__)


# ==========================================
# Complete Analysis Workflow
# ==========================================

def analyze_and_store_candidate(
    candidate_id: int,
    job_id: int
) -> Dict:
    """
    Complete workflow: Fetch candidate, analyze, and store results
    
    Args:
        candidate_id: Candidate database ID
        job_id: Job database ID
        
    Returns:
        Dictionary with analysis results and status
    """
    result = {
        "success": False,
        "candidate_id": candidate_id,
        "job_id": job_id,
        "analysis_result": None,
        "error": None
    }
    
    try:
        with DatabaseSession() as db:
            # Fetch candidate
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if not candidate:
                result["error"] = f"Candidate {candidate_id} not found"
                return result
            
            # Fetch job
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                result["error"] = f"Job {job_id} not found"
                return result
            
            # Check if analysis already exists
            existing_analysis = db.query(AnalysisResult).filter(
                AnalysisResult.candidate_id == candidate_id
            ).first()
            
            if existing_analysis:
                # Update status to processing
                existing_analysis.status = AnalysisStatus.PROCESSING
                db.commit()
            else:
                # Create new analysis record
                new_analysis = AnalysisResult(
                    candidate_id=candidate_id,
                    relevance_score=0.0,
                    status=AnalysisStatus.PROCESSING
                )
                db.add(new_analysis)
                db.commit()
                existing_analysis = new_analysis
            
            logger.info(f"Starting analysis for candidate {candidate_id} on job {job_id}")
            
            # Perform LLM analysis
            analysis_result = analyze_candidate(
                resume_text=candidate.parsed_text,
                job_description=job.description,
                job_title=job.title,
                job_requirements=job.requirements
            )
            
            if not analysis_result["success"]:
                # Update status to failed
                existing_analysis.status = AnalysisStatus.FAILED
                existing_analysis.error_message = analysis_result["error"]
                db.commit()
                
                result["error"] = analysis_result["error"]
                return result
            
            # Extract analysis data
            analysis_data = analysis_result["analysis"]
            metadata = analysis_result["metadata"]
            
            # Update analysis record
            existing_analysis.relevance_score = analysis_data["relevance_score"]
            existing_analysis.matched_skills = analysis_data["matched_skills"]
            existing_analysis.missing_skills = analysis_data["missing_skills"]
            existing_analysis.feedback = analysis_data["feedback"]
            existing_analysis.strengths = analysis_data.get("strengths", [])
            existing_analysis.weaknesses = analysis_data.get("weaknesses", [])
            existing_analysis.experience_match = analysis_data.get("experience_match")
            existing_analysis.education_match = analysis_data.get("education_match")
            existing_analysis.status = AnalysisStatus.COMPLETED
            existing_analysis.llm_model = metadata["model"]
            existing_analysis.llm_tokens_used = metadata["tokens_used"]
            existing_analysis.analysis_duration = metadata["duration_seconds"]
            existing_analysis.error_message = None
            
            db.commit()
            
            logger.info(f"Analysis completed for candidate {candidate_id}")
            logger.info(f"  Relevance Score: {existing_analysis.relevance_score}")
            
            result["success"] = True
            result["analysis_result"] = existing_analysis.to_dict()
            
            return result
    
    except Exception as e:
        logger.error(f"Error in analysis workflow: {e}")
        result["error"] = str(e)
        
        # Try to update status to failed
        try:
            with DatabaseSession() as db:
                analysis = db.query(AnalysisResult).filter(
                    AnalysisResult.candidate_id == candidate_id
                ).first()
                if analysis:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.error_message = str(e)
                    db.commit()
        except Exception as db_error:
            logger.error(f"Failed to update analysis status: {db_error}")
        
        return result


# ==========================================
# Batch Analysis
# ==========================================

def analyze_all_candidates_for_job(job_id: int) -> Dict:
    """
    Analyze all candidates for a specific job
    
    Args:
        job_id: Job database ID
        
    Returns:
        Dictionary with batch analysis results
    """
    result = {
        "success": False,
        "job_id": job_id,
        "total_candidates": 0,
        "analyzed": 0,
        "failed": 0,
        "results": [],
        "error": None
    }
    
    try:
        with DatabaseSession() as db:
            # Fetch job
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                result["error"] = f"Job {job_id} not found"
                return result
            
            # Fetch all candidates for this job
            candidates = db.query(Candidate).filter(Candidate.job_id == job_id).all()
            result["total_candidates"] = len(candidates)
            
            if not candidates:
                result["error"] = "No candidates found for this job"
                return result
            
            logger.info(f"Starting batch analysis for {len(candidates)} candidates")
            
            # Analyze each candidate
            for candidate in candidates:
                logger.info(f"Analyzing candidate {candidate.id}: {candidate.name}")
                
                analysis_result = analyze_and_store_candidate(
                    candidate_id=candidate.id,
                    job_id=job_id
                )
                
                result["results"].append(analysis_result)
                
                if analysis_result["success"]:
                    result["analyzed"] += 1
                else:
                    result["failed"] += 1
            
            result["success"] = True
            logger.info(f"Batch analysis complete: {result['analyzed']}/{result['total_candidates']} successful")
            
            return result
    
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        result["error"] = str(e)
        return result


# ==========================================
# Get Analysis Results
# ==========================================

def get_candidates_with_analysis(job_id: int, sort_by: str = "score") -> List[Dict]:
    """
    Get all candidates with their analysis results for a job
    
    Args:
        job_id: Job database ID
        sort_by: Sort criteria ("score", "name", "date")
        
    Returns:
        List of candidates with analysis data
    """
    try:
        with DatabaseSession() as db:
            # Query candidates with their analysis results
            candidates = db.query(Candidate).filter(
                Candidate.job_id == job_id
            ).all()
            
            results = []
            
            for candidate in candidates:
                candidate_data = {
                    "id": candidate.id,
                    "name": candidate.name,
                    "email": candidate.email,
                    "phone": candidate.phone,
                    "file_name": candidate.file_name,
                    "uploaded_at": candidate.uploaded_at,
                    "analysis": None,
                    "has_analysis": False
                }
                
                # Get analysis if exists
                if candidate.analysis_result:
                    analysis = candidate.analysis_result
                    candidate_data["analysis"] = {
                        "relevance_score": analysis.relevance_score,
                        "matched_skills": analysis.matched_skills,
                        "missing_skills": analysis.missing_skills,
                        "feedback": analysis.feedback,
                        "strengths": analysis.strengths,
                        "weaknesses": analysis.weaknesses,
                        "experience_match": analysis.experience_match,
                        "education_match": analysis.education_match,
                        "status": analysis.status.value,
                        "analyzed_at": analysis.analyzed_at,
                        "error_message": analysis.error_message
                    }
                    candidate_data["has_analysis"] = analysis.status == AnalysisStatus.COMPLETED
                
                results.append(candidate_data)
            
            # Sort results
            if sort_by == "score":
                results.sort(
                    key=lambda x: x["analysis"]["relevance_score"] if x["has_analysis"] else -1,
                    reverse=True
                )
            elif sort_by == "name":
                results.sort(key=lambda x: x["name"])
            elif sort_by == "date":
                results.sort(key=lambda x: x["uploaded_at"], reverse=True)
            
            return results
    
    except Exception as e:
        logger.error(f"Error fetching candidates with analysis: {e}")
        return []


# ==========================================
# Statistics
# ==========================================

def get_analysis_statistics(job_id: int) -> Dict:
    """
    Get analysis statistics for a job
    
    Args:
        job_id: Job database ID
        
    Returns:
        Dictionary with statistics
    """
    try:
        with DatabaseSession() as db:
            candidates = db.query(Candidate).filter(Candidate.job_id == job_id).all()
            
            total = len(candidates)
            analyzed = 0
            pending = 0
            failed = 0
            total_score = 0
            
            for candidate in candidates:
                if candidate.analysis_result:
                    if candidate.analysis_result.status == AnalysisStatus.COMPLETED:
                        analyzed += 1
                        total_score += candidate.analysis_result.relevance_score
                    elif candidate.analysis_result.status == AnalysisStatus.FAILED:
                        failed += 1
                    else:
                        pending += 1
                else:
                    pending += 1
            
            avg_score = (total_score / analyzed) if analyzed > 0 else 0
            
            return {
                "total_candidates": total,
                "analyzed": analyzed,
                "pending": pending,
                "failed": failed,
                "average_score": round(avg_score, 2),
                "completion_rate": round((analyzed / total * 100), 2) if total > 0 else 0
            }
    
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        return {
            "total_candidates": 0,
            "analyzed": 0,
            "pending": 0,
            "failed": 0,
            "average_score": 0,
            "completion_rate": 0
        }


# ==========================================
# Test Function
# ==========================================

if __name__ == "__main__":
    """Test analysis service"""
    
    print("=" * 60)
    print("Analysis Service Test")
    print("=" * 60)
    print("\nThis module requires database records to test.")
    print("Use the Streamlit UI to test complete workflow.")
    print("=" * 60)