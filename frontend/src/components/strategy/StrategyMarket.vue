<template>
  <div class="strategy-market">
    <div class="market-header">
      <div class="header-left">
        <h3>策略市场</h3>
        <el-tag type="info" size="small">
          共 {{ totalStrategies }} 个策略
        </el-tag>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索策略..."
          :prefix-icon="Search"
          style="width: 200px"
          @input="handleSearch"
        />
        <el-button @click="refreshStrategies" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="market-filters">
      <div class="filter-group">
        <span class="filter-label">分类:</span>
        <el-button-group>
          <el-button 
            v-for="category in categories" 
            :key="category.value"
            :type="selectedCategory === category.value ? 'primary' : 'default'"
            size="small"
            @click="selectedCategory = category.value"
          >
            {{ category.label }}
          </el-button>
        </el-button-group>
      </div>
      
      <div class="filter-group">
        <span class="filter-label">排序:</span>
        <el-select v-model="sortBy" size="small" style="width: 120px">
          <el-option label="最新" value="latest" />
          <el-option label="最热" value="popular" />
          <el-option label="收益率" value="return" />
          <el-option label="评分" value="rating" />
        </el-select>
      </div>
    </div>

    <!-- 策略列表 -->
    <div class="strategy-list" v-loading="loading">
      <div class="strategy-grid">
        <div 
          v-for="strategy in filteredStrategies" 
          :key="strategy.id"
          class="strategy-item"
          @click="viewStrategy(strategy)"
        >
          <div class="strategy-cover">
            <img :src="strategy.cover || '/default-strategy.png'" :alt="strategy.name" />
            <div class="strategy-overlay">
              <el-button type="primary" size="small">查看详情</el-button>
            </div>
          </div>
          
          <div class="strategy-content">
            <div class="strategy-header">
              <h4 class="strategy-name">{{ strategy.name }}</h4>
              <div class="strategy-rating">
                <el-rate 
                  v-model="strategy.rating" 
                  disabled 
                  size="small"
                  :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
                />
                <span class="rating-text">({{ strategy.ratingCount }})</span>
              </div>
            </div>
            
            <p class="strategy-description">{{ strategy.description }}</p>
            
            <div class="strategy-tags">
              <el-tag 
                v-for="tag in strategy.tags" 
                :key="tag" 
                size="small" 
                effect="plain"
              >
                {{ tag }}
              </el-tag>
            </div>
            
            <div class="strategy-metrics">
              <div class="metric-item">
                <span class="metric-label">年化收益</span>
                <span class="metric-value" :class="strategy.annualReturn >= 0 ? 'profit' : 'loss'">
                  {{ strategy.annualReturn >= 0 ? '+' : '' }}{{ strategy.annualReturn.toFixed(2) }}%
                </span>
              </div>
              <div class="metric-item">
                <span class="metric-label">最大回撤</span>
                <span class="metric-value loss">{{ strategy.maxDrawdown.toFixed(2) }}%</span>
              </div>
              <div class="metric-item">
                <span class="metric-label">夏普比率</span>
                <span class="metric-value">{{ strategy.sharpeRatio.toFixed(2) }}</span>
              </div>
            </div>
            
            <div class="strategy-footer">
              <div class="strategy-author">
                <el-avatar :size="24" :src="strategy.author.avatar">
                  {{ strategy.author.name.charAt(0) }}
                </el-avatar>
                <span class="author-name">{{ strategy.author.name }}</span>
              </div>
              <div class="strategy-actions">
                <el-button 
                  type="success" 
                  size="small"
                  @click.stop="subscribeStrategy(strategy)"
                  :disabled="strategy.isSubscribed"
                >
                  {{ strategy.isSubscribed ? '已订阅' : '订阅' }}
                </el-button>
                <el-button 
                  type="primary" 
                  size="small"
                  @click.stop="cloneStrategy(strategy)"
                >
                  克隆
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          :total="totalStrategies"
          layout="prev, pager, next, jumper"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 策略详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="selectedStrategy?.name"
      width="800px"
      @close="selectedStrategy = null"
    >
      <div class="strategy-detail" v-if="selectedStrategy">
        <div class="detail-header">
          <div class="detail-cover">
            <img :src="selectedStrategy.cover || '/default-strategy.png'" :alt="selectedStrategy.name" />
          </div>
          <div class="detail-info">
            <h3>{{ selectedStrategy.name }}</h3>
            <div class="detail-rating">
              <el-rate 
                v-model="selectedStrategy.rating" 
                disabled 
                :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
              />
              <span class="rating-text">({{ selectedStrategy.ratingCount }} 评价)</span>
            </div>
            <p class="detail-description">{{ selectedStrategy.description }}</p>
            <div class="detail-tags">
              <el-tag 
                v-for="tag in selectedStrategy.tags" 
                :key="tag" 
                effect="plain"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>
        
        <div class="detail-metrics">
          <div class="metrics-grid">
            <div class="metric-card">
              <div class="metric-title">年化收益率</div>
              <div class="metric-value" :class="selectedStrategy.annualReturn >= 0 ? 'profit' : 'loss'">
                {{ selectedStrategy.annualReturn >= 0 ? '+' : '' }}{{ selectedStrategy.annualReturn.toFixed(2) }}%
              </div>
            </div>
            <div class="metric-card">
              <div class="metric-title">最大回撤</div>
              <div class="metric-value loss">{{ selectedStrategy.maxDrawdown.toFixed(2) }}%</div>
            </div>
            <div class="metric-card">
              <div class="metric-title">夏普比率</div>
              <div class="metric-value">{{ selectedStrategy.sharpeRatio.toFixed(2) }}</div>
            </div>
            <div class="metric-card">
              <div class="metric-title">胜率</div>
              <div class="metric-value">{{ selectedStrategy.winRate.toFixed(2) }}%</div>
            </div>
          </div>
        </div>
        
        <div class="detail-author">
          <h4>策略作者</h4>
          <div class="author-info">
            <el-avatar :size="40" :src="selectedStrategy.author.avatar">
              {{ selectedStrategy.author.name.charAt(0) }}
            </el-avatar>
            <div class="author-details">
              <div class="author-name">{{ selectedStrategy.author.name }}</div>
              <div class="author-bio">{{ selectedStrategy.author.bio }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailDialogVisible = false">关闭</el-button>
          <el-button 
            type="success" 
            @click="subscribeStrategy(selectedStrategy)"
            :disabled="selectedStrategy?.isSubscribed"
          >
            {{ selectedStrategy?.isSubscribed ? '已订阅' : '订阅策略' }}
          </el-button>
          <el-button type="primary" @click="cloneStrategy(selectedStrategy)">
            克隆策略
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'

interface Strategy {
  id: string
  name: string
  description: string
  cover?: string
  category: string
  tags: string[]
  annualReturn: number
  maxDrawdown: number
  sharpeRatio: number
  winRate: number
  rating: number
  ratingCount: number
  isSubscribed: boolean
  author: {
    name: string
    avatar?: string
    bio: string
  }
  createdAt: string
}

interface Category {
  label: string
  value: string
}

const loading = ref(false)
const searchKeyword = ref('')
const selectedCategory = ref('all')
const sortBy = ref('latest')
const currentPage = ref(1)
const pageSize = ref(12)
const detailDialogVisible = ref(false)
const selectedStrategy = ref<Strategy | null>(null)

const categories: Category[] = [
  { label: '全部', value: 'all' },
  { label: '趋势跟踪', value: 'trend' },
  { label: '均值回归', value: 'mean_reversion' },
  { label: '套利策略', value: 'arbitrage' },
  { label: '量化选股', value: 'stock_selection' },
  { label: '高频交易', value: 'high_frequency' }
]

// 模拟策略数据
const strategies = ref<Strategy[]>([
  {
    id: 'STR001',
    name: '双均线趋势策略',
    description: '基于快慢均线交叉的经典趋势跟踪策略，适合中长期投资',
    category: 'trend',
    tags: ['趋势跟踪', '均线', '中长期'],
    annualReturn: 15.6,
    maxDrawdown: 8.2,
    sharpeRatio: 1.45,
    winRate: 62.5,
    rating: 4.5,
    ratingCount: 128,
    isSubscribed: false,
    author: {
      name: '量化大师',
      bio: '专注量化交易10年，擅长趋势策略开发'
    },
    createdAt: '2024-01-01'
  },
  {
    id: 'STR002',
    name: 'RSI均值回归策略',
    description: '利用RSI指标识别超买超卖机会，适合震荡市场',
    category: 'mean_reversion',
    tags: ['均值回归', 'RSI', '震荡市'],
    annualReturn: 12.3,
    maxDrawdown: 6.8,
    sharpeRatio: 1.32,
    winRate: 58.7,
    rating: 4.2,
    ratingCount: 95,
    isSubscribed: true,
    author: {
      name: '技术分析师',
      bio: '资深技术分析师，专注指标策略研发'
    },
    createdAt: '2024-01-05'
  },
  {
    id: 'STR003',
    name: '多因子选股策略',
    description: '基于财务指标和技术指标的多因子选股模型',
    category: 'stock_selection',
    tags: ['多因子', '选股', '基本面'],
    annualReturn: 18.9,
    maxDrawdown: 12.5,
    sharpeRatio: 1.28,
    winRate: 65.3,
    rating: 4.7,
    ratingCount: 156,
    isSubscribed: false,
    author: {
      name: '基金经理',
      bio: '公募基金经理，专注量化选股策略'
    },
    createdAt: '2024-01-10'
  }
])

const totalStrategies = computed(() => strategies.value.length)

const filteredStrategies = computed(() => {
  let filtered = strategies.value

  // 分类筛选
  if (selectedCategory.value !== 'all') {
    filtered = filtered.filter(s => s.category === selectedCategory.value)
  }

  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(s => 
      s.name.toLowerCase().includes(keyword) ||
      s.description.toLowerCase().includes(keyword) ||
      s.tags.some(tag => tag.toLowerCase().includes(keyword))
    )
  }

  // 排序
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'popular':
        return b.ratingCount - a.ratingCount
      case 'return':
        return b.annualReturn - a.annualReturn
      case 'rating':
        return b.rating - a.rating
      case 'latest':
      default:
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    }
  })

  return filtered
})

