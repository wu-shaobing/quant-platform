import { Decimal } from 'decimal.js'

/**
 * 数字格式化配置选项
 */
interface NumberFormatOptions {
  /**
   * 小数位数
   */
  precision?: number
  /**
   * 是否使用千位分隔符
   */
  useGrouping?: boolean
  /**
   * 千位分隔符
   */
  groupingSeparator?: string
  /**
   * 小数点符号
   */
  decimalSeparator?: string
  /**
   * 前缀
   */
  prefix?: string
  /**
   * 后缀
   */
  suffix?: string
  /**
   * 是否显示正号
   */
  showPositiveSign?: boolean
  /**
   * 空值时显示的文本
   */
  nullDisplay?: string
  /**
   * 无效值时显示的文本
   */
  invalidDisplay?: string
}

/**
 * 默认格式化选项
 */
const DEFAULT_OPTIONS: Required<NumberFormatOptions> = {
  precision: 2,
  useGrouping: true,
  groupingSeparator: ',',
  decimalSeparator: '.',
  prefix: '',
  suffix: '',
  showPositiveSign: false,
  nullDisplay: '--',
  invalidDisplay: '--'
}

/**
 * 基础数字格式化函数
 * @param value 数值
 * @param options 格式化选项
 * @returns 格式化后的字符串
 */
export function formatNumber(
  value: number | string | null | undefined,
  options: NumberFormatOptions = {}
): string {
  const opts = { ...DEFAULT_OPTIONS, ...options }

  // 处理空值
  if (value === null || value === undefined) {
    return opts.nullDisplay
  }

  // 转换为数字
  const num = typeof value === 'string' ? parseFloat(value) : value

  // 处理无效值
  if (isNaN(num) || !isFinite(num)) {
    return opts.invalidDisplay
  }

  try {
    // 使用 Decimal.js 进行精确计算
    const decimal = new Decimal(num)
    
    // 应用精度
    const rounded = decimal.toFixed(opts.precision)
    
    // 分离整数和小数部分
    const [integerPart, decimalPart] = rounded.split('.')
    
    // 处理千位分隔符
    let formattedInteger = integerPart
    if (opts.useGrouping && Math.abs(parseInt(integerPart)) >= 1000) {
      formattedInteger = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, opts.groupingSeparator)
    }
    
    // 组合结果
    let result = formattedInteger
    if (decimalPart && opts.precision > 0) {
      result += opts.decimalSeparator + decimalPart
    }
    
    // 添加正号
    if (opts.showPositiveSign && num > 0) {
      result = '+' + result
    }
    
    // 添加前缀和后缀
    return opts.prefix + result + opts.suffix
    
  } catch (error) {
    console.error('数字格式化失败:', error)
    return opts.invalidDisplay
  }
}

/**
 * 货币格式化
 * @param value 数值
 * @param currency 货币符号
 * @param precision 小数位数
 * @returns 格式化后的货币字符串
 */
export function formatCurrency(
  value: number | string | null | undefined,
  currency = '¥',
  precision = 2
): string {
  return formatNumber(value, {
    precision,
    prefix: currency,
    useGrouping: true
  })
}

/**
 * 百分比格式化
 * @param value 数值 (0.15 表示 15%)
 * @param precision 小数位数
 * @param multiply100 是否乘以100 (如果传入的值已经是百分比形式则设为false)
 * @returns 格式化后的百分比字符串
 */
export function formatPercent(
  value: number | string | null | undefined,
  precision = 2,
  multiply100 = true
): string {
  if (value === null || value === undefined) {
    return '--'
  }

  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return '--'
  }

  const percentValue = multiply100 ? num * 100 : num
  
  return formatNumber(percentValue, {
    precision,
    suffix: '%',
    showPositiveSign: true
  })
}

/**
 * 中文数字单位格式化
 * @param value 数值
 * @param precision 小数位数
 * @param forceUnit 强制使用指定单位
 * @returns 格式化后的字符串
 */
