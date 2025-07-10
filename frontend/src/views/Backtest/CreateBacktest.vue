<template>
  <div class="create-backtest-page">
    <div class="container mx-auto p-6">
      <div class="bg-white rounded-lg shadow-lg p-6">
        <h1 class="text-2xl font-bold text-gray-800 mb-6">创建回测</h1>
        
        <form class="space-y-6">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium mb-2">回测名称</label>
              <input 
                type="text" 
                placeholder="输入回测名称"
                class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">选择策略</label>
              <select class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">选择已有策略</option>
                <option value="strategy1">双均线策略</option>
                <option value="strategy2">RSI均值回归</option>
                <option value="strategy3">动量突破策略</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label class="block text-sm font-medium mb-2">开始日期</label>
              <input 
                type="date" 
                class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">结束日期</label>
              <input 
                type="date" 
                class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label class="block text-sm font-medium mb-2">初始资金</label>
              <input 
                type="number" 
                placeholder="1000000"
                class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">手续费率(%)</label>
              <input 
                type="number" 
                placeholder="0.0003"
                step="0.0001"
                class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>
            <div>
              <label class="block text-sm font-medium mb-2">滑点率(%)</label>
              <input 
                type="number" 
                placeholder="0.0001"
                step="0.0001"
                class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium mb-2">股票池</label>
            <textarea 
              placeholder="输入股票代码，用逗号分隔，如：000001,000002,600036"
              rows="3"
              class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium mb-2">备注</label>
            <textarea 
              placeholder="回测说明和备注信息"
              rows="2"
              class="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            ></textarea>
          </div>

          <div class="flex space-x-4">
            <button 
              type="button"
              class="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600"
            >
              开始回测
            </button>
            <button 
              type="button"
              class="bg-gray-500 text-white px-6 py-2 rounded hover:bg-gray-600"
            >
              保存配置
            </button>
            <router-link 
              to="/backtest"
              class="bg-red-500 text-white px-6 py-2 rounded hover:bg-red-600"
            >
              取消
            </router-link>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  console.log('创建回测页面加载')
})
</script>

<style scoped>
.create-backtest-page {
  min-height: calc(100vh - 64px);
  background-color: #f5f5f5;
}
</style> 
 