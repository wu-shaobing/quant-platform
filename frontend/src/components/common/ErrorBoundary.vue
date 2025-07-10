<template>
  <div class="error-boundary">
    <slot v-if="!hasError" />
    
    <!-- 错误显示界面 -->
    <div v-else class="error-display">
      <div class="error-icon">
        <el-icon size="48" color="#f56c6c">
          <Warning />
        </el-icon>
      </div>
      
      <div class="error-content">
        <h3 class="error-title">{{ errorTitle }}</h3>
        <p class="error-message">{{ errorMessage }}</p>
        
        <div v-if="showDetails" class="error-details">
          <el-collapse>
            <el-collapse-item title="错误详情">
              <pre class="error-stack">{{ errorStack }}</pre>
            </el-collapse-item>
          </el-collapse>
        </div>
        
        <div class="error-actions">
          <el-button type="primary" @click="handleRetry">
            重试
          </el-button>
          <el-button @click="handleReload">
            刷新页面
          </el-button>
          <el-button v-if="!showDetails" text @click="showDetails = true">
            查看详情
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { Warning } from '@element-plus/icons-vue'

interface Props {
  fallbackTitle?: string
  fallbackMessage?: string
  showRetry?: boolean
  onRetry?: () => void
}

const props = withDefaults(defineProps<Props>(), {
  fallbackTitle: '组件发生错误',
  fallbackMessage: '抱歉，组件运行时发生了错误。请尝试刷新页面或联系技术支持。',
  showRetry: true
})

const emit = defineEmits<{
  (e: 'error', error: Error): void
  (e: 'retry'): void
}>()

// 错误状态
const hasError = ref(false)
const errorTitle = ref('')
const errorMessage = ref('')
const errorStack = ref('')
const showDetails = ref(false)

// 捕获错误
onErrorCaptured((error: Error, instance, info) => {
  console.error('ErrorBoundary captured error:', error)
  
  hasError.value = true
  errorTitle.value = props.fallbackTitle
  errorMessage.value = error.message || props.fallbackMessage
  errorStack.value = error.stack || '无堆栈信息'
  
  // 发送错误事件
  emit('error', error)
  
  // 报告错误到监控系统
  reportError(error, {
    component: instance?.$options?.name || 'Unknown',
    errorInfo: info,
    timestamp: new Date().toISOString()
  })
  
  // 阻止错误继续传播
  return false
})

// 重试处理
const handleRetry = () => {
  if (props.onRetry) {
    props.onRetry()
  }
  
  // 重置错误状态
  hasError.value = false
  showDetails.value = false
  
  emit('retry')
}

// 刷新页面
const handleReload = () => {
  window.location.reload()
}

// 错误报告函数
const reportError = (error: Error, context: Record<string, unknown>) => {
  // 这里可以集成Sentry或其他错误监控服务
  if (import.meta.env.PROD) {
    // 生产环境错误上报
    console.error('Error reported:', { error, context })
  }
}
</script>

<style scoped>
.error-boundary {
  width: 100%;
  height: 100%;
}

.error-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  padding: 40px 20px;
  text-align: center;
}

.error-icon {
  margin-bottom: 24px;
}

.error-content {
  max-width: 600px;
  width: 100%;
}

.error-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 12px;
}

.error-message {
  font-size: 16px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 24px;
}

.error-details {
  margin-bottom: 24px;
  text-align: left;
}

.error-stack {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.error-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}

@media (max-width: 768px) {
  .error-display {
    padding: 20px 16px;
  }
  
  .error-title {
    font-size: 20px;
  }
  
  .error-message {
    font-size: 14px;
  }
  
  .error-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .error-actions .el-button {
    width: 100%;
    max-width: 200px;
  }
}
</style> 