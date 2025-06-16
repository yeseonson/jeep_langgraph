import uuid
from datetime import datetime

uuid_hex = uuid.uuid4().hex[:8]

def generate_user_id():
    return f"usr_{uuid_hex}"

def generate_thread_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"thr_{uuid_hex}_{timestamp}"

def generate_message_id():
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"msg_{uuid_hex}_{timestamp}"