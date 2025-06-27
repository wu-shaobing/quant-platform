import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'
import durationPlugin from 'dayjs/plugin/duration'
import timezone from 'dayjs/plugin/timezone'
import utcPlugin from 'dayjs/plugin/utc'
import customParseFormat from 'dayjs/plugin/customParseFormat'
import weekOfYear from 'dayjs/plugin/weekOfYear'
import quarterOfYear from 'dayjs/plugin/quarterOfYear'

// 加载插件
dayjs.extend(relativeTime)
dayjs.extend(durationPlugin)
dayjs.extend(timezone)
dayjs.extend(utcPlugin)
dayjs.extend(customParseFormat)
dayjs.extend(weekOfYear)
dayjs.extend(quarterOfYear)

// 设置中文语言
dayjs.locale('zh-cn')

/**
 * 日期格式化选项
 */
export interface DateFormatOptions {
  format?: string
  locale?: string
  timezone?: string
  relative?: boolean
  showTime?: boolean
}

/**
 * 默认格式化选项
 */
const DEFAULT_OPTIONS: Required<DateFormatOptions> = {
  format: 'YYYY-MM-DD',
  locale: 'zh-cn',
  timezone: 'Asia/Shanghai',
  relative: false,
  showTime: false
}

/**
 * 常用日期格式常量
 */
export const DATE_FORMATS = {
  // 日期格式
  DATE: 'YYYY-MM-DD',
  DATE_CN: 'YYYY年MM月DD日',
  DATE_SHORT: 'MM-DD',
  DATE_SHORT_CN: 'MM月DD日',
  
  // 时间格式
  TIME: 'HH:mm:ss',
  TIME_SHORT: 'HH:mm',
  TIME_12: 'hh:mm:ss A',
  TIME_12_SHORT: 'hh:mm A',
  
  // 日期时间格式
  DATETIME: 'YYYY-MM-DD HH:mm:ss',
  DATETIME_CN: 'YYYY年MM月DD日 HH:mm:ss',
  DATETIME_SHORT: 'MM-DD HH:mm',
  DATETIME_MINUTE: 'YYYY-MM-DD HH:mm',
  
  // ISO格式
  ISO: 'YYYY-MM-DDTHH:mm:ss.SSSZ',
  ISO_DATE: 'YYYY-MM-DD',
  
  // 特殊格式
  TIMESTAMP: 'x', // Unix时间戳(毫秒)
  TIMESTAMP_SECOND: 'X', // Unix时间戳(秒)
  
  // 交易相关格式
  TRADING_DATE: 'YYYY-MM-DD',
  TRADING_TIME: 'HH:mm:ss',
  TRADING_DATETIME: 'YYYY-MM-DD HH:mm:ss',
  MARKET_TIME: 'HH:mm'
} as const

/**
 * 基础日期格式化函数
 * @param date 日期值
 * @param format 格式字符串
 * @param options 格式化选项
 * @returns 格式化后的日期字符串
 */
export function formatDate(
  date: dayjs.ConfigType,
  format: string = DATE_FORMATS.DATE,
  options: Partial<DateFormatOptions> = {}
): string {
  const opts = { ...DEFAULT_OPTIONS, ...options }
  
  if (!date) return '--'
  
  try {
    let dayjsObj = dayjs(date)
    
    // 设置时区
    if (opts.timezone) {
      dayjsObj = dayjsObj.tz(opts.timezone)
    }
    
    // 相对时间
    if (opts.relative) {
      return dayjsObj.fromNow()
    }
    
    return dayjsObj.format(format)
  } catch (error) {
    console.error('日期格式化失败:', error)
    return '--'
  }
}

/**
 * 格式化为标准日期
 * @param date 日期值
 * @returns YYYY-MM-DD格式的日期字符串
 */
export function formatDateOnly(date: dayjs.ConfigType): string {
  return formatDate(date, DATE_FORMATS.DATE)
}

/**
 * 格式化为中文日期
 * @param date 日期值
 * @returns YYYY年MM月DD日格式的日期字符串
 */
