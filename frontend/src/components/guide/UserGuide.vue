<template>
  <div class="user-guide">
    <!-- 引导遮罩层 -->
    <div
      v-if="isActive"
      class="guide-overlay"
      :class="{ 'guide-overlay--active': isActive }"
    >
      <!-- 高亮区域 -->
      <div
        v-if="currentStep"
        class="guide-spotlight"
        :style="spotlightStyle"
      ></div>
      
      <!-- 引导卡片 -->
      <div
        v-if="currentStep"
        class="guide-card"
        :style="cardStyle"
      >
        <div class="guide-card__header">
          <h3 class="guide-card__title">{{ currentStep.title }}</h3>
          <div class="guide-card__progress">
            {{ currentStepIndex + 1 }} / {{ steps.length }}
          </div>
        </div>
        
        <div class="guide-card__content">
          <div class="guide-card__description">
            {{ currentStep.description }}
          </div>
          
          <!-- 图片或视频 -->
          <div v-if="currentStep.media" class="guide-card__media">
            <img
              v-if="currentStep.media.type === 'image'"
              :src="currentStep.media.url"
              :alt="currentStep.title"
              class="guide-media__image"
            />
            <video
              v-else-if="currentStep.media.type === 'video'"
              :src="currentStep.media.url"
              controls
              class="guide-media__video"
            />
          </div>
          
          <!-- 交互式演示 -->
          <div v-if="currentStep.interactive" class="guide-card__interactive">
            <component
              :is="currentStep.interactive.component"
              v-bind="currentStep.interactive.props"
              @complete="handleInteractiveComplete"
            />
          </div>
          
          <!-- 提示列表 -->
          <ul v-if="currentStep.tips" class="guide-card__tips">
            <li v-for="tip in currentStep.tips" :key="tip" class="guide-tip">
              <el-icon class="guide-tip__icon"><InfoFilled /></el-icon>
              {{ tip }}
            </li>
          </ul>
        </div>
        
        <div class="guide-card__actions">
          <el-button
            v-if="currentStepIndex > 0"
            @click="previousStep"
            size="small"
          >
            上一步
          </el-button>
          
          <el-button
            v-if="currentStep.interactive && !interactiveCompleted"
            type="primary"
            @click="handleTryIt"
            size="small"
          >
            试一试
          </el-button>
          
          <el-button
            v-if="!currentStep.interactive || interactiveCompleted"
            type="primary"
            @click="nextStep"
            size="small"
          >
            {{ currentStepIndex < steps.length - 1 ? '下一步' : '完成' }}
          </el-button>
          
          <el-button
            @click="skipGuide"
            size="small"
            text
          >
            跳过引导
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 引导启动按钮 -->
    <el-button
      v-if="!isActive && showStartButton"
      class="guide-start-button"
      type="primary"
      circle
      size="large"
      @click="startGuide"
    >
      <el-icon><QuestionFilled /></el-icon>
    </el-button>
    
    <!-- 引导菜单 -->
    <el-drawer
      v-model="showGuideMenu"
      title="用户引导"
      direction="rtl"
      size="400px"
    >
      <div class="guide-menu">
        <div class="guide-menu__section">
          <h4>快速入门</h4>
          <div class="guide-menu__items">
            <div
              v-for="guide in quickStartGuides"
              :key="guide.id"
              class="guide-menu__item"
              @click="startSpecificGuide(guide.id)"
            >
              <el-icon class="guide-menu__icon">
                <component :is="guide.icon" />
              </el-icon>
              <div class="guide-menu__info">
                <div class="guide-menu__title">{{ guide.title }}</div>
                <div class="guide-menu__desc">{{ guide.description }}</div>
              </div>
              <div class="guide-menu__duration">{{ guide.duration }}</div>
            </div>
          </div>
        </div>
        
        <div class="guide-menu__section">
          <h4>功能介绍</h4>
          <div class="guide-menu__items">
            <div
              v-for="guide in featureGuides"
              :key="guide.id"
              class="guide-menu__item"
              @click="startSpecificGuide(guide.id)"
            >
              <el-icon class="guide-menu__icon">
                <component :is="guide.icon" />
              </el-icon>
              <div class="guide-menu__info">
                <div class="guide-menu__title">{{ guide.title }}</div>
                <div class="guide-menu__desc">{{ guide.description }}</div>
              </div>
              <div class="guide-menu__duration">{{ guide.duration }}</div>
            </div>
          </div>
        </div>
        
        <div class="guide-menu__section">
          <h4>高级功能</h4>
          <div class="guide-menu__items">
            <div
              v-for="guide in advancedGuides"
              :key="guide.id"
              class="guide-menu__item"
              @click="startSpecificGuide(guide.id)"
            >
              <el-icon class="guide-menu__icon">
                <component :is="guide.icon" />
              </el-icon>
              <div class="guide-menu__info">
                <div class="guide-menu__title">{{ guide.title }}</div>
                <div class="guide-menu__desc">{{ guide.description }}</div>
              </div>
              <div class="guide-menu__duration">{{ guide.duration }}</div>
            </div>
          </div>
        </div>
        
        <div class="guide-menu__footer">
          <el-button @click="resetGuideProgress" size="small" text>
            重置引导进度
          </el-button>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { InfoFilled, QuestionFilled, TrendCharts, DataAnalysis, Setting, Monitor } from '@element-plus/icons-vue'
