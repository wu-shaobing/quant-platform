<template>
  <div class="stock-detail-page">
    <div class="container mx-auto p-6">
      <div class="bg-white rounded-lg shadow-lg p-6">
        <h1 class="text-2xl font-bold text-gray-800 mb-4">股票详情</h1>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h2 class="text-lg font-semibold mb-2">基本信息</h2>
            <div class="space-y-2">
              <p><span class="font-medium">股票代码:</span> {{ route.params.symbol }}</p>
              <p><span class="font-medium">股票名称:</span> 加载中...</p>
              <p><span class="font-medium">当前价格:</span> 加载中...</p>
            </div>
          </div>
          <div>
            <h2 class="text-lg font-semibold mb-2">操作</h2>
            <div class="space-y-2">
              <button class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                买入
              </button>
              <button class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 ml-2">
                卖出
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

onMounted(() => {
  console.log('股票详情页面加载，股票代码:', route.params.symbol)
})
</script>

<style scoped>
.stock-detail-page {
  min-height: calc(100vh - 64px);
  background-color: #f5f5f5;
}
</style> 