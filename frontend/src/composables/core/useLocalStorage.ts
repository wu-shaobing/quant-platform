import { ref, watch, Ref } from 'vue'

/**
 * 本地存储配置选项
 */
interface UseLocalStorageOptions<T> {
  defaultValue?: T
  serializer?: {
    read: (value: string) => T
    write: (value: T) => string
  }
  onError?: (error: Error) => void
  syncAcrossTabs?: boolean
}

/**
 * 默认序列化器
 */
const defaultSerializer = {
  read: <T>(value: string): T => {
    try {
      return JSON.parse(value)
    } catch {
      return value as T
    }
  },
  write: <T>(value: T): string => {
    try {
      return JSON.stringify(value)
    } catch {
      return String(value)
    }
  }
}

/**
 * 类型安全的本地存储组合函数
 * @param key 存储键名
 * @param defaultValue 默认值
 * @param options 配置选项
 * @returns 响应式存储值和相关方法
 */
export function useLocalStorage<T>(
  key: string,
  defaultValue?: T,
  options: UseLocalStorageOptions<T> = {}
): [Ref<T>, (value: T) => void, () => void] {
  const {
    defaultValue: optionsDefaultValue,
    serializer = defaultSerializer,
    onError = (error: Error) => console.error('LocalStorage error:', error),
    syncAcrossTabs = true
  } = options

  const finalDefaultValue = optionsDefaultValue ?? defaultValue

  /**
   * 从本地存储读取值
   */
  const read = (): T => {
    try {
      const item = localStorage.getItem(key)
      if (item === null) {
        return finalDefaultValue as T
      }
      return serializer.read(item)
    } catch (error) {
      onError(error as Error)
      return finalDefaultValue as T
    }
  }

  /**
   * 写入值到本地存储
   */
  const write = (value: T): void => {
    try {
      if (value === null || value === undefined) {
        localStorage.removeItem(key)
      } else {
        localStorage.setItem(key, serializer.write(value))
      }
    } catch (error) {
      onError(error as Error)
    }
  }

  /**
   * 删除存储项
   */
  const remove = (): void => {
    try {
      localStorage.removeItem(key)
      storedValue.value = finalDefaultValue as T
    } catch (error) {
      onError(error as Error)
    }
  }

  // 创建响应式引用
  const storedValue = ref<T>(read())

  /**
   * 更新存储值
   */
  const setValue = (value: T): void => {
    storedValue.value = value
    write(value)
  }

  // 监听值变化，自动同步到本地存储
  watch(
    storedValue,
    (newValue) => {
      write(newValue)
    },
    { deep: true }
  )

  // 跨标签页同步
  if (syncAcrossTabs) {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === key && e.newValue !== serializer.write(storedValue.value)) {
        try {
          if (e.newValue === null) {
            storedValue.value = finalDefaultValue as T
          } else {
            storedValue.value = serializer.read(e.newValue)
          }
        } catch (error) {
          onError(error as Error)
        }
      }
    }

    window.addEventListener('storage', handleStorageChange)

    // 清理监听器
    const cleanup = () => {
      window.removeEventListener('storage', handleStorageChange)
    }

    // 在组件卸载时自动清理
    if (typeof window !== 'undefined' && 'onbeforeunload' in window) {
      window.addEventListener('beforeunload', cleanup)
    }
  }

  return [storedValue, setValue, remove]
}

/**
 * 专门用于存储对象的本地存储函数
 */
export function useLocalStorageObject<T extends Record<string, any>>(
  key: string,
  defaultValue: T,
  options?: Omit<UseLocalStorageOptions<T>, 'serializer'>
) {
  return useLocalStorage(key, defaultValue, {
    ...options,
    serializer: {
      read: (value: string) => {
        try {
          const parsed = JSON.parse(value)
          return { ...defaultValue, ...parsed }
        } catch {
          return defaultValue
        }
      },
      write: (value: T) => JSON.stringify(value)
    }
  })
}

/**
 * 专门用于存储数组的本地存储函数
 */