import { useUserGuide } from '@/composables/guide/useUserGuide'

export interface GuideStep {
  id: string
  title: string
  description: string
  target?: string // CSS选择器
  position?: 'top' | 'bottom' | 'left' | 'right'
  offset?: { x: number; y: number }
  tips?: string[]
  media?: {
    type: 'image' | 'video'
    url: string
  }
  interactive?: {
    component: string
    props?: Record<string, any>
  }
  action?: () => void | Promise<void>
  condition?: () => boolean
}

export interface GuideConfig {
  id: string
  title: string
  description: string
  icon: string
  duration: string
  steps: GuideStep[]
  category: 'quickstart' | 'feature' | 'advanced'
}

interface Props {
  guides?: GuideConfig[]
  autoStart?: boolean
  showStartButton?: boolean
  storageKey?: string
}

const props = withDefaults(defineProps<Props>(), {
  guides: () => [],
  autoStart: false,
  showStartButton: true,
  storageKey: 'user-guide-progress'
})

const emit = defineEmits<{
  start: [guideId: string]
  complete: [guideId: string]
  skip: [guideId: string]
  stepChange: [step: GuideStep, index: number]
}>()

const {
  isActive,
  currentGuide,
  currentStepIndex,
  startGuide: startGuideComposable,
  nextStep: nextStepComposable,
  previousStep: previousStepComposable,
  skipGuide: skipGuideComposable,
  completeGuide,
  resetProgress
} = useUserGuide()

const showGuideMenu = ref(false)
const interactiveCompleted = ref(false)
const spotlightElement = ref<HTMLElement | null>(null)

// 默认引导配置
const defaultGuides: GuideConfig[] = [
  {
    id: 'dashboard-intro',
    title: '仪表盘介绍',
    description: '了解仪表盘的主要功能和布局',
    icon: 'Monitor',
    duration: '3分钟',
    category: 'quickstart',
    steps: [
      {
        id: 'welcome',
        title: '欢迎使用量化交易平台',
        description: '这是一个专业的量化投资平台，让我们开始快速了解主要功能。',
        tips: ['平台提供实时行情数据', '支持多种交易策略', '具备完善的风险管理功能']
      },
      {
        id: 'nav-overview',
        title: '导航栏概览',
        description: '左侧导航栏包含了平台的所有主要功能模块。',
        target: '.layout-sidebar',
        position: 'right'
      },
      {
        id: 'dashboard-cards',
        title: '仪表盘卡片',
        description: '这些卡片显示了您的账户概况和关键指标。',
        target: '.dashboard-cards',
        position: 'bottom'
      }
    ]
  },
  {
    id: 'trading-guide',
    title: '交易功能指南',
    description: '学习如何使用交易终端进行买卖操作',
    icon: 'TrendCharts',
    duration: '5分钟',
    category: 'feature',
    steps: [
      {
        id: 'trading-panel',
        title: '交易面板',
        description: '这里是您进行股票买卖的主要区域。',
        target: '.trading-panel',
        position: 'left'
      },
      {
        id: 'order-book',
        title: '订单薄',
        description: '实时显示买卖盘口信息，帮助您做出交易决策。',
        target: '.order-book',
        position: 'top'
      }
    ]
  },
  {
    id: 'strategy-guide',
    title: '策略管理',
    description: '创建和管理您的量化交易策略',
    icon: 'DataAnalysis',
    duration: '8分钟',
    category: 'advanced',
    steps: [
      {
        id: 'strategy-list',
        title: '策略列表',
        description: '查看和管理您的所有交易策略。',
        target: '.strategy-list',
        position: 'right'
      }
    ]
  }
]

const allGuides = computed(() => [...defaultGuides, ...props.guides])

const quickStartGuides = computed(() => 
  allGuides.value.filter(guide => guide.category === 'quickstart')
)

