<!--
  风险预警系统组件
  提供实时风险监控、预警规则配置、风险报告生成等功能
-->
<template>
  <div class="risk-alert-system">
    <!-- 系统头部 -->
    <div class="system-header">
      <div class="header-info">
        <h2 class="system-title">
          <el-icon><Warning /></el-icon>
          风险预警系统
        </h2>
        <p class="system-description">实时监控投资组合风险，及时发现并预警潜在风险</p>
      </div>
      
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="showCreateRuleDialog = true">
          添加预警规则
        </el-button>
        <el-button :icon="Setting" @click="showSettingsDialog = true">
          系统设置
        </el-button>
        <el-button 
          :type="systemEnabled ? 'danger' : 'success'" 
          @click="toggleSystem"
        >
          {{ systemEnabled ? '停用系统' : '启用系统' }}
        </el-button>
      </div>
    </div>

    <!-- 风险概览 -->
    <div class="risk-overview">
      <div class="overview-cards">
        <div class="risk-card critical">
          <div class="card-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">{{ criticalAlerts.length }}</div>
            <div class="card-label">严重预警</div>
          </div>
        </div>
        
        <div class="risk-card warning">
          <div class="card-icon">
            <el-icon><InfoFilled /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">{{ warningAlerts.length }}</div>
            <div class="card-label">一般预警</div>
          </div>
        </div>
        
        <div class="risk-card info">
          <div class="card-icon">
            <el-icon><Bell /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">{{ infoAlerts.length }}</div>
            <div class="card-label">提示信息</div>
          </div>
        </div>
        
        <div class="risk-card success">
          <div class="card-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="card-content">
            <div class="card-value">{{ activeRules.length }}</div>
            <div class="card-label">活跃规则</div>
          </div>
        </div>
      </div>
      
      <!-- 风险状态指示器 -->
      <div class="risk-indicator">
        <div class="indicator-title">系统风险等级</div>
        <div class="indicator-gauge">
          <el-progress
            type="dashboard"
            :percentage="riskLevel"
            :color="getRiskLevelColor(riskLevel)"
            :width="120"
          >
            <template #default="{ percentage }">
              <span class="risk-level-text">
                {{ getRiskLevelText(percentage) }}
              </span>
            </template>
          </el-progress>
        </div>
      </div>
    </div>

    <!-- 实时预警列表 -->
    <div class="alerts-section">
      <div class="section-header">
        <h3 class="section-title">实时预警</h3>
        <div class="section-actions">
          <el-button size="small" @click="clearAllAlerts">
            清除所有
          </el-button>
          <el-button size="small" @click="refreshAlerts">
            刷新
          </el-button>
        </div>
      </div>
      
      <div class="alerts-list">
        <div
          v-for="alert in sortedAlerts"
          :key="alert.id"
          class="alert-item"
          :class="alert.level"
        >
          <div class="alert-icon">
            <el-icon v-if="alert.level === 'critical'"><Warning /></el-icon>
            <el-icon v-else-if="alert.level === 'warning'"><InfoFilled /></el-icon>
            <el-icon v-else><Bell /></el-icon>
          </div>
          
          <div class="alert-content">
            <div class="alert-title">{{ alert.title }}</div>
            <div class="alert-message">{{ alert.message }}</div>
            <div class="alert-meta">
              <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
              <span class="alert-source">{{ alert.source }}</span>
            </div>
          </div>
          
          <div class="alert-actions">
            <el-button size="small" text @click="viewAlertDetail(alert)">
              详情
            </el-button>
            <el-button size="small" text @click="dismissAlert(alert.id)">
              忽略
            </el-button>
          </div>
        </div>
        
        <div v-if="sortedAlerts.length === 0" class="no-alerts">
          <el-icon><CircleCheck /></el-icon>
          <p>暂无风险预警</p>
        </div>
      </div>
    </div>

    <!-- 预警规则管理 -->
    <div class="rules-section">
      <div class="section-header">
        <h3 class="section-title">预警规则</h3>
        <div class="section-actions">
          <el-button size="small" type="primary" @click="showCreateRuleDialog = true">
            添加规则
          </el-button>
        </div>
      </div>
      
      <el-table :data="riskRules" style="width: 100%">
        <el-table-column prop="name" label="规则名称" />
        <el-table-column prop="type" label="规则类型">
          <template #default="{ row }">
            <el-tag :type="getRuleTypeTagType(row.type)">
              {{ getRuleTypeLabel(row.type) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="threshold" label="阈值" />
        <el-table-column prop="enabled" label="状态">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              @change="toggleRule(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="lastTriggered" label="最后触发">
          <template #default="{ row }">
            {{ row.lastTriggered ? formatTime(row.lastTriggered) : '从未触发' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" text @click="editRule(row)">
              编辑
            </el-button>
            <el-button size="small" text type="danger" @click="deleteRule(row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 创建/编辑规则对话框 -->
    <el-dialog
      v-model="showCreateRuleDialog"
      :title="editingRule ? '编辑预警规则' : '创建预警规则'"
      width="600px"
    >
      <el-form
        ref="ruleFormRef"
        :model="ruleForm"
        :rules="ruleFormRules"
        label-width="120px"
      >
        <el-form-item label="规则名称" prop="name">
          <el-input v-model="ruleForm.name" placeholder="请输入规则名称" />
        </el-form-item>
        
        <el-form-item label="规则类型" prop="type">
          <el-select v-model="ruleForm.type" style="width: 100%" @change="handleRuleTypeChange">
            <el-option label="持仓集中度" value="concentration" />
            <el-option label="单日亏损" value="daily_loss" />
            <el-option label="最大回撤" value="max_drawdown" />
            <el-option label="杠杆比例" value="leverage" />
            <el-option label="波动率" value="volatility" />
            <el-option label="Beta值" value="beta" />
            <el-option label="VaR风险" value="var" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="预警级别" prop="level">
          <el-select v-model="ruleForm.level" style="width: 100%">
            <el-option label="提示" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="阈值设置" prop="threshold">
          <div class="threshold-setting">
            <el-input-number
              v-model="ruleForm.threshold"
              :precision="ruleForm.type === 'concentration' ? 0 : 2"
              :step="ruleForm.type === 'concentration' ? 1 : 0.01"
              :min="0"
              :max="ruleForm.type === 'concentration' ? 100 : 1"
            />
            <span class="threshold-unit">{{ getThresholdUnit(ruleForm.type) }}</span>
          </div>
        </el-form-item>
        
        <el-form-item label="检查频率" prop="frequency">
          <el-select v-model="ruleForm.frequency" style="width: 100%">
            <el-option label="实时" value="realtime" />
            <el-option label="每分钟" value="1min" />
            <el-option label="每5分钟" value="5min" />
            <el-option label="每小时" value="1hour" />
            <el-option label="每日" value="daily" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="通知方式" prop="notificationMethods">
          <el-checkbox-group v-model="ruleForm.notificationMethods">
            <el-checkbox value="popup">弹窗提醒</el-checkbox>
            <el-checkbox value="email">邮件通知</el-checkbox>
            <el-checkbox value="sms">短信通知</el-checkbox>
            <el-checkbox value="webhook">Webhook</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item label="规则描述" prop="description">
          <el-input
            v-model="ruleForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入规则描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateRuleDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRule">
          {{ editingRule ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 系统设置对话框 -->
    <el-dialog v-model="showSettingsDialog" title="系统设置" width="500px">
      <el-form label-width="120px">
        <el-form-item label="全局启用">
          <el-switch v-model="systemSettings.enabled" />
        </el-form-item>
        
        <el-form-item label="检查间隔">
          <el-select v-model="systemSettings.checkInterval" style="width: 100%">
            <el-option label="1秒" value="1s" />
            <el-option label="5秒" value="5s" />
            <el-option label="10秒" value="10s" />
            <el-option label="30秒" value="30s" />
            <el-option label="1分钟" value="1min" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="历史保留">
          <el-input-number
            v-model="systemSettings.historyRetentionDays"
            :min="1"
            :max="365"
          />
          <span style="margin-left: 8px;">天</span>
        </el-form-item>
        
        <el-form-item label="最大预警数">
          <el-input-number
            v-model="systemSettings.maxAlerts"
            :min="10"
            :max="1000"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showSettingsDialog = false">取消</el-button>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { 
  Warning, 
  InfoFilled, 
  Bell, 
  CircleCheck, 
  Plus, 
  Setting 
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRiskManagement } from '@/composables/risk/useRiskManagement'
import { formatTime } from '@/utils/format/date'
import type { RiskAlert, RiskRule } from '@/types/risk'

// 组合函数
const {
  alerts,
  riskRules,
  systemEnabled,
  systemSettings,
  createRule,
  updateRule,
  deleteRule: deleteRiskRule,
  toggleRule,
  clearAlert,
  clearAllAlerts: clearAllRiskAlerts,
  calculateRiskLevel,
  startMonitoring,
  stopMonitoring
} = useRiskManagement()

// 响应式数据
const showCreateRuleDialog = ref(false)
const showSettingsDialog = ref(false)
const editingRule = ref<RiskRule | null>(null)

// 表单相关
const ruleFormRef = ref()
const ruleForm = ref({
  name: '',
  type: 'concentration',
  level: 'warning',
  threshold: 0,
  frequency: 'realtime',
  notificationMethods: ['popup'],
  description: '',
  enabled: true
})

const ruleFormRules = {
  name: [
    { required: true, message: '请输入规则名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择规则类型', trigger: 'change' }
  ],
  level: [
    { required: true, message: '请选择预警级别', trigger: 'change' }
  ],
  threshold: [
    { required: true, message: '请设置阈值', trigger: 'blur' }
  ]
}

// 计算属性
const criticalAlerts = computed(() => 
  alerts.value.filter(alert => alert.level === 'critical')
)

const warningAlerts = computed(() => 
  alerts.value.filter(alert => alert.level === 'warning')
)

const infoAlerts = computed(() => 
  alerts.value.filter(alert => alert.level === 'info')
)

const activeRules = computed(() => 
  riskRules.value.filter(rule => rule.enabled)
)

const sortedAlerts = computed(() => {
  return [...alerts.value].sort((a, b) => {
    const levelOrder = { critical: 3, warning: 2, info: 1 }
    if (levelOrder[a.level] !== levelOrder[b.level]) {
      return levelOrder[b.level] - levelOrder[a.level]
    }
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  })
})

const riskLevel = computed(() => calculateRiskLevel())

// 方法
const toggleSystem = async () => {
  try {
    if (systemEnabled.value) {
      stopMonitoring()
      ElMessage.success('风险预警系统已停用')
    } else {
      startMonitoring()
      ElMessage.success('风险预警系统已启用')
    }
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const refreshAlerts = () => {
  // 刷新预警数据
  ElMessage.success('预警数据已刷新')
}

const dismissAlert = (alertId: string) => {
  clearAlert(alertId)
  ElMessage.success('预警已忽略')
}

const viewAlertDetail = (alert: RiskAlert) => {
  ElMessageBox.alert(
    `<div>
      <p><strong>预警详情：</strong></p>
      <p><strong>标题：</strong>${alert.title}</p>
      <p><strong>消息：</strong>${alert.message}</p>
      <p><strong>级别：</strong>${alert.level}</p>
      <p><strong>来源：</strong>${alert.source}</p>
      <p><strong>时间：</strong>${formatTime(alert.timestamp)}</p>
      ${alert.data ? `<p><strong>数据：</strong>${JSON.stringify(alert.data, null, 2)}</p>` : ''}
    </div>`,
    '预警详情',
    {
      dangerouslyUseHTMLString: true,
      confirmButtonText: '确定'
    }
  )
}

const editRule = (rule: RiskRule) => {
  editingRule.value = rule
  ruleForm.value = {
    name: rule.name,
    type: rule.type,
    level: rule.level,
    threshold: rule.threshold,
    frequency: rule.frequency,
    notificationMethods: rule.notificationMethods,
    description: rule.description || '',
    enabled: rule.enabled
  }
  showCreateRuleDialog.value = true
}

const handleRuleTypeChange = () => {
  // 根据规则类型设置默认阈值
  const defaultThresholds = {
    concentration: 30,
    daily_loss: 0.05,
    max_drawdown: 0.1,
    leverage: 2,
    volatility: 0.3,
    beta: 1.5,
    var: 0.05
  }
  
  ruleForm.value.threshold = defaultThresholds[ruleForm.value.type] || 0
}

const saveRule = async () => {
  try {
    await ruleFormRef.value.validate()
    
    const ruleData = {
      ...ruleForm.value,
      id: editingRule.value?.id,
      createdAt: editingRule.value?.createdAt || new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      lastTriggered: editingRule.value?.lastTriggered || null,
      triggerCount: editingRule.value?.triggerCount || 0
    }
    
    if (editingRule.value) {
      await updateRule(editingRule.value.id, ruleData)
      ElMessage.success('规则更新成功')
    } else {
      await createRule(ruleData)
      ElMessage.success('规则创建成功')
    }
    
    showCreateRuleDialog.value = false
    editingRule.value = null
    resetRuleForm()
    
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const deleteRule = async (ruleId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个预警规则吗？', '确认删除', {
      type: 'warning'
    })
    
    await deleteRiskRule(ruleId)
    ElMessage.success('规则删除成功')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const saveSettings = () => {
  // 保存系统设置
  ElMessage.success('设置保存成功')
  showSettingsDialog.value = false
}

const resetRuleForm = () => {
  ruleForm.value = {
    name: '',
    type: 'concentration',
    level: 'warning',
    threshold: 0,
    frequency: 'realtime',
    notificationMethods: ['popup'],
    description: '',
    enabled: true
  }
}

// 辅助方法
const getRiskLevelColor = (level: number) => {
  if (level >= 80) return '#f56c6c'
  if (level >= 60) return '#e6a23c'
  if (level >= 40) return '#409eff'
  return '#67c23a'
}

const getRiskLevelText = (level: number) => {
  if (level >= 80) return '高风险'
  if (level >= 60) return '中高风险'
  if (level >= 40) return '中等风险'
  if (level >= 20) return '低风险'
  return '安全'
}

const getRuleTypeTagType = (type: string) => {
  const typeMap = {
    concentration: 'warning',
    daily_loss: 'danger',
    max_drawdown: 'danger',
    leverage: 'warning',
    volatility: 'info',
    beta: 'info',
    var: 'danger'
  }
  return typeMap[type] || 'info'
}

const getRuleTypeLabel = (type: string) => {
  const labelMap = {
    concentration: '持仓集中度',
    daily_loss: '单日亏损',
    max_drawdown: '最大回撤',
    leverage: '杠杆比例',
    volatility: '波动率',
    beta: 'Beta值',
    var: 'VaR风险'
  }
  return labelMap[type] || type
}

const getThresholdUnit = (type: string) => {
  const unitMap = {
    concentration: '%',
    daily_loss: '%',
    max_drawdown: '%',
    leverage: '倍',
    volatility: '%',
    beta: '',
    var: '%'
  }
  return unitMap[type] || ''
}

// 生命周期
onMounted(() => {
  if (systemEnabled.value) {
    startMonitoring()
  }
})

onUnmounted(() => {
  stopMonitoring()
})
</script>

<style scoped>
.risk-alert-system {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.system-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header-info h2 {
  margin: 0 0 8px 0;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-info p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.risk-overview {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
}

.overview-cards {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.risk-card {
  display: flex;
  align-items: center;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-left: 4px solid;
}

.risk-card.critical {
  border-left-color: #f56c6c;
}

.risk-card.warning {
  border-left-color: #e6a23c;
}

.risk-card.info {
  border-left-color: #409eff;
}

.risk-card.success {
  border-left-color: #67c23a;
}

.card-icon {
  font-size: 24px;
  margin-right: 16px;
}

.risk-card.critical .card-icon {
  color: #f56c6c;
}

.risk-card.warning .card-icon {
  color: #e6a23c;
}

.risk-card.info .card-icon {
  color: #409eff;
}

.risk-card.success .card-icon {
  color: #67c23a;
}

.card-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  line-height: 1;
}

.card-label {
  font-size: 14px;
  color: #606266;
  margin-top: 4px;
}

.risk-indicator {
  width: 200px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.indicator-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.risk-level-text {
  font-size: 14px;
  font-weight: 600;
}

.alerts-section,
.rules-section {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 20px 0 20px;
}

.section-title {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.alerts-list {
  padding: 20px;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  margin-bottom: 12px;
  transition: all 0.3s;
}

.alert-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.alert-item.critical {
  border-left: 4px solid #f56c6c;
  background: #fef0f0;
}

.alert-item.warning {
  border-left: 4px solid #e6a23c;
  background: #fdf6ec;
}

.alert-item.info {
  border-left: 4px solid #409eff;
  background: #ecf5ff;
}

.alert-icon {
  font-size: 20px;
  margin-right: 12px;
  margin-top: 2px;
}

.alert-item.critical .alert-icon {
  color: #f56c6c;
}

.alert-item.warning .alert-icon {
  color: #e6a23c;
}

.alert-item.info .alert-icon {
  color: #409eff;
}

.alert-content {
  flex: 1;
}

.alert-title {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.alert-message {
  color: #606266;
  font-size: 14px;
  margin-bottom: 8px;
}

.alert-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #909399;
}

.alert-actions {
  display: flex;
  gap: 8px;
}

.no-alerts {
  text-align: center;
  padding: 40px;
  color: #909399;
}

.no-alerts .el-icon {
  font-size: 48px;
  color: #67c23a;
  margin-bottom: 16px;
}

.threshold-setting {
  display: flex;
  align-items: center;
  gap: 8px;
}

.threshold-unit {
  color: #606266;
  font-size: 14px;
}

@media (max-width: 1200px) {
  .overview-cards {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .risk-overview {
    flex-direction: column;
  }
  
  .risk-indicator {
    width: 100%;
  }
}

@media (max-width: 768px) {
  .system-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: space-between;
  }
  
  .overview-cards {
    grid-template-columns: 1fr;
  }
  
  .alert-item {
    flex-direction: column;
    gap: 12px;
  }
  
  .alert-actions {
    justify-content: flex-end;
  }
}
</style>