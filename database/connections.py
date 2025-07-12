import sqlite3
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from typing import Dict, List, Optional, Any
import pandas as pd
from cryptography.fernet import Fernet
import base64
import os
from .models import ConnectionConfig, DatabaseType
from config import DATABASE_ENCRYPTION_KEY, MAX_QUERY_EXECUTION_TIME, MAX_RESULT_ROWS

class DatabaseManager:
    def __init__(self):
        self.connections: Dict[str, sa.Engine] = {}
        self.active_connection: Optional[str] = None
        self.cipher = self._get_cipher()
    
    def _get_cipher(self) -> Optional[Fernet]:
        """Initialize encryption for connection strings"""
        if DATABASE_ENCRYPTION_KEY:
            try:
                # The key from .env is already properly formatted for Fernet
                # Don't double-encode it
                return Fernet(DATABASE_ENCRYPTION_KEY.encode())
            except Exception as e:
                print(f"Warning: Invalid encryption key format: {e}")
                print("Encryption will be disabled for connection strings")
                return None
        return None
    
    def add_connection(self, config: ConnectionConfig) -> bool:
        """Add a new database connection"""
        try:
            # Encrypt connection string if cipher is available
            connection_string = config.connection_string
            if self.cipher:
                connection_string = self.cipher.encrypt(connection_string.encode()).decode()
            
            engine = create_engine(
                config.connection_string,
                pool_timeout=MAX_QUERY_EXECUTION_TIME,
                pool_recycle=3600,
                echo=False
            )
            
            # Test connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self.connections[config.name] = engine
            if not self.active_connection:
                self.active_connection = config.name
            
            return True
            
        except Exception as e:
            print(f"Failed to add connection {config.name}: {str(e)}")
            return False
    
    def remove_connection(self, name: str) -> bool:
        """Remove a database connection"""
        if name in self.connections:
            self.connections[name].dispose()
            del self.connections[name]
            
            if self.active_connection == name:
                self.active_connection = next(iter(self.connections.keys()), None)
            
            return True
        return False
    
    def set_active_connection(self, name: str) -> bool:
        """Set the active database connection"""
        if name in self.connections:
            self.active_connection = name
            return True
        return False
    
    def get_active_engine(self) -> Optional[sa.Engine]:
        """Get the currently active database engine"""
        if self.active_connection and self.active_connection in self.connections:
            return self.connections[self.active_connection]
        return None
    
    def list_connections(self) -> List[str]:
        """List all available connection names"""
        return list(self.connections.keys())
    
    def test_connection(self, connection_string: str) -> tuple[bool, str]:
        """Test a database connection string"""
        try:
            engine = create_engine(connection_string)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            engine.dispose()
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """Execute a query and return results as DataFrame"""
        engine = self.get_active_engine()
        if not engine:
            raise ValueError("No active database connection")
        
        try:
            with engine.connect() as conn:
                # Set query timeout
                if 'sqlite' not in str(engine.url):
                    conn.execute(text(f"SET SESSION max_execution_time = {MAX_QUERY_EXECUTION_TIME * 1000}"))
                
                result = pd.read_sql(
                    text(query), 
                    conn, 
                    params=params or {}
                )
                
                # Limit result size
                if len(result) > MAX_RESULT_ROWS:
                    result = result.head(MAX_RESULT_ROWS)
                
                return result
                
        except Exception as e:
            raise SQLAlchemyError(f"Query execution failed: {str(e)}")
    
    def get_database_type(self) -> Optional[DatabaseType]:
        """Get the type of the active database"""
        engine = self.get_active_engine()
        if not engine:
            return None
        
        dialect_name = engine.dialect.name.lower()
        if 'sqlite' in dialect_name:
            return DatabaseType.SQLITE
        elif 'mysql' in dialect_name:
            return DatabaseType.MYSQL
        elif 'postgresql' in dialect_name:
            return DatabaseType.POSTGRESQL
        
        return None
    
    def create_sample_sqlite_db(self, file_path: str = "sample_data/sample.db") -> bool:
        """Create a sample SQLite database for testing"""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            conn = sqlite3.connect(file_path)
            cursor = conn.cursor()
            
            # Create sample tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS customers (
                    customer_id INTEGER PRIMARY KEY,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT UNIQUE,
                    phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY,
                    customer_id INTEGER,
                    order_date DATE,
                    total_amount DECIMAL(10,2),
                    status TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    product_id INTEGER PRIMARY KEY,
                    product_name TEXT NOT NULL,
                    category TEXT,
                    price DECIMAL(10,2),
                    stock_quantity INTEGER
                )
            ''')
            
            # Insert sample data
            customers_data = [
                (1, 'John', 'Doe', 'john@email.com', '555-0101'),
                (2, 'Jane', 'Smith', 'jane@email.com', '555-0102'),
                (3, 'Bob', 'Johnson', 'bob@email.com', '555-0103')
            ]
            
            cursor.executemany(
                'INSERT OR REPLACE INTO customers (customer_id, first_name, last_name, email, phone) VALUES (?, ?, ?, ?, ?)',
                customers_data
            )
            
            orders_data = [
                (1, 1, '2024-01-15', 99.99, 'completed'),
                (2, 2, '2024-01-16', 149.50, 'shipped'),
                (3, 1, '2024-01-17', 75.25, 'pending')
            ]
            
            cursor.executemany(
                'INSERT OR REPLACE INTO orders (order_id, customer_id, order_date, total_amount, status) VALUES (?, ?, ?, ?, ?)',
                orders_data
            )
            
            products_data = [
                (1, 'Laptop', 'Electronics', 999.99, 10),
                (2, 'Mouse', 'Electronics', 29.99, 50),
                (3, 'Keyboard', 'Electronics', 79.99, 25)
            ]
            
            cursor.executemany(
                'INSERT OR REPLACE INTO products (product_id, product_name, category, price, stock_quantity) VALUES (?, ?, ?, ?, ?)',
                products_data
            )
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Failed to create sample database: {str(e)}")
            return False