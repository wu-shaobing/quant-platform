# 18-WebSocket文档

## WebSocket概述

### 技术实现
- **后端**: FastAPI原生WebSocket支持
- **前端**: 原生WebSocket API (非Socket.IO)
- **协议**: JSON消息格式，自定义协议
- **认证**: JWT Token认证机制

### 应用场景
- **实时行情推送**：股票、期货价格实时更新
- **订单状态更新**：交易订单状态变化通知
- **账户资金变动**：持仓、资金实时同步
- **策略信号推送**：量化策略买卖信号通知
- **系统消息通知**：重要公告、风险提醒

### 技术优势
- **低延迟**：毫秒级数据推送 (< 10ms)
- **双向通信**：服务端主动推送数据
- **连接复用**：单连接多频道订阅
- **自动重连**：网络断线自动恢复
- **原生兼容**：前后端使用原生WebSocket，无第三方依赖

## 连接建立

### 连接地址
```
开发环境: ws://localhost:8000/ws
生产环境: wss://api.your-domain.com/ws
```

### 前端连接示例
```javascript
// 前端原生WebSocket连接
const socket = new WebSocket('ws://localhost:8000/ws');

socket.onopen = function(event) {
    console.log('WebSocket连接已建立');
    
    // 发送认证消息
    const authMessage = {
        type: 'auth',
        data: {
            token: localStorage.getItem('access_token')
        }
    };
    socket.send(JSON.stringify(authMessage));
};

socket.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('收到消息:', message);
    
    // 处理不同类型的消息
    switch(message.type) {
        case 'auth_response':
            handleAuthResponse(message);
            break;
        case 'market_data':
            handleMarketData(message);
            break;
        case 'order_update':
            handleOrderUpdate(message);
            break;
    }
};

socket.onerror = function(error) {
    console.error('WebSocket错误:', error);
};

socket.onclose = function(event) {
    console.log('WebSocket连接已关闭');
    // 实现重连逻辑
    setTimeout(() => {
        reconnect();
    }, 3000);
};
```

### 后端实现
```python
# app/api/v1/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import websocket_manager
from app.websocket.handlers import handle_message
import uuid
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    connection_id = str(uuid.uuid4())
    
    try:
        await websocket_manager.connect(websocket, connection_id)
        logger.info(f"新的WebSocket连接: {connection_id}")
        
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理消息
            await handle_message(connection_id, message)
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket连接断开: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket错误: {connection_id}, 错误: {e}")
    finally:
        await websocket_manager.disconnect(connection_id)
```

## 消息协议

### 消息格式
```json
{
  "type": "message_type",
  "channel": "channel_name",
  "data": {},
  "timestamp": "2023-12-01T10:30:00Z",
  "sequence": 12345
}
```

### 消息类型

#### 1. 认证消息
```json
// 客户端发送
{
  "type": "auth",
  "data": {
    "token": "<access_token>"
  }
}

// 服务端响应
{
  "type": "auth_response",
  "data": {
    "status": "success",
    "user_id": 1,
    "permissions": ["read:market_data", "place:order"]
  },
  "timestamp": "2023-12-01T10:30:00Z"
}
```

#### 2. 订阅消息
```json
// 订阅行情
{
  "type": "subscribe",
  "channel": "market_data",
  "symbols": ["SHFE.rb2405", "SHFE.hc2405"],
  "fields": ["last_price", "volume", "bid", "ask"]
}

// 订阅订单更新
{
  "type": "subscribe",
  "channel": "orders",
  "user_id": 1
}

// 订阅策略信号
{
  "type": "subscribe",
  "channel": "strategy_signals",
  "strategy_id": "STR_20231201_001"
}
```

#### 3. 取消订阅
```json
{
  "type": "unsubscribe",
  "channel": "market_data",
  "symbols": ["SHFE.rb2405"]
}
```

#### 4. 心跳消息
```json
// 客户端发送
{
  "type": "ping",
  "timestamp": "2023-12-01T10:30:00Z"
}

// 服务端响应
{
  "type": "pong",
  "timestamp": "2023-12-01T10:30:00Z"
}
```

