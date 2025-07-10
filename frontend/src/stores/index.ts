import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

// Import all store modules
export { useAuthStore } from './modules/auth'
export { useBacktestStore } from './modules/backtest'
export { useMarketStore } from './modules/market'
export { usePortfolioStore } from './modules/portfolio'
export { useRiskStore } from './modules/risk'
export { useStrategyStore } from './modules/strategy'
export { useTradingStore } from './modules/trading'
export { useUiStore } from './modules/ui'
export { useUserStore } from './modules/user'

// Create and configure pinia instance
export const pinia = createPinia()

// Add plugins
pinia.use(piniaPluginPersistedstate)

export default pinia
