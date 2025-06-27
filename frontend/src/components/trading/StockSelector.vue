<template>
  <div class="stock-selector">
    <!-- 搜索框 -->
    <div class="search-section">
      <el-input
        v-model="searchKeyword"
        placeholder="输入股票代码或名称搜索"
        clearable
        @input="handleSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
    </div>

    <!-- 热门股票 -->
    <div v-if="!searchKeyword" class="hot-stocks-section">
      <h4 class="section-title">热门股票</h4>
      <div class="stock-grid">
        <div
          v-for="stock in hotStocks"
          :key="stock.symbol"
          class="stock-item"
          @click="handleSelect(stock)"
        >
          <div class="stock-info">
            <div class="stock-code">{{ stock.symbol }}</div>
            <div class="stock-name">{{ stock.name }}</div>
          </div>
          <div class="stock-price">
            <div :class="getPriceChangeClass(stock.change)">
              {{ formatPrice(stock.price, 2) }}
            </div>
            <div class="change-info" :class="getPriceChangeClass(stock.change)">
              {{ formatPriceChange(stock.change, stock.changePercent) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-else class="search-results-section">
      <h4 class="section-title">搜索结果</h4>
      
      <div v-if="searching" class="loading-state">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>搜索中...</span>
      </div>
      
      <div v-else-if="searchResults.length === 0" class="empty-state">
        <el-empty description="未找到相关股票" :image-size="60" />
      </div>
      
      <div v-else class="results-list">
        <div
          v-for="stock in searchResults"
          :key="stock.symbol"
          class="result-item"
          @click="handleSelect(stock)"
        >
          <div class="stock-info">
            <div class="stock-code">{{ stock.symbol }}</div>
            <div class="stock-name">{{ stock.name }}</div>
            <div class="stock-market">{{ getMarketName(stock.market) }}</div>
          </div>
          <div class="stock-price">
            <div :class="getPriceChangeClass(stock.change)">
              {{ formatPrice(stock.price, 2) }}
            </div>
            <div class="change-info" :class="getPriceChangeClass(stock.change)">
              {{ formatPriceChange(stock.change, stock.changePercent) }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近选择 -->
    <div v-if="recentStocks.length > 0 && !searchKeyword" class="recent-section">
      <h4 class="section-title">最近选择</h4>
      <div class="recent-list">
        <el-tag
          v-for="stock in recentStocks"
          :key="stock.symbol"
          class="recent-tag"
          @click="handleSelect(stock)"
        >
          {{ stock.symbol }} {{ stock.name }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Search, Loading } from '@element-plus/icons-vue'
import { 
  formatPrice, 
  formatPriceChange, 
  getPriceChangeClass 
} from '@/utils/format/financial'

interface StockInfo {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  market: 'SH' | 'SZ' | 'BJ'
  volume?: number
  turnover?: number
}

interface Emits {
  (e: 'select', stock: StockInfo): void
}

const emit = defineEmits<Emits>()

// 状态
const searchKeyword = ref('')
const searching = ref(false)
const searchResults = ref<StockInfo[]>([])

// 热门股票数据
const hotStocks = ref<StockInfo[]>([
  {
    symbol: '000001',
    name: '平安银行',
    price: 12.50,
    change: 0.25,
    changePercent: 0.0204,
    market: 'SZ'
  },
  {
    symbol: '000002',
    name: '万科A',
    price: 18.30,
    change: -0.15,
    changePercent: -0.0081,
    market: 'SZ'
  },
  {
    symbol: '600000',
    name: '浦发银行',
    price: 8.90,
    change: 0.10,
    changePercent: 0.0114,
    market: 'SH'
  },
  {
    symbol: '600036',
    name: '招商银行',
    price: 35.20,
    change: 0.80,
    changePercent: 0.0233,
    market: 'SH'
  },
  {
    symbol: '600519',
    name: '贵州茅台',
    price: 1680.00,
    change: -20.00,
    changePercent: -0.0118,
    market: 'SH'
  },
  {
    symbol: '000858',
    name: '五粮液',
    price: 158.50,
    change: 2.30,
    changePercent: 0.0147,
    market: 'SZ'
  }
])

// 最近选择的股票
const recentStocks = ref<StockInfo[]>([])

// 方法
const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    return
  }

  searching.value = true
  
  try {
    // 模拟搜索API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 模拟搜索结果
    const keyword = searchKeyword.value.toLowerCase()
    searchResults.value = [
      ...hotStocks.value,
      {
        symbol: '300750',
        name: '宁德时代',
        price: 210.00,
        change: 5.50,
        changePercent: 0.0269,
        market: 'SZ'
      }
    ].filter(stock => 
      stock.symbol.includes(keyword) || 
      stock.name.toLowerCase().includes(keyword)
    )
  } catch (error) {
    console.error('搜索失败:', error)
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

const handleSelect = (stock: StockInfo) => {
  // 添加到最近选择
  addToRecent(stock)
  
  // 触发选择事件
  emit('select', stock)
}

const addToRecent = (stock: StockInfo) => {
  // 移除已存在的相同股票
  const filtered = recentStocks.value.filter(s => s.symbol !== stock.symbol)
  
  // 添加到开头，最多保留5个
  recentStocks.value = [stock, ...filtered].slice(0, 5)
  
  // 保存到本地存储
  localStorage.setItem('recent_stocks', JSON.stringify(recentStocks.value))
}

const loadRecentStocks = () => {
  try {
    const saved = localStorage.getItem('recent_stocks')
    if (saved) {
      recentStocks.value = JSON.parse(saved)
    }
  } catch (error) {
    console.error('加载最近选择失败:', error)
  }
}

const getMarketName = (market: string) => {
  const marketNames = {
    'SH': '上交所',
    'SZ': '深交所',
    'BJ': '北交所'
  }
  return marketNames[market as keyof typeof marketNames] || market
}

onMounted(() => {
  loadRecentStocks()
})
</script>

<style scoped lang="scss">
.stock-selector {
  @apply p-4;
  
  .search-section {
    @apply mb-6;
  }
  
  .section-title {
    @apply text-sm font-medium text-gray-700 mb-3;
  }
  
  // 热门股票网格
  .stock-grid {
    @apply grid grid-cols-1 gap-3;
    
    .stock-item {
      @apply flex items-center justify-between p-3 border border-gray-200 rounded-lg cursor-pointer transition-colors;
      
      &:hover {
        @apply bg-gray-50 border-blue-300;
      }
      
      .stock-info {
        .stock-code {
          @apply font-mono text-sm font-medium text-gray-900;
        }
        
        .stock-name {
          @apply text-xs text-gray-600 mt-1;
        }
      }
      
      .stock-price {
        @apply text-right;
        
        .change-info {
          @apply text-xs mt-1;
        }
      }
    }
  }
  
  // 搜索结果
  .search-results-section {
    .loading-state {
      @apply flex items-center justify-center py-8 text-gray-500;
      
      .el-icon {
        @apply mr-2;
      }
    }
    
    .empty-state {
      @apply py-8;
    }
    
    .results-list {
      @apply space-y-2;
      
      .result-item {
        @apply flex items-center justify-between p-3 border border-gray-200 rounded-lg cursor-pointer transition-colors;
        
        &:hover {
          @apply bg-gray-50 border-blue-300;
        }
        
        .stock-info {
          .stock-code {
            @apply font-mono text-sm font-medium text-gray-900;
          }
          
          .stock-name {
            @apply text-xs text-gray-600 mt-1;
          }
          
          .stock-market {
            @apply text-xs text-gray-400 mt-1;
          }
        }
        
        .stock-price {
          @apply text-right;
          
          .change-info {
            @apply text-xs mt-1;
          }
        }
      }
    }
  }
  
  // 最近选择
  .recent-section {
    @apply mt-6 pt-4 border-t border-gray-200;
    
    .recent-list {
      @apply flex flex-wrap gap-2;
      
      .recent-tag {
        @apply cursor-pointer;
        
        &:hover {
          @apply bg-blue-50 border-blue-300;
        }
      }
    }
  }
}

// 价格变化颜色
:deep(.text-financial-up) {
  @apply text-red-500;
}

:deep(.text-financial-down) {
  @apply text-green-500;
}

:deep(.text-financial-neutral) {
  @apply text-gray-500;
}
</style> 