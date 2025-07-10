"""
统一日志配置模块
"""
import os
import sys
import json
import logging
import logging.config
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger
from pythonjsonlogger import jsonlogger

from .config import settings


class StructuredFormatter(jsonlogger.JsonFormatter):
    """结构化日志格式化器"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # 添加标准字段
        log_record['timestamp'] = datetime.utcnow().isoformat()
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # 添加应用信息
        log_record['service'] = 'quant-platform-backend'
        log_record['version'] = getattr(settings, 'VERSION', '1.0.0')
        log_record['environment'] = getattr(settings, 'ENVIRONMENT', 'development')
        
        # 添加进程信息
        log_record['process_id'] = os.getpid()
        log_record['thread_id'] = record.thread
        
        # 处理异常信息
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)


class TradingLogFilter(logging.Filter):
    """交易相关日志过滤器"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # 为交易相关日志添加特殊标记
        if hasattr(record, 'order_id'):
            record.log_type = 'trading'
        elif hasattr(record, 'symbol'):
            record.log_type = 'market_data'
        elif hasattr(record, 'strategy_id'):
            record.log_type = 'strategy'
        else:
            record.log_type = 'system'
        
        return True


class LoggingConfig:
    """日志配置管理器"""
    
    def __init__(self):
        self.log_dir = Path(getattr(settings, 'LOG_DIR', 'logs'))
        self.log_level = getattr(settings, 'LOG_LEVEL', 'INFO')
        self.enable_json_logs = getattr(settings, 'ENABLE_JSON_LOGS', True)
        self.enable_file_logs = getattr(settings, 'ENABLE_FILE_LOGS', True)
        self.max_log_size = getattr(settings, 'MAX_LOG_SIZE', '100MB')
        self.backup_count = getattr(settings, 'LOG_BACKUP_COUNT', 10)
        
        # 创建日志目录
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def setup_logging(self):
        """设置日志系统"""
        # 清除现有配置
        logging.getLogger().handlers.clear()
        
        # 配置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # 添加处理器
        self._add_console_handler(root_logger)
        
        if self.enable_file_logs:
            self._add_file_handlers(root_logger)
        
        # 配置第三方库日志级别
        self._configure_third_party_loggers()
        
        # 设置loguru
        self._setup_loguru()
        
        logger.info("Logging system initialized", extra={
            'log_level': self.log_level,
            'log_dir': str(self.log_dir),
            'json_logs': self.enable_json_logs,
            'file_logs': self.enable_file_logs
        })
    
    def _add_console_handler(self, root_logger: logging.Logger):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.log_level)
        
        if self.enable_json_logs:
            formatter = StructuredFormatter(
                '%(timestamp)s %(level)s %(logger)s %(message)s'
            )
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        console_handler.setFormatter(formatter)
        console_handler.addFilter(TradingLogFilter())
        root_logger.addHandler(console_handler)
    
    def _add_file_handlers(self, root_logger: logging.Logger):
        """添加文件处理器"""
        from logging.handlers import RotatingFileHandler
        
        # 应用主日志
        app_handler = RotatingFileHandler(
            self.log_dir / 'app.log',
            maxBytes=self._parse_size(self.max_log_size),
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        app_handler.setLevel(self.log_level)
        
        # 交易日志
        trading_handler = RotatingFileHandler(
            self.log_dir / 'trading.log',
            maxBytes=self._parse_size(self.max_log_size),
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        trading_handler.setLevel(self.log_level)
        trading_handler.addFilter(lambda record: getattr(record, 'log_type', '') == 'trading')
        
        # 错误日志
        error_handler = RotatingFileHandler(
            self.log_dir / 'error.log',
            maxBytes=self._parse_size(self.max_log_size),
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        
        # 设置格式化器
        if self.enable_json_logs:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
        
        for handler in [app_handler, trading_handler, error_handler]:
            handler.setFormatter(formatter)
            handler.addFilter(TradingLogFilter())
            root_logger.addHandler(handler)
    
    def _configure_third_party_loggers(self):
        """配置第三方库日志级别"""
        third_party_loggers = {
            'uvicorn': 'INFO',
            'uvicorn.access': 'WARNING',
            'fastapi': 'INFO',
            'sqlalchemy': 'WARNING',
            'sqlalchemy.engine': 'WARNING',
            'alembic': 'INFO',
            'asyncio': 'WARNING',
            'websockets': 'INFO',
            'prometheus_client': 'WARNING'
        }
        
        for logger_name, level in third_party_loggers.items():
            logging.getLogger(logger_name).setLevel(level)
    
    def _setup_loguru(self):
        """设置loguru日志"""
        # 移除默认处理器
        logger.remove()
        
        # 控制台输出
        logger.add(
            sys.stdout,
            level=self.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        if self.enable_file_logs:
            # 文件输出
            logger.add(
                self.log_dir / 'loguru.log',
                level=self.log_level,
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
                rotation=self.max_log_size,
                retention=f"{self.backup_count} files",
                compression="zip",
                encoding="utf-8",
                backtrace=True,
                diagnose=True
            )
            
            # JSON格式日志
            if self.enable_json_logs:
                logger.add(
                    self.log_dir / 'structured.log',
                    level=self.log_level,
                    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
                    rotation=self.max_log_size,
                    retention=f"{self.backup_count} files",
                    serialize=True,
                    encoding="utf-8"
                )
    
    def _parse_size(self, size_str: str) -> int:
        """解析大小字符串"""
        size_str = size_str.upper()
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            return int(size_str)


# 全局日志配置实例
logging_config = LoggingConfig()


def setup_logging():
    """设置日志系统"""
    logging_config.setup_logging()


def get_logger(name: str) -> logging.Logger:
    """获取日志器"""
    return logging.getLogger(name)


def log_trading_event(event_type: str, data: Dict[str, Any], level: str = 'INFO'):
    """记录交易事件"""
    logger_instance = get_logger('trading')
    
    log_data = {
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        **data
    }
    
    getattr(logger_instance, level.lower())(
        f"Trading event: {event_type}",
        extra=log_data
    )


def log_market_data_event(symbol: str, event_type: str, data: Dict[str, Any]):
    """记录行情数据事件"""
    logger_instance = get_logger('market_data')
    
    log_data = {
        'symbol': symbol,
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        **data
    }
    
    logger_instance.info(
        f"Market data event: {symbol} - {event_type}",
        extra=log_data
    )


def log_strategy_event(strategy_id: str, event_type: str, data: Dict[str, Any]):
    """记录策略事件"""
    logger_instance = get_logger('strategy')
    
    log_data = {
        'strategy_id': strategy_id,
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        **data
    }
    
    logger_instance.info(
        f"Strategy event: {strategy_id} - {event_type}",
        extra=log_data
    )


def log_system_event(component: str, event_type: str, data: Dict[str, Any], level: str = 'INFO'):
    """记录系统事件"""
    logger_instance = get_logger('system')
    
    log_data = {
        'component': component,
        'event_type': event_type,
        'timestamp': datetime.utcnow().isoformat(),
        **data
    }
    
    getattr(logger_instance, level.lower())(
        f"System event: {component} - {event_type}",
        extra=log_data
    )
