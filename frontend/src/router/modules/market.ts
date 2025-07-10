import type { RouteRecordRaw } from 'vue-router'

const marketRoutes: RouteRecordRaw[] = [
  {
    path: '/market',
    name: 'market',
    component: () => import('@/views/Market/MarketView.vue'),
    meta: {
      title: '行情中心'
    }
  },
  {
    path: '/market/:symbol',
    name: 'stock-detail',
    component: () => import('@/views/Market/StockDetail.vue'),
    meta: {
      title: '股票详情'
    },
    props: true
  }
]

export default marketRoutes 