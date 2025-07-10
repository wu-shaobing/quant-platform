"""
WebSocket连接管理器
"""
import json
import logging
from typing import Dict, List, Set, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self):
        # 活跃连接 {user_id: [websockets]}
        self.active_connections: Dict[int, List[WebSocket]] = defaultdict(list)
        
        # 订阅管理 {topic: {user_id: [websockets]}}
        self.subscriptions: Dict[str, Dict[int, List[WebSocket]]] = defaultdict(lambda: defaultdict(list))
        
        # 连接元数据 {websocket: {'user_id': int, 'subscriptions': set}}
        self.connection_meta: Dict[WebSocket, Dict] = {}
        
        # 心跳管理
        self.heartbeat_tasks: Dict[WebSocket, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """建立WebSocket连接"""
        try:
            await websocket.accept()
            
            # 添加到活跃连接
            self.active_connections[user_id].append(websocket)
            
            # 初始化连接元数据
            self.connection_meta[websocket] = {
                'user_id': user_id,
                'subscriptions': set(),
                'connected_at': asyncio.get_event_loop().time()
            }
            
            # 启动心跳
            self.heartbeat_tasks[websocket] = asyncio.create_task(
                self._heartbeat_loop(websocket)
            )
            
            logger.info(f"用户 {user_id} WebSocket连接建立")
            
            # 发送连接确认
            await self.send_to_connection(websocket, {
                'type': 'connection_established',
                'user_id': user_id,
                'timestamp': asyncio.get_event_loop().time()
            })
            
        except Exception as e:
            logger.error(f"WebSocket连接失败: {e}")
            await self.disconnect(websocket)
    
    async def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        try:
            if websocket in self.connection_meta:
                meta = self.connection_meta[websocket]
                user_id = meta['user_id']
                subscriptions = meta['subscriptions']
                
                # 从活跃连接中移除
                if user_id in self.active_connections:
                    if websocket in self.active_connections[user_id]:
                        self.active_connections[user_id].remove(websocket)
                    
                    # 如果用户没有其他连接，清理用户记录
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                
                # 从订阅中移除
                for topic in subscriptions:
                    if topic in self.subscriptions and user_id in self.subscriptions[topic]:
                        if websocket in self.subscriptions[topic][user_id]:
                            self.subscriptions[topic][user_id].remove(websocket)
                        
                        # 清理空的订阅记录
                        if not self.subscriptions[topic][user_id]:
                            del self.subscriptions[topic][user_id]
                        if not self.subscriptions[topic]:
                            del self.subscriptions[topic]
                
                # 停止心跳任务
                if websocket in self.heartbeat_tasks:
                    self.heartbeat_tasks[websocket].cancel()
                    del self.heartbeat_tasks[websocket]
                
                # 清理连接元数据
                del self.connection_meta[websocket]
                
                logger.info(f"用户 {user_id} WebSocket连接断开")
        
        except Exception as e:
            logger.error(f"WebSocket断开处理失败: {e}")
    
    async def subscribe(self, websocket: WebSocket, topic: str):
        """订阅主题"""
        if websocket not in self.connection_meta:
            return False
        
        user_id = self.connection_meta[websocket]['user_id']
        
        # 添加到订阅
        self.subscriptions[topic][user_id].append(websocket)
        self.connection_meta[websocket]['subscriptions'].add(topic)
        
        logger.info(f"用户 {user_id} 订阅主题: {topic}")
        
        # 发送订阅确认
        await self.send_to_connection(websocket, {
            'type': 'subscription_confirmed',
            'topic': topic,
            'timestamp': asyncio.get_event_loop().time()
        })
        
        return True
    
    async def unsubscribe(self, websocket: WebSocket, topic: str):
        """取消订阅主题"""
        if websocket not in self.connection_meta:
            return False
        
        user_id = self.connection_meta[websocket]['user_id']
        
        # 从订阅中移除
        if topic in self.subscriptions and user_id in self.subscriptions[topic]:
            if websocket in self.subscriptions[topic][user_id]:
                self.subscriptions[topic][user_id].remove(websocket)
            
            if not self.subscriptions[topic][user_id]:
                del self.subscriptions[topic][user_id]
            if not self.subscriptions[topic]:
                del self.subscriptions[topic]
        
        # 从连接元数据中移除
        self.connection_meta[websocket]['subscriptions'].discard(topic)
        
        logger.info(f"用户 {user_id} 取消订阅主题: {topic}")
        
        # 发送取消订阅确认
        await self.send_to_connection(websocket, {
            'type': 'unsubscription_confirmed',
            'topic': topic,
            'timestamp': asyncio.get_event_loop().time()
        })
        
        return True
    
    async def send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]):
        """发送消息到指定连接"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            await self.disconnect(websocket)
    
    async def send_to_user(self, user_id: int, message: Dict[str, Any]):
        """发送消息到指定用户的所有连接"""
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(message, default=str))
                except Exception as e:
                    logger.error(f"发送消息到用户 {user_id} 失败: {e}")
                    disconnected.append(websocket)
            
            # 清理断开的连接
            for websocket in disconnected:
                await self.disconnect(websocket)
    
    async def broadcast_to_topic(self, topic: str, message: Dict[str, Any]):
        """广播消息到订阅指定主题的所有用户"""
        if topic in self.subscriptions:
            disconnected = []
            for user_id, websockets in self.subscriptions[topic].items():
                for websocket in websockets:
                    try:
                        await websocket.send_text(json.dumps(message, default=str))
                    except Exception as e:
                        logger.error(f"广播消息到主题 {topic} 失败: {e}")
                        disconnected.append(websocket)
            
            # 清理断开的连接
            for websocket in disconnected:
                await self.disconnect(websocket)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """广播消息到所有连接"""
        disconnected = []
        for user_id, websockets in self.active_connections.items():
            for websocket in websockets:
                try:
                    await websocket.send_text(json.dumps(message, default=str))
                except Exception as e:
                    logger.error(f"广播消息失败: {e}")
                    disconnected.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected:
            await self.disconnect(websocket)
    
    async def _heartbeat_loop(self, websocket: WebSocket):
        """心跳循环"""
        try:
            while True:
                await asyncio.sleep(30)  # 30秒心跳间隔
                await self.send_to_connection(websocket, {
                    'type': 'heartbeat',
                    'timestamp': asyncio.get_event_loop().time()
                })
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"心跳失败: {e}")
            await self.disconnect(websocket)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        total_subscriptions = sum(
            sum(len(connections) for connections in topic_subs.values())
            for topic_subs in self.subscriptions.values()
        )
        
        return {
            'total_users': len(self.active_connections),
            'total_connections': total_connections,
            'total_subscriptions': total_subscriptions,
            'topics': list(self.subscriptions.keys()),
            'active_users': list(self.active_connections.keys())
        }


# 全局WebSocket管理器实例
websocket_manager = WebSocketManager()
