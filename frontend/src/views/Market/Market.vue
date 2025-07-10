<template>
  <div class="market-page">
    <el-container class="market-container">
      <el-aside width="300px" class="market-aside">
        <div class="aside-header">
          <el-input placeholder="Search stock..." :prefix-icon="Search" />
        </div>
        <el-tabs v-model="activeTab" class="market-tabs">
          <el-tab-pane label="Watchlist" name="watchlist">
            <el-table :data="watchlistData" stripe height="calc(100vh - 180px)">
              <el-table-column prop="name" label="Name" />
              <el-table-column prop="price" label="Price" />
              <el-table-column prop="change" label="Change" />
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="Movers" name="movers">
            <p>Top movers list will be here.</p>
          </el-tab-pane>
        </el-tabs>
      </el-aside>
      <el-main class="market-main">
        <h2>Market Details</h2>
        <p>Select a stock from the list to see details and charts.</p>
        <div class="chart-placeholder">Chart Area</div>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Search } from '@element-plus/icons-vue'

const activeTab = ref('watchlist')

const watchlistData = ref([
  { name: 'AAPL', price: '172.28', change: '+1.5%' },
  { name: 'GOOGL', price: '139.74', change: '-0.8%' },
  { name: 'MSFT', price: '370.95', change: '+0.5%' },
  { name: 'TSLA', price: '245.01', change: '+2.1%' },
])
</script>

<style scoped>
.market-page { height: 100%; }
.market-container { height: calc(100vh - 100px); }
.market-aside { display: flex; flex-direction: column; border-right: 1px solid #eee; }
.aside-header { padding: 10px; border-bottom: 1px solid #eee; }
.market-tabs { flex-grow: 1; display: flex; flex-direction: column; }
.market-tabs .el-tabs__content { flex-grow: 1; }
.market-main { padding: 20px; }
.chart-placeholder { margin-top: 20px; height: 300px; background-color: #f5f7fa; display: flex; align-items: center; justify-content: center; color: #909399; border-radius: 4px; }
</style>
