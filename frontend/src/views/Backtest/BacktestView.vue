<template>
  <div class="backtest-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1>回测分析</h1>
          <p>策略历史数据回测与性能评估</p>
        </div>
        <div class="action-section">
          <el-button type="primary" @click="openCreateDialog">
            <el-icon><Plus /></el-icon>
            新建回测
          </el-button>
          <el-button @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="16">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon color="#409EFF"><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ totalBacktests }}</div>
              <div class="stat-label">总回测数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon color="#67C23A"><SuccessFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ successfulBacktests }}</div>
              <div class="stat-label">成功回测</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon color="#E6A23C"><Clock /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ runningBacktests }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon">
              <el-icon color="#F56C6C"><Trophy /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatPercent(bestReturn) }}</div>
              <div class="stat-label">最佳收益</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区 -->
    <div class="main-content">
      <el-row :gutter="16">
        <!-- 左侧：回测列表 -->
        <el-col :span="16">
          <div class="content-card">
            <div class="card-header">
              <h3>回测列表</h3>
              <div class="header-actions">
                <el-input
                  v-model="searchQuery"
                  placeholder="搜索回测..."
                  style="width: 200px"
                  clearable
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
                
                <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 120px">
                  <el-option label="全部" value="" />
                  <el-option label="运行中" value="running" />
                  <el-option label="已完成" value="completed" />
                  <el-option label="失败" value="failed" />
                </el-select>
              </div>
            </div>
            
            <div class="backtest-list">
              <el-table
                :data="filteredBacktests"
                v-loading="loading"
                @row-click="handleRowClick"
                row-class-name="backtest-row"
              >
                <el-table-column prop="name" label="回测名称" min-width="150">
                  <template #default="{ row }">
                    <div class="backtest-name">
                      <span class="name">{{ row.name }}</span>
                      <el-tag v-if="row.isFavorite" type="warning" size="small">收藏</el-tag>
                    </div>
                  </template>
                </el-table-column>
                
                <el-table-column prop="strategy" label="策略" width="120" />
                
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getStatusType(row.status)">
                      {{ getStatusText(row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                
                <el-table-column prop="totalReturn" label="总收益" width="100">
                  <template #default="{ row }">
                    <span :class="getPriceClass(row.totalReturn)">
                      {{ formatPercent(row.totalReturn) }}
                    </span>
                  </template>
                </el-table-column>
                
                <el-table-column prop="sharpeRatio" label="夏普比率" width="100">
                  <template #default="{ row }">
                    {{ formatNumber(row.sharpeRatio, 2) }}
                  </template>
                </el-table-column>
                
                <el-table-column prop="maxDrawdown" label="最大回撤" width="100">
                  <template #default="{ row }">
                    <span class="price-down">
                      {{ formatPercent(row.maxDrawdown) }}
                    </span>
                  </template>
                </el-table-column>
                
                <el-table-column prop="duration" label="时间周期" width="120">
                  <template #default="{ row }">
                    {{ formatDateRange(row.startDate, row.endDate) }}
                  </template>
                </el-table-column>
                
                <el-table-column prop="createTime" label="创建时间" width="120">
                  <template #default="{ row }">
                    {{ formatTime(row.createTime) }}
                  </template>
                </el-table-column>
                
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button-group>
                      <el-button
                        size="small"
                        @click.stop="viewBacktest(row)"
                        :disabled="row.status !== 'completed'"
                      >
                        查看
                      </el-button>
                      <el-dropdown @command="handleCommand" trigger="click">
                        <el-button size="small">
                          更多<el-icon><ArrowDown /></el-icon>
                        </el-button>
                        <template #dropdown>
                          <el-dropdown-menu>
                            <el-dropdown-item 
                              :command="{ action: 'clone', row }"
                              :disabled="row.status !== 'completed'"
                            >
                              克隆
                            </el-dropdown-item>
                            <el-dropdown-item 
                              :command="{ action: 'favorite', row }"
                            >
                              {{ row.isFavorite ? '取消收藏' : '收藏' }}
                            </el-dropdown-item>
                            <el-dropdown-item 
                              :command="{ action: 'export', row }"
                              :disabled="row.status !== 'completed'"
                            >
                              导出
                            </el-dropdown-item>
                            <el-dropdown-item 
                              :command="{ action: 'delete', row }"
                              divided
                            >
                              删除
                            </el-dropdown-item>
                          </el-dropdown-menu>
                        </template>
                      </el-dropdown>
                    </el-button-group>
                  </template>
                </el-table-column>
              </el-table>
              
              <!-- 分页 -->
              <div class="pagination">
                <el-pagination
                  v-model:current-page="currentPage"
                  v-model:page-size="pageSize"
                  :total="totalBacktests"
                  :page-sizes="[10, 20, 50, 100]"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="handleSizeChange"
                  @current-change="handleCurrentChange"
                />
              </div>
            </div>
          </div>
        </el-col>
        
        <!-- 右侧：快速信息 -->
        <el-col :span="8">
          <div class="content-card">
            <div class="card-header">
              <h3>快速操作</h3>
            </div>
            
            <div class="quick-actions">
              <!-- 快速回测 -->
              <div class="action-item">
                <h4>快速回测</h4>
                <p>使用预设参数快速创建回测</p>
                <el-button type="primary" size="small" @click="quickBacktest">
                  开始快速回测
                </el-button>
              </div>
              
              <!-- 策略对比 -->
              <div class="action-item">
                <h4>策略对比</h4>
                <p>对比多个策略的回测结果</p>
                <el-button size="small" @click="compareStrategies">
                  策略对比
                </el-button>
              </div>
              
              <!-- 参数优化 -->
              <div class="action-item">
                <h4>参数优化</h4>
                <p>自动寻找最优策略参数</p>
                <el-button size="small" @click="optimizeParameters">
                  参数优化
                </el-button>
              </div>
            </div>
          </div>
          
          <!-- 最近回测 -->
          <div class="content-card" style="margin-top: 16px;">
            <div class="card-header">
              <h3>最近回测</h3>
            </div>
            
            <div class="recent-backtests">
              <div
                v-for="backtest in recentBacktests"
                :key="backtest.id"
                class="recent-item"
                @click="viewBacktest(backtest)"
              >
                <div class="item-header">
                  <span class="item-name">{{ backtest.name }}</span>
                  <el-tag :type="getStatusType(backtest.status)" size="small">
                    {{ getStatusText(backtest.status) }}
                  </el-tag>
                </div>
                <div class="item-content">
                  <div class="item-row">
                    <span>收益率:</span>
                    <span :class="getPriceClass(backtest.totalReturn)">
                      {{ formatPercent(backtest.totalReturn) }}
                    </span>
                  </div>
                  <div class="item-row">
                    <span>夏普比率:</span>
                    <span>{{ formatNumber(backtest.sharpeRatio, 2) }}</span>
                  </div>
                </div>
                <div class="item-time">
                  {{ formatTime(backtest.createTime) }}
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 创建回测对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建回测"
      width="800px"
      :close-on-click-modal="false"
    >
      <BacktestForm
        ref="backtestFormRef"
        @submit="handleCreateSubmit"
        @cancel="createDialogVisible = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Plus, 
  Refresh, 
  Search, 
  ArrowDown,
  TrendCharts,
  SuccessFilled,
  Clock,
  Trophy
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useBacktestStore } from '@/stores/modules/backtest'
import { formatPercent, formatNumber, formatTime } from '@/utils/formatters'
import BacktestForm from '@/components/backtest/BacktestForm.vue'

// Router
const router = useRouter()

// Store
const backtestStore = useBacktestStore()

// 响应式状态
const loading = ref(false)
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const createDialogVisible = ref(false)
const backtestFormRef = ref()

// 模拟数据
const totalBacktests = ref(156)
const successfulBacktests = ref(142)
const runningBacktests = ref(3)
const bestReturn = ref(0.342)

// 计算属性
const filteredBacktests = computed(() => {
  let backtests = backtestStore.backtests

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    backtests = backtests.filter(backtest => 
      backtest.name.toLowerCase().includes(query) ||
      backtest.strategy.toLowerCase().includes(query)
    )
  }

  // 状态过滤
  if (statusFilter.value) {
    backtests = backtests.filter(backtest => 
      backtest.status === statusFilter.value
    )
  }

  return backtests
})

const recentBacktests = computed(() => {
  return backtestStore.backtests
    .filter(b => b.status === 'completed')
    .sort((a, b) => b.createTime - a.createTime)
    .slice(0, 5)
})

// 方法
const refreshData = async () => {
  try {
    loading.value = true
    await backtestStore.fetchBacktests()
    ElMessage.success('数据刷新成功')
  } catch {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  createDialogVisible.value = true
}

const handleCreateSubmit = async (formData: Record<string, unknown>) => {
  try {
    await backtestStore.createBacktest(formData)
    ElMessage.success('回测创建成功')
    createDialogVisible.value = false
    await refreshData()
  } catch (error) {
    console.error('创建回测失败:', error)
    ElMessage.error('创建回测失败')
  }
}

const handleRowClick = (row: { status: string; [key: string]: unknown }) => {
  if (row.status === 'completed') {
    viewBacktest(row)
  }
}

const viewBacktest = (backtest: { id: string; [key: string]: unknown }) => {
  router.push(`/backtest/detail/${backtest.id}`)
}

const handleCommand = async (command: { action: string; row: { id: string; [key: string]: unknown } }) => {
  const { action, row } = command

  switch (action) {
    case 'clone':
      await cloneBacktest(row)
      break
    case 'favorite':
      await toggleFavorite(row)
      break
    case 'export':
      await exportBacktest(row)
      break
    case 'delete':
      await deleteBacktest(row)
      break
  }
}

const cloneBacktest = async (backtest: { id: string; [key: string]: unknown }) => {
  try {
    await backtestStore.cloneBacktest(backtest.id)
    ElMessage.success('回测克隆成功')
    await refreshData()
  } catch {
    ElMessage.error('回测克隆失败')
  }
}

const toggleFavorite = async (backtest: { id: string; isFavorite?: boolean; [key: string]: unknown }) => {
  try {
    await backtestStore.toggleFavorite(backtest.id)
    ElMessage.success(backtest.isFavorite ? '取消收藏成功' : '收藏成功')
    await refreshData()
  } catch {
    ElMessage.error('操作失败')
  }
}

const exportBacktest = async (backtest: { id: string; [key: string]: unknown }) => {
  try {
    await backtestStore.exportBacktest(backtest.id)
    ElMessage.success('导出成功')
  } catch {
    ElMessage.error('导出失败')
  }
}

const deleteBacktest = async (backtest: { id: string; name: string; [key: string]: unknown }) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除回测 "${backtest.name}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await backtestStore.deleteBacktest(backtest.id)
    ElMessage.success('删除成功')
    await refreshData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const quickBacktest = () => {
  router.push('/backtest/quick')
}

const compareStrategies = () => {
  router.push('/backtest/compare')
}

const optimizeParameters = () => {
  router.push('/backtest/optimize')
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
}

const getStatusType = (status: string) => {
  const types: Record<string, string> = {
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    pending: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    pending: '等待中'
  }
  return texts[status] || status
}

const getPriceClass = (value: number) => {
  if (value > 0) return 'price-up'
  if (value < 0) return 'price-down'
  return 'price-neutral'
}

const formatDateRange = (start: number, end: number) => {
  const startDate = new Date(start).toLocaleDateString()
  const endDate = new Date(end).toLocaleDateString()
  return `${startDate} - ${endDate}`
}

// 生命周期
onMounted(async () => {
  await refreshData()
})
</script>

<style scoped>
.backtest-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.title-section h1 {
  margin: 0 0 4px 0;
  font-size: 24px;
  color: #333;
}

.title-section p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.action-section {
  display: flex;
  gap: 12px;
}

.stats-section {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  margin-right: 16px;
}

.stat-icon .el-icon {
  font-size: 32px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.main-content {
  margin-bottom: 20px;
}

.content-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e8e8e8;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.backtest-list {
  padding: 0;
}

.backtest-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.name {
  font-weight: 500;
}

.backtest-row {
  cursor: pointer;
}

.backtest-row:hover {
  background-color: #f5f7fa;
}

.pagination {
  padding: 16px 20px;
  display: flex;
  justify-content: center;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.price-neutral {
  color: #909399;
}

.quick-actions {
  padding: 20px;
}

.action-item {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.action-item:last-child {
  margin-bottom: 0;
  border-bottom: none;
}

.action-item h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #333;
}

.action-item p {
  margin: 0 0 8px 0;
  font-size: 12px;
  color: #666;
}

.recent-backtests {
  padding: 0 20px 20px;
}

.recent-item {
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.recent-item:hover {
  background-color: #f5f7fa;
}

.recent-item:last-child {
  margin-bottom: 0;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.item-name {
  font-weight: 500;
  font-size: 14px;
  color: #333;
}

.item-content {
  margin-bottom: 8px;
}

.item-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 4px;
}

.item-row span:first-child {
  color: #666;
}

.item-time {
  font-size: 11px;
  color: #999;
}

@media (max-width: 768px) {
  .backtest-page {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .action-section {
    width: 100%;
    justify-content: flex-end;
  }
  
  .main-content .el-col {
    margin-bottom: 16px;
  }
}
</style> 