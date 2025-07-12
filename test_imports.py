try:
    from database.models import DatabaseType
    print("✅ DatabaseType imported successfully")
    
    from database.connections import DatabaseManager
    print("✅ DatabaseManager imported successfully")
    
    from database import DatabaseType, DatabaseManager
    print("✅ Both imported from database package")
    
except ImportError as e:
    print(f"❌ Import error: {e}")