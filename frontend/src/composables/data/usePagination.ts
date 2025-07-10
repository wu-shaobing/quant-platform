import { ref, computed, watch, type Ref } from 'vue'

/**
 * usePagination 组合式函数
 * 提供分页功能，包括页码管理、页面大小设置、数据切片等
 */
export const usePagination = <T = any>(
  data: Ref<T[]> | (() => T[]),
  options: {
    defaultPageSize?: number
    pageSizes?: number[]
  } = {}
) => {
  const {
    defaultPageSize = 20,
    pageSizes = [10, 20, 50, 100]
  } = options

  // 分页状态
  const pagination = ref({
    currentPage: 1,
    pageSize: defaultPageSize,
    total: 0
  })

  // 获取数据的计算属性
  const sourceData = computed(() => {
    if (typeof data === 'function') {
      return data()
    }
    return data.value
  })

  // 分页后的数据
  const paginatedData = computed(() => {
    const start = (pagination.value.currentPage - 1) * pagination.value.pageSize
    const end = start + pagination.value.pageSize
    return sourceData.value.slice(start, end)
  })

  // 总页数
  const totalPages = computed(() => {
    return Math.ceil(sourceData.value.length / pagination.value.pageSize)
  })

  // 分页信息
  const pageInfo = computed(() => {
    const { currentPage, pageSize } = pagination.value
    const total = sourceData.value.length
    const start = (currentPage - 1) * pageSize + 1
    const end = Math.min(currentPage * pageSize, total)
    
    return {
      start,
      end,
      total,
      currentPage,
      totalPages: totalPages.value,
      hasNext: currentPage < totalPages.value,
      hasPrev: currentPage > 1
    }
  })

  // 页面大小改变处理
  const handlePageSizeChange = (size: number) => {
    pagination.value.pageSize = size
    pagination.value.currentPage = 1 // 重置到第一页
  }

  // 当前页改变处理
  const handleCurrentPageChange = (page: number) => {
    if (page >= 1 && page <= totalPages.value) {
      pagination.value.currentPage = page
    }
  }

  // 跳转到第一页
  const goToFirstPage = () => {
    pagination.value.currentPage = 1
  }

  // 跳转到最后一页
  const goToLastPage = () => {
    pagination.value.currentPage = totalPages.value
  }

  // 上一页
  const goToPrevPage = () => {
    if (pagination.value.currentPage > 1) {
      pagination.value.currentPage--
    }
  }

  // 下一页
  const goToNextPage = () => {
    if (pagination.value.currentPage < totalPages.value) {
      pagination.value.currentPage++
    }
  }

  // 重置分页
  const resetPagination = () => {
    pagination.value.currentPage = 1
    pagination.value.pageSize = defaultPageSize
  }

  // 监听数据变化，自动更新总数并调整当前页
  watch(
    sourceData,
    (newData) => {
      pagination.value.total = newData.length
      
      // 如果当前页超出范围，调整到最后一页
      if (pagination.value.currentPage > totalPages.value && totalPages.value > 0) {
        pagination.value.currentPage = totalPages.value
      }
      
      // 如果没有数据，重置到第一页
      if (newData.length === 0) {
        pagination.value.currentPage = 1
      }
    },
    { immediate: true }
  )

  return {
    pagination,
    paginatedData,
    totalPages,
    pageInfo,
    pageSizes,
    handlePageSizeChange,
    handleCurrentPageChange,
    goToFirstPage,
    goToLastPage,
    goToPrevPage,
    goToNextPage,
    resetPagination
  }
} 