<template>
  <div class="order-book">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>订单簿</span>
          <el-select v-model="selectedSymbol" placeholder="选择股票" size="small" style="width: 120px">
            <el-option label="平安银行" value="000001" />
            <el-option label="万科A" value="000002" />
            <el-option label="招商银行" value="600036" />
          </el-select>
        </div>
      </template>
      
      <div class="order-book-content">
        <!-- 卖盘 -->
        <div class="sell-orders">
          <div class="section-title">卖盘</div>
          <div class="order-row header">
            <span>价格</span>
            <span>数量</span>
          </div>
          <div 
            v-for="(order, index) in sellOrders" 
            :key="`sell-${index}`"
            class="order-row sell"
          >
            <span class="price">{{ order.price.toFixed(2) }}</span>
            <span class="quantity">{{ order.quantity }}</span>
          </div>
        </div>
        
        <!-- 当前价格 -->
        <div class="current-price">
          <div class="price-display">
            <span class="current">{{ currentPrice.toFixed(2) }}</span>
            <span :class="priceChange >= 0 ? 'change-up' : 'change-down'">
              {{ priceChange >= 0 ? '+' : '' }}{{ priceChange.toFixed(2) }}
            </span>
          </div>
        </div>
        
        <!-- 买盘 -->
        <div class="buy-orders">
          <div class="section-title">买盘</div>
          <div class="order-row header">
            <span>价格</span>
            <span>数量</span>
          </div>
          <div 
            v-for="(order, index) in buyOrders" 
            :key="`buy-${index}`"
            class="order-row buy"
          >
            <span class="price">{{ order.price.toFixed(2) }}</span>
            <span class="quantity">{{ order.quantity }}</span>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// 订单接口
interface Order {
  price: number
  quantity: number
}

// 选中的股票代码
const selectedSymbol = ref('000001')

// 当前价格
const currentPrice = ref(13.20)
const priceChange = ref(0.70)

// 模拟卖盘数据（价格从高到低）
const sellOrders = ref<Order[]>([
  { price: 13.25, quantity: 1200 },
  { price: 13.24, quantity: 800 },
  { price: 13.23, quantity: 1500 },
  { price: 13.22, quantity: 900 },
  { price: 13.21, quantity: 2000 }
])

// 模拟买盘数据（价格从高到低）
const buyOrders = ref<Order[]>([
  { price: 13.19, quantity: 1800 },
  { price: 13.18, quantity: 1100 },
  { price: 13.17, quantity: 1600 },
  { price: 13.16, quantity: 700 },
  { price: 13.15, quantity: 2200 }
])
</script>

<style scoped>
.order-book {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.order-book-content {
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

.section-title {
  font-weight: bold;
  margin-bottom: 8px;
  text-align: center;
  padding: 4px 0;
  border-bottom: 1px solid #e5e7eb;
}

.order-row {
  display: flex;
  justify-content: space-between;
  padding: 2px 8px;
  border-radius: 2px;
}

.order-row.header {
  font-weight: bold;
  background-color: #f3f4f6;
  margin-bottom: 4px;
}

.order-row.sell {
  background-color: #fef2f2;
  color: #dc2626;
}

.order-row.buy {
  background-color: #f0fdf4;
  color: #16a34a;
}

.order-row.sell:hover {
  background-color: #fee2e2;
}

.order-row.buy:hover {
  background-color: #dcfce7;
}

.current-price {
  margin: 16px 0;
  text-align: center;
  padding: 8px;
  background-color: #f9fafb;
  border-radius: 4px;
}

.price-display {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
}

.current {
  font-size: 16px;
  font-weight: bold;
  color: #1f2937;
}

.change-up {
  color: #16a34a;
  font-size: 12px;
}

.change-down {
  color: #dc2626;
  font-size: 12px;
}

.price {
  font-weight: bold;
}

.quantity {
  text-align: right;
}
</style> 