/**
 * 数据导出工具
 * 支持多种格式的数据导出功能
 */

import { ElMessage } from 'element-plus'
import { formatDate } from '@/utils/format/date'

export interface ExportOptions {
  filename?: string
  format?: 'excel' | 'csv' | 'json' | 'pdf'
  sheetName?: string
  headers?: string[]
  dateFormat?: string
  timezone?: string
}

export interface TableColumn {
  key: string
  title: string
  width?: number
  type?: 'string' | 'number' | 'date' | 'currency' | 'percent'
  formatter?: (value: any) => string
}

/**
 * 导出为Excel格式
 */
export async function exportToExcel<T = any>(
  data: T[],
  columns: TableColumn[],
  options: ExportOptions = {}
): Promise<void> {
  try {
    // 动态导入xlsx库以减少打包体积
    const XLSX = await import('xlsx')
    
    const {
      filename = 'export',
      sheetName = 'Sheet1',
      dateFormat = 'YYYY-MM-DD HH:mm:ss'
    } = options

    // 格式化数据
    const formattedData = data.map(row => {
      const formattedRow: any = {}
      columns.forEach(col => {
        const value = (row as any)[col.key]
        formattedRow[col.title] = formatCellValue(value, col, dateFormat)
      })
      return formattedRow
    })

    // 创建工作簿
    const workbook = XLSX.utils.book_new()
    const worksheet = XLSX.utils.json_to_sheet(formattedData)

    // 设置列宽
    const colWidths = columns.map(col => ({
      wch: col.width || 15
    }))
    worksheet['!cols'] = colWidths

    // 添加工作表
    XLSX.utils.book_append_sheet(workbook, worksheet, sheetName)

    // 导出文件
    XLSX.writeFile(workbook, `${filename}.xlsx`)
    
    ElMessage.success('Excel文件导出成功')
  } catch (error) {
    console.error('Excel导出失败:', error)
    ElMessage.error('Excel导出失败')
    throw error
  }
}

/**
 * 导出为CSV格式
 */
export function exportToCSV<T = any>(
  data: T[],
  columns: TableColumn[],
  options: ExportOptions = {}
): void {
  try {
    const {
      filename = 'export',
      dateFormat = 'YYYY-MM-DD HH:mm:ss'
    } = options

    // 创建CSV内容
    const headers = columns.map(col => col.title).join(',')
    const rows = data.map(row => {
      return columns.map(col => {
        const value = (row as any)[col.key]
        const formattedValue = formatCellValue(value, col, dateFormat)
        // CSV需要处理特殊字符
        return `"${String(formattedValue).replace(/"/g, '""')}"`
      }).join(',')
    })

    const csvContent = [headers, ...rows].join('\n')
    
    // 添加BOM以支持中文
    const BOM = '\uFEFF'
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })

    downloadBlob(blob, `${filename}.csv`)
    
    ElMessage.success('CSV文件导出成功')
  } catch (error) {
    console.error('CSV导出失败:', error)
    ElMessage.error('CSV导出失败')
    throw error
  }
}

/**
 * 导出为JSON格式
 */
export function exportToJSON<T = any>(
  data: T[],
  options: ExportOptions = {}
): void {
  try {
    const { filename = 'export' } = options

    const jsonContent = JSON.stringify(data, null, 2)
    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' })

    downloadBlob(blob, `${filename}.json`)
    
    ElMessage.success('JSON文件导出成功')
  } catch (error) {
    console.error('JSON导出失败:', error)
    ElMessage.error('JSON导出失败')
    throw error
  }
}

/**
 * 导出交易记录
 */
export async function exportTradingRecords(
  records: any[],
  options: ExportOptions = {}
): Promise<void> {
  const columns: TableColumn[] = [
    { key: 'timestamp', title: '时间', type: 'date', width: 20 },
    { key: 'symbol', title: '股票代码', width: 12 },
    { key: 'symbolName', title: '股票名称', width: 15 },
    { key: 'side', title: '方向', width: 8, formatter: (value) => value === 'buy' ? '买入' : '卖出' },
    { key: 'orderType', title: '订单类型', width: 12, formatter: formatOrderType },
    { key: 'quantity', title: '数量', type: 'number', width: 12 },
    { key: 'price', title: '价格', type: 'currency', width: 12 },
    { key: 'amount', title: '金额', type: 'currency', width: 15 },
    { key: 'fee', title: '手续费', type: 'currency', width: 12 },
    { key: 'status', title: '状态', width: 10, formatter: formatOrderStatus },
    { key: 'orderId', title: '订单号', width: 20 }
  ]

  const filename = options.filename || `交易记录_${formatDate(new Date(), 'YYYYMMDD_HHmmss')}`
  
  await exportToExcel(records, columns, { ...options, filename })
}

/**
 * 导出持仓记录
 */
