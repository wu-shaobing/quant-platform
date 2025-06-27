<template>
  <div class="order-management-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">订单管理</h1>
          <div class="page-subtitle">
            <span>实时监控交易订单状态</span>
            <el-tag v-if="wsConnected" type="success" size="small">
              <el-icon><Connection /></el-icon>
              实时连接
            </el-tag>
            <el-tag v-else type="danger" size="small">
              <el-icon><Close /></el-icon>
              连接断开
            </el-tag>
            <el-tag v-if="hasRiskOrders" type="warning" size="small">
              <el-icon><Warning /></el-icon>
              风险提醒
            </el-tag>
          </div>
        </div>
        <div class="header-actions">
          <el-button
            :loading="loading"
            @click="refreshOrders"
            type="primary"
            :icon="Refresh"
          >
            刷新数据
          </el-button>
          <el-button
            @click="exportOrders"
            :icon="Download"
          >
            导出订单
          </el-button>
          <el-dropdown @command="handleMoreActions">
            <el-button :icon="MoreFilled">
              更多操作<el-icon class="el-icon--right"><arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="riskAnalysis" :icon="Warning">风险分析</el-dropdown-item>
                <el-dropdown-item command="performance" :icon="TrendCharts">执行分析</el-dropdown-item>
                <el-dropdown-item command="autoCancel" :icon="Timer">自动撤单</el-dropdown-item>
                <el-dropdown-item command="template" :icon="Document">订单模板</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
          <el-button
            @click="$router.push('/trading/terminal')"
            type="success"
            :icon="Plus"
          >
            新建订单
          </el-button>
        </div>
      </div>
    </div>

    <!-- 实时监控面板 -->
    <div v-if="showMonitorPanel" class="monitor-panel">
      <el-card class="monitor-card">
        <template #header>
          <div class="monitor-header">
            <span>实时监控</span>
            <el-button
              type="text"
              :icon="Close"
              @click="showMonitorPanel = false"
            />
          </div>
        </template>
        <div class="monitor-content">
          <div class="monitor-item">
            <div class="monitor-label">活跃订单</div>
            <div class="monitor-value">{{ activeOrdersCount }}</div>
          </div>
          <div class="monitor-item">
            <div class="monitor-label">平均成交时间</div>
            <div class="monitor-value">{{ avgFillTime }}s</div>
          </div>
          <div class="monitor-item">
            <div class="monitor-label">成交滑点</div>
            <div class="monitor-value" :class="slippageClass">{{ avgSlippage }}%</div>
          </div>
          <div class="monitor-item">
            <div class="monitor-label">风险订单</div>
            <div class="monitor-value risk">{{ riskOrdersCount }}</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 订单统计卡片 -->
    <div class="stats-cards">
      <div class="stats-grid">
        <div class="stat-card pending">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-label">待成交</div>
              <div class="stat-value">{{ orderStats.pending }}</div>
              <div class="stat-trend">
                <span class="trend-text">今日新增 {{ orderStats.todayPending }}</span>
              </div>
            </div>
            <div class="stat-icon">
              <el-icon><Clock /></el-icon>
            </div>
          </div>
          <div class="stat-progress">
            <el-progress
              :percentage="(orderStats.pending / Math.max(orderStats.total, 1)) * 100"
              :stroke-width="3"
              :show-text="false"
              color="#e6a23c"
            />
          </div>
        </div>

        <div class="stat-card filled">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-label">已成交</div>
              <div class="stat-value">{{ orderStats.filled }}</div>
              <div class="stat-trend">
                <span class="trend-text">成交率 {{ orderStats.fillRate }}%</span>
              </div>
            </div>
            <div class="stat-icon">
              <el-icon><Check /></el-icon>
            </div>
          </div>
          <div class="stat-progress">
            <el-progress
              :percentage="orderStats.fillRate"
              :stroke-width="3"
              :show-text="false"
              color="#67c23a"
            />
          </div>
        </div>

        <div class="stat-card partial">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-label">部分成交</div>
              <div class="stat-value">{{ orderStats.partial }}</div>
              <div class="stat-trend">
                <span class="trend-text">平均成交 {{ orderStats.avgFillPercent }}%</span>
              </div>
            </div>
            <div class="stat-icon">
              <el-icon><PieChart /></el-icon>
            </div>
          </div>
          <div class="stat-progress">
            <el-progress
              :percentage="orderStats.avgFillPercent"
              :stroke-width="3"
              :show-text="false"
              color="#409eff"
            />
          </div>
        </div>

        <div class="stat-card cancelled">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-label">已撤销</div>
              <div class="stat-value">{{ orderStats.cancelled }}</div>
              <div class="stat-trend">
                <span class="trend-text">撤单率 {{ orderStats.cancelRate }}%</span>
              </div>
            </div>
            <div class="stat-icon">
              <el-icon><Close /></el-icon>
            </div>
          </div>
          <div class="stat-progress">
            <el-progress
              :percentage="orderStats.cancelRate"
              :stroke-width="3"
              :show-text="false"
              color="#909399"
            />
          </div>
        </div>

        <div class="stat-card performance">
          <div class="stat-content">
            <div class="stat-info">
              <div class="stat-label">执行效率</div>
              <div class="stat-value">{{ orderStats.efficiency }}%</div>
              <div class="stat-trend">
                <span class="trend-text">较昨日 {{ orderStats.efficiencyChange > 0 ? '+' : '' }}{{ orderStats.efficiencyChange }}%</span>
              </div>
            </div>
            <div class="stat-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
          </div>
          <div class="stat-progress">
            <el-progress
              :percentage="orderStats.efficiency"
              :stroke-width="3"
              :show-text="false"
              :color="getEfficiencyColor(orderStats.efficiency)"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-card class="filter-card">
        <div class="filter-content">
          <div class="filter-row">
            <div class="filter-group">
              <label class="filter-label">订单状态</label>
              <el-select
                v-model="filters.status"
                placeholder="全部状态"
                style="width: 140px"
                @change="handleFilterChange"
              >
                <el-option label="全部状态" value="" />
                <el-option
                  v-for="status in orderStatuses"
                  :key="status.value"
                  :label="status.label"
                  :value="status.value"
                />
              </el-select>
            </div>

            <div class="filter-group">
              <label class="filter-label">交易方向</label>
              <el-select
                v-model="filters.side"
                placeholder="全部方向"
                style="width: 120px"
                @change="handleFilterChange"
              >
                <el-option label="全部方向" value="" />
                <el-option label="买入" value="buy" />
                <el-option label="卖出" value="sell" />
              </el-select>
            </div>

            <div class="filter-group">
              <label class="filter-label">订单类型</label>
              <el-select
                v-model="filters.orderType"
                placeholder="全部类型"
                style="width: 120px"
                @change="handleFilterChange"
              >
                <el-option label="全部类型" value="" />
                <el-option label="限价单" value="limit" />
                <el-option label="市价单" value="market" />
                <el-option label="止损单" value="stop" />
                <el-option label="止盈单" value="stop-profit" />
              </el-select>
            </div>

            <div class="filter-group">
              <label class="filter-label">风险等级</label>
              <el-select
                v-model="filters.riskLevel"
                placeholder="全部风险"
                style="width: 120px"
                @change="handleFilterChange"
              >
                <el-option label="全部风险" value="" />
                <el-option label="低风险" value="low" />
                <el-option label="中风险" value="medium" />
                <el-option label="高风险" value="high" />
              </el-select>
            </div>

            <div class="filter-group">
              <label class="filter-label">时间范围</label>
              <el-date-picker
                v-model="filters.dateRange"
                type="datetimerange"
                range-separator="至"
                start-placeholder="开始时间"
                end-placeholder="结束时间"
                format="MM-DD HH:mm"
                value-format="YYYY-MM-DD HH:mm:ss"
                style="width: 280px"
                @change="handleFilterChange"
              />
            </div>

            <div class="filter-group">
              <label class="filter-label">搜索</label>
              <el-input
                v-model="filters.keyword"
                placeholder="股票代码/名称/订单号"
                style="width: 200px"
                clearable
                @input="handleSearchInput"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
          </div>

          <div class="filter-actions">
            <el-button @click="resetFilters" :icon="RefreshLeft">
              重置筛选
            </el-button>
            <el-button @click="showMonitorPanel = !showMonitorPanel" :icon="Monitor">
              {{ showMonitorPanel ? '隐藏' : '显示' }}监控
            </el-button>
            <el-checkbox v-model="autoRefresh" @change="handleAutoRefreshChange">
              自动刷新
            </el-checkbox>
            <el-checkbox v-model="showRiskOnly" @change="handleFilterChange">
              只看风险订单
            </el-checkbox>
            <el-button
              v-if="selectedOrders.length > 0"
              type="danger"
              :icon="Delete"
              @click="batchCancelOrders"
            >
              批量撤单 ({{ selectedOrders.length }})
            </el-button>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 订单列表 -->
    <div class="order-table-section">
      <el-card class="table-card">
        <template #header>
          <div class="table-header">
            <div class="table-title">
              <span>订单列表</span>
              <el-tag size="small">{{ filteredOrders.length }} 条记录</el-tag>
            </div>
            <div class="table-actions">
              <el-button-group>
                <el-button
                  v-for="status in quickFilters"
                  :key="status.value"
                  :type="filters.status === status.value ? 'primary' : 'default'"
                  size="small"
                  @click="quickFilterStatus(status.value)"
                >
                  {{ status.label }}
                </el-button>
              </el-button-group>
            </div>
          </div>
        </template>

        <div v-loading="loading" class="table-container">
          <el-table
            ref="orderTable"
            :data="paginatedOrders"
            style="width: 100%"
            height="600"
            stripe
            border
            @selection-change="handleSelectionChange"
            @sort-change="handleSortChange"
            row-key="id"
          >
            <!-- 选择列 -->
            <el-table-column
              type="selection"
              width="50"
              :selectable="isOrderSelectable"
            />

            <!-- 订单号 -->
            <el-table-column
              prop="orderNo"
              label="订单号"
              width="140"
              fixed="left"
              show-overflow-tooltip
            >
              <template #default="{ row }">
                <div class="order-no">
                  <span class="order-id">{{ row.orderNo }}</span>
                  <el-tag
                    v-if="row.isUrgent"
                    type="danger"
                    size="small"
                    class="urgent-tag"
                  >
                    紧急
                  </el-tag>
                </div>
              </template>
            </el-table-column>

            <!-- 股票信息 -->
            <el-table-column label="股票信息" width="150">
              <template #default="{ row }">
                <div class="stock-info">
                  <div class="stock-code">{{ row.symbol }}</div>
                  <div class="stock-name">{{ row.stockName }}</div>
                </div>
              </template>
            </el-table-column>

            <!-- 交易方向 -->
            <el-table-column prop="side" label="方向" width="80" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="row.side === 'buy' ? 'danger' : 'success'"
                  size="small"
                >
                  {{ row.side === 'buy' ? '买入' : '卖出' }}
                </el-tag>
              </template>
            </el-table-column>

            <!-- 订单类型 -->
            <el-table-column prop="orderType" label="类型" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small" type="info">
                  {{ getOrderTypeLabel(row.orderType) }}
                </el-tag>
              </template>
            </el-table-column>

            <!-- 委托数量 -->
            <el-table-column
              prop="quantity"
              label="委托数量"
              width="100"
              align="right"
              sortable="custom"
            >
              <template #default="{ row }">
                <span class="quantity">{{ formatNumber(row.quantity) }}</span>
              </template>
            </el-table-column>

            <!-- 委托价格 -->
            <el-table-column
              prop="price"
              label="委托价格"
              width="100"
              align="right"
              sortable="custom"
            >
              <template #default="{ row }">
                <span class="price">
                  {{ row.orderType === 'market' ? '市价' : formatPrice(row.price) }}
                </span>
              </template>
            </el-table-column>

            <!-- 成交信息 -->
            <el-table-column label="成交信息" width="140" align="right">
              <template #default="{ row }">
                <div class="fill-info">
                  <div class="fill-quantity">
                    已成交: {{ formatNumber(row.filledQuantity) }}
                  </div>
                  <div class="fill-price" v-if="row.avgFillPrice > 0">
                    均价: {{ formatPrice(row.avgFillPrice) }}
                  </div>
                  <div class="fill-progress">
                    <el-progress
                      :percentage="row.fillPercent"
                      :stroke-width="4"
                      :show-text="false"
                      :color="getProgressColor(row.fillPercent)"
                    />
                    <span class="progress-text">{{ row.fillPercent }}%</span>
                  </div>
                </div>
              </template>
            </el-table-column>

            <!-- 订单状态 -->
            <el-table-column prop="status" label="状态" width="100" align="center">
              <template #default="{ row }">
                <div class="status-info">
                  <el-tag
                    :type="getStatusTagType(row.status)"
                    size="small"
                    :effect="row.status === 'pending' ? 'light' : 'plain'"
                  >
                    <el-icon v-if="row.status === 'pending'" class="is-loading">
                      <Loading />
                    </el-icon>
                    {{ getStatusLabel(row.status) }}
                  </el-tag>
                  <div v-if="row.rejectReason" class="reject-reason">
                    {{ row.rejectReason }}
                  </div>
                </div>
              </template>
            </el-table-column>

            <!-- 时间信息 -->
            <el-table-column label="时间信息" width="140">
              <template #default="{ row }">
                <div class="time-info">
                  <div class="create-time">
                    创建: {{ formatDateTime(row.createTime) }}
                  </div>
                  <div v-if="row.updateTime" class="update-time">
                    更新: {{ formatDateTime(row.updateTime) }}
                  </div>
                </div>
              </template>
            </el-table-column>

            <!-- 操作列 -->
            <el-table-column label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button
                    v-if="canCancelOrder(row)"
                    type="danger"
                    size="small"
                    :loading="row.cancelling"
                    @click="cancelOrder(row)"
                  >
                    撤单
                  </el-button>
                  <el-button
                    v-if="canModifyOrder(row)"
                    type="warning"
                    size="small"
                    @click="modifyOrder(row)"
                  >
                    改单
                  </el-button>
                  <el-button
                    type="info"
                    size="small"
                    @click="viewOrderDetail(row)"
                    text
                  >
                    详情
                  </el-button>
                </div>
              </template>
            </el-table-column>
          </el-table>

          <!-- 分页 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pagination.currentPage"
              v-model:page-size="pagination.pageSize"
              :total="filteredOrders.length"
              :page-sizes="[20, 50, 100, 200]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handlePageSizeChange"
              @current-change="handleCurrentPageChange"
            />
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!loading && filteredOrders.length === 0" class="empty-state">
          <el-empty description="暂无订单数据">
            <template #image>
              <el-icon size="80" color="#c0c4cc"><DocumentCopy /></el-icon>
            </template>
            <el-button type="primary" @click="$router.push('/trading/terminal')">
              创建订单
            </el-button>
          </el-empty>
        </div>
      </el-card>
    </div>

    <!-- 订单详情弹窗 -->
    <el-dialog
      v-model="showDetailDialog"
      title="订单详情"
      width="800px"
      :close-on-click-modal="false"
    >
      <OrderDetailPanel
        v-if="selectedOrder"
        :order="selectedOrder"
        @close="showDetailDialog = false"
        @refresh="refreshOrderDetail"
      />
    </el-dialog>

    <!-- 改单弹窗 -->
    <el-dialog
      v-model="showModifyDialog"
      title="修改订单"
      width="600px"
      :close-on-click-modal="false"
    >
      <OrderModifyForm
        v-if="selectedOrder"
        :order="selectedOrder"
        @success="handleModifySuccess"
        @cancel="showModifyDialog = false"
      />
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
  Clock,
  Check,
  PieChart,
  Search,
  RefreshLeft,
  Delete,
  Loading,
  DocumentCopy,
  Warning,
  MoreFilled,
  ArrowDown,
  Timer,
  TrendCharts,
  Document,
  Monitor
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useOrders } from '@/composables/trading/useOrders'
import { usePagination } from '@/composables/data/usePagination'
import { formatNumber, formatPrice, formatDateTime, formatCurrency } from '@/utils/formatters'
import { debounce } from 'lodash-es'
import OrderDetailPanel from '@/components/trading/OrderDetailPanel.vue'
import OrderModifyForm from '@/components/trading/OrderModifyForm.vue'
import type { Order, OrderStatus, OrderSide, OrderType } from '@/types/trading'

