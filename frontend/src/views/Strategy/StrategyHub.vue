<!--
  策略中心页面
  提供策略浏览、搜索、分类等功能
-->
<template>
  <div class="strategy-hub">
    <!-- 页面头部 -->
    <div class="hub-header">
      <div class="header-content">
        <h1 class="page-title">策略中心</h1>
        <p class="page-description">发现、学习和使用优质的量化交易策略</p>
      </div>
      
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="createStrategy">
          创建策略
        </el-button>
        <el-button :icon="Upload" @click="importStrategy">
          导入策略
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索策略名称、标签或作者..."
          :prefix-icon="Search"
          size="large"
          clearable
          @input="handleSearch"
        />
        <el-button type="primary" size="large" @click="handleSearch">
          搜索
        </el-button>
      </div>
      
      <div class="filter-bar">
        <!-- 分类筛选 -->
        <el-select
          v-model="selectedCategory"
          placeholder="策略分类"
          clearable
          @change="handleFilter"
        >
          <el-option
            v-for="category in categories"
            :key="category.value"
            :label="category.label"
            :value="category.value"
          />
        </el-select>
        
        <!-- 风险等级 -->
        <el-select
          v-model="selectedRiskLevel"
          placeholder="风险等级"
          clearable
          @change="handleFilter"
        >
          <el-option label="低风险" value="low" />
          <el-option label="中风险" value="medium" />
          <el-option label="高风险" value="high" />
        </el-select>
        
        <!-- 收益范围 -->
        <el-select
          v-model="selectedReturnRange"
          placeholder="年化收益"
          clearable
          @change="handleFilter"
        >
          <el-option label="0-10%" value="0-10" />
          <el-option label="10-20%" value="10-20" />
          <el-option label="20-50%" value="20-50" />
          <el-option label="50%以上" value="50+" />
        </el-select>
        
        <!-- 排序方式 -->
        <el-select
          v-model="sortBy"
          placeholder="排序方式"
          @change="handleSort"
        >
          <el-option label="最新发布" value="latest" />
          <el-option label="最受欢迎" value="popular" />
          <el-option label="收益最高" value="return" />
          <el-option label="风险最低" value="risk" />
          <el-option label="评分最高" value="rating" />
        </el-select>
      </div>
    </div>

    <!-- 推荐策略 -->
    <div v-if="!searchQuery" class="featured-section">
      <h2 class="section-title">
        <el-icon><Star /></el-icon>
        推荐策略
      </h2>
      
      <div class="featured-grid">
        <div
          v-for="strategy in featuredStrategies"
          :key="strategy.id"
          class="featured-card"
          @click="viewStrategy(strategy)"
        >
          <div class="card-header">
            <div class="strategy-info">
              <h3 class="strategy-name">{{ strategy.name }}</h3>
              <p class="strategy-author">{{ strategy.author }}</p>
            </div>
            <div class="strategy-badge">
              <el-tag :type="getRiskTagType(strategy.riskLevel)">
                {{ getRiskLabel(strategy.riskLevel) }}
              </el-tag>
            </div>
          </div>
          
          <div class="card-content">
            <p class="strategy-description">{{ strategy.description }}</p>
            
            <div class="strategy-metrics">
              <div class="metric">
                <span class="metric-label">年化收益</span>
                <span class="metric-value profit">{{ formatPercent(strategy.annualReturn) }}</span>
              </div>
              <div class="metric">
                <span class="metric-label">最大回撤</span>
                <span class="metric-value loss">{{ formatPercent(strategy.maxDrawdown) }}</span>
              </div>
              <div class="metric">
                <span class="metric-label">夏普比率</span>
                <span class="metric-value">{{ formatNumber(strategy.sharpeRatio, 2) }}</span>
              </div>
            </div>
          </div>
          
          <div class="card-footer">
            <div class="strategy-stats">
              <span class="stat">
                <el-icon><View /></el-icon>
                {{ strategy.viewCount }}
              </span>
              <span class="stat">
                <el-icon><Star /></el-icon>
                {{ strategy.favoriteCount }}
              </span>
              <span class="stat">
                <el-icon><Download /></el-icon>
                {{ strategy.downloadCount }}
              </span>
            </div>
            
            <div class="strategy-rating">
              <el-rate
                v-model="strategy.rating"
                disabled
                show-score
                text-color="#ff9900"
                score-template="{value}"
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 策略列表 -->
    <div class="strategies-section">
      <div class="section-header">
        <h2 class="section-title">
          {{ searchQuery ? '搜索结果' : '全部策略' }}
          <span class="result-count">({{ totalCount }})</span>
        </h2>
        
        <div class="view-toggle">
          <el-button-group>
            <el-button
              :type="viewMode === 'grid' ? 'primary' : 'default'"
              :icon="Grid"
              @click="viewMode = 'grid'"
            />
            <el-button
              :type="viewMode === 'list' ? 'primary' : 'default'"
              :icon="List"
              @click="viewMode = 'list'"
            />
          </el-button-group>
        </div>
      </div>
      
      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="6" animated />
      </div>
      
      <!-- 网格视图 -->
      <div v-else-if="viewMode === 'grid'" class="strategies-grid">
        <StrategyCard
          v-for="strategy in strategies"
          :key="strategy.id"
          :strategy="strategy"
          @view="viewStrategy"
          @favorite="toggleFavorite"
          @download="downloadStrategy"
        />
      </div>
      
      <!-- 列表视图 -->
      <div v-else class="strategies-list">
        <div
          v-for="strategy in strategies"
          :key="strategy.id"
          class="strategy-list-item"
          @click="viewStrategy(strategy)"
        >
          <div class="item-left">
            <div class="strategy-basic">
              <h3 class="strategy-name">{{ strategy.name }}</h3>
              <p class="strategy-author">作者: {{ strategy.author }}</p>
              <p class="strategy-description">{{ strategy.description }}</p>
            </div>
            
            <div class="strategy-tags">
              <el-tag
                v-for="tag in strategy.tags"
                :key="tag"
                size="small"
                type="info"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
          
          <div class="item-right">
            <div class="strategy-performance">
              <div class="perf-item">
                <span class="perf-label">年化收益</span>
                <span class="perf-value profit">{{ formatPercent(strategy.annualReturn) }}</span>
              </div>
              <div class="perf-item">
                <span class="perf-label">最大回撤</span>
                <span class="perf-value loss">{{ formatPercent(strategy.maxDrawdown) }}</span>
              </div>
              <div class="perf-item">
                <span class="perf-label">夏普比率</span>
                <span class="perf-value">{{ formatNumber(strategy.sharpeRatio, 2) }}</span>
              </div>
            </div>
            
            <div class="strategy-actions">
              <el-button size="small" @click.stop="toggleFavorite(strategy)">
                <el-icon><Star /></el-icon>
                {{ strategy.isFavorited ? '已收藏' : '收藏' }}
              </el-button>
              <el-button size="small" type="primary" @click.stop="downloadStrategy(strategy)">
                <el-icon><Download /></el-icon>
                使用
              </el-button>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="!loading && strategies.length === 0" class="empty-state">
        <el-empty description="暂无策略数据">
          <el-button type="primary" @click="createStrategy">
            创建第一个策略
          </el-button>
        </el-empty>
      </div>
      
      <!-- 分页 -->
      <div v-if="totalCount > pageSize" class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalCount"
          :page-sizes="[12, 24, 48, 96]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handlePageSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Plus, Upload, Search, Star, View, Download, Grid, List
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { formatPercent, formatNumber } from '@/utils/formatters'
import { useStrategyStore } from '@/stores/modules/strategy'
import StrategyCard from '@/components/strategy/StrategyCard/StrategyCard.vue'
import type { Strategy } from '@/types/strategy'

