"""
Render-compatible Flask app entry point
"""
import os
from app import app
from config import DevelopmentConfig, ProductionConfig

# Use environment variable to determine config
env = os.getenv('FLASK_ENV', 'development')
config = ProductionConfig if env == 'production' else DevelopmentConfig

app.config.from_object(config)

# Get port from environment variable (Render provides this)
port = int(os.getenv('PORT', 5000))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=False)
