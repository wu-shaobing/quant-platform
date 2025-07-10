import { ref, onMounted, onUnmounted } from 'vue'
import { websocketService, WebSocketService, MessageType, Channel } from '@/services/websocket.service'
import type { TickData, DepthData, OrderData, TradeData, PositionData, StrategyData } from '@/types/api'

export function useWebSocket() {
  const isConnected = ref(websocketService.isConnectionActive())

  const onConnect = () => {
    isConnected.value = true
  }
  
  const onDisconnect = () => {
    isConnected.value = false
  }

  onMounted(() => {
    websocketService.connect()
    // 监听内部事件
    websocketService.on('connect', onConnect)
    websocketService.on('disconnect', onDisconnect)
  })

  onUnmounted(() => {
    // 移除监听器，但不主动断开，保持连接共享
    websocketService.off('connect', onConnect)
    websocketService.off('disconnect', onDisconnect)
  })

  // 订阅行情
  const subscribeMarketTick = (symbols: string[], callback: (data: TickData) => void) => 
    websocketService.subscribeMarketTick(symbols, callback)

  // 订阅深度
  const subscribeMarketDepth = (symbol: string, callback: (data: DepthData) => void) => 
    websocketService.subscribeMarketDepth(symbol, callback)

  // 订阅K线
  const subscribeMarketKline = (symbol: string, interval: string, callback: (data: any) => void) =>
    websocketService.subscribeMarketKline(symbol, interval, callback)

  // 订阅订单
  const subscribeTradingOrders = (callback: (data: OrderData) => void) =>
    websocketService.subscribeTradingOrders(callback)

  // 订阅成交
  const subscribeTradingTrades = (callback: (data: TradeData) => void) =>
    websocketService.subscribeTradingTrades(callback)

  // 订阅持仓
  const subscribeTradingPositions = (callback: (data: PositionData) => void) =>
    websocketService.subscribeTradingPositions(callback)

  // 订阅策略状态
  const subscribeStrategyStatus = (strategyId: string, callback: (data: StrategyData) => void) =>
    websocketService.subscribeStrategyStatus(strategyId, callback)

  return {
    isConnected,
    websocketService,
    // 订阅函数
    subscribeMarketTick,
    subscribeMarketDepth,
    subscribeMarketKline,
    subscribeTradingOrders,
    subscribeTradingTrades,
    subscribeTradingPositions,
    subscribeStrategyStatus
  }
}
