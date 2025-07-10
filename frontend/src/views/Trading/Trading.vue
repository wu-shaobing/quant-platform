<template>
  <div class="trading-view">
    <!-- 页面头部 -->
    <div class="trading-header">
      <div class="header-content">
        <h1 class="page-title">交易中心</h1>
        <div class="header-actions">
          <el-button-group>
            <el-button 
              :type="activeTab === 'terminal' ? 'primary' : 'default'"
              @click="switchTab('terminal')"
            >
              交易终端
            </el-button>
            <el-button 
              :type="activeTab === 'orders' ? 'primary' : 'default'"
              @click="switchTab('orders')"
            >
              订单管理
            </el-button>
            <el-button 
              :type="activeTab === 'positions' ? 'primary' : 'default'"
              @click="switchTab('positions')"
            >
              持仓管理
            </el-button>
          </el-button-group>
          
          <el-button type="primary" @click="refreshData" :loading="loading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="trading-content">
      <!-- 交易终端 -->
      <div v-if="activeTab === 'terminal'" class="tab-content">
        <TradingTerminal />
      </div>
      
      <!-- 订单管理 -->
      <div v-else-if="activeTab === 'orders'" class="tab-content">
        <OrderManagement />
      </div>
      
      <!-- 持仓管理 -->
      <div v-else-if="activeTab === 'positions'" class="tab-content">
        <PositionManagement />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import TradingTerminal from './TradingTerminal.vue'
import OrderManagement from './OrderManagement.vue'
import PositionManagement from './PositionManagement.vue'
import { useTradingStore } from '@/stores/modules/trading'

const route = useRoute()
const router = useRouter()
const tradingStore = useTradingStore()

// 状态
const activeTab = ref<'terminal' | 'orders' | 'positions'>('terminal')
const loading = ref(false)

// 方法
const switchTab = (tab: 'terminal' | 'orders' | 'positions') => {
  activeTab.value = tab
  // 更新URL参数
  router.push({ 
    path: '/trading', 
    query: { ...route.query, tab } 
  })
}

const refreshData = async () => {
  try {
    loading.value = true
    await tradingStore.refresh()
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新失败:', error)
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

// 初始化
onMounted(() => {
  // 从URL参数获取初始标签
  const tab = route.query.tab as string
  if (tab && ['terminal', 'orders', 'positions'].includes(tab)) {
    activeTab.value = tab as 'terminal' | 'orders' | 'positions'
  }
  
  // 初始化交易数据
  tradingStore.initialize()
})
</script>

<style scoped>
.trading-view {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.trading-header {
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

.trading-content {
  background: white;
  border-radius: 8px;
  overflow: hidden;
}

.tab-content {
  min-height: 600px;
}
</style>
