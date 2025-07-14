import json
from typing import List, Dict, Any
from jeepchat.config.config import JEEP_S3_BUCKET
from jeepchat.services.database import s3_client
from jeepchat.logger import logger


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

                messages.sort(key=lambda x: x.get('timestamp', ''))
            return messages
        
        except Exception as e:
            logger.error(f"S3에서 thread 메시지 조회 실패: {e}")
            return []

    def get_user_threads(self, user_id: str, limit: int = 20) -> List[str]:
        try:
            thread_last_modified = {}
            prefix = f"messages/{user_id}/"
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=self.bucket, Prefix=prefix)

            for page in page_iterator:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    parts = obj['Key'].split('/')
                    if len(parts) < 4:
                        continue

                    thread_id = parts[2]
                    last_modified = obj['LastModified']

                    # 최신 메시지를 기준으로 thread 갱신
                    if thread_id not in thread_last_modified or thread_last_modified[thread_id] < last_modified:
                        thread_last_modified[thread_id] = last_modified

            # 최신순으로 정렬 후 thread_id만 추출
            sorted_threads = sorted(thread_last_modified.items(), key=lambda x: x[1], reverse=True)
            return [tid for tid, _ in sorted_threads[:limit]]

        except Exception as e:
            logger.error(f"사용자 thread 목록 조회 실패: {e}")
            return []