## 数据推送

### 1. 实时行情推送

**Tick数据**:
```json
{
  "type": "market_data",
  "channel": "tick",
  "symbol": "SHFE.rb2405",
  "data": {
    "last_price": "4000.0",
    "bid_price": "3999.0",
    "ask_price": "4001.0",
    "bid_volume": "10",
    "ask_volume": "15",
    "volume": "1000",
    "turnover": "3995000.0",
    "open_interest": "5000",
    "change": "10.0",
    "change_percent": "0.25"
  },
  "timestamp": "2023-12-01T10:30:00.123Z"
}
```

**K线数据**:
```json
{
  "type": "kline",
  "channel": "kline_1m",
  "symbol": "SHFE.rb2405",
  "data": {
    "open": "3990.0",
    "high": "4010.0",
    "low": "3985.0",
    "close": "4000.0",
    "volume": "500",
    "turnover": "1997500.0",
    "start_time": "2023-12-01T10:30:00Z",
    "end_time": "2023-12-01T10:31:00Z"
  }
}
```

**深度行情**:
```json
{
  "type": "depth",
  "channel": "depth",
  "symbol": "SHFE.rb2405",
  "data": {
    "bids": [
      ["3999.0", "10"],
      ["3998.0", "20"],
      ["3997.0", "15"]
    ],
    "asks": [
      ["4001.0", "15"],
      ["4002.0", "25"],
      ["4003.0", "30"]
    ]
  },
  "timestamp": "2023-12-01T10:30:00Z"
}
```

### 2. 交易状态推送

**订单更新**:
```json
{
  "type": "order_update",
  "channel": "orders",
  "data": {
    "order_id": "ORD_20231201_001",
    "symbol": "SHFE.rb2405",
    "side": "BUY",
    "quantity": "1.0",
    "price": "4000.0",
    "status": "FILLED",
    "filled_quantity": "1.0",
    "filled_price": "4000.0",
    "updated_at": "2023-12-01T10:30:00Z"
  }
}
```

**持仓更新**:
```json
{
  "type": "position_update",
  "channel": "positions",
  "data": {
    "symbol": "SHFE.rb2405",
    "side": "LONG",
    "quantity": "5.0",
    "avg_price": "3980.0",
    "market_value": "20000.0",
    "unrealized_pnl": "100.0",
    "updated_at": "2023-12-01T10:30:00Z"
  }
}
```

**资金更新**:
```json
{
  "type": "account_update",
  "channel": "account",
  "data": {
    "total_assets": "100000.0",
    "available_cash": "50000.0",
    "frozen_cash": "5000.0",
    "market_value": "45000.0",
    "updated_at": "2023-12-01T10:30:00Z"
  }
}
```

### 3. 策略信号推送

**买卖信号**:
```json
{
  "type": "strategy_signal",
  "channel": "signals",
  "data": {
    "strategy_id": "STR_20231201_001",
    "strategy_name": "MACD策略",
    "symbol": "SHFE.rb2405",
    "signal": "BUY",
    "price": "4000.0",
    "quantity": "1.0",
    "confidence": 0.85,
    "reason": "MACD金叉，看涨信号",
    "timestamp": "2023-12-01T10:30:00Z"
  }
}
```

### 4. 系统消息推送

**风险提醒**:
```json
{
  "type": "risk_alert",
  "channel": "notifications",
  "data": {
    "level": "WARNING",
    "title": "持仓风险提醒",
    "message": "螺纹钢持仓已达到风控上限",
    "symbol": "SHFE.rb2405",
    "current_position": "10.0",
    "max_position": "10.0",
    "timestamp": "2023-12-01T10:30:00Z"
  }
}
```

## 客户端实现

### 1. JavaScript/TypeScript实现

