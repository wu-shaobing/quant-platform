<template>
  <div class="order-form">
    <div class="form-header">
      <h3>下单交易</h3>
      <div class="account-info">
        <span>可用资金: {{ formatCurrency(availableCash) }}</span>
      </div>
    </div>
    
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
      @submit.prevent="handleSubmit"
    >
      <!-- 股票选择 -->
      <el-form-item label="股票代码" prop="symbol">
        <el-autocomplete
          v-model="form.symbol"
          :fetch-suggestions="searchStocks"
          placeholder="输入股票代码或名称"
          style="width: 100%"
          :loading="searchLoading"
          @select="handleStockSelect"
          @blur="handleSymbolBlur"
        >
          <template #default="{ item }">
            <div class="stock-option">
              <div class="stock-info">
                <span class="stock-code">{{ item.symbol }}</span>
                <span class="stock-name">{{ item.name }}</span>
              </div>
              <div class="stock-price">
                <span 
                  class="price"
                  :class="getPriceClass(item.changePercent)"
                >
                  {{ formatPrice(item.currentPrice) }}
                </span>
                <span 
                  class="change"
                  :class="getPriceClass(item.changePercent)"
                >
                  {{ formatChange(item.change, item.changePercent) }}
                </span>
              </div>
            </div>
          </template>
        </el-autocomplete>
      </el-form-item>
      
      <!-- 交易方向 -->
      <el-form-item label="交易方向">
        <el-radio-group v-model="form.side" @change="handleSideChange">
          <el-radio-button value="buy" class="buy-button">
            买入
          </el-radio-button>
          <el-radio-button value="sell" class="sell-button">
            卖出
          </el-radio-button>
        </el-radio-group>
      </el-form-item>
      
      <!-- 订单类型 -->
      <el-form-item label="订单类型" prop="orderType">
        <el-select v-model="form.orderType" style="width: 100%" @change="handleOrderTypeChange">
          <el-option label="限价单" value="limit" />
          <el-option label="市价单" value="market" />
          <el-option label="止损单" value="stop" />
          <el-option label="止盈单" value="stop-profit" />
        </el-select>
      </el-form-item>
      
      <!-- 价格设置 -->
      <el-form-item 
        v-if="showPriceInput" 
        label="委托价格" 
        prop="price"
      >
        <div class="price-input-group">
          <el-input-number
            v-model="form.price"
            :precision="2"
            :step="0.01"
            :min="0"
            style="width: 100%"
            placeholder="输入委托价格"
            @change="calculateAmount"
          />
          <div class="price-buttons">
            <el-button 
              size="small" 
              @click="setPriceByMarket(-0.01)"
              :disabled="!selectedStock"
            >
              -1%
            </el-button>
            <el-button 
              size="small" 
              @click="setPriceByMarket(0)"
              :disabled="!selectedStock"
            >
              现价
            </el-button>
            <el-button 
              size="small" 
              @click="setPriceByMarket(0.01)"
              :disabled="!selectedStock"
            >
              +1%
            </el-button>
          </div>
        </div>
      </el-form-item>
      
      <!-- 数量设置 -->
      <el-form-item label="委托数量" prop="quantity">
        <div class="quantity-input-group">
          <el-input-number
            v-model="form.quantity"
            :precision="0"
            :step="100"
            :min="0"
            :max="maxQuantity"
            style="width: 100%"
            placeholder="输入委托数量"
            @change="calculateAmount"
          />
          <div class="quantity-buttons">
            <el-button 
              size="small" 
              @click="setQuantityByPercent(0.25)"
              :disabled="!canCalculateQuantity"
            >
              1/4
            </el-button>
            <el-button 
              size="small" 
              @click="setQuantityByPercent(0.5)"
              :disabled="!canCalculateQuantity"
            >
              1/2
            </el-button>
            <el-button 
              size="small" 
              @click="setQuantityByPercent(1)"
              :disabled="!canCalculateQuantity"
            >
              全部
            </el-button>
          </div>
        </div>
      </el-form-item>
      
      <!-- 金额显示 -->
      <el-form-item label="委托金额">
        <div class="amount-display">
          <span class="amount">{{ formatCurrency(estimatedAmount) }}</span>
          <span class="fee">手续费: {{ formatCurrency(estimatedFee) }}</span>
        </div>
      </el-form-item>
      
      <!-- 持仓信息 (卖出时显示) -->
      <el-form-item v-if="form.side === 'sell' && currentPosition" label="持仓信息">
        <div class="position-info">
          <div class="position-row">
            <span>持仓数量:</span>
            <span>{{ currentPosition.totalQuantity }}</span>
          </div>
          <div class="position-row">
            <span>可卖数量:</span>
            <span>{{ currentPosition.availableQuantity }}</span>
          </div>
          <div class="position-row">
            <span>成本价:</span>
            <span>{{ formatPrice(currentPosition.avgPrice) }}</span>
          </div>
          <div class="position-row">
            <span>浮动盈亏:</span>
            <span :class="getPriceClass(currentPosition.unrealizedPnlPercent)">
              {{ formatCurrency(currentPosition.unrealizedPnl) }}
              ({{ formatPercent(currentPosition.unrealizedPnlPercent) }})
            </span>
          </div>
        </div>
      </el-form-item>
      
      <!-- 风险提示 -->
      <div v-if="riskWarnings.length > 0" class="risk-warnings">
        <el-alert
          v-for="warning in riskWarnings"
          :key="warning.type"
          :title="warning.message"
          :type="warning.level"
          :closable="false"
          show-icon
        />
      </div>
      
      <!-- 提交按钮 -->
      <el-form-item>
        <el-button
          type="primary"
          :loading="submitting"
          :disabled="!canSubmit"
          style="width: 100%"
          size="large"
          @click="handleSubmit"
        >
          {{ submitButtonText }}
        </el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useOrderForm } from '@/composables/trading/useOrderForm'