const router = useRouter()

// 使用订单管理组合函数
const {
  loading,
  orders,
  orderStats,
  wsConnected,
  selectedOrders,
  refreshOrders,
  cancelOrder: cancelSingleOrder,
  batchCancelOrders: batchCancel,
  exportOrders: exportOrdersData,
  subscribeOrderUpdates,
  unsubscribeOrderUpdates,
  hasRiskOrders,
  riskOrdersCount,
  activeOrdersCount,
  avgFillTime,
  avgSlippage,
  slippageClass,
  efficiency,
  efficiencyChange
} = useOrders()

// 本地状态 / 筛选与排序 —— 必须先声明供后续 computed 使用
const showRiskOnly = ref(false)

const filters = ref({
  status: '',
  side: '',
  orderType: '',
  dateRange: null as [string, string] | null,
  keyword: '',
  riskLevel: ''
})

const sortConfig = ref({
  prop: 'createTime',
  order: 'descending'
})

// 计算属性：过滤后的订单
const filteredOrders = computed(() => {
  let result = [...orders.value]

  // 状态筛选
  if (filters.value.status) {
    result = result.filter(order => order.status === filters.value.status)
  }

  // 方向筛选
  if (filters.value.side) {
    result = result.filter(order => order.side === filters.value.side)
  }

  // 类型筛选
  if (filters.value.orderType) {
    result = result.filter(order => order.orderType === filters.value.orderType)
  }

  // 风险等级筛选
  if (filters.value.riskLevel) {
    result = result.filter(order => order.riskLevel === filters.value.riskLevel)
  }

  // 只看风险订单
  if (showRiskOnly.value) {
    result = result.filter(order => order.riskLevel && order.riskLevel !== 'low')
  }

  // 时间范围筛选
  if (filters.value.dateRange) {
    const [startTime, endTime] = filters.value.dateRange
    result = result.filter(order => {
      const createTime = new Date(order.createTime).getTime()
      return createTime >= new Date(startTime).getTime() &&
             createTime <= new Date(endTime).getTime()
    })
  }

  // 关键词搜索
  if (filters.value.keyword) {
    const keyword = filters.value.keyword.toLowerCase()
    result = result.filter(order =>
      order.orderNo.toLowerCase().includes(keyword) ||
      order.symbol.toLowerCase().includes(keyword) ||
      order.stockName.toLowerCase().includes(keyword)
    )
  }

  // 排序
  if (sortConfig.value.prop) {
    result.sort((a, b) => {
      const aVal = a[sortConfig.value.prop as keyof Order]
      const bVal = b[sortConfig.value.prop as keyof Order]
      return sortConfig.value.order === 'ascending' ? (aVal > bVal ? 1 : -1) : (aVal < bVal ? 1 : -1)
    })
  }

  return result
})

