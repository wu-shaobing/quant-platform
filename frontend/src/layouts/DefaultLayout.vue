<template>
  <div class="default-layout">
    <!-- 侧边栏 -->
    <aside
      :class="[
        'layout-sidebar',
        {
          'layout-sidebar--collapsed': sidebarCollapsed,
          'layout-sidebar--mobile': isMobile
        }
      ]"
    >
      <div class="sidebar-header">
        <div class="logo">
          <img src="/favicon.ico" alt="Logo" class="logo-image" />
          <span v-show="!sidebarCollapsed" class="logo-text">量化平台</span>
        </div>
        
        <el-button
          v-if="!isMobile"
          text
          :icon="sidebarCollapsed ? 'Expand' : 'Fold'"
          @click="toggleSidebar"
        />
      </div>
      
      <nav class="sidebar-nav">
        <el-menu
          :default-active="activeMenu"
          :collapse="sidebarCollapsed"
          :unique-opened="true"
          router
          @select="handleMenuSelect"
        >
          <template v-for="item in menuItems" :key="item.path">
            <!-- 单级菜单 -->
            <el-menu-item
              v-if="!item.children"
              :index="item.path"
              :disabled="item.disabled"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>
            
            <!-- 多级菜单 -->
            <el-sub-menu
              v-else
              :index="item.path"
              :disabled="item.disabled"
            >
              <template #title>
                <el-icon><component :is="item.icon" /></el-icon>
                <span>{{ item.title }}</span>
              </template>
              
              <el-menu-item
                v-for="child in item.children"
                :key="child.path"
                :index="child.path"
                :disabled="child.disabled"
              >
                <el-icon><component :is="child.icon" /></el-icon>
                <template #title>{{ child.title }}</template>
              </el-menu-item>
            </el-sub-menu>
          </template>
        </el-menu>
      </nav>
    </aside>
    
    <!-- 主内容区域 -->
    <div class="layout-main">
      <!-- 顶部导航栏 -->
      <header class="layout-header">
        <div class="header-left">
          <el-button
            v-if="isMobile"
            text
            :icon="'Menu'"
            @click="toggleSidebar"
          />
          
          <el-breadcrumb separator="/">
            <el-breadcrumb-item
              v-for="item in breadcrumbs"
              :key="item.path"
              :to="item.path"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 通知中心 -->
          <el-badge :value="unreadCount" :hidden="!hasUnread" class="notification-badge">
            <el-button
              text
              :icon="'Bell'"
              @click="showNotifications = true"
            />
          </el-badge>
          
          <!-- 主题切换 -->
          <el-button
            text
            :icon="themeIcon"
            @click="toggleTheme"
          />
          
          <!-- 全屏切换 -->
          <el-button
            text
            :icon="isFullscreen ? 'FullScreen' : 'FullScreen'"
            @click="toggleFullscreen"
          />
          
          <!-- 用户菜单 -->
          <el-dropdown @command="handleUserCommand">
            <div class="user-avatar">
              <el-avatar :src="currentUser?.avatar" :size="32">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span v-if="!isMobile" class="username">{{ currentUser?.username }}</span>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </div>
            
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人资料
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      
      <!-- 页面内容 -->
      <main class="layout-content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-slide" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" :key="route.path" />
            </keep-alive>
          </transition>
        </router-view>
      </main>
    </div>
    
    <!-- 移动端遮罩 -->
    <div
      v-if="isMobile && !sidebarCollapsed"
      class="layout-overlay"
      @click="closeSidebar"
    />
    
    <!-- 通知抽屉 -->
    <el-drawer
      v-model="showNotifications"
      title="通知中心"
      direction="rtl"
      :size="isMobile ? '100%' : '400px'"
    >
      <div class="notifications-content">
        <div v-if="!hasUnread" class="no-notifications">
          <el-empty description="暂无通知" />
        </div>
        
        <div v-else class="notifications-list">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            :class="[
              'notification-item',
              {
                'notification-item--unread': !notification.read
              }
            ]"
            @click="markAsRead(notification.id)"
          >
            <div class="notification-icon">
              <el-icon :class="`notification-icon--${notification.level}`">
                <component :is="getNotificationIcon(notification.type)" />
              </el-icon>
            </div>
            
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.message }}</div>
              <div class="notification-time">
                {{ formatRelativeTime(notification.timestamp) }}
              </div>
            </div>
            
            <el-button
              text
              size="small"
              :icon="'Close'"
              @click.stop="removeNotification(notification.id)"
            />
          </div>
        </div>
        
        <div v-if="hasUnread" class="notifications-actions">
          <el-button type="primary" @click="markAllAsRead">
            全部标记为已读
          </el-button>
          <el-button @click="clearAllNotifications">
            清空所有通知
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  User,
  Setting,
  SwitchButton,
  ArrowDown
} from '@element-plus/icons-vue'
import { useAuth } from '@/composables/useAuth'
import { useTheme } from '@/composables/useTheme'
import { useNotification } from '@/composables/useNotification'
import { useBreakpoints } from '@/composables/core/useMediaQuery'
import { useFullscreen } from '@/composables/core/useFullscreen'
import { formatRelativeTime } from '@/utils/formatters'

// 组合式函数
const route = useRoute()
const router = useRouter()
const { currentUser, logout } = useAuth()
const { getThemeIcon, toggleTheme } = useTheme()
const { 
  notifications, 
  unreadCount, 
  hasUnread, 
  markAsRead, 
  markAllAsRead, 
  removeNotification, 
  clearAllNotifications 
} = useNotification()
const { isMobile } = useBreakpoints()
const { isFullscreen, toggle: toggleFullscreen } = useFullscreen()

