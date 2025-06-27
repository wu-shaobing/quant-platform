/**
 * 通知服务
 * 提供消息推送、预警通知、系统通知等功能
 */

import { ref, reactive } from 'vue'
import { ElNotification, ElMessage } from 'element-plus'
import { formatDate } from '@/utils/format/date'

// 通知类型
export type NotificationType = 'info' | 'success' | 'warning' | 'error'

// 通知优先级
export type NotificationPriority = 'low' | 'normal' | 'high' | 'urgent'

// 通知分类
export type NotificationCategory = 
  | 'system'      // 系统通知
  | 'trade'       // 交易通知
  | 'alert'       // 预警通知
  | 'market'      // 市场资讯
  | 'strategy'    // 策略通知
  | 'risk'        // 风险提醒
  | 'account'     // 账户通知

// 通知项接口
export interface NotificationItem {
  id: string
  title: string
  message: string
  type: NotificationType
  category: NotificationCategory
  priority: NotificationPriority
  timestamp: number
  read: boolean
  persistent?: boolean
  actions?: NotificationAction[]
  data?: any
  expiresAt?: number
}

// 通知操作
export interface NotificationAction {
  id: string
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger'
  handler: (notification: NotificationItem) => void | Promise<void>
}

// 通知配置
export interface NotificationConfig {
  title: string
  message: string
  type?: NotificationType
  category?: NotificationCategory
  priority?: NotificationPriority
  persistent?: boolean
  duration?: number
  showInPopup?: boolean
  showInList?: boolean
  actions?: NotificationAction[]
  data?: any
  expiresAt?: number
}

// 推送配置
export interface PushConfig {
  enabled: boolean
  categories: NotificationCategory[]
  priorities: NotificationPriority[]
  sound: boolean
  vibration: boolean
  desktop: boolean
  browser: boolean
}

/**
 * 通知服务类
 */
class NotificationService {
  // 通知列表
  private notifications = ref<NotificationItem[]>([])
  
  // 未读数量
  private unreadCount = ref(0)
  
  // 推送配置
  private pushConfig = reactive<PushConfig>({
    enabled: true,
    categories: ['system', 'trade', 'alert', 'risk'],
    priorities: ['normal', 'high', 'urgent'],
    sound: true,
    vibration: true,
    desktop: true,
    browser: true
  })
  
  // 服务工作者
  private serviceWorker: ServiceWorker | null = null
  
  // 通知权限状态
  private permissionStatus = ref<NotificationPermission>('default')

  constructor() {
    this.init()
  }

  /**
   * 初始化通知服务
   */
  private async init(): Promise<void> {
    // 检查通知权限
    this.checkPermission()
    
    // 注册Service Worker
    await this.registerServiceWorker()
    
    // 加载本地存储的通知
    this.loadStoredNotifications()
    
    // 定期清理过期通知
    this.startCleanupTimer()
  }

  /**
   * 检查通知权限
   */
  private checkPermission(): void {
    if ('Notification' in window) {
      this.permissionStatus.value = Notification.permission
    }
  }