const router = useRouter()
const strategyStore = useStrategyStore()

// 搜索和筛选状态
const searchQuery = ref('')
const selectedCategory = ref('')
const selectedRiskLevel = ref('')
const selectedReturnRange = ref('')
const sortBy = ref('latest')
const viewMode = ref<'grid' | 'list'>('grid')

// 分页状态
const currentPage = ref(1)
const pageSize = ref(24)
const totalCount = ref(0)
const loading = ref(false)

// 策略数据
const strategies = ref<Strategy[]>([])
const featuredStrategies = ref<Strategy[]>([])

// 分类选项
const categories = [
  { label: '趋势跟踪', value: 'trend' },
  { label: '均值回归', value: 'mean_reversion' },
  { label: '套利策略', value: 'arbitrage' },
  { label: '动量策略', value: 'momentum' },
  { label: '价值投资', value: 'value' },
  { label: '技术分析', value: 'technical' },
  { label: '基本面分析', value: 'fundamental' },
  { label: '量化选股', value: 'stock_selection' },
  { label: '风险平价', value: 'risk_parity' },
  { label: '机器学习', value: 'machine_learning' }
]

// 获取风险标签类型
const getRiskTagType = (riskLevel: string) => {
  switch (riskLevel) {
    case 'low': return 'success'
    case 'medium': return 'warning'
    case 'high': return 'danger'
    default: return 'info'
  }
}

