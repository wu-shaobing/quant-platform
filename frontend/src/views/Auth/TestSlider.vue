<template>
  <div class="test-slider-page">
    <div class="container">
      <el-card class="test-card">
        <template #header>
          <div class="card-header">
            <h2>滑轨验证测试页面</h2>
            <p>测试滑轨验证功能的集成效果</p>
          </div>
        </template>
        
        <div class="slider-test-section">
          <SliderCaptcha
            @success="onVerificationSuccess"
            @error="onVerificationError"
            @refresh="onVerificationRefresh"
          />
        </div>
        
        <div class="result-section" v-if="verificationResult">
          <el-alert
            :title="verificationResult.title"
            :type="verificationResult.type"
            :description="verificationResult.description"
            show-icon
            :closable="false"
          />
        </div>
        
        <div class="token-section" v-if="verificationToken">
          <el-divider content-position="left">验证令牌</el-divider>
          <el-input
            v-model="verificationToken"
            type="textarea"
            :rows="3"
            readonly
            placeholder="验证令牌将在这里显示"
          />
          <div class="token-actions">
            <el-button @click="copyToken" :icon="CopyDocument" size="small">
              复制令牌
            </el-button>
            <el-button @click="validateToken" :icon="Check" size="small" type="primary">
              验证令牌
            </el-button>
          </div>
        </div>
        
        <div class="actions-section">
          <el-button @click="resetTest" :icon="Refresh" size="large">
            重置测试
          </el-button>
          <el-button @click="goToLogin" type="primary" size="large">
            前往登录页面
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { CopyDocument, Check, Refresh } from '@element-plus/icons-vue'
import SliderCaptcha from '@/components/common/SliderCaptcha/index.vue'
import { userApi } from '@/api'

const router = useRouter()

// 状态管理
const verificationToken = ref('')
const verificationResult = ref<{
  title: string
  type: 'success' | 'error' | 'warning' | 'info'
  description: string
} | null>(null)

// 验证成功回调
const onVerificationSuccess = (token: string) => {
  verificationToken.value = token
  verificationResult.value = {
    title: '验证成功！',
    type: 'success',
    description: `滑轨验证通过，获得验证令牌。令牌长度: ${token.length} 字符`
  }
  ElMessage.success('滑轨验证成功！')
}

// 验证错误回调
const onVerificationError = (message: string) => {
  verificationResult.value = {
    title: '验证失败',
    type: 'error',
    description: `验证过程中出现错误: ${message}`
  }
  ElMessage.error(`验证失败: ${message}`)
}

// 刷新验证码回调
const onVerificationRefresh = () => {
  verificationToken.value = ''
  verificationResult.value = null
  ElMessage.info('验证码已刷新')
}

// 复制令牌
const copyToken = async () => {
  try {
    await navigator.clipboard.writeText(verificationToken.value)
    ElMessage.success('令牌已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

// 验证令牌有效性
const validateToken = async () => {
  if (!verificationToken.value) {
    ElMessage.warning('请先完成滑轨验证获取令牌')
    return
  }
  
  try {
    const response = await userApi.validateVerificationToken(verificationToken.value)
    if (response.success) {
      ElMessage.success('令牌验证通过！')
      verificationResult.value = {
        title: '令牌有效',
        type: 'success',
        description: `验证令牌有效，可以用于后续认证流程。`
      }
    } else {
      ElMessage.error(`令牌验证失败: ${response.message}`)
      verificationResult.value = {
        title: '令牌无效',
        type: 'error',
        description: `令牌验证失败: ${response.message}`
      }
    }
  } catch (error) {
    console.error('令牌验证失败:', error)
    ElMessage.error('令牌验证失败，请重试')
  }
}

// 重置测试
const resetTest = () => {
  verificationToken.value = ''
  verificationResult.value = null
  ElMessage.info('测试已重置')
}

// 前往登录页面
const goToLogin = () => {
  router.push('/auth/login')
}
</script>

<style scoped lang="scss">
.test-slider-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.container {
  width: 100%;
  max-width: 600px;
}

.test-card {
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border-radius: 16px;
  border: none;
  
  :deep(.el-card__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 16px 16px 0 0;
  }
}

.card-header {
  text-align: center;
  
  h2 {
    margin: 0 0 8px 0;
    font-size: 24px;
    font-weight: 600;
  }
  
  p {
    margin: 0;
    opacity: 0.9;
    font-size: 14px;
  }
}

.slider-test-section {
  margin-bottom: 24px;
  display: flex;
  justify-content: center;
}

.result-section {
  margin-bottom: 24px;
}

.token-section {
  margin-bottom: 24px;
  
  .token-actions {
    margin-top: 12px;
    display: flex;
    gap: 12px;
    justify-content: center;
  }
}

.actions-section {
  display: flex;
  gap: 16px;
  justify-content: center;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
}

// 响应式设计
@media (max-width: 768px) {
  .test-slider-page {
    padding: 12px;
  }
  
  .actions-section {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
  
  .token-actions {
    flex-direction: column;
    
    .el-button {
      width: 100%;
    }
  }
}

// 暗色主题适配
.dark {
  .test-card {
    background: var(--el-bg-color);
  }
}
</style> 