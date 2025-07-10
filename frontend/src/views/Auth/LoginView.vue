<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 左侧品牌区域 -->
      <div class="brand-section">
        <div class="brand-content">
          <div class="brand-logo">
            <el-icon size="48"><TrendCharts /></el-icon>
          </div>
          <h1 class="brand-title">量化投资平台</h1>
          <p class="brand-subtitle">专业的量化交易与投资管理系统</p>
          
          <div class="features">
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>实时行情数据</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>智能策略回测</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>风险控制管理</span>
            </div>
            <div class="feature-item">
              <el-icon><Check /></el-icon>
              <span>投资组合优化</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧登录表单 -->
      <div class="form-section">
        <div class="form-container">
          <div class="form-header">
            <h2>{{ isLogin ? '登录账户' : '注册账户' }}</h2>
            <p>{{ isLogin ? '欢迎回来，请登录您的账户' : '创建新账户开始量化投资之旅' }}</p>
          </div>
          
          <el-form
            ref="formRef"
            :model="formData"
            :rules="dynamicRules"
            class="login-form"
            size="large"
            @submit.prevent="handleSubmit"
          >
            <!-- 用户名/邮箱 -->
            <el-form-item prop="username">
              <el-input
                v-model="formData.username"
                :placeholder="isLogin ? '用户名或邮箱' : '用户名'"
                :prefix-icon="User"
                clearable
              />
            </el-form-item>
            
            <!-- 邮箱（仅注册时显示） -->
            <el-form-item v-if="!isLogin" prop="email">
              <el-input
                v-model="formData.email"
                placeholder="邮箱地址"
                :prefix-icon="Message"
                clearable
              />
            </el-form-item>
            
            <!-- 密码 -->
            <el-form-item prop="password">
              <el-input
                v-model="formData.password"
                type="password"
                show-password
                placeholder="请输入密码"
                :prefix-icon="Lock"
                clearable
                @blur="!isLogin && formRef?.validateField('confirmPassword')"
              />
            </el-form-item>
            
            <!-- 确认密码（仅注册时显示） -->
            <el-form-item v-if="!isLogin" prop="confirmPassword">
              <el-input
                v-model="formData.confirmPassword"
                type="password"
                placeholder="确认密码"
                :prefix-icon="Lock"
                show-password
                clearable
              />
            </el-form-item>
            
            <!-- 滑块验证 -->
            <el-form-item prop="verificationToken">
              <SliderCaptcha
                ref="sliderCaptchaRef"
                @success="onCaptchaSuccess"
                @error="onCaptchaError"
                @refresh="onCaptchaRefresh"
              />
            </el-form-item>
            
            <!-- 记住我 & 忘记密码 -->
            <div class="form-options" v-if="isLogin">
              <el-checkbox v-model="formData.remember">记住我</el-checkbox>
              <el-button type="text" @click="showForgotPassword">
                忘记密码？
              </el-button>
            </div>
            
            <!-- 用户协议（仅注册时显示） -->
            <div class="form-options" v-if="!isLogin">
              <el-form-item prop="agreeTerms">
                <el-checkbox v-model="formData.agreeTerms">
                  我已阅读并同意
                  <el-button type="text" @click="showTerms">用户协议</el-button>
                  和
                  <el-button type="text" @click="showPrivacy">隐私政策</el-button>
                </el-checkbox>
              </el-form-item>
            </div>
            
            <!-- 提交按钮 -->
            <el-form-item>
              <el-button
                type="primary"
                class="submit-button"
                :loading="loading"
                @click="handleSubmit"
                native-type="submit"
              >
                {{ isLogin ? '登录' : '注册' }}
              </el-button>
            </el-form-item>
            
            <!-- 切换登录/注册 -->
            <div class="form-switch">
              <span>{{ isLogin ? '还没有账户？' : '已有账户？' }}</span>
              <el-button type="text" @click="toggleMode">
                {{ isLogin ? '立即注册' : '立即登录' }}
              </el-button>
            </div>
          </el-form>
          
          <!-- 第三方登录 -->
          <div class="social-login">
            <div class="divider">
              <span>或使用第三方登录</span>
            </div>
            <div class="social-buttons">
              <el-button class="social-button wechat" @click="loginWithWechat">
                <el-icon><ChatDotRound /></el-icon>
                微信
              </el-button>
              <el-button class="social-button qq" @click="loginWithQQ">
                <el-icon><User /></el-icon>
                QQ
              </el-button>
              <el-button class="social-button github" @click="loginWithGithub">
                <el-icon><Link /></el-icon>
                GitHub
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 忘记密码对话框 -->
    <el-dialog
      v-model="forgotPasswordVisible"
      title="重置密码"
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form :model="resetForm" :rules="resetRules" ref="resetFormRef">
        <el-form-item label="邮箱地址" prop="email">
          <el-input
            v-model="resetForm.email"
            placeholder="请输入注册邮箱"
            :prefix-icon="Message"
          />
        </el-form-item>
        <el-form-item label="验证码" prop="code">
          <div class="code-row">
            <el-input
              v-model="resetForm.code"
              placeholder="邮箱验证码"
              style="flex: 1"
            />
            <el-button
              :disabled="codeCountdown > 0"
              @click="sendResetCode"
            >
              {{ codeCountdown > 0 ? `${codeCountdown}s` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="forgotPasswordVisible = false">取消</el-button>
          <el-button type="primary" @click="resetPassword">
            重置密码
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import {
  TrendCharts,
  Check,
  User,
  Message,
  Lock,
  ChatDotRound,
  Link,
  Key,
  Loading
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useUserStore } from '@/stores/modules/user'
import { userApi } from '@/api'
import SliderCaptcha from '@/components/common/SliderCaptcha/index.vue'

// Router
const router = useRouter()

// Store
const userStore = useUserStore()

// State
const loading = ref(false)
const isLogin = ref(true)
const forgotPasswordVisible = ref(false)
const codeCountdown = ref(0)

// Form refs
const formRef = ref<FormInstance>()
const resetFormRef = ref<FormInstance>()
const sliderCaptchaRef = ref<InstanceType<typeof SliderCaptcha>>()

// Form data
const formData = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  remember: false,
  agreeTerms: false,
  verificationToken: ''
})

