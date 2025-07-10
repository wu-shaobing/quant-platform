"""
CTP WebSocket接口
"""
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user_from_websocket
from app.models.user import User
from app.services.ctp_service import ctp_service, ctp_market_service
from app.core.websocket import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/ctp/{client_id}")
async def ctp_websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    token: Optional[str] = None
):
    """
    CTP WebSocket连接端点
    
    支持以下消息类型:
    - subscribe_market: 订阅行情数据
    - unsubscribe_market: 取消订阅行情数据
    - get_status: 获取CTP状态
    - ping: 心跳检测
    """
    user = None
    
    try:
        # 验证用户身份（如果提供了token）
        if token:
            # 这里应该验证token并获取用户信息
            # user = await get_current_user_from_websocket(token)
            pass
        
        # 建立WebSocket连接
        await websocket.accept()
        logger.info(f"CTP WebSocket连接建立: {client_id}")
        
        # 注册连接到管理器
        user_id = user.id if user else None
        await websocket_manager.connect(websocket, client_id, user_id)
        
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "client_id": client_id,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # 启动行情数据推送任务
        market_task = asyncio.create_task(
            _market_data_pusher(websocket, client_id)
        )
        
        # 消息处理循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理消息
                response = await _handle_message(message, client_id, user)
                
                # 发送响应
                if response:
                    await websocket.send_json(response)
                    
            except WebSocketDisconnect:
                logger.info(f"CTP WebSocket连接断开: {client_id}")
                break
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "message": "无效的JSON格式",
                    "timestamp": asyncio.get_event_loop().time()
                })
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": f"处理消息失败: {str(e)}",
                    "timestamp": asyncio.get_event_loop().time()
                })
    
    except Exception as e:
        logger.error(f"CTP WebSocket连接失败: {e}")
    
    finally:
        # 清理连接
        try:
            # 取消行情推送任务
            if 'market_task' in locals():
                market_task.cancel()
            
            # 取消订阅所有行情
            await ctp_market_service.unsubscribe(client_id)
            
            # 从管理器移除连接
            await websocket_manager.disconnect(client_id)
            
            logger.info(f"CTP WebSocket连接清理完成: {client_id}")
            
        except Exception as e:
            logger.error(f"清理WebSocket连接失败: {e}")


