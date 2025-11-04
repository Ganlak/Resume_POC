"""
Configuration Management Module
Loads and validates environment variables using Pydantic Settings
"""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings
    Loads configuration from environment variables
    """
    
    # ==========================================
    # Application Settings
    # ==========================================
    APP_NAME: str = Field(default="Candidate-Job Matcher")
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=True)
    LOG_LEVEL: str = Field(default="INFO")
    
    # ==========================================
    # Azure OpenAI Configuration
    # ==========================================
    AZURE_OPENAI_ENDPOINT: str = Field(...)
    AZURE_OPENAI_API_KEY: str = Field(...)
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = Field(...)
    AZURE_OPENAI_EMBED_DEPLOYMENT: Optional[str] = Field(default=None)
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-12-01-preview")
    AZURE_OPENAI_MODEL: str = Field(default="gpt-4.1")
    
    # LLM Provider
    LLM_PROVIDER: str = Field(default="azure_openai")
    
    # ==========================================
    # Database Configuration
    # ==========================================
    DATABASE_URL: str = Field(default="sqlite:///./data/job_matcher.db")
    DB_POOL_SIZE: int = Field(default=5)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_TIMEOUT: int = Field(default=30)
    
    # ==========================================
    # File Upload Settings
    # ==========================================
    MAX_FILE_SIZE: int = Field(default=10485760)  # 10MB
    ALLOWED_EXTENSIONS: str = Field(default="pdf,docx,txt")
    UPLOAD_FOLDER: str = Field(default="./data/uploads")
    
    # ==========================================
    # Export Settings
    # ==========================================
    EXPORT_FOLDER: str = Field(default="./data/exports")
    EXPORT_FORMATS: str = Field(default="csv,pdf")
    
    # ==========================================
    # LLM Analysis Settings
    # ==========================================
    LLM_TEMPERATURE: float = Field(default=0.3)
    LLM_MAX_TOKENS: int = Field(default=2000)
    LLM_TIMEOUT: int = Field(default=60)
    
    # ==========================================
    # Pagination & Display
    # ==========================================
    RESULTS_PER_PAGE: int = Field(default=10)
    MIN_RELEVANCE_SCORE: int = Field(default=0)
    
    # ==========================================
    # Security
    # ==========================================
    SECRET_KEY: str = Field(default="dev-secret-key-change-in-production")
    
    # ==========================================
    # Feature Flags
    # ==========================================
    ENABLE_BATCH_PROCESSING: bool = Field(default=True)
    ENABLE_CACHING: bool = Field(default=False)
    
    # ==========================================
    # Redis (Optional)
    # ==========================================
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    REDIS_ENABLED: bool = Field(default=False)
    
    # ==========================================
    # Logging
    # ==========================================
    LOG_FILE: str = Field(default="./logs/app.log")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # ==========================================
    # Validators
    # ==========================================
    
    @field_validator("ALLOWED_EXTENSIONS")
    @classmethod
    def validate_extensions(cls, v: str) -> List[str]:
        """Convert comma-separated extensions to list"""
        return [ext.strip().lower() for ext in v.split(",")]
    
    @field_validator("EXPORT_FORMATS")
    @classmethod
    def validate_export_formats(cls, v: str) -> List[str]:
        """Convert comma-separated formats to list"""
        return [fmt.strip().lower() for fmt in v.split(",")]
    
    @field_validator("LLM_TEMPERATURE")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Ensure temperature is between 0 and 1"""
        if not 0 <= v <= 1:
            raise ValueError("LLM_TEMPERATURE must be between 0 and 1")
        return v
    
    @field_validator("MAX_FILE_SIZE")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        """Ensure file size is reasonable (max 50MB)"""
        if v > 52428800:  # 50MB
            raise ValueError("MAX_FILE_SIZE cannot exceed 50MB (52428800 bytes)")
        return v
    
    # ==========================================
    # Helper Methods
    # ==========================================
    
    def get_upload_path(self) -> Path:
        """Get absolute path for upload folder"""
        path = Path(self.UPLOAD_FOLDER)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_export_path(self) -> Path:
        """Get absolute path for export folder"""
        path = Path(self.EXPORT_FOLDER)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_log_path(self) -> Path:
        """Get absolute path for log file"""
        log_path = Path(self.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        return log_path
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.APP_ENV.lower() == "production"
    
    def get_allowed_extensions_set(self) -> set:
        """Get set of allowed file extensions"""
        return set(self.ALLOWED_EXTENSIONS)
    
    def get_database_url(self) -> str:
        """Get database URL with proper formatting"""
        return self.DATABASE_URL


# ==========================================
# Initialize Settings Instance
# ==========================================

def get_settings() -> Settings:
    """
    Get settings instance (singleton pattern)
    """
    return Settings()


# Create global settings instance
settings = get_settings()


# ==========================================
# Utility Functions
# ==========================================

def create_required_directories():
    """
    Create all required directories for the application
    """
    directories = [
        settings.get_upload_path(),
        settings.get_export_path(),
        settings.get_log_path().parent,
        Path("./data")
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep file to track empty directories
        gitkeep = directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()


# Create directories on import
create_required_directories()


if __name__ == "__main__":
    """Test configuration loading"""
    print("=" * 50)
    print("Configuration Loaded Successfully!")
    print("=" * 50)
    print(f"App Name: {settings.APP_NAME}")
    print(f"Environment: {settings.APP_ENV}")
    print(f"LLM Provider: {settings.LLM_PROVIDER}")
    print(f"Azure Endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
    print(f"Database: {settings.DATABASE_URL}")
    print(f"Upload Folder: {settings.get_upload_path()}")
    print(f"Export Folder: {settings.get_export_path()}")
    print(f"Allowed Extensions: {settings.ALLOWED_EXTENSIONS}")
    print(f"Max File Size: {settings.MAX_FILE_SIZE / 1024 / 1024:.2f} MB")
    print("=" * 50)