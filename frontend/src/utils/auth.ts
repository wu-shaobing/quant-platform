/**
 * 认证相关工具函数
 */
import { STORAGE_KEYS } from './constants'
import { jwtDecode } from 'jwt-decode'

interface TokenPayload {
  userId: string
  username: string
  email: string
  exp: number
  iat: number
}

/**
 * 获取存储的Token
 */
export const getToken = (): string | null => {
  return localStorage.getItem(STORAGE_KEYS.AUTH_TOKEN)
}

/**
 * 设置Token
 */
export const setToken = (token: string): void => {
  localStorage.setItem(STORAGE_KEYS.AUTH_TOKEN, token)
}

/**
 * 移除Token
 */
export const removeToken = (): void => {
  localStorage.removeItem(STORAGE_KEYS.AUTH_TOKEN)
  localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN)
  localStorage.removeItem(STORAGE_KEYS.USER_INFO)
}

/**
 * 获取刷新Token
 */
export const getRefreshToken = (): string | null => {
  return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN)
}

/**
 * 设置刷新Token
 */
export const setRefreshToken = (token: string): void => {
  localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, token)
}

/**
 * 检查Token是否存在
 */
export const hasToken = (): boolean => {
  return !!getToken()
}

/**
 * 解析Token
 */
export const parseToken = (token: string): TokenPayload | null => {
  try {
    return jwtDecode<TokenPayload>(token)
  } catch (error) {
    console.error('Token解析失败:', error)
    return null
  }
}

/**
 * 检查Token是否过期
 */
export const isTokenExpired = (token?: string): boolean => {
  const tokenToCheck = token || getToken()
  if (!tokenToCheck) return true
  
  const payload = parseToken(tokenToCheck)
  if (!payload) return true
  
  // 提前5分钟判断过期
  const now = Date.now() / 1000
  return payload.exp < (now + 300)
}

/**
 * 检查Token是否即将过期（30分钟内）
 */
export const isTokenExpiringSoon = (token?: string): boolean => {
  const tokenToCheck = token || getToken()
  if (!tokenToCheck) return true
  
  const payload = parseToken(tokenToCheck)
  if (!payload) return true
  
  const now = Date.now() / 1000
  return payload.exp < (now + 1800) // 30分钟
}

/**
 * 获取Token剩余时间（秒）
 */
export const getTokenRemainingTime = (token?: string): number => {
  const tokenToCheck = token || getToken()
  if (!tokenToCheck) return 0
  
  const payload = parseToken(tokenToCheck)
  if (!payload) return 0
  
  const now = Date.now() / 1000
  return Math.max(0, payload.exp - now)
}

/**
 * 格式化Token过期时间
 */
export const formatTokenExpireTime = (token?: string): string => {
  const tokenToCheck = token || getToken()
  if (!tokenToCheck) return '未知'
  
  const payload = parseToken(tokenToCheck)
  if (!payload) return '未知'
  
  const expireDate = new Date(payload.exp * 1000)
  return expireDate.toLocaleString()
}

/**
 * 清除所有认证信息
 */
export const clearAuth = (): void => {
  removeToken()
  // 清除其他可能的用户相关缓存
  const keysToRemove = [
    STORAGE_KEYS.USER_INFO,
    STORAGE_KEYS.WATCHLIST,
    STORAGE_KEYS.TRADING_SETTINGS
  ]
  
  keysToRemove.forEach(key => {
    localStorage.removeItem(key)
  })
}

/**
 * 生成随机字符串（用于state参数等）
 */