// Reset password form
const resetForm = reactive({
  email: '',
  code: ''
})

// Validation Rules
const validatePass = (_rule: any, value: any, callback: any) => {
  if (!isLogin.value && value !== formData.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const formRules = reactive<FormRules>({
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码长度不能少于8位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validatePass, trigger: 'blur' }
  ],
  verificationToken: [{ required: true, message: '请完成滑块验证', trigger: 'change' }],
  agreeTerms: [
    {
      validator: (_rule, value, callback) => {
        if (value) {
          callback()
        } else {
          callback(new Error('请阅读并同意用户协议和隐私政策'))
        }
      },
      trigger: 'change'
    }
  ]
})

// 根据登录/注册状态动态返回规则
const dynamicRules = computed(() => {
  if (isLogin.value) {
    return {
      username: formRules.username,
      password: formRules.password,
      verificationToken: formRules.verificationToken,
    }
  }
  return {
    username: formRules.username,
    email: formRules.email,
    password: formRules.password,
    confirmPassword: formRules.confirmPassword,
    verificationToken: formRules.verificationToken,
    agreeTerms: formRules.agreeTerms,
  }
})

// Methods
const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        if (isLogin.value) {
          await userStore.login(formData)
          router.push('/')
        } else {
          await userStore.register(formData)
          ElMessage.success('注册成功！请登录。')
          isLogin.value = true
        }
      } catch (error: any) {
        ElMessage.error(error.message || '操作失败')
        // 失败后刷新验证码
        sliderCaptchaRef.value?.refresh()
      } finally {
        loading.value = false
      }
    }
  })
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
  formRef.value?.resetFields()
  sliderCaptchaRef.value?.refresh()
}

const showForgotPassword = () => {
  forgotPasswordVisible.value = true
}

const sendResetCode = async () => {
  if (!resetForm.email) {
    ElMessage.warning('请输入邮箱地址')
    return
  }

  try {
    // 发送重置密码验证码
    await userStore.sendResetCode(resetForm.email)
    
    ElMessage.success('验证码已发送到您的邮箱')
    
    // 开始倒计时
    codeCountdown.value = 60
    const timer = setInterval(() => {
      codeCountdown.value--
      if (codeCountdown.value <= 0) {
        clearInterval(timer)
      }
    }, 1000)
  } catch (error: any) {
    ElMessage.error(error.message || '发送验证码失败')
  }
}

