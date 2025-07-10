"""
数据格式化工具模块
提供金融数据、时间、数字等格式化功能
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union, Any
from datetime import datetime, date, time
import re


class PriceFormatter:
    """价格格式化器"""
    
    @staticmethod
    def format_price(
        price: Union[float, Decimal, str, None], 
        precision: int = 2,
        show_sign: bool = False,
        currency: str = "¥"
    ) -> str:
        """
        格式化价格
        
        Args:
            price: 价格值
            precision: 小数位数
            show_sign: 是否显示正负号
            currency: 货币符号
            
        Returns:
            格式化后的价格字符串
        """
        if price is None:
            return "--"
            
        try:
            price_decimal = Decimal(str(price))
            formatted = price_decimal.quantize(
                Decimal('0.' + '0' * precision), 
                rounding=ROUND_HALF_UP
            )
            
            # 添加千分位分隔符
            price_str = f"{formatted:,.{precision}f}"
            
            # 添加正负号
            if show_sign and formatted > 0:
                price_str = f"+{price_str}"
                
            # 添加货币符号
            if currency:
                price_str = f"{currency}{price_str}"
                
            return price_str
        except (ValueError, TypeError):
            return "--"
    
    @staticmethod
    def format_change(
        change: Union[float, Decimal, None],
        change_percent: Union[float, Decimal, None] = None,
        precision: int = 2
    ) -> str:
        """
        格式化涨跌幅
        
        Args:
            change: 涨跌额
            change_percent: 涨跌幅百分比
            precision: 小数位数
            
        Returns:
            格式化后的涨跌幅字符串
        """
        if change is None:
            return "--"
            
        try:
            change_decimal = Decimal(str(change))
            change_str = PriceFormatter.format_price(
                change_decimal, precision, show_sign=True, currency=""
            )
            
            if change_percent is not None:
                percent_str = PercentFormatter.format_percent(
                    change_percent, precision, show_sign=True
                )
                return f"{change_str} ({percent_str})"
            
            return change_str
        except (ValueError, TypeError):
            return "--"


class PercentFormatter:
    """百分比格式化器"""
    
    @staticmethod
    def format_percent(
        value: Union[float, Decimal, None],
        precision: int = 2,
        show_sign: bool = False
    ) -> str:
        """
        格式化百分比
        
        Args:
            value: 数值（小数形式，如0.05表示5%）
            precision: 小数位数
            show_sign: 是否显示正负号
            
        Returns:
            格式化后的百分比字符串
        """
        if value is None:
            return "--"
            
        try:
            value_decimal = Decimal(str(value)) * 100
            formatted = value_decimal.quantize(
                Decimal('0.' + '0' * precision),
                rounding=ROUND_HALF_UP
            )
            
            percent_str = f"{formatted:.{precision}f}%"
            
            if show_sign and formatted > 0:
                percent_str = f"+{percent_str}"
                
            return percent_str
        except (ValueError, TypeError):
            return "--"


class NumberFormatter:
    """数字格式化器"""
    
    @staticmethod
    def format_volume(volume: Union[int, float, None]) -> str:
        """
        格式化成交量
        
        Args:
            volume: 成交量
            
        Returns:
            格式化后的成交量字符串（如：1.23万、4.56亿）
        """
        if volume is None:
            return "--"
            
        try:
            volume = float(volume)
            
            if volume >= 100000000:  # 亿
                return f"{volume / 100000000:.2f}亿"
            elif volume >= 10000:  # 万
                return f"{volume / 10000:.2f}万"
            else:
                return f"{volume:,.0f}"
        except (ValueError, TypeError):
            return "--"
    
    @staticmethod
    def format_amount(amount: Union[float, Decimal, None]) -> str:
        """
        格式化金额
        
        Args:
            amount: 金额
            
        Returns:
            格式化后的金额字符串
        """
        if amount is None:
            return "--"
            
        try:
            amount = float(amount)
            
            if amount >= 100000000:  # 亿
                return f"{amount / 100000000:.2f}亿"
            elif amount >= 10000:  # 万
                return f"{amount / 10000:.2f}万"
            else:
                return f"{amount:,.2f}"
        except (ValueError, TypeError):
            return "--"
    
    @staticmethod
    def format_ratio(ratio: Union[float, Decimal, None], precision: int = 4) -> str:
        """
        格式化比率（如夏普比率）
        
        Args:
            ratio: 比率值
            precision: 小数位数
            
        Returns:
            格式化后的比率字符串
        """
        if ratio is None:
            return "--"
            
        try:
            ratio_decimal = Decimal(str(ratio))
            formatted = ratio_decimal.quantize(
                Decimal('0.' + '0' * precision),
                rounding=ROUND_HALF_UP
            )
            return f"{formatted:.{precision}f}"
        except (ValueError, TypeError):
            return "--"


class DateTimeFormatter:
    """日期时间格式化器"""
    
    @staticmethod
    def format_datetime(
        dt: Union[datetime, str, None],
        fmt: str = "%Y-%m-%d %H:%M:%S"
    ) -> str:
        """
        格式化日期时间
        
        Args:
            dt: 日期时间对象或字符串
            fmt: 格式化模板
            
        Returns:
            格式化后的日期时间字符串
        """
        if dt is None:
            return "--"
            
        try:
            if isinstance(dt, str):
                # 尝试解析字符串
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            
            if isinstance(dt, datetime):
                return dt.strftime(fmt)
                
            return str(dt)
        except (ValueError, TypeError):
            return "--"
    
    @staticmethod
    def format_date(
        d: Union[date, datetime, str, None],
        fmt: str = "%Y-%m-%d"
    ) -> str:
        """
        格式化日期
        
        Args:
            d: 日期对象或字符串
            fmt: 格式化模板
            
        Returns:
            格式化后的日期字符串
        """
        if d is None:
            return "--"
            
        try:
            if isinstance(d, str):
                d = datetime.fromisoformat(d.replace('Z', '+00:00')).date()
            elif isinstance(d, datetime):
                d = d.date()
            
            if isinstance(d, date):
                return d.strftime(fmt)
                
            return str(d)
        except (ValueError, TypeError):
            return "--"
    
    @staticmethod
    def format_time(
        t: Union[time, datetime, str, None],
        fmt: str = "%H:%M:%S"
    ) -> str:
        """
        格式化时间
        
        Args:
            t: 时间对象或字符串
            fmt: 格式化模板
            
        Returns:
            格式化后的时间字符串
        """
        if t is None:
            return "--"
            
        try:
            if isinstance(t, str):
                t = datetime.fromisoformat(t.replace('Z', '+00:00')).time()
            elif isinstance(t, datetime):
                t = t.time()
            
            if isinstance(t, time):
                return t.strftime(fmt)
                
            return str(t)
        except (ValueError, TypeError):
            return "--"
    
    @staticmethod
    def format_trading_time(dt: Union[datetime, str, None]) -> str:
        """
        格式化交易时间（智能显示）
        
        Args:
            dt: 日期时间
            
        Returns:
            格式化后的交易时间字符串
        """
        if dt is None:
            return "--"
            
        try:
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            
            now = datetime.now()
            
            # 今天的显示时间
            if dt.date() == now.date():
                return dt.strftime("%H:%M:%S")
            # 本年的显示月日时间
            elif dt.year == now.year:
                return dt.strftime("%m-%d %H:%M")
            # 其他显示完整日期时间
            else:
                return dt.strftime("%Y-%m-%d %H:%M")
                
        except (ValueError, TypeError):
            return "--"


class SymbolFormatter:
    """股票代码格式化器"""
    
    @staticmethod
    def format_symbol(symbol: str) -> str:
        """
        格式化股票代码
        
        Args:
            symbol: 原始股票代码
            
        Returns:
            格式化后的股票代码
        """
        if not symbol:
            return ""
            
        # 移除多余的空格
        symbol = symbol.strip().upper()
        
        # 添加交易所后缀（如果没有）
        if '.' not in symbol:
            if symbol.startswith('00') or symbol.startswith('30'):
                symbol = f"{symbol}.SZ"  # 深交所
            elif symbol.startswith('60') or symbol.startswith('68'):
                symbol = f"{symbol}.SH"  # 上交所
        
        return symbol
    
    @staticmethod
    def get_exchange_from_symbol(symbol: str) -> str:
        """
        从股票代码获取交易所
        
        Args:
            symbol: 股票代码
            
        Returns:
            交易所代码
        """
        if not symbol:
            return ""
            
        symbol = symbol.upper()
        
        if '.SH' in symbol or symbol.startswith('60') or symbol.startswith('68'):
            return "SH"
        elif '.SZ' in symbol or symbol.startswith('00') or symbol.startswith('30'):
            return "SZ"
        elif '.BJ' in symbol or symbol.startswith('8') or symbol.startswith('4'):
            return "BJ"
        else:
            return ""


class StatusFormatter:
    """状态格式化器"""
    
    # 状态颜色映射
    STATUS_COLORS = {
        "success": "green",
        "error": "red", 
        "warning": "orange",
        "info": "blue",
        "pending": "gray"
    }
    
    # 订单状态映射
    ORDER_STATUS_MAP = {
        "submitted": "已提交",
        "partial_filled": "部分成交",
        "all_filled": "全部成交",
        "cancelled": "已撤销",
        "rejected": "已拒绝"
    }
    
    @staticmethod
    def format_order_status(status: str) -> str:
        """
        格式化订单状态
        
        Args:
            status: 订单状态英文
            
        Returns:
            中文状态描述
        """
        return StatusFormatter.ORDER_STATUS_MAP.get(status, status)
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """
        获取状态对应的颜色
        
        Args:
            status: 状态
            
        Returns:
            颜色代码
        """
        return StatusFormatter.STATUS_COLORS.get(status, "gray")


def format_api_response(data: Any, success: bool = True, message: str = "") -> dict:
    """
    格式化API响应
    
    Args:
        data: 响应数据
        success: 是否成功
        message: 响应消息
        
    Returns:
        标准化的API响应格式
    """
    response = {
        "success": success,
        "data": data,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    return response


def clean_numeric_string(value: str) -> str:
    """
    清理数字字符串（移除非数字字符）
    
    Args:
        value: 原始字符串
        
    Returns:
        清理后的数字字符串
    """
    if not value:
        return ""
        
    # 保留数字、小数点、负号
    cleaned = re.sub(r'[^\d.-]', '', str(value))
    return cleaned