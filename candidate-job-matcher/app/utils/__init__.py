"""
Utils Package
Contains utility functions and helpers
"""

from app.utils.validators import (
    validate_file_extension,
    validate_file_size,
    validate_filename,
    validate_uploaded_file,
    validate_text_content,
    validate_email,
    extract_email,
    validate_phone,
    extract_phone,
    extract_name_from_filename,
    extract_name_from_text,
    validate_job_title,
    validate_job_description
)

from app.utils.helpers import (
    generate_unique_filename,
    get_file_hash,
    safe_file_path,
    get_file_size_mb,
    ensure_directory_exists,
    clean_text,
    truncate_text,
    extract_first_n_words,
    format_datetime,
    get_time_ago,
    format_file_size,
    format_percentage,
    safe_get,
    remove_duplicates,
    chunks,
    log_function_call,
    log_error
)

__all__ = [
    # Validators
    "validate_file_extension",
    "validate_file_size",
    "validate_filename",
    "validate_uploaded_file",
    "validate_text_content",
    "validate_email",
    "extract_email",
    "validate_phone",
    "extract_phone",
    "extract_name_from_filename",
    "extract_name_from_text",
    "validate_job_title",
    "validate_job_description",
    
    # Helpers
    "generate_unique_filename",
    "get_file_hash",
    "safe_file_path",
    "get_file_size_mb",
    "ensure_directory_exists",
    "clean_text",
    "truncate_text",
    "extract_first_n_words",
    "format_datetime",
    "get_time_ago",
    "format_file_size",
    "format_percentage",
    "safe_get",
    "remove_duplicates",
    "chunks",
    "log_function_call",
    "log_error",
]