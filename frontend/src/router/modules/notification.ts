import type { RouteRecordRaw } from 'vue-router'

const notificationRoutes: RouteRecordRaw[] = [
  {
    path: '/notifications',
    name: 'Notifications',
    meta: {
      title: '消息中心',
      icon: 'Bell',
      requiresAuth: true,
    },
    children: [
      {
        path: '',
        name: 'NotificationList',
        component: () => import('@/views/Notification/NotificationList.vue'),
        meta: {
          title: '消息列表',
        },
      },
      {
        path: 'alerts',
        name: 'AlertNotifications',
        component: () => import('@/views/Notification/AlertNotifications.vue'),
        meta: {
          title: '告警通知',
        },
      },
      {
        path: 'trading',
        name: 'TradingNotifications',
        component: () => import('@/views/Notification/TradingNotifications.vue'),
        meta: {
          title: '交易通知',
        },
      },
      {
        path: 'system',
        name: 'SystemNotifications',
        component: () => import('@/views/Notification/SystemNotifications.vue'),
        meta: {
          title: '系统通知',
        },
      },
      {
        path: 'settings',
        name: 'NotificationSettings',
        component: () => import('@/views/Notification/NotificationSettings.vue'),
        meta: {
          title: '通知设置',
        },
      },
    ],
  },
]

export default notificationRoutes