  /**
   * 请求通知权限
   */
  async requestPermission(): Promise<NotificationPermission> {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission()
      this.permissionStatus.value = permission
      return permission
    }
    return 'denied'
  }

  /**
   * 注册Service Worker
   */
  private async registerServiceWorker(): Promise<void> {
    if ('serviceWorker' in navigator) {
      try {
        const registration = await navigator.serviceWorker.register('/sw.js')
        this.serviceWorker = registration.active
        console.log('Service Worker registered successfully')
      } catch (error) {
        console.warn('Service Worker registration failed:', error)
      }
    }
  }

  /**
   * 发送通知
   * @param config 通知配置
   * @returns 通知ID
   */
  async notify(config: NotificationConfig): Promise<string> {
    const notification: NotificationItem = {
      id: this.generateId(),
      title: config.title,
      message: config.message,
      type: config.type || 'info',
      category: config.category || 'system',
      priority: config.priority || 'normal',
      timestamp: Date.now(),
      read: false,
      persistent: config.persistent || false,
      actions: config.actions || [],
      data: config.data,
      expiresAt: config.expiresAt
    }

    // 添加到通知列表
    if (config.showInList !== false) {
      this.addToList(notification)
    }

    // 显示弹窗通知
    if (config.showInPopup !== false && this.shouldShowPopup(notification)) {
      this.showPopupNotification(notification, config.duration)
    }

    // 发送桌面通知
    if (this.shouldShowDesktop(notification)) {
      this.showDesktopNotification(notification)
    }

    // 保存到本地存储
    this.saveToStorage()

    return notification.id
  }

  /**
   * 快捷通知方法
   */
  info(title: string, message: string, config?: Partial<NotificationConfig>) {
    return this.notify({ ...config, title, message, type: 'info' })
  }

  success(title: string, message: string, config?: Partial<NotificationConfig>) {
    return this.notify({ ...config, title, message, type: 'success' })
  }

  warning(title: string, message: string, config?: Partial<NotificationConfig>) {
    return this.notify({ ...config, title, message, type: 'warning' })
  }

  error(title: string, message: string, config?: Partial<NotificationConfig>) {
    return this.notify({ ...config, title, message, type: 'error' })
  }

  /**
   * 交易通知
   */
  trade(title: string, message: string, data?: any) {
    return this.notify({
      title,
      message,
      type: 'info',
      category: 'trade',
      priority: 'high',
      data,
      persistent: true
    })
  }

  /**
   * 预警通知
   */
  alert(title: string, message: string, data?: any) {
    return this.notify({
      title,
      message,
      type: 'warning',
      category: 'alert',
      priority: 'urgent',
      data,
      persistent: true,
      sound: true
    })
  }

  /**
   * 风险通知
   */
  risk(title: string, message: string, data?: any) {
    return this.notify({
      title,
      message,
      type: 'error',
      category: 'risk',
      priority: 'urgent',
      data,
      persistent: true
    })
  }

  /**
   * 策略通知
   */
  strategy(title: string, message: string, data?: any) {
    return this.notify({
      title,
      message,
      type: 'info',
      category: 'strategy',
      priority: 'normal',
      data
    })
  }

  /**
   * 添加到通知列表
   */
  private addToList(notification: NotificationItem): void {
    this.notifications.value.unshift(notification)
    this.updateUnreadCount()
    
    // 限制通知数量
    if (this.notifications.value.length > 1000) {
      this.notifications.value = this.notifications.value.slice(0, 1000)
    }
  }

  /**
   * 显示弹窗通知
   */
  private showPopupNotification(notification: NotificationItem, duration?: number): void {
    const config: any = {
      title: notification.title,
      message: notification.message,
      type: notification.type,
      duration: duration || this.getDurationByPriority(notification.priority),
      showClose: true,
      onClick: () => this.handleNotificationClick(notification)
    }

    // 添加操作按钮
    if (notification.actions && notification.actions.length > 0) {
      config.dangerouslyUseHTMLString = true
      config.message = `
        <div>${notification.message}</div>
        <div style="margin-top: 10px;">
          ${notification.actions.map(action => `
            <button 
              class="el-button el-button--${action.type || 'primary'} el-button--small"
              onclick="window.notificationService.handleAction('${notification.id}', '${action.id}')"
            >
              ${action.label}
            </button>
          `).join('')}
        </div>
      `
    }

    ElNotification(config)
  }

  /**
   * 显示桌面通知
   */
  private showDesktopNotification(notification: NotificationItem): void {
    if (this.permissionStatus.value !== 'granted') return

    const desktopNotification = new Notification(notification.title, {
      body: notification.message,
      icon: this.getNotificationIcon(notification.type),
      tag: notification.id,
      requireInteraction: notification.priority === 'urgent',
      silent: !this.pushConfig.sound
    })

    desktopNotification.onclick = () => {
      window.focus()
      this.handleNotificationClick(notification)
      desktopNotification.close()
    }

    // 自动关闭
    if (notification.priority !== 'urgent') {
      setTimeout(() => {
        desktopNotification.close()
      }, this.getDurationByPriority(notification.priority))
    }
  }

  /**
   * 获取通知图标
   */
  private getNotificationIcon(type: NotificationType): string {
    const icons = {
      info: '/icons/info.png',
      success: '/icons/success.png',
      warning: '/icons/warning.png',
      error: '/icons/error.png'
    }
    return icons[type] || icons.info
  }

  /**
   * 根据优先级获取显示时长
   */
  private getDurationByPriority(priority: NotificationPriority): number {
    const durations = {
      low: 3000,
      normal: 4500,
      high: 6000,
      urgent: 0 // 不自动关闭
    }
    return durations[priority]
  }

  /**
   * 判断是否显示弹窗
   */
  private shouldShowPopup(notification: NotificationItem): boolean {
    if (!this.pushConfig.enabled) return false
    if (!this.pushConfig.categories.includes(notification.category)) return false
    if (!this.pushConfig.priorities.includes(notification.priority)) return false
    return true
  }

  /**
   * 判断是否显示桌面通知
   */
  private shouldShowDesktop(notification: NotificationItem): boolean {
    if (!this.pushConfig.desktop) return false
    if (this.permissionStatus.value !== 'granted') return false
    return this.shouldShowPopup(notification)
  }

  /**
   * 处理通知点击
   */
  private handleNotificationClick(notification: NotificationItem): void {
    this.markAsRead(notification.id)
    
    // 触发自定义事件
    window.dispatchEvent(new CustomEvent('notification-click', {
      detail: notification
    }))
  }

  /**
   * 处理通知操作
   */
  async handleAction(notificationId: string, actionId: string): Promise<void> {
    const notification = this.notifications.value.find(n => n.id === notificationId)
    if (!notification) return

    const action = notification.actions?.find(a => a.id === actionId)
    if (!action) return

    try {
      await action.handler(notification)
      this.markAsRead(notificationId)
    } catch (error) {
      console.error('Notification action error:', error)
      ElMessage.error('操作执行失败')
    }
  }

  /**
   * 标记为已读
   */
  markAsRead(id: string): void {
    const notification = this.notifications.value.find(n => n.id === id)
    if (notification && !notification.read) {
      notification.read = true
      this.updateUnreadCount()
      this.saveToStorage()
    }
  }

  /**
   * 标记所有为已读
   */
  markAllAsRead(): void {
    this.notifications.value.forEach(notification => {
      notification.read = true
    })
    this.updateUnreadCount()
    this.saveToStorage()
  }

  /**
   * 删除通知
   */
  remove(id: string): void {
    const index = this.notifications.value.findIndex(n => n.id === id)
    if (index >= 0) {
      this.notifications.value.splice(index, 1)
      this.updateUnreadCount()
      this.saveToStorage()
    }
  }

  /**
   * 清空所有通知
   */
  clear(): void {
    this.notifications.value = []
    this.unreadCount.value = 0
    this.saveToStorage()
  }

  /**
   * 清理过期通知
   */
  private cleanupExpired(): void {
    const now = Date.now()
    this.notifications.value = this.notifications.value.filter(notification => {
      if (notification.persistent) return true
      if (notification.expiresAt && notification.expiresAt < now) return false
      
      // 默认保留7天
      const sevenDaysAgo = now - 7 * 24 * 60 * 60 * 1000
      return notification.timestamp > sevenDaysAgo
    })
    
    this.updateUnreadCount()
    this.saveToStorage()
  }

  /**
   * 启动清理定时器
   */
  private startCleanupTimer(): void {
    // 每小时清理一次过期通知
    setInterval(() => {
      this.cleanupExpired()
    }, 60 * 60 * 1000)
  }

  /**
   * 更新未读数量
   */
  private updateUnreadCount(): void {
    this.unreadCount.value = this.notifications.value.filter(n => !n.read).length
  }

  /**
   * 生成唯一ID
   */
  private generateId(): string {
    return `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  /**
   * 保存到本地存储
   */
  private saveToStorage(): void {
    try {
      const data = {
        notifications: this.notifications.value.slice(0, 100), // 只保存最新100条
        config: this.pushConfig
      }
      localStorage.setItem('notifications', JSON.stringify(data))
    } catch (error) {
      console.warn('Failed to save notifications to storage:', error)
    }
  }

  /**
   * 从本地存储加载
   */
  private loadStoredNotifications(): void {
    try {
      const stored = localStorage.getItem('notifications')
      if (stored) {
        const data = JSON.parse(stored)
        this.notifications.value = data.notifications || []
        if (data.config) {
          Object.assign(this.pushConfig, data.config)
        }
        this.updateUnreadCount()
      }
    } catch (error) {
      console.warn('Failed to load notifications from storage:', error)
    }
  }

  /**
   * 获取通知列表
   */
  getNotifications(): NotificationItem[] {
    return this.notifications.value
  }

  /**
   * 获取未读数量
   */
  getUnreadCount(): number {
    return this.unreadCount.value
  }

  /**
   * 获取推送配置
   */
  getPushConfig(): PushConfig {
    return this.pushConfig
  }

  /**
   * 更新推送配置
   */
  updatePushConfig(config: Partial<PushConfig>): void {
    Object.assign(this.pushConfig, config)
    this.saveToStorage()
  }

  /**
   * 获取分类统计
   */
  getCategoryStats(): Record<NotificationCategory, number> {
    const stats: Record<string, number> = {}
    
    this.notifications.value.forEach(notification => {
      stats[notification.category] = (stats[notification.category] || 0) + 1
    })
    
    return stats as Record<NotificationCategory, number>
  }

  /**
   * 按分类获取通知
   */
  getNotificationsByCategory(category: NotificationCategory): NotificationItem[] {
    return this.notifications.value.filter(n => n.category === category)
  }

  /**
   * 按优先级获取通知
   */
  getNotificationsByPriority(priority: NotificationPriority): NotificationItem[] {
    return this.notifications.value.filter(n => n.priority === priority)
  }
}

// 创建单例实例
const notificationService = new NotificationService()

// 将服务暴露到全局，以便在HTML中调用
declare global {
  interface Window {
    notificationService: NotificationService
  }
}
window.notificationService = notificationService

export default notificationService
export { NotificationService }
export type {
  NotificationItem,
  NotificationConfig,
  NotificationAction,
  NotificationType,
  NotificationPriority,
  NotificationCategory,
  PushConfig
} 