export async function exportPositions(
  positions: any[],
  options: ExportOptions = {}
): Promise<void> {
  const columns: TableColumn[] = [
    { key: 'symbol', title: '股票代码', width: 12 },
    { key: 'symbolName', title: '股票名称', width: 15 },
    { key: 'quantity', title: '持仓数量', type: 'number', width: 12 },
    { key: 'availableQuantity', title: '可用数量', type: 'number', width: 12 },
    { key: 'avgPrice', title: '成本价', type: 'currency', width: 12 },
    { key: 'currentPrice', title: '现价', type: 'currency', width: 12 },
    { key: 'marketValue', title: '市值', type: 'currency', width: 15 },
    { key: 'unrealizedPnl', title: '浮动盈亏', type: 'currency', width: 15 },
    { key: 'unrealizedPnlPercent', title: '盈亏比例', type: 'percent', width: 12 },
    { key: 'updateTime', title: '更新时间', type: 'date', width: 20 }
  ]

  const filename = options.filename || `持仓记录_${formatDate(new Date(), 'YYYYMMDD_HHmmss')}`
  
  await exportToExcel(positions, columns, { ...options, filename })
}

/**
 * 导出策略回测报告
 */
export async function exportBacktestReport(
  report: any,
  options: ExportOptions = {}
): Promise<void> {
  try {
    const XLSX = await import('xlsx')
    
    const { filename = `回测报告_${formatDate(new Date(), 'YYYYMMDD_HHmmss')}` } = options

    const workbook = XLSX.utils.book_new()

    // 基本信息表
    const basicInfo = [
      ['策略名称', report.strategyName],
      ['回测期间', `${formatDate(report.startDate)} ~ ${formatDate(report.endDate)}`],
      ['初始资金', formatCurrency(report.initialCapital)],
      ['最终资金', formatCurrency(report.finalCapital)],
      ['总收益', formatCurrency(report.totalReturn)],
      ['总收益率', formatPercent(report.totalReturnRate)],
      ['年化收益率', formatPercent(report.annualizedReturn)],
      ['最大回撤', formatPercent(report.maxDrawdown)],
      ['夏普比率', report.sharpeRatio?.toFixed(4) || '-'],
      ['胜率', formatPercent(report.winRate)],
      ['交易次数', report.totalTrades],
      ['盈利交易', report.profitableTrades],
      ['亏损交易', report.losingTrades]
    ]
    
    const basicInfoSheet = XLSX.utils.aoa_to_sheet(basicInfo)
    XLSX.utils.book_append_sheet(workbook, basicInfoSheet, '基本信息')

    // 交易记录表
    if (report.trades && report.trades.length > 0) {
      const tradeColumns: TableColumn[] = [
        { key: 'timestamp', title: '时间', type: 'date' },
        { key: 'symbol', title: '股票代码' },
        { key: 'side', title: '方向', formatter: (value) => value === 'buy' ? '买入' : '卖出' },
        { key: 'quantity', title: '数量', type: 'number' },
        { key: 'price', title: '价格', type: 'currency' },
        { key: 'amount', title: '金额', type: 'currency' },
        { key: 'pnl', title: '盈亏', type: 'currency' },
        { key: 'pnlPercent', title: '盈亏率', type: 'percent' }
      ]

      const formattedTrades = report.trades.map((trade: any) => {
        const formattedTrade: any = {}
        tradeColumns.forEach(col => {
          const value = trade[col.key]
          formattedTrade[col.title] = formatCellValue(value, col)
        })
        return formattedTrade
      })

      const tradesSheet = XLSX.utils.json_to_sheet(formattedTrades)
      XLSX.utils.book_append_sheet(workbook, tradesSheet, '交易记录')
    }

    // 净值曲线表
    if (report.equityCurve && report.equityCurve.length > 0) {
      const equityData = report.equityCurve.map((point: any) => ({
        '日期': formatDate(point.date),
        '净值': formatCurrency(point.equity),
        '收益率': formatPercent(point.returnRate),
        '累计收益率': formatPercent(point.cumulativeReturn),
        '回撤': formatPercent(point.drawdown)
      }))

      const equitySheet = XLSX.utils.json_to_sheet(equityData)
      XLSX.utils.book_append_sheet(workbook, equitySheet, '净值曲线')
    }

    // 月度收益表
    if (report.monthlyReturns && report.monthlyReturns.length > 0) {
      const monthlyData = report.monthlyReturns.map((month: any) => ({
        '年月': month.period,
        '月收益率': formatPercent(month.return),
        '累计收益率': formatPercent(month.cumulativeReturn),
        '交易次数': month.trades
      }))

      const monthlySheet = XLSX.utils.json_to_sheet(monthlyData)
      XLSX.utils.book_append_sheet(workbook, monthlySheet, '月度收益')
    }

    // 导出文件
    XLSX.writeFile(workbook, `${filename}.xlsx`)
    
    ElMessage.success('回测报告导出成功')
  } catch (error) {
    console.error('回测报告导出失败:', error)
    ElMessage.error('回测报告导出失败')
    throw error
  }
}

/**
 * 导出K线数据
 */
