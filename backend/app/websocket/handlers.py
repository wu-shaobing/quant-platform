"""
WebSocket处理器
"""
import json
import logging
from typing import Dict, Any
from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .manager import websocket_manager
from app.core.database import get_async_session
from app.core.auth import get_current_user_from_websocket
from app.services.trading_service import TradingService
from app.services.market_data_service import MarketDataService
from app.models.user import User

logger = logging.getLogger(__name__)


async def handle_trading_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_user_from_websocket),
    db: AsyncSession = Depends(get_async_session)
):
    """处理交易WebSocket连接"""
    trading_service = TradingService(db)
    
    await websocket_manager.connect(websocket, user.id)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get('type')
            
            if message_type == 'subscribe_orders':
                # 订阅订单更新
                await websocket_manager.subscribe(websocket, f"orders_{user.id}")
                
                # 发送当前订单状态
                orders = await trading_service.get_orders(user.id, limit=50)
                await websocket_manager.send_to_connection(websocket, {
                    'type': 'orders_snapshot',
                    'data': [order.__dict__ for order in orders]
                })
            
            elif message_type == 'subscribe_positions':
                # 订阅持仓更新
                await websocket_manager.subscribe(websocket, f"positions_{user.id}")
                
                # 发送当前持仓状态
                positions = await trading_service.get_positions(user.id)
                await websocket_manager.send_to_connection(websocket, {
                    'type': 'positions_snapshot',
                    'data': [pos.__dict__ for pos in positions]
                })
            
            elif message_type == 'subscribe_trades':
                # 订阅成交更新
                await websocket_manager.subscribe(websocket, f"trades_{user.id}")
                
                # 发送最近成交记录
                trades = await trading_service.get_trades(user.id, limit=50)
                await websocket_manager.send_to_connection(websocket, {
                    'type': 'trades_snapshot',
                    'data': [trade.__dict__ for trade in trades]
                })
            
            elif message_type == 'submit_order':
                # 处理订单提交
                try:
                    order_data = message.get('data')
                    result = await trading_service.submit_order(user.id, order_data)
                    
                    await websocket_manager.send_to_connection(websocket, {
                        'type': 'order_submit_result',
                        'data': result
                    })
                    
                    # 如果订单提交成功，广播给订阅者
                    if result.get('success'):
                        await websocket_manager.broadcast_to_topic(
                            f"orders_{user.id}",
                            {
                                'type': 'order_update',
                                'data': result.get('data')
                            }
                        )
                
                except Exception as e:
                    await websocket_manager.send_to_connection(websocket, {
                        'type': 'error',
                        'message': f"订单提交失败: {str(e)}"
                    })
            
            elif message_type == 'cancel_order':
                # 处理订单撤销
                try:
                    order_id = message.get('order_id')
                    result = await trading_service.cancel_order(order_id)
                    
                    await websocket_manager.send_to_connection(websocket, {
                        'type': 'order_cancel_result',
                        'data': result
                    })
                    
                    # 广播订单状态更新
                    if result.get('success'):
                        await websocket_manager.broadcast_to_topic(
                            f"orders_{user.id}",
                            {
                                'type': 'order_cancelled',
                                'order_id': order_id
                            }
                        )
                
                except Exception as e:
                    await websocket_manager.send_to_connection(websocket, {
                        'type': 'error',
                        'message': f"订单撤销失败: {str(e)}"
                    })
            
            elif message_type == 'ping':
                # 心跳响应
                await websocket_manager.send_to_connection(websocket, {
                    'type': 'pong',
                    'timestamp': message.get('timestamp')
                })
            
            else:
                await websocket_manager.send_to_connection(websocket, {
                    'type': 'error',
                    'message': f"未知消息类型: {message_type}"
                })
    
    except WebSocketDisconnect:
        logger.info(f"用户 {user.id} 交易WebSocket连接断开")
    except Exception as e:
        logger.error(f"交易WebSocket处理错误: {e}")
    finally:
        await websocket_manager.disconnect(websocket)


