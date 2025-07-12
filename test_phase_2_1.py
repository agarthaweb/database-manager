# test_phase_2_1.py
import os
from database.connections import DatabaseManager
from database.models import ConnectionConfig, DatabaseType
from database.schema_analyzer import SchemaAnalyzer
from query_engine.nl_processor import NLProcessor

def test_nl_processor_comprehensive():
    """Comprehensive test of our Phase 2.1 NLP engine"""
    
    print("🚀 Testing Phase 2.1: Query Intent Classification")
    print("=" * 60)
    
    # Setup - like initializing your app stack
    db_manager = DatabaseManager()
    
    # Create sample database - like seeding test data
    print("\n📊 Setting up test database...")
    db_manager.create_sample_sqlite_db()
    
    # Add connection - like configuring database connection - Fix the parameters
    config = ConnectionConfig(
        name="test_db",
        connection_string="sqlite:///sample_data/sample.db",
        database_type=DatabaseType.SQLITE,  # Use DatabaseType enum
        db_type="sqlite"  # Keep this as string
    )
    success = db_manager.add_connection(config)
    print(f"✅ Database connection: {'Success' if success else 'Failed'}")
    
    # Analyze schema - like discovering API endpoints
    engine = db_manager.get_active_engine()
    analyzer = SchemaAnalyzer(engine)
    schema = analyzer.analyze_database()
    print(f"✅ Schema analyzed: {len(schema.tables)} tables found")
    
    # Create NL processor - like initializing your smart API handler
    processor = NLProcessor(schema)
    print("✅ NLP processor initialized")
    
    # Test different query types - like testing various API endpoints
    test_cases = [
        {
            "query": "Show me all customers",
            "expected_type": "SELECT",
            "description": "Simple table retrieval"
        },
        {
            "query": "Find customers with their orders",
            "expected_type": "SELECT", 
            "description": "Join query across related tables"
        },
        {
            "query": "What are the top 5 products by price?",
            "expected_type": "SELECT",
            "description": "Aggregation with ordering and limits"
        },
        {
            "query": "How many orders were placed last month?",
            "expected_type": "SELECT",
            "description": "Count aggregation with date filtering"
        },
        {
            "query": "List all products that have been ordered",
            "expected_type": "SELECT",
            "description": "Distinct values across joined tables"
        }
    ]
    
    print("\n🧪 Testing Natural Language Processing...")
    print("-" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['description']}")
        print(f"Natural Query: \"{test_case['query']}\"")
        
        try:
            # Process query - like making API request
            result = processor.process_query(test_case['query'])
            
            # Display results
            print(f"🔍 Intent Analysis:")
            print(f"   Type: {result.intent.query_type.value}")
            print(f"   Tables: {result.intent.tables_mentioned}")
            print(f"   Complexity: {result.intent.complexity_score}/10")
            print(f"   Requires JOINs: {result.intent.requires_joins}")
            
            print(f"\n💻 Generated SQL:")
            print(f"   {result.sql_query}")
            
            print(f"\n🔒 Safety Check: {'✅ Safe' if result.is_safe else '❌ Unsafe'}")
            
            if result.warnings:
                print(f"⚠️  Warnings: {', '.join(result.warnings)}")
            
            print(f"\n📚 Explanation:")
            print(f"   {result.explanation}")
            
            # Success indicator
            status = "✅ PASS" if result.is_safe and result.sql_query else "❌ FAIL"
            print(f"\n{status}")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
        
        print("-" * 60)
    
    print("\n🎯 Phase 2.1 Testing Complete!")
    print("Ready to proceed to Phase 2.2: Schema Context Integration")

if __name__ == "__main__":
    test_nl_processor_comprehensive()