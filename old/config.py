import os
from datetime import datetime

class Config:
    """Base configuration"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:5000')

    # Mission elapsed time start
    _mission_start = os.getenv('MISSION_START_TIME', '2025-01-01T00:00:00Z')
    try:
        MISSION_START_TIME = datetime.fromisoformat(_mission_start.replace('Z', '+00:00'))
    except ValueError:
        MISSION_START_TIME = datetime.utcnow()


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    MOCK_MODE = True  # Use mock data when backend unavailable


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    MOCK_MODE = False


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    MOCK_MODE = True


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
