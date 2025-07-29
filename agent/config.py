"""
Configuration management for ADAS Diagnostics Co-pilot.

This module provides environment-based configuration using Pydantic Settings
for all application components including databases, LLM providers, and automotive-specific settings.
"""

import os
from typing import Optional, List
from enum import Enum

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"
    GROQ = "groq"


class EmbeddingProvider(str, Enum):
    """Supported embedding providers."""
    OPENAI = "openai"
    OLLAMA = "ollama"
    GEMINI = "gemini"


class AppEnvironment(str, Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseSettings):
    """Database configuration."""
    
    # PostgreSQL Configuration
    database_url: str = Field(
        ...,
        description="PostgreSQL connection URL with pgvector support"
    )
    
    # Neo4j Configuration
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URI"
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j username"
    )
    neo4j_password: str = Field(
        ...,
        description="Neo4j password"
    )
    
    # Connection Pool Settings
    min_connections: int = Field(
        default=5,
        description="Minimum database connections in pool"
    )
    max_connections: int = Field(
        default=20,
        description="Maximum database connections in pool"
    )
    
    model_config = {"env_prefix": "", "env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


class LLMConfig(BaseSettings):
    """LLM provider configuration."""
    
    # Provider Selection
    llm_provider: LLMProvider = Field(
        default=LLMProvider.GEMINI,
        description="LLM provider to use"
    )

    # API Configuration
    llm_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        description="Base URL for LLM API"
    )
    llm_api_key: str = Field(
        ...,
        description="API key for LLM provider"
    )
    llm_choice: str = Field(
        default="gemini-1.5-flash",
        description="Specific model to use for chat"
    )

    # Embedding Configuration (Use Gemini for consistency)
    embedding_provider: EmbeddingProvider = Field(
        default=EmbeddingProvider.GEMINI,
        description="Embedding provider to use"
    )
    embedding_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta",
        description="Base URL for embedding API"
    )
    embedding_api_key: str = Field(
        default="",
        description="API key for embedding provider (uses same as LLM)"
    )
    embedding_model: str = Field(
        default="text-embedding-004",
        description="Embedding model to use"
    )
    
    # Ingestion-specific LLM
    ingestion_llm_choice: Optional[str] = Field(
        default=None,
        description="Specific model for ingestion (defaults to llm_choice)"
    )
    
    @validator('ingestion_llm_choice', always=True)
    def set_ingestion_llm_default(cls, v, values):
        """Set default ingestion LLM to main LLM choice."""
        return v or values.get('llm_choice', 'gpt-4o-mini')
    
    model_config = {"env_prefix": "", "env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


class AutomotiveConfig(BaseSettings):
    """Automotive-specific configuration."""
    
    # Processing Configuration
    max_batch_size: int = Field(
        default=50,
        description="Maximum documents to process in a single batch"
    )
    
    # Search Configuration
    vector_search_limit: int = Field(
        default=10,
        description="Default limit for vector search results"
    )
    similarity_threshold: float = Field(
        default=0.7,
        description="Minimum similarity threshold for vector search"
    )
    
    # Knowledge Graph Configuration
    graph_search_limit: int = Field(
        default=20,
        description="Default limit for graph search results"
    )
    max_relationship_depth: int = Field(
        default=3,
        description="Maximum depth for relationship traversal"
    )
    
    # File Processing
    supported_file_types: List[str] = Field(
        default=[".md", ".txt", ".pdf", ".csv", ".json"],
        description="Supported file types for ingestion"
    )
    max_file_size_mb: int = Field(
        default=100,
        description="Maximum file size in MB"
    )
    
    # Mercedes E-Class Specific Configuration
    vehicle_make: str = Field(
        default="Mercedes-Benz",
        description="Vehicle manufacturer"
    )
    vehicle_model: str = Field(
        default="E-Class",
        description="Vehicle model"
    )
    vin_pattern: str = Field(
        default=r"WDD213.*",
        description="Mercedes E-Class VIN pattern"
    )

    # Pattern Matching
    ota_version_pattern: str = Field(
        default=r"v\d+\.\d+\.\d+",
        description="Regex pattern for OTA version detection"
    )
    dtc_code_pattern: str = Field(
        default=r"[BPUC]\d{4}",
        description="Regex pattern for DTC code detection"
    )
    mercedes_part_pattern: str = Field(
        default=r"A\d{3}-\d{3}-\d{2}-\d{2}",
        description="Mercedes part number pattern"
    )
    

    
    model_config = {"env_prefix": "", "env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


class AppConfig(BaseSettings):
    """Main application configuration."""
    
    # Application Settings
    app_env: AppEnvironment = Field(
        default=AppEnvironment.DEVELOPMENT,
        description="Application environment"
    )
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Logging level"
    )
    app_port: int = Field(
        default=8058,
        description="Application port"
    )
    
    # API Configuration
    api_title: str = Field(
        default="ADAS Diagnostics Co-pilot API",
        description="API title"
    )
    api_version: str = Field(
        default="1.0.0",
        description="API version"
    )
    api_description: str = Field(
        default="AI-powered agent for automotive diagnostics and root cause analysis",
        description="API description"
    )
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed CORS methods"
    )
    cors_headers: List[str] = Field(
        default=["*"],
        description="Allowed CORS headers"
    )
    
    # Security
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for session management"
    )
    
    model_config = {"env_prefix": "", "env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


class Settings(BaseSettings):
    """Combined application settings."""

    # Database settings
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # LLM settings
    llm: LLMConfig = Field(default_factory=LLMConfig)

    # Automotive settings
    automotive: AutomotiveConfig = Field(default_factory=AutomotiveConfig)

    # App settings
    app: AppConfig = Field(default_factory=AppConfig)

    model_config = {"env_prefix": "", "extra": "ignore", "env_file": ".env", "env_file_encoding": "utf-8"}

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app.app_env == AppEnvironment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app.app_env == AppEnvironment.PRODUCTION


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings


# Convenience functions for common settings
def get_database_url() -> str:
    """Get database URL."""
    return get_settings().database.database_url


def get_neo4j_config() -> tuple[str, str, str]:
    """Get Neo4j configuration."""
    settings = get_settings()
    return (
        settings.database.neo4j_uri,
        settings.database.neo4j_user,
        settings.database.neo4j_password
    )


def get_llm_config() -> tuple[str, str, str, str]:
    """Get LLM configuration."""
    settings = get_settings()
    return (
        settings.llm.llm_provider.value,
        settings.llm.llm_base_url,
        settings.llm.llm_api_key,
        settings.llm.llm_choice
    )


def get_embedding_config() -> tuple[str, str, str, str]:
    """Get embedding configuration."""
    settings = get_settings()
    return (
        settings.llm.embedding_provider.value,
        settings.llm.embedding_base_url,
        settings.llm.embedding_api_key,
        settings.llm.embedding_model
    )