export const generateRandomString = (length = 32): string => {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

/**
 * 加密敏感数据
 */
export const encryptSensitiveData = (data: string): string => {
  // 简单的Base64编码，实际项目中应该使用更安全的加密方式
  try {
    return btoa(encodeURIComponent(data))
  } catch (error) {
    console.error('数据加密失败:', error)
    return data
  }
}

/**
 * 解密敏感数据
 */
export const decryptSensitiveData = (encryptedData: string): string => {
  try {
    return decodeURIComponent(atob(encryptedData))
  } catch (error) {
    console.error('数据解密失败:', error)
    return encryptedData
  }
}

/**
 * 检查密码强度
 */
export const checkPasswordStrength = (password: string): {
  score: number
  level: 'weak' | 'medium' | 'strong' | 'very-strong'
  suggestions: string[]
} => {
  let score = 0
  const suggestions: string[] = []
  
  // 长度检查
  if (password.length >= 8) {
    score += 1
  } else {
    suggestions.push('密码长度至少8位')
  }
  
  if (password.length >= 12) {
    score += 1
  }
  
  // 包含小写字母
  if (/[a-z]/.test(password)) {
    score += 1
  } else {
    suggestions.push('包含小写字母')
  }
  
  // 包含大写字母
  if (/[A-Z]/.test(password)) {
    score += 1
  } else {
    suggestions.push('包含大写字母')
  }
  
  // 包含数字
  if (/\d/.test(password)) {
    score += 1
  } else {
    suggestions.push('包含数字')
  }
  
  // 包含特殊字符
  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    score += 1
  } else {
    suggestions.push('包含特殊字符')
  }
  
  // 不包含常见弱密码模式
  const weakPatterns = [
    /123456/,
    /password/i,
    /qwerty/i,
    /abc123/i,
    /111111/,
    /000000/
  ]
  
  const hasWeakPattern = weakPatterns.some(pattern => pattern.test(password))
  if (hasWeakPattern) {
    score -= 2
    suggestions.push('避免使用常见的弱密码模式')
  }
  
  // 确定强度等级
  let level: 'weak' | 'medium' | 'strong' | 'very-strong'
  if (score <= 2) {
    level = 'weak'
  } else if (score <= 4) {
    level = 'medium'
  } else if (score <= 5) {
    level = 'strong'
  } else {
    level = 'very-strong'
  }
  
  return {
    score: Math.max(0, score),
    level,
    suggestions
  }
}

/**
 * 检查是否需要重新登录
 */
export const shouldReLogin = (): boolean => {
  const token = getToken()
  if (!token) return true
  
  // 检查Token是否过期
  if (isTokenExpired(token)) return true
  
  // 检查上次登录时间（可选）
  const lastLoginTime = localStorage.getItem('last_login_time')
  if (lastLoginTime) {
    const lastLogin = parseInt(lastLoginTime)
    const now = Date.now()
    // 如果超过7天未登录，要求重新登录
    if (now - lastLogin > 7 * 24 * 60 * 60 * 1000) {
      return true
    }
  }
  
  return false
}

/**
 * 记录登录时间
 */
export const recordLoginTime = (): void => {
  localStorage.setItem('last_login_time', Date.now().toString())
}

/**
 * 获取用户权限列表
 */
export const getUserPermissions = (): string[] => {
  const token = getToken()
  if (!token) return []
  
  const payload = parseToken(token)
  if (!payload) return []
  
  // 从Token中解析权限，或从本地存储获取
  const userInfo = localStorage.getItem(STORAGE_KEYS.USER_INFO)
  if (userInfo) {
    try {
      const user = JSON.parse(userInfo)
      return user.permissions || []
    } catch (error) {
      console.error('解析用户信息失败:', error)
    }
  }
  
  return []
}

/**
 * 检查用户是否有指定权限
 */
export const hasPermission = (permission: string): boolean => {
  const permissions = getUserPermissions()
  return permissions.includes(permission) || permissions.includes('*')
}

/**
 * 检查用户是否有任一权限
 */
export const hasAnyPermission = (permissions: string[]): boolean => {
  return permissions.some(permission => hasPermission(permission))
}

/**
 * 检查用户是否有所有权限
 */
export const hasAllPermissions = (permissions: string[]): boolean => {
  return permissions.every(permission => hasPermission(permission))
}