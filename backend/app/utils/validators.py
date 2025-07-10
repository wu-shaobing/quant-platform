"""
业务数据验证工具模块
提供订单参数、用户输入、金融数据等验证功能
"""
import re
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from datetime import datetime, date
from enum import Enum

from ..schemas.trading import Direction, OrderType, OrderStatus
from ..schemas.market import Exchange, ProductClass


class ValidationResult:
    """验证结果类"""
    
    def __init__(self, is_valid: bool = True, error_message: str = "", error_code: str = ""):
        self.is_valid = is_valid
        self.error_message = error_message
        self.error_code = error_code
    
    def __bool__(self):
        return self.is_valid
    
    def __str__(self):
        return self.error_message if not self.is_valid else "Valid"


class UserValidator:
    """用户数据验证器"""
    
    @staticmethod
    def validate_username(username: str) -> ValidationResult:
        """
        验证用户名
        
        Args:
            username: 用户名
            
        Returns:
            验证结果
        """
        if not username:
            return ValidationResult(False, "用户名不能为空", "USERNAME_EMPTY")
        
        if len(username) < 3:
            return ValidationResult(False, "用户名长度不能少于3个字符", "USERNAME_TOO_SHORT")
        
        if len(username) > 50:
            return ValidationResult(False, "用户名长度不能超过50个字符", "USERNAME_TOO_LONG")
        
        # 只允许字母、数字、下划线
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return ValidationResult(False, "用户名只能包含字母、数字和下划线", "USERNAME_INVALID_CHARS")
        
        # 不能以数字开头
        if username[0].isdigit():
            return ValidationResult(False, "用户名不能以数字开头", "USERNAME_START_WITH_DIGIT")
        
        return ValidationResult()
    
    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """
        验证邮箱地址
        
        Args:
            email: 邮箱地址
            
        Returns:
            验证结果
        """
        if not email:
            return ValidationResult(False, "邮箱地址不能为空", "EMAIL_EMPTY")
        
        # 基本邮箱格式验证
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return ValidationResult(False, "邮箱地址格式不正确", "EMAIL_INVALID_FORMAT")
        
        if len(email) > 100:
            return ValidationResult(False, "邮箱地址长度不能超过100个字符", "EMAIL_TOO_LONG")
        
        return ValidationResult()
    
    @staticmethod
    def validate_phone(phone: str) -> ValidationResult:
        """
        验证手机号码
        
        Args:
            phone: 手机号码
            
        Returns:
            验证结果
        """
        if not phone:
            return ValidationResult(False, "手机号码不能为空", "PHONE_EMPTY")
        
        # 中国手机号码格式验证
        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, phone):
            return ValidationResult(False, "手机号码格式不正确", "PHONE_INVALID_FORMAT")
        
        return ValidationResult()
    
    @staticmethod
    def validate_password(password: str) -> ValidationResult:
        """
        验证密码强度
        
        Args:
            password: 密码
            
        Returns:
            验证结果
        """
        if not password:
            return ValidationResult(False, "密码不能为空", "PASSWORD_EMPTY")
        
        if len(password) < 8:
            return ValidationResult(False, "密码长度不能少于8个字符", "PASSWORD_TOO_SHORT")
        
        if len(password) > 128:
            return ValidationResult(False, "密码长度不能超过128个字符", "PASSWORD_TOO_LONG")
        
        # 检查是否包含字母
        if not re.search(r'[a-zA-Z]', password):
            return ValidationResult(False, "密码必须包含字母", "PASSWORD_NO_LETTER")
        
        # 检查是否包含数字
        if not re.search(r'\d', password):
            return ValidationResult(False, "密码必须包含数字", "PASSWORD_NO_DIGIT")
        
        # 检查是否包含特殊字符（可选）
        # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        #     return ValidationResult(False, "密码必须包含特殊字符", "PASSWORD_NO_SPECIAL")
        
        return ValidationResult()