import { useMarketData } from '@/composables/useMarketData'
import { useTradingStore } from '@/stores/modules/trading'
import { useUserStore } from '@/stores/modules/user'
import { formatCurrency, formatPrice, formatPercent, formatChange } from '@/utils/formatters'
import type { OrderFormData, StockInfo, Position, RiskWarning } from '@/types/trading'

interface Props {
  defaultSymbol?: string
  defaultSide?: 'buy' | 'sell'
  quickTradeMode?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  defaultSymbol: '',
  defaultSide: 'buy',
  quickTradeMode: false
})

const emit = defineEmits<{
  (e: 'submit', data: OrderFormData): void
  (e: 'stock-select', stock: StockInfo): void
  (e: 'side-change', side: 'buy' | 'sell'): void
}>()

// Stores
const tradingStore = useTradingStore()
const userStore = useUserStore()

// Form相关
const formRef = ref()
const {
  form,
  rules,
  submitting,
  resetForm,
  validateForm,
  submitOrder
} = useOrderForm()

// 市场数据相关
const {
  searchStocks: searchStocksApi,
  getStockInfo,
  subscribeQuote,
  unsubscribeQuote
} = useMarketData()

// 状态
const searchLoading = ref(false)
const selectedStock = ref<StockInfo | null>(null)

// 计算属性
const availableCash = computed(() => tradingStore.account?.availableCash || 0)

const currentPosition = computed(() => {
  if (!form.symbol) return null
  return tradingStore.getPositionBySymbol(form.symbol)
})

const showPriceInput = computed(() => {
  return ['limit', 'stop', 'stop-profit'].includes(form.orderType)
})

const maxQuantity = computed(() => {
  if (form.side === 'sell' && currentPosition.value) {
    return currentPosition.value.availableQuantity
  }
  
  if (form.side === 'buy' && form.price > 0) {
    return Math.floor(availableCash.value / form.price / 100) * 100
  }
  
  return 0
})

