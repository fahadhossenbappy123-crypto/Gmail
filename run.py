"""
Render-compatible Flask app entry point
"""
import os
import sys

# Set Flask environment
os.environ.setdefault('FLASK_ENV', os.getenv('FLASK_ENV', 'development'))

try:
    from app import app, db
    from config import DevelopmentConfig, ProductionConfig
    
    # Use environment variable to determine config
    env = os.getenv('FLASK_ENV', 'development')
    config = ProductionConfig if env == 'production' else DevelopmentConfig
    
    app.config.from_object(config)
    
    # Create database tables if they don't exist (gracefully)
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created/verified")
        except Exception as e:
            print(f"⚠ Warning: Could not initialize database tables: {type(e).__name__}")
            print(f"  {str(e)[:100]}...")
            print("  App will continue but database operations may fail")
    
except ImportError as e:
    print(f"✗ Error importing app: {e}")
    print("  Please check if all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"✗ Startup error: {type(e).__name__}: {e}")
    sys.exit(1)

# Get port from environment variable (Render provides this)
port = int(os.getenv('PORT', 5000))

if __name__ == '__main__':
    try:
        print(f"Starting Flask app on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"✗ Error running app: {e}")
        sys.exit(1)
