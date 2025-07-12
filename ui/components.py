# ui/components.py - Complete rewrite for Phase 3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json

from database.connections import DatabaseManager
from database.models import ConnectionConfig, DatabaseType
from database.schema_analyzer import SchemaAnalyzer

class UIComponents:
    
    @staticmethod
    def render_header():
        """Render the main application header"""
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 1rem 0;">
                <h1 style="color: #1e3c72; margin-bottom: 0;">🔍 SQL Query Builder Pro</h1>
                <p style="color: #666; margin-top: 0;">Powered by Agarthaweb</p>
            </div>
            """, unsafe_allow_html=True)
    
    @staticmethod
    def render_sidebar_navigation():
        """Render sidebar navigation menu"""
        
        st.markdown("### 🧭 Navigation")
        
        # Quick stats about current session
        if st.session_state.db_manager.get_active_engine():
            if 'query_history' in st.session_state:
                query_count = len(st.session_state.query_history)
                successful_queries = len([q for q in st.session_state.query_history if q.get('success', False)])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Queries", query_count)
                with col2:
                    st.metric("Success", f"{successful_queries}/{query_count}" if query_count > 0 else "0/0")
        
        st.markdown("---")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Refresh Schema", use_container_width=True):
            if 'schema_analyzer' in st.session_state:
                del st.session_state.schema_analyzer
                del st.session_state.schema
            st.rerun()
        
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.query_history = []
            st.success("History cleared!")
        
        if st.button("📊 Sample Queries", use_container_width=True):
            st.session_state.show_samples = True
    
    @staticmethod
    def render_connection_manager():
        """Enhanced database connection manager"""
        
        st.markdown("### 🔌 Database Connections")
        
        # Show active connections
        connections = st.session_state.db_manager.list_connections()
        active_connection = st.session_state.db_manager.active_connection
        
        if connections:
            st.markdown("**Active Connections:**")
            for conn in connections:
                is_active = conn == active_connection
                status = "🟢" if is_active else "⚪"
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{status} {conn}")
                with col2:
                    if not is_active and st.button("Connect", key=f"connect_{conn}"):
                        st.session_state.db_manager.set_active_connection(conn)
                        st.rerun()
        
        # Connection form in expander
        with st.expander("➕ Add New Connection"):
            UIComponents.render_connection_form()
    
    @staticmethod
    def render_connection_form():
        """Database connection form"""
        
        conn_name = st.text_input("Connection Name", placeholder="My Database")
        db_type = st.selectbox("Database Type", ["SQLite", "MySQL", "PostgreSQL"])
        
        if db_type == "SQLite":
            col1, col2 = st.columns([2, 1])
            with col1:
                db_file = st.text_input("Database File", placeholder="path/to/database.db")
            with col2:
                if st.button("📁 Browse"):
                    st.info("File browser not implemented in this demo")
            
            conn_string = f"sqlite:///{db_file}" if db_file else ""
            
        elif db_type == "MySQL":
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Host", value="localhost")
                user = st.text_input("Username")
            with col2:
                port = st.number_input("Port", value=3306)
                password = st.text_input("Password", type="password")
            
            database = st.text_input("Database Name")
            conn_string = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}" if all([user, password, database]) else ""
            
        else:  # PostgreSQL
            col1, col2 = st.columns(2)
            with col1:
                host = st.text_input("Host", value="localhost")
                user = st.text_input("Username")
            with col2:
                port = st.number_input("Port", value=5432)
                password = st.text_input("Password", type="password")
            
            database = st.text_input("Database Name")
            conn_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}" if all([user, password, database]) else ""
        
        # Test and add connection
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧪 Test Connection", disabled=not conn_string):
                if conn_string:
                    is_valid, message = st.session_state.db_manager.test_connection(conn_string)
                    if is_valid:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
        
        with col2:
            if st.button("➕ Add Connection", disabled=not (conn_name and conn_string)):
                config = ConnectionConfig(
                    name=conn_name,
                    connection_string=conn_string,
                    database_type=DatabaseType.SQLITE if db_type == "SQLite" else DatabaseType.MYSQL if db_type == "MySQL" else DatabaseType.POSTGRESQL,
                    db_type=db_type.lower()
                )
                
                success = st.session_state.db_manager.add_connection(config)
                if success:
                    st.success("✅ Connection added!")
                    st.rerun()
                else:
                    st.error("❌ Failed to add connection")
    
    @staticmethod
    def render_schema_explorer():
        """Enhanced schema explorer with search and relationships"""
        
        if 'schema_analyzer' not in st.session_state:
            st.warning("Please connect to a database first.")
            return
        
        analyzer = st.session_state.schema_analyzer
        schema = st.session_state.schema
        
        # Search functionality
        search_col1, search_col2 = st.columns([2, 1])
        
        with search_col1:
            search_term = st.text_input(
                "🔍 Search tables and columns:", 
                placeholder="e.g., customer, order, email"
            )
        
        with search_col2:
            search_type = st.selectbox("Search in:", ["All", "Tables", "Columns"])
        
        if search_term:
            UIComponents.render_search_results(analyzer, search_term, search_type)
        else:
            UIComponents.render_schema_overview(analyzer, schema)
    
    @staticmethod
    def render_search_results(analyzer, search_term, search_type):
        """Render schema search results"""
        
        results = analyzer.search_schema(search_term)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if results['tables']:
                st.subheader("📋 Tables Found")
                for table in results['tables']:
                    with st.expander(f"🗃️ {table}"):
                        UIComponents.render_table_details(analyzer, table)
        
        with col2:
            if results['columns']:
                st.subheader("📊 Columns Found")
                
                # Group columns by table
                columns_by_table = {}
                for col in results['columns']:
                    table = col['table']
                    if table not in columns_by_table:
                        columns_by_table[table] = []
                    columns_by_table[table].append(col)
                
                for table, columns in columns_by_table.items():
                    st.write(f"**{table}:**")
                    for col in columns:
                        st.write(f"  • {col['column']} ({col['type']})")
        
        # Show suggestions if no results
        if not results['tables'] and not results['columns'] and results['suggestions']:
            st.info("🔍 **Suggestions:** " + ", ".join(results['suggestions'][:5]))
    
    @staticmethod
    def render_schema_overview(analyzer, schema):
        """Render complete schema overview"""
        
        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Tables", len(schema.tables))
        
        with col2:
            total_columns = sum(len(table.columns) for table in schema.tables)
            st.metric("Total Columns", total_columns)
        
        with col3:
            total_rows = sum(table.row_count or 0 for table in schema.tables)
            st.metric("Total Rows", f"{total_rows:,}" if total_rows > 0 else "Unknown")
        
        with col4:
            fk_count = sum(len(table.get_foreign_keys()) for table in schema.tables)
            st.metric("Relationships", fk_count)
        
        st.markdown("---")
        
        # Table details
        for table in schema.tables:
            with st.expander(f"🗃️ {table.name} ({len(table.columns)} columns)"):
                UIComponents.render_table_details(analyzer, table.name)
    
    @staticmethod
    def render_table_details(analyzer, table_name):
        """Render detailed table information"""
        
        schema = st.session_state.schema
        table = schema.get_table(table_name)
        
        if not table:
            st.error(f"Table {table_name} not found")
            return
        
        # Table info
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Rows:** ~{table.row_count:,}" if table.row_count else "**Rows:** Unknown")
            pk_columns = [c.name for c in table.get_primary_keys()]
            st.write(f"**Primary Keys:** {', '.join(pk_columns) if pk_columns else 'None'}")
        
        with col2:
            fk_columns = table.get_foreign_keys()
            st.write(f"**Foreign Keys:** {len(fk_columns)}")
            if table.description:
                st.write(f"**Description:** {table.description}")
        
        # Columns table
        columns_data = []
        for col in table.columns:
            flags = []
            if col.is_primary_key:
                flags.append("PK")
            if col.is_foreign_key:
                flags.append(f"FK→{col.foreign_key_table}")
            if not col.is_nullable:
                flags.append("NOT NULL")
            
            columns_data.append({
                "Column": col.name,
                "Type": col.data_type,
                "Flags": ", ".join(flags) if flags else "-",
                "Description": col.description or "-"
            })
        
        if columns_data:
            df = pd.DataFrame(columns_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Sample data
        if st.button(f"👀 View Sample Data", key=f"sample_{table_name}"):
            try:
                sample_df = analyzer.get_sample_data(table_name, limit=5)
                st.write("**Sample Data:**")
                st.dataframe(sample_df, use_container_width=True)
            except Exception as e:
                st.error(f"Error loading sample data: {e}")
        
        # Related tables
        related_tables = analyzer.get_related_tables(table_name)
        if related_tables:
            st.write(f"**Related Tables:** {', '.join(related_tables)}")
    
    @staticmethod
    def render_query_results_visualization():
        """Enhanced results visualization with charts"""
        
        if 'query_results' not in st.session_state:
            st.info("📊 Execute a query to see results and visualizations here!")
            return
        
        results = st.session_state.query_results
        df = results['data']
        
        # Results header
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader("📊 Query Results")
            st.write(f"**Query:** {results['natural_query']}")
        
        with col2:
            st.metric("Rows", results['row_count'])
        
        with col3:
            st.metric("Columns", len(df.columns))
        
        # Display options
        view_tab1, view_tab2, view_tab3 = st.tabs(["📋 Table View", "📈 Charts", "💾 Export"])
        
        with view_tab1:
            UIComponents.render_data_table(df)
        
        with view_tab2:
            UIComponents.render_auto_charts(df)
        
        with view_tab3:
            UIComponents.render_export_options(df, results)
    
    @staticmethod
    def render_data_table(df):
        """Enhanced data table with filtering and pagination"""
        
        if df.empty:
            st.warning("No data to display")
            return
        
        # Table controls
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Column filter
            all_columns = list(df.columns)
            selected_columns = st.multiselect(
                "Select columns to display:",
                all_columns,
                default=all_columns[:10]  # Show first 10 columns by default
            )
        
        with col2:
            # Row limit
            row_limit = st.selectbox("Rows to display:", [25, 50, 100, 500, "All"])
        
        with col3:
            # Search
            search_value = st.text_input("Search in data:", placeholder="Search...")
        
        # Apply filters
        display_df = df[selected_columns] if selected_columns else df
        
        if search_value:
            # Simple text search across all columns
            mask = display_df.astype(str).apply(
                lambda x: x.str.contains(search_value, case=False, na=False)
            ).any(axis=1)
            display_df = display_df[mask]
        
        if row_limit != "All":
            display_df = display_df.head(int(row_limit))
        
        # Display table
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Table statistics
        if not display_df.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Showing:** {len(display_df)} of {len(df)} rows")
            with col2:
                if search_value:
                    st.write(f"**Filtered by:** '{search_value}'")
            with col3:
                st.write(f"**Columns:** {len(display_df.columns)}")
    
    @staticmethod
    def render_auto_charts(df):
        """Automatically generate charts based on data types"""
        
        if df.empty:
            st.warning("No data available for visualization")
            return
        
        numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        if not numeric_columns and not categorical_columns:
            st.info("No suitable columns found for visualization")
            return
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Bar chart for categorical data
            if categorical_columns and len(df) <= 1000:  # Limit for performance
                cat_column = st.selectbox("Categorical column for bar chart:", categorical_columns)
                
                if cat_column:
                    value_counts = df[cat_column].value_counts().head(20)  # Top 20 values
                    
                    fig = px.bar(
                        x=value_counts.index,
                        y=value_counts.values,
                        title=f"Distribution of {cat_column}",
                        labels={'x': cat_column, 'y': 'Count'}
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
        
        with chart_col2:
            # Histogram for numeric data
            if numeric_columns:
                num_column = st.selectbox("Numeric column for histogram:", numeric_columns)
                
                if num_column:
                    fig = px.histogram(
                        df,
                        x=num_column,
                        title=f"Distribution of {num_column}",
                        nbins=30
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
        
        # Additional charts if we have both numeric and categorical
        if numeric_columns and categorical_columns and len(df) <= 1000:
            st.subheader("📈 Advanced Visualizations")
            
            viz_col1, viz_col2 = st.columns(2)
            
            with viz_col1:
                # Scatter plot
                if len(numeric_columns) >= 2:
                    x_col = st.selectbox("X-axis:", numeric_columns, key="scatter_x")
                    y_col = st.selectbox("Y-axis:", [col for col in numeric_columns if col != x_col], key="scatter_y")
                    color_col = st.selectbox("Color by:", ["None"] + categorical_columns, key="scatter_color")
                    
                    if x_col and y_col:
                        fig = px.scatter(
                            df,
                            x=x_col,
                            y=y_col,
                            color=color_col if color_col != "None" else None,
                            title=f"{y_col} vs {x_col}"
                        )
                        st.plotly_chart(fig, use_container_width=True)
            
            with viz_col2:
                # Box plot
                if categorical_columns and numeric_columns:
                    cat_col = st.selectbox("Category:", categorical_columns, key="box_cat")
                    num_col = st.selectbox("Numeric:", numeric_columns, key="box_num")
                    
                    if cat_col and num_col:
                        fig = px.box(
                            df,
                            x=cat_col,
                            y=num_col,
                            title=f"{num_col} by {cat_col}"
                        )
                        fig.update_xaxes(tickangle=45)
                        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_export_options(df, results):
        """Export options for query results"""
        
        st.subheader("💾 Export Options")
        
        # Export formats
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV Export
            csv_data = df.to_csv(index=False)
            st.download_button(
                "📄 Download CSV",
                data=csv_data,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # JSON Export
            json_data = df.to_json(orient='records', indent=2)
            st.download_button(
                "📋 Download JSON",
                data=json_data,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col3:
            # SQL Export (with the query that generated this data)
            sql_export = f"""-- Query executed on: {results['timestamp']}
-- Natural language: {results['natural_query']}
-- Rows returned: {results['row_count']}

{results['sql']};"""
            
            st.download_button(
                "🗃️ Download SQL",
                data=sql_export,
                file_name=f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                mime="text/plain",
                use_container_width=True
            )
        
        # Export summary
        st.markdown("---")
        st.info(f"""
        **Export Summary:**
        - **Rows:** {len(df):,}
        - **Columns:** {len(df.columns)}
        - **Query:** {results['natural_query']}
        - **Generated:** {results['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
        """)