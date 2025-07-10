"""
WebSocket实时通信服务
提供行情数据、交易状态、系统通知等实时推送功能
"""
import json
import asyncio
import logging
from typing import Dict, Set, List, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from app.core.config import settings
from app.core.monitoring import metrics_collector

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    """消息类型"""
    # 系统消息
    HEARTBEAT = "heartbeat"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    ERROR = "error"
    AUTH = "auth"
    
    # 行情数据
    MARKET_DATA = "market_data"
    KLINE_DATA = "kline_data"
    DEPTH_DATA = "depth_data"
    TRADE_TICK = "trade_tick"
    
    # 交易数据
    ORDER_UPDATE = "order_update"
    TRADE_UPDATE = "trade_update"
    POSITION_UPDATE = "position_update"
    ACCOUNT_UPDATE = "account_update"
    
    # 策略数据
    STRATEGY_STATUS = "strategy_status"
    BACKTEST_PROGRESS = "backtest_progress"
    
    # 风控数据
    RISK_ALERT = "risk_alert"
    
    # 系统通知
    NOTIFICATION = "notification"
    SYSTEM_STATUS = "system_status"


@dataclass
class WSMessage:
    """WebSocket消息"""
    type: str
    data: Any
    timestamp: datetime = None
    client_id: str = None
    channel: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "client_id": self.client_id,
            "channel": self.channel
        }
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class ConnectionManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接
        self.active_connections: Dict[str, WebSocket] = {}
        # 用户连接映射
        self.user_connections: Dict[int, Set[str]] = defaultdict(set)
        # 频道订阅
        self.channel_subscriptions: Dict[str, Set[str]] = defaultdict(set)
        # 连接元数据
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        # 心跳任务
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str, user_id: Optional[int] = None) -> bool:
        """建立连接"""
        try:
            await websocket.accept()
            
            # 检查连接数限制
            if len(self.active_connections) >= settings.WS_MAX_CONNECTIONS:
                await websocket.close(code=1013, reason="Too many connections")
                return False
            
            # 存储连接
            self.active_connections[client_id] = websocket
            
            # 用户关联
            if user_id:
                self.user_connections[user_id].add(client_id)
            
            # 存储元数据
            self.connection_metadata[client_id] = {
                "user_id": user_id,
                "connected_at": datetime.utcnow(),
                "last_heartbeat": datetime.utcnow(),
                "subscribed_channels": set()
            }
            
            # 启动心跳
            self.heartbeat_tasks[client_id] = asyncio.create_task(
                self._heartbeat_loop(client_id)
            )
            
            # 发送欢迎消息
            await self.send_personal_message(
                WSMessage(
                    type=MessageType.SYSTEM_STATUS,
                    data={"status": "connected", "client_id": client_id},
                    client_id=client_id
                ),
                client_id
            )
            
            # 更新指标
            metrics_collector.gauge_set("websocket_connections", len(self.active_connections))
            metrics_collector.counter_inc("websocket_connections_total")
            
            logger.info(f"WebSocket client {client_id} connected, user_id: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect client {client_id}: {e}")
            return False
    
    async def disconnect(self, client_id: str):
        """断开连接"""
        if client_id not in self.active_connections:
            return
        
        # 获取连接信息
        metadata = self.connection_metadata.get(client_id, {})
        user_id = metadata.get("user_id")
        
        # 取消心跳任务
        if client_id in self.heartbeat_tasks:
            self.heartbeat_tasks[client_id].cancel()
            del self.heartbeat_tasks[client_id]
        
        # 取消所有订阅
        subscribed_channels = metadata.get("subscribed_channels", set())
        for channel in subscribed_channels:
            self.channel_subscriptions[channel].discard(client_id)
        
        # 移除连接
        del self.active_connections[client_id]
        
        # 移除用户关联
        if user_id:
            self.user_connections[user_id].discard(client_id)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        
        # 移除元数据
        if client_id in self.connection_metadata:
            del self.connection_metadata[client_id]
        
        # 更新指标
        metrics_collector.gauge_set("websocket_connections", len(self.active_connections))
        metrics_collector.counter_inc("websocket_disconnections_total")
        
        logger.info(f"WebSocket client {client_id} disconnected")
    
    async def send_personal_message(self, message: WSMessage, client_id: str):
        """发送个人消息"""
        websocket = self.active_connections.get(client_id)
        if not websocket:
            return False
        
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(message.to_json())
                metrics_collector.counter_inc("websocket_messages_sent")
                return True
        except Exception as e:
            logger.error(f"Failed to send message to {client_id}: {e}")
            await self.disconnect(client_id)
        
        return False
    
    async def send_to_user(self, message: WSMessage, user_id: int):
        """发送消息给用户的所有连接"""
        client_ids = self.user_connections.get(user_id, set())
        tasks = [
            self.send_personal_message(message, client_id)
            for client_id in client_ids
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_channel(self, message: WSMessage, channel: str):
        """向频道广播消息"""
        client_ids = self.channel_subscriptions.get(channel, set())
        if not client_ids:
            return
        
        message.channel = channel
        tasks = [
            self.send_personal_message(message, client_id)
            for client_id in client_ids
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        metrics_collector.counter_inc("websocket_broadcast_messages", len(tasks))
    
    async def broadcast_to_all(self, message: WSMessage):
        """向所有连接广播消息"""
        tasks = [
            self.send_personal_message(message, client_id)
            for client_id in self.active_connections.keys()
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def subscribe_channel(self, client_id: str, channel: str) -> bool:
        """订阅频道"""
        if client_id not in self.active_connections:
            return False
        
        self.channel_subscriptions[channel].add(client_id)
        self.connection_metadata[client_id]["subscribed_channels"].add(channel)
        
        metrics_collector.counter_inc("websocket_subscriptions")
        logger.debug(f"Client {client_id} subscribed to channel {channel}")
        return True
    
    def unsubscribe_channel(self, client_id: str, channel: str) -> bool:
        """取消订阅频道"""
        if client_id not in self.active_connections:
            return False
        
        self.channel_subscriptions[channel].discard(client_id)
        self.connection_metadata[client_id]["subscribed_channels"].discard(channel)
        
        metrics_collector.counter_inc("websocket_unsubscriptions")
        logger.debug(f"Client {client_id} unsubscribed from channel {channel}")
        return True
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return {
            "total_connections": len(self.active_connections),
            "total_users": len(self.user_connections),
            "total_channels": len(self.channel_subscriptions),
            "channels": {
                channel: len(clients) 
                for channel, clients in self.channel_subscriptions.items()
            },
            "connections": [
                {
                    "client_id": client_id,
                    "user_id": metadata.get("user_id"),
                    "connected_at": metadata.get("connected_at").isoformat() if metadata.get("connected_at") else None,
                    "subscribed_channels": list(metadata.get("subscribed_channels", set()))
                }
                for client_id, metadata in self.connection_metadata.items()
            ]
        }
    
    async def _heartbeat_loop(self, client_id: str):
        """心跳循环"""
        while client_id in self.active_connections:
            try:
                await asyncio.sleep(settings.WS_HEARTBEAT_INTERVAL)
                
                # 发送心跳
                await self.send_personal_message(
                    WSMessage(
                        type=MessageType.HEARTBEAT,
                        data={"timestamp": datetime.utcnow().isoformat()},
                        client_id=client_id
                    ),
                    client_id
                )
                
                # 更新心跳时间
                if client_id in self.connection_metadata:
                    self.connection_metadata[client_id]["last_heartbeat"] = datetime.utcnow()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error for client {client_id}: {e}")
                await self.disconnect(client_id)
                break


class WebSocketService:
    """WebSocket服务"""
    
    def __init__(self):
        self.manager = ConnectionManager()
        self.message_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认消息处理器"""
        self.message_handlers[MessageType.SUBSCRIBE] = self._handle_subscribe
        self.message_handlers[MessageType.UNSUBSCRIBE] = self._handle_unsubscribe
        self.message_handlers[MessageType.HEARTBEAT] = self._handle_heartbeat
    
    async def handle_connection(self, websocket: WebSocket, client_id: str, user_id: Optional[int] = None):
        """处理WebSocket连接"""
        # 建立连接
        if not await self.manager.connect(websocket, client_id, user_id):
            return
        
        try:
            while True:
                # 接收消息
                data = await websocket.receive_text()
                await self._process_message(data, client_id)
                
        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected normally")
        except Exception as e:
            logger.error(f"WebSocket error for client {client_id}: {e}")
        finally:
            await self.manager.disconnect(client_id)
    
    async def _process_message(self, data: str, client_id: str):
        """处理收到的消息"""
        try:
            message_data = json.loads(data)
            message_type = message_data.get("type")
            
            if message_type in self.message_handlers:
                await self.message_handlers[message_type](message_data, client_id)
            else:
                await self.manager.send_personal_message(
                    WSMessage(
                        type=MessageType.ERROR,
                        data={"error": "unknown_message_type", "type": message_type},
                        client_id=client_id
                    ),
                    client_id
                )
            
            metrics_collector.counter_inc("websocket_messages_received")
            
        except json.JSONDecodeError:
            await self.manager.send_personal_message(
                WSMessage(
                    type=MessageType.ERROR,
                    data={"error": "invalid_json"},
                    client_id=client_id
                ),
                client_id
            )
        except Exception as e:
            logger.error(f"Error processing message from {client_id}: {e}")
            await self.manager.send_personal_message(
                WSMessage(
                    type=MessageType.ERROR,
                    data={"error": "processing_error", "message": str(e)},
                    client_id=client_id
                ),
                client_id
            )
    
    async def _handle_subscribe(self, message_data: Dict[str, Any], client_id: str):
        """处理订阅消息"""
        channel = message_data.get("channel")
        if not channel:
            await self.manager.send_personal_message(
                WSMessage(
                    type=MessageType.ERROR,
                    data={"error": "missing_channel"},
                    client_id=client_id
                ),
                client_id
            )
            return
        
        success = self.manager.subscribe_channel(client_id, channel)
        await self.manager.send_personal_message(
            WSMessage(
                type=MessageType.SUBSCRIBE,
                data={"channel": channel, "success": success},
                client_id=client_id
            ),
            client_id
        )
    
    async def _handle_unsubscribe(self, message_data: Dict[str, Any], client_id: str):
        """处理取消订阅消息"""
        channel = message_data.get("channel")
        if not channel:
            await self.manager.send_personal_message(
                WSMessage(
                    type=MessageType.ERROR,
                    data={"error": "missing_channel"},
                    client_id=client_id
                ),
                client_id
            )
            return
        
        success = self.manager.unsubscribe_channel(client_id, channel)
        await self.manager.send_personal_message(
            WSMessage(
                type=MessageType.UNSUBSCRIBE,
                data={"channel": channel, "success": success},
                client_id=client_id
            ),
            client_id
        )
    
    async def _handle_heartbeat(self, message_data: Dict[str, Any], client_id: str):
        """处理心跳消息"""
        # 更新心跳时间
        if client_id in self.manager.connection_metadata:
            self.manager.connection_metadata[client_id]["last_heartbeat"] = datetime.utcnow()
    
    def register_handler(self, message_type: str, handler: Callable):
        """注册消息处理器"""
        self.message_handlers[message_type] = handler
    
    # 业务方法
    async def send_market_data(self, symbol: str, data: Dict[str, Any]):
        """发送行情数据"""
        message = WSMessage(
            type=MessageType.MARKET_DATA,
            data={"symbol": symbol, **data}
        )
        await self.manager.broadcast_to_channel(message, f"market.{symbol}")
        await self.manager.broadcast_to_channel(message, "market.all")
    
    async def send_order_update(self, user_id: int, order_data: Dict[str, Any]):
        """发送订单更新"""
        message = WSMessage(
            type=MessageType.ORDER_UPDATE,
            data=order_data
        )
        await self.manager.send_to_user(message, user_id)
    
    async def send_trade_update(self, user_id: int, trade_data: Dict[str, Any]):
        """发送成交更新"""
        message = WSMessage(
            type=MessageType.TRADE_UPDATE,
            data=trade_data
        )
        await self.manager.send_to_user(message, user_id)
    
    async def send_position_update(self, user_id: int, position_data: Dict[str, Any]):
        """发送持仓更新"""
        message = WSMessage(
            type=MessageType.POSITION_UPDATE,
            data=position_data
        )
        await self.manager.send_to_user(message, user_id)
    
    async def send_risk_alert(self, user_id: int, alert_data: Dict[str, Any]):
        """发送风险警报"""
        message = WSMessage(
            type=MessageType.RISK_ALERT,
            data=alert_data
        )
        await self.manager.send_to_user(message, user_id)
    
    async def send_system_notification(self, notification_data: Dict[str, Any], target_users: Optional[List[int]] = None):
        """发送系统通知"""
        message = WSMessage(
            type=MessageType.NOTIFICATION,
            data=notification_data
        )
        
        if target_users:
            for user_id in target_users:
                await self.manager.send_to_user(message, user_id)
        else:
            await self.manager.broadcast_to_all(message)
    
    async def send_backtest_progress(self, user_id: int, progress_data: Dict[str, Any]):
        """发送回测进度"""
        message = WSMessage(
            type=MessageType.BACKTEST_PROGRESS,
            data=progress_data
        )
        await self.manager.send_to_user(message, user_id)
    
    def get_connection_info(self) -> Dict[str, Any]:
        """获取连接信息"""
        return self.manager.get_connection_info()


# 全局WebSocket服务实例
ws_service = WebSocketService()


# WebSocket端点函数
async def websocket_endpoint(websocket: WebSocket, client_id: str = None, user_id: int = None):
    """
    WebSocket端点
    
    Args:
        websocket: WebSocket连接
        client_id: 客户端ID
        user_id: 用户ID
    """
    if not client_id:
        # 如果没有提供client_id，生成一个
        import uuid
        client_id = str(uuid.uuid4())
    
    await ws_service.handle_connection(websocket, client_id, user_id)


# 简单的WebSocket端点（无需认证）
async def simple_websocket_endpoint(websocket: WebSocket):
    """
    简单的WebSocket端点，无需认证
    """
    await websocket.accept()
    
    # 发送欢迎消息
    await websocket.send_json({
        "type": "connected",
        "message": "WebSocket连接成功",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type", "unknown")
                
                # 处理不同类型的消息
                if message_type == "ping":
                    # 心跳响应
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                elif message_type == "echo":
                    # 回显消息
                    await websocket.send_json({
                        "type": "echo",
                        "data": message.get("data", ""),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                else:
                    # 未知消息类型
                    await websocket.send_json({
                        "type": "error",
                        "message": f"未知消息类型: {message_type}",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "无效的JSON格式",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info("WebSocket连接正常断开")
    except Exception as e:
        logger.error(f"WebSocket连接错误: {e}")
    finally:
        logger.info("WebSocket连接已关闭")


# 频道常量
class Channels:
    """预定义频道"""
    MARKET_ALL = "market.all"
    MARKET_STOCK = "market.stock"
    MARKET_FUTURES = "market.futures"
    MARKET_CRYPTO = "market.crypto"
    
    SYSTEM_STATUS = "system.status"
    SYSTEM_ALERTS = "system.alerts"
    
    @staticmethod
    def market_symbol(symbol: str) -> str:
        """获取特定标的的行情频道"""
        return f"market.{symbol}"
    
    @staticmethod
    def user_private(user_id: int) -> str:
        """获取用户私有频道"""
        return f"user.{user_id}" 

# WebSocket端点函数
async def websocket_endpoint(websocket: WebSocket, client_id: str = None, user_id: int = None):
    """
    WebSocket端点
    
    Args:
        websocket: WebSocket连接
        client_id: 客户端ID
        user_id: 用户ID
    """
    if not client_id:
        # 如果没有提供client_id，生成一个
        import uuid
        client_id = str(uuid.uuid4())
    
    await ws_service.handle_connection(websocket, client_id, user_id)


# 创建全局WebSocket管理器实例
websocket_manager = WebSocketService()