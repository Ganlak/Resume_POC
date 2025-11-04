"""
LLM Analyzer Service
Uses Azure OpenAI to analyze candidate resumes against job descriptions
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
import time

from openai import AzureOpenAI
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from app.config import settings

logger = logging.getLogger(__name__)


# ==========================================
# Azure OpenAI Client Setup
# ==========================================

class AzureOpenAIClient:
    """
    Azure OpenAI client wrapper with retry logic
    """
    
    def __init__(self):
        """Initialize Azure OpenAI client"""
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = settings.AZURE_OPENAI_CHAT_DEPLOYMENT
        self.model = settings.AZURE_OPENAI_MODEL
        
        logger.info(f"Azure OpenAI client initialized")
        logger.info(f"  Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
        logger.info(f"  Deployment: {self.deployment_name}")
        logger.info(f"  Model: {self.model}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception)
    )
    def create_chat_completion(
        self,
        messages: list,
        temperature: float = None,
        max_tokens: int = None,
        response_format: dict = None
    ) -> Dict:
        """
        Create chat completion with retry logic
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            response_format: Response format specification
            
        Returns:
            API response dictionary
        """
        try:
            # Use settings if not provided
            if temperature is None:
                temperature = settings.LLM_TEMPERATURE
            if max_tokens is None:
                max_tokens = settings.LLM_MAX_TOKENS
            
            # Create completion
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format
            )
            
            return response
        
        except Exception as e:
            logger.error(f"Error calling Azure OpenAI: {e}")
            raise


# ==========================================
# Prompt Templates
# ==========================================

SYSTEM_PROMPT = """You are an expert HR recruiter and technical interviewer with years of experience in candidate evaluation. Your task is to analyze candidate resumes against job descriptions and provide detailed, actionable feedback.

You must respond ONLY with valid JSON format. Do not include any explanatory text before or after the JSON.

The JSON must have this exact structure:
{
    "relevance_score": <number between 0-100>,
    "matched_skills": ["skill1", "skill2", ...],
    "missing_skills": ["skill1", "skill2", ...],
    "strengths": ["strength1", "strength2", ...],
    "weaknesses": ["weakness1", "weakness2", ...],
    "experience_match": <number between 0-100>,
    "education_match": <number between 0-100>,
    "feedback": "detailed feedback summary"
}

Guidelines for analysis:
- relevance_score: Overall fit (0-100), consider skills, experience, education
- matched_skills: Skills from job description that candidate has
- missing_skills: Required/preferred skills candidate lacks
- strengths: Candidate's strong points relevant to the role
- weaknesses: Areas where candidate could improve
- experience_match: How well experience level matches (0-100)
- education_match: How well education matches requirements (0-100)
- feedback: 2-3 paragraphs with actionable insights

Be objective, fair, and constructive in your evaluation."""


def create_analysis_prompt(resume_text: str, job_description: str, job_title: str) -> str:
    """
    Create user prompt for resume analysis
    
    Args:
        resume_text: Candidate's resume text
        job_description: Job description text
        job_title: Job title
        
    Returns:
        Formatted prompt string
    """
    prompt = f"""Analyze this candidate's resume for the following job position.

JOB TITLE:
{job_title}

JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME:
{resume_text}

