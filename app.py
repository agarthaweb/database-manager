import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import re
from datetime import datetime, timedelta

from database.connections import DatabaseManager
from database.models import ConnectionConfig, DatabaseType
from database.schema_analyzer import SchemaAnalyzer
from query_engine.nl_processor import NLProcessor
from ui.components import UIComponents
from utils.helpers import format_sql, safe_execute
from config import *
# app.py - Add this at the top after imports
import os

# Production environment detection
IS_PRODUCTION = os.getenv("STREAMLIT_SHARING") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER")

# Update your Google API key loading
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY and not IS_PRODUCTION:
    st.error("🔑 Google API key not configured. Please check your .env file.")
    st.stop()
elif not GOOGLE_API_KEY and IS_PRODUCTION:
    st.error("🔑 Google API key not configured in production environment.")
    st.stop()

def main():
    """Main application entry point"""
    
    # Enhanced page configuration
    st.set_page_config(
        page_title="SQL Query Builder Pro",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for professional styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .query-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .success-box {
        background: #d1f2eb;
        border: 1px solid #00b894;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Check API configuration
    if not GOOGLE_API_KEY:
        st.error("🔑 Google API key not configured. Please check your .env file.")
        st.stop()
    
    # Initialize session state
    if 'db_manager' not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    if 'favorites' not in st.session_state:
        st.session_state.favorites = []
    
    # Header with navigation
    UIComponents.render_header()
    
    # Sidebar for database connections and navigation
    with st.sidebar:
        UIComponents.render_sidebar_navigation()
        UIComponents.render_connection_manager()
    
    # Main content area with tabs
    if st.session_state.db_manager.get_active_engine():
        render_main_application()
    else:
        render_welcome_screen()

def render_main_application():
    """Render the main application interface"""
    
    # Initialize schema analyzer
    engine = st.session_state.db_manager.get_active_engine()
    
    if 'schema_analyzer' not in st.session_state:
        st.session_state.schema_analyzer = SchemaAnalyzer(engine)
        st.session_state.schema = st.session_state.schema_analyzer.analyze_database()
    
    # Create main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Query Builder", 
        "📊 Schema Explorer", 
        "📈 Results & Visualization", 
        "📚 Query Library", 
        "⚙️ Settings"
    ])
    
    with tab1:
        render_query_builder()
    
    with tab2:
        UIComponents.render_schema_explorer()
    
    with tab3:
        UIComponents.render_query_results_visualization()
    
    with tab4:
        render_query_library()
    
    with tab5:
        render_settings()

