"""
通用辅助函数模块
提供ID生成、时间处理、数据转换等通用功能
"""
import uuid
import hashlib
import secrets
import json
import base64
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal
import asyncio
import functools
import logging
from pathlib import Path
import gzip
import pickle


# ==================== ID生成工具 ====================

def generate_uuid() -> uuid.UUID:
    """
    生成UUID对象
    
    Returns:
        UUID对象
    """
    return uuid.uuid4()


def generate_short_id(length: int = 8) -> str:
    """
    生成短ID
    
    Args:
        length: ID长度
        
    Returns:
        短ID字符串
    """
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_order_id() -> str:
    """
    生成订单ID
    
    Returns:
        订单ID（格式：ORD + 时间戳 + 随机数）
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = generate_short_id(4)
    return f"ORD{timestamp}{random_part}"


def generate_strategy_id() -> str:
    """
    生成策略ID
    
    Returns:
        策略ID（格式：STR + 时间戳 + 随机数）
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = generate_short_id(4)
    return f"STR{timestamp}{random_part}"


def generate_backtest_id() -> str:
    """
    生成回测ID
    
    Returns:
        回测ID（格式：BT + 时间戳 + 随机数）
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = generate_short_id(4)
    return f"BT{timestamp}{random_part}"


def generate_hash(data: str, algorithm: str = "md5") -> str:
    """
    生成数据哈希值
    
    Args:
        data: 要哈希的数据
        algorithm: 哈希算法（md5, sha1, sha256）
        
    Returns:
        哈希值字符串
    """
    if algorithm == "md5":
        return hashlib.md5(data.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(data.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(data.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


# ==================== 时间处理工具 ====================

def now() -> datetime:
    """
    获取当前时间（带时区）
    
    Returns:
        当前时间
    """
    return datetime.now(timezone.utc)


def today() -> date:
    """
    获取今天日期
    
    Returns:
        今天日期
    """
    return date.today()


def is_trading_day(target_date: date) -> bool:
    """
    判断是否为交易日（简单版本，排除周末）
    
    Args:
        target_date: 目标日期
        
    Returns:
        是否为交易日
    """
    # 周一到周五为交易日（这里简化处理，实际应该考虑节假日）
    return target_date.weekday() < 5


def get_trading_days_between(start_date: date, end_date: date) -> List[date]:
    """
    获取两个日期之间的所有交易日
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        交易日列表
    """
    trading_days = []
    current_date = start_date
    
    while current_date <= end_date:
        if is_trading_day(current_date):
            trading_days.append(current_date)
        current_date += timedelta(days=1)
    
    return trading_days


def get_market_open_time(target_date: date) -> datetime:
    """
    获取指定日期的市场开盘时间
    
    Args:
        target_date: 目标日期
        
    Returns:
        开盘时间
    """
    return datetime.combine(target_date, time(9, 30))


def get_market_close_time(target_date: date) -> datetime:
    """
    获取指定日期的市场收盘时间
    
    Args:
        target_date: 目标日期
        
    Returns:
        收盘时间
    """
    return datetime.combine(target_date, time(15, 0))


def is_market_open(dt: Optional[datetime] = None) -> bool:
    """
    判断当前是否为交易时间
    
    Args:
        dt: 指定时间（默认为当前时间）
        
    Returns:
        是否为交易时间
    """
    if dt is None:
        dt = datetime.now()
    
    # 检查是否为交易日
    if not is_trading_day(dt.date()):
        return False
    
    # 检查是否在交易时间内
    current_time = dt.time()
    
    # 上午交易时间：9:30-11:30
    morning_start = time(9, 30)
    morning_end = time(11, 30)
    
    # 下午交易时间：13:00-15:00
    afternoon_start = time(13, 0)
    afternoon_end = time(15, 0)
    
    return (morning_start <= current_time <= morning_end) or \
           (afternoon_start <= current_time <= afternoon_end)


def parse_datetime(dt_str: str, fmt: Optional[str] = None) -> Optional[datetime]:
    """
    解析日期时间字符串
    
    Args:
        dt_str: 日期时间字符串
        fmt: 格式化模板
        
    Returns:
        解析后的日期时间对象
    """
    if not dt_str:
        return None
    
    try:
        if fmt:
            return datetime.strptime(dt_str, fmt)
        else:
            # 尝试常见格式
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%d",
                "%Y/%m/%d %H:%M:%S",
                "%Y/%m/%d",
                "%Y%m%d",
                "%Y%m%d%H%M%S"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(dt_str, fmt)
                except ValueError:
                    continue
            
            # 尝试ISO格式
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        return None


# ==================== 数据转换工具 ====================

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    安全转换为浮点数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        转换后的浮点数
    """
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """
    安全转换为整数
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        转换后的整数
    """
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_decimal(value: Any, default: Decimal = Decimal('0')) -> Decimal:
    """
    安全转换为Decimal
    
    Args:
        value: 要转换的值
        default: 默认值
        
    Returns:
        转换后的Decimal
    """
    try:
        return Decimal(str(value)) if value is not None else default
    except (ValueError, TypeError):
        return default


def dict_to_obj(data: Dict[str, Any]) -> object:
    """
    将字典转换为对象
    
    Args:
        data: 字典数据
        
    Returns:
        对象
    """
    class DictObj:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    return DictObj(**data)


def obj_to_dict(obj: object, exclude_private: bool = True) -> Dict[str, Any]:
    """
    将对象转换为字典
    
    Args:
        obj: 对象
        exclude_private: 是否排除私有属性
        
    Returns:
        字典
    """
    result = {}
    
    for key, value in obj.__dict__.items():
        if exclude_private and key.startswith('_'):
            continue
        
        if isinstance(value, (str, int, float, bool, type(None))):
            result[key] = value
        elif isinstance(value, (datetime, date)):
            result[key] = value.isoformat()
        elif isinstance(value, Decimal):
            result[key] = float(value)
        else:
            result[key] = str(value)
    
    return result