export function formatDateCN(date: dayjs.ConfigType): string {
  return formatDate(date, DATE_FORMATS.DATE_CN)
}

/**
 * 格式化为时间
 * @param date 日期值
 * @param showSeconds 是否显示秒
 * @returns 时间字符串
 */
export function formatTime(date: dayjs.ConfigType, showSeconds = true): string {
  const format = showSeconds ? DATE_FORMATS.TIME : DATE_FORMATS.TIME_SHORT
  return formatDate(date, format)
}

/**
 * 格式化为日期时间
 * @param date 日期值
 * @param showSeconds 是否显示秒
 * @returns 日期时间字符串
 */
export function formatDateTime(date: dayjs.ConfigType, showSeconds = true): string {
  const format = showSeconds ? DATE_FORMATS.DATETIME : DATE_FORMATS.DATETIME_MINUTE
  return formatDate(date, format)
}

/**
 * 格式化为相对时间
 * @param date 日期值
 * @returns 相对时间字符串 (如: 2小时前)
 */
export function formatRelativeTime(date: dayjs.ConfigType): string {
  if (!date) return '--'
  
  try {
    return dayjs(date).fromNow()
  } catch (error) {
    console.error('相对时间格式化失败:', error)
    return '--'
  }
}

/**
 * 格式化为智能时间 (根据时间差自动选择格式)
 * @param date 日期值
 * @returns 智能格式化的时间字符串
 */
export function formatSmartTime(date: dayjs.ConfigType): string {
  if (!date) return '--'
  
  try {
    const now = dayjs()
    const target = dayjs(date)
    const diff = now.diff(target, 'minute')
    
    if (diff < 1) {
      return '刚刚'
    } else if (diff < 60) {
      return `${diff}分钟前`
    } else if (diff < 1440) { // 24小时
      return `${Math.floor(diff / 60)}小时前`
    } else if (diff < 2880) { // 48小时
      return '昨天 ' + target.format('HH:mm')
    } else if (diff < 4320) { // 72小时
      return '前天 ' + target.format('HH:mm')
    } else if (target.year() === now.year()) {
      return target.format('MM-DD HH:mm')
    } else {
      return target.format('YYYY-MM-DD')
    }
  } catch (error) {
    console.error('智能时间格式化失败:', error)
    return '--'
  }
}

/**
 * 格式化交易时间 (交易日专用)
 * @param date 日期值
 * @returns 交易时间字符串
 */
export function formatTradingTime(date: dayjs.ConfigType): string {
  if (!date) return '--'
  
  try {
    const target = dayjs(date)
    const now = dayjs()
    
    // 如果是今天，只显示时间
    if (target.isSame(now, 'day')) {
      return target.format('HH:mm:ss')
    }
    
    // 如果是本年，显示月日和时间
    if (target.isSame(now, 'year')) {
      return target.format('MM-DD HH:mm:ss')
    }
    
    // 否则显示完整日期时间
    return target.format('YYYY-MM-DD HH:mm:ss')
  } catch (error) {
    console.error('交易时间格式化失败:', error)
    return '--'
  }
}

/**
 * 格式化市场时间 (只显示时分)
 * @param date 日期值
 * @returns 市场时间字符串 (HH:mm)
 */
export function formatMarketTime(date: dayjs.ConfigType): string {
  return formatDate(date, DATE_FORMATS.MARKET_TIME)
}

/**
 * 格式化时间段
 * @param startDate 开始时间
 * @param endDate 结束时间
 * @param format 格式
 * @returns 时间段字符串
 */
export function formatTimeRange(
  startDate: dayjs.ConfigType,
  endDate: dayjs.ConfigType,
  format: string = DATE_FORMATS.DATETIME_MINUTE
): string {
  if (!startDate || !endDate) return '--'
  
  try {
    const start = dayjs(startDate)
    const end = dayjs(endDate)
    
    // 如果是同一天，只显示一次日期
    if (start.isSame(end, 'day')) {
      return `${start.format('YYYY-MM-DD')} ${start.format('HH:mm')} - ${end.format('HH:mm')}`
    }
    
    return `${start.format(format)} - ${end.format(format)}`
  } catch (error) {
    console.error('时间段格式化失败:', error)
    return '--'
  }
}

