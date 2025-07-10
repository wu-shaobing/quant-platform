<template>
  <div class="quick-order-form">
    <div class="form-header">
      <h3>快速下单</h3>
    </div>
    
    <div class="quick-actions">
      <div class="symbol-display">
        <span class="symbol">{{ symbol }}</span>
        <span class="price">¥12.85</span>
        <span class="change positive">+1.18%</span>
      </div>
      
      <div class="preset-amounts">
        <div class="amount-label">快速金额</div>
        <div class="amount-buttons">
          <el-button
            v-for="amount in presetAmounts"
            :key="amount"
            size="small"
            @click="handleQuickOrder(amount)"
          >
            {{ formatAmount(amount) }}
          </el-button>
        </div>
      </div>
      
      <div class="order-buttons">
        <el-button 
          type="danger" 
          size="large"
          class="buy-button"
          @click="handleQuickBuy"
        >
          买入
        </el-button>
        <el-button 
          type="success" 
          size="large"
          class="sell-button"
          @click="handleQuickSell"
        >
          卖出
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'

interface Props {
  symbol: string
  presetAmounts: number[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'quick-order', data: { symbol: string; amount: number; side: string }): void
}>()

const formatAmount = (amount: number) => {
  if (amount >= 10000) {
    return `${(amount / 10000).toFixed(0)}万`
  }
  return `${amount.toLocaleString()}`
}

const handleQuickOrder = (amount: number) => {
  emit('quick-order', {
    symbol: props.symbol,
    amount,
    side: 'buy'
  })
}

const handleQuickBuy = () => {
  ElMessage.success('快速买入功能')
}

const handleQuickSell = () => {
  ElMessage.success('快速卖出功能')
}
</script>

<style scoped>
.quick-order-form {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-header h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #333;
}

.symbol-display {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.symbol {
  font-weight: bold;
  color: #333;
}

.price {
  font-weight: bold;
  color: #333;
}

.change.positive {
  color: #f56c6c;
}

.change.negative {
  color: #67c23a;
}

.preset-amounts {
  margin-bottom: 16px;
}

.amount-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.amount-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.order-buttons {
  display: flex;
  gap: 12px;
}

.buy-button,
.sell-button {
  flex: 1;
}
</style>