const featureGuides = computed(() => 
  allGuides.value.filter(guide => guide.category === 'feature')
)

const advancedGuides = computed(() => 
  allGuides.value.filter(guide => guide.category === 'advanced')
)

const steps = computed(() => currentGuide.value?.steps || [])
const currentStep = computed(() => steps.value[currentStepIndex.value])

// 计算聚光灯样式
const spotlightStyle = computed(() => {
  if (!currentStep.value?.target) {
    return {
      display: 'none'
    }
  }

  const element = document.querySelector(currentStep.value.target) as HTMLElement
  if (!element) {
    return {
      display: 'none'
    }
  }

  const rect = element.getBoundingClientRect()
  const padding = 8

  return {
    left: `${rect.left - padding}px`,
    top: `${rect.top - padding}px`,
    width: `${rect.width + padding * 2}px`,
    height: `${rect.height + padding * 2}px`
  }
})

// 计算引导卡片样式
const cardStyle = computed(() => {
  if (!currentStep.value?.target) {
    return {
      left: '50%',
      top: '50%',
      transform: 'translate(-50%, -50%)'
    }
  }

  const element = document.querySelector(currentStep.value.target) as HTMLElement
  if (!element) {
    return {
      left: '50%',
      top: '50%',
      transform: 'translate(-50%, -50%)'
    }
  }

  const rect = element.getBoundingClientRect()
  const cardWidth = 320
  const cardHeight = 200
  const offset = currentStep.value.offset || { x: 0, y: 0 }
  
  let left = rect.left
  let top = rect.top
  let transform = ''

  switch (currentStep.value.position) {
    case 'top':
      left = rect.left + rect.width / 2
      top = rect.top - 20
      transform = 'translate(-50%, -100%)'
      break
    case 'bottom':
      left = rect.left + rect.width / 2
      top = rect.bottom + 20
      transform = 'translateX(-50%)'
      break
    case 'left':
      left = rect.left - 20
      top = rect.top + rect.height / 2
      transform = 'translate(-100%, -50%)'
      break
    case 'right':
      left = rect.right + 20
      top = rect.top + rect.height / 2
      transform = 'translateY(-50%)'
      break
    default:
      left = rect.left + rect.width / 2
      top = rect.bottom + 20
      transform = 'translateX(-50%)'
  }

  // 应用偏移
  left += offset.x
  top += offset.y

  // 边界检查
  const viewport = {
    width: window.innerWidth,
    height: window.innerHeight
  }

  if (left < 10) left = 10
  if (left + cardWidth > viewport.width - 10) left = viewport.width - cardWidth - 10
  if (top < 10) top = 10
  if (top + cardHeight > viewport.height - 10) top = viewport.height - cardHeight - 10

  return {
    left: `${left}px`,
    top: `${top}px`,
    transform
  }
})

const startGuide = (guideId?: string) => {
  const guide = guideId ? allGuides.value.find(g => g.id === guideId) : allGuides.value[0]
  if (!guide) return

  startGuideComposable(guide)
  emit('start', guide.id)
}

const startSpecificGuide = (guideId: string) => {
  showGuideMenu.value = false
  startGuide(guideId)
}

const nextStep = async () => {
  if (!currentStep.value) return

  // 执行步骤动作
  if (currentStep.value.action) {
    try {
      await currentStep.value.action()
    } catch (error) {
      console.error('Guide step action failed:', error)
    }
  }

  // 检查条件
  if (currentStep.value.condition && !currentStep.value.condition()) {
    ElMessage.warning('请先完成当前步骤的要求')
    return
  }

  if (currentStepIndex.value < steps.value.length - 1) {
    nextStepComposable()
    interactiveCompleted.value = false
    emit('stepChange', currentStep.value, currentStepIndex.value)
  } else {
    completeGuide()
    emit('complete', currentGuide.value!.id)
  }
}

const previousStep = () => {
  if (currentStepIndex.value > 0) {
    previousStepComposable()
    interactiveCompleted.value = false
    emit('stepChange', currentStep.value, currentStepIndex.value)
  }
}

const skipGuide = () => {
  if (currentGuide.value) {
    emit('skip', currentGuide.value.id)
  }
  skipGuideComposable()
}

const handleTryIt = () => {
  // 聚焦到目标元素
  if (currentStep.value?.target) {
    const element = document.querySelector(currentStep.value.target) as HTMLElement
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      element.focus()
      
      // 添加高亮效果
      element.classList.add('guide-highlight')
      setTimeout(() => {
        element.classList.remove('guide-highlight')
      }, 2000)
    }
  }
}

