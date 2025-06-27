/**
 * 用户引导 Composable
 * 管理用户引导的状态和逻辑
 */

import { ref, computed, reactive } from 'vue'

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
  delay?: number // 延迟显示时间（毫秒）
}

export interface GuideConfig {
  id: string
  title: string
  description: string
  icon: string
  duration: string
  steps: GuideStep[]
  category: 'quickstart' | 'feature' | 'advanced'
  autoStart?: boolean
  skipable?: boolean
  repeatable?: boolean
}

export interface GuideProgress {
  completedGuides: string[]
  skippedGuides: string[]
  currentGuide?: string
  currentStep?: number
  lastActiveTime: number
}

const STORAGE_KEY = 'quant-platform-guide-progress'

// 全局状态
const state = reactive({
  isActive: false,
  currentGuide: null as GuideConfig | null,
  currentStepIndex: 0,
  guides: new Map<string, GuideConfig>(),
  progress: {
    completedGuides: [],
    skippedGuides: [],
    lastActiveTime: Date.now()
  } as GuideProgress
})

export function useUserGuide() {
  // 加载进度
  const loadProgress = (): GuideProgress => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        return { ...state.progress, ...JSON.parse(saved) }
      }
    } catch (error) {
      console.warn('Failed to load guide progress:', error)
    }
    return state.progress
  }

  // 保存进度
  const saveProgress = () => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state.progress))
    } catch (error) {
      console.warn('Failed to save guide progress:', error)
    }
  }

  // 注册引导
  const registerGuide = (guide: GuideConfig) => {
    state.guides.set(guide.id, guide)
  }

  // 批量注册引导
  const registerGuides = (guides: GuideConfig[]) => {
    guides.forEach(guide => registerGuide(guide))
  }

  // 获取引导
  const getGuide = (id: string): GuideConfig | undefined => {
    return state.guides.get(id)
  }

  // 获取所有引导
  const getAllGuides = (): GuideConfig[] => {
    return Array.from(state.guides.values())
  }

  // 按类别获取引导
  const getGuidesByCategory = (category: GuideConfig['category']): GuideConfig[] => {
    return getAllGuides().filter(guide => guide.category === category)
  }

  // 开始引导
  const startGuide = (guide: GuideConfig | string) => {
    const guideConfig = typeof guide === 'string' ? getGuide(guide) : guide
    if (!guideConfig) {
      console.warn('Guide not found:', guide)
      return false
    }

    // 检查是否已完成且不可重复
    if (!guideConfig.repeatable && state.progress.completedGuides.includes(guideConfig.id)) {
      console.info('Guide already completed:', guideConfig.id)
      return false
    }

    state.currentGuide = guideConfig
    state.currentStepIndex = 0
    state.isActive = true
    state.progress.currentGuide = guideConfig.id
    state.progress.currentStep = 0
    state.progress.lastActiveTime = Date.now()

    saveProgress()
    return true
  }

  // 下一步
  const nextStep = () => {
    if (!state.currentGuide || !state.isActive) return false

    const nextIndex = state.currentStepIndex + 1
    if (nextIndex < state.currentGuide.steps.length) {
      state.currentStepIndex = nextIndex
      state.progress.currentStep = nextIndex
      state.progress.lastActiveTime = Date.now()
      saveProgress()
      return true
    }

    return false
  }

  // 上一步
  const previousStep = () => {
    if (!state.currentGuide || !state.isActive || state.currentStepIndex <= 0) return false

    state.currentStepIndex--
    state.progress.currentStep = state.currentStepIndex
    state.progress.lastActiveTime = Date.now()
    saveProgress()
    return true
  }

  // 跳转到指定步骤
  const goToStep = (stepIndex: number) => {
    if (!state.currentGuide || !state.isActive) return false

    if (stepIndex >= 0 && stepIndex < state.currentGuide.steps.length) {
      state.currentStepIndex = stepIndex
      state.progress.currentStep = stepIndex
      state.progress.lastActiveTime = Date.now()
      saveProgress()
      return true
    }

    return false
  }

  // 完成引导
  const completeGuide = () => {
    if (!state.currentGuide) return false

    const guideId = state.currentGuide.id
    
    // 添加到已完成列表
    if (!state.progress.completedGuides.includes(guideId)) {
      state.progress.completedGuides.push(guideId)
    }

    // 从跳过列表中移除（如果存在）
    const skippedIndex = state.progress.skippedGuides.indexOf(guideId)
    if (skippedIndex > -1) {
      state.progress.skippedGuides.splice(skippedIndex, 1)
    }

    // 重置状态
    state.isActive = false
    state.currentGuide = null
    state.currentStepIndex = 0
    state.progress.currentGuide = undefined
    state.progress.currentStep = undefined
    state.progress.lastActiveTime = Date.now()

    saveProgress()
    return true
  }

  // 跳过引导
  const skipGuide = () => {
    if (!state.currentGuide) return false

    const guideId = state.currentGuide.id

    // 添加到跳过列表
    if (!state.progress.skippedGuides.includes(guideId)) {
      state.progress.skippedGuides.push(guideId)
    }

    // 重置状态
    state.isActive = false
    state.currentGuide = null
    state.currentStepIndex = 0
    state.progress.currentGuide = undefined
    state.progress.currentStep = undefined
    state.progress.lastActiveTime = Date.now()

    saveProgress()
    return true
  }

  // 暂停引导
  const pauseGuide = () => {
    if (!state.isActive) return false

    state.isActive = false
    state.progress.lastActiveTime = Date.now()
    saveProgress()
    return true
  }

  // 恢复引导
  const resumeGuide = () => {
    if (state.isActive || !state.currentGuide) return false

    state.isActive = true
    state.progress.lastActiveTime = Date.now()
    saveProgress()
    return true
  }

  // 重置进度
  const resetProgress = () => {
    state.progress = {
      completedGuides: [],
      skippedGuides: [],
      lastActiveTime: Date.now()
    }
    
    state.isActive = false
    state.currentGuide = null
    state.currentStepIndex = 0

    saveProgress()
  }

  // 重置特定引导的进度
  const resetGuideProgress = (guideId: string) => {
    // 从完成列表中移除
    const completedIndex = state.progress.completedGuides.indexOf(guideId)
    if (completedIndex > -1) {
      state.progress.completedGuides.splice(completedIndex, 1)
    }

    // 从跳过列表中移除
    const skippedIndex = state.progress.skippedGuides.indexOf(guideId)
    if (skippedIndex > -1) {
      state.progress.skippedGuides.splice(skippedIndex, 1)
    }

    // 如果当前正在进行这个引导，则停止
    if (state.currentGuide?.id === guideId) {
      state.isActive = false
      state.currentGuide = null
      state.currentStepIndex = 0
      state.progress.currentGuide = undefined
      state.progress.currentStep = undefined
    }

    state.progress.lastActiveTime = Date.now()
    saveProgress()
  }

  // 检查引导是否已完成
  const isGuideCompleted = (guideId: string): boolean => {
    return state.progress.completedGuides.includes(guideId)
  }

  // 检查引导是否已跳过
  const isGuideSkipped = (guideId: string): boolean => {
    return state.progress.skippedGuides.includes(guideId)
  }

  // 检查是否应该显示引导
  const shouldShowGuide = (guideId: string): boolean => {
    const guide = getGuide(guideId)
    if (!guide) return false

    // 如果不可重复且已完成，则不显示
    if (!guide.repeatable && isGuideCompleted(guideId)) {
      return false
    }

    return true
  }

  // 获取推荐的下一个引导
  const getNextRecommendedGuide = (): GuideConfig | null => {
    const allGuides = getAllGuides()
    
    // 按优先级排序：快速入门 > 功能介绍 > 高级功能
    const priorityOrder = ['quickstart', 'feature', 'advanced']
    
    for (const category of priorityOrder) {
      const categoryGuides = allGuides.filter(guide => 
        guide.category === category && shouldShowGuide(guide.id)
      )
      
      if (categoryGuides.length > 0) {
        return categoryGuides[0]
      }
    }

    return null
  }

  // 获取统计信息
  const getStatistics = () => {
    const allGuides = getAllGuides()
    const totalGuides = allGuides.length
    const completedCount = state.progress.completedGuides.length
    const skippedCount = state.progress.skippedGuides.length
    const remainingCount = totalGuides - completedCount - skippedCount

    return {
      total: totalGuides,
      completed: completedCount,
      skipped: skippedCount,
      remaining: remainingCount,
      completionRate: totalGuides > 0 ? (completedCount / totalGuides) * 100 : 0
    }
  }

  // 自动启动引导
  const autoStartGuide = () => {
    const nextGuide = getNextRecommendedGuide()
    if (nextGuide && nextGuide.autoStart) {
      return startGuide(nextGuide)
    }
    return false
  }

  // 计算属性
  const isActive = computed(() => state.isActive)
  const currentGuide = computed(() => state.currentGuide)
  const currentStepIndex = computed(() => state.currentStepIndex)
  const currentStep = computed(() => {
    if (!state.currentGuide || state.currentStepIndex < 0) return null
    return state.currentGuide.steps[state.currentStepIndex] || null
  })
  const hasNextStep = computed(() => {
    if (!state.currentGuide) return false
    return state.currentStepIndex < state.currentGuide.steps.length - 1
  })
  const hasPreviousStep = computed(() => state.currentStepIndex > 0)
  const progress = computed(() => {
    if (!state.currentGuide) return 0
    return ((state.currentStepIndex + 1) / state.currentGuide.steps.length) * 100
  })

  // 初始化
  const init = () => {
    state.progress = loadProgress()
    
    // 如果有未完成的引导，恢复状态
    if (state.progress.currentGuide && state.progress.currentStep !== undefined) {
      const guide = getGuide(state.progress.currentGuide)
      if (guide && state.progress.currentStep < guide.steps.length) {
        state.currentGuide = guide
        state.currentStepIndex = state.progress.currentStep
        // 不自动激活，让用户决定是否继续
      }
    }
  }

  // 页面加载时初始化
  init()

  return {
    // 状态
    isActive,
    currentGuide,
    currentStepIndex,
    currentStep,
    hasNextStep,
    hasPreviousStep,
    progress,

    // 方法
    registerGuide,
    registerGuides,
    getGuide,
    getAllGuides,
    getGuidesByCategory,
    startGuide,
    nextStep,
    previousStep,
    goToStep,
    completeGuide,
    skipGuide,
    pauseGuide,
    resumeGuide,
    resetProgress,
    resetGuideProgress,
    isGuideCompleted,
    isGuideSkipped,
    shouldShowGuide,
    getNextRecommendedGuide,
    getStatistics,
    autoStartGuide
  }
} 