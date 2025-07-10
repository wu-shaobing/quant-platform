<template>
  <div class="trading-terminal">
    <div class="terminal-header">
      <div class="header-left">
        <el-select v-model="selectedSymbol" placeholder="选择交易品种" @change="onSymbolChange">
          <el-option
            v-for="symbol in symbols"
            :key="symbol.code"
            :label="`${symbol.name} (${symbol.code})`"
            :value="symbol.code"
          />
        </el-select>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button :type="activeTab === 'buy' ? 'primary' : 'default'" @click="activeTab = 'buy'">
            买入
          </el-button>
          <el-button :type="activeTab === 'sell' ? 'primary' : 'default'" @click="activeTab = 'sell'">
            卖出
          </el-button>
        </el-button-group>
      </div>
    </div>

    <div class="terminal-content">
      <!-- 价格信息 -->
      <div class="price-info">
        <div class="price-item">
          <span class="label">最新价</span>
          <span class="value" :class="priceChangeClass">{{ currentPrice }}</span>
        </div>
        <div class="price-item">
          <span class="label">涨跌幅</span>
          <span class="value" :class="priceChangeClass">{{ priceChange }}%</span>
        </div>
        <div class="price-item">
          <span class="label">买一价</span>
          <span class="value bid">{{ bidPrice }}</span>
        </div>
        <div class="price-item">
          <span class="label">卖一价</span>
          <span class="value ask">{{ askPrice }}</span>
        </div>
      </div>

      <!-- 交易表单 -->
      <div class="trading-form">
        <el-form :model="orderForm" :rules="rules" ref="formRef" label-width="80px">
          <el-form-item label="订单类型" prop="orderType">
            <el-select v-model="orderForm.orderType" @change="onOrderTypeChange">
              <el-option label="限价单" value="limit" />
              <el-option label="市价单" value="market" />
              <el-option label="止损单" value="stop" />
              <el-option label="止盈单" value="takeProfit" />
            </el-select>
          </el-form-item>

          <el-form-item 
            v-if="orderForm.orderType === 'limit'" 
            label="价格" 
            prop="price"
          >
            <el-input-number
              v-model="orderForm.price"
              :precision="2"
              :step="0.01"
              :min="0"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="数量" prop="quantity">
            <el-input-number
              v-model="orderForm.quantity"
              :precision="0"
              :step="100"
              :min="100"
              style="width: 100%"
            />
          </el-form-item>

          <el-form-item label="有效期" prop="timeInForce">
            <el-select v-model="orderForm.timeInForce">
              <el-option label="当日有效" value="DAY" />
              <el-option label="立即成交或撤销" value="IOC" />
              <el-option label="全部成交或撤销" value="FOK" />
              <el-option label="撤销前有效" value="GTC" />
            </el-select>
          </el-form-item>

          <!-- 止损止盈 -->
          <el-form-item>
            <div class="stop-profit-section">
              <el-checkbox v-model="orderForm.enableStopLoss">止损</el-checkbox>
              <el-input-number
                v-if="orderForm.enableStopLoss"
                v-model="orderForm.stopLossPrice"
                :precision="2"
                :step="0.01"
                :min="0"
                size="small"
                style="width: 120px; margin-left: 8px"
              />
            </div>
          </el-form-item>

          <el-form-item>
            <div class="stop-profit-section">
              <el-checkbox v-model="orderForm.enableTakeProfit">止盈</el-checkbox>
              <el-input-number
                v-if="orderForm.enableTakeProfit"
                v-model="orderForm.takeProfitPrice"
                :precision="2"
                :step="0.01"
                :min="0"
                size="small"
                style="width: 120px; margin-left: 8px"
              />
            </div>
          </el-form-item>

          <!-- 交易按钮 -->
          <el-form-item>
            <el-button
              :type="activeTab === 'buy' ? 'success' : 'danger'"
              :loading="submitting"
              @click="submitOrder"
              style="width: 100%"
            >
              {{ activeTab === 'buy' ? '买入' : '卖出' }}
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 账户信息 -->
      <div class="account-info">
        <div class="info-item">
          <span class="label">可用资金</span>
          <span class="value">{{ formatNumber(accountInfo.availableBalance) }}</span>
        </div>
        <div class="info-item">
          <span class="label">持仓市值</span>
          <span class="value">{{ formatNumber(accountInfo.positionValue) }}</span>
        </div>
        <div class="info-item">
          <span class="label">总资产</span>
          <span class="value">{{ formatNumber(accountInfo.totalAssets) }}</span>
        </div>
        <div class="info-item">
          <span class="label">今日盈亏</span>
          <span class="value" :class="accountInfo.todayPnl >= 0 ? 'profit' : 'loss'">
            {{ accountInfo.todayPnl >= 0 ? '+' : '' }}{{ formatNumber(accountInfo.todayPnl) }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'

interface Symbol {
  code: string
  name: string
  price: number
  change: number
  bidPrice: number
  askPrice: number
}

interface OrderForm {
  orderType: string
  price: number
  quantity: number
  timeInForce: string
  enableStopLoss: boolean
  stopLossPrice: number
  enableTakeProfit: boolean
  takeProfitPrice: number
}

interface AccountInfo {
  availableBalance: number
  positionValue: number
  totalAssets: number
  todayPnl: number
}

const activeTab = ref<'buy' | 'sell'>('buy')
const selectedSymbol = ref('')
const submitting = ref(false)
const formRef = ref<FormInstance>()

// 模拟数据
const symbols = ref<Symbol[]>([
  { code: 'IF2312', name: '沪深300主力', price: 3850.2, change: 1.25, bidPrice: 3850.0, askPrice: 3850.4 },
  { code: 'IC2312', name: '中证500主力', price: 5420.8, change: -0.85, bidPrice: 5420.6, askPrice: 5421.0 },
  { code: 'IH2312', name: '上证50主力', price: 2680.5, change: 0.65, bidPrice: 2680.3, askPrice: 2680.7 }
])

const accountInfo = reactive<AccountInfo>({
  availableBalance: 500000,
  positionValue: 150000,
  totalAssets: 650000,
  todayPnl: 2500
})

const orderForm = reactive<OrderForm>({
  orderType: 'limit',
  price: 0,
  quantity: 100,
  timeInForce: 'DAY',
  enableStopLoss: false,
  stopLossPrice: 0,
  enableTakeProfit: false,
  takeProfitPrice: 0
})

// 表单验证规则
const rules = {
  orderType: [{ required: true, message: '请选择订单类型', trigger: 'change' }],
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
  timeInForce: [{ required: true, message: '请选择有效期', trigger: 'change' }]
}

// 计算属性
const currentSymbol = computed(() => {
  return symbols.value.find(s => s.code === selectedSymbol.value)
})

const currentPrice = computed(() => {
  return currentSymbol.value?.price.toFixed(2) || '0.00'
})

const priceChange = computed(() => {
  return currentSymbol.value?.change.toFixed(2) || '0.00'
})

const bidPrice = computed(() => {
  return currentSymbol.value?.bidPrice.toFixed(2) || '0.00'
})

const askPrice = computed(() => {
  return currentSymbol.value?.askPrice.toFixed(2) || '0.00'
})

const priceChangeClass = computed(() => {
  const change = currentSymbol.value?.change || 0
  return change > 0 ? 'profit' : change < 0 ? 'loss' : ''
})

// 格式化数字
const formatNumber = (value: number): string => {
  return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

// 品种变化
const onSymbolChange = () => {
  if (currentSymbol.value) {
    orderForm.price = currentSymbol.value.price
  }
}

// 订单类型变化
const onOrderTypeChange = () => {
  if (orderForm.orderType === 'market') {
    orderForm.price = 0
  } else if (currentSymbol.value) {
    orderForm.price = currentSymbol.value.price
  }
}

// 提交订单
const submitOrder = async () => {
  if (!formRef.value) return
  
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    await ElMessageBox.confirm(
      `确定要${activeTab.value === 'buy' ? '买入' : '卖出'}${selectedSymbol.value}吗？`,
      '确认交易',
      { type: 'warning' }
    )

    submitting.value = true
    
    // 模拟提交订单
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    ElMessage.success('订单提交成功')
    
    // 重置表单
    formRef.value.resetFields()
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('订单提交失败')
    }
  } finally {
    submitting.value = false
  }
}

// 初始化
onMounted(() => {
  selectedSymbol.value = symbols.value[0]?.code || ''
  onSymbolChange()
})
</script>

<style scoped>
.trading-terminal {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.terminal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #ebeef5;
}

.header-left .el-select {
  width: 200px;
}

.terminal-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.price-info {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.price-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.price-item .label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.price-item .value {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.price-item .value.profit {
  color: #f56c6c;
}

.price-item .value.loss {
  color: #67c23a;
}

.price-item .value.bid {
  color: #67c23a;
}

.price-item .value.ask {
  color: #f56c6c;
}

.trading-form {
  flex: 1;
}

.stop-profit-section {
  display: flex;
  align-items: center;
}

.account-info {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 6px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-item .label {
  font-size: 14px;
  color: #606266;
}

.info-item .value {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.info-item .value.profit {
  color: #f56c6c;
}

.info-item .value.loss {
  color: #67c23a;
}

@media (max-width: 768px) {
  .price-info {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .account-info {
    grid-template-columns: 1fr;
  }
}
</style> 