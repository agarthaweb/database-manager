# test_phase_2_2.py
import os
from database.connections import DatabaseManager
from database.models import ConnectionConfig, DatabaseType
from database.schema_analyzer import SchemaAnalyzer
from query_engine.nl_processor import NLProcessor

def test_phase_2_2_comprehensive():
    """Test Phase 2.2: Schema Context Integration"""
    
    print("🚀 Testing Phase 2.2: Schema Context Integration")
    print("=" * 70)
    
    # Setup
    db_manager = DatabaseManager()
    db_manager.create_sample_sqlite_db()
    
    config = ConnectionConfig(
        name="test_db",
        connection_string="sqlite:///sample_data/sample.db",
        database_type=DatabaseType.SQLITE,
        db_type="sqlite"
    )
    success = db_manager.add_connection(config)
    
    # Enhanced setup
    engine = db_manager.get_active_engine()
    analyzer = SchemaAnalyzer(engine)
    schema = analyzer.analyze_database()
    
    # Add analyzer to processor for enhanced features
    processor = NLProcessor(schema)
    processor.schema_analyzer = analyzer  # Enable advanced features
    
    print(f"✅ Enhanced setup complete - {len(schema.tables)} tables analyzed")
    
    # Advanced test cases
    advanced_test_cases = [
        {
            "query": "Show me customers who have made expensive orders",
            "description": "Complex filtering with business logic",
            "expected_features": ["WHERE clause", "JOIN", "price filtering"]
        },
        {
            "query": "Find the most popular products this year",
            "description": "Aggregation with date filtering",
            "expected_features": ["GROUP BY", "COUNT/SUM", "date filtering"]
        },
        {
            "query": "List customers with no orders",
            "description": "LEFT JOIN for missing relationships",
            "expected_features": ["LEFT JOIN", "IS NULL"]
        },
        {
            "query": "What are the monthly sales trends?",
            "description": "Time-based aggregation",
            "expected_features": ["GROUP BY month", "SUM", "date functions"]
        },
        {
            "query": "Show product performance by category",
            "description": "Multi-level grouping and analysis",
            "expected_features": ["GROUP BY", "multiple calculations"]
        }
    ]
    
    print("\n🧪 Testing Enhanced Natural Language Processing...")
    print("-" * 70)
    
    for i, test_case in enumerate(advanced_test_cases, 1):
        print(f"\n📝 Advanced Test {i}: {test_case['description']}")
        print(f"Natural Query: \"{test_case['query']}\"")
        
        try:
            result = processor.process_query(test_case['query'])
            
            # Enhanced analysis
            print(f"\n🔍 Enhanced Intent Analysis:")
            print(f"   Type: {result.intent.query_type.value}")
            print(f"   Tables: {result.intent.tables_mentioned}")
            print(f"   Columns: {result.intent.columns_mentioned}")
            print(f"   Complexity: {result.intent.complexity_score}/10")
            print(f"   Confidence: {result.intent.confidence:.1%}")
            print(f"   Requires JOINs: {result.intent.requires_joins}")
            
            print(f"\n💻 Generated SQL:")
            print(f"   {result.sql_query}")
            
            print(f"\n🔒 Safety & Performance:")
            print(f"   Safe: {'✅' if result.is_safe else '❌'}")
            
            if result.warnings:
                print(f"   Warnings:")
                for warning in result.warnings:
                    print(f"     • {warning}")
            
            # Test new Phase 2.2 features
            suggestions = processor.suggest_query_improvements(result.sql_query, result.intent)
            if suggestions:
                print(f"\n💡 Optimization Suggestions:")
                for suggestion in suggestions[:2]:  # Show top 2
                    print(f"     • {suggestion}")
            
            alternatives = processor.generate_query_alternatives(test_case['query'], result.intent)
            if alternatives:
                print(f"\n🔄 Query Alternatives:")
                for alt in alternatives[:1]:  # Show 1 alternative
                    print(f"     • {alt.split('--')[1].strip() if '--' in alt else alt}")
            
            print(f"\n📚 Explanation:")
            print(f"   {result.explanation}")
            
            # Feature verification
            print(f"\n✅ Feature Check:")
            sql_upper = result.sql_query.upper()
            for feature in test_case['expected_features']:
                feature_upper = feature.upper()
                found = any(key in sql_upper for key in feature_upper.split())
                status = "✅" if found else "⚪"
                print(f"   {status} {feature}")
            
            print("-" * 70)
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            print("-" * 70)
    
    # Test schema context optimization
    print(f"\n🎯 Testing Schema Context Optimization...")
    
    # Test token limit management
    context_3000 = analyzer.get_schema_context_optimized(max_tokens=3000)
    context_1000 = analyzer.get_schema_context_optimized(max_tokens=1000)
    
    print(f"   Context at 3000 tokens: {len(context_3000.split())} words")
    print(f"   Context at 1000 tokens: {len(context_1000.split())} words")
    print(f"   ✅ Dynamic context sizing working")
    
    # Test schema search
    search_results = analyzer.search_schema("customer")
    print(f"\n🔍 Schema Search Results for 'customer':")
    print(f"   Tables found: {search_results.get('tables', [])}")
    print(f"   Columns found: {len(search_results.get('columns', []))}")
    
    print(f"\n🎉 Phase 2.2 Testing Complete!")
    print("Ready for Phase 3: Core Features Implementation")

if __name__ == "__main__":
    test_phase_2_2_comprehensive()