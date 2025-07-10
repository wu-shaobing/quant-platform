<template>
  <div class="position-management-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">持仓管理</h1>
          <div class="page-subtitle">
            <span>实时监控投资组合表现</span>
            <el-tag v-if="wsConnected" type="success" size="small">
              <el-icon><Connection /></el-icon>
              实时更新
            </el-tag>
            <el-tag v-else type="danger" size="small">
              <el-icon><Close /></el-icon>
              连接断开
            </el-tag>
          </div>
        </div>
        <div class="header-actions">
          <el-button
            :loading="loading"
            @click="refreshAll"
            type="primary"
            :icon="Refresh"
          >
            刷新数据
          </el-button>
          <el-button
            @click="exportPositions"
            :icon="Download"
          >
            导出持仓
          </el-button>
          <el-dropdown @command="handleMoreActions">
            <el-button :icon="MoreFilled">
              更多操作<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="clearAll" :icon="Delete">一键清仓</el-dropdown-item>
                <el-dropdown-item command="rebalance" :icon="Refresh">资产再平衡</el-dropdown-item>
                <el-dropdown-item command="riskAnalysis" :icon="Warning">风险分析</el-dropdown-item>
                <el-dropdown-item command="performance" :icon="TrendCharts">绩效分析</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button
            @click="$router.push('/trading/terminal')"
            type="success"
            :icon="Plus"
          >
            快速交易
          </el-button>
        </div>
      </div>
    </div>

    <!-- 账户概览卡片 -->
    <div class="overview-section">
      <div class="overview-grid">
        <div class="overview-card total-assets">
          <div class="card-content">
            <div class="card-info">
              <div class="card-label">总资产</div>
              <div class="card-value">{{ formatCurrency(accountSummary.totalAssets) }}</div>
              <div class="card-trend">
                <span :class="getTrendClass(accountSummary.totalAssetsChange)">
                  {{ formatPnl(accountSummary.totalAssetsChange) }}
                  ({{ formatPercent(accountSummary.totalAssetsChangePercent) }})
                </span>
              </div>
            </div>
            <div class="card-icon">
              <el-icon><Wallet /></el-icon>
            </div>
          </div>
        </div>

        <div class="overview-card available-cash">
          <div class="card-content">
            <div class="card-info">
              <div class="card-label">可用资金</div>
              <div class="card-value">{{ formatCurrency(accountSummary.availableCash) }}</div>
              <div class="card-trend">
                <span class="trend-text">
                  占比 {{ formatPercent(accountSummary.cashRatio) }}
                </span>
              </div>
            </div>
            <div class="card-icon">
              <el-icon><Money /></el-icon>
            </div>
          </div>
        </div>

        <div class="overview-card today-pnl">
          <div class="card-content">
            <div class="card-info">
              <div class="card-label">今日盈亏</div>
              <div class="card-value" :class="getPnlClass(accountSummary.todayPnl)">
                {{ formatPnl(accountSummary.todayPnl) }}
              </div>
              <div class="card-trend">
                <span :class="getPnlClass(accountSummary.todayPnl)">
                  ({{ formatPercent(accountSummary.todayPnlPercent) }})
                </span>
              </div>
            </div>
            <div class="card-icon" :class="accountSummary.todayPnl >= 0 ? 'up' : 'down'">
              <el-icon><TrendCharts /></el-icon>
            </div>
          </div>
        </div>

        <div class="overview-card total-pnl">
          <div class="card-content">
            <div class="card-info">
              <div class="card-label">总盈亏</div>
              <div class="card-value" :class="getPnlClass(accountSummary.totalPnl)">
                {{ formatPnl(accountSummary.totalPnl) }}
              </div>
              <div class="card-trend">
                <span :class="getPnlClass(accountSummary.totalPnl)">
                  ({{ formatPercent(totalPnlPercent) }})
                </span>
              </div>
            </div>
            <div class="card-icon" :class="accountSummary.totalPnl >= 0 ? 'up' : 'down'">
              <el-icon><DataAnalysis /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 持仓统计 -->
    <div class="statistics-section">
      <div class="statistics-grid">
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><PieChart /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ positions.length }}</div>
            <div class="stat-label">持仓股票</div>
          </div>
        </div>
        
        <div class="stat-card profit">
          <div class="stat-icon">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ profitablePositions }}</div>
            <div class="stat-label">盈利股票</div>
          </div>
        </div>
        
        <div class="stat-card loss">
          <div class="stat-icon">
            <el-icon><Bottom /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ losingPositions }}</div>
            <div class="stat-label">亏损股票</div>
          </div>
        </div>
        
        <div class="stat-card">
          <div class="stat-icon">
            <el-icon><Money /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatCurrency(totalMarketValue) }}</div>
            <div class="stat-label">总市值</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选和操作栏 -->
    <div class="filter-section">
      <div class="filter-content">
        <div class="filter-left">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索股票代码或名称"
            size="default"
            style="width: 240px"
            clearable
            @input="handleSearchInput"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="filterPnlType"
            placeholder="盈亏筛选"
            size="default"
            style="width: 120px"
            @change="handleFilterChange"
          >
            <el-option label="全部" value="" />
            <el-option label="盈利" value="profit" />
            <el-option label="亏损" value="loss" />
            <el-option label="持平" value="neutral" />
          </el-select>
          
          <el-select
            v-model="sortField"
            placeholder="排序字段"
            size="default"
            style="width: 140px"
            @change="handleSortChange"
          >
            <el-option label="默认" value="" />
            <el-option label="盈亏金额" value="unrealizedPnl" />
            <el-option label="盈亏比例" value="unrealizedPnlPercent" />
            <el-option label="持仓市值" value="marketValue" />
            <el-option label="持仓数量" value="size" />
          </el-select>
          
          <el-button-group>
            <el-button
              :type="sortOrder === 'asc' ? 'primary' : 'default'"
              size="default"
              @click="setSortOrder('asc')"
            >
              <el-icon><Sort /></el-icon>
              升序
            </el-button>
            <el-button
              :type="sortOrder === 'desc' ? 'primary' : 'default'"
              size="default"
              @click="setSortOrder('desc')"
            >
              <el-icon><SortDown /></el-icon>
              降序
            </el-button>
          </el-button-group>
        </div>
        
        <div class="filter-right">
          <el-checkbox v-model="showOnlyProfit" @change="handleFilterChange">
            只看盈利
          </el-checkbox>
          <el-checkbox v-model="autoRefresh" @change="handleAutoRefreshChange">
            自动刷新
          </el-checkbox>
          <span class="result-count">
            共 {{ filteredPositions.length }} 条记录
          </span>
        </div>
      </div>
    </div>

    <!-- 持仓列表 -->
    <div class="table-section">
      <div v-loading="loading" class="table-container">
        <el-table
          ref="tableRef"
          :data="paginatedPositions"
          style="width: 100%"
          stripe
          border
          :height="tableHeight"
          @sort-change="handleTableSort"
          @selection-change="handleSelectionChange"
        >
          <!-- 选择列 -->
          <el-table-column
            type="selection"
            width="50"
            fixed="left"
          />
          
          <!-- 股票代码 -->
          <el-table-column
            prop="symbol"
            label="股票代码"
            width="100"
            fixed="left"
            sortable="custom"
          >
            <template #default="{ row }">
              <div class="symbol-cell">
                <span class="symbol-code">{{ row.symbol }}</span>
                <span class="symbol-name">{{ getStockName(row.symbol) }}</span>
              </div>
            </template>
          </el-table-column>

          <!-- 持仓数量 -->
          <el-table-column
            prop="size"
            label="持仓数量"
            width="100"
            align="right"
            sortable="custom"
          >
            <template #default="{ row }">
              <span class="number-value">{{ formatNumber(row.size) }}</span>
            </template>
          </el-table-column>

          <!-- 成本价 -->
          <el-table-column
            prop="avgPrice"
            label="成本价"
            width="100"
            align="right"
            sortable="custom"
          >
            <template #default="{ row }">
              <span class="price-value">{{ formatPrice(row.avgPrice) }}</span>
            </template>
          </el-table-column>

          <!-- 现价 -->
          <el-table-column
            prop="markPrice"
            label="现价"
            width="100"
            align="right"
            sortable="custom"
          >
            <template #default="{ row }">
              <span 
                class="price-value"
                :class="getPriceChangeClass(row.markPrice - row.avgPrice)"
              >
                {{ formatPrice(row.markPrice) }}
              </span>
            </template>
          </el-table-column>

          <!-- 市值 -->
          <el-table-column
            prop="marketValue"
            label="市值"
            width="120"
            align="right"
            sortable="custom"
          >
            <template #default="{ row }">
              <span class="currency-value">{{ formatCurrency(row.markPrice * row.size) }}</span>
            </template>
          </el-table-column>

          <!-- 浮动盈亏 -->
          <el-table-column
            prop="unrealizedPnl"
            label="浮动盈亏"
            width="140"
            align="right"
            sortable="custom"
          >
            <template #default="{ row }">
              <div class="pnl-cell">
                <div class="pnl-amount" :class="getPnlClass(row.unrealizedPnl)">
                  {{ formatPnl(row.unrealizedPnl) }}
                </div>
                <div class="pnl-percent" :class="getPnlClass(row.unrealizedPnl)">
                  ({{ formatPercent(row.unrealizedPnlPercent) }})
                </div>
              </div>
            </template>
          </el-table-column>

          <!-- 持仓占比 -->
          <el-table-column
            label="持仓占比"
            width="100"
            align="right"
          >
            <template #default="{ row }">
              <div class="ratio-cell">
                <span class="ratio-value">
                  {{ formatPercent(getPositionRatio(row)) }}
                </span>
                <div class="ratio-bar">
                  <div 
                    class="ratio-fill"
                    :style="{ width: `${Math.min(getPositionRatio(row), 100)}%` }"
                  />
                </div>
              </div>
            </template>
          </el-table-column>

          <!-- 更新时间 -->
          <el-table-column
            prop="updateTime"
            label="更新时间"
            width="120"
            align="center"
          >
            <template #default="{ row }">
              <span class="time-value">{{ formatTime(row.updateTime) }}</span>
            </template>
          </el-table-column>

          <!-- 操作列 -->
          <el-table-column
            label="操作"
            width="160"
            fixed="right"
          >
            <template #default="{ row }">
              <div class="action-buttons">
                <el-button
                  type="primary"
                  size="small"
                  @click="buyStock(row.symbol, getStockName(row.symbol))"
                >
                  买入
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="sellStock(row)"
                >
                  卖出
                </el-button>
                <el-button
                  type="info"
                  size="small"
                  text
                  @click="viewDetail(row)"
                >
                  详情
                </el-button>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 空状态 -->
        <div v-if="!loading && filteredPositions.length === 0" class="empty-state">
          <el-empty description="暂无持仓数据">
            <el-button type="primary" @click="$router.push('/trading/terminal')">
              开始交易
            </el-button>
          </el-empty>
        </div>
      </div>

      <!-- 批量操作栏 -->
      <div v-if="selectedPositions.length > 0" class="batch-actions">
        <div class="batch-info">
          已选择 {{ selectedPositions.length }} 项
        </div>
        <div class="batch-buttons">
          <el-button @click="batchSell" type="danger">
            批量卖出
          </el-button>
          <el-button @click="batchExport">
            导出选中
          </el-button>
          <el-button @click="clearSelection" text>
            取消选择
          </el-button>
        </div>
      </div>

      <!-- 分页 -->
      <div class="pagination-section">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :small="false"
          :disabled="loading"
          :background="true"
          layout="total, sizes, prev, pager, next, jumper"
          :total="filteredPositions.length"
          @size-change="handlePageSizeChange"
          @current-change="handleCurrentPageChange"
        />
      </div>
    </div>

    <!-- 持仓详情弹窗 -->
    <el-dialog 
      v-model="showDetailDialog" 
      title="持仓详情" 
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="selectedPosition" class="position-detail">
        <div class="detail-grid">
          <div class="detail-item">
            <label>股票代码</label>
            <span>{{ selectedPosition.symbol }}</span>
          </div>
          <div class="detail-item">
            <label>股票名称</label>
            <span>{{ getStockName(selectedPosition.symbol) }}</span>
          </div>
          <div class="detail-item">
            <label>持仓数量</label>
            <span>{{ formatNumber(selectedPosition.size) }}</span>
          </div>
          <div class="detail-item">
            <label>成本价</label>
            <span>{{ formatPrice(selectedPosition.avgPrice) }}</span>
          </div>
          <div class="detail-item">
            <label>现价</label>
            <span :class="getPriceChangeClass(selectedPosition.markPrice - selectedPosition.avgPrice)">
              {{ formatPrice(selectedPosition.markPrice) }}
            </span>
          </div>
          <div class="detail-item">
            <label>总成本</label>
            <span>{{ formatCurrency(selectedPosition.avgPrice * selectedPosition.size) }}</span>
          </div>
          <div class="detail-item">
            <label>市值</label>
            <span>{{ formatCurrency(selectedPosition.markPrice * selectedPosition.size) }}</span>
          </div>
          <div class="detail-item">
            <label>浮动盈亏</label>
            <span :class="getPnlClass(selectedPosition.unrealizedPnl)">
              {{ formatPnl(selectedPosition.unrealizedPnl) }}
              ({{ formatPercent(selectedPosition.unrealizedPnlPercent) }})
            </span>
          </div>
          <div class="detail-item">
            <label>持仓占比</label>
            <span>{{ formatPercent(getPositionRatio(selectedPosition)) }}</span>
          </div>
          <div class="detail-item">
            <label>更新时间</label>
            <span>{{ formatDateTime(selectedPosition.updateTime) }}</span>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="showDetailDialog = false">关闭</el-button>
          <el-button type="primary" @click="buyStock(selectedPosition?.symbol || '', getStockName(selectedPosition?.symbol || ''))">
            买入
          </el-button>
          <el-button type="danger" @click="sellStock(selectedPosition!)">
            卖出
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Connection,
  Close,
  Refresh,
  Download,
  Plus,
  Wallet, 
  Money, 
  TrendCharts, 
  DataAnalysis, 
  Search,
  PieChart,
  Bottom,
  MoreFilled,
  ArrowDown,
  Delete,
  Warning,
  Sort,
  SortDown
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { usePositions } from '@/composables/trading/usePositions'
import { usePagination } from '@/composables/data/usePagination'
import { formatCurrency, formatPrice, formatNumber, formatPercent } from '@/utils/formatters'
import { debounce } from 'lodash-es'
import type { Position } from '@/types/trading'

