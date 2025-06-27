<template>
  <div class="backtest-history-page">
    <div class="container mx-auto p-6">
      <div class="bg-white rounded-lg shadow-lg p-6">
        <h1 class="text-2xl font-bold text-gray-800 mb-6">回测历史</h1>
        
        <!-- 筛选器 -->
        <div class="mb-6">
          <div class="flex flex-wrap gap-4 mb-4">
            <select class="px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">全部策略</option>
              <option value="strategy1">双均线策略</option>
              <option value="strategy2">RSI均值回归</option>
              <option value="strategy3">动量突破策略</option>
            </select>
            <select class="px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option value="">全部状态</option>
              <option value="completed">已完成</option>
              <option value="running">运行中</option>
              <option value="failed">失败</option>
            </select>
            <input 
              type="date" 
              class="px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="开始日期"
            >
          </div>
        </div>

        <!-- 回测列表 -->
        <div class="overflow-x-auto">
          <table class="w-full border-collapse">
            <thead>
              <tr class="bg-gray-50">
                <th class="border p-3 text-left">回测名称</th>
                <th class="border p-3 text-left">策略</th>
                <th class="border p-3 text-left">时间范围</th>
                <th class="border p-3 text-left">初始资金</th>
                <th class="border p-3 text-left">总收益率</th>
                <th class="border p-3 text-left">最大回撤</th>
                <th class="border p-3 text-left">夏普比率</th>
                <th class="border p-3 text-left">状态</th>
                <th class="border p-3 text-left">创建时间</th>
                <th class="border p-3 text-left">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td class="border p-3 font-medium">双均线策略回测v1</td>
                <td class="border p-3">双均线策略</td>
                <td class="border p-3">2023-01-01 ~ 2023-12-31</td>
                <td class="border p-3">¥1,000,000</td>
                <td class="border p-3 text-red-500">+15.2%</td>
                <td class="border p-3 text-green-500">-3.5%</td>
                <td class="border p-3">1.85</td>
                <td class="border p-3">
                  <span class="px-2 py-1 rounded text-sm bg-green-100 text-green-800">已完成</span>
                </td>
                <td class="border p-3">2024-01-10 14:30</td>
                <td class="border p-3">
                  <div class="space-x-2">
                    <button class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">
                      查看
                    </button>
                    <button class="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600">
                      下载
                    </button>
                  </div>
                </td>
              </tr>
              <tr>
                <td class="border p-3 font-medium">RSI均值回归测试</td>
                <td class="border p-3">RSI均值回归</td>
                <td class="border p-3">2023-06-01 ~ 2023-12-31</td>
                <td class="border p-3">¥500,000</td>
                <td class="border p-3 text-green-500">-2.1%</td>
                <td class="border p-3 text-green-500">-8.2%</td>
                <td class="border p-3">-0.25</td>
                <td class="border p-3">
                  <span class="px-2 py-1 rounded text-sm bg-green-100 text-green-800">已完成</span>
                </td>
                <td class="border p-3">2024-01-08 10:15</td>
                <td class="border p-3">
                  <div class="space-x-2">
                    <button class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">
                      查看
                    </button>
                    <button class="bg-gray-500 text-white px-3 py-1 rounded text-sm hover:bg-gray-600">
                      下载
                    </button>
                  </div>
                </td>
              </tr>
              <tr>
                <td class="border p-3 font-medium">动量策略优化测试</td>
                <td class="border p-3">动量突破策略</td>
                <td class="border p-3">2023-01-01 ~ 2023-12-31</td>
                <td class="border p-3">¥2,000,000</td>
                <td class="border p-3 text-gray-400">--</td>
                <td class="border p-3 text-gray-400">--</td>
                <td class="border p-3 text-gray-400">--</td>
                <td class="border p-3">
                  <span class="px-2 py-1 rounded text-sm bg-yellow-100 text-yellow-800">运行中</span>
                </td>
                <td class="border p-3">2024-01-11 09:00</td>
                <td class="border p-3">
                  <div class="space-x-2">
                    <button class="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600">
                      停止
                    </button>
                    <button class="bg-blue-500 text-white px-3 py-1 rounded text-sm hover:bg-blue-600">
                      监控
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 分页 -->
        <div class="mt-6 flex justify-between items-center">
          <div class="text-sm text-gray-600">
            显示 1-3 条，共 3 条记录
          </div>
          <div class="flex space-x-2">
            <button class="px-3 py-1 border rounded hover:bg-gray-50" disabled>上一页</button>
            <button class="px-3 py-1 border rounded bg-blue-500 text-white">1</button>
            <button class="px-3 py-1 border rounded hover:bg-gray-50" disabled>下一页</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

onMounted(() => {
  console.log('回测历史页面加载')
})
</script>

<style scoped>
.backtest-history-page {
  min-height: calc(100vh - 64px);
  background-color: #f5f5f5;
}
</style> 