/**
 * 计算时间差
 * @param startDate 开始时间
 * @param endDate 结束时间 (默认为当前时间)
 * @param unit 单位
 * @returns 时间差
 */
export function getTimeDiff(
  startDate: dayjs.ConfigType,
  endDate: dayjs.ConfigType = dayjs(),
  unit: dayjs.ManipulateType = 'millisecond'
): number {
  if (!startDate) return 0
  
  try {
    return dayjs(endDate).diff(dayjs(startDate), unit)
  } catch (error) {
    console.error('时间差计算失败:', error)
    return 0
  }
}

/**
 * 格式化持续时间
 * @param duration 持续时间 (毫秒)
 * @returns 格式化的持续时间字符串
 */
export function formatDuration(duration: number): string {
  if (duration < 0) return '--'
  
  try {
    const d = dayjs.duration(duration)
    
    if (d.asDays() >= 1) {
      return `${Math.floor(d.asDays())}天${d.hours()}小时${d.minutes()}分钟`
    } else if (d.asHours() >= 1) {
      return `${d.hours()}小时${d.minutes()}分钟`
    } else if (d.asMinutes() >= 1) {
      return `${d.minutes()}分钟${d.seconds()}秒`
    } else {
      return `${d.seconds()}秒`
    }
  } catch (error) {
    console.error('持续时间格式化失败:', error)
    return '--'
  }
}

/**
 * 检查是否为工作日
 * @param date 日期
 * @returns 是否为工作日
 */
export function isWorkday(date: dayjs.ConfigType): boolean {
  if (!date) return false
  
  try {
    const dayOfWeek = dayjs(date).day()
    return dayOfWeek >= 1 && dayOfWeek <= 5 // 周一到周五
  } catch (error) {
    console.error('工作日检查失败:', error)
    return false
  }
}

/**
 * 检查是否为交易时间
 * @param date 日期时间
 * @param sessions 交易时段 (格式: [['09:30', '11:30'], ['13:00', '15:00']])
 * @returns 是否为交易时间
 */
export function isTradingTime(
  date: dayjs.ConfigType,
  sessions: string[][] = [['09:30', '11:30'], ['13:00', '15:00']]
): boolean {
  if (!date) return false
  
  try {
    const target = dayjs(date)
    
    // 检查是否为工作日
    if (!isWorkday(target)) return false
    
    const timeStr = target.format('HH:mm')
    
    // 检查是否在任一交易时段内
    return sessions.some(([start, end]) => {
      return timeStr >= start && timeStr <= end
    })
  } catch (error) {
    console.error('交易时间检查失败:', error)
    return false
  }
}

/**
 * 获取下一个交易日
 * @param date 基准日期
 * @param holidays 节假日列表 (YYYY-MM-DD格式)
 * @returns 下一个交易日
 */
export function getNextTradingDay(
  date: dayjs.ConfigType,
  holidays: string[] = []
): dayjs.Dayjs {
  let nextDay = dayjs(date).add(1, 'day')
  
  while (!isWorkday(nextDay) || holidays.includes(nextDay.format('YYYY-MM-DD'))) {
    nextDay = nextDay.add(1, 'day')
  }
  
  return nextDay
}

/**
 * 获取上一个交易日
 * @param date 基准日期
 * @param holidays 节假日列表 (YYYY-MM-DD格式)
 * @returns 上一个交易日
 */
export function getPrevTradingDay(
  date: dayjs.ConfigType,
  holidays: string[] = []
): dayjs.Dayjs {
  let prevDay = dayjs(date).subtract(1, 'day')
  
  while (!isWorkday(prevDay) || holidays.includes(prevDay.format('YYYY-MM-DD'))) {
    prevDay = prevDay.subtract(1, 'day')
  }
  
  return prevDay
}

