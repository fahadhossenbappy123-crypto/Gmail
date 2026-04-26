"""
WSGI entry point for Gunicorn and Flask development
Compatible with both: python run.py and gunicorn run:app
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set Flask environment
os.environ.setdefault('FLASK_ENV', os.getenv('FLASK_ENV', 'development'))

# Import app and initialize
logger.info("Importing Flask app...")
try:
    from app import app, db
    from config import DevelopmentConfig, ProductionConfig
except ImportError as e:
    logger.error(f"Failed to import app: {e}")
    sys.exit(1)

# Configure app
env = os.getenv('FLASK_ENV', 'development')
config = ProductionConfig if env == 'production' else DevelopmentConfig
app.config.from_object(config)

logger.info(f"App configured for {env} environment")

# Initialize database with error handling
try:
    with app.app_context():
        logger.info("Initializing database...")
        db.create_all()
        logger.info("✅ Database initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ Could not initialize database: {e}")
    logger.info("Continuing without database initialization (will retry on first request)")

if __name__ == '__main__':
    logger.info("Starting Flask development server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
logger.info(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not set')[:50]}...")

# Database is automatically initialized in app.py before_first_request

# Get port from environment variable (Render provides this)
port = int(os.getenv('PORT', 5000))

# This is the WSGI application object used by Gunicorn
application = app

if __name__ == '__main__':
    # Local development server
    logger.info(f"Starting Flask development server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