def render_query_builder():
    """Enhanced query builder interface with preview functionality"""
    
    st.markdown('<div class="main-header"><h2>🔍 Intelligent Query Builder</h2></div>', 
                unsafe_allow_html=True)
    
    # Create two columns for input and preview
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Natural Language Input")
        
        # Enhanced query input with suggestions
        query_placeholder = st.selectbox(
            "Try one of these examples or write your own:",
            [
                "Type your own question...",
                "Show me all customers",
                "Find customers with their recent orders", 
                "What are the top 10 products by sales?",
                "List customers who haven't ordered in 30 days",
                "Show monthly sales trends for this year",
                "Find products that are running low on stock"
            ]
        )
        
        if query_placeholder == "Type your own question...":
            query_placeholder = ""
        
        natural_query = st.text_area(
            "Ask a question about your data:",
            value=query_placeholder,
            height=120,
            placeholder="e.g., 'Show me customers who have spent more than $1000 this year'"
        )
        
        # Query analysis and generation
        if natural_query and natural_query != "Type your own question...":
            with st.spinner("🧠 Analyzing your question..."):
                # Initialize NL processor
                processor = NLProcessor(st.session_state.schema, st.session_state.schema_analyzer)
                result = processor.process_query(natural_query)
                
                # Store result in session state
                st.session_state.current_result = result
    
    with col2:
        st.subheader("Query Intelligence")
        
        if 'current_result' in st.session_state:
            result = st.session_state.current_result
            
            # Display metrics
            col_metric1, col_metric2 = st.columns(2)
            
            with col_metric1:
                confidence_color = "green" if result.intent.confidence > 0.8 else "orange" if result.intent.confidence > 0.6 else "red"
                st.metric(
                    "Confidence", 
                    f"{result.intent.confidence:.0%}",
                    delta=None
                )
            
            with col_metric2:
                complexity_color = "green" if result.intent.complexity_score < 5 else "orange" if result.intent.complexity_score < 8 else "red"
                st.metric(
                    "Complexity", 
                    f"{result.intent.complexity_score}/10",
                    delta=None
                )
            
            # Query details
            st.markdown("**📋 Analysis:**")
            st.write(f"• **Type:** {result.intent.query_type.value.title()}")
            st.write(f"• **Tables:** {', '.join(result.intent.tables_mentioned) if result.intent.tables_mentioned else 'Auto-detected'}")
            st.write(f"• **Requires JOINs:** {'Yes' if result.intent.requires_joins else 'No'}")
            
            # Safety status
            if result.is_safe:
                st.success("✅ Query is safe to execute")
            else:
                st.error("❌ Query contains unsafe operations")
    
    # Generated SQL display and PREVIEW
    if 'current_result' in st.session_state:
        result = st.session_state.current_result
        
        st.markdown("---")
        
        # Create three columns: SQL, Preview, Actions
        col_sql, col_preview, col_actions = st.columns([2, 2, 1])
        
        with col_sql:
            st.subheader("Generated SQL Query")
            
            # Format and display SQL
            formatted_sql = format_sql(result.sql_query)
            st.code(formatted_sql, language="sql")
            
            # Show explanation in expander
            with st.expander("🤖 Query Explanation"):
                st.write(result.explanation)
        
        with col_preview:
            st.subheader("🔍 Query Preview")
            
            # Auto-generate preview
            if result.is_safe:
                generate_query_preview(result.sql_query, natural_query)
            else:
                st.error("❌ Cannot preview unsafe query")
        
        with col_actions:
            st.subheader("Actions")
            
            # Execute full query button
            if st.button("▶️ Execute Full Query", type="primary", use_container_width=True):
                if result.is_safe:
                    execute_query(result.sql_query, natural_query)
                else:
                    st.error("Cannot execute unsafe query")
            
            # Refresh preview button
            if st.button("🔄 Refresh Preview", use_container_width=True):
                if result.is_safe:
                    generate_query_preview(result.sql_query, natural_query, force_refresh=True)
            
            # Save to favorites
            if st.button("⭐ Save to Favorites", use_container_width=True):
                save_to_favorites(natural_query, result.sql_query)
            
            # Copy to clipboard
            if st.button("📋 Copy SQL", use_container_width=True):
                st.write("SQL copied to clipboard!")
            
            # Download query
            st.download_button(
                "💾 Download SQL",
                data=result.sql_query,
                file_name=f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                mime="text/plain",
                use_container_width=True
            )
        
        # Warnings and suggestions (full width)
        if result.warnings:
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.warning("⚠️ **Performance Warnings:**")
            for warning in result.warnings:
                st.write(f"• {warning}")
            st.markdown('</div>', unsafe_allow_html=True)

def execute_query(sql_query: str, natural_query: str):
    """Execute SQL query and display results"""
    
    try:
        with st.spinner("🔍 Executing query..."):
            # Execute query using database manager
            df = st.session_state.db_manager.execute_query(sql_query)
            
            # Store results in session state
            st.session_state.query_results = {
                'data': df,
                'sql': sql_query,
                'natural_query': natural_query,
                'timestamp': datetime.now(),
                'row_count': len(df)
            }
            
            # Add to query history
            st.session_state.query_history.append({
                'natural_query': natural_query,
                'sql_query': sql_query,
                'timestamp': datetime.now(),
                'row_count': len(df),
                'success': True
            })
            
            st.success(f"✅ Query executed successfully! Retrieved {len(df)} rows.")
            
            # Auto-switch to results tab (would require JavaScript in real implementation)
            st.info("💡 Check the 'Results & Visualization' tab to see your data!")
            
    except Exception as e:
        st.error(f"❌ Query execution failed: {str(e)}")
        
        # Add failed query to history
        st.session_state.query_history.append({
            'natural_query': natural_query,
            'sql_query': sql_query,
            'timestamp': datetime.now(),
            'error': str(e),
            'success': False
        })

def save_to_favorites(natural_query: str, sql_query: str):
    """Save query to favorites"""
    
    favorite = {
        'id': len(st.session_state.favorites) + 1,
        'natural_query': natural_query,
        'sql_query': sql_query,
        'timestamp': datetime.now(),
        'tags': []
    }
    
    st.session_state.favorites.append(favorite)
    st.success("⭐ Query saved to favorites!")

