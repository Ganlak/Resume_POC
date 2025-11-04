"""
Validation Utilities
Input validation functions for file uploads and data
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import re
import os
from typing import Tuple, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


# ==========================================
# File Validation
# ==========================================

def validate_file_extension(filename: str) -> Tuple[bool, str]:
    """
    Validate if file has an allowed extension
    
    Args:
        filename: Name of the file to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not filename:
        return False, "Filename is empty"
    
    # Get file extension
    file_ext = Path(filename).suffix.lower().lstrip('.')
    
    # Check against allowed extensions
    allowed_extensions = settings.get_allowed_extensions_set()
    
    if file_ext not in allowed_extensions:
        return False, f"File extension '.{file_ext}' not allowed. Allowed: {', '.join(allowed_extensions)}"
    
    return True, "Valid file extension"


def validate_file_size(file_size: int) -> Tuple[bool, str]:
    """
    Validate if file size is within allowed limit
    
    Args:
        file_size: Size of file in bytes
        
    Returns:
        Tuple of (is_valid, message)
    """
    max_size = settings.MAX_FILE_SIZE
    
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        return False, f"File size {actual_mb:.2f}MB exceeds maximum {max_mb:.2f}MB"
    
    if file_size == 0:
        return False, "File is empty"
    
    return True, "Valid file size"


def validate_filename(filename: str) -> Tuple[bool, str]:
    """
    Validate filename for security (prevent path traversal)
    
    Args:
        filename: Name of the file to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not filename:
        return False, "Filename is empty"
    
    # Check for path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        return False, "Invalid filename: path traversal detected"
    
    # Check for special characters
    if not re.match(r'^[a-zA-Z0-9._\-\s()]+$', filename):
        return False, "Invalid filename: contains special characters"
    
    return True, "Valid filename"


def validate_uploaded_file(filename: str, file_size: int) -> Tuple[bool, str]:
    """
    Comprehensive validation for uploaded files
    
    Args:
        filename: Name of the file
        file_size: Size of file in bytes
        
    Returns:
        Tuple of (is_valid, message)
    """
    # Validate filename
    is_valid, message = validate_filename(filename)
    if not is_valid:
        return False, message
    
    # Validate extension
    is_valid, message = validate_file_extension(filename)
    if not is_valid:
        return False, message
    
    # Validate size
    is_valid, message = validate_file_size(file_size)
    if not is_valid:
        return False, message
    
    return True, "File validation passed"


# ==========================================
# Text Content Validation
# ==========================================

def validate_text_content(text: str, min_length: int = 50) -> Tuple[bool, str]:
    """
    Validate if extracted text content is sufficient
    
    Args:
        text: Extracted text content
        min_length: Minimum required text length
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not text or not text.strip():
        return False, "No text content found in document"
    
    cleaned_text = text.strip()
    
    if len(cleaned_text) < min_length:
        return False, f"Text content too short (minimum {min_length} characters required)"
    
    return True, "Valid text content"


# ==========================================
# Email Validation
# ==========================================

def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid email format
    """
    if not email:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def extract_email(text: str) -> Optional[str]:
    """
    Extract email address from text
    
    Args:
        text: Text to search for email
        
    Returns:
        First email found or None
    """
    email_pattern = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
    matches = re.findall(email_pattern, text)
    
    if matches:
        return matches[0]
    return None


# ==========================================
# Phone Number Validation
# ==========================================

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        bool: True if valid phone format
    """
    if not phone:
        return False
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    # Check if it's a valid phone number (10-15 digits)
    return bool(re.match(r'^\+?\d{10,15}$', cleaned))


def extract_phone(text: str) -> Optional[str]:
    """
    Extract phone number from text
    
    Args:
        text: Text to search for phone number
        
    Returns:
        First phone number found or None
    """
    # Common phone patterns
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-123-456-7890
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # (123) 456-7890
        r'\d{10}',  # 1234567890
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]
    
    return None


# ==========================================
# Name Extraction
# ==========================================

