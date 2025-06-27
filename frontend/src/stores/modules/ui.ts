import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'
import type { MessageOptions, NotificationOptions } from 'element-plus'

// 通知类型
export interface NotificationItem {
  id: string
  type: 'success' | 'warning' | 'error' | 'info'
  title: string
  message: string
  duration?: number
  timestamp: number
  read: boolean
  actions?: Array<{
    label: string
    action: () => void
    type?: 'primary' | 'success' | 'warning' | 'danger'
  }>
}

// 弹窗状态
export interface ModalState {
  id: string
  component: unknown
  props?: Record<string, unknown>
  options?: {
    title?: string
    width?: string
    closable?: boolean
    destroyOnClose?: boolean
    maskClosable?: boolean
  }
}

// 布局配置
export interface LayoutConfig {
  sidebarCollapsed: boolean
  sidebarWidth: number
  headerHeight: number
  footerHeight: number
  showHeader: boolean
  showFooter: boolean
  showSidebar: boolean
  showBreadcrumb: boolean
  showTabs: boolean
  fixedHeader: boolean
  fixedSidebar: boolean
}

// 页面加载状态
export interface PageLoadingState {
  global: boolean
  routes: Map<string, boolean>
  components: Map<string, boolean>
  apis: Map<string, boolean>
}

