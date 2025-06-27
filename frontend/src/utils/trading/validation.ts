/**
 * 交易验证工具函数
 */
import type { OrderFormData } from '@/types/trading'

export interface ValidationResult {
  isValid: boolean
  errors: string[]
  warnings: string[]
}

/**
 * 验证订单数据
 */
export function validateOrder(order: OrderFormData): ValidationResult {
  const errors: string[] = []
  const warnings: string[] = []

  // 基础字段验证
  if (!order.symbol) {
    errors.push('请选择股票代码')
  }

  if (!order.quantity || order.quantity <= 0) {
    errors.push('请输入有效的委托数量')
  }

  if (order.quantity && order.quantity % 100 !== 0) {
    errors.push('委托数量必须是100的整数倍')
  }

  if (['limit', 'stop', 'stop-profit'].includes(order.orderType)) {
    if (!order.price || order.price <= 0) {
      errors.push('请输入有效的委托价格')
    }
  }

  // 价格合理性检查
  if (order.price && order.currentPrice) {
    const deviation = Math.abs(order.price - order.currentPrice) / order.currentPrice
    if (deviation > 0.1) { // 偏离超过10%
      warnings.push('委托价格偏离市价较大，请确认')
    }
  }

  // 资金检查
  if (order.side === 'buy' && order.availableCash) {
    const totalAmount = (order.price || order.currentPrice || 0) * order.quantity
    const estimatedFee = totalAmount * 0.0003 // 简化手续费计算
    
    if (totalAmount + estimatedFee > order.availableCash) {
      errors.push('可用资金不足')
    }
  }

  // 持仓检查
  if (order.side === 'sell' && order.availableQuantity !== undefined) {
    if (order.quantity > order.availableQuantity) {
      errors.push('可卖数量不足')
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  }
}

/**
 * 验证股票代码格式
 */
export function validateStockSymbol(symbol: string): boolean {
  // A股代码格式验证
  const aSharePattern = /^(00|30|60|68)\d{4}$/
  // 港股代码格式验证  
  const hkPattern = /^\d{5}$/
  // 美股代码格式验证
  const usPattern = /^[A-Z]{1,5}$/

  return aSharePattern.test(symbol) || hkPattern.test(symbol) || usPattern.test(symbol)
}

/**
 * 验证交易时间
 */
export function validateTradingTime(): ValidationResult {
  const now = new Date()
  const hour = now.getHours()
  const minute = now.getMinutes()
  const day = now.getDay()

  const errors: string[] = []
  const warnings: string[] = []

  // 检查是否为交易日（简化版，实际需要考虑节假日）
  if (day === 0 || day === 6) {
    errors.push('当前为非交易日')
  }

  // 检查交易时间段
  const isAMSession = (hour === 9 && minute >= 30) || (hour >= 10 && hour < 11) || (hour === 11 && minute <= 30)
  const isPMSession = (hour === 13) || (hour >= 14 && hour < 15)

  if (!isAMSession && !isPMSession) {
    if (hour < 9 || (hour === 9 && minute < 30)) {
      warnings.push('距离开盘还有一段时间')
    } else if (hour >= 15) {
      warnings.push('当前为收盘时间')
    } else {
      warnings.push('当前为午休时间')
    }
  }

  return {
    isValid: errors.length === 0,
    errors,
    warnings
  }
}

/**
 * 计算交易手续费
 */
export function calculateTradingFee(
  amount: number,
  side: 'buy' | 'sell',
  market: 'A' | 'HK' | 'US' = 'A'
): number {
  let fee = 0

  switch (market) {
    case 'A':
      // A股手续费计算
      const commissionRate = 0.0003 // 万分之三
      const minCommission = 5 // 最低5元
      
      fee += Math.max(amount * commissionRate, minCommission) // 佣金
      
      if (side === 'sell') {
        fee += amount * 0.001 // 印花税（卖出时收取）
      }
      
      fee += amount * 0.00002 // 过户费
      break
      
    case 'HK':
      // 港股手续费计算
      fee += amount * 0.0025 // 佣金
      fee += Math.min(amount * 0.005, 100) // 交易费
      fee += Math.min(amount * 0.00015, 500) // 交收费
      fee += 2.5 // 交易系统使用费
      break
      
    case 'US':
      // 美股手续费计算（简化）
      fee = 0.005 // 每股0.005美元，最低1美元
      break
  }

  return Number(fee.toFixed(2))
}

/**
 * 风险等级评估
 */
export function assessRiskLevel(order: OrderFormData): 'low' | 'medium' | 'high' {
  let riskScore = 0

  // 金额占比风险
  if (order.availableCash && order.price && order.quantity) {
    const orderAmount = order.price * order.quantity
    const ratio = orderAmount / order.availableCash
    
    if (ratio > 0.8) riskScore += 3
    else if (ratio > 0.5) riskScore += 2
    else if (ratio > 0.3) riskScore += 1
  }

  // 价格偏离风险
  if (order.price && order.currentPrice) {
    const deviation = Math.abs(order.price - order.currentPrice) / order.currentPrice
    
    if (deviation > 0.1) riskScore += 3
    else if (deviation > 0.05) riskScore += 2
    else if (deviation > 0.02) riskScore += 1
  }

  // 订单类型风险
  if (order.orderType === 'market') {
    riskScore += 1
  } else if (['stop', 'stop-profit'].includes(order.orderType)) {
    riskScore += 2
  }

  // 数量风险
  if (order.quantity && order.quantity > 10000) {
    riskScore += 2
  } else if (order.quantity && order.quantity > 5000) {
    riskScore += 1
  }

  if (riskScore >= 6) return 'high'
  if (riskScore >= 3) return 'medium'
  return 'low'
}