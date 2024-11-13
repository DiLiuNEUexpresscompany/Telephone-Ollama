import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(
    name: str = "twilio_bot",
    log_level: int = logging.INFO,
    log_dir: str = "logs",
    max_size: int = 5 * 1024 * 1024,  # 5MB
    backup_count: int = 5
) -> logging.Logger:
    """
    设置应用程序日志记录器
    
    Args:
        name (str): 日志记录器名称
        log_level (int): 日志级别
        log_dir (str): 日志文件目录
        max_size (int): 单个日志文件最大大小（字节）
        backup_count (int): 保留的日志文件数量
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    try:
        # 创建日志目录
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # 创建日志记录器
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        
        # 如果已经配置了处理器，直接返回
        if logger.handlers:
            return logger
            
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        today = datetime.now().strftime('%Y-%m-%d')
        file_handler = RotatingFileHandler(
            filename=log_path / f"{name}_{today}.log",
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 错误日志单独记录
        error_handler = RotatingFileHandler(
            filename=log_path / f"{name}_error_{today}.log",
            maxBytes=max_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setFormatter(formatter)
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)
        
        logger.info("Logger initialized successfully")
        return logger
        
    except Exception as e:
        # 如果设置失败，确保至少有基本的控制台日志记录
        basic_logger = logging.getLogger(name)
        basic_logger.setLevel(logging.INFO)
        
        if not basic_logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            basic_logger.addHandler(console_handler)
            
        basic_logger.error(f"Failed to setup logger: {e}")
        return basic_logger

def get_logger(name: str = None) -> logging.Logger:
    """
    获取一个已配置的日志记录器
    
    Args:
        name (str): 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    if name is None:
        return logging.getLogger('twilio_bot')
    return logging.getLogger(f'twilio_bot.{name}')