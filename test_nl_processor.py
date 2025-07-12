from database.connections import DatabaseManager
from database.models import ConnectionConfig, DatabaseType
from database.schema_analyzer import SchemaAnalyzer
from query_engine.nl_processor import NLProcessor

def test_nl_processor_enhanced():
    """Enhanced test with Phase 2.2 features"""
    
    # Setup
    db_manager = DatabaseManager()
    db_manager.create_sample_sqlite_db()
    
    config = ConnectionConfig(
        name="test_db",
        connection_string="sqlite:///sample_data/sample.db",
        database_type=DatabaseType.SQLITE,
        db_type="sqlite"
    )
    db_manager.add_connection(config)
    
    # Enhanced setup with schema analyzer
    engine = db_manager.get_active_engine()
    analyzer = SchemaAnalyzer(engine)
    schema = analyzer.analyze_database()
    
    # Create enhanced NL processor
    processor = NLProcessor(schema, schema_analyzer=analyzer)
    
    # Test queries with enhanced analysis
    test_queries = [
        "Show me all customers",
        "Find customers with their orders", 
        "What are the top 5 products by sales?",
        "Show customers who haven't placed any orders"  # New complex query
    ]
    
    for query in test_queries:
        print(f"\nNatural Query: {query}")
        result = processor.process_query(query)
        print(f"Generated SQL: {result.sql_query}")
        print(f"Confidence: {result.intent.confidence:.1%}")
        print(f"Complexity: {result.intent.complexity_score}/10")
        print(f"Safe: {result.is_safe}")
        print(f"Tables: {result.intent.tables_mentioned}")
        if result.warnings:
            print(f"Warnings: {result.warnings}")

if __name__ == "__main__":
    test_nl_processor_enhanced()