```javascript
class QuantWebSocket {
  constructor(url, token) {
    this.url = url;
    this.token = token;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectInterval = 1000;
    this.subscriptions = new Map();
    this.messageHandlers = new Map();
    this.heartbeatInterval = null;
  }

  // 连接WebSocket
  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('WebSocket连接成功');
        this.authenticate().then(() => {
          this.startHeartbeat();
          this.reconnectAttempts = 0;
          resolve();
        }).catch(reject);
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('解析消息失败:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket连接关闭:', event.code, event.reason);
        this.stopHeartbeat();
        if (!event.wasClean) {
          this.reconnect();
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
        reject(error);
      };
    });
  }

  // 认证
  async authenticate() {
    return new Promise((resolve, reject) => {
      const authMessage = {
        type: 'auth',
        token: this.token
      };
      
      this.send(authMessage);
      
      // 等待认证响应
      const timeout = setTimeout(() => {
        reject(new Error('认证超时'));
      }, 5000);
      
      this.once('auth_response', (data) => {
        clearTimeout(timeout);
        if (data.status === 'success') {
          resolve(data);
        } else {
          reject(new Error('认证失败'));
        }
      });
    });
  }

  // 发送消息
  send(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket未连接，无法发送消息');
    }
  }

  // 订阅频道
  subscribe(channel, options = {}) {
    const message = {
      type: 'subscribe',
      channel: channel,
      ...options
    };
    
    this.send(message);
    this.subscriptions.set(channel, options);
  }

  // 取消订阅
  unsubscribe(channel, options = {}) {
    const message = {
      type: 'unsubscribe',
      channel: channel,
      ...options
    };
    
    this.send(message);
    this.subscriptions.delete(channel);
  }

  // 处理消息
  handleMessage(message) {
    const { type, channel } = message;
    
    // 触发特定类型的处理器
    if (this.messageHandlers.has(type)) {
      this.messageHandlers.get(type).forEach(handler => {
        handler(message.data, message);
      });
    }
    
    // 触发频道处理器
    if (channel && this.messageHandlers.has(channel)) {
      this.messageHandlers.get(channel).forEach(handler => {
        handler(message.data, message);
      });
    }
  }

  // 注册消息处理器
  on(eventType, handler) {
    if (!this.messageHandlers.has(eventType)) {
      this.messageHandlers.set(eventType, []);
    }
    this.messageHandlers.get(eventType).push(handler);
  }

  // 注册一次性处理器
  once(eventType, handler) {
    const onceHandler = (...args) => {
      handler(...args);
      this.off(eventType, onceHandler);
    };
    this.on(eventType, onceHandler);
  }

  // 移除处理器
  off(eventType, handler) {
    if (this.messageHandlers.has(eventType)) {
      const handlers = this.messageHandlers.get(eventType);
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  // 心跳检测
  startHeartbeat() {
    this.heartbeatInterval = setInterval(() => {
      this.send({
        type: 'ping',
        timestamp: new Date().toISOString()
      });
    }, 30000);
  }

  stopHeartbeat() {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  // 重连机制
  reconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('重连次数已达上限');
      return;
    }

    const delay = this.reconnectInterval * Math.pow(2, this.reconnectAttempts);
    console.log(`${delay}ms后尝试重连...`);
    
    setTimeout(() => {
      this.reconnectAttempts++;
      this.connect().then(() => {
        // 重新订阅之前的频道
        this.subscriptions.forEach((options, channel) => {
          this.subscribe(channel, options);
        });
      }).catch(error => {
        console.error('重连失败:', error);
      });
    }, delay);
  }

  // 关闭连接
  close() {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close(1000, '正常关闭');
    }
  }
}

// 使用示例
const ws = new QuantWebSocket('wss://api.quant-platform.com/ws', token);

// 连接WebSocket
await ws.connect();

// 订阅实时行情
ws.subscribe('market_data', {
  symbols: ['SHFE.rb2405', 'SHFE.hc2405'],
  fields: ['last_price', 'volume', 'bid', 'ask']
});

// 订阅订单更新
ws.subscribe('orders', { user_id: 1 });

// 处理行情数据
ws.on('market_data', (data, message) => {
  console.log('收到行情数据:', data);
  // 更新UI
  updateMarketData(data);
});

// 处理订单更新
ws.on('order_update', (data, message) => {
  console.log('订单状态更新:', data);
  // 更新订单列表
  updateOrderList(data);
});
```

