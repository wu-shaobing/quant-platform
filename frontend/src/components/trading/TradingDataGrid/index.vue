<template>
  <div class="trading-data-grid">
    <!-- 工具栏 -->
    <div class="trading-data-grid__toolbar">
      <div class="trading-data-grid__tabs">
        <div
          v-for="tab in tabs"
          :key="tab.key"
          :class="[
            'trading-data-grid__tab',
            { 'trading-data-grid__tab--active': activeTab === tab.key }
          ]"
          @click="setActiveTab(tab.key)"
        >
          <span>{{ tab.label }}</span>
          <el-badge
            v-if="tab.count !== undefined"
            :value="tab.count"
            :hidden="tab.count === 0"
            type="primary"
          />
        </div>
      </div>
      
      <div class="trading-data-grid__actions">
        <el-button-group size="small">
          <el-button
            :type="viewMode === 'table' ? 'primary' : 'default'"
            @click="setViewMode('table')"
            :icon="Grid"
          >
            表格
          </el-button>
          <el-button
            :type="viewMode === 'card' ? 'primary' : 'default'"
            @click="setViewMode('card')"
            :icon="List"
          >
            卡片
          </el-button>
        </el-button-group>
        
        <el-button size="small" @click="refresh" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        
        <el-dropdown @command="handleExport">
          <el-button size="small">
            <el-icon><Download /></el-icon>
            导出
            <el-icon><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv">导出CSV</el-dropdown-item>
              <el-dropdown-item command="excel">导出Excel</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 过滤器 -->
    <div v-if="showFilters" class="trading-data-grid__filters">
      <el-form :model="filters" inline size="small">
        <el-form-item v-if="activeTab === 'orders'" label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable>
            <el-option label="全部" value="" />
            <el-option label="待成交" value="pending" />
            <el-option label="部分成交" value="partial" />
            <el-option label="已成交" value="filled" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="股票代码">
          <el-input
            v-model="filters.symbol"
            placeholder="请输入股票代码"
            clearable
            style="width: 120px"
          />
        </el-form-item>
        
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            size="small"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="applyFilters">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 数据内容 -->
    <div class="trading-data-grid__content">
      <!-- 表格视图 -->
      <div v-if="viewMode === 'table'" class="trading-data-grid__table">
        <VirtualTable
          :data="filteredData"
          :columns="currentColumns"
          :height="tableHeight"
          :loading="loading"
          :row-key="getRowKey"
          @row-click="handleRowClick"
          @sort-change="handleSort"
          ref="tableRef"
        >
          <!-- 自定义列渲染 -->
          <template #status="{ value, row }">
            <el-tag
              :type="getStatusType(value)"
              size="small"
              effect="plain"
            >
              {{ getStatusText(value) }}
            </el-tag>
          </template>
          
          <template #side="{ value }">
            <span :class="getSideClass(value)">
              {{ getSideText(value) }}
            </span>
          </template>
          
          <template #price="{ value }">
            <span class="trading-data-grid__price">
              {{ formatPrice(value) }}
            </span>
          </template>
          
          <template #volume="{ value }">
            <span class="trading-data-grid__volume">
              {{ formatVolume(value) }}
            </span>
          </template>
          
          <template #amount="{ value }">
            <span class="trading-data-grid__amount">
              {{ formatCurrency(value) }}
            </span>
          </template>
          
          <template #pnl="{ value }">
            <span :class="getPnlClass(value)">
              {{ formatCurrency(value) }}
            </span>
          </template>
          
          <template #pnlPercent="{ value }">
            <span :class="getPnlClass(value)">
              {{ formatPercent(value) }}
            </span>
          </template>
          
          <template #actions="{ row }">
            <div class="trading-data-grid__actions-cell">
              <el-button
                v-if="canCancel(row)"
                size="small"
                type="danger"
                text
                @click.stop="cancelOrder(row)"
              >
                撤单
              </el-button>
              <el-button
                v-if="canModify(row)"
                size="small"
                type="primary"
                text
                @click.stop="modifyOrder(row)"
              >
                改单
              </el-button>
              <el-button
                size="small"
                text
                @click.stop="viewDetails(row)"
              >
                详情
              </el-button>
            </div>
          </template>
        </VirtualTable>
      </div>
      
      <!-- 卡片视图 -->
      <div v-else class="trading-data-grid__cards">
        <div
          v-for="item in filteredData"
          :key="getRowKey(item)"
          class="trading-data-grid__card"
          @click="handleRowClick(item)"
        >
          <div class="trading-data-grid__card-header">
            <div class="trading-data-grid__card-title">
              <span class="trading-data-grid__symbol">{{ item.symbol }}</span>
              <el-tag
                v-if="item.status"
                :type="getStatusType(item.status)"
                size="small"
                effect="plain"
              >
                {{ getStatusText(item.status) }}
              </el-tag>
            </div>
            <div class="trading-data-grid__card-time">
              {{ formatTime(item.createTime || item.updateTime) }}
            </div>
          </div>
          
          <div class="trading-data-grid__card-body">
            <div class="trading-data-grid__card-row">
              <span class="trading-data-grid__card-label">方向:</span>
              <span :class="getSideClass(item.side)">
                {{ getSideText(item.side) }}
              </span>
            </div>
            
            <div class="trading-data-grid__card-row">
              <span class="trading-data-grid__card-label">价格:</span>
              <span class="trading-data-grid__price">
                {{ formatPrice(item.price) }}
              </span>
            </div>
            
            <div class="trading-data-grid__card-row">
              <span class="trading-data-grid__card-label">数量:</span>
              <span class="trading-data-grid__volume">
                {{ formatVolume(item.volume || item.quantity) }}
              </span>
            </div>
            
            <div v-if="item.amount" class="trading-data-grid__card-row">
              <span class="trading-data-grid__card-label">金额:</span>
              <span class="trading-data-grid__amount">
                {{ formatCurrency(item.amount) }}
              </span>
            </div>
            
            <div v-if="item.pnl !== undefined" class="trading-data-grid__card-row">
              <span class="trading-data-grid__card-label">盈亏:</span>
              <span :class="getPnlClass(item.pnl)">
                {{ formatCurrency(item.pnl) }}
              </span>
            </div>
          </div>
          
          <div class="trading-data-grid__card-actions">
            <el-button
              v-if="canCancel(item)"
              size="small"
              type="danger"
              text
              @click.stop="cancelOrder(item)"
            >
              撤单
            </el-button>
            <el-button
              v-if="canModify(item)"
              size="small"
              type="primary"
              text
              @click.stop="modifyOrder(item)"
            >
              改单
            </el-button>
            <el-button
              size="small"
              text
              @click.stop="viewDetails(item)"
            >
              详情
            </el-button>
          </div>
        </div>
        
        <!-- 空状态 -->
        <div v-if="filteredData.length === 0 && !loading" class="trading-data-grid__empty">
          <el-empty description="暂无数据" />
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="showPagination" class="trading-data-grid__pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  ElButton,
  ElButtonGroup,
  ElBadge,
  ElDropdown,
  ElDropdownMenu,
  ElDropdownItem,
  ElForm,
  ElFormItem,
  ElSelect,
  ElOption,
  ElInput,
  ElDatePicker,
  ElTag,
  ElIcon,
  ElEmpty,
  ElPagination
} from 'element-plus'
import {
  Grid,
  List,
  Refresh,
  Download,
  ArrowDown
} from '@element-plus/icons-vue'
import VirtualTable from '@/components/common/VirtualTable/index.vue'
import { formatPrice, formatVolume, formatCurrency, formatPercent } from '@/utils/format/number'
import { formatTime } from '@/utils/format/date'
import type { TableColumn } from '@/components/common/VirtualTable/index.vue'

