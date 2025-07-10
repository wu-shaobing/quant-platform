import CryptoJS from 'crypto-js'
import DOMPurify from 'dompurify'

// ============ 数据加密/解密 ============

const ENCRYPTION_KEY = import.meta.env.VITE_ENCRYPTION_KEY || 'default-key-change-in-production'

/**
 * 加密敏感数据
 */
export function encryptData(data: string): string {
  try {
    return CryptoJS.AES.encrypt(data, ENCRYPTION_KEY).toString()
  } catch (error) {
    console.error('数据加密失败:', error)
    return data
  }
}

/**
 * 解密敏感数据
 */
export function decryptData(encryptedData: string): string {
  try {
    const bytes = CryptoJS.AES.decrypt(encryptedData, ENCRYPTION_KEY)
    return bytes.toString(CryptoJS.enc.Utf8)
  } catch (error) {
    console.error('数据解密失败:', error)
    return encryptedData
  }
}

/**
 * 生成随机密钥
 */
export function generateRandomKey(length: number = 32): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  let result = ''
  for (let i = 0; i < length; i++) {
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

// ============ 输入验证和清理 ============

/**
 * 清理HTML内容，防止XSS攻击
 */
export function sanitizeHtml(html: string): string {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
    ALLOWED_ATTR: ['href', 'target']
  })
}

/**
 * 验证邮箱格式
 */
export function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

/**
 * 验证密码强度
 */
export function validatePassword(password: string): {
  isValid: boolean
  score: number
  feedback: string[]
} {
  const feedback: string[] = []
  let score = 0

  // 长度检查
  if (password.length >= 8) {
    score += 1
  } else {
    feedback.push('密码长度至少8位')
  }

  // 包含小写字母
  if (/[a-z]/.test(password)) {
    score += 1
  } else {
    feedback.push('需要包含小写字母')
  }

  // 包含大写字母
  if (/[A-Z]/.test(password)) {
    score += 1
  } else {
    feedback.push('需要包含大写字母')
  }

  // 包含数字
  if (/\d/.test(password)) {
    score += 1
  } else {
    feedback.push('需要包含数字')
  }

  // 包含特殊字符
  if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    score += 1
  } else {
    feedback.push('需要包含特殊字符')
  }

  return {
    isValid: score >= 4,
    score,
    feedback
  }
}

/**
 * 验证手机号格式
 */
export function validatePhone(phone: string): boolean {
  const phoneRegex = /^1[3-9]\d{9}$/
  return phoneRegex.test(phone)
}

/**
 * 验证身份证号格式
 */
export function validateIdCard(idCard: string): boolean {
  const idCardRegex = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/
  return idCardRegex.test(idCard)
}

// ============ 数据脱敏 ============

/**
 * 脱敏手机号
 */
export function maskPhone(phone: string): string {
  if (!phone || phone.length !== 11) return phone
  return phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
}

/**
 * 脱敏邮箱
 */
export function maskEmail(email: string): string {
  if (!email || !email.includes('@')) return email
  const [username, domain] = email.split('@')
  if (username.length <= 2) return email
  const maskedUsername = username.charAt(0) + '*'.repeat(username.length - 2) + username.charAt(username.length - 1)
  return `${maskedUsername}@${domain}`
}

/**
 * 脱敏身份证号
 */
export function maskIdCard(idCard: string): string {
  if (!idCard || idCard.length < 8) return idCard
  return idCard.replace(/(\d{4})\d+(\d{4})/, '$1**********$2')
}

/**
 * 脱敏银行卡号
 */
export function maskBankCard(cardNumber: string): string {
  if (!cardNumber || cardNumber.length < 8) return cardNumber
  return cardNumber.replace(/(\d{4})\d+(\d{4})/, '$1 **** **** $2')
}

// ============ 安全检查 ============

/**
 * 检查是否为安全的URL
 */
export function isSafeUrl(url: string): boolean {
  try {
    const urlObj = new URL(url)
    const allowedProtocols = ['http:', 'https:']
    const blockedDomains = ['localhost', '127.0.0.1', '0.0.0.0']
    
    if (!allowedProtocols.includes(urlObj.protocol)) {
      return false
    }
    
    if (import.meta.env.PROD && blockedDomains.some(domain => urlObj.hostname.includes(domain))) {
      return false
    }
    
    return true
  } catch {
    return false
  }
}

/**
 * 检查文件类型是否安全
 */
export function isSafeFileType(filename: string, allowedTypes: string[]): boolean {
  const extension = filename.split('.').pop()?.toLowerCase()
  return extension ? allowedTypes.includes(extension) : false
}

/**
 * 检查文件大小是否在限制内
 */
