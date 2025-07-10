"""
市场数据服务模块
处理行情数据、K线数据、深度数据等市场相关功能
"""
import random
import asyncio
from datetime import datetime, timedelta, date, time
from typing import List, Dict, Any, Optional, Union
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, asc, func
from sqlalchemy.orm import selectinload

from app.models.market import Symbol, MarketData, KLineData, DepthData, TradeTick, MarketType, KLineType
from app.schemas.market import (
    ContractData, TickData, BarData, DepthData, 
    MarketDataRequest, TickDataResponse, BarDataResponse
)
from app.utils.formatters import format_api_response, PriceFormatter, NumberFormatter
from app.utils.validators import MarketDataValidator, TradingValidator, ValidationResult
from app.utils.helpers import (
    generate_uuid, now, today, is_trading_day, get_trading_days_between,
    is_market_open, get_logger, paginate_list, safe_decimal, safe_float
)
from app.utils.exceptions import ValidationError, MarketDataError


logger = get_logger(__name__)


class MarketService:
    """市场数据服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # 模拟数据缓存
        self._price_cache = {}
        self._last_update = {}
    
    async def get_symbol_list(
        self, 
        market_type: Optional[MarketType] = None,
        exchange: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict[str, Any]:
        """
        获取交易标的列表
        
        Args:
            market_type: 市场类型筛选
            exchange: 交易所筛选
            search: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            标的列表
        """
        logger.info(f"获取标的列表: market_type={market_type}, exchange={exchange}")
        
        # 构建查询条件
        conditions = [Symbol.is_active == True]
        
        if market_type:
            conditions.append(Symbol.market_type == market_type)
        
        if exchange:
            conditions.append(Symbol.exchange == exchange)
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                Symbol.code.ilike(search_term) |
                Symbol.name.ilike(search_term)
            )
        
        # 构建查询
        stmt = select(Symbol).where(and_(*conditions))
        
        # 计算总数
        count_stmt = select(func.count(Symbol.id)).where(and_(*conditions))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar()
        
        # 分页查询
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size).order_by(Symbol.code)
        
        result = await self.db.execute(stmt)
        symbols = result.scalars().all()
        
        # 如果没有数据，创建一些模拟数据
        if not symbols and page == 1:
            await self._create_mock_symbols()
            # 重新查询
            result = await self.db.execute(stmt)
            symbols = result.scalars().all()
            
            # 重新计算总数
            total_result = await self.db.execute(count_stmt)
            total = total_result.scalar()
        
        # 转换为响应格式
        symbol_list = []
        for symbol in symbols:
            symbol_data = {
                "id": str(symbol.id),
                "code": symbol.code,
                "name": symbol.name,
                "market_type": symbol.market_type.value,
                "exchange": symbol.exchange,
                "sector": symbol.sector,
                "industry": symbol.industry,
                "currency": symbol.currency,
                "lot_size": symbol.lot_size,
                "tick_size": float(symbol.tick_size),
                "is_tradable": symbol.is_tradable,
                "created_at": symbol.created_at.isoformat() if symbol.created_at else None,
                "updated_at": symbol.updated_at.isoformat() if symbol.updated_at else None
            }
            symbol_list.append(symbol_data)
        
        return format_api_response(
            data={
                "items": symbol_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            },
            message="获取成功"
        )
    
    async def get_market_data(
        self, 
        symbol_codes: List[str],
        include_depth: bool = False
    ) -> Dict[str, Any]:
        """
        获取实时行情数据
        
        Args:
            symbol_codes: 标的代码列表
            include_depth: 是否包含深度数据
            
        Returns:
            行情数据
        """
        logger.info(f"获取实时行情: {symbol_codes}")
        
        if not symbol_codes:
            raise ValidationError("标的代码列表不能为空")
        
        # 验证标的代码
        for code in symbol_codes:
            result = TradingValidator.validate_symbol(code)
            if not result:
                raise ValidationError(f"无效的标的代码: {code}")
        
        market_data_list = []
        
        for symbol_code in symbol_codes:
            # 先尝试从数据库获取
            market_data = await self._get_latest_market_data(symbol_code)
            
            if not market_data:
                # 如果没有数据，生成模拟数据
                market_data = await self._generate_mock_market_data(symbol_code)
            
            if market_data:
                data = {
                    "symbol_code": market_data.symbol_code,
                    "last_price": float(market_data.last_price),
                    "open_price": float(market_data.open_price) if market_data.open_price else None,
                    "high_price": float(market_data.high_price) if market_data.high_price else None,
                    "low_price": float(market_data.low_price) if market_data.low_price else None,
                    "pre_close": float(market_data.pre_close) if market_data.pre_close else None,
                    "volume": market_data.volume,
                    "turnover": float(market_data.turnover) if market_data.turnover else None,
                    "bid_price": float(market_data.bid_price) if market_data.bid_price else None,
                    "bid_volume": market_data.bid_volume,
                    "ask_price": float(market_data.ask_price) if market_data.ask_price else None,
                    "ask_volume": market_data.ask_volume,
                    "change": float(market_data.change) if market_data.change else None,
                    "change_percent": float(market_data.change_percent) if market_data.change_percent else None,
                    "spread": float(market_data.spread) if market_data.spread else None,
                    "trading_date": market_data.trading_date.isoformat() if market_data.trading_date else None,
                    "timestamp": market_data.timestamp.isoformat() if market_data.timestamp else None
                }
                
                # 如果需要深度数据
                if include_depth:
                    depth_data = await self._get_depth_data(symbol_code)
                    if depth_data:
                        data["depth"] = depth_data
                
                market_data_list.append(data)
        
        return format_api_response(
            data=market_data_list,
            message="获取成功"
        )
    
    async def get_kline_data(
        self,
        symbol_code: str,
        kline_type: KLineType,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取K线数据
        
        Args:
            symbol_code: 标的代码
            kline_type: K线类型
            start_date: 开始日期
            end_date: 结束日期
            limit: 数据条数限制
            
        Returns:
            K线数据
        """
        logger.info(f"获取K线数据: {symbol_code}, {kline_type}")
        
        # 验证输入参数
        symbol_result = TradingValidator.validate_symbol(symbol_code)
        if not symbol_result:
            raise ValidationError(symbol_result.error_message)
        
        date_result = MarketDataValidator.validate_date_range(start_date, end_date)
        if not date_result:
            raise ValidationError(date_result.error_message)
        
        limit_result = MarketDataValidator.validate_limit(limit, 5000)
        if not limit_result:
            raise ValidationError(limit_result.error_message)
        
        # 构建查询条件
        conditions = [
            KLineData.symbol_code == symbol_code,
            KLineData.kline_type == kline_type
        ]
        
        if start_date:
            conditions.append(KLineData.trading_date >= start_date)
        
        if end_date:
            conditions.append(KLineData.trading_date <= end_date)
        
        # 构建查询
        stmt = select(KLineData).where(and_(*conditions)).order_by(KLineData.trading_date.desc())
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = await self.db.execute(stmt)
        kline_data = result.scalars().all()
        
        # 如果没有数据，生成模拟数据
        if not kline_data:
            kline_data = await self._generate_mock_kline_data(
                symbol_code, kline_type, start_date, end_date, limit
            )
        
        # 转换为响应格式
        kline_list = []
        for kline in kline_data:
            data = {
                "symbol_code": kline.symbol_code,
                "kline_type": kline.kline_type.value,
                "open_price": float(kline.open_price),
                "high_price": float(kline.high_price),
                "low_price": float(kline.low_price),
                "close_price": float(kline.close_price),
                "volume": kline.volume,
                "turnover": float(kline.turnover) if kline.turnover else None,
                "change": float(kline.change) if kline.change else None,
                "change_percent": float(kline.change_percent) if kline.change_percent else None,
                "amplitude": float(kline.amplitude) if kline.amplitude else None,
                "ma5": float(kline.ma5) if kline.ma5 else None,
                "ma10": float(kline.ma10) if kline.ma10 else None,
                "ma20": float(kline.ma20) if kline.ma20 else None,
                "is_up": kline.is_up,
                "body_size": float(kline.body_size) if kline.body_size else None,
                "upper_shadow": float(kline.upper_shadow) if kline.upper_shadow else None,
                "lower_shadow": float(kline.lower_shadow) if kline.lower_shadow else None,
                "trading_date": kline.trading_date.isoformat() if kline.trading_date else None,
                "period_start": kline.period_start.isoformat() if kline.period_start else None,
                "period_end": kline.period_end.isoformat() if kline.period_end else None,
                "created_at": kline.created_at.isoformat() if kline.created_at else None
            }
            kline_list.append(data)
        
        return format_api_response(
            data={
                "symbol_code": symbol_code,
                "kline_type": kline_type.value,
                "data": kline_list,
                "count": len(kline_list)
            },
            message="获取成功"
        )
    
    async def get_trade_ticks(
        self,
        symbol_code: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取逐笔成交数据
        
        Args:
            symbol_code: 标的代码
            start_time: 开始时间
            end_time: 结束时间
            limit: 数据条数限制
            
        Returns:
            逐笔成交数据
        """
        logger.info(f"获取逐笔成交: {symbol_code}")
        
        # 验证输入参数
        symbol_result = TradingValidator.validate_symbol(symbol_code)
        if not symbol_result:
            raise ValidationError(symbol_result.error_message)
        
        limit_result = MarketDataValidator.validate_limit(limit, 10000)
        if not limit_result:
            raise ValidationError(limit_result.error_message)
        
        # 构建查询条件
        conditions = [TradeTick.symbol_code == symbol_code]
        
        if start_time:
            conditions.append(TradeTick.trade_time >= start_time)
        
        if end_time:
            conditions.append(TradeTick.trade_time <= end_time)
        
        # 构建查询
        stmt = select(TradeTick).where(and_(*conditions)).order_by(TradeTick.trade_time.desc())
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = await self.db.execute(stmt)
        trade_ticks = result.scalars().all()
        
        # 如果没有数据，生成模拟数据
        if not trade_ticks:
            trade_ticks = await self._generate_mock_trade_ticks(
                symbol_code, start_time, end_time, limit or 100
            )
        
        # 转换为响应格式
        tick_list = []
        for tick in trade_ticks:
            data = {
                "symbol_code": tick.symbol_code,
                "price": float(tick.price),
                "volume": tick.volume,
                "turnover": float(tick.turnover),
                "direction": tick.direction,
                "trade_time": tick.trade_time.isoformat() if tick.trade_time else None,
                "timestamp": tick.timestamp.isoformat() if tick.timestamp else None
            }
            tick_list.append(data)
        
        return format_api_response(
            data={
                "symbol_code": symbol_code,
                "data": tick_list,
                "count": len(tick_list)
            },
            message="获取成功"
        )
    
    async def get_market_statistics(self) -> Dict[str, Any]:
        """
        获取市场统计数据
        
        Returns:
            市场统计数据
        """
        logger.info("获取市场统计数据")
        
        # 模拟市场统计数据
        stats = {
            "total_symbols": 4500,
            "active_symbols": 4200,
            "trading_symbols": 3800,
            "market_cap": "85.6万亿",
            "total_volume": "1.2万亿",
            "total_turnover": "8,500亿",
            "up_count": 1850,
            "down_count": 1420,
            "flat_count": 530,
            "limit_up_count": 45,
            "limit_down_count": 12,
            "markets": {
                "stock": {
                    "total": 4200,
                    "up": 1750,
                    "down": 1350,
                    "flat": 100
                },
                "futures": {
                    "total": 200,
                    "up": 80,
                    "down": 60,
                    "flat": 60
                },
                "crypto": {
                    "total": 100,
                    "up": 20,
                    "down": 10,
                    "flat": 70
                }
            },
            "top_gainers": [
                {"code": "000001", "name": "平安银行", "change_percent": 9.98},
                {"code": "000002", "name": "万科A", "change_percent": 8.56},
                {"code": "000858", "name": "五粮液", "change_percent": 7.23}
            ],
            "top_losers": [
                {"code": "002415", "name": "海康威视", "change_percent": -8.92},
                {"code": "000725", "name": "京东方A", "change_percent": -7.45},
                {"code": "002594", "name": "比亚迪", "change_percent": -6.78}
            ],
            "most_active": [
                {"code": "000001", "name": "平安银行", "volume": 125000000, "turnover": 8500000000},
                {"code": "000858", "name": "五粮液", "volume": 98000000, "turnover": 12000000000},
                {"code": "000002", "name": "万科A", "volume": 85000000, "turnover": 2100000000}
            ],
            "update_time": now().isoformat()
        }
        
        return format_api_response(
            data=stats,
            message="获取成功"
        )
    
    # ==================== 私有方法 ====================
    
    async def _get_latest_market_data(self, symbol_code: str) -> Optional[MarketData]:
        """获取最新行情数据"""
        stmt = select(MarketData).where(
            MarketData.symbol_code == symbol_code
        ).order_by(MarketData.timestamp.desc()).limit(1)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_depth_data(self, symbol_code: str) -> Optional[Dict[str, Any]]:
        """获取深度数据"""
        stmt = select(DepthData).where(
            DepthData.symbol_code == symbol_code
        ).order_by(DepthData.timestamp.desc()).limit(1)
        
        result = await self.db.execute(stmt)
        depth = result.scalar_one_or_none()
        
        if depth:
            return {
                "bid_prices": depth.bid_prices,
                "bid_volumes": depth.bid_volumes,
                "ask_prices": depth.ask_prices,
                "ask_volumes": depth.ask_volumes,
                "timestamp": depth.timestamp.isoformat() if depth.timestamp else None
            }
        
        return None
    
    async def _create_mock_symbols(self) -> None:
        """创建模拟标的数据"""
        mock_symbols = [
            {
                "code": "000001", "name": "平安银行", "market_type": MarketType.STOCK,
                "exchange": "SZSE", "sector": "金融", "industry": "银行"
            },
            {
                "code": "000002", "name": "万科A", "market_type": MarketType.STOCK,
                "exchange": "SZSE", "sector": "房地产", "industry": "房地产开发"
            },
            {
                "code": "000858", "name": "五粮液", "market_type": MarketType.STOCK,
                "exchange": "SZSE", "sector": "食品饮料", "industry": "白酒"
            },
            {
                "code": "600036", "name": "招商银行", "market_type": MarketType.STOCK,
                "exchange": "SSE", "sector": "金融", "industry": "银行"
            },
            {
                "code": "600519", "name": "贵州茅台", "market_type": MarketType.STOCK,
                "exchange": "SSE", "sector": "食品饮料", "industry": "白酒"
            },
            {
                "code": "BTCUSDT", "name": "比特币/USDT", "market_type": MarketType.CRYPTO,
                "exchange": "BINANCE", "sector": "数字货币", "industry": "加密货币"
            },
            {
                "code": "ETHUSDT", "name": "以太坊/USDT", "market_type": MarketType.CRYPTO,
                "exchange": "BINANCE", "sector": "数字货币", "industry": "加密货币"
            },
            {
                "code": "IF2312", "name": "沪深300股指期货", "market_type": MarketType.FUTURES,
                "exchange": "CFFEX", "sector": "金融期货", "industry": "股指期货"
            }
        ]
        
        for symbol_data in mock_symbols:
            symbol = Symbol(
                id=generate_uuid(),
                code=symbol_data["code"],
                name=symbol_data["name"],
                market_type=symbol_data["market_type"],
                exchange=symbol_data["exchange"],
                sector=symbol_data["sector"],
                industry=symbol_data["industry"],
                currency="CNY" if symbol_data["market_type"] != MarketType.CRYPTO else "USDT",
                lot_size=100 if symbol_data["market_type"] == MarketType.STOCK else 1,
                tick_size=Decimal("0.01"),
                is_active=True,
                is_tradable=True,
                created_at=now(),
                updated_at=now()
            )
            self.db.add(symbol)
        
        await self.db.commit()
        logger.info("已创建模拟标的数据")
    
    async def _generate_mock_market_data(self, symbol_code: str) -> MarketData:
        """生成模拟行情数据"""
        # 获取基础价格
        base_price = self._get_base_price(symbol_code)
        
        # 生成价格变动
        change_percent = random.uniform(-0.1, 0.1)  # -10% 到 +10%
        current_price = base_price * (1 + change_percent)
        
        # 生成其他价格
        high_price = current_price * random.uniform(1.0, 1.05)
        low_price = current_price * random.uniform(0.95, 1.0)
        open_price = base_price * random.uniform(0.98, 1.02)
        
        # 生成成交量
        volume = random.randint(1000000, 100000000)
        turnover = current_price * volume
        
        # 生成买卖盘
        bid_price = current_price * 0.999
        ask_price = current_price * 1.001
        bid_volume = random.randint(1000, 50000)
        ask_volume = random.randint(1000, 50000)
        
        market_data = MarketData(
            id=generate_uuid(),
            symbol_code=symbol_code,
            last_price=Decimal(str(round(current_price, 2))),
            open_price=Decimal(str(round(open_price, 2))),
            high_price=Decimal(str(round(high_price, 2))),
            low_price=Decimal(str(round(low_price, 2))),
            pre_close=Decimal(str(round(base_price, 2))),
            volume=volume,
            turnover=Decimal(str(round(turnover, 2))),
            bid_price=Decimal(str(round(bid_price, 2))),
            bid_volume=bid_volume,
            ask_price=Decimal(str(round(ask_price, 2))),
            ask_volume=ask_volume,
            change=Decimal(str(round(current_price - base_price, 2))),
            change_percent=Decimal(str(round(change_percent * 100, 2))),
            trading_date=today(),
            timestamp=now()
        )
        
        # 缓存价格用于下次生成
        self._price_cache[symbol_code] = current_price
        self._last_update[symbol_code] = now()
        
        return market_data
    
    async def _generate_mock_kline_data(
        self,
        symbol_code: str,
        kline_type: KLineType,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[KLineData]:
        """生成模拟K线数据"""
        # 确定日期范围
        if not end_date:
            end_date = today()
        
        if not start_date:
            if limit:
                # 根据limit计算开始日期
                days_back = min(limit, 250)  # 最多250天
            else:
                days_back = 30  # 默认30天
            start_date = end_date - timedelta(days=days_back)
        
        # 获取交易日
        trading_days = get_trading_days_between(start_date, end_date)
        if limit:
            trading_days = trading_days[-limit:]  # 取最近的数据
        
        # 生成K线数据
        kline_data = []
        base_price = self._get_base_price(symbol_code)
        current_price = base_price
        
        for trading_day in trading_days:
            # 生成价格变动
            change_percent = random.uniform(-0.05, 0.05)  # -5% 到 +5%
            
            open_price = current_price
            close_price = open_price * (1 + change_percent)
            high_price = max(open_price, close_price) * random.uniform(1.0, 1.03)
            low_price = min(open_price, close_price) * random.uniform(0.97, 1.0)
            
            # 生成成交量
            volume = random.randint(500000, 50000000)
            turnover = (open_price + close_price) / 2 * volume
            
            kline = KLineData(
                id=generate_uuid(),
                symbol_code=symbol_code,
                kline_type=kline_type,
                open_price=Decimal(str(round(open_price, 2))),
                high_price=Decimal(str(round(high_price, 2))),
                low_price=Decimal(str(round(low_price, 2))),
                close_price=Decimal(str(round(close_price, 2))),
                volume=volume,
                turnover=Decimal(str(round(turnover, 2))),
                change=Decimal(str(round(close_price - open_price, 2))),
                change_percent=Decimal(str(round(change_percent * 100, 2))),
                amplitude=Decimal(str(round((high_price - low_price) / open_price * 100, 2))),
                trading_date=trading_day,
                period_start=datetime.combine(trading_day, time(9, 30)),
                period_end=datetime.combine(trading_day, time(15, 0)),
                created_at=now()
            )
            
            kline_data.append(kline)
            current_price = close_price
        
        return kline_data
    
    async def _generate_mock_trade_ticks(
        self,
        symbol_code: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[TradeTick]:
        """生成模拟逐笔成交数据"""
        if not end_time:
            end_time = now()
        
        if not start_time:
            start_time = end_time - timedelta(hours=1)  # 默认1小时
        
        trade_ticks = []
        base_price = self._get_base_price(symbol_code)
        current_time = start_time
        time_interval = (end_time - start_time) / limit
        
        for i in range(limit):
            # 生成价格变动
            price_change = random.uniform(-0.02, 0.02)  # -2% 到 +2%
            price = base_price * (1 + price_change)
            
            # 生成成交量
            volume = random.randint(100, 10000)
            turnover = price * volume
            
            # 生成买卖方向
            direction = random.choice(['B', 'S', 'N'])  # Buy, Sell, Neutral
            
            tick = TradeTick(
                id=generate_uuid(),
                symbol_code=symbol_code,
                price=Decimal(str(round(price, 2))),
                volume=volume,
                turnover=Decimal(str(round(turnover, 2))),
                direction=direction,
                trade_time=current_time,
                timestamp=current_time
            )
            
            trade_ticks.append(tick)
            current_time += time_interval
        
        return trade_ticks
    
    def _get_base_price(self, symbol_code: str) -> float:
        """获取基础价格"""
        # 如果有缓存的价格，使用缓存
        if symbol_code in self._price_cache:
            last_update = self._last_update.get(symbol_code)
            if last_update and (now() - last_update).seconds < 300:  # 5分钟内的缓存有效
                return self._price_cache[symbol_code]
        
        # 根据标的代码生成基础价格
        price_map = {
            "000001": 12.50,    # 平安银行
            "000002": 18.80,    # 万科A
            "000858": 158.00,   # 五粮液
            "600036": 35.60,    # 招商银行
            "600519": 1680.00,  # 贵州茅台
            "BTCUSDT": 42000.00, # 比特币
            "ETHUSDT": 2800.00,  # 以太坊
            "IF2312": 4200.00   # 股指期货
        }
        
        return price_map.get(symbol_code, 100.00)  # 默认100元