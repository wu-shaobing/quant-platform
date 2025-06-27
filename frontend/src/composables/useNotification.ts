/**
 * 通知相关组合式函数
 */
import { ref, computed, readonly } from 'vue'
import { ElNotification } from 'element-plus'
import { NOTIFICATION_CONFIG } from '@/utils/constants'

interface NotificationItem {
  id: string
  type: 'order' | 'trade' | 'price_alert' | 'strategy' | 'risk' | 'system'
  level: 'info' | 'warning' | 'error' | 'success'
  title: string
  message: string
  timestamp: number
  read: boolean
  data?: unknown
}

export const useNotification = () => {
  const notifications = ref<NotificationItem[]>([])
  const soundEnabled = ref(true)
  const desktopEnabled = ref(false)
  
  // 计算属性
  const unreadCount = computed(() => {
    return notifications.value.filter(n => !n.read).length
  })
  
  const hasUnread = computed(() => unreadCount.value > 0)
  
  /**
   * 生成通知ID
   */
  const generateId = (): string => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2)
  }
  
  /**
   * 播放通知音效
   */
  const playNotificationSound = (type: string) => {
    if (!soundEnabled.value) return
    
    try {
      let audioFile = '/sounds/notification.mp3'
      
      switch (type) {
        case 'trade':
          audioFile = '/sounds/trade-success.mp3'
          break
        case 'risk':
        case 'error':
          audioFile = '/sounds/alert.mp3'
          break
      }
      
      const audio = new Audio(audioFile)
      audio.volume = 0.5
      audio.play().catch(error => {
        console.warn('播放通知音效失败:', error)
      })
    } catch (error) {
      console.warn('音效播放错误:', error)
    }
  }
  
  /**
   * 显示桌面通知
   */
  const showDesktopNotification = (title: string, message: string, icon?: string) => {
    if (!desktopEnabled.value || !('Notification' in window)) return
    
    if (Notification.permission === 'granted') {
      new Notification(title, {
        body: message,
        icon: icon || '/favicon.ico',
        tag: 'quant-platform'
      })
    }
  }
  
  /**
   * 请求桌面通知权限
   */
  const requestDesktopPermission = async (): Promise<boolean> => {
    if (!('Notification' in window)) {
      console.warn('此浏览器不支持桌面通知')
      return false
    }
    
    if (Notification.permission === 'granted') {
      return true
    }
    
    if (Notification.permission === 'denied') {
      return false
    }
    
    const permission = await Notification.requestPermission()
    return permission === 'granted'
  }
  
  /**
   * 添加通知
   */
  const addNotification = (notification: Omit<NotificationItem, 'id' | 'timestamp' | 'read'>) => {
    const newNotification: NotificationItem = {
      ...notification,
      id: generateId(),
      timestamp: Date.now(),
      read: false
    }
    
    notifications.value.unshift(newNotification)
    
    // 限制通知数量
    if (notifications.value.length > 100) {
      notifications.value = notifications.value.slice(0, 100)
    }
    
    // 播放音效
    playNotificationSound(notification.type)
    
    // 显示桌面通知
    showDesktopNotification(notification.title, notification.message)
    
    // 显示Element Plus通知
    const duration = NOTIFICATION_CONFIG.DURATION[notification.level] || 3000
    
    ElNotification({
      title: notification.title,
      message: notification.message,
      type: notification.level,
      duration,
      position: 'top-right'
    })
    
    return newNotification.id
  }
  
  /**
   * 标记通知为已读
   */
  const markAsRead = (id: string) => {
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.read = true
    }
  }
  
  /**
   * 标记所有通知为已读
   */
  const markAllAsRead = () => {
    notifications.value.forEach(n => {
      n.read = true
    })
  }
  
  /**
   * 删除通知
   */
  const removeNotification = (id: string) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }
  
  /**
   * 清空所有通知
   */
  const clearAllNotifications = () => {
    notifications.value = []
  }
  
  /**
   * 清空已读通知
   */
  const clearReadNotifications = () => {
    notifications.value = notifications.value.filter(n => !n.read)
  }
  
  /**
   * 获取特定类型的通知
   */
  const getNotificationsByType = (type: string) => {
    return notifications.value.filter(n => n.type === type)
  }
  
  /**
   * 显示成功消息
   */
  const success = (message: string, title = '成功') => {
    addNotification({
      type: 'system',
      level: 'success',
      title,
      message
    })
  }
  
  /**
   * 显示错误消息
   */
  const error = (message: string, title = '错误') => {
    addNotification({
      type: 'system',
      level: 'error',
      title,
      message
    })
  }
  
  /**
   * 显示警告消息
   */
  const warning = (message: string, title = '警告') => {
    addNotification({
      type: 'system',
      level: 'warning',
      title,
      message
    })
  }
  
  /**
   * 显示信息消息
   */
  const info = (message: string, title = '提示') => {
    addNotification({
      type: 'system',
      level: 'info',
      title,
      message
    })
  }
  
  /**
   * 订单通知
   */
  const notifyOrder = (orderData: Record<string, unknown>) => {
    const { status, symbol, side, quantity, price } = orderData
    
    let title = '订单通知'
    let message = ''
    let level: 'info' | 'success' | 'warning' | 'error' = 'info'
    
    switch (status) {
      case 'filled':
        title = '订单成交'
        message = `${side === 'buy' ? '买入' : '卖出'} ${symbol} ${quantity}股 @ ${price}`
        level = 'success'
        break
      case 'partial_filled':
        title = '订单部分成交'
        message = `${side === 'buy' ? '买入' : '卖出'} ${symbol} 部分成交`
        level = 'info'
        break
      case 'cancelled':
        title = '订单已撤销'
        message = `${symbol} ${side === 'buy' ? '买入' : '卖出'}订单已撤销`
        level = 'warning'
        break
      case 'rejected':
        title = '订单被拒绝'
        message = `${symbol} ${side === 'buy' ? '买入' : '卖出'}订单被拒绝`
        level = 'error'
        break
    }
    
    addNotification({
      type: 'order',
      level,
      title,
      message,
      data: orderData
    })
  }
  
  /**
   * 价格提醒通知
   */
  const notifyPriceAlert = (alertData: Record<string, unknown>) => {
    const { symbol, currentPrice, targetPrice, condition } = alertData
    
    const conditionText = condition === 'above' ? '突破' : '跌破'
    
    addNotification({
      type: 'price_alert',
      level: 'warning',
      title: '价格提醒',
      message: `${symbol} 价格 ${currentPrice} ${conditionText} ${targetPrice}`,
      data: alertData
    })
  }
  
  /**
   * 策略通知
   */
  const notifyStrategy = (strategyData: Record<string, unknown>) => {
    const { name, status, message } = strategyData
    
    let level: 'info' | 'success' | 'warning' | 'error' = 'info'
    
    switch (status) {
      case 'started':
        level = 'success'
        break
      case 'stopped':
        level = 'warning'
        break
      case 'error':
        level = 'error'
        break
    }
    
    addNotification({
      type: 'strategy',
      level,
      title: '策略通知',
      message: `策略 ${name}: ${message}`,
      data: strategyData
    })
  }
  
  /**
   * 风险通知
   */
  const notifyRisk = (riskData: Record<string, unknown>) => {
    const { type, level, message } = riskData
    
    addNotification({
      type: 'risk',
      level: level === 'high' ? 'error' : 'warning',
      title: '风险提醒',
      message: `${type}: ${message}`,
      data: riskData
    })
  }
  
  /**
   * 切换音效开关
   */
  const toggleSound = () => {
    soundEnabled.value = !soundEnabled.value
    localStorage.setItem('notification_sound', soundEnabled.value.toString())
  }
  
  /**
   * 切换桌面通知开关
   */
  const toggleDesktop = async () => {
    if (!desktopEnabled.value) {
      const granted = await requestDesktopPermission()
      if (granted) {
        desktopEnabled.value = true
        localStorage.setItem('notification_desktop', 'true')
      }
    } else {
      desktopEnabled.value = false
      localStorage.setItem('notification_desktop', 'false')
    }
  }
  
  /**
   * 初始化设置
   */
  const initSettings = () => {
    // 恢复音效设置
    const soundSetting = localStorage.getItem('notification_sound')
    if (soundSetting !== null) {
      soundEnabled.value = soundSetting === 'true'
    }
    
    // 恢复桌面通知设置
    const desktopSetting = localStorage.getItem('notification_desktop')
    if (desktopSetting === 'true' && Notification.permission === 'granted') {
      desktopEnabled.value = true
    }
  }
  
  // 初始化
  initSettings()
  
  return {
    // 状态
    notifications: readonly(notifications),
    unreadCount,
    hasUnread,
    soundEnabled: readonly(soundEnabled),
    desktopEnabled: readonly(desktopEnabled),
    
    // 方法
    addNotification,
    markAsRead,
    markAllAsRead,
    removeNotification,
    clearAllNotifications,
    clearReadNotifications,
    getNotificationsByType,
    
    // 快捷方法
    success,
    error,
    warning,
    info,
    
    // 业务通知
    notifyOrder,
    notifyPriceAlert,
    notifyStrategy,
    notifyRisk,
    
    // 设置
    toggleSound,
    toggleDesktop,
    requestDesktopPermission
  }
}