class TradingValidator:
    """交易数据验证器"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> ValidationResult:
        """
        验证股票代码
        
        Args:
            symbol: 股票代码
            
        Returns:
            验证结果
        """
        if not symbol:
            return ValidationResult(False, "股票代码不能为空", "SYMBOL_EMPTY")
        
        symbol = symbol.strip().upper()
        
        # 基本格式验证
        if not re.match(r'^[A-Z0-9.]+$', symbol):
            return ValidationResult(False, "股票代码格式不正确", "SYMBOL_INVALID_FORMAT")
        
        if len(symbol) > 20:
            return ValidationResult(False, "股票代码长度不能超过20个字符", "SYMBOL_TOO_LONG")
        
        return ValidationResult()
    
    @staticmethod
    def validate_price(price: Union[float, Decimal, str, None], allow_zero: bool = False) -> ValidationResult:
        """
        验证价格
        
        Args:
            price: 价格
            allow_zero: 是否允许零价格
            
        Returns:
            验证结果
        """
        if price is None:
            return ValidationResult(False, "价格不能为空", "PRICE_EMPTY")
        
        try:
            price_decimal = Decimal(str(price))
        except (ValueError, TypeError):
            return ValidationResult(False, "价格格式不正确", "PRICE_INVALID_FORMAT")
        
        if not allow_zero and price_decimal <= 0:
            return ValidationResult(False, "价格必须大于0", "PRICE_MUST_POSITIVE")
        
        if price_decimal < 0:
            return ValidationResult(False, "价格不能为负数", "PRICE_NEGATIVE")
        
        # 检查价格精度（最多4位小数）
        if price_decimal.as_tuple().exponent < -4:
            return ValidationResult(False, "价格精度不能超过4位小数", "PRICE_TOO_PRECISE")
        
        # 检查价格范围（最大100万）
        if price_decimal > 1000000:
            return ValidationResult(False, "价格不能超过100万", "PRICE_TOO_LARGE")
        
        return ValidationResult()
    
    @staticmethod
    def validate_volume(volume: Union[int, float, str, None]) -> ValidationResult:
        """
        验证交易数量
        
        Args:
            volume: 交易数量
            
        Returns:
            验证结果
        """
        if volume is None:
            return ValidationResult(False, "交易数量不能为空", "VOLUME_EMPTY")
        
        try:
            volume_float = float(volume)
        except (ValueError, TypeError):
            return ValidationResult(False, "交易数量格式不正确", "VOLUME_INVALID_FORMAT")
        
        if volume_float <= 0:
            return ValidationResult(False, "交易数量必须大于0", "VOLUME_MUST_POSITIVE")
        
        # 检查是否为整数倍（股票通常以100股为单位）
        if volume_float != int(volume_float):
            return ValidationResult(False, "交易数量必须为整数", "VOLUME_NOT_INTEGER")
        
        # 检查数量范围
        if volume_float > 1000000:
            return ValidationResult(False, "单笔交易数量不能超过100万股", "VOLUME_TOO_LARGE")
        
        return ValidationResult()
    
    @staticmethod
    def validate_direction(direction: str) -> ValidationResult:
        """
        验证交易方向
        
        Args:
            direction: 交易方向
            
        Returns:
            验证结果
        """
        if not direction:
            return ValidationResult(False, "交易方向不能为空", "DIRECTION_EMPTY")
        
        try:
            Direction(direction)
        except ValueError:
            return ValidationResult(False, f"无效的交易方向: {direction}", "DIRECTION_INVALID")
        
        return ValidationResult()
    
    @staticmethod
    def validate_order_type(order_type: str) -> ValidationResult:
        """
        验证订单类型
        
        Args:
            order_type: 订单类型
            
        Returns:
            验证结果
        """
        if not order_type:
            return ValidationResult(False, "订单类型不能为空", "ORDER_TYPE_EMPTY")
        
        try:
            OrderType(order_type)
        except ValueError:
            return ValidationResult(False, f"无效的订单类型: {order_type}", "ORDER_TYPE_INVALID")
        
        return ValidationResult()
    
    @staticmethod
    def validate_order_request(order_data: Dict[str, Any]) -> ValidationResult:
        """
        验证完整的订单请求
        
        Args:
            order_data: 订单数据字典
            
        Returns:
            验证结果
        """
        # 验证必填字段
        required_fields = ['symbol', 'direction', 'volume']
        for field in required_fields:
            if field not in order_data or order_data[field] is None:
                return ValidationResult(False, f"缺少必填字段: {field}", f"{field.upper()}_REQUIRED")
        
        # 验证股票代码
        symbol_result = TradingValidator.validate_symbol(order_data['symbol'])
        if not symbol_result:
            return symbol_result
        
        # 验证交易方向
        direction_result = TradingValidator.validate_direction(order_data['direction'])
        if not direction_result:
            return direction_result
        
        # 验证交易数量
        volume_result = TradingValidator.validate_volume(order_data['volume'])
        if not volume_result:
            return volume_result
        
        # 验证价格（如果是限价单）
        order_type = order_data.get('order_type', 'limit')
        if order_type == 'limit':
            if 'price' not in order_data:
                return ValidationResult(False, "限价单必须指定价格", "PRICE_REQUIRED_FOR_LIMIT_ORDER")
            
            price_result = TradingValidator.validate_price(order_data['price'])
            if not price_result:
                return price_result
        
        return ValidationResult()


class MarketDataValidator:
    """市场数据验证器"""
    
    @staticmethod
    def validate_date_range(start_date: Optional[date], end_date: Optional[date]) -> ValidationResult:
        """
        验证日期范围
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            验证结果
        """
        if start_date and end_date:
            if start_date > end_date:
                return ValidationResult(False, "开始日期不能晚于结束日期", "INVALID_DATE_RANGE")
            
            # 检查日期范围是否过大（最多5年）
            if (end_date - start_date).days > 365 * 5:
                return ValidationResult(False, "日期范围不能超过5年", "DATE_RANGE_TOO_LARGE")
        
        # 检查日期是否在未来
        today = date.today()
        if start_date and start_date > today:
            return ValidationResult(False, "开始日期不能是未来日期", "START_DATE_IN_FUTURE")
        
        if end_date and end_date > today:
            return ValidationResult(False, "结束日期不能是未来日期", "END_DATE_IN_FUTURE")
        
        return ValidationResult()
    
    @staticmethod
    def validate_kline_interval(interval: str) -> ValidationResult:
        """
        验证K线周期
        
        Args:
            interval: K线周期
            
        Returns:
            验证结果
        """
        valid_intervals = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', '1M']
        
        if interval not in valid_intervals:
            return ValidationResult(
                False, 
                f"无效的K线周期: {interval}，支持的周期: {', '.join(valid_intervals)}", 
                "INVALID_KLINE_INTERVAL"
            )
        
        return ValidationResult()
    
    @staticmethod
    def validate_limit(limit: Optional[int], max_limit: int = 10000) -> ValidationResult:
        """
        验证数据条数限制
        
        Args:
            limit: 数据条数
            max_limit: 最大限制
            
        Returns:
            验证结果
        """
        if limit is not None:
            if limit <= 0:
                return ValidationResult(False, "数据条数必须大于0", "LIMIT_MUST_POSITIVE")
            
            if limit > max_limit:
                return ValidationResult(False, f"数据条数不能超过{max_limit}", "LIMIT_TOO_LARGE")
        
        return ValidationResult()


class StrategyValidator:
    """策略验证器"""
    
    @staticmethod
    def validate_strategy_name(name: str) -> ValidationResult:
        """
        验证策略名称
        
        Args:
            name: 策略名称
            
        Returns:
            验证结果
        """
        if not name:
            return ValidationResult(False, "策略名称不能为空", "STRATEGY_NAME_EMPTY")
        
        if len(name) < 2:
            return ValidationResult(False, "策略名称长度不能少于2个字符", "STRATEGY_NAME_TOO_SHORT")
        
        if len(name) > 100:
            return ValidationResult(False, "策略名称长度不能超过100个字符", "STRATEGY_NAME_TOO_LONG")
        
        # 不允许特殊字符（除了中文、字母、数字、空格、下划线、横线）
        if not re.match(r'^[\u4e00-\u9fa5a-zA-Z0-9\s_-]+$', name):
            return ValidationResult(False, "策略名称包含不允许的字符", "STRATEGY_NAME_INVALID_CHARS")
        
        return ValidationResult()
    
    @staticmethod
    def validate_strategy_code(code: str) -> ValidationResult:
        """
        验证策略代码
        
        Args:
            code: 策略代码
            
        Returns:
            验证结果
        """
        if not code:
            return ValidationResult(False, "策略代码不能为空", "STRATEGY_CODE_EMPTY")
        
        if len(code) > 100000:  # 100KB
            return ValidationResult(False, "策略代码长度不能超过100KB", "STRATEGY_CODE_TOO_LONG")
        
        # 基本的Python语法检查（简单版本）
        try:
            compile(code, '<string>', 'exec')
        except SyntaxError as e:
            return ValidationResult(False, f"策略代码语法错误: {str(e)}", "STRATEGY_CODE_SYNTAX_ERROR")
        
        # 检查是否包含危险的操作
        dangerous_keywords = ['import os', 'import sys', 'exec(', 'eval(', '__import__', 'open(']
        for keyword in dangerous_keywords:
            if keyword in code:
                return ValidationResult(False, f"策略代码包含不允许的操作: {keyword}", "STRATEGY_CODE_DANGEROUS")
        
        return ValidationResult()
    
    @staticmethod
    def validate_strategy_parameters(parameters: Dict[str, Any]) -> ValidationResult:
        """
        验证策略参数
        
        Args:
            parameters: 策略参数字典
            
        Returns:
            验证结果
        """
        if not isinstance(parameters, dict):
            return ValidationResult(False, "策略参数必须是字典格式", "STRATEGY_PARAMS_NOT_DICT")
        
        # 检查参数数量
        if len(parameters) > 100:
            return ValidationResult(False, "策略参数数量不能超过100个", "STRATEGY_PARAMS_TOO_MANY")
        
        # 检查参数名称和值
        for key, value in parameters.items():
            if not isinstance(key, str):
                return ValidationResult(False, "参数名称必须是字符串", "STRATEGY_PARAM_KEY_NOT_STRING")
            
            if len(key) > 50:
                return ValidationResult(False, f"参数名称长度不能超过50个字符: {key}", "STRATEGY_PARAM_KEY_TOO_LONG")
            
            # 参数值必须是基本类型
            if not isinstance(value, (int, float, str, bool, type(None))):
                return ValidationResult(False, f"参数值类型不支持: {key}", "STRATEGY_PARAM_VALUE_UNSUPPORTED")
        
        return ValidationResult()


class BacktestValidator:
    """回测验证器"""
    
    @staticmethod
    def validate_backtest_period(start_date: date, end_date: date) -> ValidationResult:
        """
        验证回测周期
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            验证结果
        """
        # 基本日期范围验证
        date_result = MarketDataValidator.validate_date_range(start_date, end_date)
        if not date_result:
            return date_result
        
        # 回测周期不能太短（至少1天）
        if (end_date - start_date).days < 1:
            return ValidationResult(False, "回测周期至少需要1天", "BACKTEST_PERIOD_TOO_SHORT")
        
        # 回测周期不能太长（最多10年）
        if (end_date - start_date).days > 365 * 10:
            return ValidationResult(False, "回测周期不能超过10年", "BACKTEST_PERIOD_TOO_LONG")
        
        return ValidationResult()
    
    @staticmethod
    def validate_initial_capital(capital: Union[float, Decimal]) -> ValidationResult:
        """
        验证初始资金
        
        Args:
            capital: 初始资金
            
        Returns:
            验证结果
        """
        try:
            capital_decimal = Decimal(str(capital))
        except (ValueError, TypeError):
            return ValidationResult(False, "初始资金格式不正确", "INITIAL_CAPITAL_INVALID")
        
        if capital_decimal <= 0:
            return ValidationResult(False, "初始资金必须大于0", "INITIAL_CAPITAL_MUST_POSITIVE")
        
        if capital_decimal < 10000:
            return ValidationResult(False, "初始资金不能少于1万元", "INITIAL_CAPITAL_TOO_SMALL")
        
        if capital_decimal > 1000000000:  # 10亿
            return ValidationResult(False, "初始资金不能超过10亿元", "INITIAL_CAPITAL_TOO_LARGE")
        
        return ValidationResult()


def validate_pagination(page: int, page_size: int, max_page_size: int = 1000) -> ValidationResult:
    """
    验证分页参数
    
    Args:
        page: 页码
        page_size: 每页数量
        max_page_size: 最大每页数量
        
    Returns:
        验证结果
    """
    if page < 1:
        return ValidationResult(False, "页码必须大于等于1", "PAGE_INVALID")
    
    if page_size < 1:
        return ValidationResult(False, "每页数量必须大于等于1", "PAGE_SIZE_INVALID")
    
    if page_size > max_page_size:
        return ValidationResult(False, f"每页数量不能超过{max_page_size}", "PAGE_SIZE_TOO_LARGE")
    
    return ValidationResult()


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    清理用户输入
    
    Args:
        text: 原始文本
        max_length: 最大长度
        
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 移除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    
    # 移除SQL注入相关字符
    text = re.sub(r'[\'";\\]', '', text)
    
    # 限制长度
    if len(text) > max_length:
        text = text[:max_length]
    
    # 移除首尾空格
    text = text.strip()
    
    return text