def flatten_dict(data: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
    """
    扁平化字典
    
    Args:
        data: 嵌套字典
        separator: 分隔符
        
    Returns:
        扁平化后的字典
    """
    def _flatten(obj: Any, parent_key: str = '') -> Dict[str, Any]:
        items = []
        
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_key = f"{parent_key}{separator}{key}" if parent_key else key
                items.extend(_flatten(value, new_key).items())
        else:
            return {parent_key: obj}
        
        return dict(items)
    
    return _flatten(data)


# ==================== 文件处理工具 ====================

def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在
    
    Args:
        path: 目录路径
        
    Returns:
        Path对象
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def read_json_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    读取JSON文件
    
    Args:
        file_path: 文件路径
        
    Returns:
        JSON数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def write_json_file(data: Dict[str, Any], file_path: Union[str, Path]) -> bool:
    """
    写入JSON文件
    
    Args:
        data: 要写入的数据
        file_path: 文件路径
        
    Returns:
        是否成功
    """
    try:
        ensure_dir(Path(file_path).parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def compress_data(data: bytes) -> bytes:
    """
    压缩数据
    
    Args:
        data: 原始数据
        
    Returns:
        压缩后的数据
    """
    return gzip.compress(data)


def decompress_data(compressed_data: bytes) -> bytes:
    """
    解压缩数据
    
    Args:
        compressed_data: 压缩的数据
        
    Returns:
        解压后的数据
    """
    return gzip.decompress(compressed_data)


def serialize_object(obj: Any) -> bytes:
    """
    序列化对象
    
    Args:
        obj: 要序列化的对象
        
    Returns:
        序列化后的字节数据
    """
    return pickle.dumps(obj)


def deserialize_object(data: bytes) -> Any:
    """
    反序列化对象
    
    Args:
        data: 序列化的字节数据
        
    Returns:
        反序列化后的对象
    """
    return pickle.loads(data)


# ==================== 编码解码工具 ====================

def encode_base64(data: Union[str, bytes]) -> str:
    """
    Base64编码
    
    Args:
        data: 要编码的数据
        
    Returns:
        Base64编码字符串
    """
    if isinstance(data, str):
        data = data.encode('utf-8')
    return base64.b64encode(data).decode('ascii')


def decode_base64(encoded_data: str) -> bytes:
    """
    Base64解码
    
    Args:
        encoded_data: Base64编码的字符串
        
    Returns:
        解码后的字节数据
    """
    return base64.b64decode(encoded_data)


# ==================== 异步工具 ====================

def run_sync(coro):
    """
    在同步环境中运行异步函数
    
    Args:
        coro: 协程对象
        
    Returns:
        协程执行结果
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


def async_retry(max_attempts: int = 3, delay: float = 1.0):
    """
    异步重试装饰器
    
    Args:
        max_attempts: 最大重试次数
        delay: 重试延迟时间
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
                    else:
                        raise last_exception
            
            raise last_exception
        
        return wrapper
    return decorator


# ==================== 缓存工具 ====================

def memoize(maxsize: int = 128):
    """
    内存缓存装饰器
    
    Args:
        maxsize: 最大缓存条目数
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable):
        return functools.lru_cache(maxsize=maxsize)(func)
    return decorator


# ==================== 日志工具 ====================

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        日志记录器
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
    
    return logger


# ==================== 分页工具 ====================

def paginate_list(items: List[Any], page: int, page_size: int) -> Dict[str, Any]:
    """
    对列表进行分页
    
    Args:
        items: 要分页的列表
        page: 页码（从1开始）
        page_size: 每页数量
        
    Returns:
        分页结果
    """
    total = len(items)
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    
    page_items = items[start_index:end_index]
    
    return {
        "items": page_items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
        "has_next": end_index < total,
        "has_prev": page > 1
    }


# ==================== 性能监控工具 ====================

def timing(func: Callable):
    """
    函数执行时间监控装饰器
    
    Args:
        func: 要监控的函数
        
    Returns:
        装饰器函数
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger = get_logger(f"timing.{func.__name__}")
            logger.info(f"Function {func.__name__} took {duration:.4f} seconds")
    
    return wrapper


def async_timing(func: Callable):
    """
    异步函数执行时间监控装饰器
    
    Args:
        func: 要监控的异步函数
        
    Returns:
        装饰器函数
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger = get_logger(f"timing.{func.__name__}")
            logger.info(f"Async function {func.__name__} took {duration:.4f} seconds")
    
    return wrapper


# ==================== 数据校验工具 ====================

def is_valid_json(json_str: str) -> bool:
    """
    检查字符串是否为有效的JSON
    
    Args:
        json_str: JSON字符串
        
    Returns:
        是否有效
    """
    try:
        json.loads(json_str)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def deep_merge_dict(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度合并字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        
    Returns:
        合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    将列表分块
    
    Args:
        items: 要分块的列表
        chunk_size: 每块大小
        
    Returns:
        分块后的列表
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def remove_duplicates(items: List[Any], key_func: Optional[Callable] = None) -> List[Any]:
    """
    移除列表中的重复项
    
    Args:
        items: 原始列表
        key_func: 用于比较的键函数
        
    Returns:
        去重后的列表
    """
    if key_func is None:
        return list(dict.fromkeys(items))
    else:
        seen = set()
        result = []
        for item in items:
            key = key_func(item)
            if key not in seen:
                seen.add(key)
                result.append(item)
        return result