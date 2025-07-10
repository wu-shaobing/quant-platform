/**
 * 金融数据格式化工具
 */

import Decimal from 'decimal.js'

// 配置Decimal精度
Decimal.config({ precision: 20, rounding: 4 })

/**
 * 格式化货币
 * @param value 数值
 * @param precision 小数位数
 * @param currency 货币符号
 * @param locale 地区
 */
export function formatCurrency(
  value: number | string,
  precision = 2,
  currency = '¥',
  locale = 'zh-CN'
): string {
  if (value === null || value === undefined || value === '') {
    return `${currency}0.00`
  }

  const num = new Decimal(value)
  
  if (num.isNaN()) {
    return `${currency}0.00`
  }

  // 大数值简化显示
  const absNum = num.abs()
  
  if (absNum.gte(1e12)) {
    return `${currency}${num.div(1e12).toFixed(precision)}万亿`
  } else if (absNum.gte(1e8)) {
    return `${currency}${num.div(1e8).toFixed(precision)}亿`
  } else if (absNum.gte(1e4)) {
    return `${currency}${num.div(1e4).toFixed(precision)}万`
  }

  const formatted = new Intl.NumberFormat(locale, {
    minimumFractionDigits: precision,
    maximumFractionDigits: precision
  }).format(num.toNumber())

  return `${currency}${formatted}`
}

/**
 * 格式化价格
 * @param value 数值
 * @param precision 小数位数
 */
export function formatPrice(value: number | string, precision = 2): string {
  if (value === null || value === undefined || value === '') {
    return '0.00'
  }

  const num = new Decimal(value)
  
  if (num.isNaN()) {
    return '0.00'
  }

  return num.toFixed(precision)
}

/**
 * 格式化百分比
 * @param value 数值（小数形式，如0.05表示5%）
 * @param precision 小数位数
 * @param showSign 是否显示正负号
 */
export function formatPercent(
  value: number | string,
  precision = 2,
  showSign = false
): string {
  if (value === null || value === undefined || value === '') {
    return '0.00%'
  }

  const num = new Decimal(value)
  
  if (num.isNaN()) {
    return '0.00%'
  }

  const percent = num.mul(100)
  const sign = showSign && percent.gt(0) ? '+' : ''
  
  return `${sign}${percent.toFixed(precision)}%`
}

/**
 * 格式化变化值和百分比
 * @param change 变化值
 * @param changePercent 变化百分比
 * @param precision 小数位数
 */
export function formatChange(
  change: number | string,
  changePercent: number | string,
  precision = 2
): string {
  const changeNum = new Decimal(change || 0)
  const percentNum = new Decimal(changePercent || 0)
  
  const changeStr = changeNum.gt(0) ? `+${changeNum.toFixed(precision)}` : changeNum.toFixed(precision)
  const percentStr = formatPercent(percentNum, precision, true)
  
  return `${changeStr} (${percentStr})`
}

/**
 * 格式化成交量
 * @param volume 成交量
 * @param precision 小数位数
 */
export function formatVolume(volume: number | string, precision = 0): string {
  if (volume === null || volume === undefined || volume === '') {
    return '0'
  }

  const num = new Decimal(volume)
  
  if (num.isNaN()) {
    return '0'
  }

  const absNum = num.abs()
  
  if (absNum.gte(1e8)) {
    return `${num.div(1e8).toFixed(precision)}亿`
  } else if (absNum.gte(1e4)) {
    return `${num.div(1e4).toFixed(precision)}万`
  }

  return num.toFixed(precision)
}

/**
 * 格式化成交额
 * @param turnover 成交额
 * @param precision 小数位数
 */
export function formatTurnover(turnover: number | string, precision = 2): string {
  return formatCurrency(turnover, precision, '')
}

/**
 * 格式化市值
 * @param marketCap 市值
 * @param precision 小数位数
 */
export function formatMarketCap(marketCap: number | string, precision = 2): string {
  return formatCurrency(marketCap, precision, '')
}

/**
 * 格式化市盈率
 * @param pe 市盈率
 * @param precision 小数位数
 */
