<template>
  <div class="backtest-form">
    <div class="form-header">
      <h3>创建回测</h3>
      <p class="form-description">配置回测参数，分析策略历史表现</p>
    </div>
    
    <!-- @ts-ignore -->
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
      class="form-content"
    >
      <!-- 基本信息 -->
      <el-card class="form-section" shadow="never">
        <template #header>
          <div class="section-header">
            <el-icon><Setting /></el-icon>
            <span>基本配置</span>
          </div>
        </template>
        
        <!-- @ts-ignore -->
        <el-form-item label="回测名称" prop="name">
          <!-- @ts-ignore -->
          <el-input
            v-model="form.name"
            placeholder="请输入回测名称"
            clearable
          />
        </el-form-item>
        
        <!-- @ts-ignore -->
        <el-form-item label="策略选择" prop="strategyId">
          <!-- @ts-ignore -->
          <el-select
            v-model="form.strategyId"
            placeholder="请选择策略"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="strategy in strategies"
              :key="strategy.id"
              :label="strategy.name"
              :value="strategy.id"
            />
          </el-select>
        </el-form-item>
        
        <!-- @ts-ignore -->
        <el-form-item label="股票池" prop="stockPool">
          <!-- @ts-ignore -->
          <el-select
            v-model="form.stockPool"
            placeholder="请选择股票"
            multiple
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="stock in stocks"
              :key="stock.code"
              :label="`${stock.name}(${stock.code})`"
              :value="stock.code"
            />
          </el-select>
        </el-form-item>
      </el-card>
      
      <!-- 时间设置 -->
      <el-card class="form-section" shadow="never">
        <template #header>
          <div class="section-header">
            <el-icon><Calendar /></el-icon>
            <span>时间设置</span>
          </div>
        </template>
        
        <!-- @ts-ignore -->
        <el-form-item label="回测区间" prop="dateRange">
          <!-- @ts-ignore -->
          <el-date-picker
            v-model="form.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 100%"
          />
        </el-form-item>
        
        <el-form-item label="交易频率" prop="frequency">
          <el-radio-group v-model="form.frequency">
            <el-radio value="daily">日频</el-radio>
            <el-radio value="weekly">周频</el-radio>
            <el-radio value="monthly">月频</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-card>
      
      <!-- 资金设置 -->
      <el-card class="form-section" shadow="never">
        <template #header>
          <div class="section-header">
            <el-icon><Money /></el-icon>
            <span>资金设置</span>
          </div>
        </template>
        
        <!-- @ts-ignore -->
        <el-form-item label="初始资金" prop="initialCapital">
          <!-- @ts-ignore -->
          <el-input-number
            v-model="form.initialCapital"
            :min="10000"
            :max="10000000"
            :step="10000"
            style="width: 100%"
          />
          <span class="input-suffix">元</span>
        </el-form-item>
        
        <!-- @ts-ignore -->
        <el-form-item label="手续费率" prop="commissionRate">
          <!-- @ts-ignore -->
          <el-input-number
            v-model="form.commissionRate"
            :min="0"
            :max="0.01"
            :step="0.0001"
            :precision="4"
            style="width: 100%"
          />
          <span class="input-suffix">%</span>
        </el-form-item>
        
        <!-- @ts-ignore -->
        <el-form-item label="印花税率" prop="stampTaxRate">
          <!-- @ts-ignore -->
          <el-input-number
            v-model="form.stampTaxRate"
            :min="0"
            :max="0.01"
            :step="0.0001"
            :precision="4"
            style="width: 100%"
          />
          <span class="input-suffix">%</span>
        </el-form-item>
      </el-card>
      
      <!-- 风险控制 -->
      <el-card class="form-section" shadow="never">
        <template #header>
          <div class="section-header">
            <el-icon><Warning /></el-icon>
            <span>风险控制</span>
          </div>
        </template>
        
        <!-- @ts-ignore -->
        <el-form-item label="最大回撤" prop="maxDrawdown">
          <!-- @ts-ignore -->
          <el-input-number
            v-model="form.maxDrawdown"
            :min="0"
            :max="1"
            :step="0.01"
            :precision="2"
            style="width: 100%"
          />
          <span class="input-suffix">%</span>
        </el-form-item>
        
        <el-form-item label="单股持仓上限" prop="maxPositionRatio">
          <el-input-number
            v-model="form.maxPositionRatio"
            :min="0.01"
            :max="1"
            :step="0.01"
            :precision="2"
            style="width: 100%"
            controls-position="right"
          />
          <span class="input-suffix">%</span>
        </el-form-item>
      </el-card>
      
      <!-- 提交按钮 -->
      <div class="form-actions">
        <el-button @click="resetForm">重置</el-button>
        <el-button
          type="primary"
          :loading="submitting"
          @click="handleSubmit"
        >
          开始回测
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Setting, Calendar, Money, Warning } from '@element-plus/icons-vue'
import type { BacktestFormData } from '@/types/backtest'
import type { FormRules } from '@/types/element-plus'