const handleInteractiveComplete = () => {
  interactiveCompleted.value = true
  ElMessage.success('很好！您已经掌握了这个功能')
}

const resetGuideProgress = () => {
  resetProgress()
  showGuideMenu.value = false
  ElMessage.success('引导进度已重置')
}

// 键盘事件处理
const handleKeydown = (event: KeyboardEvent) => {
  if (!isActive.value) return

  switch (event.key) {
    case 'Escape':
      skipGuide()
      break
    case 'ArrowRight':
    case ' ':
      event.preventDefault()
      nextStep()
      break
    case 'ArrowLeft':
      event.preventDefault()
      previousStep()
      break
  }
}

onMounted(() => {
  // 检查是否需要自动启动
  if (props.autoStart) {
    const hasSeenGuide = localStorage.getItem(`${props.storageKey}-completed`)
    if (!hasSeenGuide) {
      nextTick(() => {
        startGuide()
      })
    }
  }

  // 添加键盘事件监听
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})

// 暴露方法给父组件
defineExpose({
  startGuide,
  showGuideMenu: () => { showGuideMenu.value = true },
  isActive: () => isActive.value
})
</script>

<style scoped lang="scss">
.user-guide {
  position: relative;
}

.guide-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 9999;
  opacity: 0;
  visibility: hidden;
  transition: all 0.3s ease;

  &--active {
    opacity: 1;
    visibility: visible;
  }
}

.guide-spotlight {
  position: absolute;
  background-color: rgba(255, 255, 255, 0.1);
  border: 2px solid var(--el-color-primary);
  border-radius: 8px;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.5);
  transition: all 0.3s ease;
  z-index: 10000;
}

.guide-card {
  position: absolute;
  width: 320px;
  max-width: 90vw;
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  z-index: 10001;
  animation: guideCardIn 0.3s ease;

  &__header {
    padding: 20px 20px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  &__title {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  &__progress {
    background: var(--el-color-primary-light-9);
    color: var(--el-color-primary);
    padding: 4px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
  }

  &__content {
    padding: 16px 20px;
  }

  &__description {
    color: var(--el-text-color-regular);
    line-height: 1.6;
    margin-bottom: 16px;
  }

  &__media {
    margin-bottom: 16px;
    border-radius: 8px;
    overflow: hidden;
  }

  &__interactive {
    margin-bottom: 16px;
    padding: 16px;
    background: var(--el-color-primary-light-9);
    border-radius: 8px;
  }

  &__tips {
    margin: 0;
    padding: 0;
    list-style: none;
  }

  &__actions {
    padding: 0 20px 20px;
    display: flex;
    gap: 8px;
    justify-content: flex-end;
  }
}

.guide-tip {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  color: var(--el-text-color-regular);
  font-size: 14px;

  &__icon {
    color: var(--el-color-primary);
    margin-top: 2px;
    flex-shrink: 0;
  }

  &:last-child {
    margin-bottom: 0;
  }
}

.guide-media {
  &__image,
  &__video {
    width: 100%;
    height: auto;
    display: block;
  }
}

.guide-start-button {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);

  &:hover {
    transform: scale(1.05);
  }
}

.guide-menu {
  &__section {
    margin-bottom: 32px;

    h4 {
      margin: 0 0 16px;
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }

  &__items {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  &__item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;

    &:hover {
      background: var(--el-color-primary-light-9);
    }
  }

  &__icon {
    width: 32px;
    height: 32px;
    background: var(--el-color-primary-light-8);
    color: var(--el-color-primary);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  &__info {
    flex: 1;
  }

  &__title {
    font-weight: 500;
    color: var(--el-text-color-primary);
    margin-bottom: 4px;
  }

  &__desc {
    font-size: 12px;
    color: var(--el-text-color-regular);
  }

  &__duration {
    font-size: 12px;
    color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
    padding: 2px 8px;
    border-radius: 12px;
  }

  &__footer {
    padding-top: 24px;
    border-top: 1px solid var(--el-border-color-light);
    text-align: center;
  }
}

@keyframes guideCardIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

// 全局高亮样式
:global(.guide-highlight) {
  position: relative;
  z-index: 9998;

  &::after {
    content: '';
    position: absolute;
    top: -4px;
    left: -4px;
    right: -4px;
    bottom: -4px;
    border: 2px solid var(--el-color-primary);
    border-radius: 8px;
    animation: guideHighlight 2s ease;
  }
}

@keyframes guideHighlight {
  0%, 100% {
    opacity: 0;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.02);
  }
}
</style> 