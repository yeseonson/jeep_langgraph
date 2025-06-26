import getpass
from datetime import datetime
import uuid

# 사용자 ID는 Linux 계정명 기반
def generate_user_id():
    return f"usr_{getpass.getuser()}"

# Thread ID는 시간 기준 + uuid로 고유성 확보
def generate_thread_id(user_id: str):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"thr_{user_id}_{timestamp}"

# Message ID는 Thread 내 유일성을 위해 microsecond까지 포함 + uuid 일부 사용
def generate_message_id(user_id: str):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    short_uuid = uuid.uuid4().hex[:6]
    return f"msg_{user_id}_{timestamp}{short_uuid}"
