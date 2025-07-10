<template>
  <div class="component-showcase">
    <div class="showcase-header">
      <h1>组件展示与测试中心</h1>
      <p>这里展示了系统中的各种组件和功能测试页面</p>
    </div>
    
    <div class="showcase-grid">
      <!-- 认证组件区域 -->
      <el-card class="showcase-card">
        <template #header>
          <div class="card-header">
            <el-icon><User /></el-icon>
            <span>认证组件</span>
          </div>
        </template>
        
        <div class="component-list">
          <div class="component-item">
            <h4>滑轨验证组件</h4>
            <p>现代化的滑轨验证码组件，支持拖拽验证和防机器人检测</p>
            <div class="component-actions">
              <el-button @click="goToSliderTest" type="primary" size="small">
                测试滑轨验证
              </el-button>
              <el-button @click="goToLogin" size="small">
                查看登录页面
              </el-button>
            </div>
          </div>
          
          <div class="component-item">
            <h4>用户认证</h4>
            <p>完整的用户认证流程，包括登录、注册、密码重置等功能</p>
            <div class="component-actions">
              <el-button @click="goToLogin" type="primary" size="small">
                前往登录
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
      
      <!-- 市场数据组件区域 -->
      <el-card class="showcase-card">
        <template #header>
          <div class="card-header">
            <el-icon><TrendCharts /></el-icon>
            <span>市场数据组件</span>
          </div>
        </template>
        
        <div class="component-list">
          <div class="component-item">
            <h4>实时行情</h4>
            <p>实时市场数据展示，支持多种金融产品</p>
            <div class="component-actions">
              <el-button @click="goToMarket" type="primary" size="small">
                查看行情
              </el-button>
            </div>
          </div>
          
          <div class="component-item">
            <h4>K线图表</h4>
            <p>专业的K线图表组件，支持多种技术指标</p>
            <div class="component-actions">
              <el-button @click="goToCharts" type="primary" size="small">
                查看图表
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
      
      <!-- 交易组件区域 -->
      <el-card class="showcase-card">
        <template #header>
          <div class="card-header">
            <el-icon><Money /></el-icon>
            <span>交易组件</span>
          </div>
        </template>
        
        <div class="component-list">
          <div class="component-item">
            <h4>交易面板</h4>
            <p>专业的交易下单界面，支持多种订单类型</p>
            <div class="component-actions">
              <el-button @click="goToTrading" type="primary" size="small">
                查看交易
              </el-button>
            </div>
          </div>
          
          <div class="component-item">
            <h4>订单管理</h4>
            <p>订单列表、历史记录、交易统计等功能</p>
            <div class="component-actions">
              <el-button @click="goToOrders" type="primary" size="small">
                查看订单
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
      
      <!-- 策略组件区域 -->
      <el-card class="showcase-card">
        <template #header>
          <div class="card-header">
            <el-icon><Setting /></el-icon>
            <span>策略组件</span>
          </div>
        </template>
        
        <div class="component-list">
          <div class="component-item">
            <h4>策略编辑器</h4>
            <p>可视化策略编辑器，支持拖拽式策略构建</p>
            <div class="component-actions">
              <el-button @click="goToStrategy" type="primary" size="small">
                策略编辑
              </el-button>
            </div>
          </div>
          
          <div class="component-item">
            <h4>回测系统</h4>
            <p>强大的策略回测功能，支持多种回测指标</p>
            <div class="component-actions">
              <el-button @click="goToBacktest" type="primary" size="small">
                策略回测
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>
    
    <div class="showcase-footer">
      <el-divider />
      <p>更多组件和功能正在开发中...</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { User, TrendCharts, Money, Setting } from '@element-plus/icons-vue'

const router = useRouter()

// 导航方法
const goToSliderTest = () => {
  router.push('/test-slider')
}

const goToLogin = () => {
  router.push('/login')
}

const goToMarket = () => {
  router.push('/market')
}

const goToCharts = () => {
  router.push('/market/charts')
}

const goToTrading = () => {
  router.push('/trading')
}

const goToOrders = () => {
  router.push('/trading/orders')
}

const goToStrategy = () => {
  router.push('/strategy')
}

const goToBacktest = () => {
  router.push('/backtest')
}
</script>

<style scoped lang="scss">
.component-showcase {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.showcase-header {
  text-align: center;
  margin-bottom: 32px;
  
  h1 {
    font-size: 32px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin-bottom: 8px;
  }
  
  p {
    font-size: 16px;
    color: var(--el-text-color-regular);
    margin: 0;
  }
}

.showcase-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.showcase-card {
  height: fit-content;
  
  .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
}

.component-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.component-item {
  padding: 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-fill-color-extra-light);
  
  h4 {
    margin: 0 0 8px 0;
    font-size: 16px;
    font-weight: 600;
    color: var(--el-text-color-primary);
  }
  
  p {
    margin: 0 0 12px 0;
    font-size: 14px;
    color: var(--el-text-color-regular);
    line-height: 1.5;
  }
}

.component-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.showcase-footer {
  text-align: center;
  
  p {
    color: var(--el-text-color-placeholder);
    font-style: italic;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .showcase-grid {
    grid-template-columns: 1fr;
  }
  
  .component-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
}

// 暗色主题适配
.dark {
  .component-item {
    background: var(--el-fill-color-dark);
    border-color: var(--el-border-color-dark);
  }
}
</style>