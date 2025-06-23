import redis
import boto3
import json
from opensearchpy import OpenSearch
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jeepchat.config.config import OPENSEARCH_HOST, OPENSEARCH_PORT, VALKEY_HOST, VALKEY_PORT, VALKEY_PASSWORD, JEEP_S3_BUCKET
from jeepchat.core.logger import logger


def opensearch_client():
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

def valkey_client():
    logger.info("Attempting to connect to OpenSearch client: ")

    if not VALKEY_HOST or not VALKEY_PORT:
        raise ValueError("VALKEY_HOST and VALKEY_PORT must be set")

    try:
        client = redis.Redis(
            host=str(VALKEY_HOST), 
            port=int(VALKEY_PORT), 
            db=0, 
            password=VALKEY_PASSWORD
        )
        client.ping()
        logger.info("Successfully connected to Valkey client")
        return client
    
    except Exception as e:
        logger.error(f"Failed to connect to Valkey client: {e}")
        raise

def s3_client():
    if not JEEP_S3_BUCKET:
        raise ValueError("JEEP_S3_BUCKET must be set")
        
    try:
        client = boto3.client('s3')
        client.head_bucket(Bucket=JEEP_S3_BUCKET)
        logger.info(f"Bucket '{JEEP_S3_BUCKET}' exists and is accessible.")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to S3 client: {e}")
        raise

async def load_from_s3(session_id: str) -> Optional[Dict[str, Any]]:
    """S3에서 대화 로드"""
    try:
        client = s3_client()
        if not client:
            return None
            
        for days_back in range(7):
            date = datetime.now() - timedelta(days=days_back)
            s3_key = f"chat_archives/{date.year}/{date.month:02d}/{date.day:02d}/{session_id}.json"

            try:
                response = client.get_object(Bucket=JEEP_S3_BUCKET, key=s3_key)
                return json.loads(response['Body'].read().decode('utf-8'))
            except client.exceptions.NoSuchKey:
                continue
    except Exception as e:
        logger.error(f"S3 로드 실패: {e}")
        
    return None

def s3_client_put_object(data):
    try:
        client = boto3.client('s3')
        client.put_object(
            Bucket=JEEP_S3_BUCKET,
            Body=json.dumps(data.__dict__, ensure_ascii=False, indent=2),
            ContentType='application/json'
        )

    except Exception as e:
        logger.error(f"Failed to put object to S3: {e}")
