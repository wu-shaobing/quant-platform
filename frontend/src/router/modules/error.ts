import type { RouteRecordRaw } from 'vue-router'

const errorRoutes: RouteRecordRaw[] = [
  {
    path: '/error',
    name: 'Error',
    meta: {
      title: '错误页面',
      hidden: true,
    },
    children: [
      {
        path: '403',
        name: 'Error403',
        component: () => import('@/views/Error/403.vue'),
        meta: {
          title: '403 - 无权限访问',
        },
      },
      {
        path: '404',
        name: 'Error404',
        component: () => import('@/views/Error/404.vue'),
        meta: {
          title: '404 - 页面不存在',
        },
      },
      {
        path: '500',
        name: 'Error500',
        component: () => import('@/views/Error/500.vue'),
        meta: {
          title: '500 - 服务器错误',
        },
      },
      {
        path: 'network',
        name: 'NetworkError',
        component: () => import('@/views/Error/NetworkError.vue'),
        meta: {
          title: '网络错误',
        },
      },
    ],
  },
  // 404路由必须放在最后
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/Error/404.vue'),
    meta: {
      title: '页面不存在',
      hidden: true,
    },
  },
]

export default errorRoutes