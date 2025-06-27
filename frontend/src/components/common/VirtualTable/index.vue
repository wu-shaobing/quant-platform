<template>
  <div class="virtual-table" ref="tableContainer">
    <!-- 表头 -->
    <div class="table-header" :style="{ width: `${totalWidth}px` }">
      <div
        v-for="column in columns"
        :key="column.key"
        class="header-cell"
        :style="{ 
          width: `${column.width}px`,
          textAlign: column.align || 'left'
        }"
        @click="handleSort(column)"
      >
        <span>{{ column.title }}</span>
        <span v-if="column.sortable" class="sort-icon">
          <el-icon v-if="sortConfig.key === column.key">
            <component :is="sortConfig.order === 'asc' ? 'ArrowUp' : 'ArrowDown'" />
          </el-icon>
          <el-icon v-else class="sort-default">
            <Sort />
          </el-icon>
        </span>
      </div>
    </div>

    <!-- 虚拟滚动容器 -->
    <div 
      class="table-body"
      :style="{ height: `${height}px` }"
      @scroll="handleScroll"
      ref="scrollContainer"
    >
      <!-- 占位容器 -->
      <div 
        class="scroll-placeholder"
        :style="{ height: `${totalHeight}px` }"
      />
      
      <!-- 可见行容器 -->
      <div 
        class="visible-rows"
        :style="{ 
          transform: `translateY(${offsetY}px)`,
          width: `${totalWidth}px`
        }"
      >
        <div
          v-for="(item, index) in visibleData"
          :key="getRowKey(item, startIndex + index)"
          class="table-row"
          :class="getRowClass(item, startIndex + index)"
          @click="handleRowClick(item, startIndex + index)"
          @dblclick="handleRowDblClick(item, startIndex + index)"
        >
          <div
            v-for="column in columns"
            :key="column.key"
            class="table-cell"
            :style="{ 
              width: `${column.width}px`,
              textAlign: column.align || 'left'
            }"
          >
            <slot 
              v-if="column.slot"
              :name="column.slot"
              :row="item"
              :column="column"
              :index="startIndex + index"
            >
              {{ getCellValue(item, column) }}
            </slot>
            <span v-else>
              {{ getCellValue(item, column) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="table-loading">
      <el-icon class="is-loading">
        <Loading />
      </el-icon>
      <span>{{ loadingText }}</span>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && data.length === 0" class="table-empty">
      <slot name="empty">
        <el-empty description="暂无数据" />
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts" name="VirtualTable">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { Sort, Loading } from '@element-plus/icons-vue'
import { debounce } from 'lodash-es'

interface Column {
  key: string
  title: string
  width: number
  align?: 'left' | 'center' | 'right'
  sortable?: boolean
  slot?: string
  formatter?: (value: unknown, row: Record<string, unknown>) => string
}

interface SortConfig {
  key: string
  order: 'asc' | 'desc'
}

interface Props {
  data: Record<string, unknown>[]
  columns: Column[]
  height?: number
  rowHeight?: number
  overscan?: number
  loading?: boolean
  loadingText?: string
  rowKey?: string | ((row: Record<string, unknown>, index: number) => string)
  rowClassName?: string | ((row: Record<string, unknown>, index: number) => string)
  sortable?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  height: 400,
  rowHeight: 40,
  overscan: 5,
  loading: false,
  loadingText: '加载中...',
  rowKey: 'id',
  rowClassName: '',
  sortable: true
})

const emit = defineEmits<{
  (e: 'row-click', row: any, index: number): void
  (e: 'row-dblclick', row: any, index: number): void
  (e: 'sort-change', config: SortConfig): void
  (e: 'scroll', event: Event): void
}>()

// 引用
const tableContainer = ref<HTMLElement>()
const scrollContainer = ref<HTMLElement>()

// 状态
const scrollTop = ref(0)
const sortConfig = ref<SortConfig>({ key: '', order: 'asc' })

// 计算属性
const totalWidth = computed(() => {
  return props.columns.reduce((sum, col) => sum + col.width, 0)
})

const totalHeight = computed(() => {
  return props.data.length * props.rowHeight
})

const visibleCount = computed(() => {
  return Math.ceil(props.height / props.rowHeight) + props.overscan * 2
})

const startIndex = computed(() => {
  const start = Math.floor(scrollTop.value / props.rowHeight) - props.overscan
  return Math.max(0, start)
})

const endIndex = computed(() => {
  const end = startIndex.value + visibleCount.value
  return Math.min(props.data.length, end)
})

const visibleData = computed(() => {
  return props.data.slice(startIndex.value, endIndex.value)
})

const offsetY = computed(() => {
  return startIndex.value * props.rowHeight
})

// 排序后的数据
const sortedData = computed(() => {
  if (!sortConfig.value.key || !props.sortable) {
    return props.data
  }

  const { key, order } = sortConfig.value
  const column = props.columns.find(col => col.key === key)
  
  if (!column?.sortable) {
    return props.data
  }

  return [...props.data].sort((a, b) => {
    const aVal = getCellValue(a, column)
    const bVal = getCellValue(b, column)
    
    let result = 0
    
    if (typeof aVal === 'number' && typeof bVal === 'number') {
      result = aVal - bVal
    } else {
      result = String(aVal).localeCompare(String(bVal))
    }
    
    return order === 'asc' ? result : -result
  })
})

// 方法
const handleScroll = debounce((event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
  emit('scroll', event)
}, 16)

const handleSort = (column: Column) => {
  if (!column.sortable || !props.sortable) return

  if (sortConfig.value.key === column.key) {
    // 切换排序方向
    sortConfig.value.order = sortConfig.value.order === 'asc' ? 'desc' : 'asc'
  } else {
    // 新的排序列
    sortConfig.value.key = column.key
    sortConfig.value.order = 'asc'
  }

  emit('sort-change', { ...sortConfig.value })
}

const handleRowClick = (row: any, index: number) => {
  emit('row-click', row, index)
}

const handleRowDblClick = (row: any, index: number) => {
  emit('row-dblclick', row, index)
}

const getCellValue = (row: any, column: Column) => {
  const value = row[column.key]
  
  if (column.formatter) {
    return column.formatter(value, row)
  }
  
  return value
}

const getRowKey = (row: any, index: number) => {
  if (typeof props.rowKey === 'function') {
    return props.rowKey(row, index)
  }
  return row[props.rowKey] || index
}

const getRowClass = (row: any, index: number) => {
  let className = 'table-row-default'
  
  if (typeof props.rowClassName === 'function') {
    className += ' ' + props.rowClassName(row, index)
  } else if (props.rowClassName) {
    className += ' ' + props.rowClassName
  }
  
  return className
}

// 滚动到指定行
const scrollToRow = (index: number) => {
  if (!scrollContainer.value) return
  
  const targetScrollTop = index * props.rowHeight
  scrollContainer.value.scrollTop = targetScrollTop
}

// 刷新表格
const refresh = () => {
  nextTick(() => {
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = 0
    }
    scrollTop.value = 0
  })
}

