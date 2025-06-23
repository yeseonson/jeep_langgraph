import json
from typing import List, Dict, Any

from jeepchat.config.config import JEEP_S3_BUCKET
from jeepchat.services.database import s3_client
from jeepchat.core.logger import logger


class S3ChatHistoryManager:
    def __init__(self):
        self.s3_client = s3_client()
        self.bucket = JEEP_S3_BUCKET

    def get_thread_messages(self, user_id: str, thread_id: str) -> List[Dict[str, Any]]:
        try:
            messages = []
            prefix = f"messages/{user_id}/{thread_id}/"
            response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
            if 'Contents' in response:
                objects = sorted(response['Contents'], key=lambda x: x['LastModified'])
                for obj in objects:
                    try:
                        res = self.s3_client.get_object(Bucket=self.bucket, Key=obj['Key'])
                        message_data = json.loads(res['Body'].read().decode('utf-8'))
                        messages.append(message_data)
                    except Exception as e:
                        logger.error(f"메시지 파일 읽기 실패: {obj['Key']}, 에러: {e}")
            return messages
        except Exception as e:
            logger.error(f"S3에서 thread 메시지 조회 실패: {e}")
            return []

    def get_user_threads(self, user_id: str) -> List[str]:
        try:
            threads = set()
            prefix = f"messages/{user_id}/"
            response = self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=prefix, Delimiter='/')
            if 'CommonPrefixes' in response:
                for prefix_info in response['CommonPrefixes']:
                    thread_path = prefix_info['Prefix']
                    thread_id = thread_path.split('/')[-2]
                    threads.add(thread_id)
            return sorted(list(threads))
        except Exception as e:
            logger.error(f"사용자 thread 목록 조회 실패: {e}")
            return []