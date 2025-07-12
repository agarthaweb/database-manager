#!/usr/bin/env python3
"""
SQL Query Builder - Command Line Interface
"""

import os
from database import DatabaseManager, ConnectionConfig, DatabaseType, SchemaAnalyzer
from config import OPENAI_API_KEY

def main():
    print("🔍 SQL Query Builder - Command Line Interface")
    print("=" * 50)
    
    # Check API key
    if not OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        print("Please add your API key to the .env file")
        return
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    # Create sample database for testing
    print("📊 Creating sample database...")
    if db_manager.create_sample_sqlite_db():
        print("✅ Sample database created successfully")
        
        # Add sample connection
        config = ConnectionConfig(
            name="sample_db",
            database_type=DatabaseType.SQLITE,
            connection_string="sqlite:///sample_data/sample.db",
            description="Sample SQLite database for testing"
        )
        
        if db_manager.add_connection(config):
            print("✅ Sample database connection added")
            
            # Analyze schema
            engine = db_manager.get_active_engine()
            analyzer = SchemaAnalyzer(engine)
            schema = analyzer.analyze_database()
            
            print(f"\n📋 Database Schema Analysis:")
            print(f"Database: {schema.database_name}")
            print(f"Type: {schema.database_type.value}")
            print(f"Tables: {len(schema.tables)}")
            
            for table in schema.tables:
                print(f"\n  📄 Table: {table.name}")
                print(f"     Columns: {len(table.columns)}")
                print(f"     Rows: {table.row_count}")
                
                for col in table.columns[:3]:  # Show first 3 columns
                    flags = []
                    if col.is_primary_key:
                        flags.append("PK")
                    if col.is_foreign_key:
                        flags.append("FK")
                    if not col.is_nullable:
                        flags.append("NOT NULL")
                    
                    flag_str = f" ({', '.join(flags)})" if flags else ""
                    print(f"       - {col.name}: {col.data_type}{flag_str}")
        
        else:
            print("❌ Failed to add sample database connection")
    else:
        print("❌ Failed to create sample database")
    
    print(f"\n🚀 Ready to start!")
    print("Run 'streamlit run app.py' to launch the web interface")

if __name__ == "__main__":
    main()