/**
 * 格式化工具函数 - 导入更安全的金融格式化工具
 */
import dayjs from 'dayjs'
import numeral from 'numeral'

// 导入新的金融格式化工具
export {
  formatCurrency,
  formatPrice,
  formatPercent,
  formatChange,
  formatVolume,
  formatTurnover,
  formatMarketCap,
  formatPE,
  formatPB,
  safeCalculate,
  validateNumber
} from './format/financial'

// 兼容性格式化函数 - 使用新的金融格式化工具
export const formatCurrencyLegacy = (value: number, currency = '¥'): string => {
  if (isNaN(value)) return `${currency}0.00`
  return `${currency}${value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
}

export const formatPriceLegacy = (value: number): string => {
  if (isNaN(value)) return '0.00'
  return value.toFixed(2)
}

export const formatPercentLegacy = (value: number, decimals = 2): string => {
  if (isNaN(value)) return '0.00%'
  const sign = value >= 0 ? '+' : ''
  return `${sign}${(value * 100).toFixed(decimals)}%`
}

export const formatChangeLegacy = (change: number, isPercent = true): string => {
  if (isNaN(change)) return '0.00'
  
  const sign = change > 0 ? '+' : ''
  const value = isPercent ? (change * 100).toFixed(2) : change.toFixed(2)
  const suffix = isPercent ? '%' : ''
  
  return `${sign}${value}${suffix}`
}

export const formatVolumeLegacy = (volume: number): string => {
  if (isNaN(volume) || volume < 0) return '0'
  
  if (volume >= 100000000) {
    return `${(volume / 100000000).toFixed(2)}亿`
  } else if (volume >= 10000) {
    return `${(volume / 10000).toFixed(2)}万`
  } else {
    return volume.toFixed(0)
  }
}

// 保留原有市值格式化函数作为兼容性函数
export const formatMarketCapLegacy = (value: number | string): string => {
  const num = Number(value)
  if (isNaN(num)) return '--'
  
  if (num >= 1000000000000) {
    return numeral(num / 1000000000000).format('0.00') + '万亿'
  } else if (num >= 100000000) {
    return numeral(num / 100000000).format('0.00') + '亿'
  } else if (num >= 10000) {
    return numeral(num / 10000).format('0.00') + '万'
  } else {
    return numeral(num).format('0,0')
  }
}

/**
 * 格式化金额 (成交额等)
 */
export const formatAmount = (value: number | string): string => {
  const num = Number(value)
  if (isNaN(num)) return '--'
  
  if (num >= 1000000000000) {
    return numeral(num / 1000000000000).format('0.00') + '万亿'
  } else if (num >= 100000000) {
    return numeral(num / 100000000).format('0.00') + '亿'
  } else if (num >= 10000) {
    return numeral(num / 10000).format('0.00') + '万'
  } else {
    return numeral(num).format('0,0')
  }
}

/**
 * 格式化数字 - 增强类型安全
 */
export const formatNumber = (value: number | string, precision = 2): string => {
  const num = Number(value)
  if (isNaN(num)) return '0'
  return num.toLocaleString('zh-CN', {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision
  })
}

/**
 * 格式化日期时间
 */
export const formatDateTime = (
  value: string | number | Date,
  format = 'YYYY-MM-DD HH:mm:ss'
): string => {
  if (!value) return '--'
  return dayjs(value).format(format)
}

/**
 * 格式化日期
 */
export const formatDate = (
  value: string | number | Date,
  format = 'YYYY-MM-DD'
): string => {
  if (!value) return '--'
  return dayjs(value).format(format)
}

/**
 * 格式化时间
 */
export const formatTime = (time: Date | string | number, format = 'YYYY-MM-DD HH:mm:ss'): string => {
  let date: Date
  
  if (time instanceof Date) {
    date = time
  } else if (typeof time === 'string') {
    date = new Date(time)
  } else if (typeof time === 'number') {
    date = new Date(time)
  } else {
    return ''
  }
  
  if (isNaN(date.getTime())) return ''
  
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

/**
 * 格式化相对时间
 */
export const formatRelativeTime = (time: Date | string | number): string => {
  const now = new Date()
  const targetTime = new Date(time)
  
  if (isNaN(targetTime.getTime())) return ''
  
  const diff = now.getTime() - targetTime.getTime()
  const seconds = Math.floor(diff / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) {
    return `${days}天前`
  } else if (hours > 0) {
    return `${hours}小时前`
  } else if (minutes > 0) {
    return `${minutes}分钟前`
  } else if (seconds > 0) {
    return `${seconds}秒前`
  } else {
    return '刚刚'
  }
}

/**
 * 格式化持续时间
 */
export const formatDuration = (milliseconds: number): string => {
  if (isNaN(milliseconds) || milliseconds < 0) return '0秒'
  
  const seconds = Math.floor(milliseconds / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) {
    const remainingHours = hours % 24
    return remainingHours > 0 ? `${days}天${remainingHours}小时` : `${days}天`
  } else if (hours > 0) {
    const remainingMinutes = minutes % 60
    return remainingMinutes > 0 ? `${hours}小时${remainingMinutes}分钟` : `${hours}小时`
  } else if (minutes > 0) {
    const remainingSeconds = seconds % 60
    return remainingSeconds > 0 ? `${minutes}分钟${remainingSeconds}秒` : `${minutes}分钟`
  } else {
    return `${seconds}秒`
  }
}

/**
 * 格式化文件大小
 */
export const formatFileSize = (bytes: number): string => {
  if (isNaN(bytes) || bytes < 0) return '0 B'
  
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(unitIndex === 0 ? 0 : 2)} ${units[unitIndex]}`
}