### 2. Vue3组合式API集成

```javascript
// composables/useWebSocket.js
import { ref, reactive, onMounted, onUnmounted } from 'vue';
import { useAuthStore } from '@/stores/auth';

export function useWebSocket() {
  const authStore = useAuthStore();
  const ws = ref(null);
  const connected = ref(false);
  const marketData = reactive(new Map());
  const orders = ref([]);
  
  const connect = async () => {
    try {
      ws.value = new QuantWebSocket(
        'wss://api.quant-platform.com/ws',
        authStore.token
      );
      
      await ws.value.connect();
      connected.value = true;
      
      // 设置事件处理器
      setupEventHandlers();
      
    } catch (error) {
      console.error('WebSocket连接失败:', error);
    }
  };
  
  const setupEventHandlers = () => {
    // 行情数据处理
    ws.value.on('market_data', (data) => {
      marketData.set(data.symbol, data);
    });
    
    // 订单更新处理
    ws.value.on('order_update', (data) => {
      const index = orders.value.findIndex(o => o.order_id === data.order_id);
      if (index > -1) {
        orders.value[index] = { ...orders.value[index], ...data };
      } else {
        orders.value.push(data);
      }
    });
  };
  
  const subscribeMarketData = (symbols) => {
    if (ws.value && connected.value) {
      ws.value.subscribe('market_data', { symbols });
    }
  };
  
  const subscribeOrders = () => {
    if (ws.value && connected.value) {
      ws.value.subscribe('orders', { user_id: authStore.user.id });
    }
  };
  
  onMounted(() => {
    connect();
  });
  
  onUnmounted(() => {
    if (ws.value) {
      ws.value.close();
    }
  });
  
  return {
    connected,
    marketData,
    orders,
    subscribeMarketData,
    subscribeOrders
  };
}
```

## 服务端实现

### 1. FastAPI WebSocket服务