// 获取风险标签文本
const getRiskLabel = (riskLevel: string) => {
  switch (riskLevel) {
    case 'low': return '低风险'
    case 'medium': return '中风险'
    case 'high': return '高风险'
    default: return '未知'
  }
}

// 搜索处理
const handleSearch = async () => {
  currentPage.value = 1
  await loadStrategies()
}

// 筛选处理
const handleFilter = async () => {
  currentPage.value = 1
  await loadStrategies()
}

// 排序处理
const handleSort = async () => {
  await loadStrategies()
}

// 分页处理
const handlePageChange = async (page: number) => {
  currentPage.value = page
  await loadStrategies()
}

const handlePageSizeChange = async (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  await loadStrategies()
}

// 加载策略列表
const loadStrategies = async () => {
  try {
    loading.value = true
    
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value,
      search: searchQuery.value,
      category: selectedCategory.value,
      riskLevel: selectedRiskLevel.value,
      returnRange: selectedReturnRange.value,
      sortBy: sortBy.value
    }
    
    const response = await strategyStore.getStrategies(params)
    strategies.value = response.items
    totalCount.value = response.total
    
  } catch (error) {
    ElMessage.error('加载策略列表失败')
  } finally {
    loading.value = false
  }
}

// 加载推荐策略
const loadFeaturedStrategies = async () => {
  try {
    const response = await strategyStore.getFeaturedStrategies()
    featuredStrategies.value = response
  } catch (error) {
    console.error('加载推荐策略失败:', error)
  }
}

// 查看策略详情
const viewStrategy = (strategy: Strategy) => {
  router.push(`/strategy/detail/${strategy.id}`)
}

// 创建策略
const createStrategy = () => {
  router.push('/strategy/develop')
}

// 导入策略
const importStrategy = () => {
  // 创建文件输入元素
  const fileInput = document.createElement('input')
  fileInput.type = 'file'
  fileInput.accept = '.json,.py,.js,.ts'
  fileInput.multiple = true
  
  fileInput.onchange = async (event) => {
    const files = (event.target as HTMLInputElement).files
    if (!files || files.length === 0) return
    
    try {
      loading.value = true
      
      for (const file of files) {
        await processStrategyFile(file)
      }
      
      ElMessage.success(`成功导入 ${files.length} 个策略文件`)
      await fetchStrategies() // 刷新策略列表
      
    } catch (error) {
      console.error('导入策略失败:', error)
      ElMessage.error('导入策略失败，请检查文件格式')
    } finally {
      loading.value = false
    }
  }
  
  fileInput.click()
}

// 处理策略文件
const processStrategyFile = async (file: File): Promise<void> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = async (e) => {
      try {
        const content = e.target?.result as string
        let strategyData: any
        
        // 根据文件类型解析内容
        if (file.name.endsWith('.json')) {
          strategyData = JSON.parse(content)
        } else if (file.name.endsWith('.py')) {
          // Python策略文件解析
          strategyData = await parsePythonStrategy(content, file.name)
        } else if (file.name.endsWith('.js') || file.name.endsWith('.ts')) {
          // JavaScript/TypeScript策略文件解析
          strategyData = await parseJavaScriptStrategy(content, file.name)
        } else {
          throw new Error('不支持的文件格式')
        }
        
        // 验证策略数据格式
        validateStrategyData(strategyData)
        
        // 调用API保存策略
        await strategyStore.importStrategy(strategyData)
        
        resolve()
      } catch (error) {
        reject(error)
      }
    }
    
    reader.onerror = () => reject(new Error('文件读取失败'))
    reader.readAsText(file)
  })
}

