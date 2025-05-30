import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

MODEL_ID = os.getenv('MODEL_ID')
EMBEDDING_MODEL_ID = os.getenv('EMBEDDING_MODEL_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENSEARCH_HOST = os.getenv('OPENSEARCH_HOST')
OPENSEARCH_PORT = os.getenv('OPENSEARCH_PORT')
GPT_4O_MINI_MODEL_ID = os.getenv('GPT_4O_MINI_MODEL_ID')
PRODUCT_INDEX_NAME = "jeep_product"
KNOWLEDGE_INDEX_NAME = "jeep_knowledge"
VALKEY_HOST = os.getenv("VALKEY_HOST")
VALKEY_PORT = os.getenv("VALKEY_PORT")
VALKEY_PASSWORD = os.getenv("VALKEY_PASSWORD")
OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)