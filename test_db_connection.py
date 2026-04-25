"""
Test database connection and table creation
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    print("=" * 60)
    print("Testing PostgreSQL Database Connection")
    print("=" * 60)
    
    # Check environment variables
    print("\n✓ Environment Variables:")
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        # Hide password in output
        masked_url = db_url.replace(os.getenv('DB_PASSWORD', ''), '***')
        print(f"  DATABASE_URL: {masked_url}")
    else:
        print(f"  DATABASE_URL: Not set")
        
    print(f"  DB_HOST: {os.getenv('DB_HOST')}")
    print(f"  DB_PORT: {os.getenv('DB_PORT')}")
    print(f"  DB_NAME: {os.getenv('DB_NAME')}")
    print(f"  FLASK_ENV: {os.getenv('FLASK_ENV', 'development')}")
    
    # Test Flask app initialization
    print("\n✓ Initializing Flask App:")
    try:
        from app import app, db
        print("  ✓ Flask app imported successfully")
    except Exception as e:
        print(f"  ✗ Error importing app: {e}")
        return False
    
    # Test database connection
    print("\n✓ Testing Database Connection:")
    try:
        with app.app_context():
            # Test connection
            connection = db.engine.connect()
            print("  ✓ Successfully connected to PostgreSQL")
            connection.close()
            
            # Create tables
            print("\n✓ Creating Database Tables:")
            db.create_all()
            print("  ✓ Tables created successfully")
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"\n✓ Database Tables ({len(tables)} tables):")
            for table in tables:
                print(f"    - {table}")
            
            print("\n" + "=" * 60)
            print("✓ Database connection test PASSED")
            print("=" * 60)
            return True
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        print("✗ Database connection test FAILED")
        print("=" * 60)
        return False

if __name__ == '__main__':
    success = test_connection()
    exit(0 if success else 1)