const handleSearch = () => {
  currentPage.value = 1
}

const handlePageChange = (page: number) => {
  currentPage.value = page
}

const refreshStrategies = async () => {
  loading.value = true
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('策略列表刷新成功')
  } catch (error) {
    ElMessage.error('策略列表刷新失败')
  } finally {
    loading.value = false
  }
}

const viewStrategy = (strategy: Strategy) => {
  selectedStrategy.value = strategy
  detailDialogVisible.value = true
}

const subscribeStrategy = async (strategy: Strategy) => {
  if (!strategy) return
  
  try {
    await ElMessageBox.confirm(`确定要订阅策略"${strategy.name}"吗？`, '确认订阅', {
      type: 'info'
    })
    
    loading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    strategy.isSubscribed = true
    ElMessage.success('策略订阅成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('策略订阅失败')
    }
  } finally {
    loading.value = false
  }
}

const cloneStrategy = async (strategy: Strategy) => {
  if (!strategy) return
  
  try {
    await ElMessageBox.confirm(`确定要克隆策略"${strategy.name}"吗？`, '确认克隆', {
      type: 'info'
    })
    
    loading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('策略克隆成功，已添加到我的策略')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('策略克隆失败')
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  refreshStrategies()
})
</script>

<style scoped>
.strategy-market {
  padding: 20px;
}