export function formatPE(pe: number | string, precision = 2): string {
  if (pe === null || pe === undefined || pe === '') {
    return '-'
  }

  const num = new Decimal(pe)
  
  if (num.isNaN() || num.lte(0)) {
    return '-'
  }

  return num.toFixed(precision)
}

/**
 * 格式化市净率
 * @param pb 市净率
 * @param precision 小数位数
 */
export function formatPB(pb: number | string, precision = 2): string {
  return formatPE(pb, precision) // 逻辑相同
}

/**
 * 格式化换手率
 * @param turnoverRate 换手率
 * @param precision 小数位数
 */
export function formatTurnoverRate(turnoverRate: number | string, precision = 2): string {
  return formatPercent(turnoverRate, precision)
}

/**
 * 格式化涨跌幅限制
 * @param value 当前价格
 * @param basePrice 基准价格（如昨收价）
 * @param limitPercent 涨跌幅限制（如0.1表示10%）
 */
export function formatPriceLimit(
  value: number | string,
  basePrice: number | string,
  limitPercent = 0.1
): { isLimit: boolean; limitType: 'up' | 'down' | null } {
  const price = new Decimal(value || 0)
  const base = new Decimal(basePrice || 0)
  const limit = new Decimal(limitPercent)
  
  if (base.lte(0)) {
    return { isLimit: false, limitType: null }
  }
  
  const upLimit = base.mul(limit.add(1))
  const downLimit = base.mul(Decimal.sub(1, limit))
  
  if (price.gte(upLimit)) {
    return { isLimit: true, limitType: 'up' }
  } else if (price.lte(downLimit)) {
    return { isLimit: true, limitType: 'down' }
  }
  
  return { isLimit: false, limitType: null }
}

/**
 * 安全的数值运算
 */
export const safeCalculate = {
  add: (a: number | string, b: number | string): number => {
    return new Decimal(a || 0).add(new Decimal(b || 0)).toNumber()
  },
  
  sub: (a: number | string, b: number | string): number => {
    return new Decimal(a || 0).sub(new Decimal(b || 0)).toNumber()
  },
  
  mul: (a: number | string, b: number | string): number => {
    return new Decimal(a || 0).mul(new Decimal(b || 0)).toNumber()
  },
  
  div: (a: number | string, b: number | string): number => {
    const divisor = new Decimal(b || 1)
    if (divisor.eq(0)) return 0
    return new Decimal(a || 0).div(divisor).toNumber()
  }
}

/**
 * 数值验证工具
 */
export const validateNumber = {
  isPositive: (value: number | string): boolean => {
    const num = new Decimal(value || 0)
    return !num.isNaN() && num.gt(0)
  },
  
  isNonNegative: (value: number | string): boolean => {
    const num = new Decimal(value || 0)
    return !num.isNaN() && num.gte(0)
  },
  
  isInRange: (value: number | string, min: number, max: number): boolean => {
    const num = new Decimal(value || 0)
    return !num.isNaN() && num.gte(min) && num.lte(max)
  },
  
  isValidPrice: (value: number | string): boolean => {
    const num = new Decimal(value || 0)
    return !num.isNaN() && num.gt(0) && num.lt(1e10)
  },
  
  isValidQuantity: (value: number | string): boolean => {
    const num = new Decimal(value || 0)
    return !num.isNaN() && num.gt(0) && num.mod(100).eq(0) // 股票数量必须是100的倍数
  }
}

/**
 * 格式化比率（例如夏普比率、盈亏比等）
 * 若数值无效则返回"-"，否则返回保留precision位小数的字符串
 * @param value 数值
 * @param precision 小数位数
 */
export function formatRatio(value: number | string, precision = 2): string {
  if (value === null || value === undefined || value === '') {
    return '-'
  }
  const num = new Decimal(value)
  if (num.isNaN()) {
    return '-'
  }
  return num.toFixed(precision)
}

/**
 * 根据涨跌幅返回价格颜色class
 * > 0 => 'price-up', < 0 => 'price-down', else 'price-neutral'
 * @param changePercent 变化百分比（-0.05 => -5%）
 */
export function getPriceChangeClass(changePercent: number | string): string {
  const num = new Decimal(changePercent || 0)
  if (num.gt(0)) return 'price-up'
  if (num.lt(0)) return 'price-down'
  return 'price-neutral'
}