/**
 * 标签页配置
 */
export interface TabConfig {
  key: string
  label: string
  count?: number
}

/**
 * 数据项类型
 */
export interface DataItem {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  price: number
  volume?: number
  quantity?: number
  amount?: number
  status?: string
  pnl?: number
  pnlPercent?: number
  createTime?: string
  updateTime?: string
  [key: string]: any
}

/**
 * 组件属性
 */
interface Props {
  data: DataItem[]
  tabs: TabConfig[]
  activeTab: string
  loading?: boolean
  showFilters?: boolean
  showPagination?: boolean
  height?: number
  viewMode?: 'table' | 'card'
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  showFilters: true,
  showPagination: true,
  height: 600,
  viewMode: 'table'
})

/**
 * 组件事件
 */
interface Emits {
  (e: 'tab-change', tab: string): void
  (e: 'view-mode-change', mode: 'table' | 'card'): void
  (e: 'refresh'): void
  (e: 'export', format: 'csv' | 'excel'): void
  (e: 'row-click', row: DataItem): void
  (e: 'cancel-order', order: DataItem): void
  (e: 'modify-order', order: DataItem): void
  (e: 'view-details', item: DataItem): void
  (e: 'filters-change', filters: any): void
  (e: 'sort-change', key: string, order: 'asc' | 'desc'): void
  (e: 'page-change', page: number, size: number): void
}