export function formatChineseNumber(
  value: number | string | null | undefined,
  precision = 2,
  forceUnit?: '万' | '亿' | '万亿'
): string {
  if (value === null || value === undefined) {
    return '--'
  }

  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return '--'
  }

  const absNum = Math.abs(num)
  
  if (forceUnit) {
    const unitMap = {
      '万': 10000,
      '亿': 100000000,
      '万亿': 1000000000000
    }
    
    const divisor = unitMap[forceUnit]
    const result = new Decimal(num).div(divisor).toFixed(precision)
    return result + forceUnit
  }

  // 自动选择单位
  if (absNum >= 1000000000000) {
    // 万亿
    const result = new Decimal(num).div(1000000000000).toFixed(precision)
    return result + '万亿'
  } else if (absNum >= 100000000) {
    // 亿
    const result = new Decimal(num).div(100000000).toFixed(precision)
    return result + '亿'
  } else if (absNum >= 10000) {
    // 万
    const result = new Decimal(num).div(10000).toFixed(precision)
    return result + '万'
  } else {
    return formatNumber(num, { precision })
  }
}

/**
 * 文件大小格式化
 * @param bytes 字节数
 * @param precision 小数位数
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(
  bytes: number | string | null | undefined,
  precision = 2
): string {
  if (bytes === null || bytes === undefined) {
    return '--'
  }

  const num = typeof bytes === 'string' ? parseFloat(bytes) : bytes
  if (isNaN(num) || num < 0) {
    return '--'
  }

  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  let unitIndex = 0
  let size = num

  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }

  return formatNumber(size, { precision }) + ' ' + units[unitIndex]
}

/**
 * 时间间隔格式化
 * @param seconds 秒数
 * @returns 格式化后的时间字符串
 */
export function formatDuration(seconds: number | string | null | undefined): string {
  if (seconds === null || seconds === undefined) {
    return '--'
  }

  const num = typeof seconds === 'string' ? parseFloat(seconds) : seconds
  if (isNaN(num) || num < 0) {
    return '--'
  }

  const hours = Math.floor(num / 3600)
  const minutes = Math.floor((num % 3600) / 60)
  const secs = Math.floor(num % 60)

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  } else {
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }
}

/**
 * 涨跌幅格式化 (带颜色类名)
 * @param value 涨跌幅值
 * @param precision 小数位数
 * @returns 包含值和样式类名的对象
 */
export function formatChange(
  value: number | string | null | undefined,
  precision = 2
): {
  text: string
  className: string
} {
  if (value === null || value === undefined) {
    return { text: '--', className: 'text-neutral' }
  }

  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) {
    return { text: '--', className: 'text-neutral' }
  }

  const text = formatNumber(num, {
    precision,
    showPositiveSign: true
  })

  let className = 'text-neutral'
  if (num > 0) {
    className = 'text-up'
  } else if (num < 0) {
    className = 'text-down'
  }

  return { text, className }
}

/**
 * 涨跌幅和涨跌额组合格式化
 * @param change 涨跌额
 * @param changePercent 涨跌幅
 * @param precision 小数位数
 * @returns 格式化后的字符串
 */
export function formatChangeWithPercent(
  change: number | string | null | undefined,
  changePercent: number | string | null | undefined,
  precision = 2
): {
  text: string
  className: string
} {
  const changeResult = formatChange(change, precision)
  const percentResult = formatPercent(changePercent, precision, false)

  return {
    text: `${changeResult.text} (${percentResult})`,
    className: changeResult.className
  }
}

/**
 * 股价格式化 (根据价格范围自动调整精度)
 * @param price 价格
 * @returns 格式化后的价格字符串
 */
export function formatPrice(price: number | string | null | undefined): string {
  if (price === null || price === undefined) {
    return '--'
  }

  const num = typeof price === 'string' ? parseFloat(price) : price
  if (isNaN(num)) {
    return '--'
  }

  // 根据价格范围自动调整精度
  let precision = 2
  if (num >= 1000) {
    precision = 1
  } else if (num >= 100) {
    precision = 2
  } else if (num >= 10) {
    precision = 2
  } else if (num >= 1) {
    precision = 3
  } else {
    precision = 4
  }

  return formatNumber(num, { precision })
}

/**
 * 成交量格式化
 * @param volume 成交量
 * @returns 格式化后的成交量字符串
 */
