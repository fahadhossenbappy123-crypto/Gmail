"""
Database Initialization Script
Run this once to create all tables
"""
import os
from dotenv import load_dotenv
from app import app
from database import db

load_dotenv()

def init_db():
    """Initialize database with tables"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✓ Database initialized successfully!")
        print("\nTables created:")
        print("  - users")
        print("  - gmail_accounts")
        print("  - earnings")
        print("  - withdrawals")

if __name__ == '__main__':
    init_db()