// 获取选中行
const getSelectedRows = () => {
  // 这里可以实现行选择逻辑
  return []
}

// 暴露方法给父组件
defineExpose({
  scrollToRow,
  refresh,
  getSelectedRows
})

// 监听数据变化
watch(
  () => props.data,
  () => {
    refresh()
  },
  { deep: true }
)

// 生命周期
onMounted(() => {
  // 初始化滚动监听
})

onUnmounted(() => {
  // 清理
})
</script>

<style scoped>
.virtual-table {
  position: relative;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  background: white;
  overflow: hidden;
}

.table-header {
  display: flex;
  background: #fafafa;
  border-bottom: 1px solid #e8e8e8;
  position: sticky;
  top: 0;
  z-index: 10;
}

.header-cell {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 8px;
  font-weight: 600;
  border-right: 1px solid #e8e8e8;
  cursor: pointer;
  user-select: none;
}

.header-cell:last-child {
  border-right: none;
}

.header-cell:hover {
  background: #f0f0f0;
}

.sort-icon {
  margin-left: 4px;
  color: #409eff;
}

.sort-default {
  color: #c0c4cc;
}

.table-body {
  position: relative;
  overflow: auto;
}

.scroll-placeholder {
  width: 1px;
}

.visible-rows {
  position: absolute;
  top: 0;
  left: 0;
}

.table-row {
  display: flex;
  border-bottom: 1px solid #e8e8e8;
  transition: background-color 0.2s;
}

.table-row:hover {
  background: #f5f7fa;
}

.table-row:last-child {
  border-bottom: none;
}

.table-cell {
  display: flex;
  align-items: center;
  padding: 8px;
  border-right: 1px solid #e8e8e8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.table-cell:last-child {
  border-right: none;
}

.table-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: center;
  gap: 8px;
  color: #666;
}

.table-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
}

@media (max-width: 768px) {
  .header-cell,
  .table-cell {
    padding: 6px 4px;
    font-size: 12px;
  }
}
</style>