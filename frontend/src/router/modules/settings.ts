import type { RouteRecordRaw } from 'vue-router'

const settingsRoutes: RouteRecordRaw[] = [
  {
    path: '/settings',
    name: 'Settings',
    meta: {
      title: '系统设置',
      icon: 'Setting',
      requiresAuth: true,
    },
    children: [
      {
        path: '',
        name: 'SettingsIndex',
        component: () => import('@/views/Settings/SettingsView.vue'),
        meta: {
          title: '基础设置',
        },
      },
      {
        path: 'profile',
        name: 'UserProfile',
        component: () => import('@/views/Settings/UserProfile.vue'),
        meta: {
          title: '个人资料',
        },
      },
      {
        path: 'security',
        name: 'SecuritySettings',
        component: () => import('@/views/Settings/SecuritySettings.vue'),
        meta: {
          title: '安全设置',
        },
      },
      {
        path: 'notifications',
        name: 'NotificationSettings',
        component: () => import('@/views/Settings/NotificationSettings.vue'),
        meta: {
          title: '通知设置',
        },
      },
      {
        path: 'trading',
        name: 'TradingSettings',
        component: () => import('@/views/Settings/TradingSettings.vue'),
        meta: {
          title: '交易设置',
        },
      },
      {
        path: 'api',
        name: 'ApiSettings',
        component: () => import('@/views/Settings/ApiSettings.vue'),
        meta: {
          title: 'API设置',
        },
      },
    ],
  },
]

export default settingsRoutes