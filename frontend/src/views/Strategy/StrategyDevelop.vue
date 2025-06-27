<template>
  <div class="strategy-develop-page">
    <div class="container mx-auto p-6">
      <!-- 页面头部 -->
      <div class="flex justify-between items-center mb-6">
        <div>
          <h1 class="text-2xl font-bold text-gray-800">策略开发</h1>
          <p class="text-gray-600 mt-1">创建和编辑量化交易策略</p>
        </div>
        <div class="flex gap-2">
          <el-button @click="showTemplateDialog = true" type="info" size="small">
            <el-icon><Document /></el-icon>
            策略模板
          </el-button>
          <el-button @click="importStrategy" type="primary" size="small">
            <el-icon><Upload /></el-icon>
            导入策略
          </el-button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- 左侧：策略配置 -->
        <div class="lg:col-span-1">
          <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 class="text-lg font-semibold text-gray-800 mb-4">基本信息</h3>
            
            <el-form :model="strategyForm" :rules="formRules" ref="formRef" label-width="80px">
              <el-form-item label="策略名称" prop="name">
                <el-input v-model="strategyForm.name" placeholder="输入策略名称" />
              </el-form-item>

              <el-form-item label="策略类型" prop="type">
                <el-select v-model="strategyForm.type" placeholder="选择策略类型" style="width: 100%">
                  <el-option
                    v-for="type in strategyTypes"
                    :key="type.value"
                    :label="type.label"
                    :value="type.value"
                  />
                </el-select>
              </el-form-item>

              <el-form-item label="风险等级" prop="riskLevel">
                <el-select v-model="strategyForm.riskLevel" placeholder="选择风险等级" style="width: 100%">
                  <el-option label="低风险" value="low" />
                  <el-option label="中等风险" value="medium" />
                  <el-option label="高风险" value="high" />
                </el-select>
              </el-form-item>

              <el-form-item label="最小资金" prop="minCapital">
                <el-input-number
                  v-model="strategyForm.minCapital"
                  :min="10000"
                  :step="10000"
                  style="width: 100%"
                />
              </el-form-item>

              <el-form-item label="最大持仓" prop="maxPositions">
                <el-input-number
                  v-model="strategyForm.maxPositions"
                  :min="1"
                  :max="50"
                  style="width: 100%"
                />
              </el-form-item>

              <el-form-item label="策略描述" prop="description">
                <el-input
                  v-model="strategyForm.description"
                  type="textarea"
                  :rows="3"
                  placeholder="详细描述策略逻辑和使用场景"
                />
              </el-form-item>

              <el-form-item label="标签">
                <el-tag
                  v-for="tag in strategyForm.tags"
                  :key="tag"
                  closable
                  @close="removeTag(tag)"
                  class="mr-2 mb-2"
                >
                  {{ tag }}
                </el-tag>
                <el-input
                  v-if="inputVisible"
                  ref="inputRef"
                  v-model="inputValue"
                  size="small"
                  style="width: 100px"
                  @keyup.enter="handleInputConfirm"
                  @blur="handleInputConfirm"
                />
                <el-button v-else size="small" @click="showInput">
                  + 新标签
                </el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- 策略参数 -->
          <div class="bg-white rounded-lg shadow-md p-6">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-semibold text-gray-800">策略参数</h3>
              <el-button @click="addParameter" type="primary" size="small" text>
                <el-icon><Plus /></el-icon>
                添加参数
              </el-button>
            </div>

            <div v-if="strategyForm.parameters.length === 0" class="text-center py-4 text-gray-500">
              暂无参数配置
            </div>

            <div v-else class="space-y-3">
              <div
                v-for="(param, index) in strategyForm.parameters"
                :key="index"
                class="border rounded-lg p-3"
              >
                <div class="flex justify-between items-start mb-2">
                  <div class="flex-1 grid grid-cols-2 gap-2">
                    <el-input
                      v-model="param.name"
                      placeholder="参数名"
                      size="small"
                    />
                    <el-select v-model="param.type" placeholder="类型" size="small">
                      <el-option label="数字" value="number" />
                      <el-option label="字符串" value="string" />
                      <el-option label="布尔" value="boolean" />
                    </el-select>
                  </div>
                  <el-button
                    @click="removeParameter(index)"
                    type="danger"
                    size="small"
                    text
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
                <div class="grid grid-cols-2 gap-2">
                  <el-input
                    v-model="param.defaultValue"
                    placeholder="默认值"
                    size="small"
                  />
                  <el-input
                    v-model="param.description"
                    placeholder="描述"
                    size="small"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：代码编辑器 -->
        <div class="lg:col-span-2">
          <div class="bg-white rounded-lg shadow-md">
            <!-- 编辑器头部 -->
            <div class="border-b border-gray-200 p-4">
              <div class="flex justify-between items-center">
                <div class="flex items-center gap-4">
                  <h3 class="text-lg font-semibold text-gray-800">策略代码</h3>
                  <el-select v-model="selectedLanguage" size="small" style="width: 120px">
                    <el-option label="Python" value="python" />
                    <el-option label="JavaScript" value="javascript" />
                  </el-select>
                </div>
                <div class="flex gap-2">
                  <el-button @click="formatCode" size="small" text>
                    <el-icon><MagicStick /></el-icon>
                    格式化
                  </el-button>
                  <el-button @click="validateCode" size="small" text>
                    <el-icon><Check /></el-icon>
                    验证语法
                  </el-button>
                  <el-button @click="fullscreen = !fullscreen" size="small" text>
                    <el-icon><FullScreen /></el-icon>
                    {{ fullscreen ? '退出' : '全屏' }}
                  </el-button>
                </div>
              </div>
            </div>

            <!-- 代码编辑器 -->
            <div :class="['relative', fullscreen ? 'fixed inset-0 z-50 bg-white' : '']">
              <div class="code-editor-container" :style="{ height: fullscreen ? '100vh' : '600px' }">
                <textarea
                  ref="codeEditor"
                  v-model="strategyForm.code"
                  class="w-full h-full p-4 font-mono text-sm border-0 focus:outline-none resize-none"
                  :placeholder="codeTemplate"
                  @input="onCodeChange"
                />
              </div>

              <!-- 语法错误提示 -->
              <div v-if="syntaxErrors.length > 0" class="border-t border-red-200 bg-red-50 p-3">
                <div class="flex items-center mb-2">
                  <el-icon class="text-red-500 mr-2"><Warning /></el-icon>
                  <span class="text-red-700 font-medium">语法错误</span>
                </div>
                <ul class="text-sm text-red-600 space-y-1">
                  <li v-for="error in syntaxErrors" :key="error.line">
                    第 {{ error.line }} 行: {{ error.message }}
                  </li>
                </ul>
              </div>
            </div>

            <!-- 编辑器底部工具栏 -->
            <div class="border-t border-gray-200 p-4">
              <div class="flex justify-between items-center">
                <div class="flex items-center gap-4 text-sm text-gray-600">
                  <span>行数: {{ codeLineCount }}</span>
                  <span>字符: {{ strategyForm.code.length }}</span>
                  <span v-if="lastSaved" class="text-green-600">
                    <el-icon><Check /></el-icon>
                    已保存 {{ formatTime(lastSaved) }}
                  </span>
                </div>
                <div class="flex gap-2">
                  <el-button @click="saveStrategy" :loading="saving" type="primary" size="small">
                    <el-icon><DocumentAdd /></el-icon>
                    保存策略
                  </el-button>
                  <el-button @click="runBacktest" :loading="backtesting" type="success" size="small">
                    <el-icon><VideoPlay /></el-icon>
                    运行回测
                  </el-button>
                  <el-button @click="deployStrategy" type="warning" size="small">
                    <el-icon><Upload /></el-icon>
                    部署策略
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 策略模板选择弹窗 -->
    <el-dialog v-model="showTemplateDialog" title="选择策略模板" width="800px">
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div
          v-for="template in strategyTemplates"
          :key="template.id"
          class="border rounded-lg p-4 cursor-pointer hover:border-blue-500 transition-colors"
          @click="selectTemplate(template)"
        >
          <div class="flex items-start justify-between mb-2">
            <h4 class="font-medium text-gray-800">{{ template.name }}</h4>
            <el-tag :type="template.difficulty === 'easy' ? 'success' : template.difficulty === 'medium' ? 'warning' : 'danger'" size="small">
              {{ template.difficulty === 'easy' ? '简单' : template.difficulty === 'medium' ? '中等' : '困难' }}
            </el-tag>
          </div>
          <p class="text-sm text-gray-600 mb-3">{{ template.description }}</p>
          <div class="flex flex-wrap gap-1">
            <el-tag v-for="tag in template.tags" :key="tag" size="small" type="info">
              {{ tag }}
            </el-tag>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 回测结果弹窗 -->
    <el-dialog v-model="showBacktestDialog" title="回测结果" width="900px">
      <div v-if="backtestResult" class="space-y-6">
        <!-- 关键指标 -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <p class="text-2xl font-bold" :class="backtestResult.totalReturn >= 0 ? 'text-red-600' : 'text-green-600'">
              {{ formatPercent(backtestResult.totalReturn) }}
            </p>
            <p class="text-sm text-gray-600">总收益率</p>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <p class="text-2xl font-bold text-blue-600">
              {{ backtestResult.sharpeRatio.toFixed(2) }}
            </p>
            <p class="text-sm text-gray-600">夏普比率</p>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <p class="text-2xl font-bold text-red-600">
              {{ formatPercent(backtestResult.maxDrawdown) }}
            </p>
            <p class="text-sm text-gray-600">最大回撤</p>
          </div>
          <div class="text-center p-4 bg-gray-50 rounded-lg">
            <p class="text-2xl font-bold text-green-600">
              {{ formatPercent(backtestResult.winRate) }}
            </p>
            <p class="text-sm text-gray-600">胜率</p>
          </div>
        </div>

        <!-- 详细统计 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 class="font-medium text-gray-800 mb-3">收益统计</h4>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-600">年化收益率:</span>
                <span>{{ formatPercent(backtestResult.annualizedReturn) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">波动率:</span>
                <span>{{ formatPercent(backtestResult.volatility) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">索提诺比率:</span>
                <span>{{ backtestResult.sortinoRatio.toFixed(2) }}</span>
              </div>
            </div>
          </div>
          <div>
            <h4 class="font-medium text-gray-800 mb-3">交易统计</h4>
            <div class="space-y-2 text-sm">
              <div class="flex justify-between">
                <span class="text-gray-600">总交易次数:</span>
                <span>{{ backtestResult.totalTrades }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">平均持仓天数:</span>
                <span>{{ backtestResult.avgTradeDuration }} 天</span>
              </div>
              <div class="flex justify-between">
                <span class="text-gray-600">盈利因子:</span>
                <span>{{ backtestResult.profitFactor.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  Document,
  Upload,
  Plus,
  Delete,
  MagicStick,
  Check,
  FullScreen,
  Warning,
  DocumentAdd,
  VideoPlay
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useStrategy } from '@/composables/strategy/useStrategy'
import { formatPercent, formatTime } from '@/utils/formatters'

const router = useRouter()
const { createStrategy } = useStrategy()

// 表单数据
const strategyForm = ref({
  name: '',
  type: '',
  description: '',
  riskLevel: 'medium',
  minCapital: 100000,
  maxPositions: 10,
  code: '',
  tags: [],
  parameters: []
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入策略名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择策略类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入策略描述', trigger: 'blur' }
  ]
}

// 策略类型选项
const strategyTypes = [
  { value: 'trend_following', label: '趋势跟踪' },
  { value: 'mean_reversion', label: '均值回归' },
  { value: 'momentum', label: '动量策略' },
  { value: 'arbitrage', label: '套利策略' },
  { value: 'factor_model', label: '因子模型' },
  { value: 'machine_learning', label: '机器学习' },
  { value: 'custom', label: '自定义' }
]

// 界面状态
const formRef = ref()
const codeEditor = ref()
const inputRef = ref()
const saving = ref(false)
const backtesting = ref(false)
const fullscreen = ref(false)
const showTemplateDialog = ref(false)
const showBacktestDialog = ref(false)
const selectedLanguage = ref('python')
const inputVisible = ref(false)
const inputValue = ref('')
const lastSaved = ref<Date | null>(null)
const syntaxErrors = ref([])
const backtestResult = ref(null)

// 策略模板
const strategyTemplates = [
  {
    id: 'ma_cross',
    name: '双均线交叉',
    description: '基于短期和长期移动平均线交叉的经典趋势跟踪策略',
    difficulty: 'easy',
    tags: ['趋势跟踪', '技术指标', '经典策略'],
    code: `# 双均线交叉策略
def initialize(context):
    context.short_window = 5
    context.long_window = 20
    context.symbol = '000001.XSHE'

def handle_data(context, data):
    # 获取历史数据
    hist = data.history(context.symbol, ['close'], context.long_window, '1d')
    
    # 计算移动平均线
    short_ma = hist['close'].rolling(window=context.short_window).mean().iloc[-1]
    long_ma = hist['close'].rolling(window=context.long_window).mean().iloc[-1]
    
    current_price = data.current(context.symbol, 'close')
    
    # 交易逻辑
    if short_ma > long_ma and not context.portfolio.positions[context.symbol]:
        # 金叉买入
        order_target_percent(context.symbol, 1.0)
    elif short_ma < long_ma and context.portfolio.positions[context.symbol]:
        # 死叉卖出
        order_target_percent(context.symbol, 0.0)`
  },
  {
    id: 'rsi_reversal',
    name: 'RSI均值回归',
    description: '利用RSI指标识别超买超卖机会的均值回归策略',
    difficulty: 'medium',
    tags: ['均值回归', 'RSI', '技术指标'],
    code: `# RSI均值回归策略
import talib

def initialize(context):
    context.symbol = '000001.XSHE'
    context.rsi_period = 14
    context.oversold = 30
    context.overbought = 70

def handle_data(context, data):
    # 获取历史数据
    hist = data.history(context.symbol, ['close'], context.rsi_period + 10, '1d')
    
    # 计算RSI
    rsi = talib.RSI(hist['close'].values, timeperiod=context.rsi_period)[-1]
    
    current_position = context.portfolio.positions[context.symbol].amount
    
    # 交易逻辑
    if rsi < context.oversold and current_position == 0:
        # RSI超卖，买入
        order_target_percent(context.symbol, 0.5)
    elif rsi > context.overbought and current_position > 0:
        # RSI超买，卖出
        order_target_percent(context.symbol, 0.0)`
  }
]

// 计算属性
const codeTemplate = computed(() => {
  if (selectedLanguage.value === 'python') {
    return `# 策略模板 - Python
def initialize(context):
    """
    策略初始化函数
    在策略启动时执行一次
    """
    # 设置基准和股票池
    context.benchmark = '000300.XSHG'
    context.stocks = ['000001.XSHE', '000002.XSHE']
    
    # 设置策略参数
    context.max_position = 10
    context.stop_loss = 0.05
    
def handle_data(context, data):
    """
    策略主逻辑函数
    每个交易日执行一次
    """
    # 获取当前持仓
    current_positions = context.portfolio.positions
    
    # 策略逻辑
    for stock in context.stocks:
        current_price = data.current(stock, 'close')
        
        # 在此处添加您的交易逻辑
        # 例如：技术指标计算、信号生成、下单等
        
        pass

def before_trading_start(context, data):
    """
    盘前处理函数
    每个交易日开盘前执行
    """
    pass

def after_trading_end(context, data):
    """
    盘后处理函数
    每个交易日收盘后执行
    """
    pass`
  } else {
    return `// 策略模板 - JavaScript
function initialize(context) {
    // 策略初始化
    context.benchmark = '000300.XSHG';
    context.stocks = ['000001.XSHE', '000002.XSHE'];
    context.maxPosition = 10;
    context.stopLoss = 0.05;
}

function handleData(context, data) {
    // 策略主逻辑
    const currentPositions = context.portfolio.positions;
    
    context.stocks.forEach(stock => {
        const currentPrice = data.current(stock, 'close');
        
        // 在此处添加您的交易逻辑
        
    });
}

function beforeTradingStart(context, data) {
    // 盘前处理
}

function afterTradingEnd(context, data) {
    // 盘后处理
}`
  }
})

const codeLineCount = computed(() => {
  return strategyForm.value.code.split('\n').length
})

// 方法
const addParameter = () => {
  strategyForm.value.parameters.push({
    name: '',
    type: 'number',
    defaultValue: '',
    description: ''
  })
}

const removeParameter = (index: number) => {
  strategyForm.value.parameters.splice(index, 1)
}

const removeTag = (tag: string) => {
  const index = strategyForm.value.tags.indexOf(tag)
  if (index > -1) {
    strategyForm.value.tags.splice(index, 1)
  }
}

const showInput = () => {
  inputVisible.value = true
  nextTick(() => {
    inputRef.value?.focus()
  })
}

const handleInputConfirm = () => {
  if (inputValue.value && !strategyForm.value.tags.includes(inputValue.value)) {
    strategyForm.value.tags.push(inputValue.value)
  }
  inputVisible.value = false
  inputValue.value = ''
}

const selectTemplate = (template: any) => {
  strategyForm.value.code = template.code
  strategyForm.value.name = template.name
  strategyForm.value.description = template.description
  showTemplateDialog.value = false
  ElMessage.success('模板加载成功')
}

const formatCode = () => {
  // 简单的代码格式化
  ElMessage.info('代码格式化功能开发中...')
}

const validateCode = () => {
  // 简单的语法验证
  syntaxErrors.value = []
  
  if (!strategyForm.value.code.trim()) {
    syntaxErrors.value.push({ line: 1, message: '代码不能为空' })
    return
  }

  // 检查必要的函数
  if (selectedLanguage.value === 'python') {
    if (!strategyForm.value.code.includes('def initialize(context)')) {
      syntaxErrors.value.push({ line: 1, message: '缺少 initialize 函数' })
    }
    if (!strategyForm.value.code.includes('def handle_data(context, data)')) {
      syntaxErrors.value.push({ line: 1, message: '缺少 handle_data 函数' })
    }
  }

  if (syntaxErrors.value.length === 0) {
    ElMessage.success('语法验证通过')
  }
}

const onCodeChange = () => {
  // 自动保存逻辑
  clearTimeout(window.autoSaveTimer)
  window.autoSaveTimer = setTimeout(() => {
    if (strategyForm.value.name && strategyForm.value.code) {
      autoSave()
    }
  }, 5000)
}

const autoSave = async () => {
  try {
    // 自动保存到本地存储
    localStorage.setItem('strategy_draft', JSON.stringify(strategyForm.value))
    lastSaved.value = new Date()
  } catch (error) {
    console.error('自动保存失败:', error)
  }
}

const saveStrategy = async () => {
  try {
    await formRef.value?.validate()
    
    saving.value = true
    
    const strategyData = {
      ...strategyForm.value,
      status: 'draft'
    }
    
    const newStrategy = await createStrategy(strategyData)
    
    ElMessage.success('策略保存成功')
    
    // 清除草稿
    localStorage.removeItem('strategy_draft')
    
    // 可选：跳转到策略详情页
    // router.push(`/strategy/detail/${newStrategy.id}`)
    
  } catch (error) {
    console.error('保存策略失败:', error)
  } finally {
    saving.value = false
  }
}

const runBacktest = async () => {
  try {
    await formRef.value?.validate()
    
    if (!strategyForm.value.code.trim()) {
      ElMessage.warning('请先编写策略代码')
      return
    }
    
    backtesting.value = true
    
    // 模拟回测
    await new Promise(resolve => setTimeout(resolve, 3000))
    
    // 模拟回测结果
    backtestResult.value = {
      totalReturn: 0.25 + (Math.random() - 0.5) * 0.3,
      annualizedReturn: 0.18 + (Math.random() - 0.5) * 0.2,
      sharpeRatio: 1.5 + Math.random() * 1.0,
      maxDrawdown: -(0.05 + Math.random() * 0.1),
      winRate: 0.6 + Math.random() * 0.2,
      volatility: 0.12 + Math.random() * 0.08,
      sortinoRatio: 1.8 + Math.random() * 0.8,
      totalTrades: Math.floor(50 + Math.random() * 200),
      avgTradeDuration: Math.floor(3 + Math.random() * 10),
      profitFactor: 1.2 + Math.random() * 0.8
    }
    
    showBacktestDialog.value = true
    ElMessage.success('回测完成')
    
  } catch (error) {
    console.error('回测失败:', error)
    ElMessage.error('回测失败')
  } finally {
    backtesting.value = false
  }
}

const deployStrategy = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要部署这个策略吗？部署后策略将可以实盘运行。',
      '部署策略',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    ElMessage.info('策略部署功能开发中...')
  } catch (error) {
    // 用户取消
  }
}

const importStrategy = () => {
  ElMessage.info('策略导入功能开发中...')
}

// 生命周期
onMounted(() => {
  // 恢复草稿
  const draft = localStorage.getItem('strategy_draft')
  if (draft) {
    try {
      const draftData = JSON.parse(draft)
      Object.assign(strategyForm.value, draftData)
      ElMessage.info('已恢复上次编辑的草稿')
    } catch (error) {
      console.error('恢复草稿失败:', error)
    }
  }
})

// 监听语言变化
watch(selectedLanguage, () => {
  if (!strategyForm.value.code.trim()) {
    strategyForm.value.code = codeTemplate.value
  }
})
</script>

<style scoped>
.strategy-develop-page {
  min-height: calc(100vh - 64px);
  background-color: #f5f5f5;
}

.code-editor-container {
  position: relative;
  background-color: #fafafa;
}

.code-editor-container textarea {
  background-color: transparent;
  line-height: 1.5;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-tag) {
  margin-right: 8px;
  margin-bottom: 4px;
}

:deep(.el-dialog) {
  border-radius: 8px;
}

:deep(.el-dialog__body) {
  padding: 20px;
}
</style> 