export const useUIStore = defineStore('ui', () => {
  // ============ 状态定义 ============
  
  // 全局加载状态
  const globalLoading = ref(false)
  
  // 页面加载状态
  const pageLoading = ref<PageLoadingState>({
    global: false,
    routes: new Map(),
    components: new Map(),
    apis: new Map()
  })
  
  // 布局配置
  const layoutConfig = ref<LayoutConfig>({
    sidebarCollapsed: false,
    sidebarWidth: 240,
    headerHeight: 64,
    footerHeight: 48,
    showHeader: true,
    showFooter: true,
    showSidebar: true,
    showBreadcrumb: true,
    showTabs: true,
    fixedHeader: true,
    fixedSidebar: true
  })
  
  // 当前设备类型
  const deviceType = ref<'desktop' | 'tablet' | 'mobile'>('desktop')
  
  // 屏幕尺寸
  const screenSize = ref({
    width: window.innerWidth,
    height: window.innerHeight
  })
  
  // 弹窗管理
  const modals = ref<ModalState[]>([])
  
  // 通知列表
  const notifications = ref<NotificationItem[]>([])
  
  // 面包屑导航
  const breadcrumbs = ref<Array<{
    label: string
    path?: string
    icon?: string
  }>>([])
  
  // 标签页列表
  const tabs = ref<Array<{
    name: string
    label: string
    path: string
    closable?: boolean
    icon?: string
  }>>([])
  
  // 当前激活的标签页
  const activeTab = ref('')
  
  // 主题配置
  const themeConfig = ref({
    primaryColor: '#409EFF',
    darkMode: false,
    colorScheme: 'blue',
    borderRadius: '4px',
    componentSize: 'default' as 'large' | 'default' | 'small'
  })
  
  // 全屏状态
  const isFullscreen = ref(false)
  
  // 侧边栏缓存状态（移动端）
  const sidebarCacheCollapsed = ref(false)

  // ============ 计算属性 ============
  
  // 是否为暗黑模式
  const isDarkMode = computed(() => themeConfig.value.darkMode)
  
  // 是否为移动端
  const isMobile = computed(() => deviceType.value === 'mobile')
  
  // 是否为平板
  const isTablet = computed(() => deviceType.value === 'tablet')
  
  // 是否为桌面端
  const isDesktop = computed(() => deviceType.value === 'desktop')
  
  // 未读通知数量
  const unreadNotificationsCount = computed(() => {
    return notifications.value.filter(n => !n.read).length
  })
  
  // 当前打开的弹窗数量
  const openModalsCount = computed(() => modals.value.length)
  
  // 布局内容区域样式
  const contentStyle = computed(() => {
    const { sidebarCollapsed, sidebarWidth, headerHeight, showHeader, showSidebar } = layoutConfig.value
    
    const marginLeft = showSidebar 
      ? (sidebarCollapsed ? 64 : sidebarWidth) 
      : 0
    const marginTop = showHeader ? headerHeight : 0
    
    return {
      marginLeft: `${marginLeft}px`,
      marginTop: `${marginTop}px`,
      transition: 'margin-left 0.3s ease'
    }
  })

  // ============ 布局管理方法 ============
  
  // 切换侧边栏状态
  const toggleSidebar = () => {
    if (isMobile.value) {
      // 移动端直接显示/隐藏侧边栏
      layoutConfig.value.showSidebar = !layoutConfig.value.showSidebar
    } else {
      // 桌面端折叠/展开侧边栏
      layoutConfig.value.sidebarCollapsed = !layoutConfig.value.sidebarCollapsed
    }
  }
  
  // 设置侧边栏状态
  const setSidebarCollapsed = (collapsed: boolean) => {
    layoutConfig.value.sidebarCollapsed = collapsed
  }
  
  // 设置布局配置
  const updateLayoutConfig = (config: Partial<LayoutConfig>) => {
    layoutConfig.value = { ...layoutConfig.value, ...config }
  }
  
  // 响应屏幕尺寸变化
  const handleResize = () => {
    screenSize.value = {
      width: window.innerWidth,
      height: window.innerHeight
    }
    
    // 更新设备类型
    if (screenSize.value.width < 768) {
      deviceType.value = 'mobile'
      // 移动端自动收起侧边栏
      if (!sidebarCacheCollapsed.value) {
        sidebarCacheCollapsed.value = layoutConfig.value.sidebarCollapsed
        layoutConfig.value.sidebarCollapsed = true
      }
    } else if (screenSize.value.width < 1024) {
      deviceType.value = 'tablet'
    } else {
      deviceType.value = 'desktop'
      // 桌面端恢复侧边栏状态
      if (sidebarCacheCollapsed.value !== null) {
        layoutConfig.value.sidebarCollapsed = sidebarCacheCollapsed.value
        sidebarCacheCollapsed.value = false
      }
    }
  }

  // ============ 弹窗管理方法 ============
  
  // 打开弹窗
  const openModal = (modal: Omit<ModalState, 'id'>) => {
    const id = `modal_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const modalState: ModalState = { id, ...modal }
    modals.value.push(modalState)
    return id
  }
  
  // 关闭弹窗
  const closeModal = (id: string) => {
    const index = modals.value.findIndex(modal => modal.id === id)
    if (index !== -1) {
      modals.value.splice(index, 1)
    }
  }
  
  // 关闭所有弹窗
  const closeAllModals = () => {
    modals.value = []
  }
  
  // 获取弹窗
  const getModal = (id: string) => {
    return modals.value.find(modal => modal.id === id)
  }

  // ============ 通知管理方法 ============
  
  // 添加通知
  const addNotification = (notification: Omit<NotificationItem, 'id' | 'timestamp' | 'read'>) => {
    const id = `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
    const notificationItem: NotificationItem = {
      id,
      timestamp: Date.now(),
      read: false,
      ...notification
    }
    
    notifications.value.unshift(notificationItem)
    
    // 如果通知数量超过100条，删除最旧的
    if (notifications.value.length > 100) {
      notifications.value = notifications.value.slice(0, 100)
    }
    
    return id
  }
  
  // 标记通知为已读
  const markNotificationAsRead = (id: string) => {
    const notification = notifications.value.find(n => n.id === id)
    if (notification) {
      notification.read = true
    }
  }
  
  // 标记所有通知为已读
  const markAllNotificationsAsRead = () => {
    notifications.value.forEach(notification => {
      notification.read = true
    })
  }
  
  // 删除通知
  const removeNotification = (id: string) => {
    const index = notifications.value.findIndex(n => n.id === id)
    if (index !== -1) {
      notifications.value.splice(index, 1)
    }
  }
  
  // 清空所有通知
  const clearAllNotifications = () => {
    notifications.value = []
  }

  // ============ 消息提示方法 ============
  
  // 显示消息
  const showMessage = (options: string | MessageOptions) => {
    return ElMessage(options)
  }
  
  // 显示成功消息
  const showSuccessMessage = (message: string) => {
    return ElMessage.success(message)
  }
  
  // 显示错误消息
  const showErrorMessage = (message: string) => {
    return ElMessage.error(message)
  }
  
  // 显示警告消息
  const showWarningMessage = (message: string) => {
    return ElMessage.warning(message)
  }
  
  // 显示信息消息
  const showInfoMessage = (message: string) => {
    return ElMessage.info(message)
  }
  
  // 显示通知
  const showNotification = (options: NotificationOptions) => {
    return ElNotification(options)
  }
  
  // 显示确认对话框
  const showConfirm = (message: string, title = '确认', options?: Record<string, unknown>) => {
    return ElMessageBox.confirm(message, title, {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
      ...options
    })
  }
  
  // 显示提示对话框
  const showAlert = (message: string, title = '提示', options?: Record<string, unknown>) => {
    return ElMessageBox.alert(message, title, {
      confirmButtonText: '确认',
      ...options
    })
  }
  
  // 显示输入对话框
  const showPrompt = (message: string, title = '输入', options?: Record<string, unknown>) => {
    return ElMessageBox.prompt(message, title, {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      ...options
    })
  }

  // ============ 加载状态管理 ============
  
  // 设置全局加载状态
  const setGlobalLoading = (loading: boolean) => {
    globalLoading.value = loading
    pageLoading.value.global = loading
  }
  
  // 设置路由加载状态
  const setRouteLoading = (route: string, loading: boolean) => {
    if (loading) {
      pageLoading.value.routes.set(route, true)
    } else {
      pageLoading.value.routes.delete(route)
    }
  }
  
  // 设置组件加载状态
  const setComponentLoading = (component: string, loading: boolean) => {
    if (loading) {
      pageLoading.value.components.set(component, true)
    } else {
      pageLoading.value.components.delete(component)
    }
  }
  
  // 设置API加载状态
  const setApiLoading = (api: string, loading: boolean) => {
    if (loading) {
      pageLoading.value.apis.set(api, true)
    } else {
      pageLoading.value.apis.delete(api)
    }
  }
  
  // 检查是否有任何加载状态
  const hasAnyLoading = computed(() => {
    return pageLoading.value.global ||
           pageLoading.value.routes.size > 0 ||
           pageLoading.value.components.size > 0 ||
           pageLoading.value.apis.size > 0
  })

  // ============ 标签页管理 ============
  
  // 添加标签页
  const addTab = (tab: {
    name: string
    label: string
    path: string
    closable?: boolean
    icon?: string
  }) => {
    const existingIndex = tabs.value.findIndex(t => t.name === tab.name)
    if (existingIndex !== -1) {
      // 如果标签页已存在，激活它
      activeTab.value = tab.name
    } else {
      // 添加新标签页
      tabs.value.push({ closable: true, ...tab })
      activeTab.value = tab.name
    }
  }
  
  // 移除标签页
  const removeTab = (name: string) => {
    const index = tabs.value.findIndex(tab => tab.name === name)
    if (index !== -1) {
      tabs.value.splice(index, 1)
      
      // 如果删除的是当前激活的标签页，激活前一个或后一个
      if (activeTab.value === name && tabs.value.length > 0) {
        const newIndex = Math.min(index, tabs.value.length - 1)
        activeTab.value = tabs.value[newIndex].name
      }
    }
  }
  
  // 设置激活标签页
  const setActiveTab = (name: string) => {
    activeTab.value = name
  }
  
  // 关闭其他标签页
  const closeOtherTabs = (name: string) => {
    tabs.value = tabs.value.filter(tab => tab.name === name || !tab.closable)
    activeTab.value = name
  }
  
  // 关闭所有标签页
  const closeAllTabs = () => {
    tabs.value = tabs.value.filter(tab => !tab.closable)
    if (tabs.value.length > 0) {
      activeTab.value = tabs.value[0].name
    } else {
      activeTab.value = ''
    }
  }

  // ============ 面包屑导航管理 ============
  
  // 设置面包屑
  const setBreadcrumbs = (crumbs: Array<{
    label: string
    path?: string
    icon?: string
  }>) => {
    breadcrumbs.value = crumbs
  }
  
  // 添加面包屑
  const addBreadcrumb = (crumb: {
    label: string
    path?: string
    icon?: string
  }) => {
    breadcrumbs.value.push(crumb)
  }
  
  // 清空面包屑
  const clearBreadcrumbs = () => {
    breadcrumbs.value = []
  }

  // ============ 全屏管理 ============
  
  // 进入全屏
  const enterFullscreen = async () => {
    try {
      await document.documentElement.requestFullscreen()
      isFullscreen.value = true
    } catch (error) {
      console.error('进入全屏失败:', error)
    }
  }
  
  // 退出全屏
  const exitFullscreen = async () => {
    try {
      await document.exitFullscreen()
      isFullscreen.value = false
    } catch (error) {
      console.error('退出全屏失败:', error)
    }
  }
  
  // 切换全屏状态
  const toggleFullscreen = () => {
    if (isFullscreen.value) {
      exitFullscreen()
    } else {
      enterFullscreen()
    }
  }

  // ============ 主题管理 ============
  
  // 设置主题配置
  const setThemeConfig = (config: Partial<typeof themeConfig.value>) => {
    themeConfig.value = { ...themeConfig.value, ...config }
    applyThemeConfig()
  }
  
  // 应用主题配置
  const applyThemeConfig = () => {
    const root = document.documentElement
    
    // 设置CSS变量
    root.style.setProperty('--el-color-primary', themeConfig.value.primaryColor)
    root.style.setProperty('--el-border-radius-base', themeConfig.value.borderRadius)
    
    // 设置组件尺寸
    root.setAttribute('data-component-size', themeConfig.value.componentSize)
    
    // 设置暗色模式
    if (themeConfig.value.darkMode) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
  }

  // ============ 初始化和重置 ============
  
  // 初始化UI状态
  const initialize = () => {
    // 监听屏幕尺寸变化
    window.addEventListener('resize', handleResize)
    handleResize()
    
    // 监听全屏状态变化
    document.addEventListener('fullscreenchange', () => {
      isFullscreen.value = !!document.fullscreenElement
    })
    
    // 应用主题配置
    applyThemeConfig()
  }
  
  // 重置UI状态
  const reset = () => {
    globalLoading.value = false
    pageLoading.value = {
      global: false,
      routes: new Map(),
      components: new Map(),
      apis: new Map()
    }
    
    modals.value = []
    notifications.value = []
    breadcrumbs.value = []
    tabs.value = []
    activeTab.value = ''
    
    // 重置布局配置
    layoutConfig.value = {
      sidebarCollapsed: false,
      sidebarWidth: 240,
      headerHeight: 64,
      footerHeight: 48,
      showHeader: true,
      showFooter: true,
      showSidebar: true,
      showBreadcrumb: true,
      showTabs: true,
      fixedHeader: true,
      fixedSidebar: true
    }
  }
  
  // 清理资源
  const cleanup = () => {
    window.removeEventListener('resize', handleResize)
    document.removeEventListener('fullscreenchange', () => {})
  }

  // ============ 返回状态和方法 ============
  
  return {
    // 状态
    globalLoading,
    pageLoading,
    layoutConfig,
    deviceType,
    screenSize,
    modals,
    notifications,
    breadcrumbs,
    tabs,
    activeTab,
    themeConfig,
    isFullscreen,
    
    // 计算属性
    isDarkMode,
    isMobile,
    isTablet,
    isDesktop,
    unreadNotificationsCount,
    openModalsCount,
    contentStyle,
    hasAnyLoading,
    
    // 布局管理
    toggleSidebar,
    setSidebarCollapsed,
    updateLayoutConfig,
    handleResize,
    
    // 弹窗管理
    openModal,
    closeModal,
    closeAllModals,
    getModal,
    
    // 通知管理
    addNotification,
    markNotificationAsRead,
    markAllNotificationsAsRead,
    removeNotification,
    clearAllNotifications,
    
    // 消息提示
    showMessage,
    showSuccessMessage,
    showErrorMessage,
    showWarningMessage,
    showInfoMessage,
    showNotification,
    showConfirm,
    showAlert,
    showPrompt,
    
    // 加载状态管理
    setGlobalLoading,
    setRouteLoading,
    setComponentLoading,
    setApiLoading,
    
    // 标签页管理
    addTab,
    removeTab,
    setActiveTab,
    closeOtherTabs,
    closeAllTabs,
    
    // 面包屑管理
    setBreadcrumbs,
    addBreadcrumb,
    clearBreadcrumbs,
    
    // 全屏管理
    enterFullscreen,
    exitFullscreen,
    toggleFullscreen,
    
    // 主题管理
    setThemeConfig,
    applyThemeConfig,
    
    // 初始化和清理
    initialize,
    reset,
    cleanup
  }
}) 