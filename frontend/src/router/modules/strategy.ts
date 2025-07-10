import type { RouteRecordRaw } from 'vue-router'

const strategyRoutes: RouteRecordRaw[] = [
  {
    path: '/strategy',
    redirect: '/strategy/hub'
  },
  {
    path: '/strategy/hub',
    name: 'strategy-hub',
    component: () => import('@/views/Strategy/StrategyHub.vue'),
    meta: {
      title: '策略中心'
    }
  },
  {
    path: '/strategy/develop',
    name: 'strategy-develop',
    component: () => import('@/views/Strategy/StrategyDevelop.vue'),
    meta: {
      title: '策略开发'
    }
  },
  {
    path: '/strategy/monitor',
    name: 'strategy-monitor',
    component: () => import('@/views/Strategy/StrategyMonitor.vue'),
    meta: {
      title: '策略监控'
    }
  }
]

export default strategyRoutes 