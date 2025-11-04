"""
Services Package
Contains business logic services
"""

from app.services.document_parser import (
    parse_document,
    parse_resume,
    parse_multiple_resumes,
    extract_candidate_info
)

from app.services.llm_analyzer import (
    analyze_candidate,
    analyze_multiple_candidates,
    AzureOpenAIClient
)

from app.services.analysis_service import (
    analyze_and_store_candidate,
    analyze_all_candidates_for_job,
    get_candidates_with_analysis,
    get_analysis_statistics
)

__all__ = [
    # Document Parser
    "parse_document",
    "parse_resume",
    "parse_multiple_resumes",
    "extract_candidate_info",
    
    # LLM Analyzer
    "analyze_candidate",
    "analyze_multiple_candidates",
    "AzureOpenAIClient",
    
    # Analysis Service
    "analyze_and_store_candidate",
    "analyze_all_candidates_for_job",
    "get_candidates_with_analysis",
    "get_analysis_statistics",
]