const emit = defineEmits<Emits>()

// 模板引用
const tableRef = ref()

// 状态
const currentViewMode = ref(props.viewMode)
const filters = ref({
  status: '',
  symbol: '',
  dateRange: null as [string, string] | null
})
const pagination = ref({
  page: 1,
  size: 20,
  total: 0
})

// 计算属性
const tableHeight = computed(() => {
  let height = props.height
  if (props.showFilters) height -= 60
  if (props.showPagination) height -= 60
  return height - 100 // 减去工具栏高度
})

const currentColumns = computed((): TableColumn[] => {
  const baseColumns: TableColumn[] = [
    { key: 'symbol', title: '股票代码', width: 100, sortable: true },
    { key: 'side', title: '方向', width: 80, align: 'center' },
    { key: 'price', title: '价格', width: 100, align: 'right', sortable: true },
    { key: 'volume', title: '数量', width: 100, align: 'right', sortable: true },
    { key: 'amount', title: '金额', width: 120, align: 'right', sortable: true }
  ]

  // 根据活动标签页添加特定列
  if (props.activeTab === 'orders') {
    baseColumns.splice(1, 0, {
      key: 'status',
      title: '状态',
      width: 100,
      align: 'center'
    })
    baseColumns.push({
      key: 'createTime',
      title: '委托时间',
      width: 150,
      formatter: (value) => formatTime(value)
    })
  } else if (props.activeTab === 'positions') {
    baseColumns.push(
      { key: 'pnl', title: '浮动盈亏', width: 120, align: 'right', sortable: true },
      { key: 'pnlPercent', title: '盈亏比例', width: 100, align: 'right', sortable: true }
    )
  } else if (props.activeTab === 'trades') {
    baseColumns.push({
      key: 'updateTime',
      title: '成交时间',
      width: 150,
      formatter: (value) => formatTime(value)
    })
  }

  // 添加操作列
  baseColumns.push({
    key: 'actions',
    title: '操作',
    width: 150,
    align: 'center'
  })

  return baseColumns
})

const filteredData = computed(() => {
  let data = [...props.data]

  // 应用过滤器
  if (filters.value.status) {
    data = data.filter(item => item.status === filters.value.status)
  }

  if (filters.value.symbol) {
    data = data.filter(item => 
      item.symbol.toLowerCase().includes(filters.value.symbol.toLowerCase())
    )
  }

  if (filters.value.dateRange) {
    const [startDate, endDate] = filters.value.dateRange
    data = data.filter(item => {
      const itemDate = item.createTime || item.updateTime
      if (!itemDate) return false
      
      const date = itemDate.split(' ')[0] // 提取日期部分
      return date >= startDate && date <= endDate
    })
  }

  // 更新总数
  pagination.value.total = data.length

  // 应用分页
  if (props.showPagination) {
    const start = (pagination.value.page - 1) * pagination.value.size
    const end = start + pagination.value.size
    data = data.slice(start, end)
  }

  return data
})

/**
 * 设置活动标签页
 */
const setActiveTab = (tab: string) => {
  emit('tab-change', tab)
}

/**
 * 设置视图模式
 */
const setViewMode = (mode: 'table' | 'card') => {
  currentViewMode.value = mode
  emit('view-mode-change', mode)
}

/**
 * 刷新数据
 */
const refresh = () => {
  emit('refresh')
}

/**
 * 处理导出
 */
const handleExport = (format: 'csv' | 'excel') => {
  emit('export', format)
}

/**
 * 应用过滤器
 */
const applyFilters = () => {
  pagination.value.page = 1 // 重置到第一页
  emit('filters-change', { ...filters.value })
}

/**
 * 重置过滤器
 */
const resetFilters = () => {
  filters.value = {
    status: '',
    symbol: '',
    dateRange: null
  }
  applyFilters()
}

/**
 * 处理行点击
 */
const handleRowClick = (row: DataItem) => {
  emit('row-click', row)
}

/**
 * 处理排序
 */
const handleSort = (key: string, order: 'asc' | 'desc') => {
  emit('sort-change', key, order)
}

/**
 * 处理页面变化
 */
const handlePageChange = (page: number) => {
  pagination.value.page = page
  emit('page-change', page, pagination.value.size)
}

/**
 * 处理页面大小变化
 */
const handleSizeChange = (size: number) => {
  pagination.value.size = size
  pagination.value.page = 1
  emit('page-change', 1, size)
}

/**
 * 获取行键值
 */
const getRowKey = (row: DataItem): string => {
  return row.id || row.symbol + row.createTime
}

/**
 * 获取状态类型
 */
