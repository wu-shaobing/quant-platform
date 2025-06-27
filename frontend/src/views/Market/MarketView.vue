<template>
  <div class="market-view">
    <!-- 页面头部 -->
    <div class="market-header">
      <div class="header-content">
        <h1 class="page-title">行情分析</h1>
        <div class="header-actions">
          <el-input
            v-model="searchQuery"
            placeholder="搜索股票代码或名称"
            style="width: 200px"
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-button type="primary" @click="refreshData" :loading="loading.stocks">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 市场指数 -->
    <div class="market-indices">
      <el-row :gutter="20">
        <el-col :span="6" v-for="(index, key) in marketIndices" :key="key">
          <el-card class="index-card">
            <div class="index-content">
              <div class="index-name">{{ getIndexName(key) }}</div>
              <div class="index-value">{{ index.price.toFixed(2) }}</div>
              <div class="index-change" :class="index.change >= 0 ? 'text-success' : 'text-danger'">
                {{ index.change >= 0 ? '+' : '' }}{{ index.change.toFixed(2) }} ({{ index.changePercent.toFixed(2) }}%)
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选工具栏 -->
    <div class="filter-toolbar">
      <el-row :gutter="20" align="middle">
        <el-col :span="4">
          <el-select v-model="selectedMarket" placeholder="选择市场" @change="handleMarketChange">
            <el-option label="全部市场" value="all" />
            <el-option label="沪市主板" value="sh" />
            <el-option label="深市主板" value="sz" />
            <el-option label="创业板" value="cyb" />
            <el-option label="科创板" value="kcb" />
          </el-select>
        </el-col>
        
        <el-col :span="4">
          <el-select v-model="selectedIndustry" placeholder="选择行业" clearable @change="handleIndustryChange">
            <el-option 
              v-for="industry in industries" 
              :key="industry.code" 
              :label="industry.name" 
              :value="industry.code" 
            />
          </el-select>
        </el-col>
        
        <el-col :span="4">
          <el-select v-model="sortBy" placeholder="排序方式" @change="handleSort">
            <el-option label="涨跌幅" value="changePercent" />
            <el-option label="成交量" value="volume" />
            <el-option label="成交额" value="amount" />
            <el-option label="股价" value="currentPrice" />
          </el-select>
        </el-col>
        
        <el-col :span="4">
          <el-button-group>
            <el-button 
              :type="viewMode === 'list' ? 'primary' : 'default'"
              @click="viewMode = 'list'"
            >
              <el-icon><List /></el-icon>
            </el-button>
            <el-button 
              :type="viewMode === 'grid' ? 'primary' : 'default'"
              @click="viewMode = 'grid'"
            >
              <el-icon><Grid /></el-icon>
            </el-button>
          </el-button-group>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区域 -->
    <div class="market-content">
      <el-row :gutter="20">
        <!-- 股票列表 -->
        <el-col :span="18">
          <el-card>
            <template #header>
              <div class="card-header">
                <span>股票列表</span>
                <span class="stock-count">共 {{ filteredStocks.length }} 只股票</span>
              </div>
            </template>
            
            <!-- 列表视图 -->
            <div v-if="viewMode === 'list'">
              <el-table 
                :data="filteredStocks" 
                style="width: 100%"
                @row-click="handleStockClick"
                v-loading="loading.stocks"
              >
                <el-table-column prop="symbol" label="代码" width="80" />
                <el-table-column prop="name" label="名称" width="120" />
                <el-table-column prop="currentPrice" label="现价" width="80">
                  <template #default="{ row }">
                    ¥{{ row.currentPrice.toFixed(2) }}
                  </template>
                </el-table-column>
                <el-table-column prop="change" label="涨跌额" width="80">
                  <template #default="{ row }">
                    <span :class="row.change >= 0 ? 'text-success' : 'text-danger'">
                      {{ row.change >= 0 ? '+' : '' }}{{ row.change.toFixed(2) }}
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="changePercent" label="涨跌幅" width="80">
                  <template #default="{ row }">
                    <span :class="row.changePercent >= 0 ? 'text-success' : 'text-danger'">
                      {{ row.changePercent >= 0 ? '+' : '' }}{{ row.changePercent.toFixed(2) }}%
                    </span>
                  </template>
                </el-table-column>
                <el-table-column prop="volume" label="成交量" width="100">
                  <template #default="{ row }">
                    {{ formatVolume(row.volume) }}
                  </template>
                </el-table-column>
                <el-table-column prop="amount" label="成交额" width="100">
                  <template #default="{ row }">
                    {{ formatAmount(row.amount) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120">
                  <template #default="{ row }">
                    <el-button size="small" @click.stop="addToWatchlist(row)">
                      自选
                    </el-button>
                    <el-button size="small" type="primary" @click.stop="quickTrade(row)">
                      交易
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
            
            <!-- 网格视图 -->
            <div v-else class="grid-view">
              <el-row :gutter="16">
                <el-col :span="6" v-for="stock in filteredStocks" :key="stock.symbol">
                  <StockCard 
                    :stock="stock" 
                    @click="handleStockClick(stock)"
                    @add-watchlist="addToWatchlist(stock)"
                    @quick-trade="quickTrade(stock)"
                  />
                </el-col>
              </el-row>
            </div>
          </el-card>
        </el-col>

        <!-- 侧边栏 -->
        <el-col :span="6">
          <!-- 排行榜 -->
          <el-card class="sidebar-panel">
            <template #header>
              <div class="panel-header">
                <el-tabs v-model="activeRankingTab" size="small">
                  <el-tab-pane label="涨幅榜" name="gainers" />
                  <el-tab-pane label="跌幅榜" name="losers" />
                  <el-tab-pane label="成交额" name="volume" />
                </el-tabs>
              </div>
            </template>
            
            <div class="ranking-list">
              <div 
                class="ranking-item" 
                v-for="(stock, index) in getCurrentRanking" 
                :key="stock.symbol"
                @click="handleStockClick(stock)"
              >
                <div class="rank-number">{{ index + 1 }}</div>
                <div class="stock-info">
                  <div class="stock-symbol">{{ stock.symbol }}</div>
                  <div class="stock-name">{{ stock.name }}</div>
                </div>
                <div class="stock-change">
                  <span :class="stock.changePercent >= 0 ? 'text-success' : 'text-danger'">
                    {{ stock.changePercent >= 0 ? '+' : '' }}{{ stock.changePercent.toFixed(2) }}%
                  </span>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 板块行情 -->
          <el-card class="sidebar-panel" style="margin-top: 20px;">
            <template #header>
              <h4>板块行情</h4>
            </template>
            
            <div class="sectors-list">
              <div 
                class="sector-item" 
                v-for="sector in sectors" 
                :key="sector.code"
              >
                <div class="sector-info">
                  <span class="sector-name">{{ sector.name }}</span>
                  <span class="sector-count">{{ sector.stockCount }}只</span>
                </div>
                <div class="sector-change">
                  <span :class="sector.changePercent >= 0 ? 'text-success' : 'text-danger'">
                    {{ sector.changePercent >= 0 ? '+' : '' }}{{ sector.changePercent.toFixed(2) }}%
                  </span>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 市场资讯 -->
          <el-card class="sidebar-panel" style="margin-top: 20px;">
            <template #header>
              <h4>市场资讯</h4>
            </template>
            
            <div class="news-list">
              <div 
                class="news-item" 
                v-for="news in marketNews" 
                :key="news.id"
              >
                <div class="news-title">{{ news.title }}</div>
                <div class="news-meta">
                  <span class="news-source">{{ news.source }}</span>
                  <span class="news-time">{{ formatTime(news.publishTime) }}</span>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Search, List, Grid, Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import StockCard from '@/components/market/StockCard.vue'
import { formatVolume, formatAmount, formatTime } from '@/utils/formatters'

const router = useRouter()

// 响应式状态
const searchQuery = ref('')
const selectedMarket = ref('all')
const selectedIndustry = ref('')
const viewMode = ref<'list' | 'grid'>('list')
const sortBy = ref('changePercent')
const activeRankingTab = ref('gainers')

const loading = ref({
  stocks: false,
  indices: false
})

// 模拟数据
const mockStocks = ref([
  { symbol: '000001', name: '平安银行', currentPrice: 12.34, change: 0.56, changePercent: 4.76, volume: 125000000, amount: 1540000000 },
  { symbol: '000002', name: '万科A', currentPrice: 23.45, change: -0.78, changePercent: -3.22, volume: 98000000, amount: 2300000000 },
  { symbol: '000858', name: '五粮液', currentPrice: 156.78, change: 5.67, changePercent: 3.75, volume: 45000000, amount: 7050000000 },
  { symbol: '600036', name: '招商银行', currentPrice: 45.67, change: 1.23, changePercent: 2.77, volume: 87000000, amount: 3970000000 },
  { symbol: '600519', name: '贵州茅台', currentPrice: 1678.90, change: -23.45, changePercent: -1.38, volume: 12000000, amount: 20100000000 }
])

const marketIndices = ref({
  sh: { price: 3245.67, change: 15.23, changePercent: 0.47, volume: 125000000, amount: 185000000000 },
  sz: { price: 11234.56, change: -8.45, changePercent: -0.075, volume: 98000000, amount: 142000000000 },
  cyb: { price: 2456.78, change: 12.34, changePercent: 0.51, volume: 45000000, amount: 68000000000 },
  kcb: { price: 1234.56, change: 5.67, changePercent: 0.46, volume: 23000000, amount: 35000000000 }
})

const industries = ref([
  { code: 'tech', name: '科技' },
  { code: 'finance', name: '金融' },
  { code: 'healthcare', name: '医疗' },
  { code: 'energy', name: '能源' },
  { code: 'consumer', name: '消费' }
])

const sectors = ref([
  { code: 'tech', name: '科技板块', changePercent: 2.45, stockCount: 156 },
  { code: 'finance', name: '金融板块', changePercent: -0.85, stockCount: 89 },
  { code: 'healthcare', name: '医疗板块', changePercent: 1.23, stockCount: 67 },
  { code: 'energy', name: '能源板块', changePercent: 0.56, stockCount: 45 },
  { code: 'consumer', name: '消费板块', changePercent: -1.34, stockCount: 123 }
])

const marketNews = ref([
  {
    id: '1',
    title: '央行宣布降准0.5个百分点',
    content: '为支持实体经济发展，央行决定下调存款准备金率...',
    source: '财经网',
    publishTime: Date.now() - 3600000,
    category: 'policy'
  },
  {
    id: '2',
    title: '科技股集体上涨，AI概念持续火热',
    content: '受人工智能技术发展利好消息影响，科技股今日集体上涨...',
    source: '证券日报',
    publishTime: Date.now() - 7200000,
    category: 'market'
  }
])

// 计算属性
const filteredStocks = computed(() => {
  let stocks = mockStocks.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    stocks = stocks.filter(stock => 
      stock.symbol.toLowerCase().includes(query) || 
      stock.name.toLowerCase().includes(query)
    )
  }

  // 市场过滤
  if (selectedMarket.value !== 'all') {
    stocks = stocks.filter(stock => {
      switch (selectedMarket.value) {
        case 'sh': return stock.symbol.startsWith('60')
        case 'sz': return stock.symbol.startsWith('00')
        case 'cyb': return stock.symbol.startsWith('30')
        case 'kcb': return stock.symbol.startsWith('68')
        default: return true
      }
    })
  }

  // 排序
  return sortStocks(stocks)
})

const getCurrentRanking = computed(() => {
  switch (activeRankingTab.value) {
    case 'gainers':
      return [...mockStocks.value].sort((a, b) => b.changePercent - a.changePercent).slice(0, 10)
    case 'losers':
      return [...mockStocks.value].sort((a, b) => a.changePercent - b.changePercent).slice(0, 10)
    case 'volume':
      return [...mockStocks.value].sort((a, b) => b.amount - a.amount).slice(0, 10)
    default:
      return []
  }
})

// 方法
const getIndexName = (key: string) => {
  const names: Record<string, string> = {
    sh: '上证指数',
    sz: '深证成指',
    cyb: '创业板指',
    kcb: '科创50'
  }
  return names[key] || key
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
}

const handleMarketChange = () => {
  // 市场变化逻辑已在计算属性中处理
}

const handleIndustryChange = () => {
  // 行业变化逻辑已在计算属性中处理
}

const handleSort = () => {
  // 排序逻辑已在计算属性中处理
}

const sortStocks = (stocks: any[]) => {
  return [...stocks].sort((a, b) => {
    const aValue = a[sortBy.value] as number
    const bValue = b[sortBy.value] as number
    return bValue - aValue
  })
}

const refreshData = async () => {
  try {
    loading.value.stocks = true
    // 模拟刷新
    setTimeout(() => {
      loading.value.stocks = false
      ElMessage.success('数据刷新成功')
    }, 1000)
  } catch (err) {
    console.error('刷新失败:', err)
    ElMessage.error('数据刷新失败')
  }
}

const handleStockClick = (stock: any) => {
  router.push(`/market/${stock.symbol}`)
}

const addToWatchlist = async (stock: any) => {
  try {
    ElMessage.success(`${stock.name} 已添加到自选股`)
  } catch (err) {
    console.error('添加自选股失败:', err)
    ElMessage.error('添加自选股失败')
  }
}

const quickTrade = (stock: any) => {
  router.push({
    path: '/trading',
    query: { symbol: stock.symbol }
  })
}

onMounted(() => {
  // 初始化数据
})
</script>

<style scoped>
.market-view {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.market-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.market-indices {
  margin-bottom: 24px;
}

.index-card {
  height: 100px;
  cursor: pointer;
  transition: all 0.3s;
}

.index-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.index-content {
  text-align: center;
  padding: 8px 0;
}

.index-name {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.index-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.index-change {
  font-size: 12px;
}

.filter-toolbar {
  background: white;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.market-content {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stock-count {
  font-size: 12px;
  color: #999;
}

.grid-view {
  min-height: 400px;
}

.sidebar-panel {
  margin-bottom: 20px;
}

.panel-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.ranking-list {
  max-height: 300px;
  overflow-y: auto;
}

.ranking-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.3s;
}

.ranking-item:hover {
  background-color: #f5f7fa;
}

.rank-number {
  width: 24px;
  height: 24px;
  background: #f0f0f0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  margin-right: 12px;
}

.stock-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stock-symbol {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.stock-name {
  font-size: 12px;
  color: #666;
}

.stock-change {
  font-size: 12px;
  text-align: right;
}

.sectors-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sector-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.sector-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.sector-name {
  font-size: 14px;
  color: #333;
}

.sector-count {
  font-size: 12px;
  color: #999;
}

.sector-change {
  font-size: 12px;
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.news-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
}

.news-title {
  font-size: 14px;
  color: #333;
  margin-bottom: 4px;
  line-height: 1.4;
}

.news-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #999;
}

.text-success {
  color: #67c23a;
}

.text-danger {
  color: #f56c6c;
}
</style>