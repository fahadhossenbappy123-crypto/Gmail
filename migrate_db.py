#!/usr/bin/env python
"""
Database Migration and Setup Script
Run this to initialize or migrate database for Render deployment
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Initialize database"""
    logger.info("=" * 50)
    logger.info("Gmail Earn - Database Migration Script")
    logger.info("=" * 50)
    
    # Import app after loading environment
    try:
        from app import app, db
        logger.info("✓ Flask app imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import app: {e}")
        sys.exit(1)
    
    # Get database configuration
    with app.app_context():
        db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')
        env = os.getenv('FLASK_ENV', 'development')
        
        # Mask password in logs for security
        display_uri = db_uri
        if '@' in display_uri:
            parts = display_uri.split('@')
            display_uri = parts[0][:30] + '***@' + parts[1]
        
        logger.info(f"\nEnvironment: {env}")
        logger.info(f"Database URI: {display_uri}")
        
        # Test connection
        try:
            from sqlalchemy import text
            logger.info("\nTesting database connection...")
            
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                conn.commit()
            
            logger.info("✓ Database connection successful!")
            
        except Exception as e:
            logger.error(f"✗ Database connection failed: {e}")
            logger.error(f"  Please check your DATABASE_URL environment variable")
            sys.exit(1)
        
        # Create tables
        try:
            logger.info("\nCreating database tables...")
            db.create_all()
            logger.info("✓ Database tables created successfully!")
            
            logger.info("\nTables created:")
            logger.info("  - users")
            logger.info("  - gmail_accounts")
            logger.info("  - earnings")
            logger.info("  - withdrawals")
            
        except Exception as e:
            logger.error(f"✗ Failed to create tables: {e}")
            sys.exit(1)
        
        logger.info("\n" + "=" * 50)
        logger.info("✓ Database migration completed successfully!")
        logger.info("=" * 50)

if __name__ == '__main__':
    main()
