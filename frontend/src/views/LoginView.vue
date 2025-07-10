<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="title">量化交易平台</h1>
        <p class="subtitle">登录您的账户</p>
      </div>

      <el-form 
        ref="loginFormRef" 
        :model="loginForm" 
        :rules="loginRules" 
        class="login-form"
        @keyup.enter="handleLogin"
      >
        <!-- 用户名输入框 -->
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="用户名"
            size="large"
            :prefix-icon="User"
            clearable
          />
        </el-form-item>

        <!-- 密码输入框 -->
        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            clearable
          />
        </el-form-item>

        <!-- 滑轨验证码 -->
        <el-form-item>
          <SliderCaptcha
            ref="sliderCaptchaRef"
            :width="320"
            :height="42"
            :show-image="false"
            success-text="验证通过"
            default-text="请按住滑块，拖动到最右边"
            error-text="验证失败，请重试"
            @success="handleCaptchaSuccess"
            @error="handleCaptchaError"
          >
            <template #text="{ isSuccess, isDragging }">
              <div class="flex items-center justify-center">
                <CheckCircle v-if="isSuccess" class="w-4 h-4 mr-2 text-green-500" />
                <ArrowRight v-else-if="isDragging" class="w-4 h-4 mr-2 text-blue-500 animate-pulse" />
                <LockIcon v-else class="w-4 h-4 mr-2 text-gray-400" />
                <span>{{ isSuccess ? '验证通过' : isDragging ? '继续拖动...' : '请按住滑块，拖动到最右边' }}</span>
              </div>
            </template>
            <template #icon="{ isSuccess, isDragging }">
              <CheckCircle v-if="isSuccess" class="w-5 h-5 text-white" />
              <ArrowRight v-else-if="isDragging" class="w-5 h-5 text-blue-500 animate-pulse" />
              <ChevronRight v-else class="w-5 h-5 text-blue-500" />
            </template>
          </SliderCaptcha>
        </el-form-item>

        <!-- 记住密码和忘记密码 -->
        <el-form-item>
          <div class="flex justify-between items-center w-full">
            <el-checkbox v-model="loginForm.rememberMe">记住密码</el-checkbox>
            <el-link type="primary" :underline="false">忘记密码？</el-link>
          </div>
        </el-form-item>

        <!-- 登录按钮 -->
        <el-form-item>
          <el-button 
            type="primary" 
            size="large" 
            class="login-button"
            :loading="loading"
            :disabled="!captchaToken"
            @click="handleLogin"
          >
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>

        <!-- 注册链接 -->
        <el-form-item>
          <div class="text-center w-full">
            <span class="text-gray-500">还没有账户？</span>
            <el-link type="primary" :underline="false" @click="showRegister = true">
              立即注册
            </el-link>
          </div>
        </el-form-item>
      </el-form>
    </div>

    <!-- 注册对话框 -->
    <el-dialog 
      v-model="showRegister" 
      title="用户注册" 
      width="400px"
      :close-on-click-modal="false"
    >
      <el-form 
        ref="registerFormRef" 
        :model="registerForm" 
        :rules="registerRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="registerForm.username" placeholder="请输入用户名" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="registerForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password">
          <el-input 
            v-model="registerForm.password" 
            type="password" 
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input 
            v-model="registerForm.confirmPassword" 
            type="password" 
            placeholder="请确认密码"
            show-password
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showRegister = false">取消</el-button>
          <el-button type="primary" :loading="registerLoading" @click="handleRegister">
            {{ registerLoading ? '注册中...' : '注册' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElForm } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { CheckCircle, ArrowRight, Lock as LockIcon, ChevronRight } from 'lucide-vue-next'
import SliderCaptcha from '@/components/SliderCaptcha.vue'
import { userApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 表单引用
const loginFormRef = ref<InstanceType<typeof ElForm>>()
const registerFormRef = ref<InstanceType<typeof ElForm>>()

// 滑轨验证码相关
const sliderCaptchaRef = ref()
const captchaToken = ref('')

// 加载状态
const loading = ref(false)
const registerLoading = ref(false)
const showRegister = ref(false)

// 登录表单数据
const loginForm = reactive({
  username: '',
  password: '',
  rememberMe: false
})

// 注册表单数据
const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 登录表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

// 注册表单验证规则
const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' },
    { pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]/, message: '密码必须包含大小写字母和数字', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 滑轨验证码成功回调
const handleCaptchaSuccess = (token: string, time: number) => {
  captchaToken.value = token
  console.log(`验证成功，耗时 ${time} 秒`)
  ElMessage.success(`验证成功，耗时 ${time} 秒`)
}

// 滑轨验证码失败回调
const handleCaptchaError = (message: string) => {
  captchaToken.value = ''
  console.error('验证失败:', message)
  ElMessage.error(message)
}

// 登录处理
const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  // 验证表单
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  // 检查验证码
  if (!captchaToken.value) {
    ElMessage.warning('请先完成滑轨验证')
    return
  }
  
  loading.value = true
  
  try {
    const response = await userApi.login({
      username: loginForm.username,
      password: loginForm.password,
      verification_token: captchaToken.value
    })
    
    // 保存用户信息
    userStore.setUser(response.user)
    userStore.setToken(response.access_token)
    
    ElMessage.success('登录成功')
    
    // 跳转到首页
    router.push('/')
    
  } catch (error: any) {
    console.error('登录失败:', error)
    ElMessage.error(error.response?.data?.detail || '登录失败，请重试')
    
    // 重置验证码
    captchaToken.value = ''
    sliderCaptchaRef.value?.reset()
  } finally {
    loading.value = false
  }
}

// 注册处理
const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  const valid = await registerFormRef.value.validate().catch(() => false)
  if (!valid) return
  
  registerLoading.value = true
  
  try {
    await userApi.register({
      username: registerForm.username,
      email: registerForm.email,
      password: registerForm.password
    })
    
    ElMessage.success('注册成功，请登录')
    showRegister.value = false
    
    // 清空注册表单
    Object.assign(registerForm, {
      username: '',
      email: '',
      password: '',
      confirmPassword: ''
    })
    
  } catch (error: any) {
    console.error('注册失败:', error)
    ElMessage.error(error.response?.data?.detail || '注册失败，请重试')
  } finally {
    registerLoading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  padding: 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.title {
  font-size: 28px;
  font-weight: 700;
  color: #1a202c;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 16px;
  color: #718096;
  margin: 0;
}

.login-form {
  width: 100%;
}

.login-button {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

:deep(.el-form-item) {
  margin-bottom: 20px;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
}

/* 响应式设计 */
@media (max-width: 480px) {
  .login-card {
    padding: 24px;
    margin: 0 16px;
  }
  
  .title {
    font-size: 24px;
  }
  
  .subtitle {
    font-size: 14px;
  }
}
</style> 