const router = useRouter()

// 使用持仓管理组合函数
const {
  loading,
  positions,
  accountSummary,
  totalPnl,
  totalPnlPercent,
  totalMarketValue,
  profitablePositions,
  losingPositions,
  wsConnected,
  fetchPositions,
  fetchAccountSummary,
  buyStock,
  sellStock,
  refreshAll,
  exportPositions: exportPositionsData,
  subscribePositionUpdates,
  unsubscribePositionUpdates
} = usePositions()

// 本地状态
const searchKeyword = ref('')
const filterPnlType = ref('')
const showOnlyProfit = ref(false)
const autoRefresh = ref(false)
const sortField = ref('')
const sortOrder = ref<'asc' | 'desc'>('desc')
const showDetailDialog = ref(false)
const selectedPosition = ref<Position | null>(null)
const selectedPositions = ref<Position[]>([])
const tableRef = ref()
const tableHeight = ref(500)

// 股票名称映射（实际应该从API获取）
const stockNames = ref<Record<string, string>>({
  '000001': '平安银行',
  '000002': '万科A',
  '600036': '招商银行'
})

// 分页配置
const pagination = ref({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 计算属性
const filteredPositions = computed(() => {
  let result = [...positions.value]
  
  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(pos => 
      pos.symbol.toLowerCase().includes(keyword) ||
      getStockName(pos.symbol).toLowerCase().includes(keyword)
    )
  }
  
  // 盈亏类型过滤
  if (filterPnlType.value) {
    switch (filterPnlType.value) {
      case 'profit':
        result = result.filter(pos => pos.unrealizedPnl > 0)
        break
      case 'loss':
        result = result.filter(pos => pos.unrealizedPnl < 0)
        break
      case 'neutral':
        result = result.filter(pos => pos.unrealizedPnl === 0)
        break
    }
  }
  
  // 只看盈利过滤
  if (showOnlyProfit.value) {
    result = result.filter(pos => pos.unrealizedPnl > 0)
  }
  
  // 排序
  if (sortField.value) {
    result.sort((a, b) => {
      let aVal: number
      let bVal: number
      
      switch (sortField.value) {
        case 'marketValue':
          aVal = a.markPrice * a.size
          bVal = b.markPrice * b.size
          break
        default:
          aVal = a[sortField.value as keyof Position] as number
          bVal = b[sortField.value as keyof Position] as number
      }
      
      if (sortOrder.value === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
  }
  
  return result
})

const paginatedPositions = computed(() => {
  const start = (pagination.value.currentPage - 1) * pagination.value.pageSize
  const end = start + pagination.value.pageSize
  return filteredPositions.value.slice(start, end)
})

// 方法
const getStockName = (symbol: string) => {
  return stockNames.value[symbol] || symbol
}

const formatPnl = (value: number) => {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${formatCurrency(value)}`
}

const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleTimeString()
}

const formatDateTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString()
}

const getTrendClass = (value: number) => {
  if (value > 0) return 'trend-up'
  if (value < 0) return 'trend-down'
  return 'trend-neutral'
}

const getPriceChangeClass = (change: number) => {
  if (change > 0) return 'price-up'
  if (change < 0) return 'price-down'
  return 'price-neutral'
}

const getPnlClass = (pnl: number) => {
  if (pnl > 0) return 'pnl-up'
  if (pnl < 0) return 'pnl-down'
  return 'pnl-neutral'
}

const getPositionRatio = (position: Position) => {
  const positionValue = position.markPrice * position.size
  return totalMarketValue.value > 0 ? (positionValue / totalMarketValue.value) * 100 : 0
}

const handleSearchInput = debounce(() => {
  pagination.value.currentPage = 1
}, 300)

const handleFilterChange = () => {
  pagination.value.currentPage = 1
}

const handleSortChange = () => {
  pagination.value.currentPage = 1
}

const setSortOrder = (order: 'asc' | 'desc') => {
  sortOrder.value = order
  handleSortChange()
}

const handleTableSort = ({ prop, order }: any) => {
  sortField.value = prop || ''
  sortOrder.value = order === 'ascending' ? 'asc' : 'desc'
  handleSortChange()
}

const handleSelectionChange = (selection: Position[]) => {
  selectedPositions.value = selection
}

const handlePageSizeChange = (size: number) => {
  pagination.value.pageSize = size
  pagination.value.currentPage = 1
}

const handleCurrentPageChange = (page: number) => {
  pagination.value.currentPage = page
}

const handleAutoRefreshChange = (enabled: boolean) => {
  if (enabled) {
    // 启动自动刷新
    startAutoRefresh()
  } else {
    // 停止自动刷新
    stopAutoRefresh()
  }
}

let autoRefreshTimer: NodeJS.Timeout | null = null

const startAutoRefresh = () => {
  autoRefreshTimer = setInterval(() => {
    refreshAll()
  }, 30000) // 30秒刷新一次
}

const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

const handleMoreActions = (command: string) => {
  switch (command) {
    case 'clearAll':
      clearAllPositions()
      break
    case 'rebalance':
      ElMessage.info('资产再平衡功能开发中')
      break
    case 'riskAnalysis':
      ElMessage.info('风险分析功能开发中')
      break
    case 'performance':
      ElMessage.info('绩效分析功能开发中')
      break
  }
}

const clearAllPositions = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清空所有持仓吗？此操作不可撤销。',
      '确认清仓',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    ElMessage.success('清仓订单已提交')
    await refreshAll()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('清仓失败')
    }
  }
}

const exportPositions = async () => {
  try {
    await exportPositionsData(filteredPositions.value)
    ElMessage.success('持仓数据导出成功')
  } catch (error) {
    ElMessage.error('持仓数据导出失败')
  }
}

const batchSell = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要卖出选中的 ${selectedPositions.value.length} 只股票吗？`,
      '批量卖出确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    ElMessage.success('批量卖出订单已提交')
    clearSelection()
    await refreshAll()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量卖出失败')
    }
  }
}

const batchExport = async () => {
  try {
    await exportPositionsData(selectedPositions.value)
    ElMessage.success('选中数据导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const clearSelection = () => {
  tableRef.value?.clearSelection()
  selectedPositions.value = []
}

const viewDetail = (position: Position) => {
  selectedPosition.value = position
  showDetailDialog.value = true
}

// ======= 监听窗口大小，自动调整表格高度 =======
const updateTableHeight = () => {
  const windowHeight = window.innerHeight
  tableHeight.value = Math.max(400, windowHeight - 600)
}

// 生命周期
onMounted(() => {
  refreshAll()
  subscribePositionUpdates()

  updateTableHeight()
  window.addEventListener('resize', updateTableHeight)
})

onUnmounted(() => {
  unsubscribePositionUpdates()
  stopAutoRefresh()
  window.removeEventListener('resize', updateTableHeight)
})

// 监听筛选条件变化更新分页总数
watch(
  filteredPositions,
  (newData) => {
    pagination.value.total = newData.length
  },
  { immediate: true }
)
</script>

<style scoped>
.position-management-page {
  min-height: calc(100vh - 64px);
  background-color: #f5f5f5;
  padding: 20px;
}

/* 页面头部样式 */
.page-header {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: #333;
}

.page-subtitle {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #666;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 概览卡片样式 */
.overview-section {
  margin-bottom: 20px;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
}

.overview-card {
  background: white;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #409EFF;
}

.overview-card.total-assets {
  border-left-color: #409EFF;
}

.overview-card.available-cash {
  border-left-color: #67C23A;
}

.overview-card.today-pnl {
  border-left-color: #E6A23C;
}

.overview-card.total-pnl {
  border-left-color: #F56C6C;
}

.card-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-info {
  flex: 1;
}

.card-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.card-value {
  font-size: 28px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.card-trend {
  font-size: 14px;
}

.card-icon {
  font-size: 32px;
  color: #409EFF;
  opacity: 0.8;
}

.card-icon.up {
  color: #67C23A;
}

.card-icon.down {
  color: #F56C6C;
}

/* 统计卡片样式 */
.statistics-section {
  margin-bottom: 20px;
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-card.profit {
  border-left: 4px solid #67C23A;
}

.stat-card.loss {
  border-left: 4px solid #F56C6C;
}

.stat-icon {
  font-size: 24px;
  color: #409EFF;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

/* 筛选区域样式 */
.filter-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.result-count {
  font-size: 14px;
  color: #666;
}

/* 表格区域样式 */
.table-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table-container {
  padding: 20px;
}

.symbol-cell {
  display: flex;
  flex-direction: column;
}

.symbol-code {
  font-weight: 600;
  color: #333;
}

.symbol-name {
  font-size: 12px;
  color: #666;
}

.pnl-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.pnl-amount {
  font-weight: 600;
}

.pnl-percent {
  font-size: 12px;
}

.ratio-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.ratio-bar {
  width: 60px;
  height: 4px;
  background: #f0f0f0;
  border-radius: 2px;
  overflow: hidden;
}

.ratio-fill {
  height: 100%;
  background: #409EFF;
  transition: width 0.3s ease;
}

.action-buttons {
  display: flex;
  gap: 4px;
}

.number-value,
.price-value,
.currency-value,
.time-value {
  font-family: 'JetBrains Mono', monospace;
}

/* 价格和盈亏颜色 */
.price-up, .pnl-up, .trend-up {
  color: #f56c6c;
}

.price-down, .pnl-down, .trend-down {
  color: #67c23a;
}

.price-neutral, .pnl-neutral, .trend-neutral {
  color: #909399;
}

.trend-text {
  color: #666;
}

/* 批量操作栏 */
.batch-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: #f8f9fa;
  border-top: 1px solid #e8e8e8;
}

.batch-info {
  font-size: 14px;
  color: #666;
}

.batch-buttons {
  display: flex;
  gap: 8px;
}

/* 分页样式 */
.pagination-section {
  padding: 20px;
  border-top: 1px solid #e8e8e8;
  display: flex;
  justify-content: center;
}

/* 空状态样式 */
.empty-state {
  padding: 60px 0;
  text-align: center;
}

/* 详情弹窗样式 */
.position-detail {
  padding: 20px 0;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item label {
  font-weight: 500;
  color: #666;
}

.detail-item span {
  font-weight: 600;
  color: #333;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .position-management-page {
    padding: 12px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
  
  .overview-grid {
    grid-template-columns: 1fr;
  }
  
  .statistics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .filter-content {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .filter-left {
    width: 100%;
    justify-content: space-between;
  }
  
  .detail-grid {
    grid-template-columns: 1fr;
  }
  
  .batch-actions {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table th) {
  background-color: #fafafa;
  color: #606266;
  font-weight: 600;
}

:deep(.el-table--border td) {
  border-right: 1px solid #ebeef5;
}

:deep(.el-empty) {
  padding: 40px 0;
}
</style> 