// 使用分页组合函数
const {
  pagination,
  paginatedData: paginatedOrders,
  handlePageSizeChange,
  handleCurrentPageChange
} = usePagination(computed(() => filteredOrders.value))

// 其它本地状态
const orderTable = ref()
const showDetailDialog = ref(false)
const showModifyDialog = ref(false)
const selectedOrder = ref<Order | null>(null)
const showMonitorPanel = ref(false)
const autoRefresh = ref(false)

// 配置数据
const orderStatuses = [
  { label: '待成交', value: 'pending' },
  { label: '已成交', value: 'filled' },
  { label: '部分成交', value: 'partial' },
  { label: '已撤销', value: 'cancelled' },
  { label: '已拒绝', value: 'rejected' }
]

const quickFilters = [
  { label: '全部', value: '' },
  { label: '待成交', value: 'pending' },
  { label: '已成交', value: 'filled' },
  { label: '已撤销', value: 'cancelled' }
]

// 方法
const handleFilterChange = () => {
  pagination.value.currentPage = 1
}

const handleSearchInput = debounce(() => {
  pagination.value.currentPage = 1
}, 300)

const resetFilters = () => {
  filters.value = {
    status: '',
    side: '',
    orderType: '',
    dateRange: null,
    keyword: '',
    riskLevel: ''
  }
  showRiskOnly.value = false
  pagination.value.currentPage = 1
}