Provide a comprehensive analysis in the specified JSON format. Be thorough but concise."""
    
    return prompt


# ==========================================
# Response Parser
# ==========================================

def parse_llm_response(response_text: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Parse LLM response and validate structure
    
    Args:
        response_text: Raw response text from LLM
        
    Returns:
        Tuple of (success, parsed_data, error_message)
    """
    try:
        # Clean response text
        response_text = response_text.strip()
        
        # Try to find JSON in response
        if "```json" in response_text:
            # Extract JSON from code block
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            # Extract from generic code block
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        # Parse JSON
        data = json.loads(response_text)
        
        # Validate required fields
        required_fields = [
            "relevance_score",
            "matched_skills",
            "missing_skills",
            "feedback"
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return False, None, f"Missing required fields: {', '.join(missing_fields)}"
        
        # Validate data types
        if not isinstance(data["relevance_score"], (int, float)):
            return False, None, "relevance_score must be a number"
        
        if not isinstance(data["matched_skills"], list):
            return False, None, "matched_skills must be a list"
        
        if not isinstance(data["missing_skills"], list):
            return False, None, "missing_skills must be a list"
        
        if not isinstance(data["feedback"], str):
            return False, None, "feedback must be a string"
        
        # Ensure score is in valid range
        data["relevance_score"] = max(0, min(100, float(data["relevance_score"])))
        
        # Set defaults for optional fields
        data.setdefault("strengths", [])
        data.setdefault("weaknesses", [])
        data.setdefault("experience_match", None)
        data.setdefault("education_match", None)
        
        logger.info("Successfully parsed LLM response")
        return True, data, None
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return False, None, f"Invalid JSON format: {str(e)}"
    
    except Exception as e:
        logger.error(f"Error parsing response: {e}")
        return False, None, f"Parsing error: {str(e)}"


# ==========================================
# Main Analysis Function
# ==========================================

def analyze_candidate(
    resume_text: str,
    job_description: str,
    job_title: str,
    job_requirements: Optional[str] = None
) -> Dict:
    """
    Analyze candidate resume against job description using Azure OpenAI
    
    Args:
        resume_text: Candidate's resume text
        job_description: Job description
        job_title: Job title
        job_requirements: Additional job requirements (optional)
        
    Returns:
        Analysis results dictionary
    """
    result = {
        "success": False,
        "analysis": None,
        "error": None,
        "metadata": {
            "model": settings.AZURE_OPENAI_MODEL,
            "deployment": settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "tokens_used": 0,
            "duration_seconds": 0
        }
    }
    
    start_time = time.time()
    
    try:
        # Combine job description with requirements if provided
        full_job_description = job_description
        if job_requirements:
            full_job_description += f"\n\nREQUIREMENTS:\n{job_requirements}"
        
        # Initialize client
        client = AzureOpenAIClient()
        
        # Create prompt
        user_prompt = create_analysis_prompt(
            resume_text=resume_text,
            job_description=full_job_description,
            job_title=job_title
        )
        
        # Prepare messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]
        
        logger.info("Sending request to Azure OpenAI...")
        
        # Call API
        response = client.create_chat_completion(
            messages=messages,
            response_format={"type": "json_object"}
        )
        
        # Extract response
        response_text = response.choices[0].message.content
        
        # Track token usage
        if hasattr(response, 'usage'):
            result["metadata"]["tokens_used"] = response.usage.total_tokens
            logger.info(f"Tokens used: {response.usage.total_tokens}")
        
        # Parse response
        success, analysis_data, error = parse_llm_response(response_text)
        
        if not success:
            result["error"] = error
            return result
        
        # Set results
        result["success"] = True
        result["analysis"] = analysis_data
        
        # Calculate duration
        duration = time.time() - start_time
        result["metadata"]["duration_seconds"] = round(duration, 2)
        
        logger.info(f"Analysis completed successfully in {duration:.2f}s")
        logger.info(f"Relevance Score: {analysis_data['relevance_score']}")
        
        return result
    
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        result["error"] = str(e)
        result["metadata"]["duration_seconds"] = round(time.time() - start_time, 2)
        return result


# ==========================================
# Batch Analysis
# ==========================================

def analyze_multiple_candidates(
    candidates: list,
    job_description: str,
    job_title: str,
    job_requirements: Optional[str] = None
) -> list:
    """
    Analyze multiple candidates in batch
    
    Args:
        candidates: List of dictionaries with 'resume_text' and 'candidate_id'
        job_description: Job description
        job_title: Job title
        job_requirements: Additional requirements
        
    Returns:
        List of analysis results
    """
    results = []
    total = len(candidates)
    
    logger.info(f"Starting batch analysis of {total} candidates")
    
    for idx, candidate in enumerate(candidates, 1):
        logger.info(f"Analyzing candidate {idx}/{total}")
        
        result = analyze_candidate(
            resume_text=candidate["resume_text"],
            job_description=job_description,
            job_title=job_title,
            job_requirements=job_requirements
        )
        
        result["candidate_id"] = candidate.get("candidate_id")
        results.append(result)
    
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"Batch analysis complete: {success_count}/{total} successful")
    
    return results


# ==========================================
# Test Function
# ==========================================

if __name__ == "__main__":
    """Test LLM analyzer"""
    
    print("=" * 60)
    print("Azure OpenAI LLM Analyzer Test")
    print("=" * 60)
    
    # Test data
    test_job_title = "Senior Python Developer"
    
    test_job_description = """
    We are looking for an experienced Python developer to join our team.
    
    Responsibilities:
    - Develop and maintain Python applications
    - Work with Django and Flask frameworks
    - Design and implement REST APIs
    - Write clean, maintainable code
    - Collaborate with cross-functional teams
    
    Requirements:
    - 5+ years of Python development experience
    - Strong knowledge of Django or Flask
    - Experience with PostgreSQL or MySQL
    - Familiarity with Docker and AWS
    - Bachelor's degree in Computer Science or related field
    """
    
    test_resume = """
    JANE SMITH
    Senior Software Engineer
    
    Email: jane.smith@email.com
    Phone: 555-123-4567
    
    EXPERIENCE:
    Senior Python Developer at Tech Solutions (2020-Present)
    - Built scalable web applications using Django
    - Designed RESTful APIs serving 100K+ daily requests
    - Implemented CI/CD pipelines with Docker
    - Mentored junior developers
    
    Python Developer at StartupCo (2018-2020)
    - Developed Flask-based microservices
    - Worked with PostgreSQL databases
    - Deployed applications on AWS EC2
    
    SKILLS:
    Python, Django, Flask, PostgreSQL, Docker, AWS, Git, REST APIs
    
    EDUCATION:
    BS Computer Science, State University, 2018
    """
    
    print("\nAnalyzing candidate...")
    print(f"Job: {test_job_title}")
    
    # Run analysis
    result = analyze_candidate(
        resume_text=test_resume,
        job_description=test_job_description,
        job_title=test_job_title
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("ANALYSIS RESULTS")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Error: {result['error']}")
    
    if result['success']:
        analysis = result['analysis']
        print(f"\nRelevance Score: {analysis['relevance_score']}/100")
        print(f"\nMatched Skills: {', '.join(analysis['matched_skills'])}")
        print(f"\nMissing Skills: {', '.join(analysis['missing_skills'])}")
        print(f"\nFeedback:\n{analysis['feedback']}")
        
        print(f"\nMetadata:")
        print(f"  Model: {result['metadata']['model']}")
        print(f"  Tokens Used: {result['metadata']['tokens_used']}")
        print(f"  Duration: {result['metadata']['duration_seconds']}s")
    
    print("\n" + "=" * 60)