/**
 * 格式化股票代码
 */
export const formatStockCode = (code: string): string => {
  if (!code) return ''
  
  // 移除可能的后缀
  const cleanCode = code.split('.')[0]
  
  // 确保是6位数字
  return cleanCode.padStart(6, '0')
}

/**
 * 格式化订单状态
 */
export const formatOrderStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    pending: '待成交',
    partial_filled: '部分成交',
    filled: '已成交',
    cancelled: '已撤销',
    rejected: '已拒绝',
    expired: '已过期'
  }
  
  return statusMap[status] || status
}

/**
 * 格式化订单类型
 */
export const formatOrderType = (type: string): string => {
  const typeMap: Record<string, string> = {
    limit: '限价单',
    market: '市价单',
    stop: '止损单',
    stop_limit: '止损限价单',
    trailing_stop: '跟踪止损单'
  }
  
  return typeMap[type] || type
}

/**
 * 格式化订单方向
 */
export const formatOrderSide = (side: string): string => {
  const sideMap: Record<string, string> = {
    buy: '买入',
    sell: '卖出'
  }
  
  return sideMap[side] || side
}

/**
 * 格式化策略状态
 */
export const formatStrategyStatus = (status: string): string => {
  const statusMap: Record<string, string> = {
    draft: '草稿',
    testing: '测试中',
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    error: '错误'
  }
  
  return statusMap[status] || status
}

/**
 * 格式化风险等级
 */
export const formatRiskLevel = (level: string): string => {
  const levelMap: Record<string, string> = {
    low: '低风险',
    medium: '中等风险',
    high: '高风险',
    extreme: '极高风险'
  }
  
  return levelMap[level] || level
}

/**
 * 格式化手机号（脱敏）
 */
export const formatMobile = (mobile: string, mask = true): string => {
  if (!mobile) return '--'
  
  if (mask && mobile.length === 11) {
    return mobile.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
  }
  
  return mobile
}

/**
 * 格式化邮箱（脱敏）
 */
export const formatEmail = (email: string, mask = true): string => {
  if (!email) return '--'
  
  if (mask) {
    const [username, domain] = email.split('@')
    if (username && domain) {
      const maskedUsername = username.length > 2 
        ? username.slice(0, 2) + '***' + username.slice(-1)
        : username
      return `${maskedUsername}@${domain}`
    }
  }
  
  return email
}

/**
 * 格式化银行卡号（脱敏）
 */
export const formatBankCard = (cardNumber: string, mask = true): string => {
  if (!cardNumber) return '--'
  
  if (mask && cardNumber.length >= 8) {
    return cardNumber.replace(/(\d{4})\d+(\d{4})/, '$1 **** **** $2')
  }
  
  return cardNumber.replace(/(\d{4})/g, '$1 ').trim()
}

/**
 * 高亮搜索关键词
 */
export const highlightKeyword = (text: string, keyword: string): string => {
  if (!text || !keyword) return text
  
  const regex = new RegExp(`(${keyword})`, 'gi')
  return text.replace(regex, '<mark>$1</mark>')
}

/**
 * 格式化K线周期
 */
export const formatKlinePeriod = (period: string): string => {
  const periodMap: Record<string, string> = {
    '1m': '1分钟',
    '5m': '5分钟',
    '15m': '15分钟',
    '30m': '30分钟',
    '1h': '1小时',
    '4h': '4小时',
    '1d': '日线',
    '1w': '周线',
    '1M': '月线'
  }
  
  return periodMap[period] || period
}

/**
 * 获取涨跌幅颜色类名
 */
export const getChangeColorClass = (change: number): string => {
  if (change > 0) return 'text-red-600'
  if (change < 0) return 'text-green-600'
  return 'text-gray-600'
}

/**
 * 截断文本
 */
export const truncateText = (text: string, maxLength: number): string => {
  if (!text || text.length <= maxLength) return text
  return text.substring(0, maxLength) + '...'
}