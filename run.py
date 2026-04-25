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

# Initialize database (lazy - only when first request comes in)
@app.before_request
def init_db_on_request():
    """Initialize database on first request if not already done"""
    if not hasattr(app, '_db_initialized'):
        with app.app_context():
            try:
                # Test connection and create tables
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    conn.commit()
                
                db.create_all()
                app._db_initialized = True
                logger.info("✓ Database tables created/verified")
                logger.info(f"  Database connected successfully")
            except Exception as e:
                logger.warning(f"Could not initialize database: {type(e).__name__}")
                logger.warning(f"  Error: {str(e)[:200]}...")
                logger.warning(f"  Retrying on next request...")
                # Don't mark as initialized to retry on next request

# Get port from environment variable (Render provides this)
port = int(os.getenv('PORT', 5000))

# This is the WSGI application object used by Gunicorn
application = app

if __name__ == '__main__':
    # Local development server
    logger.info(f"Starting Flask development server on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=False)
