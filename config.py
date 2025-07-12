import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration - Keep OpenAI for compatibility, add Gemini
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")

# Google Gemini Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = "gemini-1.5-flash"  # Fast and free model

# LLM Configuration - Update to use Gemini
LLM_PROVIDER = "gemini"  # Can be "openai" or "gemini"
LLM_MODEL = GEMINI_MODEL if LLM_PROVIDER == "gemini" else "gpt-4"
LLM_TEMPERATURE = 0.1
MAX_SCHEMA_TOKENS = 3000

# Database Configuration
SUPPORTED_DB_TYPES = ["sqlite", "mysql", "postgresql"]
MAX_QUERY_EXECUTION_TIME = 30  # seconds
MAX_RESULT_ROWS = 10000
DATABASE_ENCRYPTION_KEY = os.getenv("DATABASE_ENCRYPTION_KEY")

# UI Configuration
STREAMLIT_CONFIG = {
    "page_title": "SQL Query Builder",
    "page_icon": "🔍",
    "layout": "wide"
}

# Query Configuration
QUERY_HISTORY_LIMIT = 50
ENABLE_WRITE_OPERATIONS = False  # Safety first
DEFAULT_ROW_LIMIT = 100