export function formatVolume(volume: number | string | null | undefined): string {
  if (volume === null || volume === undefined) {
    return '--'
  }

  const num = typeof volume === 'string' ? parseFloat(volume) : volume
  if (isNaN(num)) {
    return '--'
  }

  return formatChineseNumber(num, 0)
}

/**
 * 市值格式化
 * @param marketCap 市值
 * @returns 格式化后的市值字符串
 */
export function formatMarketCap(marketCap: number | string | null | undefined): string {
  if (marketCap === null || marketCap === undefined) {
    return '--'
  }

  const num = typeof marketCap === 'string' ? parseFloat(marketCap) : marketCap
  if (isNaN(num)) {
    return '--'
  }

  return formatChineseNumber(num, 2)
}

/**
 * 换手率格式化
 * @param turnover 换手率 (小数形式，如 0.05 表示 5%)
 * @returns 格式化后的换手率字符串
 */
export function formatTurnover(turnover: number | string | null | undefined): string {
  return formatPercent(turnover, 2, true)
}

/**
 * 市盈率格式化
 * @param pe 市盈率
 * @returns 格式化后的市盈率字符串
 */
export function formatPE(pe: number | string | null | undefined): string {
  if (pe === null || pe === undefined) {
    return '--'
  }

  const num = typeof pe === 'string' ? parseFloat(pe) : pe
  if (isNaN(num) || num <= 0) {
    return '--'
  }

  return formatNumber(num, { precision: 2 })
}

/**
 * 数字输入格式化 (移除非数字字符)
 * @param value 输入值
 * @param allowDecimal 是否允许小数
 * @param allowNegative 是否允许负数
 * @returns 格式化后的数字字符串
 */
export function formatNumberInput(
  value: string,
  allowDecimal = true,
  allowNegative = false
): string {
  if (!value) return ''

  // 移除非数字字符
  let cleaned = value.replace(/[^\d.-]/g, '')

  // 处理负号
  if (!allowNegative) {
    cleaned = cleaned.replace(/-/g, '')
  } else {
    // 只允许开头有一个负号
    const negativeMatch = cleaned.match(/^-/)
    cleaned = cleaned.replace(/-/g, '')
    if (negativeMatch) {
      cleaned = '-' + cleaned
    }
  }

  // 处理小数点
  if (!allowDecimal) {
    cleaned = cleaned.replace(/\./g, '')
  } else {
    // 只允许一个小数点
    const parts = cleaned.split('.')
    if (parts.length > 2) {
      cleaned = parts[0] + '.' + parts.slice(1).join('')
    }
  }

  return cleaned
}

/**
 * 安全的数字运算 (避免浮点数精度问题)
 */
export const SafeMath = {
  /**
   * 加法
   */
  add: (a: number | string, b: number | string): number => {
    return new Decimal(a).plus(b).toNumber()
  },

  /**
   * 减法
   */
  subtract: (a: number | string, b: number | string): number => {
    return new Decimal(a).minus(b).toNumber()
  },

  /**
   * 乘法
   */
  multiply: (a: number | string, b: number | string): number => {
    return new Decimal(a).mul(b).toNumber()
  },

  /**
   * 除法
   */
  divide: (a: number | string, b: number | string): number => {
    return new Decimal(a).div(b).toNumber()
  },

  /**
   * 四舍五入
   */
  round: (value: number | string, precision = 0): number => {
    return new Decimal(value).toDecimalPlaces(precision).toNumber()
  },

  /**
   * 向上取整
   */
  ceil: (value: number | string): number => {
    return new Decimal(value).ceil().toNumber()
  },

  /**
   * 向下取整
   */
  floor: (value: number | string): number => {
    return new Decimal(value).floor().toNumber()
  },

  /**
   * 比较大小
   */
  compare: (a: number | string, b: number | string): -1 | 0 | 1 => {
    return new Decimal(a).cmp(b) as -1 | 0 | 1
  },

  /**
   * 是否相等
   */
  equals: (a: number | string, b: number | string): boolean => {
    return new Decimal(a).equals(b)
  },

  /**
   * 绝对值
   */
  abs: (value: number | string): number => {
    return new Decimal(value).abs().toNumber()
  },

  /**
   * 幂运算
   */
  pow: (base: number | string, exponent: number | string): number => {
    return new Decimal(base).pow(exponent).toNumber()
  }
} 