const getStatusType = (status: string): string => {
  const typeMap: Record<string, string> = {
    pending: 'warning',
    partial: 'info',
    filled: 'success',
    cancelled: 'danger'
  }
  return typeMap[status] || 'default'
}

/**
 * 获取状态文本
 */
const getStatusText = (status: string): string => {
  const textMap: Record<string, string> = {
    pending: '待成交',
    partial: '部分成交',
    filled: '已成交',
    cancelled: '已取消'
  }
  return textMap[status] || status
}

/**
 * 获取方向样式类
 */
const getSideClass = (side: string): string => {
  return side === 'buy' ? 'text-success' : 'text-danger'
}

/**
 * 获取方向文本
 */
const getSideText = (side: string): string => {
  return side === 'buy' ? '买入' : '卖出'
}

/**
 * 获取盈亏样式类
 */
const getPnlClass = (value: number): string => {
  if (value > 0) return 'text-success'
  if (value < 0) return 'text-danger'
  return 'text-info'
}

/**
 * 检查是否可以撤单
 */
const canCancel = (item: DataItem): boolean => {
  return item.status === 'pending' || item.status === 'partial'
}

/**
 * 检查是否可以改单
 */
const canModify = (item: DataItem): boolean => {
  return item.status === 'pending'
}

/**
 * 撤销订单
 */
const cancelOrder = (order: DataItem) => {
  emit('cancel-order', order)
}

/**
 * 修改订单
 */
const modifyOrder = (order: DataItem) => {
  emit('modify-order', order)
}

/**
 * 查看详情
 */
const viewDetails = (item: DataItem) => {
  emit('view-details', item)
}

// 监听视图模式变化
watch(() => props.viewMode, (newMode) => {
  currentViewMode.value = newMode
})

// 生命周期
onMounted(() => {
  pagination.value.total = props.data.length
})
</script>

<style scoped lang="scss">
.trading-data-grid {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;

  &__toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    background: var(--el-fill-color-lighter);
  }

  &__tabs {
    display: flex;
    gap: 4px;
  }

  &__tab {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s;
    color: var(--el-text-color-regular);

    &:hover {
      background: var(--el-fill-color-light);
      color: var(--el-text-color-primary);
    }

    &--active {
      background: var(--el-color-primary);
      color: white;

      &:hover {
        background: var(--el-color-primary);
      }
    }
  }

  &__actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__filters {
    padding: 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    background: var(--el-fill-color-extra-light);
  }

  &__content {
    flex: 1;
    min-height: 0;
  }

  &__table {
    height: 100%;
  }

  &__cards {
    height: 100%;
    overflow-y: auto;
    padding: 16px;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
    align-content: start;
  }

  &__card {
    border: 1px solid var(--el-border-color-lighter);
    border-radius: 6px;
    padding: 16px;
    background: var(--el-bg-color);
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      border-color: var(--el-color-primary);
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }

    &-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;
    }

    &-title {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    &-time {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }

    &-body {
      margin-bottom: 12px;
    }

    &-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      font-size: 14px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    &-label {
      color: var(--el-text-color-regular);
      font-weight: 500;
    }

    &-actions {
      display: flex;
      gap: 8px;
      padding-top: 12px;
      border-top: 1px solid var(--el-border-color-extra-light);
    }
  }

  &__symbol {
    font-weight: 600;
    color: var(--el-text-color-primary);
  }

  &__price {
    font-weight: 500;
    color: var(--el-text-color-primary);
  }

  &__volume {
    color: var(--el-text-color-regular);
  }

  &__amount {
    font-weight: 500;
    color: var(--el-text-color-primary);
  }

  &__actions-cell {
    display: flex;
    gap: 8px;
  }

  &__empty {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 200px;
    grid-column: 1 / -1;
  }

  &__pagination {
    padding: 16px;
    border-top: 1px solid var(--el-border-color-lighter);
    background: var(--el-fill-color-lighter);
    display: flex;
    justify-content: center;
  }
}

// 工具类
.text-success {
  color: var(--el-color-success);
}

.text-danger {
  color: var(--el-color-danger);
}

.text-info {
  color: var(--el-color-info);
}

// 响应式设计
@media (max-width: 768px) {
  .trading-data-grid {
    &__toolbar {
      flex-direction: column;
      gap: 12px;
      align-items: stretch;
    }

    &__tabs {
      justify-content: center;
    }

    &__actions {
      justify-content: center;
    }

    &__cards {
      grid-template-columns: 1fr;
      padding: 12px;
      gap: 12px;
    }

    &__card {
      padding: 12px;
    }
  }
}
</style> 