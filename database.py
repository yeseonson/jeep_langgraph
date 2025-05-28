from opensearchpy import OpenSearch
from config import OPENSEARCH_HOST, OPENSEARCH_PORT
from logger import logger

def opensearch_client() -> OpenSearch:
    logger.info(f"Attempting to connect to OpenSearch client: {OPENSEARCH_HOST}:{OPENSEARCH_PORT}")
    try:
        client = OpenSearch(
            hosts=[{'host': OPENSEARCH_HOST, 'port': OPENSEARCH_PORT}],
            use_ssl=False,
            verify_certs=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
            timeout=60
        )
        logger.info("Successfully connected to OpenSearch client")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to OpenSearch client: {e}")
        raise