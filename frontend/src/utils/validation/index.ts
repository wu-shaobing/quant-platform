/**
 * 数据验证工具
 */

import type { 
  StockInfo, 
  OrderRequest, 
  StrategyConfig, 
  BacktestConfig 
} from '@/types'
import { validateNumber } from '@/utils/format/financial'

export interface ValidationResult {
  isValid: boolean
  errors: string[]
  warnings: string[]
}

export interface ValidationRule<T> {
  field: keyof T
  required?: boolean
  validator: (value: any) => boolean | string
  message?: string
}

/**
 * 通用验证器
 */
export class Validator<T> {
  private rules: ValidationRule<T>[] = []

  constructor(rules: ValidationRule<T>[] = []) {
    this.rules = rules
  }

  addRule(rule: ValidationRule<T>): this {
    this.rules.push(rule)
    return this
  }

  validate(data: Partial<T>): ValidationResult {
    const errors: string[] = []
    const warnings: string[] = []

    for (const rule of this.rules) {
      const value = data[rule.field]
      
      // 检查必填字段
      if (rule.required && (value === undefined || value === null || value === '')) {
        errors.push(rule.message || `${String(rule.field)} is required`)
        continue
      }

      // 如果字段为空且非必填，跳过验证
      if (value === undefined || value === null || value === '') {
        continue
      }

      // 执行验证
      const result = rule.validator(value)
      if (typeof result === 'string') {
        errors.push(result)
      } else if (!result) {
        errors.push(rule.message || `${String(rule.field)} is invalid`)
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings
    }
  }
}

/**
 * 股票代码验证
 */
export function validateStockCode(code: string): boolean {
  if (!code || typeof code !== 'string') return false
  
  // 去除空格和特殊字符
  const cleanCode = code.replace(/[^\d]/g, '')
  
  // 中国A股代码格式：6位数字
  if (cleanCode.length === 6 && /^\d{6}$/.test(cleanCode)) {
    // 上海交易所：60xxxx, 688xxx (科创板)
    // 深圳交易所：00xxxx, 002xxx (中小板), 30xxxx (创业板)
    const firstTwo = cleanCode.substring(0, 2)
    const firstThree = cleanCode.substring(0, 3)
    
    return ['60', '68', '00', '30'].includes(firstTwo) || 
           firstThree === '688' || 
           firstThree === '002'
  }
  
  return false
}

/**
 * 价格验证
 */
export function validatePrice(price: number | string): boolean {
  return validateNumber.isValidPrice(price)
}

/**
 * 数量验证（中国A股必须是100的倍数）
 */
export function validateQuantity(quantity: number | string): boolean {
  return validateNumber.isValidQuantity(quantity)
}

/**
 * 订单验证器
 */
export const orderValidator = new Validator<OrderRequest>([
  {
    field: 'symbol',
    required: true,
    validator: (value: string) => validateStockCode(value),
    message: '股票代码格式不正确'
  },
  {
    field: 'side',
    required: true,
    validator: (value: string) => ['buy', 'sell'].includes(value),
    message: '订单方向必须是buy或sell'
  },
  {
    field: 'type',
    required: true,
    validator: (value: string) => ['market', 'limit', 'stop', 'stop-limit'].includes(value),
    message: '订单类型不正确'
  },
  {
    field: 'quantity',
    required: true,
    validator: validateQuantity,
    message: '数量必须是大于0的100的倍数'
  },
  {
    field: 'price',
    required: false,
    validator: validatePrice,
    message: '价格必须是大于0的有效数值'
  },
  {
    field: 'stopPrice',
    required: false,
    validator: validatePrice,
    message: '止损价格必须是大于0的有效数值'
  }
])

/**
 * 策略配置验证器
 */
export const strategyValidator = new Validator<StrategyConfig>([
  {
    field: 'name',
    required: true,
    validator: (value: string) => value.length >= 2 && value.length <= 50,
    message: '策略名称长度必须在2-50个字符之间'
  },
  {
    field: 'description',
    required: false,
    validator: (value: string) => value.length <= 500,
    message: '策略描述不能超过500个字符'
  },
  {
    field: 'maxPosition',
    required: true,
    validator: (value: number) => validateNumber.isPositive(value) && value <= 1,
    message: '最大仓位必须在0-1之间'
  },
  {
    field: 'stopLoss',
    required: false,
    validator: (value: number) => value >= 0 && value <= 1,
    message: '止损比例必须在0-1之间'
  },
  {
    field: 'takeProfit',
    required: false,
    validator: (value: number) => value >= 0,
    message: '止盈比例必须大于等于0'
  }
])

/**
 * 回测配置验证器
 */
export const backtestValidator = new Validator<BacktestConfig>([
  {
    field: 'strategyId',
    required: true,
    validator: (value: string) => value.length > 0,
    message: '必须选择策略'
  },
  {
    field: 'startDate',
    required: true,
    validator: (value: string) => {
      const date = new Date(value)
      return !isNaN(date.getTime()) && date < new Date()
    },
    message: '开始日期必须是有效的过去日期'
  },
  {
    field: 'endDate',
    required: true,
    validator: (value: string) => {
      const date = new Date(value)
      return !isNaN(date.getTime()) && date < new Date()
    },
    message: '结束日期必须是有效的过去日期'
  },
  {
    field: 'initialCapital',
    required: true,
    validator: (value: number) => validateNumber.isPositive(value) && value >= 10000,
    message: '初始资金必须大于等于10000'
  },
  {
    field: 'commission',
    required: false,
    validator: (value: number) => value >= 0 && value <= 0.01,
    message: '手续费率必须在0-1%之间'
  }
])

/**
 * 表单验证装饰器
 */
export function validateForm<T>(validator: Validator<T>) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value

