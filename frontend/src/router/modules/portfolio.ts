import type { RouteRecordRaw } from 'vue-router'

const portfolioRoutes: RouteRecordRaw[] = [
  {
    path: '/portfolio',
    name: 'Portfolio',
    component: () => import('@/views/Portfolio/PortfolioView.vue'),
    meta: {
      title: '投资组合',
      icon: 'PieChart',
      requiresAuth: true
    }
  }
]

export default portfolioRoutes