def extract_name_from_filename(filename: str) -> Optional[str]:
    """
    Extract candidate name from filename
    Common patterns: "John_Doe_Resume.pdf", "Jane-Smith-CV.docx"
    
    Args:
        filename: File name to extract from
        
    Returns:
        Extracted name or None
    """
    # Remove extension
    name = Path(filename).stem
    
    # Remove common keywords
    keywords = ['resume', 'cv', 'curriculum', 'vitae', 'updated', 'final', 'latest']
    for keyword in keywords:
        name = re.sub(keyword, '', name, flags=re.IGNORECASE)
    
    # Replace separators with spaces
    name = re.sub(r'[_\-\.]', ' ', name)
    
    # Remove extra spaces
    name = ' '.join(name.split())
    
    # Title case
    name = name.title()
    
    # Return only if it looks like a valid name (2-50 chars, letters only)
    if 2 <= len(name) <= 50 and re.match(r'^[a-zA-Z\s]+$', name):
        return name
    
    return None


def extract_name_from_text(text: str) -> Optional[str]:
    """
    Extract candidate name from resume text
    Usually appears at the top of the document
    
    Args:
        text: Resume text content
        
    Returns:
        Extracted name or None
    """
    # Get first few lines
    lines = text.split('\n')[:5]
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and lines with emails/phones
        if not line or '@' in line or re.search(r'\d{10}', line):
            continue
        
        # Check if line looks like a name (2-4 words, mostly letters)
        words = line.split()
        if 2 <= len(words) <= 4:
            # Check if mostly alphabetic
            if all(re.match(r'^[a-zA-Z\s\.\-]+$', word) for word in words):
                return line.title()
    
    return None


# ==========================================
# Job Title Validation
# ==========================================

def validate_job_title(title: str) -> Tuple[bool, str]:
    """
    Validate job title
    
    Args:
        title: Job title to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not title or not title.strip():
        return False, "Job title is required"
    
    if len(title.strip()) < 3:
        return False, "Job title too short (minimum 3 characters)"
    
    if len(title) > 255:
        return False, "Job title too long (maximum 255 characters)"
    
    return True, "Valid job title"


def validate_job_description(description: str) -> Tuple[bool, str]:
    """
    Validate job description
    
    Args:
        description: Job description to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not description or not description.strip():
        return False, "Job description is required"
    
    if len(description.strip()) < 50:
        return False, "Job description too short (minimum 50 characters)"
    
    return True, "Valid job description"


# ==========================================
# Test Functions
# ==========================================

if __name__ == "__main__":
    """Test validation functions"""
    
    print("=" * 60)
    print("Testing Validation Functions")
    print("=" * 60)
    
    # Test file extension
    print("\n1. File Extension Validation:")
    test_files = ["resume.pdf", "cv.docx", "profile.txt", "invalid.exe"]
    for filename in test_files:
        valid, msg = validate_file_extension(filename)
        print(f"  {filename}: {'VALID' if valid else 'INVALID'} - {msg}")
    
    # Test file size
    print("\n2. File Size Validation:")
    test_sizes = [1024, 5242880, 15728640]  # 1KB, 5MB, 15MB
    for size in test_sizes:
        valid, msg = validate_file_size(size)
        print(f"  {size} bytes: {'VALID' if valid else 'INVALID'} - {msg}")
    
    # Test email extraction
    print("\n3. Email Extraction:")
    test_text = "Contact me at john.doe@example.com or call 123-456-7890"
    email = extract_email(test_text)
    print(f"  Extracted: {email}")
    
    # Test phone extraction
    print("\n4. Phone Extraction:")
    phone = extract_phone(test_text)
    print(f"  Extracted: {phone}")
    
    # Test name extraction from filename
    print("\n5. Name from Filename:")
    test_filenames = ["John_Doe_Resume.pdf", "Jane-Smith-CV.docx", "document123.txt"]
    for filename in test_filenames:
        name = extract_name_from_filename(filename)
        print(f"  {filename} -> {name}")
    
    print("\n" + "=" * 60)