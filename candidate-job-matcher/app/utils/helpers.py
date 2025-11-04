"""
Helper Utilities
Common utility functions used across the application
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import os
import uuid
import hashlib
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


# ==========================================
# File Operations
# ==========================================

def generate_unique_filename(original_filename: str) -> str:
    """
    Generate a unique filename to prevent collisions
    
    Args:
        original_filename: Original file name
        
    Returns:
        Unique filename with timestamp and UUID
    """
    # Get file extension
    file_ext = Path(original_filename).suffix
    
    # Get base name without extension
    base_name = Path(original_filename).stem
    
    # Clean base name (remove special chars)
    clean_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_'))
    clean_name = clean_name[:50]  # Limit length
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Generate short UUID
    short_uuid = str(uuid.uuid4())[:8]
    
    # Combine
    unique_filename = f"{clean_name}_{timestamp}_{short_uuid}{file_ext}"
    
    return unique_filename


def get_file_hash(file_path: str) -> str:
    """
    Calculate MD5 hash of a file
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash string
    """
    hash_md5 = hashlib.md5()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    
    return hash_md5.hexdigest()


def safe_file_path(directory: str, filename: str) -> Path:
    """
    Create a safe file path preventing directory traversal
    
    Args:
        directory: Target directory
        filename: File name
        
    Returns:
        Safe Path object
    """
    # Resolve directory path
    base_dir = Path(directory).resolve()
    
    # Clean filename
    safe_filename = Path(filename).name
    
    # Combine paths
    file_path = (base_dir / safe_filename).resolve()
    
    # Ensure file is within base directory
    if not str(file_path).startswith(str(base_dir)):
        raise ValueError("Invalid file path: directory traversal detected")
    
    return file_path


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes
    
    Args:
        file_path: Path to the file
        
    Returns:
        File size in MB
    """
    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 * 1024)
    return round(size_mb, 2)


def ensure_directory_exists(directory: str) -> Path:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        directory: Directory path
        
    Returns:
        Path object of the directory
    """
    dir_path = Path(directory)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


# ==========================================
# Text Processing
# ==========================================

def clean_text(text: str) -> str:
    """
    Clean and normalize text content
    
    Args:
        text: Raw text content
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove multiple spaces
    text = " ".join(text.split())
    
    # Remove multiple newlines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    return text


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to specified length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_first_n_words(text: str, n: int = 50) -> str:
    """
    Extract first N words from text
    
    Args:
        text: Input text
        n: Number of words to extract
        
    Returns:
        First N words
    """
    if not text:
        return ""
    
    words = text.split()
    return " ".join(words[:n])


# ==========================================
# Date/Time Helpers
# ==========================================

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime object to string
    
    Args:
        dt: Datetime object
        format_str: Format string
        
    Returns:
        Formatted datetime string
    """
    if not dt:
        return ""
    
    return dt.strftime(format_str)


def get_time_ago(dt: datetime) -> str:
    """
    Get human-readable time difference
    
    Args:
        dt: Past datetime
        
    Returns:
        Human-readable string like "2 hours ago"
    """
    if not dt:
        return "Unknown"
    
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 2592000:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        return format_datetime(dt, "%Y-%m-%d")


# ==========================================
# Number Formatting
# ==========================================

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string like "1.5 MB"
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format number as percentage
    
    Args:
        value: Number (0-100)
        decimals: Decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value:.{decimals}f}%"


# ==========================================
# List/Dict Helpers
# ==========================================

def safe_get(dictionary: dict, key: str, default=None):
    """
    Safely get value from dictionary
    
    Args:
        dictionary: Dictionary to get from
        key: Key to look for
        default: Default value if key not found
        
    Returns:
        Value or default
    """
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default


def remove_duplicates(items: list) -> list:
    """
    Remove duplicates from list while preserving order
    
    Args:
        items: List with potential duplicates
        
    Returns:
        List without duplicates
    """
    seen = set()
    result = []
    
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    
    return result


def chunks(lst: list, n: int):
    """
    Split list into chunks of size n
    
    Args:
        lst: List to split
        n: Chunk size
        
    Yields:
        Chunks of the list
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# ==========================================
# Logging Helpers
# ==========================================

def log_function_call(func_name: str, **kwargs):
    """
    Log function call with parameters
    
    Args:
        func_name: Name of the function
        **kwargs: Function parameters
    """
    params = ", ".join(f"{k}={v}" for k, v in kwargs.items())
    logger.info(f"Calling {func_name}({params})")


def log_error(error: Exception, context: str = ""):
    """
    Log error with context
    
    Args:
        error: Exception object
        context: Additional context information
    """
    error_msg = f"Error in {context}: {type(error).__name__} - {str(error)}"
    logger.error(error_msg)


# ==========================================
# Test Functions
# ==========================================

if __name__ == "__main__":
    """Test helper functions"""
    
    print("=" * 60)
    print("Testing Helper Functions")
    print("=" * 60)
    
    # Test unique filename generation
    print("\n1. Unique Filename Generation:")
    original = "John_Doe_Resume.pdf"
    unique = generate_unique_filename(original)
    print(f"  Original: {original}")
    print(f"  Unique: {unique}")
    
    # Test text truncation
    print("\n2. Text Truncation:")
    long_text = "This is a very long text that needs to be truncated for display purposes."
    truncated = truncate_text(long_text, 30)
    print(f"  Original: {long_text}")
    print(f"  Truncated: {truncated}")
    
    # Test file size formatting
    print("\n3. File Size Formatting:")
    sizes = [500, 2048, 1048576, 1073741824]
    for size in sizes:
        formatted = format_file_size(size)
        print(f"  {size} bytes -> {formatted}")
    
    # Test time ago
    print("\n4. Time Ago:")
    from datetime import timedelta
    times = [
        datetime.utcnow() - timedelta(minutes=5),
        datetime.utcnow() - timedelta(hours=2),
        datetime.utcnow() - timedelta(days=3),
    ]
    for dt in times:
        ago = get_time_ago(dt)
        print(f"  {format_datetime(dt)} -> {ago}")
    
    # Test percentage formatting
    print("\n5. Percentage Formatting:")
    values = [85.5, 92.125, 67.0]
    for val in values:
        formatted = format_percentage(val)
        print(f"  {val} -> {formatted}")
    
    print("\n" + "=" * 60)