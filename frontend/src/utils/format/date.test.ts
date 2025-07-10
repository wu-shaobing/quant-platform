import { describe, it, expect } from 'vitest'
import { formatDate, formatDuration, formatRelativeTime } from './date'

describe('Date Formatting Utilities', () => {
  describe('formatDate', () => {
    it('should format a date with the default format (YYYY-MM-DD)', () => {
      const date = new Date('2023-10-27T10:00:00.000Z')
      expect(formatDate(date)).toBe('2023-10-27')
    })

    it('should format a date with a custom format', () => {
      const date = new Date('2023-10-27T10:00:00.000Z')
      expect(formatDate(date, 'YYYY/MM/DD')).toBe('2023/10/27')
    })

    it('should handle string dates', () => {
      const dateString = '2023-01-15'
      expect(formatDate(dateString)).toBe('2023-01-15')
    })

    it('should handle number timestamps (milliseconds)', () => {
      const timestamp = new Date('2023-02-20').getTime()
      expect(formatDate(timestamp)).toBe('2023-02-20')
    })

    it('should return "--" for invalid or null dates', () => {
      expect(formatDate(null)).toBe('--')
      expect(formatDate(undefined)).toBe('--')
      expect(formatDate('')).toBe('--')
    })
  })

  describe('formatDuration', () => {
    it('should format seconds into a human-readable string', () => {
      expect(formatDuration(50)).toBe('50秒')
    })

    it('should format minutes and seconds', () => {
      expect(formatDuration(135)).toBe('2分钟15秒')
    })

    it('should format hours, minutes, and seconds', () => {
      expect(formatDuration(3723)).toBe('1小时2分钟3秒')
    })

    it('should format days, hours, minutes, and seconds', () => {
      expect(formatDuration(93784)).toBe('1天2小时3分钟4秒')
    })

    it('should return "0秒" for 0 or negative seconds', () => {
      expect(formatDuration(0)).toBe('0秒')
      expect(formatDuration(-100)).toBe('0秒')
    })

    it('should handle only days', () => {
      expect(formatDuration(2 * 24 * 60 * 60)).toBe('2天')
    })
  })

  describe('formatRelativeTime', () => {
    it('should handle null/undefined input', () => {
      expect(formatRelativeTime(null)).toBe('--')
      expect(formatRelativeTime(undefined)).toBe('--')
    })

    it('should return relative time string for valid dates', () => {
      const now = new Date()
      const result = formatRelativeTime(now)
      expect(typeof result).toBe('string')
      expect(result).not.toBe('--')
    })
  })
}) 