async def handle_market_data_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_user_from_websocket),
    db: AsyncSession = Depends(get_async_session)
):
    """处理行情数据WebSocket连接"""
    market_service = MarketDataService(db)
    
    await websocket_manager.connect(websocket, user.id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get('type')
            
            if message_type == 'subscribe_tick':
                # 订阅实时行情
                symbols = message.get('symbols', [])
                for symbol in symbols:
                    await websocket_manager.subscribe(websocket, f"tick_{symbol}")
                
                await websocket_manager.send_to_connection(websocket, {
                    'type': 'tick_subscription_confirmed',
                    'symbols': symbols
                })
            
            elif message_type == 'subscribe_kline':
                # 订阅K线数据
                symbol = message.get('symbol')
                interval = message.get('interval', '1m')
                
                await websocket_manager.subscribe(websocket, f"kline_{symbol}_{interval}")
                
                # 发送历史K线数据
                klines = await market_service.get_kline_data(symbol, interval, limit=100)
                await websocket_manager.send_to_connection(websocket, {
                    'type': 'kline_snapshot',
                    'symbol': symbol,
                    'interval': interval,
                    'data': klines
                })
            
            elif message_type == 'unsubscribe':
                # 取消订阅
                topic = message.get('topic')
                await websocket_manager.unsubscribe(websocket, topic)
            
            elif message_type == 'ping':
                await websocket_manager.send_to_connection(websocket, {
                    'type': 'pong',
                    'timestamp': message.get('timestamp')
                })
    
    except WebSocketDisconnect:
        logger.info(f"用户 {user.id} 行情WebSocket连接断开")
    except Exception as e:
        logger.error(f"行情WebSocket处理错误: {e}")
    finally:
        await websocket_manager.disconnect(websocket)


async def handle_strategy_websocket(
    websocket: WebSocket,
    user: User = Depends(get_current_user_from_websocket),
    db: AsyncSession = Depends(get_async_session)
):
    """处理策略WebSocket连接"""
    await websocket_manager.connect(websocket, user.id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get('type')
            
            if message_type == 'subscribe_strategy_signals':
                # 订阅策略信号
                strategy_id = message.get('strategy_id')
                await websocket_manager.subscribe(websocket, f"strategy_signals_{strategy_id}")
            
            elif message_type == 'subscribe_backtest_progress':
                # 订阅回测进度
                task_id = message.get('task_id')
                await websocket_manager.subscribe(websocket, f"backtest_progress_{task_id}")
            
            elif message_type == 'ping':
                await websocket_manager.send_to_connection(websocket, {
                    'type': 'pong',
                    'timestamp': message.get('timestamp')
                })
    
    except WebSocketDisconnect:
        logger.info(f"用户 {user.id} 策略WebSocket连接断开")
    except Exception as e:
        logger.error(f"策略WebSocket处理错误: {e}")
    finally:
        await websocket_manager.disconnect(websocket)


# 事件广播函数
async def broadcast_order_update(user_id: int, order_data: Dict[str, Any]):
    """广播订单更新"""
    await websocket_manager.broadcast_to_topic(
        f"orders_{user_id}",
        {
            'type': 'order_update',
            'data': order_data
        }
    )


async def broadcast_trade_update(user_id: int, trade_data: Dict[str, Any]):
    """广播成交更新"""
    await websocket_manager.broadcast_to_topic(
        f"trades_{user_id}",
        {
            'type': 'trade_update',
            'data': trade_data
        }
    )


async def broadcast_position_update(user_id: int, position_data: Dict[str, Any]):
    """广播持仓更新"""
    await websocket_manager.broadcast_to_topic(
        f"positions_{user_id}",
        {
            'type': 'position_update',
            'data': position_data
        }
    )


async def broadcast_market_tick(symbol: str, tick_data: Dict[str, Any]):
    """广播实时行情"""
    await websocket_manager.broadcast_to_topic(
        f"tick_{symbol}",
        {
            'type': 'tick_update',
            'symbol': symbol,
            'data': tick_data
        }
    )


async def broadcast_kline_update(symbol: str, interval: str, kline_data: Dict[str, Any]):
    """广播K线更新"""
    await websocket_manager.broadcast_to_topic(
        f"kline_{symbol}_{interval}",
        {
            'type': 'kline_update',
            'symbol': symbol,
            'interval': interval,
            'data': kline_data
        }
    )