```python
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set, List
import json
import asyncio
from datetime import datetime
import jwt

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        # 活跃连接
        self.active_connections: Dict[str, WebSocket] = {}
        # 用户订阅
        self.user_subscriptions: Dict[str, Set[str]] = {}
        # 频道订阅者
        self.channel_subscribers: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, user_id: str):
        """接受WebSocket连接"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
        self.user_subscriptions[user_id] = set()
        print(f"用户 {user_id} 已连接")
    
    def disconnect(self, user_id: str):
        """断开连接"""
        if user_id in self.active_connections:
            # 清理订阅
            for channel in self.user_subscriptions.get(user_id, set()):
                if channel in self.channel_subscribers:
                    self.channel_subscribers[channel].discard(user_id)
            
            # 清理连接
            del self.active_connections[user_id]
            if user_id in self.user_subscriptions:
                del self.user_subscriptions[user_id]
            
            print(f"用户 {user_id} 已断开连接")
    
    async def send_personal_message(self, message: dict, user_id: str):
        """发送个人消息"""
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                print(f"发送消息失败 {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """向频道广播消息"""
        if channel in self.channel_subscribers:
            subscribers = self.channel_subscribers[channel].copy()
            for user_id in subscribers:
                await self.send_personal_message(message, user_id)
    
    def subscribe_channel(self, user_id: str, channel: str):
        """订阅频道"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].add(channel)
        
        if channel not in self.channel_subscribers:
            self.channel_subscribers[channel] = set()
        self.channel_subscribers[channel].add(user_id)
        
        print(f"用户 {user_id} 订阅频道 {channel}")
    
    def unsubscribe_channel(self, user_id: str, channel: str):
        """取消订阅频道"""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(channel)
        
        if channel in self.channel_subscribers:
            self.channel_subscribers[channel].discard(user_id)
        
        print(f"用户 {user_id} 取消订阅频道 {channel}")

manager = ConnectionManager()

async def verify_token(token: str):
    """验证JWT Token"""
    try:
        if token.startswith('Bearer '):
            token = token[7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        return user_id
    except jwt.InvalidTokenError:
        return None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    user_id = None
    try:
        # 等待认证消息
        await websocket.accept()
        auth_data = await websocket.receive_text()
        auth_message = json.loads(auth_data)
        
        if auth_message.get('type') != 'auth':
            await websocket.close(code=4001, reason="需要认证")
            return
        
        # 验证Token
        token = auth_message.get('token')
        user_id = await verify_token(token)
        
        if not user_id:
            await websocket.close(code=4001, reason="认证失败")
            return
        
        # 连接成功
        await manager.connect(websocket, user_id)
        
        # 发送认证成功响应
        await manager.send_personal_message({
            "type": "auth_response",
            "status": "success",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)
        
        # 消息循环
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await handle_message(message, user_id)
            
    except WebSocketDisconnect:
        if user_id:
            manager.disconnect(user_id)
    except Exception as e:
        print(f"WebSocket错误: {e}")
        if user_id:
            manager.disconnect(user_id)

async def handle_message(message: dict, user_id: str):
    """处理WebSocket消息"""
    message_type = message.get('type')
    
    if message_type == 'subscribe':
        channel = message.get('channel')
        if channel == 'market_data':
            symbols = message.get('symbols', [])
            for symbol in symbols:
                manager.subscribe_channel(user_id, f"market_data_{symbol}")
        elif channel == 'orders':
            manager.subscribe_channel(user_id, f"orders_{user_id}")
        elif channel == 'positions':
            manager.subscribe_channel(user_id, f"positions_{user_id}")
        
    elif message_type == 'unsubscribe':
        channel = message.get('channel')
        if channel == 'market_data':
            symbols = message.get('symbols', [])
            for symbol in symbols:
                manager.unsubscribe_channel(user_id, f"market_data_{symbol}")
        
    elif message_type == 'ping':
        # 心跳响应
        await manager.send_personal_message({
            "type": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }, user_id)

# 行情数据推送任务
async def market_data_publisher():
    """模拟行情数据推送"""
    while True:
        # 模拟行情数据
        market_data = {
            "type": "market_data",
            "channel": "tick",
            "symbol": "SHFE.rb2405",
            "data": {
                "last_price": "4000.0",
                "bid_price": "3999.0",
                "ask_price": "4001.0",
                "volume": "1000",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        await manager.broadcast_to_channel("market_data_SHFE.rb2405", market_data)
        await asyncio.sleep(1)  # 每秒推送一次

# 启动后台任务
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(market_data_publisher())
```

### 2. 消息队列集成

```python
import aioredis
from celery import Celery

# Redis连接
redis = aioredis.from_url("redis://localhost:6379")

# Celery配置
celery_app = Celery('websocket_tasks')

class WebSocketPublisher:
    def __init__(self, connection_manager):
        self.manager = connection_manager
    
    async def publish_market_data(self, symbol: str, data: dict):
        """发布行情数据"""
        message = {
            "type": "market_data",
            "channel": "tick",
            "symbol": symbol,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.manager.broadcast_to_channel(f"market_data_{symbol}", message)
    
    async def publish_order_update(self, user_id: str, order_data: dict):
        """发布订单更新"""
        message = {
            "type": "order_update",
            "channel": "orders",
            "data": order_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.manager.send_personal_message(message, str(user_id))
    
    async def publish_position_update(self, user_id: str, position_data: dict):
        """发布持仓更新"""
        message = {
            "type": "position_update",
            "channel": "positions",
            "data": position_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.manager.send_personal_message(message, str(user_id))

# 全局发布器实例
publisher = WebSocketPublisher(manager)

# Celery任务
@celery_app.task
def broadcast_market_data(symbol: str, data: dict):
    """异步广播行情数据"""
    asyncio.run(publisher.publish_market_data(symbol, data))

@celery_app.task
def send_order_update(user_id: str, order_data: dict):
    """异步发送订单更新"""
    asyncio.run(publisher.publish_order_update(user_id, order_data))
```

