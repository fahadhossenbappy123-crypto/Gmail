"""
Application Configuration
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Determine which database to use
USE_POSTGRESQL = bool(os.getenv('DATABASE_URL'))
ENVIRONMENT = os.getenv('FLASK_ENV', 'development')

def get_database_uri():
    """Construct database URI from environment variables"""
    # If DATABASE_URL is explicitly set, use it (PostgreSQL)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return database_url
    
    # For production without DATABASE_URL, try to build from components
    if ENVIRONMENT == 'production':
        db_user = os.getenv('DB_USER', 'gmaildb_user')
        db_password = os.getenv('DB_PASSWORD', 'password')
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'gmaildb')
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}?sslmode=require"
    
    # For development, use SQLite
    return 'sqlite:///gmail_app.db'

class Config:
    """Base configuration"""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-this')
    DEBUG = False
    TESTING = False
    
    # Database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    
    # Connection pool settings (used for PostgreSQL)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,  # Verify connection before using
        'pool_recycle': 3600,   # Recycle connections every hour
        'pool_size': 10,
        'max_overflow': 20,
        'connect_args': {
            'connect_timeout': 5,
            'application_name': 'gmail_create_app'
        }
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