const resetPassword = async () => {
  if (!resetFormRef.value) return

  await resetFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      await userStore.resetPassword({
        email: resetForm.email,
        code: resetForm.code
      })

      ElMessage.success('密码重置成功，新密码已发送到您的邮箱')
      forgotPasswordVisible.value = false
      
      // 清空重置表单
      Object.assign(resetForm, { email: '', code: '' })
    } catch (error: any) {
      ElMessage.error(error.message || '密码重置失败')
    }
  })
}

const showTerms = () => {
  ElMessageBox.alert('用户协议内容...', '用户协议', {
    confirmButtonText: '我已阅读'
  })
}

const showPrivacy = () => {
  ElMessageBox.alert('隐私政策内容...', '隐私政策', {
    confirmButtonText: '我已阅读'
  })
}

const loginWithWechat = () => {
  ElMessage.info('微信登录功能开发中...')
}

const loginWithQQ = () => {
  ElMessage.info('QQ登录功能开发中...')
}

const loginWithGithub = () => {
  ElMessage.info('GitHub登录功能开发中...')
}

// Captcha event handlers
const onCaptchaSuccess = (token: string) => {
  formData.verificationToken = token
  formRef.value?.validateField('verificationToken')
}

const onCaptchaError = () => {
  formData.verificationToken = ''
  // 可选：在这里给用户提示
}

const onCaptchaRefresh = () => {
  formData.verificationToken = ''
}

// Mounting logic
onMounted(() => {
  const icons = {
    User,
    Lock,
  }
  // You can use icons here
  // 如果已经登录，直接跳转
  if (userStore.isLoggedIn) {
    router.push('/')
  }
})
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.login-container {
  display: flex;
  width: 100%;
  max-width: 1000px;
  min-height: 600px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.brand-section {
  flex: 1;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.brand-content {
  text-align: center;
  max-width: 400px;
}

.brand-logo {
  margin-bottom: 24px;
}

.brand-title {
  font-size: 32px;
  font-weight: 600;
  margin: 0 0 12px 0;
}

.brand-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0 0 40px 0;
  line-height: 1.6;
}

.features {
  text-align: left;
}

.feature-item {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  font-size: 14px;
}

.feature-item .el-icon {
  margin-right: 12px;
  color: #67c23a;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  padding: 4px;
}

.form-section {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}

.form-container {
  width: 100%;
  max-width: 400px;
}

.form-header {
  text-align: center;
  margin-bottom: 32px;
}

.form-header h2 {
  font-size: 28px;
  color: #333;
  margin: 0 0 8px 0;
}

.form-header p {
  color: #666;
  font-size: 14px;
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}

.captcha-row {
  display: flex;
  width: 100%;
  gap: 10px;
}

.captcha-input {
  flex-grow: 1;
}

.captcha-image-container {
  flex-shrink: 0;
  width: 120px;
  height: 40px;
  border: 1px solid var(--el-border-color);
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.captcha-image {
  width: 100%;
  height: 100%;
}

.captcha-loading {
  font-size: 20px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  font-size: 14px;
}

.submit-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
}

.form-switch {
  text-align: center;
  font-size: 14px;
  color: #666;
}

.social-login {
  margin-top: 32px;
}

.divider {
  position: relative;
  text-align: center;
  margin-bottom: 20px;
}

.divider::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 1px;
  background: #e8e8e8;
}

.divider span {
  background: white;
  padding: 0 16px;
  color: #666;
  font-size: 12px;
}

.social-buttons {
  display: flex;
  gap: 12px;
}

.social-button {
  flex: 1;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
}

.social-button.wechat {
  background: #1aad19;
  color: white;
  border: none;
}

.social-button.qq {
  background: #12b7f5;
  color: white;
  border: none;
}

.social-button.github {
  background: #24292e;
  color: white;
  border: none;
}

.code-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 768px) {
  .login-container {
    flex-direction: column;
    max-width: 400px;
  }
  
  .brand-section {
    padding: 32px 20px;
  }
  
  .brand-title {
    font-size: 24px;
  }
  
  .form-section {
    padding: 32px 20px;
  }
  
  .social-buttons {
    flex-direction: column;
  }
}
</style>