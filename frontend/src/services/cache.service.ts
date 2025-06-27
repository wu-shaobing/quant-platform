/**
 * 缓存服务
 * 提供多级缓存管理功能
 */

export interface CacheItem<T = any> {
  value: T
  expiry: number
  timestamp: number
  accessCount: number
  lastAccess: number
}

export interface CacheOptions {
  ttl?: number // 生存时间（毫秒）
  maxSize?: number // 最大缓存数量
  storage?: 'memory' | 'localStorage' | 'sessionStorage'
  enableStats?: boolean // 是否启用统计
}

export interface CacheStats {
  size: number
  maxSize: number
  hitRate: number
  storage: string
  totalRequests: number
  totalHits: number
  totalMisses: number
  averageAccessTime: number
  topKeys: Array<{ key: string; accessCount: number; lastAccess: number }>
}

export class CacheService {
  private memoryCache = new Map<string, CacheItem>()
  private maxSize: number
  private defaultTTL: number
  private storage: 'memory' | 'localStorage' | 'sessionStorage'
  private enableStats: boolean
  
  // 统计数据
  private stats = {
    totalRequests: 0,
    totalHits: 0,
    totalMisses: 0,
    accessTimes: [] as number[]
  }

  constructor(options: CacheOptions = {}) {
    this.maxSize = options.maxSize || 1000
    this.defaultTTL = options.ttl || 5 * 60 * 1000 // 默认5分钟
    this.storage = options.storage || 'memory'
    this.enableStats = options.enableStats !== false
  }

  /**
   * 设置缓存
   */
  set<T>(key: string, value: T, ttl?: number): void {
    const expiry = Date.now() + (ttl || this.defaultTTL)
    const item: CacheItem<T> = {
      value,
      expiry,
      timestamp: Date.now(),
      accessCount: 0,
      lastAccess: Date.now()
    }

    switch (this.storage) {
      case 'memory':
        this.setMemoryCache(key, item)
        break
      case 'localStorage':
        this.setStorageCache(key, item, localStorage)
        break
      case 'sessionStorage':
        this.setStorageCache(key, item, sessionStorage)
        break
    }
  }

  /**
   * 获取缓存
   */
  get<T>(key: string): T | null {
    const startTime = performance.now()
    
    if (this.enableStats) {
      this.stats.totalRequests++
    }

    let item: CacheItem<T> | null = null

    switch (this.storage) {
      case 'memory':
        item = this.getMemoryCache(key)
        break
      case 'localStorage':
        item = this.getStorageCache(key, localStorage)
        break
      case 'sessionStorage':
        item = this.getStorageCache(key, sessionStorage)
        break
    }

    if (!item) {
      if (this.enableStats) {
        this.stats.totalMisses++
        this.recordAccessTime(performance.now() - startTime)
      }
      return null
    }

    // 检查是否过期
    if (Date.now() > item.expiry) {
      this.delete(key)
      if (this.enableStats) {
        this.stats.totalMisses++
        this.recordAccessTime(performance.now() - startTime)
      }
      return null
    }

    // 更新访问统计
    if (this.enableStats) {
      item.accessCount++
      item.lastAccess = Date.now()
      this.stats.totalHits++
      this.recordAccessTime(performance.now() - startTime)
      
      // 更新存储中的统计信息
      this.updateItemStats(key, item)
    }

    return item.value
  }

  /**
   * 删除缓存
   */
  delete(key: string): void {
    switch (this.storage) {
      case 'memory':
        this.memoryCache.delete(key)
        break
      case 'localStorage':
        localStorage.removeItem(this.getCacheKey(key))
        break
      case 'sessionStorage':
        sessionStorage.removeItem(this.getCacheKey(key))
        break
    }
  }

  /**
   * 清空缓存
   */
  clear(): void {
    switch (this.storage) {
      case 'memory':
        this.memoryCache.clear()
        break
      case 'localStorage':
        this.clearStorageCache(localStorage)
        break
      case 'sessionStorage':
        this.clearStorageCache(sessionStorage)
        break
    }
    
    // 重置统计
    if (this.enableStats) {
      this.resetStats()
    }
  }

  /**
   * 检查缓存是否存在
   */
  has(key: string): boolean {
    return this.get(key) !== null
  }

