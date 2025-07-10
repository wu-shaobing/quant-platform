"""
CTP交易接口服务
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List
from decimal import Decimal
import threading
import time

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert

from app.core.ctp_config import CTPConfig, CTPStatus, CTPError, CTPOrderRef, ctp_config, get_error_message
from app.models.ctp_models import CTPOrder, CTPTrade, CTPPosition, CTPAccount
from app.schemas.trading import OrderRequest, OrderResponse
from app.core.database import get_db

# 导入监控系统
try:
    from app.monitoring.ctp_metrics import CTPMetricsCollector
    from app.monitoring.ctp_alerts import CTPAlertManager
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    logging.warning("Monitoring system not available")

# 导入性能优化组件
try:
    from app.core.cache import cache_manager, CacheKeyPrefix
    from app.core.database_optimizer import db_optimizer
    from app.core.performance_optimizer import performance_optimizer
    OPTIMIZATION_AVAILABLE = True
except ImportError:
    OPTIMIZATION_AVAILABLE = False
    logging.warning("Performance optimization not available")

logger = logging.getLogger(__name__)


class CTPService:
    """CTP交易服务"""

    def __init__(self, config: Optional[CTPConfig] = None):
        self.config = config or ctp_config
        self.status = CTPStatus()
        self.order_ref_manager = CTPOrderRef(
            prefix=self.config.order_ref_prefix,
            max_ref=self.config.max_order_ref
        )

        # 初始化监控系统
        if MONITORING_AVAILABLE:
            self.metrics_collector = CTPMetricsCollector()
            self.alert_manager = CTPAlertManager()
            logger.info("Monitoring system initialized")
        else:
            self.metrics_collector = None
            self.alert_manager = None
        
        # 连接对象
        self.trade_api = None
        self.md_api = None
        
        # 回调函数
        self.callbacks: Dict[str, List[Callable]] = {
            'on_order': [],
            'on_trade': [],
            'on_position': [],
            'on_account': [],
            'on_tick': [],
            'on_error': []
        }
        
        # 数据缓存
        self.orders: Dict[str, Dict] = {}
        self.trades: Dict[str, Dict] = {}
        self.positions: Dict[str, Dict] = {}
        self.account: Optional[Dict] = None
        self.ticks: Dict[str, Dict] = {}
        
        # 异步锁
        self._lock = asyncio.Lock()
        self._db_session: Optional[AsyncSession] = None
        
        # 连接状态
        self._trade_connected = False
        self._md_connected = False
        self._trade_logged_in = False
        self._md_logged_in = False
        
        logger.info("CTP服务初始化完成")
    
    async def initialize(self) -> bool:
        """初始化CTP连接"""
        try:
            logger.info("开始初始化CTP连接...")
            
            # 验证配置
            if not self._validate_config():
                raise CTPError(-1, "CTP配置验证失败")
            
            # 初始化数据库会话
            self._db_session = next(get_db())
            
            # 初始化交易和行情接口
            await asyncio.gather(
                self._init_trade_api(),
                self._init_md_api()
            )
            
            # 等待连接完成
            await self._wait_for_connection()
            
            logger.info("CTP连接初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"CTP初始化失败: {e}")
            self.status.last_error = str(e)
            self.status.error_count += 1
            return False
    
    def _validate_config(self) -> bool:
        """验证配置"""
        required_fields = ['broker_id', 'user_id', 'password', 'trade_front', 'md_front']
        for field in required_fields:
            if not getattr(self.config, field):
                logger.error(f"CTP配置缺少必要字段: {field}")
                return False
        return True
    
    async def _init_trade_api(self):
        """初始化交易接口"""
        try:
            # 这里应该使用实际的CTP API
            # 由于vnpy需要在实际环境中安装，这里提供模拟实现
            logger.info("初始化交易接口...")
            
            # 模拟连接过程
            await asyncio.sleep(1)
            self._trade_connected = True
            self.status.trade_connected = True
            self.status.trade_connect_time = datetime.now().isoformat()
            
            # 模拟登录过程
            await asyncio.sleep(1)
            self._trade_logged_in = True
            self.status.trade_logged_in = True
            self.status.trade_login_time = datetime.now().isoformat()
            
            logger.info("交易接口初始化完成")
            
        except Exception as e:
            logger.error(f"交易接口初始化失败: {e}")
            raise
    
    async def _init_md_api(self):
        """初始化行情接口"""
        try:
            logger.info("初始化行情接口...")
            
            # 模拟连接过程
            await asyncio.sleep(1)
            self._md_connected = True
            self.status.md_connected = True
            self.status.md_connect_time = datetime.now().isoformat()
            
            # 模拟登录过程
            await asyncio.sleep(1)
            self._md_logged_in = True
            self.status.md_logged_in = True
            self.status.md_login_time = datetime.now().isoformat()
            
            logger.info("行情接口初始化完成")
            
        except Exception as e:
            logger.error(f"行情接口初始化失败: {e}")
            raise
    
    async def _wait_for_connection(self, timeout: int = 30):
        """等待连接完成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.status.is_ready:
                logger.info("CTP连接就绪")
                return
            await asyncio.sleep(0.5)
        
        raise CTPError(-1, f"CTP连接超时 ({timeout}秒)")
    
    async def submit_order(self, order_request: OrderRequest, user_id: int) -> OrderResponse:
        """提交订单（性能优化版本）"""
        try:
            # 使用性能优化器提交订单
            if OPTIMIZATION_AVAILABLE:
                order_data = {
                    'user_id': user_id,
                    'symbol': order_request.symbol,
                    'direction': order_request.direction,
                    'offset': order_request.offset,
                    'order_type': order_request.order_type,
                    'price': order_request.price,
                    'volume': order_request.volume
                }
                order_id = await performance_optimizer.submit_order(order_data)

                # 缓存订单请求
                await cache_manager.cache.set(
                    CacheKeyPrefix.ORDER_DATA,
                    f"request_{order_id}",
                    order_data,
                    ttl=3600
                )

            async with self._lock:
                if not self.status.trade_ready:
                    raise CTPError(-1, "交易接口未就绪")

                # 生成订单引用
                order_ref = self.order_ref_manager.get_next_ref()

                # 创建CTP订单记录
                ctp_order = CTPOrder(
                    user_id=user_id,
                    order_ref=order_ref,
                    instrument_id=order_request.symbol,
                    exchange_id=self._get_exchange_id(order_request.symbol),
                    direction=self._convert_direction(order_request.direction),
                    offset_flag=self._convert_offset(order_request.offset),
                    order_price_type=self._convert_order_type(order_request.order_type),
                    limit_price=Decimal(str(order_request.price)),
                    volume_total_original=order_request.volume,
                    time_condition="3",  # 当日有效
                    volume_condition="1",  # 任何数量
                    volume_total=order_request.volume
                )
                
                # 保存到数据库
                if self._db_session:
                    self._db_session.add(ctp_order)
                    await self._db_session.commit()
                    await self._db_session.refresh(ctp_order)
                
                # 模拟提交到CTP
                await self._simulate_order_submission(ctp_order)
                
                # 更新统计
                self.status.order_count += 1
                
                logger.info(f"订单提交成功: {order_ref}")
                
                return OrderResponse(
                    success=True,
                    message="订单提交成功",
                    data={
                        "order_ref": order_ref,
                        "order_id": str(ctp_order.id),
                        "symbol": order_request.symbol,
                        "direction": order_request.direction,
                        "price": order_request.price,
                        "volume": order_request.volume,
                        "status": "SUBMITTED"
                    }
                )
                
        except Exception as e:
            logger.error(f"订单提交失败: {e}")
            self.status.last_error = str(e)
            self.status.error_count += 1
            raise CTPError(-1, f"订单提交失败: {e}")
    
    async def cancel_order(self, order_ref: str, user_id: int) -> bool:
        """撤销订单"""
        try:
            async with self._lock:
                if not self.status.trade_ready:
                    raise CTPError(-1, "交易接口未就绪")
                
                # 查找订单
                if self._db_session:
                    result = await self._db_session.execute(
                        select(CTPOrder).where(
                            CTPOrder.order_ref == order_ref,
                            CTPOrder.user_id == user_id
                        )
                    )
                    order = result.scalar_one_or_none()
                    
                    if not order:
                        raise CTPError(-1, f"订单不存在: {order_ref}")
                    
                    # 模拟撤单
                    await self._simulate_order_cancellation(order)
                    
                    logger.info(f"订单撤销成功: {order_ref}")
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"订单撤销失败: {e}")
            self.status.last_error = str(e)
            self.status.error_count += 1
            raise CTPError(-1, f"订单撤销失败: {e}")
    
    async def query_orders(self, user_id: int) -> List[Dict]:
        """查询订单"""
        try:
            if self._db_session:
                result = await self._db_session.execute(
                    select(CTPOrder).where(CTPOrder.user_id == user_id)
                    .order_by(CTPOrder.created_at.desc())
                )
                orders = result.scalars().all()
                
                return [self._order_to_dict(order) for order in orders]
            
            return []
            
        except Exception as e:
            logger.error(f"查询订单失败: {e}")
            raise CTPError(-1, f"查询订单失败: {e}")
    
    async def query_trades(self, user_id: int) -> List[Dict]:
        """查询成交"""
        try:
            if self._db_session:
                result = await self._db_session.execute(
                    select(CTPTrade).where(CTPTrade.user_id == user_id)
                    .order_by(CTPTrade.created_at.desc())
                )
                trades = result.scalars().all()
                
                return [self._trade_to_dict(trade) for trade in trades]
            
            return []
            
        except Exception as e:
            logger.error(f"查询成交失败: {e}")
            raise CTPError(-1, f"查询成交失败: {e}")
    
    async def query_positions(self, user_id: int) -> List[Dict]:
        """查询持仓"""
        try:
            if self._db_session:
                result = await self._db_session.execute(
                    select(CTPPosition).where(CTPPosition.user_id == user_id)
                )
                positions = result.scalars().all()
                
                return [self._position_to_dict(position) for position in positions]
            
            return []
            
        except Exception as e:
            logger.error(f"查询持仓失败: {e}")
            raise CTPError(-1, f"查询持仓失败: {e}")
    
    async def query_account(self, user_id: int) -> Optional[Dict]:
        """查询账户"""
        try:
            if self._db_session:
                result = await self._db_session.execute(
                    select(CTPAccount).where(CTPAccount.user_id == user_id)
                    .order_by(CTPAccount.created_at.desc())
                    .limit(1)
                )
                account = result.scalar_one_or_none()
                
                if account:
                    return self._account_to_dict(account)
            
            return None
            
        except Exception as e:
            logger.error(f"查询账户失败: {e}")
            raise CTPError(-1, f"查询账户失败: {e}")
    
    def get_status(self) -> CTPStatus:
        """获取连接状态"""
        return self.status
    
    def add_callback(self, event: str, callback: Callable):
        """添加回调函数"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def remove_callback(self, event: str, callback: Callable):
        """移除回调函数"""
        if event in self.callbacks and callback in self.callbacks[event]:
            self.callbacks[event].remove(callback)
    
    async def _simulate_order_submission(self, order: CTPOrder):
        """模拟订单提交（用于测试）"""
        # 模拟订单状态变化
        await asyncio.sleep(0.1)
        
        # 模拟部分成交
        if order.volume_total_original > 1:
            trade_volume = min(order.volume_total_original // 2, 10)
            await self._simulate_trade(order, trade_volume)
    
    async def _simulate_order_cancellation(self, order: CTPOrder):
        """模拟订单撤销（用于测试）"""
        if self._db_session:
            await self._db_session.execute(
                update(CTPOrder)
                .where(CTPOrder.id == order.id)
                .values(order_status="a", cancel_time=datetime.now().strftime("%H:%M:%S"))
            )
            await self._db_session.commit()
    
    async def _simulate_trade(self, order: CTPOrder, volume: int):
        """模拟成交（用于测试）"""
        if self._db_session:
            # 创建成交记录
            trade = CTPTrade(
                user_id=order.user_id,
                trade_id=f"T{int(time.time() * 1000)}",
                order_ref=order.order_ref,
                order_sys_id=order.order_sys_id,
                instrument_id=order.instrument_id,
                exchange_id=order.exchange_id,
                direction=order.direction,
                offset_flag=order.offset_flag,
                price=order.limit_price,
                volume=volume,
                trade_date=datetime.now().strftime("%Y%m%d"),
                trade_time=datetime.now().strftime("%H:%M:%S")
            )
            
            self._db_session.add(trade)
            
            # 更新订单状态
            new_traded = order.volume_traded + volume
            new_total = order.volume_total - volume
            new_status = "1" if new_total == 0 else "2"  # 全部成交或部分成交
            
            await self._db_session.execute(
                update(CTPOrder)
                .where(CTPOrder.id == order.id)
                .values(
                    volume_traded=new_traded,
                    volume_total=new_total,
                    order_status=new_status
                )
            )
            
            await self._db_session.commit()
            
            # 更新统计
            self.status.trade_count += 1
    
    def _get_exchange_id(self, symbol: str) -> str:
        """根据合约代码获取交易所代码"""
        # 简单的交易所映射逻辑
        if symbol.startswith(('cu', 'al', 'zn', 'pb', 'ni', 'sn', 'au', 'ag')):
            return "SHFE"
        elif symbol.startswith(('c', 'm', 'y', 'p', 'a', 'b', 'jm', 'i', 'j')):
            return "DCE"
        elif symbol.startswith(('CF', 'SR', 'TA', 'OI', 'MA', 'FG', 'RM', 'ZC')):
            return "CZCE"
        else:
            return "SHFE"  # 默认上期所
    
    def _convert_direction(self, direction: str) -> str:
        """转换交易方向"""
        return "0" if direction.upper() in ["BUY", "LONG"] else "1"
    
    def _convert_offset(self, offset: str) -> str:
        """转换开平标志"""
        offset_map = {
            "OPEN": "0",
            "CLOSE": "1",
            "CLOSE_TODAY": "3",
            "CLOSE_YESTERDAY": "4"
        }
        return offset_map.get(offset.upper(), "0")
    
    def _convert_order_type(self, order_type: str) -> str:
        """转换订单类型"""
        type_map = {
            "LIMIT": "2",
            "MARKET": "1",
            "STOP": "3"
        }
        return type_map.get(order_type.upper(), "2")
    
    def _order_to_dict(self, order: CTPOrder) -> Dict:
        """订单对象转字典"""
        return {
            "id": str(order.id),
            "order_ref": order.order_ref,
            "order_sys_id": order.order_sys_id,
            "symbol": order.instrument_id,
            "exchange": order.exchange_id,
            "direction": order.direction,
            "offset": order.offset_flag,
            "price": float(order.limit_price),
            "volume": order.volume_total_original,
            "traded": order.volume_traded,
            "remaining": order.volume_total,
            "status": order.order_status,
            "insert_time": order.insert_time,
            "created_at": order.created_at.isoformat() if order.created_at else None
        }
    
    def _trade_to_dict(self, trade: CTPTrade) -> Dict:
        """成交对象转字典"""
        return {
            "id": str(trade.id),
            "trade_id": trade.trade_id,
            "order_ref": trade.order_ref,
            "symbol": trade.instrument_id,
            "exchange": trade.exchange_id,
            "direction": trade.direction,
            "offset": trade.offset_flag,
            "price": float(trade.price),
            "volume": trade.volume,
            "trade_time": trade.trade_time,
            "created_at": trade.created_at.isoformat() if trade.created_at else None
        }
    
    def _position_to_dict(self, position: CTPPosition) -> Dict:
        """持仓对象转字典"""
        return {
            "id": str(position.id),
            "symbol": position.instrument_id,
            "direction": position.position_direction,
            "position": position.position,
            "yd_position": position.yd_position,
            "frozen": position.long_frozen + position.short_frozen,
            "cost": float(position.position_cost),
            "margin": float(position.use_margin),
            "profit": float(position.position_profit),
            "created_at": position.created_at.isoformat() if position.created_at else None
        }
    
    def _account_to_dict(self, account: CTPAccount) -> Dict:
        """账户对象转字典"""
        return {
            "id": str(account.id),
            "account_id": account.account_id,
            "balance": float(account.balance),
            "available": float(account.available),
            "margin": float(account.curr_margin),
            "frozen_margin": float(account.frozen_margin),
            "frozen_cash": float(account.frozen_cash),
            "position_profit": float(account.position_profit),
            "close_profit": float(account.close_profit),
            "commission": float(account.commission),
            "trading_day": account.trading_day,
            "created_at": account.created_at.isoformat() if account.created_at else None
        }


    async def subscribe_market_data(self, symbols: List[str]) -> bool:
        """订阅行情数据"""
        try:
            if not self.status.md_ready:
                raise CTPError(-1, "行情接口未就绪")

            # 检查订阅数量限制
            if len(symbols) > self.config.max_subscribe_count:
                raise CTPError(-1, f"订阅数量超过限制: {len(symbols)} > {self.config.max_subscribe_count}")

            # 模拟订阅行情
            for symbol in symbols:
                await self._simulate_market_data(symbol)

            self.status.subscribe_count += len(symbols)
            logger.info(f"订阅行情成功: {symbols}")
            return True

        except Exception as e:
            logger.error(f"订阅行情失败: {e}")
            self.status.last_error = str(e)
            self.status.error_count += 1
            raise CTPError(-1, f"订阅行情失败: {e}")

    async def unsubscribe_market_data(self, symbols: List[str]) -> bool:
        """取消订阅行情数据"""
        try:
            if not self.status.md_ready:
                raise CTPError(-1, "行情接口未就绪")

            # 模拟取消订阅
            for symbol in symbols:
                if symbol in self.ticks:
                    del self.ticks[symbol]

            self.status.subscribe_count -= len(symbols)
            logger.info(f"取消订阅行情成功: {symbols}")
            return True

        except Exception as e:
            logger.error(f"取消订阅行情失败: {e}")
            raise CTPError(-1, f"取消订阅行情失败: {e}")

    async def _simulate_market_data(self, symbol: str):
        """模拟行情数据推送（用于测试）"""
        import random

        # 生成模拟行情数据
        base_price = 3000.0  # 基础价格
        tick_data = {
            "symbol": symbol,
            "exchange": self._get_exchange_id(symbol),
            "last_price": round(base_price + random.uniform(-100, 100), 2),
            "bid_price": round(base_price + random.uniform(-100, 100), 2),
            "ask_price": round(base_price + random.uniform(-100, 100), 2),
            "bid_volume": random.randint(1, 100),
            "ask_volume": random.randint(1, 100),
            "volume": random.randint(1000, 10000),
            "turnover": round(random.uniform(1000000, 10000000), 2),
            "open_interest": random.randint(10000, 100000),
            "update_time": datetime.now().strftime("%H:%M:%S"),
            "update_millisec": random.randint(0, 999),
            "timestamp": datetime.now().isoformat()
        }

        # 缓存行情数据
        self.ticks[symbol] = tick_data

        # 触发回调
        for callback in self.callbacks.get('on_tick', []):
            try:
                await callback(tick_data)
            except Exception as e:
                logger.error(f"行情回调执行失败: {e}")

    async def get_tick_data(self, symbol: str) -> Optional[Dict]:
        """获取最新行情数据"""
        return self.ticks.get(symbol)

    async def disconnect(self):
        """断开连接"""
        try:
            logger.info("断开CTP连接...")

            # 重置连接状态
            self._trade_connected = False
            self._md_connected = False
            self._trade_logged_in = False
            self._md_logged_in = False

            self.status.trade_connected = False
            self.status.md_connected = False
            self.status.trade_logged_in = False
            self.status.md_logged_in = False

            # 清理数据
            self.orders.clear()
            self.trades.clear()
            self.positions.clear()
            self.ticks.clear()
            self.account = None

            # 关闭数据库会话
            if self._db_session:
                await self._db_session.close()
                self._db_session = None

            logger.info("CTP连接已断开")

        except Exception as e:
            logger.error(f"断开CTP连接失败: {e}")
            raise CTPError(-1, f"断开连接失败: {e}")

    async def reconnect(self) -> bool:
        """重新连接"""
        try:
            logger.info("重新连接CTP...")

            # 先断开现有连接
            await self.disconnect()

            # 重新初始化
            return await self.initialize()

        except Exception as e:
            logger.error(f"重新连接失败: {e}")
            return False


class CTPMarketDataService:
    """CTP行情数据服务"""

    def __init__(self, ctp_service: CTPService):
        self.ctp_service = ctp_service
        self.subscribers: Dict[str, set] = {}  # symbol -> set of client_ids
        self.client_subscriptions: Dict[str, set] = {}  # client_id -> set of symbols

    async def subscribe(self, client_id: str, symbols: List[str]):
        """客户端订阅行情"""
        try:
            # 记录客户端订阅
            if client_id not in self.client_subscriptions:
                self.client_subscriptions[client_id] = set()

            new_symbols = []
            for symbol in symbols:
                if symbol not in self.subscribers:
                    self.subscribers[symbol] = set()
                    new_symbols.append(symbol)

                self.subscribers[symbol].add(client_id)
                self.client_subscriptions[client_id].add(symbol)

            # 订阅新的合约
            if new_symbols:
                await self.ctp_service.subscribe_market_data(new_symbols)

            logger.info(f"客户端 {client_id} 订阅行情: {symbols}")

        except Exception as e:
            logger.error(f"订阅行情失败: {e}")
            raise

    async def unsubscribe(self, client_id: str, symbols: List[str] = None):
        """客户端取消订阅行情"""
        try:
            if client_id not in self.client_subscriptions:
                return

            # 如果没有指定symbols，取消所有订阅
            if symbols is None:
                symbols = list(self.client_subscriptions[client_id])

            symbols_to_unsubscribe = []
            for symbol in symbols:
                if symbol in self.subscribers and client_id in self.subscribers[symbol]:
                    self.subscribers[symbol].remove(client_id)
                    self.client_subscriptions[client_id].discard(symbol)

                    # 如果没有其他客户端订阅这个合约，取消订阅
                    if not self.subscribers[symbol]:
                        del self.subscribers[symbol]
                        symbols_to_unsubscribe.append(symbol)

            # 清理空的客户端记录
            if not self.client_subscriptions[client_id]:
                del self.client_subscriptions[client_id]

            # 取消订阅没有客户端的合约
            if symbols_to_unsubscribe:
                await self.ctp_service.unsubscribe_market_data(symbols_to_unsubscribe)

            logger.info(f"客户端 {client_id} 取消订阅行情: {symbols}")

        except Exception as e:
            logger.error(f"取消订阅行情失败: {e}")
            raise

    def get_subscribers(self, symbol: str) -> set:
        """获取合约的订阅客户端"""
        return self.subscribers.get(symbol, set())

    def get_client_subscriptions(self, client_id: str) -> set:
        """获取客户端的订阅合约"""
        return self.client_subscriptions.get(client_id, set())

    # 监控系统集成方法
    def _record_metrics(self, operation: str, success: bool = True, duration: float = 0.0):
        """记录操作指标"""
        if self.metrics_collector:
            try:
                self.metrics_collector.record_operation(operation, success, duration)
                self.metrics_collector.update_connection_status(
                    self.status.trade_connected,
                    self.status.md_connected
                )
            except Exception as e:
                logger.warning(f"Failed to record metrics: {e}")

    def _check_alerts(self):
        """检查告警条件"""
        if self.alert_manager:
            try:
                # 检查连接状态
                if not self.status.trade_connected:
                    self.alert_manager.check_connection_alert("trade", False)
                if not self.status.md_connected:
                    self.alert_manager.check_connection_alert("md", False)

                # 检查错误率
                if self.status.error_count > 0:
                    error_rate = self.status.error_count / max(self.status.order_count, 1)
                    self.alert_manager.check_error_rate_alert(error_rate)

            except Exception as e:
                logger.warning(f"Failed to check alerts: {e}")

    async def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        status = {
            "service_status": {
                "trade_connected": self.status.trade_connected,
                "md_connected": self.status.md_connected,
                "trade_logged_in": self.status.trade_logged_in,
                "md_logged_in": self.status.md_logged_in,
                "is_ready": self.status.is_ready,
                "error_count": self.status.error_count,
                "order_count": self.status.order_count,
                "trade_count": self.status.trade_count
            }
        }

        if self.metrics_collector:
            status["metrics"] = await self.metrics_collector.get_current_metrics()

        if self.alert_manager:
            status["alerts"] = await self.alert_manager.get_active_alerts()

        return status


# 全局CTP服务实例
ctp_service = CTPService()
ctp_market_service = CTPMarketDataService(ctp_service)
