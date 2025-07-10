<template>
  <div class="test-slider-page">
    <div class="page-header">
      <h1 class="page-title">滑轨验证码测试页面</h1>
      <p class="page-description">参考 Vue Vben Admin 设计的现代化滑轨验证码组件</p>
    </div>

    <div class="test-grid">
      <!-- 基础示例 -->
      <div class="test-card">
        <h3 class="test-title">基础示例</h3>
        <p class="test-desc">最基本的滑轨验证码，简单滑动到最右边即可</p>
        <div class="test-content">
          <SliderCaptcha
            ref="slider1"
            :width="350"
            :height="42"
            :show-image="false"
            @success="handleSuccess"
            @error="handleError"
          />
          <el-button class="reset-btn" @click="resetSlider('slider1')">重置</el-button>
        </div>
      </div>

      <!-- 图片验证模式 -->
      <div class="test-card">
        <h3 class="test-title">图片验证模式</h3>
        <p class="test-desc">带背景图片的拼图验证，需要将拼图拖到正确位置</p>
        <div class="test-content">
          <SliderCaptcha
            ref="slider2"
            :width="350"
            :height="42"
            :show-image="true"
            @success="handleSuccess"
            @error="handleError"
          />
          <el-button class="reset-btn" @click="resetSlider('slider2')">重置</el-button>
        </div>
      </div>

      <!-- 自定义样式 -->
      <div class="test-card">
        <h3 class="test-title">自定义样式</h3>
        <p class="test-desc">自定义文本和图标的滑轨验证码</p>
        <div class="test-content">
          <SliderCaptcha
            ref="slider3"
            :width="350"
            :height="48"
            :show-image="false"
            success-text="验证通过 ✓"
            default-text="向右滑动解锁"
            error-text="验证失败，请重试"
            @success="handleSuccess"
            @error="handleError"
          >
            <template #text="{ isSuccess, isDragging }">
              <div class="flex items-center justify-center">
                <Shield v-if="isSuccess" class="w-4 h-4 mr-2 text-green-500" />
                <Zap v-else-if="isDragging" class="w-4 h-4 mr-2 text-yellow-500 animate-pulse" />
                <Lock v-else class="w-4 h-4 mr-2 text-gray-400" />
                <span class="font-medium">
                  {{ isSuccess ? '安全验证通过' : isDragging ? '正在验证中...' : '向右滑动进行安全验证' }}
                </span>
              </div>
            </template>
            <template #icon="{ isSuccess, isDragging }">
              <Shield v-if="isSuccess" class="w-5 h-5 text-white" />
              <Zap v-else-if="isDragging" class="w-5 h-5 text-yellow-500 animate-spin" />
              <ArrowRight v-else class="w-5 h-5 text-blue-500" />
            </template>
          </SliderCaptcha>
          <el-button class="reset-btn" @click="resetSlider('slider3')">重置</el-button>
        </div>
      </div>

      <!-- 小尺寸版本 -->
      <div class="test-card">
        <h3 class="test-title">小尺寸版本</h3>
        <p class="test-desc">适用于移动端或空间有限的场景</p>
        <div class="test-content">
          <SliderCaptcha
            ref="slider4"
            :width="280"
            :height="36"
            :show-image="false"
            :show-refresh="false"
            success-text="完成"
            default-text="滑动验证"
            @success="handleSuccess"
            @error="handleError"
          />
          <el-button class="reset-btn" @click="resetSlider('slider4')">重置</el-button>
        </div>
      </div>

      <!-- 禁用状态 -->
      <div class="test-card">
        <h3 class="test-title">禁用状态</h3>
        <p class="test-desc">禁用的滑轨验证码，无法进行交互</p>
        <div class="test-content">
          <SliderCaptcha
            ref="slider5"
            :width="350"
            :height="42"
            :show-image="false"
            :disabled="true"
            default-text="验证码已禁用"
            @success="handleSuccess"
            @error="handleError"
          />
          <el-button class="reset-btn" @click="toggleDisabled">
            {{ isDisabled ? '启用' : '禁用' }}
          </el-button>
        </div>
      </div>

      <!-- 事件监听示例 -->
      <div class="test-card">
        <h3 class="test-title">事件监听示例</h3>
        <p class="test-desc">展示拖拽过程中的各种事件</p>
        <div class="test-content">
          <SliderCaptcha
            ref="slider6"
            :width="350"
            :height="42"
            :show-image="false"
            @success="handleSuccess"
            @error="handleError"
            @start="handleStart"
            @move="handleMove"
            @end="handleEnd"
          />
          <el-button class="reset-btn" @click="resetSlider('slider6')">重置</el-button>
          
          <!-- 事件日志 -->
          <div class="event-log">
            <h4>事件日志：</h4>
            <div class="log-content">
              <div v-for="(log, index) in eventLogs" :key="index" class="log-item">
                <span class="log-time">{{ log.time }}</span>
                <span class="log-type" :class="log.type">{{ log.type }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="stats-section">
      <h2>验证统计</h2>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">{{ stats.totalAttempts }}</div>
          <div class="stat-label">总尝试次数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.successCount }}</div>
          <div class="stat-label">成功次数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.failureCount }}</div>
          <div class="stat-label">失败次数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ stats.averageTime }}s</div>
          <div class="stat-label">平均用时</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Shield, Zap, Lock, ArrowRight } from 'lucide-vue-next'
