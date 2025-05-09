import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# 創建日誌目錄
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# 日誌格式
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_logger(name: str, log_file: str = None, level=logging.INFO):
    """
    設置日誌記錄器
    
    Args:
        name: 日誌記錄器名稱
        log_file: 日誌文件名（可選）
        level: 日誌級別
    
    Returns:
        logging.Logger: 配置好的日誌記錄器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清除現有的處理器
    logger.handlers.clear()
    
    # 控制台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # 文件處理器（如果指定了日誌文件）
    if log_file:
        file_handler = RotatingFileHandler(
            log_dir / log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(log_format)
        logger.addHandler(file_handler)
    
    return logger 