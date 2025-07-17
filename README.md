# 🔍 AI-Powered SQL Query Builder

An intelligent natural language to SQL converter that transforms plain English questions into optimized database queries with real-time preview capabilities.

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.46.0-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production-brightgreen.svg)

## 🚀 Live Demo

**[https://database-manager.streamlit.app/](https://database-manager.streamlit.app/)**

## ✨ Features

### 🧠 AI-Powered Query Generation
- **Natural Language Processing**: Ask questions in plain English
- **Google Gemini Integration**: Advanced AI understanding of database schemas
- **Context-Aware**: Understands table relationships and business logic
- **Confidence Scoring**: AI indicates certainty level for generated queries

### 🔍 Real-Time Query Preview
- **Instant Results**: See query results before full execution
- **Smart Sampling**: Preview with intelligent row estimation
- **Performance Warnings**: Alerts for potentially expensive operations
- **Query Optimization**: Suggestions for better performance

### 🗄️ Multi-Database Support
- **SQLite**: File-based databases
- **MySQL**: Enterprise database support
- **PostgreSQL**: Advanced SQL features
- **Schema Analysis**: Automatic relationship detection

### 📊 Interactive Data Visualization
- **Automatic Charts**: Dynamic visualizations based on data types
- **Export Options**: CSV, JSON, and SQL downloads
- **Responsive Tables**: Sortable, filterable data grids
- **Query History**: Save and manage favorite queries

### 🔒 Security & Safety
- **Read-Only Enforcement**: Prevents destructive operations
- **SQL Injection Prevention**: Parameterized query validation
- **Connection Encryption**: Secure database credentials
- **Query Validation**: Syntax and safety checking

## 🛠️ Technology Stack

**Python, Streamlit, Google Gemini API, SQLAlchemy, Pandas, Plotly, OpenAI API, Python Dotenv, PyMySQL, Psycopg2, SQLParse, SQLGlot, Streamlit AgGrid, Streamlit Ace, Cryptography, Google Generative AI, Regular Expressions, Datetime, JSON, OS, Dataclasses, Enum, Typing, Collections, Schema Introspection, Foreign Key Analysis, Primary Key Detection, Table Relationship Mapping, Dynamic SQL Generation, Query Preview with LIMIT, COUNT Query Estimation, LEFT JOIN for Missing Data, INNER JOIN Optimization, Subquery Performance Analysis, GROUP BY Aggregation, ORDER BY with LIMIT, Window Functions Planning, Index Optimization Suggestions, Query Complexity Scoring, SQL Injection Prevention, Read-Only Query Enforcement, Multi-Database Dialect Support, Connection String Encryption, Query Result Caching, Database Connection Pooling**

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API key
- Database connection (SQLite, MySQL, or PostgreSQL)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/sql-query-builder.git
   cd sql-query-builder
    ```
2. **Create virtual environment** 
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
4. **Set up environment variabled**
    ```bash
    cp .env.example .env
    # Edit .env with your API keys
    ```
5. **Run the application**
    ```bash
    streamlit run app.py
    ```


### Environment Variables
Create a .env file in the project root:

    GOOGLE_API_KEY=your_gemini_api_key_here
    DATABASE_ENCRYPTION_KEY=your_encryption_key_here
    OPENAI_API_KEY=your_openai_key_here  # Optional fallback

## 📖 Usage Examples
Basic Queries

    "Show me all customers"
    → SELECT * FROM customers;

    "Find customers with their recent orders"
    → SELECT c.*, o.* FROM customers c 
    JOIN orders o ON c.customer_id = o.customer_id 
    WHERE o.order_date >= DATE('now', '-30 days');


Advanced Analytics

    "What are the top 5 products by sales?"
    → SELECT p.product_name, SUM(oi.quantity * p.price) as total_sales
    FROM products p
    JOIN order_items oi ON p.product_id = oi.product_id
    GROUP BY p.product_id, p.product_name
    ORDER BY total_sales DESC
    LIMIT 5;

Complex Business Logic

    "Show customers who haven't placed orders in the last 90 days"
    → SELECT c.* FROM customers c
    LEFT JOIN orders o ON c.customer_id = o.customer_id 
    AND o.order_date >= DATE('now', '-90 days')
    WHERE o.order_id IS NULL;

## 🏗️ Architecture
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   Streamlit UI  │    │  NL Processor    │    │ Database Layer  │
    │                 │    │                  │    │                 │
    │ • Query Input   │───▶│ • Intent Analysis│───▶│ • Schema Analyzer│
    │ • Results View  │    │ • SQL Generation │    │ • Query Executor│
    │ • Visualizations│    │ • Validation     │    │ • Multi-DB Support│
    └─────────────────┘    └──────────────────┘    └─────────────────┘
            │                       │                       │
            │                       │                       │
            ▼                       ▼                       ▼
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │ UI Components   │    │  Google Gemini   │    │ Database Engines│
    │                 │    │                  │    │                 │
    │ • Schema Explorer│    │ • LLM Processing │    │ • SQLite        │
    │ • Query Builder │    │ • Context Mgmt   │    │ • MySQL         │
    │ • Data Viz      │    │ • Safety Checks  │    │ • PostgreSQL    │
    └─────────────────┘    └──────────────────┘    └─────────────────┘

## 🔧 Configuration
### Database Connections

The application supports multiple database types:

    # SQLite
    connection_string = "sqlite:///path/to/database.db"
    # MySQL
    connection_string = "mysql+pymysql://user:password@host:port/database"
    # PostgreSQL
    connection_string = "postgresql+psycopg2://user:password@host:port/database"

## LLM Configuration

    # config.py
    LLM_PROVIDER = "gemini"  # or "openai"
    LLM_MODEL = "gemini-1.5-flash"
    LLM_TEMPERATURE = 0.1
    MAX_SCHEMA_TOKENS = 3000


## 📁 Project Structure
    sql-query-builder/
    ├── app.py                 # Main Streamlit application
    ├── config.py             # Configuration settings
    ├── requirements.txt      # Python dependencies
    ├── .env.example         # Environment variables template
    ├── database/            # Database management
    │   ├── connections.py   # Connection handling
    │   ├── models.py       # Data models
    │   └── schema_analyzer.py # Schema introspection
    ├── query_engine/        # AI query processing
    │   ├── nl_processor.py  # Natural language processing
    │   └── query_validator.py # Query validation
    ├── ui/                  # User interface components
    │   └── components.py    # Reusable UI elements
    └── utils/              # Utility functions
        └── helpers.py      # Helper functions

## Sample Queries for Testing
    test_queries = [
        "Show me all customers",
        "Find customers with their orders",
        "What are the top 5 products by sales?",
        "List customers who haven't ordered in 30 days",
        "Show monthly sales trends"
    ]

## 🚀 Deployment
    Streamlit Community Cloud
    Push to GitHub (public repository)
    Deploy to Streamlit Cloud: https://share.streamlit.io/
    Add environment variables in Streamlit secrets
    Configure custom domain via CNAME record

### Custom Domain Setup
Add CNAME record to your DNS:

    Type: CNAME
    Name: sql
    Value: your-app-name.streamlit.app

## 📄 License
    This project is licensed under the MIT License.

## 🙏 Acknowledgments
    Google Gemini for powering the natural language processing
    Streamlit for the excellent web framework
    SQLAlchemy for database abstraction
    Open source community for the amazing Python ecosystem