.market-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-right {
  display: flex;
  gap: 12px;
}

.market-filters {
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.strategy-list {
  min-height: 400px;
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.strategy-item {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  overflow: hidden;
}

.strategy-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.strategy-cover {
  position: relative;
  height: 150px;
  overflow: hidden;
}

.strategy-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.strategy-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.strategy-item:hover .strategy-overlay {
  opacity: 1;
}

.strategy-content {
  padding: 16px;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.strategy-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  line-height: 1.4;
}

.strategy-rating {
  display: flex;
  align-items: center;
  gap: 4px;
}

.rating-text {
  font-size: 12px;
  color: #909399;
}

.strategy-description {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.strategy-tags {
  margin-bottom: 12px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.strategy-metrics {
  margin-bottom: 12px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.metric-item {
  text-align: center;
}

.metric-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 2px;
}

.metric-value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.metric-value.profit {
  color: #f56c6c;
}

.metric-value.loss {
  color: #67c23a;
}

.strategy-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.strategy-author {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-name {
  font-size: 14px;
  color: #606266;
}

.strategy-actions {
  display: flex;
  gap: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.strategy-detail {
  padding: 16px 0;
}

.detail-header {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.detail-cover {
  width: 200px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
}

.detail-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-info {
  flex: 1;
}

.detail-info h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #303133;
}

.detail-rating {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.detail-description {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.detail-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.detail-metrics {
  margin-bottom: 24px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.metric-card {
  text-align: center;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.metric-title {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.metric-card .metric-value {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.detail-author h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #303133;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.author-details {
  flex: 1;
}

.author-details .author-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.author-bio {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 768px) {
  .market-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .market-filters {
    flex-direction: column;
    gap: 12px;
  }
  
  .strategy-grid {
    grid-template-columns: 1fr;
  }
  
  .detail-header {
    flex-direction: column;
  }
  
  .detail-cover {
    width: 100%;
    height: 200px;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style> 