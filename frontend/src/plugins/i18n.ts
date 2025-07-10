/**
 * 国际化配置
 */
import type { App } from 'vue'
import { createI18n } from 'vue-i18n'

// 导入语言文件
const messages = {
  'zh-CN': {
    // 通用
    common: {
      confirm: '确认',
      cancel: '取消',
      save: '保存',
      delete: '删除',
      edit: '编辑',
      add: '添加',
      search: '搜索',
      loading: '加载中...',
      noData: '暂无数据',
      success: '操作成功',
      error: '操作失败',
      warning: '警告',
      info: '提示'
    },
    // 导航
    nav: {
      dashboard: '仪表盘',
      market: '行情中心',
      trading: '交易中心',
      strategy: '策略中心',
      backtest: '回测分析',
      portfolio: '投资组合',
      risk: '风险管理',
      settings: '设置'
    },
    // 交易
    trading: {
      buy: '买入',
      sell: '卖出',
      price: '价格',
      quantity: '数量',
      amount: '金额',
      order: '订单',
      position: '持仓',
      balance: '余额',
      profit: '盈亏'
    }
  },
  'en': {
    // Common
    common: {
      confirm: 'Confirm',
      cancel: 'Cancel',
      save: 'Save',
      delete: 'Delete',
      edit: 'Edit',
      add: 'Add',
      search: 'Search',
      loading: 'Loading...',
      noData: 'No Data',
      success: 'Success',
      error: 'Error',
      warning: 'Warning',
      info: 'Info'
    },
    // Navigation
    nav: {
      dashboard: 'Dashboard',
      market: 'Market',
      trading: 'Trading',
      strategy: 'Strategy',
      backtest: 'Backtest',
      portfolio: 'Portfolio',
      risk: 'Risk',
      settings: 'Settings'
    },
    // Trading
    trading: {
      buy: 'Buy',
      sell: 'Sell',
      price: 'Price',
      quantity: 'Quantity',
      amount: 'Amount',
      order: 'Order',
      position: 'Position',
      balance: 'Balance',
      profit: 'P&L'
    }
  }
}

const i18n = createI18n({
  legacy: false,
  locale: 'zh-CN',
  fallbackLocale: 'en',
  messages
})

export const setupI18n = (app: App) => {
  app.use(i18n)
}

export { i18n }