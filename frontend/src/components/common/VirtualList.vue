<!--
  虚拟滚动列表组件
  支持大数据量的高性能渲染
-->
<template>
  <div 
    ref="containerRef"
    class="virtual-list"
    :style="{ height: typeof height === 'number' ? `${height}px` : height }"
    @scroll="handleScroll"
  >
    <!-- 总高度占位 -->
    <div 
      class="virtual-list-phantom"
      :style="{ height: `${totalHeight}px` }"
    />
    
    <!-- 可视区域内容 -->
    <div 
      class="virtual-list-content"
      :style="{ 
        transform: `translateY(${offsetY}px)`,
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0
      }"
    >
      <div
        v-for="(item, index) in visibleItems"
        :key="getItemKey(item, startIndex + index)"
        class="virtual-list-item"
        :style="{ 
          height: `${itemHeight}px`,
          overflow: 'hidden'
        }"
      >
        <slot 
          :item="item" 
          :index="startIndex + index"
          :active="startIndex + index === activeIndex"
        >
          {{ item }}
        </slot>
      </div>
    </div>
    
    <!-- 加载状态 -->
    <div 
      v-if="loading" 
      class="virtual-list-loading"
    >
      <slot name="loading">
        <div class="loading-content">
          <el-icon class="is-loading">
            <Loading />
          </el-icon>
          <span>加载中...</span>
        </div>
      </slot>
    </div>
    
    <!-- 空状态 -->
    <div 
      v-if="!loading && items.length === 0" 
      class="virtual-list-empty"
    >
      <slot name="empty">
        <div class="empty-content">
          <el-icon><DocumentDelete /></el-icon>
          <span>暂无数据</span>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { Loading, DocumentDelete } from '@element-plus/icons-vue'
import { throttle } from 'lodash-es'

interface Props {
  // 数据源
  items: any[]
  // 容器高度
  height: number | string
  // 每项高度
  itemHeight: number
  // 缓冲区大小（额外渲染的项目数）
  buffer?: number
  // 唯一键生成函数
  keyField?: string | ((item: any, index: number) => string | number)
  // 是否启用无限滚动
  infinite?: boolean
  // 加载状态
  loading?: boolean
  // 激活项索引
  activeIndex?: number
  // 滚动节流延迟
  throttleDelay?: number
}

const props = withDefaults(defineProps<Props>(), {
  buffer: 5,
  keyField: 'id',
  infinite: false,
  loading: false,
  activeIndex: -1,
  throttleDelay: 16
})

const emit = defineEmits<{
  (e: 'scroll', payload: { scrollTop: number; isBottom: boolean }): void
  (e: 'load-more'): void
  (e: 'item-click', item: any, index: number): void
}>()

// 模板引用
const containerRef = ref<HTMLElement>()

// 滚动状态
const scrollTop = ref(0)
const containerHeight = ref(0)

// 计算属性
const totalHeight = computed(() => props.items.length * props.itemHeight)

const visibleCount = computed(() => {
  return Math.ceil(containerHeight.value / props.itemHeight) + props.buffer * 2
})

const startIndex = computed(() => {
  const index = Math.floor(scrollTop.value / props.itemHeight) - props.buffer
  return Math.max(0, index)
})

const endIndex = computed(() => {
  const index = startIndex.value + visibleCount.value
  return Math.min(props.items.length - 1, index)
})

const visibleItems = computed(() => {
  return props.items.slice(startIndex.value, endIndex.value + 1)
})

const offsetY = computed(() => {
  return startIndex.value * props.itemHeight
})

// 生成项目键值
const getItemKey = (item: any, index: number): string | number => {
  if (typeof props.keyField === 'function') {
    return props.keyField(item, index)
  }
  
  if (typeof props.keyField === 'string' && item && typeof item === 'object') {
    return item[props.keyField] ?? index
  }
  
  return index
}

// 节流滚动处理
const handleScroll = throttle((event: Event) => {
  const target = event.target as HTMLElement
  scrollTop.value = target.scrollTop
  
  const isBottom = target.scrollTop + target.clientHeight >= target.scrollHeight - 10
  
  emit('scroll', {
    scrollTop: scrollTop.value,
    isBottom
  })
  
  // 无限滚动
  if (props.infinite && isBottom && !props.loading) {
    emit('load-more')
  }
}, props.throttleDelay)

// 滚动到指定索引
const scrollToIndex = (index: number, behavior: ScrollBehavior = 'smooth') => {
  if (!containerRef.value) return
  
  const targetScrollTop = Math.max(0, index * props.itemHeight)
  
  containerRef.value.scrollTo({
    top: targetScrollTop,
    behavior
  })
}

// 滚动到顶部
const scrollToTop = (behavior: ScrollBehavior = 'smooth') => {
  scrollToIndex(0, behavior)
}

// 滚动到底部
const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
  if (!containerRef.value) return
  
  containerRef.value.scrollTo({
    top: totalHeight.value,
    behavior
  })
}

// 获取可视区域信息
const getVisibleRange = () => {
  return {
    start: startIndex.value,
    end: endIndex.value,
    count: visibleItems.value.length
  }
}

// 更新容器高度
const updateContainerHeight = () => {
  if (containerRef.value) {
    containerHeight.value = containerRef.value.clientHeight
  }
}

// 初始化
onMounted(async () => {
  await nextTick()
  updateContainerHeight()
  
  // 监听窗口大小变化
  window.addEventListener('resize', updateContainerHeight)
})

// 清理
onUnmounted(() => {
  window.removeEventListener('resize', updateContainerHeight)
})

// 监听高度变化
watch(() => props.height, () => {
  nextTick(() => {
    updateContainerHeight()
  })
})

// 监听激活项变化，自动滚动到可视区域
watch(() => props.activeIndex, (newIndex) => {
  if (newIndex >= 0 && containerRef.value) {
    const containerTop = scrollTop.value
    const containerBottom = containerTop + containerHeight.value
    const itemTop = newIndex * props.itemHeight
    const itemBottom = itemTop + props.itemHeight
    
    // 如果激活项不在可视区域内，滚动到该项
    if (itemTop < containerTop || itemBottom > containerBottom) {
      scrollToIndex(newIndex, 'smooth')
    }
  }
})

// 暴露方法
defineExpose({
  scrollToIndex,
  scrollToTop,
  scrollToBottom,
  getVisibleRange,
  updateContainerHeight
})
</script>

<style scoped>
.virtual-list {
  position: relative;
  overflow: auto;
  width: 100%;
}

.virtual-list-phantom {
  position: absolute;
  left: 0;
  top: 0;
  right: 0;
  z-index: -1;
}

.virtual-list-content {
  width: 100%;
}

.virtual-list-item {
  width: 100%;
  box-sizing: border-box;
}

.virtual-list-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.loading-content .el-icon {
  font-size: 24px;
  color: #409eff;
}

.virtual-list-empty {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
}

.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 40px;
  color: #909399;
}

.empty-content .el-icon {
  font-size: 48px;
  color: #c0c4cc;
}

/* 自定义滚动条样式 */
.virtual-list::-webkit-scrollbar {
  width: 6px;
}

.virtual-list::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 3px;
}

.virtual-list::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
  transition: background 0.3s;
}

.virtual-list::-webkit-scrollbar-thumb:hover {
  background: #909399;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .loading-content {
    padding: 16px;
  }
  
  .empty-content {
    padding: 32px 20px;
  }
  
  .empty-content .el-icon {
    font-size: 36px;
  }
}
</style> 