export function useLocalStorageArray<T>(
  key: string,
  defaultValue: T[] = [],
  options?: Omit<UseLocalStorageOptions<T[]>, 'serializer'>
) {
  return useLocalStorage(key, defaultValue, {
    ...options,
    serializer: {
      read: (value: string) => {
        try {
          const parsed = JSON.parse(value)
          return Array.isArray(parsed) ? parsed : defaultValue
        } catch {
          return defaultValue
        }
      },
      write: (value: T[]) => JSON.stringify(value)
    }
  })
}

/**
 * 专门用于存储字符串的本地存储函数
 */
export function useLocalStorageString(
  key: string,
  defaultValue = '',
  options?: Omit<UseLocalStorageOptions<string>, 'serializer'>
) {
  return useLocalStorage(key, defaultValue, {
    ...options,
    serializer: {
      read: (value: string) => value,
      write: (value: string) => value
    }
  })
}

/**
 * 专门用于存储数字的本地存储函数
 */
export function useLocalStorageNumber(
  key: string,
  defaultValue = 0,
  options?: Omit<UseLocalStorageOptions<number>, 'serializer'>
) {
  return useLocalStorage(key, defaultValue, {
    ...options,
    serializer: {
      read: (value: string) => {
        const num = Number(value)
        return isNaN(num) ? defaultValue : num
      },
      write: (value: number) => String(value)
    }
  })
}

/**
 * 专门用于存储布尔值的本地存储函数
 */
export function useLocalStorageBoolean(
  key: string,
  defaultValue = false,
  options?: Omit<UseLocalStorageOptions<boolean>, 'serializer'>
) {
  return useLocalStorage(key, defaultValue, {
    ...options,
    serializer: {
      read: (value: string) => {
        if (value === 'true') return true
        if (value === 'false') return false
        return defaultValue
      },
      write: (value: boolean) => String(value)
    }
  })
}

/**
 * 专门用于存储日期的本地存储函数
 */
export function useLocalStorageDate(
  key: string,
  defaultValue?: Date,
  options?: Omit<UseLocalStorageOptions<Date | null>, 'serializer'>
) {
  return useLocalStorage<Date | null>(key, defaultValue || null, {
    ...options,
    serializer: {
      read: (value: string) => {
        try {
          const date = new Date(value)
          return isNaN(date.getTime()) ? defaultValue || null : date
        } catch {
          return defaultValue || null
        }
      },
      write: (value: Date | null) => value ? value.toISOString() : ''
    }
  })
}

/**
 * 获取本地存储使用情况
 */
export function getLocalStorageUsage(): {
  used: number
  available: number
  percentage: number
} {
  try {
    let used = 0
    for (const key in localStorage) {
      if (localStorage.hasOwnProperty(key)) {
        used += localStorage[key].length + key.length
      }
    }

    // 估算可用空间 (大多数浏览器限制为5MB)
    const available = 5 * 1024 * 1024 // 5MB in bytes
    const percentage = (used / available) * 100

    return {
      used,
      available,
      percentage: Math.min(percentage, 100)
    }
  } catch (error) {
    return {
      used: 0,
      available: 0,
      percentage: 0
    }
  }
}

/**
 * 清除所有本地存储
 */
export function clearAllLocalStorage(): void {
  try {
    localStorage.clear()
  } catch (error) {
    console.error('清除本地存储失败:', error)
  }
}

/**
 * 获取所有本地存储键名
 */
export function getAllLocalStorageKeys(): string[] {
  try {
    return Object.keys(localStorage)
  } catch (error) {
    console.error('获取本地存储键名失败:', error)
    return []
  }
}

/**
 * 批量设置本地存储
 */
export function setBatchLocalStorage(items: Record<string, any>): void {
  try {
    Object.entries(items).forEach(([key, value]) => {
      localStorage.setItem(key, JSON.stringify(value))
    })
  } catch (error) {
    console.error('批量设置本地存储失败:', error)
  }
}

/**
 * 批量获取本地存储
 */
export function getBatchLocalStorage<T = any>(keys: string[]): Record<string, T> {
  const result: Record<string, T> = {}
  
  try {
    keys.forEach(key => {
      const item = localStorage.getItem(key)
      if (item !== null) {
        try {
          result[key] = JSON.parse(item)
        } catch {
          result[key] = item as T
        }
      }
    })
  } catch (error) {
    console.error('批量获取本地存储失败:', error)
  }
  
  return result
} 