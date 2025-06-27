<template>
  <div class="position-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>持仓列表</span>
        </div>
      </template>
      
      <el-table :data="positions" style="width: 100%">
        <el-table-column prop="symbol" label="股票代码" width="120" />
        <el-table-column prop="name" label="股票名称" width="150" />
        <el-table-column prop="quantity" label="持仓数量" width="120" align="right" />
        <el-table-column prop="avgPrice" label="成本价" width="120" align="right">
          <template #default="scope">
            ¥{{ scope.row.avgPrice.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="currentPrice" label="现价" width="120" align="right">
          <template #default="scope">
            ¥{{ scope.row.currentPrice.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="marketValue" label="市值" width="120" align="right">
          <template #default="scope">
            ¥{{ scope.row.marketValue.toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="profitLoss" label="盈亏" width="120" align="right">
          <template #default="scope">
            <span :class="scope.row.profitLoss >= 0 ? 'text-green-600' : 'text-red-600'">
              ¥{{ scope.row.profitLoss.toFixed(2) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="profitLossRate" label="盈亏比例" width="120" align="right">
          <template #default="scope">
            <span :class="scope.row.profitLossRate >= 0 ? 'text-green-600' : 'text-red-600'">
              {{ (scope.row.profitLossRate * 100).toFixed(2) }}%
            </span>
          </template>
        </el-table-column>
      </el-table>
      
      <div v-if="positions.length === 0" class="empty-state">
        <p class="text-gray-500">暂无持仓数据</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// 持仓数据接口
interface Position {
  symbol: string
  name: string
  quantity: number
  avgPrice: number
  currentPrice: number
  marketValue: number
  profitLoss: number
  profitLossRate: number
}

// 模拟持仓数据
const positions = ref<Position[]>([
  {
    symbol: '000001',
    name: '平安银行',
    quantity: 1000,
    avgPrice: 12.50,
    currentPrice: 13.20,
    marketValue: 13200,
    profitLoss: 700,
    profitLossRate: 0.056
  },
  {
    symbol: '000002',
    name: '万科A',
    quantity: 500,
    avgPrice: 18.80,
    currentPrice: 17.90,
    marketValue: 8950,
    profitLoss: -450,
    profitLossRate: -0.048
  }
])

// 计算总市值
const totalMarketValue = computed(() => {
  return positions.value.reduce((sum, pos) => sum + pos.marketValue, 0)
})

// 计算总盈亏
const totalProfitLoss = computed(() => {
  return positions.value.reduce((sum, pos) => sum + pos.profitLoss, 0)
})
</script>

<style scoped>
.position-list {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.text-green-600 {
  color: #16a34a;
}

.text-red-600 {
  color: #dc2626;
}

.text-gray-500 {
  color: #6b7280;
}
</style> 