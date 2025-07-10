/**
 * 工具函数测试
 */
import { describe, it, expect } from 'vitest'

// 简单的工具函数用于测试
function formatNumber(num: number): string {
  if (typeof num !== 'number' || isNaN(num) || !isFinite(num)) {
    return '--'
  }
  return num.toLocaleString()
}

function validateEmail(email: string): boolean {
  const emailRegex = /^[^\s@.]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function calculatePercentage(value: number, total: number): number {
  if (total === 0) return 0
  return Math.round((value / total) * 100 * 100) / 100
}

describe('工具函数测试', () => {
  describe('formatNumber', () => {
    it('应该正确格式化数字', () => {
      expect(formatNumber(1000)).toBe('1,000')
      expect(formatNumber(1234567)).toBe('1,234,567')
      expect(formatNumber(0)).toBe('0')
    })

    it('应该处理无效输入', () => {
      expect(formatNumber(NaN)).toBe('--')
      expect(formatNumber(Infinity)).toBe('--')
      expect(formatNumber(-Infinity)).toBe('--')
    })

    it('应该处理负数', () => {
      expect(formatNumber(-1000)).toBe('-1,000')
    })

    it('应该处理小数', () => {
      expect(formatNumber(1000.5)).toBe('1,000.5')
    })
  })

  describe('validateEmail', () => {
    it('应该验证有效邮箱', () => {
      expect(validateEmail('test@example.com')).toBe(true)
      expect(validateEmail('user.name@domain.co.uk')).toBe(true)
      expect(validateEmail('test+tag@example.org')).toBe(true)
    })

    it('应该拒绝无效邮箱', () => {
      expect(validateEmail('invalid-email')).toBe(false)
      expect(validateEmail('test@')).toBe(false)
      expect(validateEmail('@example.com')).toBe(false)
      expect(validateEmail('test..test@example.com')).toBe(false)
      expect(validateEmail('')).toBe(false)
    })
  })

  describe('calculatePercentage', () => {
    it('应该正确计算百分比', () => {
      expect(calculatePercentage(50, 100)).toBe(50)
      expect(calculatePercentage(25, 100)).toBe(25)
      expect(calculatePercentage(1, 3)).toBe(33.33)
    })

    it('应该处理零总数', () => {
      expect(calculatePercentage(10, 0)).toBe(0)
    })

    it('应该处理零值', () => {
      expect(calculatePercentage(0, 100)).toBe(0)
    })

    it('应该处理大于100%的情况', () => {
      expect(calculatePercentage(150, 100)).toBe(150)
    })
  })
})