    descriptor.value = function (...args: any[]) {
      const data = args[0] as T
      const result = validator.validate(data)
      
      if (!result.isValid) {
        console.warn('Form validation failed:', result.errors)
        return { success: false, errors: result.errors }
      }

      return originalMethod.apply(this, args)
    }

    return descriptor
  }
}

/**
 * 数据清洗工具
 */
export class DataCleaner {
  /**
   * 清洗股票数据
   */
  static cleanStockData(data: any): StockInfo | null {
    try {
      if (!data || typeof data !== 'object') return null

      return {
        symbol: String(data.symbol || '').trim(),
        name: String(data.name || '').trim(),
        market: String(data.market || '').trim(),
        sector: data.sector ? String(data.sector).trim() : undefined,
        industry: data.industry ? String(data.industry).trim() : undefined,
        currentPrice: Number(data.currentPrice) || 0,
        change: Number(data.change) || 0,
        changePercent: Number(data.changePercent) || 0,
        volume: Number(data.volume) || 0,
        turnover: Number(data.turnover) || 0,
        marketCap: data.marketCap ? Number(data.marketCap) : undefined,
        pe: data.pe ? Number(data.pe) : undefined,
        pb: data.pb ? Number(data.pb) : undefined,
        high52w: data.high52w ? Number(data.high52w) : undefined,
        low52w: data.low52w ? Number(data.low52w) : undefined,
        isTrading: Boolean(data.isTrading)
      }
    } catch (error) {
      console.error('Error cleaning stock data:', error)
      return null
    }
  }

  /**
   * 清洗K线数据
   */
  static cleanKLineData(data: any[]): any[] {
    if (!Array.isArray(data)) return []

    return data
      .map(item => {
        if (!item || typeof item !== 'object') return null

        try {
          return {
            timestamp: new Date(item.timestamp).getTime(),
            open: Number(item.open) || 0,
            high: Number(item.high) || 0,
            low: Number(item.low) || 0,
            close: Number(item.close) || 0,
            volume: Number(item.volume) || 0,
            amount: item.amount ? Number(item.amount) : undefined
          }
        } catch (error) {
          console.error('Error cleaning K-line data item:', error)
          return null
        }
      })
      .filter(item => item !== null)
      .sort((a, b) => a.timestamp - b.timestamp)
  }

  /**
   * 清洗数字数据
   */
  static cleanNumber(value: any, defaultValue = 0): number {
    if (typeof value === 'number' && !isNaN(value)) return value
    if (typeof value === 'string') {
      const num = parseFloat(value)
      return isNaN(num) ? defaultValue : num
    }
    return defaultValue
  }

  /**
   * 清洗字符串数据
   */
  static cleanString(value: any, defaultValue = ''): string {
    if (typeof value === 'string') return value.trim()
    if (value === null || value === undefined) return defaultValue
    return String(value).trim()
  }

  /**
   * 清洗布尔数据
   */
  static cleanBoolean(value: any, defaultValue = false): boolean {
    if (typeof value === 'boolean') return value
    if (typeof value === 'string') {
      return ['true', '1', 'yes', 'on'].includes(value.toLowerCase())
    }
    if (typeof value === 'number') return value !== 0
    return defaultValue
  }
}

/**
 * 批量验证工具
 */
export class BatchValidator {
  private validators: Map<string, Validator<any>> = new Map()

  register<T>(key: string, validator: Validator<T>): this {
    this.validators.set(key, validator)
    return this
  }

  validate(key: string, data: any): ValidationResult {
    const validator = this.validators.get(key)
    if (!validator) {
      return {
        isValid: false,
        errors: [`Validator '${key}' not found`],
        warnings: []
      }
    }

    return validator.validate(data)
  }

  validateAll(data: Record<string, any>): Record<string, ValidationResult> {
    const results: Record<string, ValidationResult> = {}
    
    for (const [key, value] of Object.entries(data)) {
      if (this.validators.has(key)) {
        results[key] = this.validate(key, value)
      }
    }

    return results
  }
}

// 创建全局批量验证器实例
export const globalValidator = new BatchValidator()
  .register('order', orderValidator)
  .register('strategy', strategyValidator)
  .register('backtest', backtestValidator)

export default {
  Validator,
  validateStockCode,
  validatePrice,
  validateQuantity,
  orderValidator,
  strategyValidator,
  backtestValidator,
  validateForm,
  DataCleaner,
  BatchValidator,
  globalValidator
}