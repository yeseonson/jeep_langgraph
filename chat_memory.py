import json
from typing import Dict, Any, List, Optional, cast
from datetime import datetime
import boto3
from database import valkey_client
from generate_id import generate_message_id
from config import JEEP_S3_BUCKET
from logger import logger

class ChatMemoryManager:
    def __init__(self):
        self.valkey = valkey_client()
        self.default_ttl = 3600
        self.s3_client = boto3.client('s3')
        self.bucket = JEEP_S3_BUCKET

    def _get_thread_key(self, user_id: str, thread_id: str) -> str:
        return f"{user_id}:{thread_id}"

    def _backup_to_s3(self, user_id: str, thread_id: str, message_id: str, message: dict) -> None:
        """메시지를 S3에 백업"""
        try:
            # S3에 저장할 데이터 구조
            backup_data = {
                'user_id': user_id,
                'thread_id': thread_id,
                'message_id': message_id,
                'message': message,
                'timestamp': datetime.now().isoformat()
            }

            logger.info(f"backup data: {backup_data}")
            
            s3_key = f"messages/{user_id}/{thread_id}/{message_id}.json"
            
            # S3에 업로드
            self.s3_client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=json.dumps(backup_data, ensure_ascii=False),
                ContentType='application/json'
            )
        except Exception as e:
            logger.error(f"[ERROR] S3 백업 실패: {e}")

    def save_message(self, user_id: str, thread_id: str, message_id: str, message: dict) -> None:
        """개별 메시지 저장 및 thread에 메시지 id 추가"""
        try:
            message_id = generate_message_id()

            # 메시지 내용 저장
            self.valkey.setex(
                message_id,
                self.default_ttl,
                json.dumps(message, ensure_ascii=False)
            )
            
            # thread에 메시지 id 추가
            thread_key = self._get_thread_key(user_id, thread_id)
            self.valkey.rpush(thread_key, message_id)
            self.valkey.expire(thread_key, self.default_ttl)
            
            # S3에 백업
            self._backup_to_s3(user_id, thread_id, message_id, message)
        
        except Exception as e:
            logger.error(f"[ERROR] Redis 저장 실패: {e}")

    def get_thread_messages(self, user_id: str, thread_id: str) -> List[Dict[str, Any]]:
        """thread의 모든 메시지 조회"""
        try:
            message_ids = cast(List[bytes], self.valkey.lrange(self._get_thread_key(user_id, thread_id), 0, -1))
            messages = []
            for mid in message_ids:
                data = self.valkey.get(mid)
                if data:
                    messages.append(json.loads(cast(bytes, data).decode('utf-8')))
            return messages
        except Exception as e:
            logger.error(f"[ERROR] Redis 조회 실패: {e}")
            return []

    def save_context(self, user_id: str, thread_id: str, context_key: str, context_value: Any) -> None:
        """컨텍스트 항목 저장"""
        message = {
            "context": {context_key: context_value},
            "timestamp": datetime.now().isoformat()
        }
        message_id = generate_message_id()
        self.save_message(user_id, thread_id, message_id, message)

    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """개별 메시지 조회"""
        try:
            data = self.valkey.get(message_id)
            if data:
                return json.loads(cast(bytes, data).decode('utf-8'))
            return None
        except Exception as e:
            logger.error(f"[ERROR] 메시지 조회 실패: {e}")
            return None