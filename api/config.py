import os
import logging
from typing import Dict, Any

# Configure logger
logger = logging.getLogger(__name__)

class Config:
    """
    Configuration settings for the Global TimeSync API.
    """
    # API settings
    API_VERSION = "1.0.0"
    API_TITLE = "Global TimeSync API"
    API_DESCRIPTION = "A high-performance API for UTC to local time conversion with automatic DST handling"
    
    # Server settings
    HOST = "0.0.0.0"
    PORT = 5000
    
    # Authentication settings
    JWT_SECRET = os.environ.get("JWT_SECRET", "insecure_default_secret_key_for_development")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_MINUTES = 30
    
    # Cache settings
    DEFAULT_CACHE_TTL = 3600  # 1 hour
    TIMEZONE_INFO_CACHE_TTL = 300  # 5 minutes
    
    # Performance settings
    MAX_WORKERS = os.environ.get("MAX_WORKERS", 4)
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        Excludes private attributes (starting with _).
        """
        return {key: value for key, value in cls.__dict__.items() 
                if not key.startswith('_') and not callable(value)}
    
    @classmethod
    def log_config(cls) -> None:
        """
        Log the current configuration (excluding sensitive data).
        """
        config_dict = cls.to_dict()
        
        # Remove sensitive information
        if 'JWT_SECRET' in config_dict:
            config_dict['JWT_SECRET'] = '***REDACTED***'
        
        logger.info(f"Application Configuration: {config_dict}")
