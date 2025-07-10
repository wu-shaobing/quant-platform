import type { RouteRecordRaw } from 'vue-router'

const dashboardRoutes: RouteRecordRaw[] = [
  {
    path: '',
    name: 'home',
    component: () => import('@/views/Dashboard/DashboardView.vue'),
    meta: {
      title: '仪表盘'
    }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/Dashboard/DashboardView.vue'),
    meta: {
      title: '仪表盘'
    }
  }
]

export default dashboardRoutes 