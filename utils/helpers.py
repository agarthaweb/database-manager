import re
import sqlparse
from typing import List, Dict, Any, Optional

def format_sql(query: str) -> str:
    """Format SQL query for better readability"""
    try:
        return sqlparse.format(
            query, 
            reindent=True, 
            keyword_case='upper',
            identifier_case='lower',
            strip_comments=False
        )
    except:
        return query

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis if too long"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def safe_execute(func, default_value=None, *args, **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Error in {func.__name__}: {str(e)}")
        return default_value

def is_read_only_query(query: str) -> bool:
    """Check if query is read-only (SELECT only)"""
    query_clean = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)
    query_clean = query_clean.strip().upper()
    
    dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'REPLACE']
    
    for keyword in dangerous_keywords:
        if keyword in query_clean:
            return False
    
    return query_clean.startswith('SELECT') or query_clean.startswith('WITH')

def extract_table_names(query: str) -> List[str]:
    """Extract table names from SQL query"""
    try:
        parsed = sqlparse.parse(query)[0]
        tables = []
        
        def extract_from_token(token):
            if token.ttype is sqlparse.tokens.Name:
                tables.append(str(token))
            elif hasattr(token, 'tokens'):
                for sub_token in token.tokens:
                    extract_from_token(sub_token)
        
        extract_from_token(parsed)
        return list(set(tables))
    except:
        return []

def estimate_query_complexity(query: str) -> Dict[str, Any]:
    """Estimate query complexity for performance warnings"""
    complexity = {
        'score': 0,
        'factors': [],
        'warnings': []
    }
    
    query_upper = query.upper()
    
    # Count JOINs
    join_count = query_upper.count('JOIN')
    complexity['score'] += join_count * 2
    if join_count > 0:
        complexity['factors'].append(f"{join_count} JOIN(s)")
    
    # Count subqueries
    subquery_count = query_upper.count('SELECT') - 1  # Subtract main SELECT
    complexity['score'] += subquery_count * 3
    if subquery_count > 0:
        complexity['factors'].append(f"{subquery_count} subquery(s)")
    
    # Check for aggregations
    agg_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP BY']
    for func in agg_functions:
        if func in query_upper:
            complexity['score'] += 1
            complexity['factors'].append(f"Aggregation ({func})")
            break
    
    # Generate warnings
    if complexity['score'] > 10:
        complexity['warnings'].append("High complexity query - may be slow")
    elif complexity['score'] > 5:
        complexity['warnings'].append("Medium complexity query")
    
    return complexity

def validate_table_names(query: str, available_tables: List[str]) -> Dict[str, Any]:
    """Validate that table names in query exist in schema"""
    extracted_tables = extract_table_names(query)
    available_lower = [t.lower() for t in available_tables]
    
    validation = {
        'valid_tables': [],
        'invalid_tables': [],
        'errors': [],
        'warnings': []
    }
    
    for table in extracted_tables:
        if table.lower() in available_lower:
            validation['valid_tables'].append(table)
        else:
            validation['invalid_tables'].append(table)
            validation['errors'].append(f"Table '{table}' does not exist in schema")
            
            # Simple similarity matching for suggestions
            suggestions = [t for t in available_tables if table.lower() in t.lower()]
            if suggestions:
                validation['warnings'].append(f"Did you mean: {', '.join(suggestions[:3])}?")
    
    return validation

def extract_from_token(token):
    """Extract table names from SQL tokens"""
    if token.ttype is None:
        for sub_token in token.tokens:
            yield from extract_from_token(sub_token)
    elif token.ttype is sqlparse.tokens.Name:
        yield str(token)

def estimate_query_complexity(query: str) -> Dict[str, Any]:
    """Estimate query complexity for performance warnings"""
    complexity = {
        'score': 1,
        'factors': [],
        'warnings': []
    }
    
    query_upper = query.upper()
    
    # Count JOINs
    join_count = query_upper.count('JOIN')
    if join_count > 0:
        complexity['score'] += join_count * 2
        complexity['factors'].append(f"{join_count} JOIN operations")
    
    # Count subqueries
    subquery_count = query_upper.count('SELECT') - 1  # Subtract main SELECT
    if subquery_count > 0:
        complexity['score'] += subquery_count * 3
        complexity['factors'].append(f"{subquery_count} subqueries")
    
    # Check for aggregations
    agg_functions = ['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUP BY']
    agg_count = sum(1 for func in agg_functions if func in query_upper)
    if agg_count > 0:
        complexity['score'] += agg_count
        complexity['factors'].append(f"{agg_count} aggregation functions")
    
    # Generate warnings
    if complexity['score'] > 7:
        complexity['warnings'].append("High complexity query - may impact performance")
    if join_count > 3:
        complexity['warnings'].append("Multiple JOINs detected - consider query optimization")
    
    return complexity