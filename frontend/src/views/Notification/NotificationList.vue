<template>
  <div class="notification-list-page">
    <div class="page-header">
      <div class="header-left">
        <h1>通知中心</h1>
        <p class="page-description">管理和查看系统通知、交易提醒等消息</p>
      </div>
      <div class="header-actions">
        <el-button @click="markAllAsRead" :disabled="unreadCount === 0">
          <el-icon><Check /></el-icon>
          全部标记已读
        </el-button>
        <el-button @click="clearAllNotifications" type="danger" plain>
          <el-icon><Delete /></el-icon>
          清空通知
        </el-button>
      </div>
    </div>

    <!-- 过滤器和统计 -->
    <div class="filter-section">
      <el-card>
        <div class="filter-row">
          <div class="filter-left">
            <el-tabs v-model="activeFilter" @tab-change="handleFilterChange">
              <el-tab-pane label="全部" name="all">
                <template #label>
                  全部 <el-badge :value="totalCount" :hidden="totalCount === 0" />
                </template>
              </el-tab-pane>
              <el-tab-pane label="未读" name="unread">
                <template #label>
                  未读 <el-badge :value="unreadCount" :hidden="unreadCount === 0" type="danger" />
                </template>
              </el-tab-pane>
              <el-tab-pane label="系统通知" name="system">
                <template #label>
                  系统通知 <el-badge :value="systemCount" :hidden="systemCount === 0" />
                </template>
              </el-tab-pane>
              <el-tab-pane label="交易提醒" name="trading">
                <template #label>
                  交易提醒 <el-badge :value="tradingCount" :hidden="tradingCount === 0" />
                </template>
              </el-tab-pane>
              <el-tab-pane label="告警通知" name="alert">
                <template #label>
                  告警通知 <el-badge :value="alertCount" :hidden="alertCount === 0" type="warning" />
                </template>
              </el-tab-pane>
            </el-tabs>
          </div>
          <div class="filter-right">
            <el-select v-model="sortBy" placeholder="排序方式" style="width: 120px">
              <el-option label="时间倒序" value="time_desc" />
              <el-option label="时间正序" value="time_asc" />
              <el-option label="重要性" value="priority" />
            </el-select>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 通知列表 -->
    <div class="notification-list">
      <el-card v-loading="loading">
        <div v-if="filteredNotifications.length === 0" class="empty-state">
          <el-empty :description="getEmptyDescription()" />
        </div>
        <div v-else class="notification-items">
          <div
            v-for="notification in filteredNotifications"
            :key="notification.id"
            class="notification-item"
            :class="{
              'unread': !notification.read,
              'high-priority': notification.priority === 'high'
            }"
            @click="handleNotificationClick(notification)"
          >
            <div class="notification-icon">
              <el-icon :class="getIconClass(notification.type)">
                <component :is="getIcon(notification.type)" />
              </el-icon>
            </div>
            
            <div class="notification-content">
              <div class="notification-header">
                <h4 class="notification-title">{{ notification.title }}</h4>
                <div class="notification-meta">
                  <el-tag 
                    :type="getTypeTagType(notification.type)" 
                    size="small"
                  >
                    {{ getTypeLabel(notification.type) }}
                  </el-tag>
                  <el-tag 
                    v-if="notification.priority === 'high'"
                    type="danger" 
                    size="small"
                  >
                    高优先级
                  </el-tag>
                  <span class="notification-time">
                    {{ formatTime(notification.createdAt) }}
                  </span>
                </div>
              </div>
              
              <p class="notification-message">{{ notification.message }}</p>
              
              <div v-if="notification.actions?.length" class="notification-actions">
                <el-button
                  v-for="action in notification.actions"
                  :key="action.key"
                  :type="action.type || 'primary'"
                  size="small"
                  @click.stop="handleActionClick(notification, action)"
                >
                  {{ action.label }}
                </el-button>
              </div>
            </div>
            
            <div class="notification-controls">
              <el-dropdown @command="handleMenuCommand">
                <el-button text size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item 
                      :command="`${notification.read ? 'unread' : 'read'}_${notification.id}`"
                    >
                      {{ notification.read ? '标记未读' : '标记已读' }}
                    </el-dropdown-item>
                    <el-dropdown-item :command="`delete_${notification.id}`">
                      删除通知
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
        
        <!-- 分页 -->
        <div v-if="filteredNotifications.length > 0" class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="totalCount"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 通知详情弹窗 -->
    <el-dialog
      v-model="showDetailDialog"
      :title="selectedNotification?.title"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedNotification" class="notification-detail">
        <div class="detail-header">
          <div class="detail-meta">
            <el-tag :type="getTypeTagType(selectedNotification.type)">
              {{ getTypeLabel(selectedNotification.type) }}
            </el-tag>
            <span class="detail-time">
              {{ formatTime(selectedNotification.createdAt) }}
            </span>
          </div>
        </div>
        
        <div class="detail-content">
          <p>{{ selectedNotification.message }}</p>
          <div v-if="selectedNotification.details" class="detail-extra">
            <h5>详细信息：</h5>
            <pre>{{ selectedNotification.details }}</pre>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDetailDialog = false">关闭</el-button>
          <el-button 
            v-if="!selectedNotification?.read"
            type="primary" 
            @click="markAsRead(selectedNotification)"
          >
            标记已读
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Check,
  Delete,
  MoreFilled,
  Bell,
  Warning,
  InfoFilled,
  TrendCharts,
  Setting
} from '@element-plus/icons-vue'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface NotificationAction {
  key: string
  label: string
  type?: 'primary' | 'success' | 'warning' | 'danger' | 'info'
  handler?: (notification: Notification) => void
}