def render_welcome_screen():
    """Welcome screen when no database is connected"""
    
    st.markdown('<div class="main-header"><h1>🔍 SQL Query Builder Pro</h1><p>Transform natural language into powerful SQL queries</p></div>', 
                unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### 🚀 Get Started
        
        1. **Connect to a database** using the sidebar
        2. **Ask questions** in plain English
        3. **Get optimized SQL** with explanations
        4. **Execute and visualize** your results
        
        ### ✨ Features
        
        - 🧠 **AI-Powered**: Advanced natural language understanding
        - 🔒 **Safe & Secure**: Read-only queries with safety validation
        - ⚡ **Performance Optimized**: Smart query suggestions and warnings
        - 📊 **Visual Results**: Automatic chart generation
        - 📚 **Query Management**: History, favorites, and sharing
        """)
        
        if st.button("🎯 Try Sample Database", type="primary", use_container_width=True):
            # Create and connect to sample database
            st.session_state.db_manager.create_sample_sqlite_db()
            
            config = ConnectionConfig(
                name="Sample E-commerce DB",
                connection_string="sqlite:///sample_data/sample.db",
                database_type=DatabaseType.SQLITE,
                db_type="sqlite"
            )
            
            success = st.session_state.db_manager.add_connection(config)
            
            if success:
                st.success("✅ Sample database connected! Refresh the page to start querying.")
                st.rerun()

def render_query_library():
    """Render query history and favorites"""
    
    st.markdown('<div class="main-header"><h2>📚 Query Library</h2></div>', 
                unsafe_allow_html=True)
    
    # Create tabs for different views
    history_tab, favorites_tab = st.tabs(["📜 History", "⭐ Favorites"])
    
    with history_tab:
        if 'query_history' in st.session_state and st.session_state.query_history:
            st.subheader(f"Query History ({len(st.session_state.query_history)} queries)")
            
            for i, query in enumerate(reversed(st.session_state.query_history[-20:])):  # Show last 20
                with st.expander(f"Query {len(st.session_state.query_history) - i}: {query.get('natural_query', 'Unknown')[:50]}..."):
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Question:** {query.get('natural_query', 'N/A')}")
                        st.code(query.get('sql_query', 'N/A'), language='sql')
                        st.write(f"**Time:** {query.get('timestamp', 'Unknown')}")
                        
                        if query.get('success', False):
                            st.success(f"✅ Success - {query.get('row_count', 0)} rows")
                        else:
                            st.error(f"❌ Error: {query.get('error', 'Unknown error')}")
                    
                    with col2:
                        if st.button(f"🔄 Rerun", key=f"rerun_{i}"):
                            # Re-execute this query
                            if 'current_result' in st.session_state:
                                execute_query(query.get('sql_query'), query.get('natural_query'))
                        
                        if st.button(f"⭐ Favorite", key=f"fav_{i}"):
                            save_to_favorites(query.get('natural_query'), query.get('sql_query'))
        else:
            st.info("No query history yet. Run some queries to see them here!")
    
    with favorites_tab:
        if 'favorites' in st.session_state and st.session_state.favorites:
            st.subheader(f"Favorite Queries ({len(st.session_state.favorites)} saved)")
            
            for i, fav in enumerate(st.session_state.favorites):
                with st.expander(f"⭐ {fav.get('natural_query', 'Untitled')[:50]}..."):
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Question:** {fav.get('natural_query', 'N/A')}")
                        st.code(fav.get('sql_query', 'N/A'), language='sql')
                        st.write(f"**Saved:** {fav.get('timestamp', 'Unknown')}")
                    
                    with col2:
                        if st.button(f"▶️ Run", key=f"run_fav_{i}"):
                            # Execute this favorite
                            execute_query(fav.get('sql_query'), fav.get('natural_query'))
                        
                        if st.button(f"🗑️ Delete", key=f"del_fav_{i}"):
                            st.session_state.favorites.pop(i)
                            st.rerun()
        else:
            st.info("No favorite queries yet. Save some queries to see them here!")

def render_settings():
    """Render application settings"""
    
    st.markdown('<div class="main-header"><h2>⚙️ Settings</h2></div>', 
                unsafe_allow_html=True)
    
    # Database settings
    st.subheader("🔌 Database Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Current Connection:**")
        active_conn = st.session_state.db_manager.active_connection
        if active_conn:
            st.success(f"✅ Connected to: {active_conn}")
        else:
            st.warning("⚠️ No active connection")
    
    with col2:
        st.write("**Query Limits:**")
        st.info(f"Max rows: {MAX_RESULT_ROWS:,}")
        st.info(f"Timeout: {MAX_QUERY_EXECUTION_TIME}s")
    
    # AI Settings
    st.subheader("🤖 AI Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Model:** Google Gemini 1.5 Flash")
        st.write("**Provider:** Google AI")
        api_status = "✅ Connected" if GOOGLE_API_KEY else "❌ Not configured"
        st.write(f"**API Status:** {api_status}")
    
    with col2:
        st.write("**Performance Settings:**")
        st.write(f"Temperature: {LLM_TEMPERATURE}")
        st.write(f"Max tokens: {MAX_SCHEMA_TOKENS}")
    
    # Application Info
    st.subheader("ℹ️ Application Info")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Session Statistics:**")
        query_count = len(st.session_state.query_history) if 'query_history' in st.session_state else 0
        fav_count = len(st.session_state.favorites) if 'favorites' in st.session_state else 0
        st.write(f"Queries executed: {query_count}")
        st.write(f"Favorites saved: {fav_count}")
    
    with col2:
        st.write("**Actions:**")
        if st.button("🗑️ Clear All History"):
            st.session_state.query_history = []
            st.success("History cleared!")
        
        if st.button("🔄 Reset Session"):
            for key in list(st.session_state.keys()):
                if key != 'db_manager':  # Keep database connections
                    del st.session_state[key]
            st.success("Session reset!")
            st.rerun()
# app.py - Add this new function for query preview

def generate_query_preview(sql_query: str, natural_query: str, force_refresh: bool = False):
    """Generate and display a preview of the query results"""
    
    # Cache key for preview results
    preview_key = f"preview_{hash(sql_query)}"
    
    # Check if we have cached preview (unless force refresh)
    if not force_refresh and preview_key in st.session_state:
        preview_data = st.session_state[preview_key]
        display_preview_results(preview_data, from_cache=True)
        return
    
    try:
        with st.spinner("🔍 Generating preview..."):
            # Create preview query with LIMIT
            preview_sql = create_preview_query(sql_query)
            
            # Execute preview query
            start_time = datetime.now()
            preview_df = st.session_state.db_manager.execute_query(preview_sql)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Estimate total rows for full query
            estimated_total = estimate_total_rows(sql_query, preview_df)
            
            # Store preview data
            preview_data = {
                'data': preview_df,
                'sql': preview_sql,
                'original_sql': sql_query,
                'natural_query': natural_query,
                'execution_time': execution_time,
                'estimated_total': estimated_total,
                'timestamp': datetime.now()
            }
            
            # Cache the preview
            st.session_state[preview_key] = preview_data
            
            # Display results
            display_preview_results(preview_data, from_cache=False)
            
    except Exception as e:
        st.error(f"❌ Preview failed: {str(e)}")
        
        # Show helpful error guidance
        st.info("""
        **Preview Error Help:**
        - Check if all referenced tables exist
        - Verify column names are correct
        - Ensure JOIN conditions are valid
        """)

def create_preview_query(original_sql: str) -> str:
    """Create a preview version of the SQL query with LIMIT"""
    
    sql_upper = original_sql.upper().strip()
    
    # If query already has LIMIT, respect it but cap at preview limit
    if 'LIMIT' in sql_upper:
        # Extract current limit and use smaller value
        import re
        limit_match = re.search(r'LIMIT\s+(\d+)', sql_upper)
        if limit_match:
            current_limit = int(limit_match.group(1))
            preview_limit = min(current_limit, 10)  # Use smaller limit for preview
            return re.sub(r'LIMIT\s+\d+', f'LIMIT {preview_limit}', original_sql, flags=re.IGNORECASE)
    
    # Add LIMIT to SELECT queries
    if sql_upper.startswith('SELECT'):
        return f"{original_sql.rstrip(';')} LIMIT 10;"
    
    # For non-SELECT queries, return as-is (though they should be blocked by safety)
    return original_sql

def estimate_total_rows(original_sql: str, preview_df: pd.DataFrame) -> dict:
    """Estimate total rows for the full query"""
    
    estimation = {
        'method': 'unknown',
        'estimated_count': '?',
        'confidence': 'low'
    }
    
    try:
        # Method 1: If preview returned less than limit, that's the total
        if len(preview_df) < 10:
            estimation = {
                'method': 'exact',
                'estimated_count': len(preview_df),
                'confidence': 'high'
            }
        
        # Method 2: Try to get approximate count using COUNT query
        else:
            count_sql = convert_to_count_query(original_sql)
            if count_sql:
                count_result = st.session_state.db_manager.execute_query(count_sql)
                if not count_result.empty:
                    total_count = count_result.iloc[0, 0]
                    estimation = {
                        'method': 'count_query',
                        'estimated_count': total_count,
                        'confidence': 'high'
                    }
                    
        # Method 3: Extrapolation based on preview
        if estimation['method'] == 'unknown':
            # Simple extrapolation (not very accurate, but gives an idea)
            estimation = {
                'method': 'extrapolation',
                'estimated_count': f"{len(preview_df) * 10}+",
                'confidence': 'low'
            }
    
    except Exception as e:
        # If all methods fail, just indicate we have more data
        estimation = {
            'method': 'unknown',
            'estimated_count': '10+',
            'confidence': 'low'
        }
    
    return estimation

def convert_to_count_query(original_sql: str) -> str:
    """Convert a SELECT query to a COUNT query for estimation"""
    
    try:
        sql_upper = original_sql.upper().strip()
        
        # Simple conversion for basic SELECT queries
        if sql_upper.startswith('SELECT') and 'GROUP BY' not in sql_upper:
            # Find FROM clause
            from_index = sql_upper.find('FROM')
            if from_index != -1:
                from_clause = original_sql[from_index:]
                
                # Remove ORDER BY and LIMIT
                from_clause = re.sub(r'\s+ORDER\s+BY\s+[^;]*', '', from_clause, flags=re.IGNORECASE)
                from_clause = re.sub(r'\s+LIMIT\s+\d+', '', from_clause, flags=re.IGNORECASE)
                
                return f"SELECT COUNT(*) {from_clause}"
        
        return None
    
    except Exception:
        return None

def display_preview_results(preview_data: dict, from_cache: bool = False):
    """Display the preview results in a compact format"""
    
    df = preview_data['data']
    estimated = preview_data['estimated_total']
    
    # Preview header with statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Preview Rows", len(df))
    
    with col2:
        if estimated['confidence'] == 'high' and isinstance(estimated['estimated_count'], int):
            st.metric("Est. Total", f"{estimated['estimated_count']:,}")
        else:
            st.metric("Est. Total", estimated['estimated_count'])
    
    with col3:
        exec_time = preview_data['execution_time']
        st.metric("Preview Time", f"{exec_time:.2f}s")
    
    # Show cache status
    if from_cache:
        st.caption("🔄 From cache - click 'Refresh Preview' for latest data")
    else:
        st.caption("✨ Fresh preview generated")
    
    # Display preview data
    if not df.empty:
        # Compact table display
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=200  # Compact height for preview
        )
        
        # Show column info
        with st.expander("📊 Column Details"):
            col_info = []
            for col in df.columns:
                dtype = str(df[col].dtype)
                null_count = df[col].isnull().sum()
                col_info.append({
                    "Column": col,
                    "Type": dtype,
                    "Nulls": f"{null_count}/{len(df)}"
                })
            
            col_df = pd.DataFrame(col_info)
            st.dataframe(col_df, hide_index=True, use_container_width=True)
        
        # Performance hint
        if estimated['confidence'] == 'high' and isinstance(estimated['estimated_count'], int):
            if estimated['estimated_count'] > 1000:
                st.warning(f"⚠️ Full query will return ~{estimated['estimated_count']:,} rows. Consider adding filters for better performance.")
            elif estimated['estimated_count'] > 10000:
                st.error(f"🚨 Large result set (~{estimated['estimated_count']:,} rows). Strongly recommend adding WHERE clause to limit results.")
    
    else:
        st.info("📭 Preview returned no data. The full query might have conditions that filter out all results, or the referenced tables might be empty.")
        
        # Helpful suggestions for empty results
        st.markdown("""
        **Possible reasons for empty preview:**
        - Tables are empty or have no matching data
        - JOIN conditions are too restrictive
        - WHERE filters are excluding all rows
        - Table/column names might be incorrect
        """)
if __name__ == "__main__":
    main()