export function isFileSizeValid(file: File, maxSizeMB: number): boolean {
  const maxSizeBytes = maxSizeMB * 1024 * 1024
  return file.size <= maxSizeBytes
}

// ============ Token管理 ============

/**
 * 生成CSRF Token
 */
export function generateCSRFToken(): string {
  return generateRandomKey(32)
}

/**
 * 验证CSRF Token
 */
export function validateCSRFToken(token: string, expectedToken: string): boolean {
  return token === expectedToken
}

/**
 * 检查JWT Token是否过期
 */
export function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    const currentTime = Math.floor(Date.now() / 1000)
    return payload.exp < currentTime
  } catch {
    return true
  }
}

/**
 * 从JWT Token中获取用户信息
 */
export function getUserFromToken(token: string): any {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return payload
  } catch {
    return null
  }
}

// ============ 内容安全策略 ============

/**
 * 设置内容安全策略
 */
export function setContentSecurityPolicy(): void {
  const csp = [
    "default-src 'self'",
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: https:",
    "font-src 'self' https:",
    "connect-src 'self' ws: wss: https:",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'"
  ].join('; ')

  const meta = document.createElement('meta')
  meta.httpEquiv = 'Content-Security-Policy'
  meta.content = csp
  document.head.appendChild(meta)
}

// ============ 会话安全 ============

/**
 * 生成会话ID
 */
export function generateSessionId(): string {
  return generateRandomKey(64)
}

/**
 * 检查会话是否有效
 */
export function isSessionValid(sessionId: string, createdAt: number, maxAge: number = 3600000): boolean {
  if (!sessionId || sessionId.length < 32) return false
  const now = Date.now()
  return (now - createdAt) <= maxAge
}

// ============ 输入过滤 ============

/**
 * 过滤SQL注入字符
 */
export function filterSQLInjection(input: string): string {
  const sqlKeywords = [
    'SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
    'EXEC', 'UNION', 'SCRIPT', 'JAVASCRIPT', 'VBSCRIPT'
  ]
  
  let filtered = input
  sqlKeywords.forEach(keyword => {
    const regex = new RegExp(keyword, 'gi')
    filtered = filtered.replace(regex, '')
  })
  
  return filtered
}

/**
 * 过滤XSS攻击字符
 */
export function filterXSS(input: string): string {
  return input
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;')
}

// ============ 安全配置 ============

export const SECURITY_CONFIG = {
  // 密码配置
  password: {
    minLength: 8,
    maxLength: 128,
    requireUppercase: true,
    requireLowercase: true,
    requireNumbers: true,
    requireSpecialChars: true,
    maxAttempts: 5,
    lockoutDuration: 15 * 60 * 1000 // 15分钟
  },
  
  // 会话配置
  session: {
    maxAge: 24 * 60 * 60 * 1000, // 24小时
    renewThreshold: 30 * 60 * 1000, // 30分钟前续期
    maxConcurrentSessions: 3
  },
  
  // 文件上传配置
  upload: {
    maxFileSize: 10, // MB
    allowedTypes: ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'],
    maxFiles: 5
  },
  
  // API配置
  api: {
    requestTimeout: 30000, // 30秒
    maxRetries: 3,
    rateLimitPerMinute: 100
  }
}

// ============ 安全事件记录 ============

export interface SecurityEvent {
  type: 'login_attempt' | 'password_change' | 'suspicious_activity' | 'access_denied'
  userId?: string
  ip: string
  userAgent: string
  timestamp: number
  details?: any
}

/**
 * 记录安全事件
 */
export function logSecurityEvent(event: Omit<SecurityEvent, 'timestamp'>): void {
  const securityEvent: SecurityEvent = {
    ...event,
    timestamp: Date.now()
  }
  
  // 发送到后端或本地存储
  console.log('Security Event:', securityEvent)
  
  // 如果是生产环境，发送到安全监控系统
  if (import.meta.env.PROD) {
    // TODO: 发送到安全监控系统
  }
}

/**
 * 获取客户端IP（通过WebRTC）
 */
export async function getClientIP(): Promise<string> {
  return new Promise((resolve) => {
    const rtc = new RTCPeerConnection({ iceServers: [] })
    rtc.createDataChannel('')
    
    rtc.onicecandidate = (event) => {
      if (event.candidate) {
        const candidate = event.candidate.candidate
        const ipMatch = candidate.match(/(\d+\.\d+\.\d+\.\d+)/)
        if (ipMatch) {
          resolve(ipMatch[1])
          rtc.close()
        }
      }
    }
    
    rtc.createOffer().then(offer => rtc.setLocalDescription(offer))
    
    // 超时处理
    setTimeout(() => {
      resolve('unknown')
      rtc.close()
    }, 5000)
  })
} 