import { createRouter, createWebHistory } from 'vue-router'
import dashboardRoutes from './modules/dashboard'
import marketRoutes from './modules/market'
import tradingRoutes from './modules/trading'
import strategyRoutes from './modules/strategy'
import backtestRoutes from './modules/backtest'
import portfolioRoutes from './modules/portfolio'
import riskRoutes from './modules/risk'
import settingsRoutes from './modules/settings'
import errorRoutes from './modules/error'
import notificationRoutes from './modules/notification'

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
        ...settingsRoutes,
        ...notificationRoutes,
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
    // 认证相关路由
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Auth/LoginView.vue'),
      meta: {
        title: '登录',
        requiresAuth: false,
      },
    },
    {
      path: '/test-slider',
      name: 'TestSlider',
      component: () => import('@/views/Auth/TestSlider.vue'),
      meta: {
        title: '滑轨验证测试',
        requiresAuth: false,
      },
    },
    // 错误页面路由
    ...errorRoutes,
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