interface Notification {
  id: string
  type: 'system' | 'trading' | 'alert' | 'info'
  title: string
  message: string
  details?: string
  priority: 'low' | 'normal' | 'high'
  read: boolean
  createdAt: string
  actions?: NotificationAction[]
}

// 响应式数据
const loading = ref(false)
const activeFilter = ref('all')
const sortBy = ref('time_desc')
const currentPage = ref(1)
const pageSize = ref(20)
const showDetailDialog = ref(false)
const selectedNotification = ref<Notification | null>(null)

// 模拟通知数据
const notifications = ref<Notification[]>([
  {
    id: '1',
    type: 'trading',
    title: '交易执行成功',
    message: '您的买入订单已成功执行：平安银行(000001) 1000股，成交价格 ¥13.20',
    priority: 'normal',
    read: false,
    createdAt: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    actions: [
      { key: 'view_order', label: '查看订单', type: 'primary' }
    ]
  },
  {
    id: '2',
    type: 'alert',
    title: '风险警告',
    message: '您的投资组合风险度已达到80%，建议调整仓位',
    priority: 'high',
    read: false,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
    actions: [
      { key: 'adjust_position', label: '调整仓位', type: 'warning' }
    ]
  },
  {
    id: '3',
    type: 'system',
    title: '系统维护通知',
    message: '系统将于今晚23:00-01:00进行维护，期间可能影响交易功能',
    priority: 'normal',
    read: true,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString()
  },
  {
    id: '4',
    type: 'trading',
    title: '止损订单触发',
    message: '您设置的止损订单已触发：万科A(000002) 500股，止损价格 ¥17.50',
    priority: 'high',
    read: false,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
    actions: [
      { key: 'view_order', label: '查看订单', type: 'primary' }
    ]
  },
  {
    id: '5',
    type: 'info',
    title: '策略执行报告',
    message: '您的量化策略"均值回归策略"本周收益率为+3.2%，超越基准1.8%',
    priority: 'normal',
    read: true,
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(),
    actions: [
      { key: 'view_strategy', label: '查看策略', type: 'primary' }
    ]
  }
])

// 计算属性
const filteredNotifications = computed(() => {
  let filtered = notifications.value

  // 按类型过滤
  if (activeFilter.value !== 'all') {
    if (activeFilter.value === 'unread') {
      filtered = filtered.filter(n => !n.read)
    } else {
      filtered = filtered.filter(n => n.type === activeFilter.value)
    }
  }

  // 排序
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'time_asc':
        return new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime()
      case 'priority':
        const priorityOrder = { high: 3, normal: 2, low: 1 }
        return priorityOrder[b.priority] - priorityOrder[a.priority]
      default: // time_desc
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    }
  })

  return filtered
})

const totalCount = computed(() => notifications.value.length)
const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)
const systemCount = computed(() => notifications.value.filter(n => n.type === 'system').length)
const tradingCount = computed(() => notifications.value.filter(n => n.type === 'trading').length)
const alertCount = computed(() => notifications.value.filter(n => n.type === 'alert').length)

// 方法
const getIcon = (type: string) => {
  const iconMap = {
    system: Setting,
    trading: TrendCharts,
    alert: Warning,
    info: InfoFilled
  }
  return iconMap[type as keyof typeof iconMap] || Bell
}

const getIconClass = (type: string) => {
  const classMap = {
    system: 'icon-system',
    trading: 'icon-trading',
    alert: 'icon-alert',
    info: 'icon-info'
  }
  return classMap[type as keyof typeof classMap] || 'icon-default'
}

const getTypeTagType = (type: string) => {
  const typeMap = {
    system: 'info',
    trading: 'success',
    alert: 'warning',
    info: 'primary'
  }
  return typeMap[type as keyof typeof typeMap] as any
}

const getTypeLabel = (type: string) => {
  const labelMap = {
    system: '系统通知',
    trading: '交易提醒',
    alert: '告警通知',
    info: '信息通知'
  }
  return labelMap[type as keyof typeof labelMap] || '未知类型'
}