// 解析Python策略文件
const parsePythonStrategy = async (content: string, filename: string) => {
  // 提取策略元数据
  const metadataMatch = content.match(/"""([\s\S]*?)"""/)
  const metadata = metadataMatch ? parseStrategyMetadata(metadataMatch[1]) : {}
  
  // 提取策略类名
  const classMatch = content.match(/class\s+(\w+)\s*\([^)]*\):/)
  const className = classMatch ? classMatch[1] : filename.replace('.py', '')
  
  // 提取主要方法
  const methods = extractPythonMethods(content)
  
  return {
    name: metadata.name || className,
    description: metadata.description || '从Python文件导入的策略',
    author: metadata.author || 'Unknown',
    version: metadata.version || '1.0.0',
    language: 'python',
    sourceCode: content,
    entryPoint: className,
    methods: methods,
    parameters: metadata.parameters || [],
    riskLevel: metadata.riskLevel || 'medium',
    category: metadata.category || 'custom',
    tags: metadata.tags || [],
    createdAt: new Date().toISOString()
  }
}

// 解析JavaScript/TypeScript策略文件
const parseJavaScriptStrategy = async (content: string, filename: string) => {
  // 提取策略元数据（从注释中）
  const metadataMatch = content.match(/\/\*\*([\s\S]*?)\*\//)
  const metadata = metadataMatch ? parseStrategyMetadata(metadataMatch[1]) : {}
  
  // 提取类名或函数名
  const classMatch = content.match(/(?:class|function)\s+(\w+)/) 
  const name = classMatch ? classMatch[1] : filename.replace(/\.(js|ts)$/, '')
  
  // 提取导出的方法
  const methods = extractJavaScriptMethods(content)
  
  return {
    name: metadata.name || name,
    description: metadata.description || '从JavaScript/TypeScript文件导入的策略',
    author: metadata.author || 'Unknown',
    version: metadata.version || '1.0.0',
    language: filename.endsWith('.ts') ? 'typescript' : 'javascript',
    sourceCode: content,
    entryPoint: name,
    methods: methods,
    parameters: metadata.parameters || [],
    riskLevel: metadata.riskLevel || 'medium',
    category: metadata.category || 'custom',
    tags: metadata.tags || [],
    createdAt: new Date().toISOString()
  }
}

// 解析策略元数据
const parseStrategyMetadata = (metadataText: string) => {
  const metadata: any = {}
  
  // 解析各种元数据字段
  const patterns = {
    name: /@name\s+(.+)/,
    description: /@description\s+([\s\S]*?)(?=@|$)/,
    author: /@author\s+(.+)/,
    version: /@version\s+(.+)/,
    riskLevel: /@risk\s+(low|medium|high)/,
    category: /@category\s+(.+)/,
    tags: /@tags\s+(.+)/
  }
  
  Object.entries(patterns).forEach(([key, pattern]) => {
    const match = metadataText.match(pattern)
    if (match) {
      if (key === 'tags') {
        metadata[key] = match[1].split(',').map(tag => tag.trim())
      } else if (key === 'description') {
        metadata[key] = match[1].trim().replace(/\s+/g, ' ')
      } else {
        metadata[key] = match[1].trim()
      }
    }
  })
  
  // 解析参数定义
  const paramPattern = /@param\s+(\w+)\s+(.+?)\s+(.+)/g
  const parameters = []
  let paramMatch
  
  while ((paramMatch = paramPattern.exec(metadataText)) !== null) {
    parameters.push({
      name: paramMatch[1],
      type: paramMatch[2],
      description: paramMatch[3],
      defaultValue: null
    })
  }
  
  if (parameters.length > 0) {
    metadata.parameters = parameters
  }
  
  return metadata
}

// 提取Python方法
const extractPythonMethods = (content: string) => {
  const methods = []
  const methodPattern = /def\s+(\w+)\s*\([^)]*\):/g
  let match
  
  while ((match = methodPattern.exec(content)) !== null) {
    methods.push({
      name: match[1],
      type: 'function',
      language: 'python'
    })
  }
  
  return methods
}