const quickFilterStatus = (status: string) => {
  filters.value.status = status
  handleFilterChange()
}

const handleSelectionChange = (selection: Order[]) => {
  selectedOrders.value = selection
}

const handleSortChange = ({ prop, order }: any) => {
  sortConfig.value = { prop, order }
}

const isOrderSelectable = (row: Order) => {
  return canCancelOrder(row)
}

const canCancelOrder = (order: Order): boolean => {
  return ['pending', 'partial'].includes(order.status)
}

const canModifyOrder = (order: Order): boolean => {
  return order.status === 'pending' && order.orderType === 'limit'
}

const cancelOrder = async (order: Order) => {
  try {
    await ElMessageBox.confirm(
      `确定要撤销订单 ${order.orderNo} 吗？`,
      '撤销订单',
      {
        confirmButtonText: '确定撤销',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    order.cancelling = true
    await cancelSingleOrder(order.id)
    ElMessage.success('订单撤销成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('订单撤销失败')
    }
  } finally {
    order.cancelling = false
  }
}

const batchCancelOrders = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要批量撤销选中的 ${selectedOrders.value.length} 个订单吗？`,
      '批量撤销订单',
      {
        confirmButtonText: '确定撤销',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await batchCancel(selectedOrders.value.map(order => order.id))
    ElMessage.success(`成功撤销 ${selectedOrders.value.length} 个订单`)
    selectedOrders.value = []
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量撤销失败')
    }
  }
}

const modifyOrder = (order: Order) => {
  selectedOrder.value = order
  showModifyDialog.value = true
}

const viewOrderDetail = (order: Order) => {
  selectedOrder.value = order
  showDetailDialog.value = true
}

const refreshOrderDetail = () => {
  // 刷新订单详情
  refreshOrders()
}

const handleModifySuccess = () => {
  showModifyDialog.value = false
  ElMessage.success('订单修改成功')
  refreshOrders()
}

const exportOrders = async () => {
  try {
    await exportOrdersData(filteredOrders.value)
    ElMessage.success('订单数据导出成功')
  } catch (error) {
    ElMessage.error('订单数据导出失败')
  }
}

// 辅助方法
const getOrderTypeLabel = (type: OrderType): string => {
  const labels = {
    limit: '限价',
    market: '市价',
    stop: '止损',
    'stop-profit': '止盈'
  }
  return labels[type] || type
}

const getStatusLabel = (status: OrderStatus): string => {
  const labels = {
    pending: '待成交',
    filled: '已成交',
    partial: '部分成交',
    cancelled: '已撤销',
    rejected: '已拒绝'
  }
  return labels[status] || status
}

const getStatusTagType = (status: OrderStatus): string => {
  const types = {
    pending: 'warning',
    filled: 'success',
    partial: 'primary',
    cancelled: 'info',
    rejected: 'danger'
  }
  return types[status] || 'info'
}

const getProgressColor = (percent: number): string => {
  if (percent === 100) return '#67c23a'
  if (percent >= 50) return '#e6a23c'
  return '#409eff'
}

const getEfficiencyColor = (percent: number): string => {
  if (percent >= 80) return '#67c23a'
  if (percent >= 50) return '#e6a23c'
  return '#909399'
}

// 自动刷新处理
const handleAutoRefreshChange = (enabled: boolean) => {
  if (enabled) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  stopAutoRefresh() // 先停止现有的定时器
  autoRefreshTimer = setInterval(() => {
    refreshOrders()
  }, 30000) // 30秒刷新一次
}

const stopAutoRefresh = () => {
  if (autoRefreshTimer) {
    clearInterval(autoRefreshTimer)
    autoRefreshTimer = null
  }
}

// 更多操作处理
const handleMoreActions = (command: string) => {
  switch (command) {
    case 'riskAnalysis':
      showRiskAnalysis()
      break
    case 'performance':
      showPerformanceAnalysis()
      break
    case 'autoCancel':
      showAutoCancelDialog()
      break
    case 'template':
      showOrderTemplates()
      break
  }
}

const showRiskAnalysis = () => {
  ElMessage.info('风险分析功能开发中')
  // 这里可以打开风险分析弹窗
}

const showPerformanceAnalysis = () => {
  ElMessage.info('执行分析功能开发中')
  // 这里可以打开性能分析弹窗
}

const showAutoCancelDialog = () => {
  ElMessage.info('自动撤单功能开发中')
  // 这里可以打开自动撤单设置弹窗
}

const showOrderTemplates = () => {
  ElMessage.info('订单模板功能开发中')
  // 这里可以打开订单模板管理弹窗
}

// 生命周期
onMounted(() => {
  refreshOrders()
  subscribeOrderUpdates()
  
  // 显示监控面板（首次访问时）
  const hasVisited = localStorage.getItem('order-management-visited')
  if (!hasVisited) {
    showMonitorPanel.value = true
    localStorage.setItem('order-management-visited', 'true')
  }
})

onUnmounted(() => {
  unsubscribeOrderUpdates()
  stopAutoRefresh()
})
</script>

<style scoped>
.order-management-page {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 16px;
}

.page-header {
  margin-bottom: 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-left {
  flex: 1;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-subtitle {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  color: #606266;
}

.header-actions {
  display: flex;
  gap: 12px;
}

/* 监控面板样式 */
.monitor-panel {
  margin-bottom: 20px;
}

.monitor-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid #409eff;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.monitor-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 20px;
  padding: 16px 0;
}

.monitor-item {
  text-align: center;
}

.monitor-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
}

.monitor-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.monitor-value.risk {
  color: #f56c6c;
}

.stats-cards {
  margin-bottom: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.stat-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  position: relative;
}

.stat-card.pending {
  border-left: 4px solid #e6a23c;
}

.stat-card.filled {
  border-left: 4px solid #67c23a;
}

.stat-card.partial {
  border-left: 4px solid #409eff;
}

.stat-card.cancelled {
  border-left: 4px solid #909399;
}

.stat-card.performance {
  border-left: 4px solid #f56c6c;
}

.stat-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
}

.stat-info {
  flex: 1;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-trend {
  font-size: 12px;
  color: #909399;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  background: linear-gradient(135deg, #409eff, #67c23a);
}

.stat-progress {
  padding: 0 20px 16px;
}

.filter-section {
  margin-bottom: 20px;
}

.filter-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-label {
  font-size: 12px;
  color: #606266;
  font-weight: 500;
}

.filter-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.order-table-section {
  margin-bottom: 20px;
}

.table-card {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.table-container {
  min-height: 400px;
}

.order-no {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.order-id {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
}

.urgent-tag {
  align-self: flex-start;
}

.stock-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stock-code {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
  font-size: 14px;
}

.stock-name {
  font-size: 12px;
  color: #606266;
}

.quantity, .price {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
}

.fill-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.fill-quantity, .fill-price {
  font-size: 12px;
  color: #606266;
}

.fill-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-text {
  font-size: 12px;
  color: #606266;
  min-width: 30px;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: center;
}

.reject-reason {
  font-size: 11px;
  color: #f56c6c;
  text-align: center;
}

.time-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.create-time, .update-time {
  font-size: 12px;
  color: #606266;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 16px 0;
  border-top: 1px solid #ebeef5;
  margin-top: 16px;
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

:deep(.el-table) {
  font-size: 13px;
}

:deep(.el-table th) {
  background-color: #fafafa;
  color: #606266;
  font-weight: 600;
  font-size: 12px;
}

:deep(.el-table--border td) {
  border-right: 1px solid #ebeef5;
}

:deep(.el-progress-bar__outer) {
  width: 60px;
}

:deep(.is-loading) {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 768px) {
  .order-management-page {
    padding: 8px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-group {
    width: 100%;
  }
  
  .table-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style> 