const canCalculateQuantity = computed(() => {
  return form.side === 'buy' && form.price > 0 && availableCash.value > 0
})

const estimatedAmount = computed(() => {
  if (form.orderType === 'market' && selectedStock.value) {
    return selectedStock.value.currentPrice * form.quantity
  }
  return form.price * form.quantity
})

const estimatedFee = computed(() => {
  // 简化的手续费计算
  const feeRate = 0.0003 // 万分之三
  const minFee = 5 // 最低5元
  const fee = Math.max(estimatedAmount.value * feeRate, minFee)
  return fee
})

const canSubmit = computed(() => {
  if (submitting.value) return false
  if (!form.symbol || !form.quantity) return false
  
  if (showPriceInput.value && !form.price) return false
  
  if (form.side === 'sell') {
    return currentPosition.value && form.quantity <= currentPosition.value.availableQuantity
  }
  
  if (form.side === 'buy') {
    const totalAmount = estimatedAmount.value + estimatedFee.value
    return totalAmount <= availableCash.value
  }
  
  return false
})

const submitButtonText = computed(() => {
  if (submitting.value) return '提交中...'
  
  const action = form.side === 'buy' ? '买入' : '卖出'
  const symbol = selectedStock.value?.name || form.symbol
  
  if (form.quantity && symbol) {
    return `${action} ${symbol} ${form.quantity}股`
  }
  
  return action
})

const riskWarnings = computed(() => {
  const warnings: RiskWarning[] = []
  
  // 检查资金风险
  if (form.side === 'buy') {
    const totalAmount = estimatedAmount.value + estimatedFee.value
    const riskRatio = totalAmount / availableCash.value
    
    if (riskRatio > 0.9) {
      warnings.push({
        type: 'capital',
        level: 'warning',
        message: '此笔交易将占用大部分可用资金，请注意风险控制'
      })
    }
  }
  
  // 检查价格偏离
  if (showPriceInput.value && selectedStock.value && form.price > 0) {
    const deviation = Math.abs(form.price - selectedStock.value.currentPrice) / selectedStock.value.currentPrice
    
    if (deviation > 0.05) {
      warnings.push({
        type: 'price',
        level: 'warning',
        message: '委托价格偏离市价较大，请确认价格是否正确'
      })
    }
  }
  
  return warnings
})

// 方法
const searchStocks = async (queryString: string, cb: Function) => {
  if (!queryString) {
    cb([])
    return
  }
  
  searchLoading.value = true
  
  try {
    const results = await searchStocksApi(queryString)
    cb(results)
  } catch (error) {
    console.error('搜索股票失败:', error)
    cb([])
  } finally {
    searchLoading.value = false
  }
}

const handleStockSelect = async (item: StockInfo) => {
  selectedStock.value = item
  form.symbol = item.symbol
  
  // 设置默认价格为当前价
  if (showPriceInput.value) {
    form.price = item.currentPrice
  }
  
  // 订阅实时行情
  subscribeQuote(item.symbol)
  
  emit('stock-select', item)
  
  // 重新计算金额
  calculateAmount()
}

const handleSymbolBlur = async () => {
  if (form.symbol && !selectedStock.value) {
    try {
      const stockInfo = await getStockInfo(form.symbol)
      if (stockInfo) {
        await handleStockSelect(stockInfo)
      }
    } catch (error) {
      console.error('获取股票信息失败:', error)
    }
  }
}

const handleSideChange = (side: 'buy' | 'sell') => {
  emit('side-change', side)
  
  // 卖出时检查持仓
  if (side === 'sell' && !currentPosition.value) {
    ElMessage.warning('您没有该股票的持仓')
  }
  
  // 重新计算最大数量
  if (form.quantity > maxQuantity.value) {
    form.quantity = maxQuantity.value
  }
}