/**
 * 获取本周的交易日
 * @param date 基准日期
 * @param holidays 节假日列表
 * @returns 本周的交易日数组
 */
export function getWeekTradingDays(
  date: dayjs.ConfigType,
  holidays: string[] = []
): dayjs.Dayjs[] {
  const startOfWeek = dayjs(date).startOf('week').add(1, 'day') // 从周一开始
  const tradingDays: dayjs.Dayjs[] = []
  
  for (let i = 0; i < 5; i++) { // 周一到周五
    const day = startOfWeek.add(i, 'day')
    if (!holidays.includes(day.format('YYYY-MM-DD'))) {
      tradingDays.push(day)
    }
  }
  
  return tradingDays
}

/**
 * 获取本月的交易日
 * @param date 基准日期
 * @param holidays 节假日列表
 * @returns 本月的交易日数组
 */
export function getMonthTradingDays(
  date: dayjs.ConfigType,
  holidays: string[] = []
): dayjs.Dayjs[] {
  const startOfMonth = dayjs(date).startOf('month')
  const endOfMonth = dayjs(date).endOf('month')
  const tradingDays: dayjs.Dayjs[] = []
  
  let current = startOfMonth
  while (current.isBefore(endOfMonth) || current.isSame(endOfMonth, 'day')) {
    if (isWorkday(current) && !holidays.includes(current.format('YYYY-MM-DD'))) {
      tradingDays.push(current)
    }
    current = current.add(1, 'day')
  }
  
  return tradingDays
}

/**
 * 解析日期字符串
 * @param dateString 日期字符串
 * @param format 格式
 * @returns dayjs对象
 */
export function parseDate(
  dateString: string,
  format?: string
): dayjs.Dayjs | null {
  if (!dateString) return null
  
  try {
    if (format) {
      return dayjs(dateString, format)
    } else {
      return dayjs(dateString)
    }
  } catch (error) {
    console.error('日期解析失败:', error)
    return null
  }
}

/**
 * 验证日期格式
 * @param dateString 日期字符串
 * @param format 期望的格式
 * @returns 是否有效
 */
export function isValidDate(
  dateString: string,
  format?: string
): boolean {
  const parsed = parseDate(dateString, format)
  return parsed !== null && parsed.isValid()
}

/**
 * 获取时区偏移量
 * @param timezone 时区
 * @returns 偏移量 (分钟)
 */
export function getTimezoneOffset(timezone: string = 'Asia/Shanghai'): number {
  try {
    return dayjs().tz(timezone).utcOffset()
  } catch (error) {
    console.error('获取时区偏移量失败:', error)
    return 0
  }
}

/**
 * 转换时区
 * @param date 日期
 * @param fromTimezone 源时区
 * @param toTimezone 目标时区
 * @returns 转换后的日期
 */
export function convertTimezone(
  date: dayjs.ConfigType,
  fromTimezone: string,
  toTimezone: string
): dayjs.Dayjs | null {
  if (!date) return null
  
  try {
    return dayjs(date).tz(fromTimezone).tz(toTimezone)
  } catch (error) {
    console.error('时区转换失败:', error)
    return null
  }
}

/**
 * 获取当前时间戳
 * @param unit 单位 ('millisecond' | 'second')
 * @returns 时间戳
 */
export function getCurrentTimestamp(unit: 'millisecond' | 'second' = 'millisecond'): number {
  return unit === 'second' ? dayjs().unix() : dayjs().valueOf()
}

/**
 * 时间戳转日期
 * @param timestamp 时间戳
 * @param unit 单位
 * @returns dayjs对象
 */
export function timestampToDate(
  timestamp: number,
  unit: 'millisecond' | 'second' = 'millisecond'
): dayjs.Dayjs {
  return unit === 'second' ? dayjs.unix(timestamp) : dayjs(timestamp)
}

// 导出dayjs实例，方便直接使用
export { dayjs }

// 导出常用的dayjs方法
export const {
  unix,
  utc,
  tz,
  duration,
  isDayjs,
  locale
} = dayjs 