// 提取JavaScript方法
const extractJavaScriptMethods = (content: string) => {
  const methods = []
  
  // 匹配函数声明
  const functionPattern = /(?:function\s+(\w+)|(\w+)\s*:\s*function|(\w+)\s*\([^)]*\)\s*{)/g
  let match
  
  while ((match = functionPattern.exec(content)) !== null) {
    const methodName = match[1] || match[2] || match[3]
    if (methodName) {
      methods.push({
        name: methodName,
        type: 'function',
        language: 'javascript'
      })
    }
  }
  
  return methods
}

// 验证策略数据
const validateStrategyData = (data: any) => {
  const requiredFields = ['name', 'description', 'sourceCode']
  
  for (const field of requiredFields) {
    if (!data[field]) {
      throw new Error(`缺少必要字段: ${field}`)
    }
  }
  
  // 验证风险等级
  if (data.riskLevel && !['low', 'medium', 'high'].includes(data.riskLevel)) {
    throw new Error('无效的风险等级')
  }
  
  // 验证语言类型
  const supportedLanguages = ['python', 'javascript', 'typescript']
  if (data.language && !supportedLanguages.includes(data.language)) {
    throw new Error('不支持的编程语言')
  }
}

// 切换收藏状态
const toggleFavorite = async (strategy: Strategy) => {
  try {
    if (strategy.isFavorited) {
      await strategyStore.unfavoriteStrategy(strategy.id)
      strategy.isFavorited = false
      strategy.favoriteCount--
      ElMessage.success('已取消收藏')
    } else {
      await strategyStore.favoriteStrategy(strategy.id)
      strategy.isFavorited = true
      strategy.favoriteCount++
      ElMessage.success('收藏成功')
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 下载/使用策略
const downloadStrategy = async (strategy: Strategy) => {
  try {
    await strategyStore.downloadStrategy(strategy.id)
    strategy.downloadCount++
    ElMessage.success('策略已添加到我的策略')
    
    // 跳转到策略详情页面
    router.push(`/strategy/detail/${strategy.id}`)
  } catch (error) {
    ElMessage.error('下载策略失败')
  }
}

// 初始化
onMounted(async () => {
  await Promise.all([
    loadStrategies(),
    loadFeaturedStrategies()
  ])
})
</script>

<style scoped>
.strategy-hub {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.hub-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 32px;
  padding: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
}

.header-content h1 {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
}

.header-content p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.search-section {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.search-bar .el-input {
  flex: 1;
}

.filter-bar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.featured-section {
  margin-bottom: 32px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 20px 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.result-count {
  color: #666;
  font-weight: normal;
  font-size: 14px;
}

.featured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.featured-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s ease;
}

.featured-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.strategy-name {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.strategy-author {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.strategy-description {
  margin: 0 0 16px 0;
  color: #666;
  line-height: 1.6;
}

.strategy-metrics {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.metric {
  text-align: center;
}

.metric-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.metric-value {
  display: block;
  font-size: 16px;
  font-weight: 600;
}

.profit { color: #52c41a; }
.loss { color: #ff4d4f; }

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.strategy-stats {
  display: flex;
  gap: 16px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.strategies-section {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.strategies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.strategies-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.strategy-list-item {
  display: flex;
  padding: 20px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.strategy-list-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.item-left {
  flex: 1;
  margin-right: 20px;
}

.strategy-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.item-right {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  align-items: flex-end;
  min-width: 200px;
}

.strategy-performance {
  display: flex;
  gap: 20px;
  margin-bottom: 12px;
}

.perf-item {
  text-align: center;
}

.perf-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.perf-value {
  display: block;
  font-size: 14px;
  font-weight: 600;
}

.strategy-actions {
  display: flex;
  gap: 8px;
}

.loading-container {
  padding: 40px 0;
}

.empty-state {
  padding: 60px 0;
  text-align: center;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e8e8e8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .strategy-hub {
    padding: 16px;
  }
  
  .hub-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .search-bar {
    flex-direction: column;
  }
  
  .filter-bar {
    gap: 8px;
  }
  
  .featured-grid {
    grid-template-columns: 1fr;
  }
  
  .strategies-grid {
    grid-template-columns: 1fr;
  }
  
  .strategy-list-item {
    flex-direction: column;
    gap: 16px;
  }
  
  .item-right {
    align-items: flex-start;
    min-width: auto;
  }
  
  .strategy-performance {
    justify-content: flex-start;
  }
}
</style> 