const handleOrderTypeChange = () => {
  // 市价单时清空价格
  if (form.orderType === 'market') {
    form.price = 0
  } else if (selectedStock.value) {
    form.price = selectedStock.value.currentPrice
  }
  
  calculateAmount()
}

const setPriceByMarket = (offset: number) => {
  if (!selectedStock.value) return
  
  const basePrice = selectedStock.value.currentPrice
  form.price = Number((basePrice * (1 + offset)).toFixed(2))
  calculateAmount()
}

const setQuantityByPercent = (percent: number) => {
  if (form.side === 'sell' && currentPosition.value) {
    form.quantity = Math.floor(currentPosition.value.availableQuantity * percent / 100) * 100
  } else if (form.side === 'buy' && form.price > 0) {
    const maxAmount = availableCash.value * percent
    form.quantity = Math.floor(maxAmount / form.price / 100) * 100
  }
  
  calculateAmount()
}

const calculateAmount = () => {
  // 触发响应式更新
}

const getPriceClass = (changePercent: number) => {
  if (changePercent > 0) return 'price-up'
  if (changePercent < 0) return 'price-down'
  return 'price-neutral'
}

const handleSubmit = async () => {
  try {
    // 表单验证
    await validateForm()
    
    // 风险确认
    if (riskWarnings.value.some(w => w.level === 'error')) {
      ElMessage.error('存在风险错误，无法提交订单')
      return
    }
    
    if (riskWarnings.value.some(w => w.level === 'warning')) {
      await ElMessageBox.confirm(
        '检测到风险警告，是否继续提交订单？',
        '风险提示',
        {
          confirmButtonText: '继续提交',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
    }
    
    // 提交订单
    await submitOrder()
    
    emit('submit', { ...form })
    
    ElMessage.success('订单提交成功')
    
    // 重置表单
    resetForm()
    selectedStock.value = null
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('提交订单失败:', error)
      ElMessage.error(error instanceof Error ? error.message : '提交订单失败')
    }
  }
}

// 初始化
onMounted(() => {
  if (props.defaultSymbol) {
    form.symbol = props.defaultSymbol
    handleSymbolBlur()
  }
  
  if (props.defaultSide) {
    form.side = props.defaultSide
  }
})

// 监听选中股票的行情更新
watch(selectedStock, (newStock, oldStock) => {
  if (oldStock) {
    unsubscribeQuote(oldStock.symbol)
  }
  
  if (newStock) {
    subscribeQuote(newStock.symbol)
  }
})
</script>

<style scoped>
.order-form {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e8e8e8;
}

.form-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.account-info {
  font-size: 14px;
  color: #666;
}

.stock-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.stock-info {
  display: flex;
  flex-direction: column;
}

.stock-code {
  font-weight: 600;
  color: #333;
}

.stock-name {
  font-size: 12px;
  color: #666;
}

.stock-price {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.price, .change {
  font-size: 14px;
}

.price-up {
  color: #f56c6c;
}

.price-down {
  color: #67c23a;
}

.price-neutral {
  color: #909399;
}

.buy-button {
  color: #f56c6c;
}

.sell-button {
  color: #67c23a;
}

.price-input-group, .quantity-input-group {
  width: 100%;
}

.price-buttons, .quantity-buttons {
  display: flex;
  gap: 4px;
  margin-top: 8px;
}

.amount-display {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.amount {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.fee {
  font-size: 12px;
  color: #666;
}

.position-info {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
}

.position-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.position-row:last-child {
  margin-bottom: 0;
}

.risk-warnings {
  margin: 16px 0;
}

.risk-warnings .el-alert {
  margin-bottom: 8px;
}

.risk-warnings .el-alert:last-child {
  margin-bottom: 0;
}

@media (max-width: 768px) {
  .order-form {
    padding: 16px;
  }
  
  .form-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .stock-option {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .price-buttons, .quantity-buttons {
    justify-content: space-between;
  }
}
</style>