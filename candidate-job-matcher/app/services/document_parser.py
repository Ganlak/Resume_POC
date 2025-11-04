"""
Document Parser Service
Extracts text from PDF, DOCX, and TXT files using LangChain
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import logging
from typing import Tuple, Optional, Dict

# LangChain Document Loaders
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    UnstructuredFileLoader
)

# Validation
from app.utils.validators import (
    validate_uploaded_file,
    validate_text_content,
    extract_email,
    extract_phone,
    extract_name_from_filename,
    extract_name_from_text
)
from app.utils.helpers import clean_text

logger = logging.getLogger(__name__)


# ==========================================
# LangChain-based Document Parsers
# ==========================================

def parse_pdf_langchain(file_path: str) -> Tuple[bool, str, str]:
    """
    Parse PDF using LangChain PyPDFLoader
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Tuple of (success, text_content, error_message)
    """
    try:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        # Combine all pages
        text_content = "\n\n".join([doc.page_content for doc in documents])
        
        if not text_content.strip():
            return False, "", "No text content found in PDF"
        
        logger.info(f"Successfully parsed PDF with LangChain: {file_path}")
        return True, text_content, ""
    
    except Exception as e:
        logger.error(f"Error parsing PDF with LangChain: {e}")
        return False, "", str(e)


def parse_docx_langchain(file_path: str) -> Tuple[bool, str, str]:
    """
    Parse DOCX using LangChain Docx2txtLoader
    
    Args:
        file_path: Path to DOCX file
        
    Returns:
        Tuple of (success, text_content, error_message)
    """
    try:
        loader = Docx2txtLoader(file_path)
        documents = loader.load()
        
        # Combine all document parts
        text_content = "\n\n".join([doc.page_content for doc in documents])
        
        if not text_content.strip():
            return False, "", "No text content found in DOCX"
        
        logger.info(f"Successfully parsed DOCX with LangChain: {file_path}")
        return True, text_content, ""
    
    except Exception as e:
        logger.error(f"Error parsing DOCX with LangChain: {e}")
        return False, "", str(e)


def parse_txt_langchain(file_path: str) -> Tuple[bool, str, str]:
    """
    Parse TXT using LangChain TextLoader
    
    Args:
        file_path: Path to TXT file
        
    Returns:
        Tuple of (success, text_content, error_message)
    """
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                loader = TextLoader(file_path, encoding=encoding)
                documents = loader.load()
                
                text_content = "\n\n".join([doc.page_content for doc in documents])
                
                if text_content.strip():
                    logger.info(f"Successfully parsed TXT with LangChain ({encoding}): {file_path}")
                    return True, text_content, ""
            
            except Exception:
                continue
        
        return False, "", "Failed to parse TXT with supported encodings"
    
    except Exception as e:
        logger.error(f"Error parsing TXT with LangChain: {e}")
        return False, "", str(e)


def parse_unstructured_fallback(file_path: str) -> Tuple[bool, str, str]:
    """
    Fallback parser using UnstructuredFileLoader
    Handles various file types automatically
    
    Args:
        file_path: Path to file
        
    Returns:
        Tuple of (success, text_content, error_message)
    """
    try:
        loader = UnstructuredFileLoader(file_path)
        documents = loader.load()
        
        text_content = "\n\n".join([doc.page_content for doc in documents])
        
        if not text_content.strip():
            return False, "", "No text content found"
        
        logger.info(f"Successfully parsed with UnstructuredFileLoader: {file_path}")
        return True, text_content, ""
    
    except Exception as e:
        logger.error(f"Error with UnstructuredFileLoader: {e}")
        return False, "", str(e)


# ==========================================
# Main Document Parser
# ==========================================

def parse_document(file_path: str, file_type: str) -> Tuple[bool, str, str]:
    """
    Parse document based on file type using LangChain
    
    Args:
        file_path: Path to file
        file_type: File extension (pdf, docx, txt)
        
    Returns:
        Tuple of (success, text_content, error_message)
    """
    file_type = file_type.lower().strip('.')
    
    # Try specific loader first
    if file_type == 'pdf':
        success, text, error = parse_pdf_langchain(file_path)
    elif file_type == 'docx':
        success, text, error = parse_docx_langchain(file_path)
    elif file_type == 'txt':
        success, text, error = parse_txt_langchain(file_path)
    else:
        return False, "", f"Unsupported file type: {file_type}"
    
    # If specific loader failed, try fallback
    if not success or not text.strip():
        logger.info(f"Primary parser failed, trying fallback for {file_path}")
        success, text, error = parse_unstructured_fallback(file_path)
    
    return success, text, error


# ==========================================
# Resume Information Extractor
# ==========================================

def extract_candidate_info(text: str, filename: str) -> Dict[str, Optional[str]]:
    """
    Extract candidate information from resume text
    
    Args:
        text: Resume text content
        filename: Original filename
        
    Returns:
        Dictionary with extracted information
    """
    info = {
        "name": None,
        "email": None,
        "phone": None
    }
    
    # Extract email
    info["email"] = extract_email(text)
    
    # Extract phone
    info["phone"] = extract_phone(text)
    
    # Extract name (try from text first, then filename)
    info["name"] = extract_name_from_text(text)
    
    if not info["name"]:
        info["name"] = extract_name_from_filename(filename)
    
    # If still no name, use filename without extension
    if not info["name"]:
        info["name"] = Path(filename).stem.replace('_', ' ').replace('-', ' ').title()
    
    return info


# ==========================================
# Complete Resume Parser
# ==========================================

def parse_resume(
    file_path: str,
    filename: str,
    file_size: int
) -> Dict[str, any]:
    """
    Complete resume parsing with validation and extraction using LangChain
    
    Args:
        file_path: Path to resume file
        filename: Original filename
        file_size: File size in bytes
        
    Returns:
        Dictionary with parsing results
    """
    result = {
        "success": False,
        "text": "",
        "cleaned_text": "",
        "candidate_info": {},
        "error": None,
        "file_info": {
            "filename": filename,
            "file_size": file_size,
            "file_type": Path(filename).suffix.lower().strip('.')
        }
    }
    
    # Validate file
    is_valid, message = validate_uploaded_file(filename, file_size)
    if not is_valid:
        result["error"] = message
        return result
    
    # Parse document using LangChain
    file_type = result["file_info"]["file_type"]
    success, text, error = parse_document(file_path, file_type)
    
    if not success:
        result["error"] = error
        return result
    
    result["text"] = text
    
    # Clean text
    cleaned = clean_text(text)
    result["cleaned_text"] = cleaned
    
    # Validate text content
    is_valid, message = validate_text_content(cleaned, min_length=50)
    if not is_valid:
        result["error"] = message
        return result
    
    # Extract candidate information
    candidate_info = extract_candidate_info(cleaned, filename)
    result["candidate_info"] = candidate_info
    
    result["success"] = True
    
    logger.info(f"Successfully parsed resume: {filename}")
    logger.info(f"  - Name: {candidate_info.get('name')}")
    logger.info(f"  - Email: {candidate_info.get('email')}")
    logger.info(f"  - Phone: {candidate_info.get('phone')}")
    logger.info(f"  - Text length: {len(cleaned)} characters")
    
    return result


# ==========================================
# Batch Processing
# ==========================================

def parse_multiple_resumes(file_paths: list) -> list:
    """
    Parse multiple resumes in batch
    
    Args:
        file_paths: List of tuples (file_path, filename, file_size)
        
    Returns:
        List of parsing results
    """
    results = []
    
    for file_path, filename, file_size in file_paths:
        result = parse_resume(file_path, filename, file_size)
        results.append(result)
    
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"Batch parsing complete: {success_count}/{len(results)} successful")
    
    return results


# ==========================================
# Test Functions
# ==========================================

if __name__ == "__main__":
    """Test document parser with LangChain"""
    
    print("=" * 60)
    print("LangChain Document Parser Test")
    print("=" * 60)
    
    # Create test text file
    test_file_path = Path("test_resume.txt")
    test_content = """
    JOHN DOE
    Software Engineer
    
    Email: john.doe@example.com
    Phone: +1-123-456-7890
    
    EXPERIENCE
    Senior Software Engineer at Tech Corp
    - Developed web applications using Python and React
    - Led team of 5 developers
    - Implemented CI/CD pipelines
    
    SKILLS
    Python, JavaScript, React, SQL, Docker, AWS
    
    EDUCATION
    BS Computer Science, MIT, 2015
    """
    
    # Write test file
    with open(test_file_path, 'w') as f:
        f.write(test_content)
    
    print("\nTest File Created: test_resume.txt")
    print("\nParsing Resume with LangChain...")
    
    # Parse resume
    result = parse_resume(
        file_path=str(test_file_path),
        filename="test_resume.txt",
        file_size=test_file_path.stat().st_size
    )
    
    # Display results
    print("\n" + "=" * 60)
    print("PARSING RESULTS")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Error: {result['error']}")
    print(f"\nCandidate Information:")
    print(f"  Name: {result['candidate_info'].get('name')}")
    print(f"  Email: {result['candidate_info'].get('email')}")
    print(f"  Phone: {result['candidate_info'].get('phone')}")
    print(f"\nText Length: {len(result['cleaned_text'])} characters")
    print(f"\nFirst 200 characters:")
    print(result['cleaned_text'][:200])
    
    # Cleanup
    test_file_path.unlink()
    print("\n" + "=" * 60)
    print("Test file cleaned up")
    print("LangChain parsing successful!")