  /**
   * 获取缓存统计信息
   */
  getStats(): CacheStats {
    let size = 0
    let topKeys: Array<{ key: string; accessCount: number; lastAccess: number }> = []
    
    switch (this.storage) {
      case 'memory':
        size = this.memoryCache.size
        topKeys = this.getTopMemoryKeys()
        break
      case 'localStorage':
      case 'sessionStorage':
        const storage = this.storage === 'localStorage' ? localStorage : sessionStorage
        size = this.getStorageCacheSize(storage)
        topKeys = this.getTopStorageKeys(storage)
        break
    }

    const hitRate = this.stats.totalRequests > 0 
      ? (this.stats.totalHits / this.stats.totalRequests) * 100 
      : 0

    const averageAccessTime = this.stats.accessTimes.length > 0
      ? this.stats.accessTimes.reduce((a, b) => a + b, 0) / this.stats.accessTimes.length
      : 0

    return {
      size,
      maxSize: this.maxSize,
      hitRate: Math.round(hitRate * 100) / 100,
      storage: this.storage,
      totalRequests: this.stats.totalRequests,
      totalHits: this.stats.totalHits,
      totalMisses: this.stats.totalMisses,
      averageAccessTime: Math.round(averageAccessTime * 1000) / 1000,
      topKeys: topKeys.slice(0, 10) // 返回前10个最常访问的键
    }
  }

  /**
   * 重置统计信息
   */
  resetStats(): void {
    this.stats = {
      totalRequests: 0,
      totalHits: 0,
      totalMisses: 0,
      accessTimes: []
    }
  }

  /**
   * 清理过期缓存
   */
  cleanup(): void {
    const now = Date.now()

    switch (this.storage) {
      case 'memory':
        for (const [key, item] of this.memoryCache) {
          if (now > item.expiry) {
            this.memoryCache.delete(key)
          }
        }
        break
      case 'localStorage':
        this.cleanupStorageCache(localStorage)
        break
      case 'sessionStorage':
        this.cleanupStorageCache(sessionStorage)
        break
    }
  }

  /**
   * 获取或设置缓存（如果不存在则执行函数获取值）
   */
  async getOrSet<T>(
    key: string,
    factory: () => Promise<T> | T,
    ttl?: number
  ): Promise<T> {
    const cached = this.get<T>(key)
    if (cached !== null) {
      return cached
    }

    const value = await factory()
    this.set(key, value, ttl)
    return value
  }

  /**
   * 批量设置缓存
   */
  setMultiple<T>(items: Array<{ key: string; value: T; ttl?: number }>): void {
    items.forEach(item => {
      this.set(item.key, item.value, item.ttl)
    })
  }

  /**
   * 批量获取缓存
   */
  getMultiple<T>(keys: string[]): Record<string, T | null> {
    const result: Record<string, T | null> = {}
    keys.forEach(key => {
      result[key] = this.get<T>(key)
    })
    return result
  }

  /**
   * 预热缓存
   */
  async warmup<T>(
    items: Array<{ key: string; factory: () => Promise<T> | T; ttl?: number }>
  ): Promise<void> {
    const promises = items.map(async item => {
      const value = await item.factory()
      this.set(item.key, value, item.ttl)
    })
    
    await Promise.all(promises)
  }

  /**
   * 获取缓存使用情况报告
   */
  getUsageReport(): {
    memoryUsage: string
    storageUsage: string
    performance: string
    recommendations: string[]
  } {
    const stats = this.getStats()
    const recommendations: string[] = []

    // 内存使用情况
    const memoryUsagePercent = (stats.size / stats.maxSize) * 100
    let memoryUsage = `使用 ${stats.size}/${stats.maxSize} (${memoryUsagePercent.toFixed(1)}%)`
    
    if (memoryUsagePercent > 90) {
      recommendations.push('缓存使用率过高，建议增加最大缓存数量或减少TTL')
    }

    // 存储使用情况
    let storageUsage = `存储类型: ${stats.storage}`
    if (this.storage !== 'memory') {
      storageUsage += `, 项目数: ${stats.size}`
    }

    // 性能情况
    let performance = `命中率: ${stats.hitRate}%, 平均访问时间: ${stats.averageAccessTime}ms`
    
    if (stats.hitRate < 70) {
      recommendations.push('缓存命中率较低，建议检查缓存策略和TTL设置')
    }
    
    if (stats.averageAccessTime > 5) {
      recommendations.push('平均访问时间较长，建议优化缓存存储方式')
    }

    if (recommendations.length === 0) {
      recommendations.push('缓存运行状态良好')
    }

    return {
      memoryUsage,
      storageUsage,
      performance,
      recommendations
    }
  }

  // 私有方法
  private recordAccessTime(time: number): void {
    this.stats.accessTimes.push(time)
    // 保持最近1000次访问记录
    if (this.stats.accessTimes.length > 1000) {
      this.stats.accessTimes.shift()
    }
  }

  private updateItemStats<T>(key: string, item: CacheItem<T>): void {
    switch (this.storage) {
      case 'memory':
        this.memoryCache.set(key, item)
        break
      case 'localStorage':
        this.setStorageCache(key, item, localStorage)
        break
      case 'sessionStorage':
        this.setStorageCache(key, item, sessionStorage)
        break
    }
  }

  private getTopMemoryKeys(): Array<{ key: string; accessCount: number; lastAccess: number }> {
    const items = Array.from(this.memoryCache.entries())
      .map(([key, item]) => ({
        key,
        accessCount: item.accessCount,
        lastAccess: item.lastAccess
      }))
      .sort((a, b) => b.accessCount - a.accessCount)
    
    return items
  }

