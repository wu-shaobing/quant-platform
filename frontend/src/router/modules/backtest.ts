import type { RouteRecordRaw } from 'vue-router'

const backtestRoutes: RouteRecordRaw[] = [
  {
    path: '/backtest',
    name: 'backtest-view',
    component: () => import('@/views/Backtest/BacktestView.vue'),
    meta: {
      title: '回测分析'
    }
  },
  {
    path: '/backtest/create',
    name: 'create-backtest',
    component: () => import('@/views/Backtest/CreateBacktest.vue'),
    meta: {
      title: '创建回测'
    }
  },
  {
    path: '/backtest/history',
    name: 'backtest-history',
    component: () => import('@/views/Backtest/BacktestHistory.vue'),
    meta: {
      title: '回测历史'
    }
  }
]

export default backtestRoutes 