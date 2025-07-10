<template>
  <el-card class="strategy-card" :class="{ 'is-running': strategy.status === 'running' }">
    <template #header>
      <div class="card-header">
        <div class="strategy-info">
          <h3 class="strategy-name">{{ strategy.name }}</h3>
          <el-tag :type="getStatusType(strategy.status)" size="small">
            {{ getStatusText(strategy.status) }}
          </el-tag>
        </div>
        <div class="strategy-actions">
          <el-dropdown @command="handleCommand">
            <el-button type="text">
              <el-icon><MoreFilled /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="view">查看详情</el-dropdown-item>
                <el-dropdown-item command="edit">编辑策略</el-dropdown-item>
                <el-dropdown-item command="clone">克隆策略</el-dropdown-item>
                <el-dropdown-item command="export">导出策略</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除策略</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </template>

    <div class="strategy-content">
      <!-- 策略描述 -->
      <p class="strategy-description">{{ strategy.description || '暂无描述' }}</p>
      
      <!-- 策略标签 -->
      <div class="strategy-tags" v-if="strategy.tags && strategy.tags.length">
        <el-tag 
          v-for="tag in strategy.tags" 
          :key="tag" 
          size="small" 
          effect="plain"
        >
          {{ tag }}
        </el-tag>
      </div>

      <!-- 性能指标 -->
      <div class="performance-metrics">
        <div class="metric-row">
          <div class="metric-item">
            <span class="metric-label">总收益率</span>
            <span class="metric-value" :class="strategy.totalReturn >= 0 ? 'profit' : 'loss'">
              {{ strategy.totalReturn >= 0 ? '+' : '' }}{{ formatPercent(strategy.totalReturn) }}
            </span>
          </div>
          <div class="metric-item">
            <span class="metric-label">夏普比率</span>
            <span class="metric-value">{{ strategy.sharpeRatio?.toFixed(2) || '--' }}</span>
          </div>
        </div>
        <div class="metric-row">
          <div class="metric-item">
            <span class="metric-label">最大回撤</span>
            <span class="metric-value loss">{{ formatPercent(strategy.maxDrawdown) }}</span>
          </div>
          <div class="metric-item">
            <span class="metric-label">胜率</span>
            <span class="metric-value">{{ formatPercent(strategy.winRate) }}</span>
          </div>
        </div>
      </div>

      <!-- 运行状态 -->
      <div class="strategy-status" v-if="strategy.status === 'running'">
        <div class="status-item">
          <span class="status-label">运行时间</span>
          <span class="status-value">{{ formatDuration(strategy.runTime) }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">当日盈亏</span>
          <span class="status-value" :class="strategy.todayPnl >= 0 ? 'profit' : 'loss'">
            {{ strategy.todayPnl >= 0 ? '+' : '' }}{{ formatNumber(strategy.todayPnl) }}
          </span>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="card-footer">
        <div class="strategy-meta">
          <span class="meta-item">
            <el-icon><User /></el-icon>
            {{ strategy.author || '系统' }}
          </span>
          <span class="meta-item">
            <el-icon><Calendar /></el-icon>
            {{ formatDate(strategy.createdAt) }}
          </span>
        </div>
        <div class="strategy-controls">
          <el-button 
            v-if="strategy.status === 'stopped'"
            type="success" 
            size="small"
            @click="startStrategy"
            :loading="loading"
          >
            启动
          </el-button>
          <el-button 
            v-if="strategy.status === 'running'"
            type="warning" 
            size="small"
            @click="stopStrategy"
            :loading="loading"
          >
            停止
          </el-button>
          <el-button 
            type="primary" 
            size="small"
            @click="viewStrategy"
          >
            查看
          </el-button>
        </div>
      </div>
    </template>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { MoreFilled, User, Calendar } from '@element-plus/icons-vue'

interface Strategy {
  id: string
  name: string
  description?: string
  status: 'running' | 'stopped' | 'error'
  tags?: string[]
  totalReturn: number
  sharpeRatio?: number
  maxDrawdown: number
  winRate: number
  runTime?: number
  todayPnl?: number
  author?: string
  createdAt: string
}

interface Props {
  strategy: Strategy
}

interface Emits {
  (e: 'start', id: string): void
  (e: 'stop', id: string): void
  (e: 'view', id: string): void
  (e: 'edit', id: string): void
  (e: 'clone', id: string): void
  (e: 'export', id: string): void
  (e: 'delete', id: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const loading = ref(false)

// 获取状态类型
const getStatusType = (status: string): string => {
  const types = {
    running: 'success',
    stopped: 'info',
    error: 'danger'
  }
  return types[status] || 'info'
}

// 获取状态文本
const getStatusText = (status: string): string => {
  const texts = {
    running: '运行中',
    stopped: '已停止',
    error: '异常'
  }
  return texts[status] || status
}

// 格式化百分比
const formatPercent = (value: number): string => {
  return (value * 100).toFixed(2) + '%'
}

// 格式化数字
const formatNumber = (value: number): string => {
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 格式化时长
const formatDuration = (ms: number): string => {
  if (!ms) return '0分钟'
  const hours = Math.floor(ms / 3600000)
  const minutes = Math.floor((ms % 3600000) / 60000)
  return hours > 0 ? `${hours}小时${minutes}分钟` : `${minutes}分钟`
}

// 格式化日期
const formatDate = (date: string): string => {
  return new Date(date).toLocaleDateString('zh-CN')
}

// 启动策略
const startStrategy = async () => {
  try {
    await ElMessageBox.confirm(`确定要启动策略"${props.strategy.name}"吗？`, '确认启动', {
      type: 'warning'
    })
    
    loading.value = true
    emit('start', props.strategy.id)
  } catch {
    // 用户取消
  } finally {
    loading.value = false
  }
}

// 停止策略
const stopStrategy = async () => {
  try {
    await ElMessageBox.confirm(`确定要停止策略"${props.strategy.name}"吗？`, '确认停止', {
      type: 'warning'
    })
    
    loading.value = true
    emit('stop', props.strategy.id)
  } catch {
    // 用户取消
  } finally {
    loading.value = false
  }
}

// 查看策略
const viewStrategy = () => {
  emit('view', props.strategy.id)
}

// 处理下拉菜单命令
const handleCommand = (command: string) => {
  switch (command) {
    case 'view':
      emit('view', props.strategy.id)
      break
    case 'edit':
      emit('edit', props.strategy.id)
      break
    case 'clone':
      emit('clone', props.strategy.id)
      break
    case 'export':
      emit('export', props.strategy.id)
      break
    case 'delete':
      handleDelete()
      break
  }
}

// 删除策略
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除策略"${props.strategy.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        type: 'error',
        confirmButtonText: '删除',
        confirmButtonClass: 'el-button--danger'
      }
    )
    
    emit('delete', props.strategy.id)
  } catch {
    // 用户取消
  }
}
</script>

<style scoped>
.strategy-card {
  margin-bottom: 16px;
  transition: all 0.3s ease;
  border: 1px solid #e4e7ed;
}

.strategy-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.strategy-card.is-running {
  border-left: 4px solid #67c23a;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.strategy-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.strategy-actions {
  display: flex;
  gap: 8px;
}

.strategy-content {
  padding: 0;
}

.strategy-description {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.strategy-tags {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.performance-metrics {
  margin-bottom: 16px;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.metric-row:last-child {
  margin-bottom: 0;
}

.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.metric-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.metric-value.profit {
  color: #f56c6c;
}

.metric-value.loss {
  color: #67c23a;
}

.strategy-status {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  display: flex;
  justify-content: space-between;
}

.status-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.status-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.status-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.status-value.profit {
  color: #f56c6c;
}

.status-value.loss {
  color: #67c23a;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.strategy-meta {
  display: flex;
  gap: 16px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #909399;
}

.strategy-controls {
  display: flex;
  gap: 8px;
}
</style> 