// 响应式状态
const sidebarCollapsed = ref(false)
const showNotifications = ref(false)
const cachedViews = ref<string[]>([])

// 菜单配置
const menuItems = ref([
  {
    path: '/dashboard',
    title: '仪表盘',
    icon: 'Monitor'
  },
  {
    path: '/market',
    title: '行情中心',
    icon: 'TrendCharts'
  },
  {
    path: '/trading',
    title: '交易中心',
    icon: 'Document',
    children: [
      {
        path: '/trading/terminal',
        title: '交易终端',
        icon: 'Monitor'
      },
      {
        path: '/trading/orders',
        title: '订单管理',
        icon: 'Document'
      },
      {
        path: '/trading/positions',
        title: '持仓管理',
        icon: 'PieChart'
      }
    ]
  },
  {
    path: '/strategy',
    title: '策略中心',
    icon: 'DataAnalysis',
    children: [
      {
        path: '/strategy/hub',
        title: '策略中心',
        icon: 'Monitor'
      },
      {
        path: '/strategy/develop',
        title: '策略开发',
        icon: 'Document'
      },
      {
        path: '/strategy/monitor',
        title: '策略监控',
        icon: 'TrendCharts'
      }
    ]
  },
  {
    path: '/backtest',
    title: '回测分析',
    icon: 'DataAnalysis'
  },
  {
    path: '/portfolio',
    title: '投资组合',
    icon: 'PieChart'
  },
  {
    path: '/risk',
    title: '风险管理',
    icon: 'Warning'
  },
  {
    path: '/demo',
    title: '组件展示',
    icon: 'Grid'
  }
])

// 计算属性
const activeMenu = computed(() => route.path)

const themeIcon = computed(() => getThemeIcon.value)

const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched.map(item => ({
    path: item.path,
    title: item.meta?.title || ''
  }))
})

// 方法
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const closeSidebar = () => {
  if (isMobile.value) {
    sidebarCollapsed.value = true
  }
}

const handleMenuSelect = (_index: string) => {
  if (isMobile.value) {
    sidebarCollapsed.value = true
  }
}

const handleUserCommand = (command: string) => {
  switch (command) {
    case 'profile':
      router.push('/settings/profile')
      break
    case 'settings':
      router.push('/settings')
      break
    case 'logout':
      logout()
      break
  }
}

const getNotificationIcon = (type: string) => {
  const iconMap: Record<string, string> = {
    order: 'Document',
    trade: 'TrendCharts',
    price_alert: 'Bell',
    strategy: 'DataAnalysis',
    risk: 'Warning',
    system: 'Monitor'
  }
  return iconMap[type] || 'Bell'
}

// 响应式处理
const handleResize = () => {
  if (isMobile.value) {
    sidebarCollapsed.value = true
  }
}

// 生命周期
onMounted(() => {
  window.addEventListener('resize', handleResize)
  handleResize()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped lang="scss">
.default-layout {
  display: flex;
  height: 100vh;
  background-color: var(--el-bg-color-page);
}

.layout-sidebar {
  width: 256px;
  background-color: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  transition: all 0.3s ease;
  z-index: 1000;
  
  &--collapsed {
    width: 64px;
    
    .logo-text {
      opacity: 0;
    }
  }
  
  &--mobile {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    transform: translateX(-100%);
    
    &:not(.layout-sidebar--collapsed) {
      transform: translateX(0);
    }
  }
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  
  &-image {
    width: 32px;
    height: 32px;
  }
  
  &-text {
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    transition: opacity 0.3s ease;
  }
}

.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  
  :deep(.el-menu) {
    border-right: none;
  }
}

.layout-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  padding: 0 24px;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.notification-badge {
  :deep(.el-badge__content) {
    font-size: 10px;
  }
}

.user-avatar {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background-color 0.3s ease;
  
  &:hover {
    background-color: var(--el-fill-color-light);
  }
  
  .username {
    font-size: 14px;
    color: var(--el-text-color-primary);
  }
  
  .dropdown-icon {
    font-size: 12px;
    color: var(--el-text-color-regular);
  }
}

.layout-content {
  flex: 1;
  overflow: auto;
  padding: 24px;
}

.layout-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
}

.notifications-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.notifications-list {
  flex: 1;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background-color 0.3s ease;
  
  &:hover {
    background-color: var(--el-fill-color-light);
  }
  
  &--unread {
    background-color: var(--el-color-primary-light-9);
    
    .notification-title {
      font-weight: 600;
    }
  }
}

.notification-icon {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  
  &--info {
    background-color: var(--el-color-info-light-8);
    color: var(--el-color-info);
  }
  
  &--success {
    background-color: var(--el-color-success-light-8);
    color: var(--el-color-success);
  }
  
  &--warning {
    background-color: var(--el-color-warning-light-8);
    color: var(--el-color-warning);
  }
  
  &--error {
    background-color: var(--el-color-error-light-8);
    color: var(--el-color-error);
  }
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.notification-message {
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.4;
  margin-bottom: 4px;
}

.notification-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.notifications-actions {
  padding: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  display: flex;
  gap: 12px;
}

.no-notifications {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

// 过渡动画
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

// 响应式设计
@media (max-width: 768px) {
  .layout-header {
    padding: 0 16px;
  }
  
  .layout-content {
    padding: 16px;
  }
  
  .header-left {
    gap: 8px;
  }
  
  .header-right {
    gap: 8px;
  }
  
  .notifications-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
}
</style>