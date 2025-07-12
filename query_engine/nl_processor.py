# query_engine/nl_processor.py
import re
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import google.generativeai as genai

from database.models import DatabaseSchema
from utils.helpers import is_read_only_query, extract_table_names
from config import GOOGLE_API_KEY, GEMINI_MODEL, LLM_TEMPERATURE

class QueryType(Enum):
    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    CREATE = "create"
    DROP = "drop"
    UNKNOWN = "unknown"

@dataclass
class QueryIntent:
    query_type: QueryType
    confidence: float
    tables_mentioned: List[str]
    columns_mentioned: List[str]
    requires_joins: bool
    complexity_score: int

@dataclass
class QueryResult:
    sql_query: str
    intent: QueryIntent
    explanation: str
    warnings: List[str]
    is_safe: bool

class NLProcessor:
    def __init__(self, schema: DatabaseSchema, schema_analyzer=None):
        self.schema = schema
        self.schema_analyzer = schema_analyzer  # Optional for advanced features
        
        # Configure Gemini
        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=genai.types.GenerationConfig(
                temperature=LLM_TEMPERATURE,
                max_output_tokens=1000,
            )
        )
        
    def process_query(self, natural_query: str) -> QueryResult:
        """Main entry point - like a smart WordPress AJAX handler"""
        
        # Step 1: Analyze intent (like parsing $_POST data)
        intent = self._analyze_intent(natural_query)
        
        # Step 2: Generate SQL (like building database query)
        sql_query = self._generate_sql(natural_query, intent)
        
        # Step 3: Validate and add safety checks (like wp_verify_nonce)
        is_safe = self._validate_query_safety(sql_query)
        warnings = self._generate_warnings(sql_query, intent)
        
        # Step 4: Generate explanation (like admin notices)
        explanation = self._explain_query(sql_query, natural_query)
        
        return QueryResult(
            sql_query=sql_query,
            intent=intent,
            explanation=explanation,
            warnings=warnings,
            is_safe=is_safe
        )
    
    def _analyze_intent(self, query: str) -> QueryIntent:
        """Analyze what the user wants to do - like parsing form data"""
        
        # Simple keyword-based classification first
        query_lower = query.lower()
        
        # Detect query type (like checking $_POST['action'])
        if any(word in query_lower for word in ['show', 'get', 'find', 'list', 'select', 'what', 'how many']):
            query_type = QueryType.SELECT
        elif any(word in query_lower for word in ['add', 'insert', 'create new']):
            query_type = QueryType.INSERT
        elif any(word in query_lower for word in ['update', 'change', 'modify']):
            query_type = QueryType.UPDATE
        elif any(word in query_lower for word in ['delete', 'remove']):
            query_type = QueryType.DELETE
        else:
            query_type = QueryType.UNKNOWN
        
        # Find mentioned tables (like finding post types in query)
        tables_mentioned = []
        for table in self.schema.get_table_names():
            if table.lower() in query_lower or any(part in query_lower for part in table.lower().split('_')):
                tables_mentioned.append(table)
        
        # Detect if joins are needed (like checking for related post data)
        requires_joins = len(tables_mentioned) > 1 or any(word in query_lower for word in ['join', 'with', 'and', 'related'])
        
        # Calculate complexity (like checking query performance)
        complexity_score = self._calculate_complexity(query, tables_mentioned, requires_joins)
        
        return QueryIntent(
            query_type=query_type,
            confidence=0.8,  # We'll make this smarter later
            tables_mentioned=tables_mentioned,
            columns_mentioned=[],  # TODO: Implement column detection
            requires_joins=requires_joins,
            complexity_score=complexity_score
        )
    
    def _generate_sql(self, natural_query: str, intent: QueryIntent) -> str:
        """Generate SQL using Gemini - like building WP_Query"""
        
        # Build context-aware prompt
        prompt = self._build_generation_prompt(natural_query, intent)
        
        try:
            # Generate with Gemini (like calling wp_remote_get)
            response = self.model.generate_content(prompt)
            
            if not response.text:
                return "-- Error: No response from Gemini"
            
            sql_query = response.text.strip()
            
            # Clean up the response (like sanitizing form input)
            sql_query = re.sub(r'```sql\n?', '', sql_query)
            sql_query = re.sub(r'```\n?', '', sql_query)
            sql_query = sql_query.strip()
            
            return sql_query
            
        except Exception as e:
            return f"-- Error generating SQL: {str(e)}"
    
    def _build_generation_prompt(self, natural_query: str, intent: QueryIntent) -> str:
        """Build context-rich prompt - like preparing template data"""
        
        # Get relevant schema context
        schema_context = self._get_relevant_schema_context(intent.tables_mentioned)
        
        # Build the prompt (like building template variables)
        prompt = f"""You are an expert SQL query generator.

Rules:
1. Generate syntactically correct SQL queries
2. Use proper table and column names from the provided schema
3. Include appropriate JOINs when querying multiple tables
4. Always use safe, read-only queries for data retrieval
5. Return only the SQL query without explanations
6. Use standard SQL syntax compatible with multiple databases

Natural Language Query: "{natural_query}"

Database Schema Context:
{schema_context}

Requirements:
- Generate a {intent.query_type.value.upper()} query
- Use proper SQL syntax
- Include appropriate JOINs if needed
- Return only the SQL query, no explanations
- Ensure the query is safe and read-only if it's a SELECT

SQL Query:"""
        
        return prompt
    
    def _get_relevant_schema_context(self, mentioned_tables: List[str]) -> str:
        """Get schema context for mentioned tables - like getting post meta"""
        
        if not mentioned_tables:
            # Return a summary of all tables (like get_post_types())
            return self.schema.to_context_string(max_tables=10)
        
        # Build context for specific tables (like get_post_meta for specific posts)
        context_parts = []
        
        for table_name in mentioned_tables:
            table = self.schema.get_table(table_name)
            if table:
                context_parts.append(f"\nTable: {table.name}")
                for col in table.columns:
                    flags = []
                    if col.is_primary_key:
                        flags.append("PK")
                    if col.is_foreign_key:
                        flags.append(f"FK -> {col.foreign_key_table}")
                    
                    flag_str = f" ({', '.join(flags)})" if flags else ""
                    context_parts.append(f"  - {col.name}: {col.data_type}{flag_str}")
        
        return "\n".join(context_parts)
    
    def _validate_query_safety(self, sql_query: str) -> bool:
        """Validate query safety - like current_user_can() checks"""
        return is_read_only_query(sql_query)
    
    def _generate_warnings(self, sql_query: str, intent: QueryIntent) -> List[str]:
        """Generate warnings - like admin_notices"""
        warnings = []
        
        if not self._validate_query_safety(sql_query):
            warnings.append("⚠️ This query contains write operations and will be blocked")
        
        if intent.complexity_score > 7:
            warnings.append("⚠️ This is a complex query that may take longer to execute")
        
        if intent.requires_joins and len(intent.tables_mentioned) > 3:
            warnings.append("⚠️ Query involves multiple table joins - consider performance impact")
        
        return warnings
    
    def _explain_query(self, sql_query: str, natural_query: str) -> str:
        """Generate query explanation - like contextual help text"""
        
        try:
            explanation_prompt = f"""Explain this SQL query in simple terms:

Original request: {natural_query}

SQL Query:
{sql_query}

Provide a brief, clear explanation of what this query does."""

            response = self.model.generate_content(explanation_prompt)
            
            if response.text:
                return response.text.strip()
            else:
                return "Unable to generate explanation"
            
        except Exception as e:
            return f"Unable to generate explanation: {str(e)}"
    
    def _calculate_complexity(self, query: str, tables: List[str], requires_joins: bool) -> int:
        """Calculate query complexity score (1-10) - like post query performance"""
        score = 1
        
        # Base complexity
        score += len(tables)
        
        # Join complexity
        if requires_joins:
            score += 2
        
        # Aggregation complexity
        if any(word in query.lower() for word in ['sum', 'count', 'avg', 'group by', 'having']):
            score += 2
        
        # Subquery complexity
        if any(word in query.lower() for word in ['subquery', 'exists', 'in (select']):
            score += 3
        
        return min(score, 10)

    def _analyze_intent(self, query: str) -> QueryIntent:
        """Enhanced intent analysis with smarter table and column detection"""
        
        query_lower = query.lower()
        
        # Detect query type (existing logic)
        if any(word in query_lower for word in ['show', 'get', 'find', 'list', 'select', 'what', 'how many']):
            query_type = QueryType.SELECT
        elif any(word in query_lower for word in ['add', 'insert', 'create new']):
            query_type = QueryType.INSERT
        elif any(word in query_lower for word in ['update', 'change', 'modify']):
            query_type = QueryType.UPDATE
        elif any(word in query_lower for word in ['delete', 'remove']):
            query_type = QueryType.DELETE
        else:
            query_type = QueryType.UNKNOWN
        
        # Enhanced table detection with schema search
        tables_mentioned = []
        
        # Direct table name matching
        for table in self.schema.get_table_names():
            if table.lower() in query_lower:
                tables_mentioned.append(table)
        
        # Fuzzy matching for partial names
        if not tables_mentioned:
            search_results = self._search_schema_for_query(query_lower)
            tables_mentioned.extend(search_results['likely_tables'])
        
        # Enhanced column detection
        columns_mentioned = self._detect_mentioned_columns(query_lower, tables_mentioned)
        
        # Smart JOIN detection
        requires_joins = self._analyze_join_requirements(query_lower, tables_mentioned)
        
        # Enhanced complexity calculation
        complexity_score = self._calculate_enhanced_complexity(query, tables_mentioned, columns_mentioned, requires_joins)
        
        return QueryIntent(
            query_type=query_type,
            confidence=self._calculate_confidence(query_lower, tables_mentioned, columns_mentioned),
            tables_mentioned=tables_mentioned,
            columns_mentioned=columns_mentioned,
            requires_joins=requires_joins,
            complexity_score=complexity_score
        )

    def _search_schema_for_query(self, query_lower: str) -> Dict[str, List[str]]:
        """Search schema for relevant tables based on query content"""
        
        results = {
            'likely_tables': [],
            'possible_tables': []
        }
        
        # Business logic keywords to table mapping
        business_keywords = {
            'customer': ['customers', 'users', 'clients'],
            'order': ['orders', 'purchases', 'transactions'],
            'product': ['products', 'items', 'inventory'],
            'sale': ['orders', 'order_items', 'transactions'],
            'user': ['customers', 'users', 'accounts'],
            'purchase': ['orders', 'purchases', 'transactions'],
            'payment': ['payments', 'transactions', 'billing']
        }
        
        # Check for business context
        for keyword, potential_tables in business_keywords.items():
            if keyword in query_lower:
                for table in potential_tables:
                    if table in self.schema.get_table_names():
                        results['likely_tables'].append(table)
        
        # Remove duplicates
        results['likely_tables'] = list(set(results['likely_tables']))
        
        return results

    def _detect_mentioned_columns(self, query_lower: str, tables_mentioned: List[str]) -> List[str]:
        """Detect column names mentioned in natural language query"""
        
        columns_mentioned = []
        
        # Common column name patterns
        column_keywords = {
            'name': ['name', 'first_name', 'last_name', 'product_name'],
            'email': ['email', 'email_address'],
            'phone': ['phone', 'phone_number', 'telephone'],
            'price': ['price', 'cost', 'amount', 'total'],
            'date': ['date', 'created_at', 'updated_at', 'order_date'],
            'status': ['status', 'state', 'condition'],
            'quantity': ['quantity', 'qty', 'count']
        }
        
        # Search for column keywords in query
        for keyword, possible_columns in column_keywords.items():
            if keyword in query_lower:
                # Check if these columns exist in mentioned tables
                for table_name in tables_mentioned:
                    table = self.schema.get_table(table_name)
                    if table:
                        for col in table.columns:
                            if col.name.lower() in possible_columns:
                                columns_mentioned.append(f"{table_name}.{col.name}")
        
        return columns_mentioned

    def _analyze_join_requirements(self, query_lower: str, tables_mentioned: List[str]) -> bool:
        """Analyze if the query requires JOINs"""
        
        # Explicit JOIN keywords
        if any(word in query_lower for word in ['join', 'with', 'and', 'related', 'together']):
            return True
        
        # Multiple tables mentioned
        if len(tables_mentioned) > 1:
            return True
        
        # Relationship keywords
        relationship_words = ['customer orders', 'order items', 'product sales', 'user purchases']
        if any(phrase in query_lower for phrase in relationship_words):
            return True
        
        return False

    def _calculate_enhanced_complexity(self, query: str, tables: List[str], columns: List[str], requires_joins: bool) -> int:
        """Enhanced complexity calculation"""
        
        score = 1
        query_lower = query.lower()
        
        # Base complexity
        score += len(tables)
        score += len(columns) * 0.5
        
        # JOIN complexity
        if requires_joins:
            score += len(tables) * 2
        
        # Aggregation complexity
        agg_words = ['sum', 'count', 'avg', 'max', 'min', 'total', 'average', 'top', 'bottom']
        agg_count = sum(1 for word in agg_words if word in query_lower)
        score += agg_count * 2
        
        # Grouping complexity
        if any(word in query_lower for word in ['group', 'by', 'each', 'per']):
            score += 2
        
        # Sorting complexity
        if any(word in query_lower for word in ['top', 'bottom', 'best', 'worst', 'highest', 'lowest']):
            score += 1
        
        # Date/time complexity
        if any(word in query_lower for word in ['yesterday', 'today', 'last', 'this month', 'year']):
            score += 2
        
        return min(int(score), 10)

    def _calculate_confidence(self, query_lower: str, tables: List[str], columns: List[str]) -> float:
        """Calculate confidence score for intent analysis"""
        
        confidence = 0.5  # Base confidence
        
        # Boost confidence for clear table matches
        if tables:
            confidence += 0.2
        
        # Boost confidence for column matches
        if columns:
            confidence += 0.1
        
        # Boost confidence for clear SQL keywords
        sql_keywords = ['select', 'show', 'get', 'find', 'list']
        if any(keyword in query_lower for keyword in sql_keywords):
            confidence += 0.2
        
        return min(confidence, 1.0)

    def _build_generation_prompt(self, natural_query: str, intent: QueryIntent) -> str:
        """Enhanced prompt building with smart context"""
        
        # Get optimized schema context based on mentioned tables
        if intent.tables_mentioned:
            schema_context = self._get_focused_schema_context(intent.tables_mentioned)
        else:
            schema_context = self._get_general_schema_context()
        
        # Get JOIN suggestions if needed
        join_suggestions = []
        if intent.requires_joins and len(intent.tables_mentioned) > 1:
            # This would use the schema analyzer's suggest_joins method
            joins = self.schema_analyzer.suggest_joins(intent.tables_mentioned) if hasattr(self, 'schema_analyzer') else []
            join_suggestions = [f"Consider: {j['type']} {j['table2']} ON {j['condition']}" for j in joins[:2]]
        
        # Build enhanced prompt
        prompt = f"""You are an expert SQL query generator with deep database knowledge.

    Natural Language Query: "{natural_query}"

    Query Analysis:
    - Type: {intent.query_type.value.upper()}
    - Tables involved: {', '.join(intent.tables_mentioned) if intent.tables_mentioned else 'To be determined'}
    - Complexity: {intent.complexity_score}/10
    - Requires JOINs: {intent.requires_joins}

    Database Schema Context:
    {schema_context}

    {f"JOIN Suggestions:\\n" + chr(10).join(join_suggestions) if join_suggestions else ""}

    Requirements:
    - Generate a {intent.query_type.value.upper()} query
    - Use proper SQL syntax for the given schema
    - Include appropriate JOINs if needed
    - Return only the SQL query, no explanations
    - Ensure the query is safe and read-only for SELECT operations
    - Use table aliases for better readability when joining multiple tables

    SQL Query:"""
        
        return prompt

    def _get_focused_schema_context(self, mentioned_tables: List[str]) -> str:
        """Get detailed context for specific tables mentioned in query"""
        
        context_parts = []
        
        for table_name in mentioned_tables:
            table = self.schema.get_table(table_name)
            if table:
                context_parts.append(f"\nTable: {table.name}")
                
                # Add table description if available
                if table.description:
                    context_parts.append(f"  Purpose: {table.description}")
                
                # Add all columns with detailed info
                for col in table.columns:
                    flags = []
                    if col.is_primary_key:
                        flags.append("PRIMARY KEY")
                    if col.is_foreign_key:
                        flags.append(f"FOREIGN KEY → {col.foreign_key_table}.{col.foreign_key_column}")
                    if not col.is_nullable:
                        flags.append("NOT NULL")
                    
                    flag_str = f" ({', '.join(flags)})" if flags else ""
                    context_parts.append(f"  - {col.name}: {col.data_type}{flag_str}")
                
                # Add row count if available
                if table.row_count:
                    context_parts.append(f"  Approximate rows: {table.row_count:,}")
        
        # Add related tables that might be useful
        related_tables = []
        for table_name in mentioned_tables:
            # Get tables related to this one
            if hasattr(self, 'schema_analyzer'):
                related = self.schema_analyzer.get_related_tables(table_name)
                for rel_table in related:
                    if rel_table not in mentioned_tables and rel_table not in related_tables:
                        related_tables.append(rel_table)
        
        # Include context for related tables (abbreviated)
        if related_tables:
            context_parts.append(f"\nRelated Available Tables:")
            for table_name in related_tables[:3]:  # Limit to 3 related tables
                table = self.schema.get_table(table_name)
                if table:
                    key_columns = [c for c in table.columns if c.is_primary_key or c.is_foreign_key]
                    col_summary = ", ".join([f"{c.name}({c.data_type})" for c in key_columns[:3]])
                    context_parts.append(f"  - {table.name}: {col_summary}")
        
        return "\n".join(context_parts)

    def _get_general_schema_context(self) -> str:
        """Get general schema context when no specific tables are mentioned"""
        
        # Use the schema's built-in context method with optimization
        return self.schema.to_context_string(max_tables=8)
        
    def _generate_warnings(self, sql_query: str, intent: QueryIntent) -> List[str]:
        """Enhanced warning generation with performance and optimization hints"""
        warnings = []
        
        # Safety warnings
        if not self._validate_query_safety(sql_query):
            warnings.append("⚠️ This query contains write operations and will be blocked")
        
        # Complexity warnings
        if intent.complexity_score > 7:
            warnings.append("⚠️ Complex query detected - may impact performance")
        
        # JOIN warnings
        if intent.requires_joins:
            join_count = len(intent.tables_mentioned)
            if join_count > 3:
                warnings.append(f"⚠️ Multiple table JOINs ({join_count} tables) - consider performance impact")
            elif join_count == 2:
                warnings.append("💡 Tip: Ensure JOIN columns are indexed for better performance")
        
        # Query pattern warnings
        sql_upper = sql_query.upper()
        
        if 'SELECT *' in sql_upper:
            warnings.append("💡 Consider selecting specific columns instead of * for better performance")
        
        if 'ORDER BY' in sql_upper and 'LIMIT' not in sql_upper:
            warnings.append("💡 Consider adding LIMIT to ORDER BY queries to improve performance")
        
        if sql_upper.count('SELECT') > 1:  # Subqueries detected
            warnings.append("⚠️ Subqueries detected - consider JOIN alternatives for better performance")
        
        # Table size warnings (if we have row count data)
        large_tables = []
        for table_name in intent.tables_mentioned:
            table = self.schema.get_table(table_name)
            if table and table.row_count and table.row_count > 100000:
                large_tables.append(table_name)
        
        if large_tables:
            warnings.append(f"⚠️ Large tables detected: {', '.join(large_tables)} - consider adding WHERE clauses")
        
        return warnings

    def suggest_query_improvements(self, sql_query: str, intent: QueryIntent) -> List[str]:
        """Suggest improvements for the generated query"""
        
        suggestions = []
        sql_upper = sql_query.upper()
        
        # Index suggestions
        if intent.requires_joins:
            suggestions.append("Consider creating indexes on JOIN columns for better performance")
        
        # Query optimization suggestions
        if 'SELECT *' in sql_upper:
            suggestions.append("Replace SELECT * with specific column names to reduce data transfer")
        
        if 'ORDER BY' in sql_upper and 'LIMIT' not in sql_upper:
            suggestions.append("Add LIMIT clause to ORDER BY queries when you don't need all results")
        
        # Alternative approaches
        if len(intent.tables_mentioned) > 2:
            suggestions.append("For complex queries, consider breaking into smaller steps or using views")
        
        return suggestions

    def generate_query_alternatives(self, natural_query: str, intent: QueryIntent) -> List[str]:
        """Generate alternative ways to write the same query"""
        
        if not intent.tables_mentioned:
            return []
        
        alternatives = []
        
        # If it's a simple SELECT, suggest variations
        if intent.query_type == QueryType.SELECT and len(intent.tables_mentioned) == 1:
            table_name = intent.tables_mentioned[0]
            
            # Suggest different column selections
            alternatives.append(f"-- Alternative: Select specific columns\nSELECT column1, column2 FROM {table_name};")
            
            # Suggest with conditions
            alternatives.append(f"-- Alternative: Add filtering\nSELECT * FROM {table_name} WHERE condition = 'value';")
            
            # Suggest with ordering
            alternatives.append(f"-- Alternative: Add sorting\nSELECT * FROM {table_name} ORDER BY column_name;")
        
        # If it involves JOINs, suggest different JOIN types
        if intent.requires_joins and len(intent.tables_mentioned) >= 2:
            alternatives.append("-- Alternative: Use LEFT JOIN to include records with no matches")
            alternatives.append("-- Alternative: Use EXISTS instead of JOIN for existence checks")
        
        return alternatives

    def _explain_query(self, sql_query: str, natural_query: str) -> str:
        """Enhanced query explanation with performance insights"""
        
        try:
            # Enhanced explanation prompt
            explanation_prompt = f"""Explain this SQL query in simple, business-friendly terms:

    Original request: "{natural_query}"

    SQL Query:
    {sql_query}

    Please provide:
    1. What this query does in plain English
    2. Which tables it accesses and why
    3. Any JOINs and what they accomplish
    4. Performance considerations for this query

    Keep the explanation clear and practical."""

            response = self.model.generate_content(explanation_prompt)
            
            if response.text:
                return response.text.strip()
            else:
                # Fallback explanation
                return self._generate_fallback_explanation(sql_query, natural_query)
                
        except Exception as e:
            return self._generate_fallback_explanation(sql_query, natural_query)

    def _generate_fallback_explanation(self, sql_query: str, natural_query: str) -> str:
        """Generate a basic explanation when AI explanation fails"""
        
        explanation_parts = [f"This query responds to: '{natural_query}'"]
        
        sql_upper = sql_query.upper()
        
        # Determine operation type
        if sql_upper.startswith('SELECT'):
            explanation_parts.append("It retrieves data from the database.")
        elif sql_upper.startswith('INSERT'):
            explanation_parts.append("It adds new data to the database.")
        elif sql_upper.startswith('UPDATE'):
            explanation_parts.append("It modifies existing data in the database.")
        
        # Identify tables
        tables_in_query = []
        for table in self.schema.get_table_names():
            if table.upper() in sql_upper:
                tables_in_query.append(table)
        
        if tables_in_query:
            explanation_parts.append(f"Tables involved: {', '.join(tables_in_query)}")
        
        # Identify JOINs
        if 'JOIN' in sql_upper:
            explanation_parts.append("The query combines data from multiple tables using JOINs.")
        
        # Identify aggregations
        if any(func in sql_upper for func in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN']):
            explanation_parts.append("The query performs calculations on groups of data.")
        
        return " ".join(explanation_parts)