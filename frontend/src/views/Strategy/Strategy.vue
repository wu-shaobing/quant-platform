<template>
  <div class="strategy-view">
    <!-- 页面头部 -->
    <div class="strategy-header">
      <div class="header-content">
        <h1 class="page-title">策略中心</h1>
        <div class="header-actions">
          <el-button-group>
            <el-button 
              :type="activeTab === 'hub' ? 'primary' : 'default'"
              @click="switchTab('hub')"
            >
              策略市场
            </el-button>
            <el-button 
              :type="activeTab === 'develop' ? 'primary' : 'default'"
              @click="switchTab('develop')"
            >
              策略开发
            </el-button>
            <el-button 
              :type="activeTab === 'monitor' ? 'primary' : 'default'"
              @click="switchTab('monitor')"
            >
              策略监控
            </el-button>
          </el-button-group>
          
          <el-button type="primary" @click="createStrategy">
            <el-icon><Plus /></el-icon>
            新建策略
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="strategy-content">
      <!-- 策略市场 -->
      <div v-if="activeTab === 'hub'" class="tab-content">
        <StrategyHub />
      </div>
      
      <!-- 策略开发 -->
      <div v-else-if="activeTab === 'develop'" class="tab-content">
        <StrategyDevelop />
      </div>
      
      <!-- 策略监控 -->
      <div v-else-if="activeTab === 'monitor'" class="tab-content">
        <StrategyMonitor />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import StrategyHub from './StrategyHub.vue'
import StrategyDevelop from './StrategyDevelop.vue'
import StrategyMonitor from './StrategyMonitor.vue'
import { useStrategyStore } from '@/stores/modules/strategy'

const route = useRoute()
const router = useRouter()
const strategyStore = useStrategyStore()

// 状态
const activeTab = ref<'hub' | 'develop' | 'monitor'>('hub')

// 方法
const switchTab = (tab: 'hub' | 'develop' | 'monitor') => {
  activeTab.value = tab
  // 更新URL参数
  router.push({ 
    path: '/strategy', 
    query: { ...route.query, tab } 
  })
}

const createStrategy = () => {
  // 切换到开发页面
  switchTab('develop')
}

// 初始化
onMounted(() => {
  // 从URL参数获取初始标签
  const tab = route.query.tab as string
  if (tab && ['hub', 'develop', 'monitor'].includes(tab)) {
    activeTab.value = tab as 'hub' | 'develop' | 'monitor'
  }
  
  // 初始化策略数据
  strategyStore.initialize()
})
</script>

<style scoped>
.strategy-view {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.strategy-header {
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

.strategy-content {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.tab-content {
  min-height: 600px;
}
</style>