export async function exportKLineData(
  klineData: any[],
  symbol: string,
  period: string,
  options: ExportOptions = {}
): Promise<void> {
  const columns: TableColumn[] = [
    { key: 'timestamp', title: '时间', type: 'date', width: 20 },
    { key: 'open', title: '开盘价', type: 'currency', width: 12 },
    { key: 'high', title: '最高价', type: 'currency', width: 12 },
    { key: 'low', title: '最低价', type: 'currency', width: 12 },
    { key: 'close', title: '收盘价', type: 'currency', width: 12 },
    { key: 'volume', title: '成交量', type: 'number', width: 15 },
    { key: 'amount', title: '成交额', type: 'currency', width: 15 },
    { key: 'change', title: '涨跌额', type: 'currency', width: 12 },
    { key: 'changePercent', title: '涨跌幅', type: 'percent', width: 12 }
  ]

  const filename = options.filename || `${symbol}_${period}_K线数据_${formatDate(new Date(), 'YYYYMMDD')}`
  
  await exportToExcel(klineData, columns, { ...options, filename })
}

/**
 * 批量导出功能
 */
export async function batchExport(
  exports: Array<{
    name: string
    data: any[]
    columns?: TableColumn[]
    type: 'trading' | 'positions' | 'kline' | 'custom'
    options?: ExportOptions
  }>
): Promise<void> {
  try {
    const XLSX = await import('xlsx')
    
    const workbook = XLSX.utils.book_new()
    
    for (const exportItem of exports) {
      let formattedData: any[]
      
      if (exportItem.type === 'custom' && exportItem.columns) {
        formattedData = exportItem.data.map(row => {
          const formattedRow: any = {}
          exportItem.columns!.forEach(col => {
            const value = (row as any)[col.key]
            formattedRow[col.title] = formatCellValue(value, col)
          })
          return formattedRow
        })
      } else {
        formattedData = exportItem.data
      }
      
      const worksheet = XLSX.utils.json_to_sheet(formattedData)
      XLSX.utils.book_append_sheet(workbook, worksheet, exportItem.name)
    }
    
    const filename = `批量导出_${formatDate(new Date(), 'YYYYMMDD_HHmmss')}`
    XLSX.writeFile(workbook, `${filename}.xlsx`)
    
    ElMessage.success('批量导出成功')
  } catch (error) {
    console.error('批量导出失败:', error)
    ElMessage.error('批量导出失败')
    throw error
  }
}

// 辅助函数
function formatCellValue(value: any, column: TableColumn, dateFormat = 'YYYY-MM-DD HH:mm:ss'): string {
  if (value === null || value === undefined) {
    return ''
  }

  if (column.formatter) {
    return column.formatter(value)
  }

  switch (column.type) {
    case 'date':
      return formatDate(value, dateFormat)
    case 'currency':
      return formatCurrency(value)
    case 'percent':
      return formatPercent(value)
    case 'number':
      return typeof value === 'number' ? value.toLocaleString() : String(value)
    default:
      return String(value)
  }
}

function formatDate(date: any, format = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!date) return ''
  
  const d = new Date(date)
  if (isNaN(d.getTime())) return String(date)
  
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')
  const seconds = String(d.getSeconds()).padStart(2, '0')
  
  return format
    .replace('YYYY', year.toString())
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
}

function formatCurrency(value: any): string {
  if (typeof value !== 'number') return String(value)
  return value.toLocaleString('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2
  })
}

function formatPercent(value: any): string {
  if (typeof value !== 'number') return String(value)
  return `${(value * 100).toFixed(2)}%`
}

function formatOrderType(value: string): string {
  const typeMap: Record<string, string> = {
    'limit': '限价单',
    'market': '市价单',
    'stop': '止损单',
    'stop-profit': '止盈单'
  }
  return typeMap[value] || value
}

function formatOrderStatus(value: string): string {
  const statusMap: Record<string, string> = {
    'pending': '待成交',
    'partial': '部分成交',
    'filled': '已成交',
    'cancelled': '已撤销',
    'rejected': '已拒绝'
  }
  return statusMap[value] || value
}

function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  window.URL.revokeObjectURL(url)
}

/**
 * 检查浏览器是否支持文件下载
 */
export function isDownloadSupported(): boolean {
  return !!(window.URL && window.URL.createObjectURL && document.createElement)
}

/**
 * 获取文件大小限制
 */
export function getFileSizeLimit(): number {
  // 返回推荐的最大文件大小（字节）
  return 50 * 1024 * 1024 // 50MB
}

/**
 * 估算导出文件大小
 */
export function estimateFileSize(data: any[], format: 'excel' | 'csv' | 'json'): number {
  const jsonSize = JSON.stringify(data).length
  
  switch (format) {
    case 'excel':
      return jsonSize * 1.5 // Excel文件通常比JSON大50%
    case 'csv':
      return jsonSize * 0.8 // CSV文件通常比JSON小20%
    case 'json':
      return jsonSize
    default:
      return jsonSize
  }
} 