"""
Database Reset Script
Use this to reset the database for testing purposes
"""
import os
import sys

# Set Flask environment
os.environ.setdefault('FLASK_ENV', 'development')

from app import app, db

def reset_database():
    """Reset database - DROP all tables and recreate them"""
    with app.app_context():
        print("⚠️  WARNING: This will DELETE ALL DATA from the database!")
        print("Users, emails, balances, everything will be removed.")
        
        confirm = input("\nAre you sure? Type 'yes' to continue: ").strip().lower()
        
        if confirm != 'yes':
            print("❌ Database reset cancelled.")
            return
        
        try:
            print("\n🔄 Dropping all tables...")
            db.drop_all()
            print("✅ All tables dropped successfully")
            
            print("🔄 Creating new tables...")
            db.create_all()
            print("✅ Database tables recreated successfully")
            
            print("\n✨ Database reset complete!")
            print("📌 Next step: Visit your app and register test users")
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            sys.exit(1)

if __name__ == '__main__':
    reset_database()