  private getTopStorageKeys(storage: Storage): Array<{ key: string; accessCount: number; lastAccess: number }> {
    const items: Array<{ key: string; accessCount: number; lastAccess: number }> = []
    const prefix = this.getCachePrefix()
    
    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i)
      if (key && key.startsWith(prefix)) {
        try {
          const item = JSON.parse(storage.getItem(key) || '{}') as CacheItem
          items.push({
            key: key.replace(prefix, ''),
            accessCount: item.accessCount || 0,
            lastAccess: item.lastAccess || 0
          })
        } catch (error) {
          // 忽略解析错误
        }
      }
    }
    
    return items.sort((a, b) => b.accessCount - a.accessCount)
  }

  private setMemoryCache<T>(key: string, item: CacheItem<T>): void {
    // 如果超过最大容量，删除最旧的项
    if (this.memoryCache.size >= this.maxSize) {
      const oldestKey = this.getOldestMemoryCacheKey()
      if (oldestKey) {
        this.memoryCache.delete(oldestKey)
      }
    }
    
    this.memoryCache.set(key, item)
  }

  private getMemoryCache<T>(key: string): CacheItem<T> | null {
    return this.memoryCache.get(key) as CacheItem<T> || null
  }

  private getOldestMemoryCacheKey(): string | null {
    let oldestKey: string | null = null
    let oldestTimestamp = Date.now()
    
    for (const [key, item] of this.memoryCache) {
      if (item.timestamp < oldestTimestamp) {
        oldestTimestamp = item.timestamp
        oldestKey = key
      }
    }
    
    return oldestKey
  }

  private setStorageCache<T>(
    key: string,
    item: CacheItem<T>,
    storage: Storage
  ): void {
    try {
      storage.setItem(this.getCacheKey(key), JSON.stringify(item))
    } catch (error) {
      // 存储空间不足，清理过期项后重试
      this.cleanupStorageCache(storage)
      try {
        storage.setItem(this.getCacheKey(key), JSON.stringify(item))
      } catch (retryError) {
        console.warn('缓存存储失败:', retryError)
      }
    }
  }

  private getStorageCache<T>(key: string, storage: Storage): CacheItem<T> | null {
    try {
      const item = storage.getItem(this.getCacheKey(key))
      return item ? JSON.parse(item) : null
    } catch (error) {
      return null
    }
  }

  private cleanupStorageCache(storage: Storage): void {
    const now = Date.now()
    const prefix = this.getCachePrefix()
    const keysToDelete: string[] = []
    
    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i)
      if (key && key.startsWith(prefix)) {
        try {
          const item = JSON.parse(storage.getItem(key) || '{}') as CacheItem
          if (now > item.expiry) {
            keysToDelete.push(key)
          }
        } catch (error) {
          keysToDelete.push(key)
        }
      }
    }
    
    keysToDelete.forEach(key => storage.removeItem(key))
  }

  private clearStorageCache(storage: Storage): void {
    const prefix = this.getCachePrefix()
    const keysToDelete: string[] = []
    
    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i)
      if (key && key.startsWith(prefix)) {
        keysToDelete.push(key)
      }
    }
    
    keysToDelete.forEach(key => storage.removeItem(key))
  }

  private getStorageCacheSize(storage: Storage): number {
    const prefix = this.getCachePrefix()
    let count = 0
    
    for (let i = 0; i < storage.length; i++) {
      const key = storage.key(i)
      if (key && key.startsWith(prefix)) {
        count++
      }
    }
    
    return count
  }

  private getCacheKey(key: string): string {
    return `${this.getCachePrefix()}${key}`
  }

  private getCachePrefix(): string {
    return 'quant_cache_'
  }
}

// 导出默认实例
export const cacheService = new CacheService({
  maxSize: 2000,
  ttl: 10 * 60 * 1000, // 10分钟
  storage: 'memory',
  enableStats: true
})

// 导出专用缓存实例
export const marketDataCache = new CacheService({
  maxSize: 5000,
  ttl: 30 * 1000, // 30秒，行情数据更新频繁
  storage: 'memory',
  enableStats: true
})

export const userDataCache = new CacheService({
  maxSize: 500,
  ttl: 5 * 60 * 1000, // 5分钟
  storage: 'localStorage',
  enableStats: true
})

export const configCache = new CacheService({
  maxSize: 100,
  ttl: 60 * 60 * 1000, // 1小时
  storage: 'localStorage',
  enableStats: false // 配置数据不需要统计
})

// 启动定期清理任务
setInterval(() => {
  cacheService.cleanup()
  marketDataCache.cleanup()
  userDataCache.cleanup()
  configCache.cleanup()
}, 5 * 60 * 1000) // 每5分钟清理一次