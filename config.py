import os
from dotenv import load_dotenv

load_dotenv()

# API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY")

# URLs
WEAVIATE_URL = os.getenv("WEAVIATE_URL")
QDRANT_CLOUD_URL = os.getenv("QDRANT_CLOUD_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
REDIS_ENDPOINT = os.getenv("REDIS_ENDPOINT")
REDIS_HOST = REDIS_ENDPOINT[0: len(REDIS_ENDPOINT) - 6]
REDIS_PASS = os.getenv("REDIS_PASS")
REDIS_PORT = (REDIS_ENDPOINT[-5:])

# Chatwoot config
CHATWOOT_API_TOKEN = os.getenv("CHATWOOT_API_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")
INBOX_ID = os.getenv("INBOX_ID")
AGENT_ID = os.getenv("AGENT_ID")

# Collections
COLLECTION_NAMES = ["business_logic", "user_feedback"]

# Thresholds
TOP_K_RETRIEVAL = 3

# Model configs
OPENAI_CHAT_MODEL = "gpt-4o-mini"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"

# Vectorstore configs
WEAVIATE_CLASS_NAME = "ChatBot_769Audio"
WEAVIATE_TEXT_KEY = "text"

# Model tuning
OPENAI_TEMPERATURE = 0.5

# LangSmith tracking
LANGCHAIN_API_KEY = os.environ["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGSMITH_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "Sales Consulting ChatBot"


