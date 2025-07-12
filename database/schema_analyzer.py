from sqlalchemy import inspect, text, MetaData
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from .models import DatabaseSchema, TableInfo, ColumnInfo, DatabaseType
import re
from collections import defaultdict

class SchemaAnalyzer:
    def __init__(self, engine):
        self.engine = engine
        self.inspector = inspect(engine)
        self.metadata = MetaData()
        self._table_relationships = {}
        self._column_stats = {}
    
    def analyze_database(self, database_name: str = None) -> DatabaseSchema:
        """Enhanced database schema analysis with relationships and statistics"""
        try:
            # Get database type
            db_type = self._get_database_type()
            
            # Get database name
            if not database_name:
                database_name = self._get_database_name()
            
            # Get all tables with enhanced analysis
            table_names = self.inspector.get_table_names()
            tables = []
            
            # Build relationship map first
            self._build_relationship_map(table_names)
            
            for table_name in table_names:
                table_info = self._analyze_table_enhanced(table_name)
                tables.append(table_info)
            
            # Sort tables by importance (tables with more relationships first)
            tables.sort(key=lambda t: len([c for c in t.columns if c.is_foreign_key or c.is_primary_key]), reverse=True)
            
            return DatabaseSchema(
                database_name=database_name,
                database_type=db_type,
                tables=tables,
                connection_string=str(self.engine.url)
            )
            
        except Exception as e:
            raise SQLAlchemyError(f"Enhanced schema analysis failed: {str(e)}")
    
    def _get_database_type(self) -> DatabaseType:
        """Determine database type from engine"""
        dialect_name = self.engine.dialect.name.lower()
        
        if 'sqlite' in dialect_name:
            return DatabaseType.SQLITE
        elif 'mysql' in dialect_name:
            return DatabaseType.MYSQL
        elif 'postgresql' in dialect_name:
            return DatabaseType.POSTGRESQL
        else:
            # Default to SQLite for unknown types
            return DatabaseType.SQLITE
    
    def _get_database_name(self) -> str:
        """Extract database name from connection"""
        try:
            # For SQLite, use the filename
            if self.engine.dialect.name == 'sqlite':
                db_path = str(self.engine.url.database)
                if db_path == ':memory:':
                    return 'In-Memory Database'
                return db_path.split('/')[-1] if '/' in db_path else db_path
            
            # For other databases, use the database name from URL
            return self.engine.url.database or 'Unknown Database'
            
        except:
            return 'Unknown Database'
    
    def _build_relationship_map(self, table_names: List[str]):
        """Build a comprehensive map of table relationships"""
        relationships = defaultdict(list)
        
        for table_name in table_names:
            try:
                # Get foreign keys
                fk_constraints = self.inspector.get_foreign_keys(table_name)
                
                for fk in fk_constraints:
                    source_table = table_name
                    target_table = fk['referred_table']
                    
                    # Store bidirectional relationships
                    relationships[source_table].append({
                        'type': 'foreign_key',
                        'target_table': target_table,
                        'source_columns': fk['constrained_columns'],
                        'target_columns': fk['referred_columns']
                    })
                    
                    relationships[target_table].append({
                        'type': 'referenced_by',
                        'source_table': source_table,
                        'source_columns': fk['constrained_columns'],
                        'target_columns': fk['referred_columns']
                    })
                    
            except Exception as e:
                print(f"Warning: Could not analyze relationships for {table_name}: {e}")
        
        self._table_relationships = relationships
    
    def _analyze_table_enhanced(self, table_name: str) -> TableInfo:
        """Enhanced table analysis with statistics and relationships"""
        try:
            # Get basic column information
            columns_info = self.inspector.get_columns(table_name)
            
            # Get constraints
            pk_constraint = self.inspector.get_pk_constraint(table_name)
            primary_keys = pk_constraint.get('constrained_columns', [])
            
            fk_constraints = self.inspector.get_foreign_keys(table_name)
            foreign_keys = {}
            for fk in fk_constraints:
                for local_col, remote_col in zip(fk['constrained_columns'], fk['referred_columns']):
                    foreign_keys[local_col] = {
                        'table': fk['referred_table'],
                        'column': remote_col
                    }
            
            # Get unique constraints
            try:
                unique_constraints = self.inspector.get_unique_constraints(table_name)
                unique_columns = set()
                for constraint in unique_constraints:
                    unique_columns.update(constraint['column_names'])
            except:
                unique_columns = set()
            
            # Build enhanced column information
            columns = []
            for col_info in columns_info:
                col_name = col_info['name']
                
                # Get column statistics
                col_stats = self._get_column_statistics(table_name, col_name)
                
                column = ColumnInfo(
                    name=col_name,
                    data_type=self._normalize_data_type(str(col_info['type'])),
                    is_nullable=col_info.get('nullable', True),
                    is_primary_key=col_name in primary_keys,
                    is_foreign_key=col_name in foreign_keys,
                    foreign_key_table=foreign_keys.get(col_name, {}).get('table'),
                    foreign_key_column=foreign_keys.get(col_name, {}).get('column'),
                    default_value=col_info.get('default'),
                    max_length=self._extract_max_length(str(col_info['type'])),
                    description=self._generate_column_description(col_name, col_stats)
                )
                
                # Add unique constraint info
                if col_name in unique_columns:
                    column.description = f"{column.description or ''} (Unique)".strip()
                
                columns.append(column)
            
            # Get enhanced table statistics
            row_count = self._get_table_row_count(table_name)
            
            # Generate table description
            table_description = self._generate_table_description(table_name, columns, row_count)
            
            return TableInfo(
                name=table_name,
                columns=columns,
                row_count=row_count,
                description=table_description
            )
            
        except Exception as e:
            return TableInfo(
                name=table_name,
                columns=[],
                description=f"Analysis failed: {str(e)}"
            )
    
    def _normalize_data_type(self, data_type: str) -> str:
        """Normalize database-specific data types to common types"""
        data_type = data_type.upper()
        
        # Common mappings
        type_mappings = {
            'VARCHAR': 'TEXT',
            'CHAR': 'TEXT',
            'NVARCHAR': 'TEXT',
            'NCHAR': 'TEXT',
            'CLOB': 'TEXT',
            'LONGTEXT': 'TEXT',
            'MEDIUMTEXT': 'TEXT',
            'TINYTEXT': 'TEXT',
            
            'INT': 'INTEGER',
            'BIGINT': 'INTEGER',
            'SMALLINT': 'INTEGER',
            'TINYINT': 'INTEGER',
            'MEDIUMINT': 'INTEGER',
            
            'FLOAT': 'REAL',
            'DOUBLE': 'REAL',
            'DECIMAL': 'REAL',
            'NUMERIC': 'REAL',
            
            'DATETIME': 'TIMESTAMP',
            'TIMESTAMP': 'TIMESTAMP',
            'DATE': 'DATE',
            'TIME': 'TIME'
        }
        
        # Extract base type (remove size specifications)
        base_type = re.sub(r'\([^)]*\)', '', data_type).strip()
        
        return type_mappings.get(base_type, base_type)
    
    def _extract_max_length(self, data_type: str) -> Optional[int]:
        """Extract maximum length from data type specification"""
        match = re.search(r'\((\d+)\)', data_type)
        if match:
            return int(match.group(1))
        return None
    
    def _get_column_statistics(self, table_name: str, column_name: str) -> Dict[str, Any]:
        """Get basic statistics for a column"""
        try:
            with self.engine.connect() as conn:
                # Get distinct count and null count
                query = f"""
                SELECT 
                    COUNT(DISTINCT {column_name}) as distinct_count,
                    COUNT(*) as total_count,
                    COUNT(*) - COUNT({column_name}) as null_count
                FROM {table_name}
                """
                result = conn.execute(text(query)).fetchone()
                
                return {
                    'distinct_count': result[0] if result else 0,
                    'total_count': result[1] if result else 0,
                    'null_count': result[2] if result else 0,
                    'null_percentage': (result[2] / result[1] * 100) if result and result[1] > 0 else 0
                }
        except Exception as e:
            return {'distinct_count': 0, 'total_count': 0, 'null_count': 0, 'null_percentage': 0}
    
    def _generate_column_description(self, column_name: str, stats: Dict[str, Any]) -> str:
        """Generate intelligent description for a column"""
        descriptions = []
        
        # Infer purpose from column name
        name_lower = column_name.lower()
        
        if 'id' in name_lower:
            descriptions.append("Identifier")
        elif 'name' in name_lower:
            descriptions.append("Name field")
        elif 'email' in name_lower:
            descriptions.append("Email address")
        elif 'phone' in name_lower:
            descriptions.append("Phone number")
        elif 'date' in name_lower:
            descriptions.append("Date field")
        elif 'time' in name_lower:
            descriptions.append("Time field")
        elif 'created' in name_lower:
            descriptions.append("Creation timestamp")
        elif 'updated' in name_lower:
            descriptions.append("Update timestamp")
        elif 'status' in name_lower:
            descriptions.append("Status field")
        elif 'amount' in name_lower or 'price' in name_lower:
            descriptions.append("Monetary value")
        elif 'count' in name_lower or 'quantity' in name_lower:
            descriptions.append("Quantity field")
        
        # Add statistics info
        if stats.get('distinct_count', 0) > 0:
            total = stats.get('total_count', 0)
            distinct = stats.get('distinct_count', 0)
            if total > 0:
                uniqueness = distinct / total
                if uniqueness > 0.95:
                    descriptions.append("Highly unique")
                elif uniqueness < 0.1:
                    descriptions.append("Low cardinality")
        
        return ", ".join(descriptions) if descriptions else None
    
    def _generate_table_description(self, table_name: str, columns: List[ColumnInfo], row_count: int) -> str:
        """Generate intelligent description for a table"""
        descriptions = []
        
        # Infer purpose from table name
        name_lower = table_name.lower()
        
        if 'user' in name_lower or 'customer' in name_lower:
            descriptions.append("User/customer data")
        elif 'order' in name_lower:
            descriptions.append("Order/transaction data")
        elif 'product' in name_lower:
            descriptions.append("Product catalog")
        elif 'log' in name_lower:
            descriptions.append("Log data")
        elif 'config' in name_lower or 'setting' in name_lower:
            descriptions.append("Configuration data")
        
        # Add structural info
        fk_count = len([c for c in columns if c.is_foreign_key])
        
        if fk_count > 0:
            descriptions.append(f"Has {fk_count} foreign key(s)")
        
        if row_count is not None:
            if row_count > 10000:
                descriptions.append("Large table")
            elif row_count < 100:
                descriptions.append("Small table")
        
        return ", ".join(descriptions) if descriptions else f"Table with {len(columns)} columns"
    
    def _get_table_row_count(self, table_name: str) -> Optional[int]:
        """Get approximate row count for a table"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                return result.scalar()
        except:
            return None
    
    def get_table_relationships(self, table_name: str) -> List[Dict]:
        """Get all relationships for a specific table"""
        return self._table_relationships.get(table_name, [])
    
    def get_related_tables(self, table_name: str) -> List[str]:
        """Get list of tables related to the given table"""
        relationships = self._table_relationships.get(table_name, [])
        related_tables = set()
        
        for rel in relationships:
            if rel['type'] == 'foreign_key':
                related_tables.add(rel['target_table'])
            elif rel['type'] == 'referenced_by':
                related_tables.add(rel['source_table'])
        
        return list(related_tables)
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Get sample data from a table"""
        try:
            with self.engine.connect() as conn:
                query = f"SELECT * FROM {table_name} LIMIT {limit}"
                return pd.read_sql(text(query), conn)
        except Exception as e:
            return pd.DataFrame()
    
    def search_tables(self, search_term: str) -> List[str]:
        """Search for tables by name"""
        table_names = self.inspector.get_table_names()
        search_term = search_term.lower()
        
        return [
            table for table in table_names 
            if search_term in table.lower()
        ]
    
    def search_columns(self, search_term: str) -> Dict[str, List[str]]:
        """Search for columns across all tables"""
        results = {}
        search_term = search_term.lower()
        
        for table_name in self.inspector.get_table_names():
            try:
                columns = self.inspector.get_columns(table_name)
                matching_columns = [
                    col['name'] for col in columns 
                    if search_term in col['name'].lower()
                ]
                
                if matching_columns:
                    results[table_name] = matching_columns
                    
            except:
                continue
        
        return results
    
    def suggest_joins(self, tables: List[str]) -> List[Dict[str, str]]:
        """Suggest possible JOIN operations between tables"""
        joins = []
        
        for i, table1 in enumerate(tables):
            for table2 in tables[i+1:]:
                # Check if table1 has FK to table2
                relationships = self._table_relationships.get(table1, [])
                for rel in relationships:
                    if rel['type'] == 'foreign_key' and rel['target_table'] == table2:
                        joins.append({
                            'type': 'INNER JOIN',
                            'table1': table1,
                            'table2': table2,
                            'condition': f"{table1}.{rel['source_columns'][0]} = {table2}.{rel['target_columns'][0]}"
                        })
                
                # Check if table2 has FK to table1
                relationships = self._table_relationships.get(table2, [])
                for rel in relationships:
                    if rel['type'] == 'foreign_key' and rel['target_table'] == table1:
                        joins.append({
                            'type': 'INNER JOIN',
                            'table1': table2,
                            'table2': table1,
                            'condition': f"{table2}.{rel['source_columns'][0]} = {table1}.{rel['target_columns'][0]}"
                        })
        
        return joins
    
    def get_schema_context_optimized(self, max_tokens: int = 3000) -> str:
        """Get optimized schema context for LLM with token limit consideration"""
        try:
            schema = self.analyze_database()
            
            # Start with basic info
            context_parts = [
                f"Database: {schema.database_name} ({schema.database_type.value})",
                f"Tables: {len(schema.tables)}"
            ]
            
            # Estimate tokens (rough: 1 token ≈ 4 characters)
            current_length = len("\n".join(context_parts)) 
            target_length = max_tokens * 4  # Convert tokens to characters
            
            # Sort tables by importance
            important_tables = sorted(schema.tables, 
                                    key=lambda t: (
                                        len([c for c in t.columns if c.is_primary_key]) * 3 +
                                        len([c for c in t.columns if c.is_foreign_key]) * 2 +
                                        (t.row_count or 0) / 1000  # Favor tables with more data
                                    ), reverse=True)
            
            # Add tables until we hit token limit
            for table in important_tables:
                table_context = f"\n\nTable: {table.name}"
                if table.description:
                    table_context += f" - {table.description}"
                
                # Add essential columns first (PK, FK, then others)
                essential_columns = [c for c in table.columns if c.is_primary_key or c.is_foreign_key]
                other_columns = [c for c in table.columns if not c.is_primary_key and not c.is_foreign_key]
                
                for col in essential_columns:
                    col_info = f"\n  - {col.name}: {col.data_type}"
                    if col.is_primary_key:
                        col_info += " (PK)"
                    if col.is_foreign_key:
                        col_info += f" (FK -> {col.foreign_key_table}.{col.foreign_key_column})"
                    if not col.is_nullable:
                        col_info += " (NOT NULL)"
                    
                    # Check if adding this would exceed limit
                    if current_length + len(table_context + col_info) > target_length:
                        context_parts.append(f"\n... (schema truncated to fit token limit)")
                        return "\n".join(context_parts)
                    
                    table_context += col_info
                
                # Add other columns if space permits
                for col in other_columns[:5]:  # Limit to 5 additional columns per table
                    col_info = f"\n  - {col.name}: {col.data_type}"
                    if not col.is_nullable:
                        col_info += " (NOT NULL)"
                    
                    if current_length + len(table_context + col_info) > target_length:
                        if len(other_columns) > 5:
                            table_context += f"\n  ... and {len(other_columns) - 5} more columns"
                        break
                    
                    table_context += col_info
                
                # Add row count if available
                if table.row_count is not None:
                    table_context += f"\n  Rows: {table.row_count:,}"
                
                context_parts.append(table_context)
                current_length += len(table_context)
            
            # Add relationship information if space permits
            if current_length < target_length * 0.8:  # Use 80% of available space
                relationships = []
                for table in important_tables[:5]:  # Top 5 tables only
                    related = self.get_related_tables(table.name)
                    if related:
                        relationships.append(f"{table.name} -> {', '.join(related)}")
                
                if relationships:
                    rel_context = f"\n\nKey Relationships:\n" + "\n".join(relationships)
                    if current_length + len(rel_context) <= target_length:
                        context_parts.append(rel_context)
            
            return "\n".join(context_parts)
            
        except Exception as e:
            return f"Schema analysis failed: {str(e)}"
    
    def search_schema(self, search_term: str) -> Dict[str, Any]:
        """Advanced schema search functionality"""
        search_term = search_term.lower()
        results = {
            'tables': [],
            'columns': [],
            'relationships': [],
            'suggestions': []
        }
        
        try:
            schema = self.analyze_database()
            
            # Search tables
            for table in schema.tables:
                if search_term in table.name.lower():
                    results['tables'].append({
                        'name': table.name,
                        'description': table.description,
                        'columns': len(table.columns),
                        'rows': table.row_count
                    })
                
                # Search columns
                for col in table.columns:
                    if search_term in col.name.lower():
                        results['columns'].append({
                            'table': table.name,
                            'column': col.name,
                            'type': col.data_type,
                            'description': col.description,
                            'is_key': col.is_primary_key or col.is_foreign_key
                        })
            
            # Search relationships
            for table_name, relationships in self._table_relationships.items():
                for rel in relationships:
                    if (search_term in table_name.lower() or 
                        search_term in rel.get('target_table', '').lower() or
                        search_term in rel.get('source_table', '').lower()):
                        
                        results['relationships'].append({
                            'type': rel['type'],
                            'from_table': table_name,
                            'to_table': rel.get('target_table', rel.get('source_table', '')),
                            'columns': rel.get('source_columns', [])
                        })
            
            # Generate suggestions
            if not any(results.values()):
                # Fuzzy matching suggestions
                all_terms = []
                for table in schema.tables:
                    all_terms.append(table.name)
                    all_terms.extend([col.name for col in table.columns])
                
                # Simple fuzzy matching
                suggestions = [term for term in all_terms if search_term in term.lower()]
                results['suggestions'] = suggestions[:5]
            
            return results
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_join_suggestions_for_query(self, mentioned_tables: List[str]) -> List[str]:
        """Get JOIN suggestions for a natural language query"""
        if len(mentioned_tables) < 2:
            return []
        
        join_suggestions = []
        joins = self.suggest_joins(mentioned_tables)
        
        for join in joins:
            suggestion = f"{join['type']} {join['table2']} ON {join['condition']}"
            join_suggestions.append(suggestion)
        
        return join_suggestions
        

    def get_schema_context_optimized(self, max_tokens: int = 3000) -> str:
        """Get optimized schema context for LLM with token limit consideration"""
        
        schema = self.analyze_database()
        
        # Start with basic info
        context_parts = [
            f"Database: {schema.database_name} ({schema.database_type.value})",
            f"Tables: {len(schema.tables)}"
        ]
        
        # Estimate tokens (rough: 1 token ≈ 4 characters)
        current_length = len("\n".join(context_parts))
        target_length = max_tokens * 4  # Convert tokens to characters
        
        # Sort tables by importance
        important_tables = sorted(schema.tables, 
            key=lambda t: (
                len(t.get_foreign_keys()) * 3 +  # Tables with FKs are more important
                len(t.get_primary_keys()) * 2 +   # Tables with PKs are important
                (t.row_count or 0) / 1000         # Favor tables with more data
            ), reverse=True
        )
        
        # Add tables until we hit token limit
        for table in important_tables:
            table_context = f"\n\nTable: {table.name}"
            
            if table.description:
                table_context += f"\n  Purpose: {table.description}"
            
            # Add essential columns first (PK, FK, then others)
            essential_columns = [c for c in table.columns if c.is_primary_key or c.is_foreign_key]
            other_columns = [c for c in table.columns if not c.is_primary_key and not c.is_foreign_key]
            
            for col in essential_columns:
                flags = []
                if col.is_primary_key:
                    flags.append("PK")
                if col.is_foreign_key:
                    flags.append(f"FK→{col.foreign_key_table}")
                
                col_info = f"\n  - {col.name}: {col.data_type}"
                if flags:
                    col_info += f" ({', '.join(flags)})"
                
                # Check if adding this would exceed limit
                if current_length + len(table_context + col_info) > target_length:
                    break
                
                table_context += col_info
            
            # Add other columns if space permits
            for col in other_columns[:5]:  # Limit to 5 additional columns per table
                col_info = f"\n  - {col.name}: {col.data_type}"
                
                if current_length + len(table_context + col_info) > target_length:
                    break
                
                table_context += col_info
            
            # Add row count if available
            if table.row_count:
                table_context += f"\n  Rows: ~{table.row_count:,}"
            
            # Check if we can fit this table
            if current_length + len(table_context) > target_length:
                break
            
            context_parts.append(table_context)
            current_length += len(table_context)
        
        # Add relationship information if space permits
        if current_length < target_length * 0.8:  # Use 80% of available space
            relationships = []
            for table in important_tables[:5]:  # Top 5 tables only
                related = self.get_related_tables(table.name)
                if related:
                    relationships.append(f"{table.name} → {', '.join(related[:3])}")
            
            if relationships:
                rel_context = f"\n\nKey Relationships:\n" + "\n".join(relationships)
                if current_length + len(rel_context) < target_length:
                    context_parts.append(rel_context)
        
        return "\n".join(context_parts)

    def search_schema(self, search_term: str) -> Dict[str, Any]:
        """Advanced schema search functionality"""
        
        search_term = search_term.lower()
        
        results = {
            'tables': [],
            'columns': [],
            'relationships': [],
            'suggestions': []
        }
        
        # Search tables
        for table_name in self.inspector.get_table_names():
            if search_term in table_name.lower():
                results['tables'].append(table_name)
        
        # Search columns
        for table_name in self.inspector.get_table_names():
            columns = self.inspector.get_columns(table_name)
            for col in columns:
                if search_term in col['name'].lower():
                    results['columns'].append({
                        'table': table_name,
                        'column': col['name'],
                        'type': col['type']
                    })
        
        # Search relationships
        for table_name in self.inspector.get_table_names():
            related_tables = self.get_related_tables(table_name)
            for related in related_tables:
                if search_term in table_name.lower() or search_term in related.lower():
                    results['relationships'].append({
                        'from': table_name,
                        'to': related
                    })
        
        # Generate suggestions
        if not results['tables'] and not results['columns']:
            # Fuzzy matching suggestions
            all_terms = []
            for table_name in self.inspector.get_table_names():
                all_terms.append(table_name)
                columns = self.inspector.get_columns(table_name)
                all_terms.extend([col['name'] for col in columns])
            
            # Simple fuzzy matching
            suggestions = [term for term in all_terms if search_term in term.lower()]
            results['suggestions'] = suggestions[:5]
        
        return results

    def get_join_suggestions_for_query(self, mentioned_tables: List[str]) -> List[str]:
        """Get JOIN suggestions for a natural language query"""
        
        if len(mentioned_tables) < 2:
            return []
        
        join_suggestions = []
        joins = self.suggest_joins(mentioned_tables)
        
        for join in joins:
            suggestion = f"{join['type']} {join['table2']} ON {join['condition']}"
            join_suggestions.append(suggestion)
        
        return join_suggestions