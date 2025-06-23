import logging
import os
from datetime import datetime

log_dir = "/usr/local/src/log"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"langgraph_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(filename=log_file, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)