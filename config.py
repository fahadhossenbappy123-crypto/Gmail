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
        # Convert postgres:// to postgresql+psycopg2:// for SQLAlchemy
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
        elif database_url.startswith('postgresql://') and 'postgresql+psycopg2' not in database_url:
            database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        return database_url
    
    # For production without DATABASE_URL, try to build from components
    if ENVIRONMENT == 'production':
        # If running on Render without DATABASE_URL, use SQLite as fallback
        print("⚠️  WARNING: DATABASE_URL not set. Using SQLite fallback.")
        print("    On Render: Add PostgreSQL database and set DATABASE_URL environment variable")
        return 'sqlite:///gmail_app.db'
    
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
        'pool_size': 2,         # Minimal pool for free tier Render
        'max_overflow': 5,      # Minimal overflow for free tier
        'echo_pool': False,
        'connect_args': {
            'connect_timeout': 5,
            'application_name': 'gmail_create_app'
        },
        'pool_reset_on_return': 'rollback'  # Rollback on error
    }
    
    # Session Configuration for Browser Persistence
    PERMANENT_SESSION_LIFETIME = 30 * 24 * 60 * 60  # 30 days
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection

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