async def _handle_message(message: Dict[str, Any], client_id: str, user: Optional[User]) -> Optional[Dict[str, Any]]:
    """处理WebSocket消息"""
    try:
        msg_type = message.get("type")
        data = message.get("data", {})
        request_id = message.get("request_id")
        
        response = {
            "type": f"{msg_type}_response",
            "request_id": request_id,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        if msg_type == "subscribe_market":
            # 订阅行情数据
            symbols = data.get("symbols", [])
            if not symbols:
                response["success"] = False
                response["message"] = "symbols参数不能为空"
            else:
                try:
                    await ctp_market_service.subscribe(client_id, symbols)
                    response["success"] = True
                    response["message"] = f"订阅行情成功: {symbols}"
                    response["data"] = {"symbols": symbols}
                except Exception as e:
                    response["success"] = False
                    response["message"] = f"订阅行情失败: {str(e)}"
        
        elif msg_type == "unsubscribe_market":
            # 取消订阅行情数据
            symbols = data.get("symbols")
            try:
                await ctp_market_service.unsubscribe(client_id, symbols)
                response["success"] = True
                response["message"] = f"取消订阅成功: {symbols or '全部'}"
                response["data"] = {"symbols": symbols}
            except Exception as e:
                response["success"] = False
                response["message"] = f"取消订阅失败: {str(e)}"
        
        elif msg_type == "get_status":
            # 获取CTP状态
            try:
                status = ctp_service.get_status()
                response["success"] = True
                response["data"] = {
                    "trade_connected": status.trade_connected,
                    "md_connected": status.md_connected,
                    "trade_logged_in": status.trade_logged_in,
                    "md_logged_in": status.md_logged_in,
                    "is_ready": status.is_ready,
                    "last_error": status.last_error,
                    "error_count": status.error_count,
                    "order_count": status.order_count,
                    "trade_count": status.trade_count,
                    "subscribe_count": status.subscribe_count
                }
            except Exception as e:
                response["success"] = False
                response["message"] = f"获取状态失败: {str(e)}"
        
        elif msg_type == "get_tick":
            # 获取最新行情
            symbol = data.get("symbol")
            if not symbol:
                response["success"] = False
                response["message"] = "symbol参数不能为空"
            else:
                try:
                    tick_data = await ctp_service.get_tick_data(symbol)
                    response["success"] = True
                    response["data"] = tick_data
                except Exception as e:
                    response["success"] = False
                    response["message"] = f"获取行情失败: {str(e)}"
        
        elif msg_type == "ping":
            # 心跳检测
            response["type"] = "pong"
            response["success"] = True
            response["message"] = "pong"
        
        else:
            response["success"] = False
            response["message"] = f"未知的消息类型: {msg_type}"
        
        return response
        
    except Exception as e:
        logger.error(f"处理消息失败: {e}")
        return {
            "type": "error",
            "message": f"处理消息失败: {str(e)}",
            "timestamp": asyncio.get_event_loop().time()
        }


async def _market_data_pusher(websocket: WebSocket, client_id: str):
    """行情数据推送任务"""
    try:
        while True:
            # 获取客户端订阅的合约
            subscribed_symbols = ctp_market_service.get_client_subscriptions(client_id)
            
            if subscribed_symbols:
                # 推送行情数据
                for symbol in subscribed_symbols:
                    try:
                        tick_data = await ctp_service.get_tick_data(symbol)
                        if tick_data:
                            await websocket.send_json({
                                "type": "market_data",
                                "symbol": symbol,
                                "data": tick_data,
                                "timestamp": asyncio.get_event_loop().time()
                            })
                    except Exception as e:
                        logger.error(f"推送行情数据失败 {symbol}: {e}")
            
            # 等待一段时间再推送下一批数据
            await asyncio.sleep(1)  # 1秒推送一次
            
    except asyncio.CancelledError:
        logger.info(f"行情推送任务已取消: {client_id}")
    except Exception as e:
        logger.error(f"行情推送任务异常: {e}")


class CTPWebSocketManager:
    """CTP WebSocket管理器"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, set] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str, user_id: Optional[int] = None):
        """建立连接"""
        self.connections[client_id] = websocket
        
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(client_id)
    
    async def disconnect(self, client_id: str):
        """断开连接"""
        if client_id in self.connections:
            del self.connections[client_id]
        
        # 清理用户连接映射
        for user_id, client_ids in self.user_connections.items():
            client_ids.discard(client_id)
        
        # 清理空的用户记录
        self.user_connections = {
            user_id: client_ids 
            for user_id, client_ids in self.user_connections.items() 
            if client_ids
        }
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """发送消息给指定客户端"""
        if client_id in self.connections:
            try:
                await self.connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"发送消息失败 {client_id}: {e}")
                await self.disconnect(client_id)
    
    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        """发送消息给指定用户的所有连接"""
        if user_id in self.user_connections:
            for client_id in self.user_connections[user_id].copy():
                await self.send_to_client(client_id, message)
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息给所有连接"""
        for client_id in list(self.connections.keys()):
            await self.send_to_client(client_id, message)
    
    def get_connection_count(self) -> int:
        """获取连接数量"""
        return len(self.connections)
    
    def get_user_connection_count(self, user_id: int) -> int:
        """获取用户连接数量"""
        return len(self.user_connections.get(user_id, set()))


# 全局CTP WebSocket管理器
ctp_websocket_manager = CTPWebSocketManager()


# 注册CTP回调函数
async def _on_tick_callback(tick_data: Dict[str, Any]):
    """行情数据回调"""
    symbol = tick_data.get("symbol")
    if symbol:
        # 获取订阅该合约的客户端
        subscribers = ctp_market_service.get_subscribers(symbol)
        
        # 推送给所有订阅客户端
        for client_id in subscribers:
            await ctp_websocket_manager.send_to_client(client_id, {
                "type": "tick_data",
                "symbol": symbol,
                "data": tick_data,
                "timestamp": asyncio.get_event_loop().time()
            })


async def _on_order_callback(order_data: Dict[str, Any]):
    """订单回报回调"""
    user_id = order_data.get("user_id")
    if user_id:
        await ctp_websocket_manager.send_to_user(user_id, {
            "type": "order_update",
            "data": order_data,
            "timestamp": asyncio.get_event_loop().time()
        })


async def _on_trade_callback(trade_data: Dict[str, Any]):
    """成交回报回调"""
    user_id = trade_data.get("user_id")
    if user_id:
        await ctp_websocket_manager.send_to_user(user_id, {
            "type": "trade_update",
            "data": trade_data,
            "timestamp": asyncio.get_event_loop().time()
        })


# 注册回调函数
ctp_service.add_callback('on_tick', _on_tick_callback)
ctp_service.add_callback('on_order', _on_order_callback)
ctp_service.add_callback('on_trade', _on_trade_callback)
