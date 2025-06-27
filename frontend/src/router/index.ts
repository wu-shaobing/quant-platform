import { createRouter, createWebHistory } from 'vue-router'
import dashboardRoutes from './modules/dashboard'
import marketRoutes from './modules/market'
import tradingRoutes from './modules/trading'
import strategyRoutes from './modules/strategy'
import backtestRoutes from './modules/backtest'
import portfolioRoutes from './modules/portfolio'
import riskRoutes from './modules/risk'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: () => import('@/layouts/DefaultLayout.vue'),
      redirect: '/dashboard',
      children: [
        ...dashboardRoutes,
        ...marketRoutes,
        ...tradingRoutes,
        ...strategyRoutes,
        ...backtestRoutes,
        ...portfolioRoutes,
        ...riskRoutes,
        // 组件展示页面
        {
          path: '/demo',
          name: 'ComponentShowcase',
          component: () => import('@/views/Demo/ComponentShowcase.vue'),
          meta: {
            title: '组件展示',
            icon: 'Grid',
            requiresAuth: false
          }
        },
      ],
    },
    // 可以添加其他布局的路由，例如登录页面
    // {
    //   path: '/login',
    //   component: () => import('@/views/Auth/LoginView.vue')
    // }
  ],
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

export default router

