import type { RouteRecordRaw } from 'vue-router'

const tradingRoutes: RouteRecordRaw[] = [
  {
    path: '/trading',
    redirect: '/trading/terminal'
  },
  {
    path: '/trading/terminal',
    name: 'TradingTerminal',
    component: () => import('@/views/Trading/TradingTerminal.vue'),
    meta: {
      title: '交易终端',
      requiresAuth: true
    }
  },
  {
    path: '/trading/orders',
    name: 'OrderManagement',
    component: () => import('@/views/Trading/OrderManagement.vue'),
    meta: {
      title: '订单管理',
      requiresAuth: true
    }
  },
  {
    path: '/trading/positions',
    name: 'PositionManagement',
    component: () => import('@/views/Trading/PositionManagement.vue'),
    meta: {
      title: '持仓管理',
      requiresAuth: true
    }
  }
]

export default tradingRoutes 