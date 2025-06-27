/**
 * 键盘快捷键 Composable
 * 提供全局键盘快捷键管理功能
 */

import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'

export interface KeyboardShortcut {
  id: string
  key: string // 如: 'ctrl+s', 'alt+1', 'f1'
  description: string
  category: string
  handler: (event: KeyboardEvent) => void | Promise<void>
  enabled?: boolean
  global?: boolean // 是否全局生效（即使在输入框中）
  preventDefault?: boolean
  stopPropagation?: boolean
}

export interface ShortcutCategory {
  id: string
  name: string
  shortcuts: KeyboardShortcut[]
}

const STORAGE_KEY = 'quant-platform-keyboard-shortcuts'

// 全局快捷键存储
const shortcuts = ref<Map<string, KeyboardShortcut>>(new Map())
const categories = ref<Map<string, ShortcutCategory>>(new Map())
const isEnabled = ref(true)
const showHelpModal = ref(false)

// 修饰键映射
const modifierKeys = {
  ctrl: 'ctrlKey',
  cmd: 'metaKey',
  alt: 'altKey',
  shift: 'shiftKey'
} as const

export function useKeyboardShortcuts() {
  
  // 解析快捷键字符串
  const parseShortcut = (shortcut: string) => {
    const parts = shortcut.toLowerCase().split('+')
    const modifiers = {
      ctrl: false,
      cmd: false,
      alt: false,
      shift: false
    }
    
    let key = ''
    
    for (const part of parts) {
      if (part in modifierKeys) {
        modifiers[part as keyof typeof modifierKeys] = true
      } else {
        key = part
      }
    }
    
    return { modifiers, key }
  }

  // 检查快捷键是否匹配
  const isShortcutMatch = (event: KeyboardEvent, shortcut: string): boolean => {
    const { modifiers, key } = parseShortcut(shortcut)
    
    // 检查修饰键
    if (modifiers.ctrl && !event.ctrlKey) return false
    if (modifiers.cmd && !event.metaKey) return false
    if (modifiers.alt && !event.altKey) return false
    if (modifiers.shift && !event.shiftKey) return false
    
    // 检查主键
    const eventKey = event.key.toLowerCase()
    const eventCode = event.code.toLowerCase()
    
    return eventKey === key || eventCode === key || eventCode === `key${key}`
  }

  // 注册快捷键
  const registerShortcut = (shortcut: KeyboardShortcut) => {
    shortcuts.value.set(shortcut.id, shortcut)
    
    // 添加到分类
    if (!categories.value.has(shortcut.category)) {
      categories.value.set(shortcut.category, {
        id: shortcut.category,
        name: shortcut.category,
        shortcuts: []
      })
    }
    
    const category = categories.value.get(shortcut.category)!
    const existingIndex = category.shortcuts.findIndex(s => s.id === shortcut.id)
    
    if (existingIndex >= 0) {
      category.shortcuts[existingIndex] = shortcut
    } else {
      category.shortcuts.push(shortcut)
    }
    
    saveShortcuts()
  }

  // 批量注册快捷键
  const registerShortcuts = (shortcutList: KeyboardShortcut[]) => {
    shortcutList.forEach(shortcut => registerShortcut(shortcut))
  }

  // 注销快捷键
  const unregisterShortcut = (id: string) => {
    const shortcut = shortcuts.value.get(id)
    if (!shortcut) return false
    
    shortcuts.value.delete(id)
    
    // 从分类中移除
    const category = categories.value.get(shortcut.category)
    if (category) {
      const index = category.shortcuts.findIndex(s => s.id === id)
      if (index >= 0) {
        category.shortcuts.splice(index, 1)
      }
      
      // 如果分类为空，删除分类
      if (category.shortcuts.length === 0) {
        categories.value.delete(shortcut.category)
      }
    }
    
    saveShortcuts()
    return true
  }

  // 启用/禁用快捷键
  const toggleShortcut = (id: string, enabled?: boolean) => {
    const shortcut = shortcuts.value.get(id)
    if (!shortcut) return false
    
    shortcut.enabled = enabled !== undefined ? enabled : !shortcut.enabled
    saveShortcuts()
    return true
  }

  // 更新快捷键
  const updateShortcut = (id: string, updates: Partial<KeyboardShortcut>) => {
    const shortcut = shortcuts.value.get(id)
    if (!shortcut) return false
    
    Object.assign(shortcut, updates)
    saveShortcuts()
    return true
  }

  // 获取快捷键
  const getShortcut = (id: string): KeyboardShortcut | undefined => {
    return shortcuts.value.get(id)
  }

  // 获取所有快捷键
  const getAllShortcuts = (): KeyboardShortcut[] => {
    return Array.from(shortcuts.value.values())
  }

  // 按分类获取快捷键
  const getShortcutsByCategory = (categoryId: string): KeyboardShortcut[] => {
    const category = categories.value.get(categoryId)
    return category ? category.shortcuts : []
  }

  // 获取所有分类
  const getAllCategories = (): ShortcutCategory[] => {
    return Array.from(categories.value.values())
  }

  // 检查快捷键是否冲突
  const hasConflict = (key: string, excludeId?: string): boolean => {
    for (const [id, shortcut] of shortcuts.value) {
      if (id !== excludeId && shortcut.key === key && shortcut.enabled !== false) {
        return true
      }
    }
    return false
  }

  // 查找快捷键
  const findShortcut = (key: string): KeyboardShortcut | undefined => {
    for (const [, shortcut] of shortcuts.value) {
      if (shortcut.key === key && shortcut.enabled !== false) {
        return shortcut
      }
    }
    return undefined
  }

  // 处理键盘事件
  const handleKeyboardEvent = async (event: KeyboardEvent) => {
    if (!isEnabled.value) return
    
    // 检查是否在输入元素中
    const target = event.target as HTMLElement
    const isInputElement = target.tagName === 'INPUT' || 
                          target.tagName === 'TEXTAREA' || 
                          target.contentEditable === 'true'
    
    for (const [, shortcut] of shortcuts.value) {
      if (shortcut.enabled === false) continue
      
      // 如果不是全局快捷键且在输入元素中，跳过
      if (!shortcut.global && isInputElement) continue
      
      if (isShortcutMatch(event, shortcut.key)) {
        if (shortcut.preventDefault !== false) {
          event.preventDefault()
        }
        
        if (shortcut.stopPropagation !== false) {
          event.stopPropagation()
        }
        
        try {
          await shortcut.handler(event)
        } catch (error) {
          console.error('Shortcut handler error:', error)
          ElMessage.error('快捷键执行失败')
        }
        
        break // 只执行第一个匹配的快捷键
      }
    }
  }

  // 保存快捷键配置
  const saveShortcuts = () => {
    try {
      const data = {
        shortcuts: Array.from(shortcuts.value.entries()),
        categories: Array.from(categories.value.entries()),
        isEnabled: isEnabled.value
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data))
    } catch (error) {
      console.warn('Failed to save shortcuts:', error)
    }
  }

  // 加载快捷键配置
  const loadShortcuts = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        const data = JSON.parse(saved)
        
        if (data.shortcuts) {
          shortcuts.value = new Map(data.shortcuts)
        }
        
        if (data.categories) {
          categories.value = new Map(data.categories)
        }
        
        if (data.isEnabled !== undefined) {
          isEnabled.value = data.isEnabled
        }
      }
    } catch (error) {
      console.warn('Failed to load shortcuts:', error)
    }
  }

  // 重置为默认配置
  const resetToDefaults = () => {
    shortcuts.value.clear()
    categories.value.clear()
    registerDefaultShortcuts()
    saveShortcuts()
  }

  // 注册默认快捷键
  const registerDefaultShortcuts = () => {
    const defaultShortcuts: KeyboardShortcut[] = [
      // 全局快捷键
      {
        id: 'toggle-help',
        key: 'f1',
        description: '显示/隐藏帮助',
        category: '全局',
        handler: () => {
          showHelpModal.value = !showHelpModal.value
        },
        global: true
      },
      {
        id: 'toggle-shortcuts',
        key: 'ctrl+/',
        description: '显示快捷键列表',
        category: '全局',
        handler: () => {
          showHelpModal.value = !showHelpModal.value
        },
        global: true
      },
      {
        id: 'refresh-page',
        key: 'f5',
        description: '刷新页面',
        category: '全局',
        handler: () => {
          location.reload()
        },
        global: true
      },
      
      // 导航快捷键
      {
        id: 'goto-dashboard',
        key: 'alt+1',
        description: '跳转到仪表盘',
        category: '导航',
        handler: () => {
          // 这里需要路由跳转逻辑
          console.log('Navigate to dashboard')
        },
        global: true
      },
      {
        id: 'goto-market',
        key: 'alt+2',
        description: '跳转到行情',
        category: '导航',
        handler: () => {
          console.log('Navigate to market')
        },
        global: true
      },
      {
        id: 'goto-trading',
        key: 'alt+3',
        description: '跳转到交易',
        category: '导航',
        handler: () => {
          console.log('Navigate to trading')
        },
        global: true
      },
      {
        id: 'goto-portfolio',
        key: 'alt+4',
        description: '跳转到投资组合',
        category: '导航',
        handler: () => {
          console.log('Navigate to portfolio')
        },
        global: true
      },
      {
        id: 'goto-strategy',
        key: 'alt+5',
        description: '跳转到策略',
        category: '导航',  
        handler: () => {
          console.log('Navigate to strategy')
        },
        global: true
      },
      
      // 交易快捷键
      {
        id: 'quick-buy',
        key: 'ctrl+b',
        description: '快速买入',
        category: '交易',
        handler: () => {
          console.log('Quick buy')
        }
      },
      {
        id: 'quick-sell',
        key: 'ctrl+s',
        description: '快速卖出',
        category: '交易',
        handler: () => {
          console.log('Quick sell')
        }
      },
      {
        id: 'cancel-all-orders',
        key: 'ctrl+alt+c',
        description: '撤销所有订单',
        category: '交易',
        handler: () => {
          console.log('Cancel all orders')
        }
      },
      
      // 数据快捷键
      {
        id: 'export-data',
        key: 'ctrl+e',
        description: '导出数据',
        category: '数据',
        handler: () => {
          console.log('Export data')
        }
      },
      {
        id: 'refresh-data',
        key: 'ctrl+r',
        description: '刷新数据',
        category: '数据',
        handler: () => {
          console.log('Refresh data')
        }
      },
      
      // 界面快捷键
      {
        id: 'toggle-sidebar',
        key: 'ctrl+shift+s',
        description: '切换侧边栏',
        category: '界面',
        handler: () => {
          console.log('Toggle sidebar')
        },
        global: true
      },
      {
        id: 'toggle-fullscreen',
        key: 'f11',
        description: '切换全屏',
        category: '界面',
        handler: () => {
          if (document.fullscreenElement) {
            document.exitFullscreen()
          } else {
            document.documentElement.requestFullscreen()
          }
        },
        global: true
      },
      {
        id: 'zoom-in',
        key: 'ctrl+plus',
        description: '放大',
        category: '界面',
        handler: () => {
          console.log('Zoom in')
        }
      },
      {
        id: 'zoom-out',
        key: 'ctrl+minus',
        description: '缩小',
        category: '界面',
        handler: () => {
          console.log('Zoom out')
        }
      },
      {
        id: 'reset-zoom',
        key: 'ctrl+0',
        description: '重置缩放',
        category: '界面',
        handler: () => {
          console.log('Reset zoom')
        }
      }
    ]
    
    registerShortcuts(defaultShortcuts)
  }

  // 格式化快捷键显示
  const formatShortcut = (key: string): string => {
    return key
      .split('+')
      .map(part => {
        switch (part.toLowerCase()) {
          case 'ctrl': return '⌃'
          case 'cmd': return '⌘'
          case 'alt': return '⌥'
          case 'shift': return '⇧'
          case 'enter': return '↵'
          case 'space': return '␣'
          case 'tab': return '⇥'
          case 'escape': return '⎋'
          case 'backspace': return '⌫'
          case 'delete': return '⌦'
          case 'arrowup': return '↑'
          case 'arrowdown': return '↓'
          case 'arrowleft': return '←'
          case 'arrowright': return '→'
          default: return part.toUpperCase()
        }
      })
      .join('')
  }

  // 获取快捷键帮助信息
  const getHelpInfo = () => {
    const categorizedShortcuts: Record<string, KeyboardShortcut[]> = {}
    
    for (const [, shortcut] of shortcuts.value) {
      if (shortcut.enabled === false) continue
      
      if (!categorizedShortcuts[shortcut.category]) {
        categorizedShortcuts[shortcut.category] = []
      }
      
      categorizedShortcuts[shortcut.category].push(shortcut)
    }
    
    return categorizedShortcuts
  }

  // 搜索快捷键
  const searchShortcuts = (query: string): KeyboardShortcut[] => {
    const lowerQuery = query.toLowerCase()
    const results: KeyboardShortcut[] = []
    
    for (const [, shortcut] of shortcuts.value) {
      if (shortcut.enabled === false) continue
      
      if (shortcut.description.toLowerCase().includes(lowerQuery) ||
          shortcut.key.toLowerCase().includes(lowerQuery) ||
          shortcut.category.toLowerCase().includes(lowerQuery)) {
        results.push(shortcut)
      }
    }
    
    return results
  }

  // 计算属性
  const enabledShortcuts = computed(() => {
    return Array.from(shortcuts.value.values()).filter(s => s.enabled !== false)
  })

  const shortcutCount = computed(() => shortcuts.value.size)

  const categoryCount = computed(() => categories.value.size)

  // 生命周期
  onMounted(() => {
    loadShortcuts()
    
    // 如果没有快捷键，注册默认快捷键
    if (shortcuts.value.size === 0) {
      registerDefaultShortcuts()
    }
    
    // 添加键盘事件监听
    document.addEventListener('keydown', handleKeyboardEvent, true)
  })

  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyboardEvent, true)
  })

  return {
    // 状态
    shortcuts: shortcuts.value,
    categories: categories.value,
    isEnabled,
    showHelpModal,
    enabledShortcuts,
    shortcutCount,
    categoryCount,

    // 方法
    registerShortcut,
    registerShortcuts,
    unregisterShortcut,
    toggleShortcut,
    updateShortcut,
    getShortcut,
    getAllShortcuts,
    getShortcutsByCategory,
    getAllCategories,
    hasConflict,
    findShortcut,
    saveShortcuts,
    loadShortcuts,
    resetToDefaults,
    registerDefaultShortcuts,
    formatShortcut,
    getHelpInfo,
    searchShortcuts,

    // 工具方法
    parseShortcut,
    isShortcutMatch
  }
} 