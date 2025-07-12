from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from enum import Enum

class DatabaseType(Enum):
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"

@dataclass
class ColumnInfo:
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool
    is_foreign_key: bool
    foreign_key_table: Optional[str] = None
    foreign_key_column: Optional[str] = None
    default_value: Optional[Any] = None
    max_length: Optional[int] = None
    description: Optional[str] = None

@dataclass
class TableInfo:
    name: str
    columns: List[ColumnInfo]
    row_count: Optional[int] = None
    description: Optional[str] = None
    
    def get_column(self, name: str) -> Optional[ColumnInfo]:
        return next((col for col in self.columns if col.name == name), None)
    
    def get_primary_keys(self) -> List[ColumnInfo]:
        return [col for col in self.columns if col.is_primary_key]
    
    def get_foreign_keys(self) -> List[ColumnInfo]:
        return [col for col in self.columns if col.is_foreign_key]

@dataclass
class DatabaseSchema:
    database_name: str
    database_type: DatabaseType
    tables: List[TableInfo]
    connection_string: str
    
    def get_table(self, name: str) -> Optional[TableInfo]:
        return next((table for table in self.tables if table.name == name), None)
    
    def get_table_names(self) -> List[str]:
        return [table.name for table in self.tables]
    
    def to_context_string(self, max_tables: int = 20) -> str:
        """Convert schema to string format for LLM context"""
        context_parts = [f"Database: {self.database_name} ({self.database_type.value})"]
        
        tables_to_include = self.tables[:max_tables]
        for table in tables_to_include:
            context_parts.append(f"\nTable: {table.name}")
            for col in table.columns:
                col_info = f"  - {col.name}: {col.data_type}"
                if col.is_primary_key:
                    col_info += " (PK)"
                if col.is_foreign_key:
                    col_info += f" (FK -> {col.foreign_key_table}.{col.foreign_key_column})"
                if not col.is_nullable:
                    col_info += " (NOT NULL)"
                context_parts.append(col_info)
        
        if len(self.tables) > max_tables:
            context_parts.append(f"\n... and {len(self.tables) - max_tables} more tables")
        
        return "\n".join(context_parts)

@dataclass
class ConnectionConfig:
    name: str
    database_type: DatabaseType
    connection_string: str
    db_type: str
    description: Optional[str] = None
    is_active: bool = True