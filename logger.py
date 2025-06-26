import logging
import os
from datetime import datetime

def get_logger(name: str = "jeepchat") -> logging.Logger:
    # 로그 디렉토리 및 파일 경로 설정
    log_dir = "/usr/local/src/log"
    os.makedirs(log_dir, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"langgraph_{date_str}.log")

    # 로그 레벨: 환경 변수 또는 기본값 DEBUG
    log_level_str = os.getenv("LOG_LEVEL", "DEBUG").upper()
    log_level = getattr(logging, log_level_str, logging.DEBUG)

    # 로거 생성
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # 중복 핸들러 방지
    if not logger.handlers:
        # 파일 핸들러
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)  # 무조건 DEBUG까지 저장
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        ))

        # 콘솔 핸들러
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)  # 환경에 따라 조절
        console_handler.setFormatter(logging.Formatter(
            "[%(levelname)s] %(message)s"
        ))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

logger = get_logger()