## 性能优化

### 1. 连接管理优化

```python
class OptimizedConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        # 使用Redis存储订阅关系
        self.redis = aioredis.from_url("redis://localhost:6379")
    
    async def subscribe_channel(self, user_id: str, channel: str):
        """使用Redis管理订阅"""
        await self.redis.sadd(f"channel:{channel}", user_id)
        await self.redis.sadd(f"user:{user_id}:channels", channel)
    
    async def get_channel_subscribers(self, channel: str) -> Set[str]:
        """获取频道订阅者"""
        subscribers = await self.redis.smembers(f"channel:{channel}")
        return {sub.decode() for sub in subscribers}
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """优化的频道广播"""
        subscribers = await self.get_channel_subscribers(channel)
        
        # 批量发送
        tasks = []
        for user_id in subscribers:
            if user_id in self.active_connections:
                task = self.send_personal_message(message, user_id)
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
```

### 2. 消息压缩

```python
import gzip
import json

class CompressedWebSocket:
    @staticmethod
    async def send_compressed_message(websocket: WebSocket, message: dict):
        """发送压缩消息"""
        json_str = json.dumps(message, ensure_ascii=False)
        
        if len(json_str) > 1024:  # 大于1KB时压缩
            compressed = gzip.compress(json_str.encode('utf-8'))
            await websocket.send_bytes(compressed)
        else:
            await websocket.send_text(json_str)
```

### 3. 消息限流

```python
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self):
        self.user_message_count = defaultdict(list)
        self.max_messages_per_minute = 100
    
    def is_allowed(self, user_id: str) -> bool:
        """检查是否允许发送消息"""
        now = time.time()
        user_messages = self.user_message_count[user_id]
        
        # 清理过期记录
        user_messages[:] = [t for t in user_messages if now - t < 60]
        
        if len(user_messages) >= self.max_messages_per_minute:
            return False
        
        user_messages.append(now)
        return True
```

## 监控和调试

### 1. 连接监控

```python
class WebSocketMonitor:
    def __init__(self):
        self.connection_stats = {
            'total_connections': 0,
            'active_connections': 0,
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0
        }
    
    def record_connection(self):
        self.connection_stats['total_connections'] += 1
        self.connection_stats['active_connections'] += 1
    
    def record_disconnection(self):
        self.connection_stats['active_connections'] -= 1
    
    def record_message_sent(self):
        self.connection_stats['messages_sent'] += 1
    
    def record_error(self):
        self.connection_stats['errors'] += 1
    
    def get_stats(self) -> dict:
        return self.connection_stats.copy()

monitor = WebSocketMonitor()

# 在FastAPI中暴露监控接口
@app.get("/ws/stats")
async def get_websocket_stats():
    return monitor.get_stats()
```

### 2. 日志记录

```python
import logging

# 配置WebSocket专用日志
ws_logger = logging.getLogger('websocket')
ws_logger.setLevel(logging.INFO)

handler = logging.FileHandler('websocket.log')
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
ws_logger.addHandler(handler)

# 在WebSocket处理中使用
async def handle_message(message: dict, user_id: str):
    ws_logger.info(f"收到消息 - 用户: {user_id}, 类型: {message.get('type')}")
    
    try:
        # 处理消息逻辑
        pass
    except Exception as e:
        ws_logger.error(f"处理消息失败 - 用户: {user_id}, 错误: {e}")
```

## 总结

WebSocket实时通信系统的关键要素：

1. **连接管理**：认证、心跳、重连机制
2. **消息协议**：标准化的消息格式和类型
3. **数据推送**：行情、交易、策略信号的实时推送
4. **性能优化**：连接池、消息压缩、限流控制
5. **监控调试**：连接状态监控、日志记录

通过这套WebSocket系统，实现量化交易平台的实时数据推送和双向通信功能。 