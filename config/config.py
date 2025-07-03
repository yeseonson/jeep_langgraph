import os
from dotenv import load_dotenv
from openai import OpenAI
from langsmith.wrappers import wrap_openai

load_dotenv()

EMBEDDING_MODEL_ID = os.getenv('EMBEDDING_MODEL_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST')
OPENSEARCH_PORT = os.getenv('OPENSEARCH_PORT')
GPT_4O_MINI_MODEL_ID = os.getenv('GPT_4O_MINI_MODEL_ID')
QWEN3_4B_MODEL_ID = os.getenv('QWEN3_4B_MODEL_ID')
HYPERCLOVA_3B_MODEL_ID = os.getenv('HYPERCLOVA_3B_MODEL_ID')
PRODUCT_INDEX_NAME = "jeep_product"
KNOWLEDGE_INDEX_NAME = "jeep_knowledge"
REGULATION_INDEX_NAME = "tuning_regulation"
VALKEY_HOST = os.getenv("VALKEY_HOST")
VALKEY_PORT = os.getenv("VALKEY_PORT")
VALKEY_PASSWORD = os.getenv("VALKEY_PASSWORD")
OPENAI_CLIENT = wrap_openai(OpenAI(api_key=OPENAI_API_KEY))
JEEP_S3_BUCKET=os.getenv("JEEP_S3_BUCKET")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
NEO4J_URI=os.getenv("NEO4J_URI")
NEO4J_USERNAME=os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD=os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE="neo4j"
HF_HOME=os.environ['HF_HOME']