import SliderCaptcha from '@/components/SliderCaptcha.vue'

// 滑块引用
const slider1 = ref()
const slider2 = ref()
const slider3 = ref()
const slider4 = ref()
const slider5 = ref()
const slider6 = ref()

// 状态管理
const isDisabled = ref(false)

// 事件日志
const eventLogs = ref<Array<{
  time: string
  type: string
  message: string
}>>([])

// 统计数据
const stats = reactive({
  totalAttempts: 0,
  successCount: 0,
  failureCount: 0,
  totalTime: 0
})

// 计算平均时间
const averageTime = computed(() => {
  if (stats.successCount === 0) return 0
  return (stats.totalTime / stats.successCount).toFixed(2)
})

// 添加事件日志
const addLog = (type: string, message: string) => {
  const time = new Date().toLocaleTimeString()
  eventLogs.value.unshift({ time, type, message })
  
  // 保持最多20条日志
  if (eventLogs.value.length > 20) {
    eventLogs.value = eventLogs.value.slice(0, 20)
  }
}

// 成功回调
const handleSuccess = (token: string, time: number) => {
  stats.totalAttempts++
  stats.successCount++
  stats.totalTime += time
  
  addLog('success', `验证成功，耗时 ${time} 秒，令牌: ${token.substring(0, 10)}...`)
  ElMessage.success(`验证成功！耗时 ${time} 秒`)
}

// 失败回调
const handleError = (message: string) => {
  stats.totalAttempts++
  stats.failureCount++
  
  addLog('error', `验证失败: ${message}`)
  ElMessage.error(message)
}

// 开始拖拽
const handleStart = (event: MouseEvent | TouchEvent) => {
  addLog('start', '开始拖拽验证')
}

// 拖拽移动
const handleMove = (data: { moveX: number, moveDistance: number, event: MouseEvent | TouchEvent }) => {
  addLog('move', `拖拽中，当前位置: ${Math.round(data.moveX)}px`)
}

// 结束拖拽
const handleEnd = (event: MouseEvent | TouchEvent) => {
  addLog('end', '结束拖拽')
}

// 重置滑块
const resetSlider = (sliderRef: string) => {
  const slider = eval(sliderRef)
  if (slider.value) {
    slider.value.reset()
    addLog('reset', `重置滑块: ${sliderRef}`)
  }
}

// 切换禁用状态
const toggleDisabled = () => {
  isDisabled.value = !isDisabled.value
  addLog('toggle', `${isDisabled.value ? '禁用' : '启用'}滑块`)
}

// 更新统计数据中的平均时间
Object.defineProperty(stats, 'averageTime', {
  get: () => averageTime.value
})
</script>

<style scoped>
.test-slider-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 24px;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 12px 0;
}

.page-description {
  font-size: 18px;
  color: #718096;
  margin: 0;
}

.test-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.test-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.test-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.test-title {
  font-size: 20px;
  font-weight: 600;
  color: #2d3748;
  margin: 0 0 8px 0;
}

.test-desc {
  font-size: 14px;
  color: #718096;
  margin: 0 0 20px 0;
  line-height: 1.5;
}

.test-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reset-btn {
  align-self: flex-start;
}

.event-log {
  margin-top: 16px;
  padding: 16px;
  background: #f7fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.event-log h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #4a5568;
}

.log-content {
  max-height: 200px;
  overflow-y: auto;
}

.log-item {
  display: flex;
  gap: 8px;
  padding: 4px 0;
  font-size: 12px;
  border-bottom: 1px solid #e2e8f0;
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  color: #718096;
  min-width: 80px;
}

.log-type {
  min-width: 60px;
  font-weight: 600;
  text-transform: uppercase;
}

.log-type.success {
  color: #38a169;
}

.log-type.error {
  color: #e53e3e;
}

.log-type.start,
.log-type.move,
.log-type.end,
.log-type.reset,
.log-type.toggle {
  color: #3182ce;
}

.log-message {
  color: #2d3748;
  flex: 1;
}

.stats-section {
  background: white;
  border-radius: 16px;
  padding: 32px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stats-section h2 {
  font-size: 24px;
  font-weight: 600;
  color: #2d3748;
  margin: 0 0 24px 0;
  text-align: center;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.stat-item {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .test-grid {
    grid-template-columns: 1fr;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .page-description {
    font-size: 16px;
  }
  
  .test-card {
    padding: 16px;
  }
  
  .stats-section {
    padding: 24px;
  }
}
</style> 