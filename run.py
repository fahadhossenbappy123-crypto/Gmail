"""
Render-compatible Flask app entry point
"""
import os
from app import app, db
from config import DevelopmentConfig, ProductionConfig

# Use environment variable to determine config
env = os.getenv('FLASK_ENV', 'development')
config = ProductionConfig if env == 'production' else DevelopmentConfig

app.config.from_object(config)

# Create database tables if they don't exist
with app.app_context():
    db.create_all()
    print("✓ Database tables created/verified")

# Get port from environment variable (Render provides this)
port = int(os.getenv('PORT', 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=False)
