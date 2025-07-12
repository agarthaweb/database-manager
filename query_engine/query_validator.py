from typing import List, Dict, Any
import sqlparse
from database.models import DatabaseSchema
from utils.helpers import is_read_only_query, extract_table_names, validate_table_names, estimate_query_complexity

class QueryValidator:
    def __init__(self, schema: DatabaseSchema):
        self.schema = schema
    
    def validate_query(self, sql_query: str) -> Dict[str, Any]:
        """Comprehensive query validation"""
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'safety_check': True,
            'table_validation': {},
            'syntax_check': True,
            'complexity_analysis': {}
        }
        
        # 1. Syntax validation
        syntax_result = self._validate_syntax(sql_query)
        validation_result['syntax_check'] = syntax_result['is_valid']
        validation_result['errors'].extend(syntax_result['errors'])
        
        # 2. Safety validation
        if not is_read_only_query(sql_query):
            validation_result['safety_check'] = False
            validation_result['errors'].append("Write operations are not allowed")
        
        # 3. Table validation
        table_validation = validate_table_names(sql_query, self.schema.get_table_names())
        validation_result['table_validation'] = table_validation
        validation_result['errors'].extend(table_validation['errors'])
        validation_result['warnings'].extend(table_validation['warnings'])
        
        # 4. Complexity analysis
        complexity_analysis = estimate_query_complexity(sql_query)
        validation_result['complexity_analysis'] = complexity_analysis
        validation_result['warnings'].extend(complexity_analysis['warnings'])
        
        # 5. Overall validity
        validation_result['is_valid'] = (
            validation_result['syntax_check'] and 
            validation_result['safety_check'] and 
            len(validation_result['errors']) == 0
        )
        
        return validation_result
    
    def _validate_syntax(self, sql_query: str) -> Dict[str, Any]:
        """Validate SQL syntax"""
        try:
            parsed = sqlparse.parse(sql_query)
            if not parsed:
                return {
                    'is_valid': False,
                    'errors': ['Invalid SQL syntax']
                }
            
            # Check for basic SQL structure
            if not any(token.ttype is sqlparse.tokens.Keyword for token in parsed[0].tokens):
                return {
                    'is_valid': False,
                    'errors': ['Query must contain SQL keywords']
                }
            
            return {
                'is_valid': True,
                'errors': []
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f'Syntax error: {str(e)}']
            }