const formatTime = (time: string) => {
  return formatDistanceToNow(new Date(time), {
    addSuffix: true,
    locale: zhCN
  })
}

const getEmptyDescription = () => {
  const descriptions = {
    all: '暂无通知',
    unread: '暂无未读通知',
    system: '暂无系统通知',
    trading: '暂无交易提醒',
    alert: '暂无告警通知'
  }
  return descriptions[activeFilter.value as keyof typeof descriptions] || '暂无数据'
}

const handleFilterChange = (tabName: string) => {
  activeFilter.value = tabName
  currentPage.value = 1
}

const handleNotificationClick = (notification: Notification) => {
  selectedNotification.value = notification
  showDetailDialog.value = true
  
  if (!notification.read) {
    markAsRead(notification)
  }
}

const handleActionClick = (notification: Notification, action: NotificationAction) => {
  ElMessage.success(`执行操作：${action.label}`)
  
  if (action.handler) {
    action.handler(notification)
  }
}

const handleMenuCommand = (command: string) => {
  const [action, id] = command.split('_')
  const notification = notifications.value.find(n => n.id === id)
  
  if (!notification) return
  
  switch (action) {
    case 'read':
      markAsRead(notification)
      break
    case 'unread':
      markAsUnread(notification)
      break
    case 'delete':
      deleteNotification(notification)
      break
  }
}

const markAsRead = (notification: Notification) => {
  notification.read = true
  ElMessage.success('已标记为已读')
}

const markAsUnread = (notification: Notification) => {
  notification.read = false
  ElMessage.success('已标记为未读')
}

const markAllAsRead = () => {
  notifications.value.forEach(n => n.read = true)
  ElMessage.success('已全部标记为已读')
}

const deleteNotification = async (notification: Notification) => {
  try {
    await ElMessageBox.confirm('确定要删除这条通知吗？', '确认删除', {
      type: 'warning'
    })
    
    const index = notifications.value.findIndex(n => n.id === notification.id)
    if (index > -1) {
      notifications.value.splice(index, 1)
      ElMessage.success('通知已删除')
    }
  } catch {
    // 用户取消删除
  }
}

const clearAllNotifications = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有通知吗？此操作不可撤销。', '确认清空', {
      type: 'warning'
    })
    
    notifications.value.splice(0)
    ElMessage.success('已清空所有通知')
  } catch {
    // 用户取消清空
  }
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

onMounted(() => {
  // 初始化加载通知数据
  loading.value = true
  setTimeout(() => {
    loading.value = false
  }, 1000)
})
</script>

<style scoped>
.notification-list-page {
  padding: 24px;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #1f2937;
}

.page-description {
  color: #6b7280;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.filter-section {
  margin-bottom: 24px;
}

.filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.notification-list .el-card {
  min-height: 400px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.notification-items {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.notification-item {
  display: flex;
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.notification-item:hover {
  background-color: #f9fafb;
}

.notification-item.unread {
  background-color: #fef3c7;
  border-left: 4px solid #f59e0b;
}

.notification-item.high-priority {
  border-left: 4px solid #ef4444;
}

.notification-icon {
  margin-right: 16px;
  flex-shrink: 0;
}

.notification-icon .el-icon {
  font-size: 24px;
  padding: 8px;
  border-radius: 50%;
}

.icon-system {
  color: #3b82f6;
  background-color: #eff6ff;
}

.icon-trading {
  color: #10b981;
  background-color: #ecfdf5;
}

.icon-alert {
  color: #f59e0b;
  background-color: #fffbeb;
}

.icon-info {
  color: #6366f1;
  background-color: #eef2ff;
}

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.notification-title {
  font-size: 16px;
  font-weight: 500;
  margin: 0;
  color: #1f2937;
}

.notification-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.notification-time {
  font-size: 12px;
  color: #6b7280;
}

.notification-message {
  color: #4b5563;
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.notification-actions {
  display: flex;
  gap: 8px;
}

.notification-controls {
  margin-left: 16px;
  flex-shrink: 0;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #f3f4f6;
}

.notification-detail .detail-header {
  margin-bottom: 16px;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-time {
  font-size: 14px;
  color: #6b7280;
}

.detail-content {
  line-height: 1.6;
}

.detail-extra {
  margin-top: 16px;
  padding: 16px;
  background-color: #f9fafb;
  border-radius: 8px;
}

.detail-extra h5 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.detail-extra pre {
  margin: 0;
  font-size: 12px;
  color: #6b7280;
  white-space: pre-wrap;
  word-break: break-word;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .notification-list-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-actions {
    align-self: stretch;
  }
  
  .filter-row {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .notification-item {
    padding: 12px;
  }
  
  .notification-header {
    flex-direction: column;
    gap: 8px;
  }
  
  .notification-meta {
    justify-content: flex-start;
  }
}
</style> 