interface Emits {
  (e: 'submit', data: BacktestFormData): void
}

const emit = defineEmits<Emits>()

// 表单引用
const formRef = ref()

// 状态
const loading = ref(false)

// 表单数据
const form = reactive<BacktestFormData>({
  name: '',
  strategyId: '',
  stockPool: [],
  dateRange: [] as any,
  frequency: 'daily',
  initialCapital: 1000000,
  commissionRate: 0.0003,
  stampTaxRate: 0.001,
  maxDrawdown: 0.2,
  maxPositionRatio: 0.1
})

// 验证规则
const rules: FormRules = {
  name: [
    { required: true, message: '请输入回测名称', trigger: 'blur' }
  ],
  strategyId: [
    { required: true, message: '请选择策略', trigger: 'change' }
  ],
  stockPool: [
    { required: true, message: '请选择至少一只股票', trigger: 'change' }
  ],
  dateRange: [
    { required: true, message: '请选择回测时间区间', trigger: 'change' }
  ]
}

// 模拟数据
const strategies = ref([
  { id: '1', name: '双均线策略', type: 'trend_following' },
  { id: '2', name: 'RSI反转策略', type: 'mean_reversion' },
  { id: '3', name: 'MACD策略', type: 'trend_following' }
])

const stocks = ref([
  { code: '000001', name: '平安银行' },
  { code: '000002', name: '万科A' },
  { code: '000858', name: '五粮液' },
  { code: '600036', name: '招商银行' },
  { code: '600519', name: '贵州茅台' }
])

// 日期快捷选项
const dateShortcuts = [
  {
    text: '最近一年',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setFullYear(start.getFullYear() - 1)
      return [start, end]
    }
  },
  {
    text: '最近两年',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setFullYear(start.getFullYear() - 2)
      return [start, end]
    }
  },
  {
    text: '最近三年',
    value: () => {
      const end = new Date()
      const start = new Date()
      start.setFullYear(start.getFullYear() - 3)
      return [start, end]
    }
  }
]

// 方法
const submitForm = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    // 提交表单数据
    emit('submit', form)
    
    ;(ElMessage as any).success('回测创建成功')
  } catch (error) {
    ;(ElMessage as any).error('请检查表单填写是否正确')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  if (!formRef.value) return
  formRef.value.resetFields()
}

const loadStockOptions = async () => {
  try {
    // 这里可以调用API获取股票列表
    // const stockList = await stockApi.getStockList()
    // stocks.value = stockList
  } catch (error) {
    ;(ElMessage as any).error('加载股票列表失败')
  }
}

onMounted(() => {
  loadStockOptions()
})
</script>

<style scoped>
.backtest-form {
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-header {
  padding: 24px 24px 0;
  border-bottom: 1px solid #e8e8e8;
  margin-bottom: 24px;
}

.form-header h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.form-description {
  margin: 0 0 24px 0;
  color: #666;
  font-size: 14px;
}

.form-content {
  padding: 0 24px 24px;
}

.form-section {
  margin-bottom: 24px;
}

.form-section:last-of-type {
  margin-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
}

.strategy-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.strategy-type {
  font-size: 12px;
  color: #999;
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
}

.input-suffix {
  margin-left: 8px;
  color: #666;
  font-size: 14px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e8e8e8;
}

:deep(.el-card__header) {
  padding: 16px 20px;
  background: #fafafa;
}

:deep(.el-card__body) {
  padding: 20px;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-form-item__label) {
  color: #333;
  font-weight: 500;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__inner) {
  text-align: left;
}
</style>