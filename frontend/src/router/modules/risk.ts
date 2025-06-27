import type { RouteRecordRaw } from 'vue-router'

const riskRoutes: RouteRecordRaw[] = [
  {
    path: '/risk',
    name: 'Risk',
    component: () => import('@/views/Risk/RiskMonitor.vue'),
    meta: {
      title: '风险监控',
      icon: 'Warning',
      requiresAuth: true
    }
  }
]

export default riskRoutes