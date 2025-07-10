<template>
  <div class="slider-captcha" :style="{ width: width }">
    <div v-if="captchaData.background_image" class="captcha-image-container" :style="{ height: `${height}px` }">
      <img :src="captchaData.background_image" class="background-image" alt="captcha-bg" />
      <img :src="captchaData.slider_image" class="slider-image" :style="{ left: `${sliderLeft}px`, top: `${captchaData.y}px`, height: `${captchaData.h}px` }" alt="slider" />
    </div>
    <div v-else class="captcha-image-loading" :style="{ height: `${height}px` }">
      <div class="loading-icon"></div>
      <span>{{ tip }}</span>
    </div>
    <div class="slider-track" ref="trackRef">
      <div class="slider-thumb" ref="thumbRef" :class="{ 'is-dragging': isDragging }" @mousedown.prevent="onDragStart">
        <span class="thumb-icon">&gt;&gt;</span>
      </div>
      <div class="slider-tip">{{ isDragging ? '' : tip }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, reactive, onUnmounted } from 'vue'
import { userApi } from '@/api';

const props = defineProps({
  width: { type: String, default: '100%' },
  height: { type: Number, default: 150 }
})

const emit = defineEmits(['success', 'error', 'refresh'])

const captchaData = reactive({
  id: '',
  background_image: '',
  slider_image: '',
  y: 0,
  h: 0,
})

const sliderLeft = ref(0)
const tip = ref('加载中...')
const trackRef = ref<HTMLElement | null>(null)
const thumbRef = ref<HTMLElement | null>(null)

let startX = 0
let isDragging = false

const fetchCaptcha = async () => {
  reset()
  tip.value = '加载中...'
  try {
    const response = await userApi.generateSliderCaptcha();
    Object.assign(captchaData, response.data)
    tip.value = '向右拖动滑块完成拼图'
    emit('refresh')
  } catch (err) {
    tip.value = '加载失败, 请刷新'
    emit('error', '加载验证码失败')
  }
}

const onDragStart = (e: MouseEvent) => {
  if (!captchaData.id || tip.value.includes('失败')) return
  isDragging = true
  startX = e.clientX
  document.addEventListener('mousemove', onDragMove)
  document.addEventListener('mouseup', onDragEnd)
}

const onDragMove = (e: MouseEvent) => {
  if (!isDragging || !trackRef.value || !thumbRef.value) return
  e.preventDefault();
  const moveX = e.clientX - startX
  const trackWidth = trackRef.value.clientWidth
  const thumbWidth = thumbRef.value.clientWidth
  
  const newLeft = Math.max(0, Math.min(moveX, trackWidth - thumbWidth))
  sliderLeft.value = newLeft
}

const onDragEnd = async () => {
  if (!isDragging) return
  isDragging = false
  document.removeEventListener('mousemove', onDragMove)
  document.removeEventListener('mouseup', onDragEnd)

  if (sliderLeft.value < 10) return

  tip.value = '验证中...'
  try {
    const response = await userApi.verifySliderCaptcha({
      id: captchaData.id,
      position: Math.round(sliderLeft.value)
    })
    
    if (response.data.success) {
      tip.value = '验证成功'
      emit('success', response.data.token)
    } else {
      tip.value = '验证失败, 请重试'
      emit('error', '验证失败')
      setTimeout(fetchCaptcha, 1000)
    }
  } catch (err) {
    tip.value = '验证失败, 请重试'
    emit('error', '验证失败')
    setTimeout(fetchCaptcha, 1000)
  }
}

const reset = () => {
    sliderLeft.value = 0
    captchaData.id = ''
    captchaData.background_image = ''
    captchaData.slider_image = ''
}

onMounted(fetchCaptcha)

onUnmounted(() => {
    document.removeEventListener('mousemove', onDragMove)
    document.removeEventListener('mouseup', onDragEnd)
})

defineExpose({ refresh: fetchCaptcha })

</script>

<style scoped>
.slider-captcha {
  position: relative;
  user-select: none;
  width: 100%;
}
.captcha-image-container {
  position: relative;
  overflow: hidden;
  border-radius: var(--el-border-radius-base);
  background-color: var(--el-fill-color-light);
}
.captcha-image-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  background-color: #f7f9fa;
  border: 1px dashed #dcdfe6;
  border-radius: 4px;
  color: #909399;
}
.loading-icon {
  width: 30px;
  height: 30px;
  border: 3px solid #c0c4cc;
  border-top-color: var(--el-color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
.background-image, .slider-image {
  position: absolute;
  top: 0;
}
.background-image {
  width: 100%;
  height: 100%;
}
.slider-image {
  height: auto; /* Let the height be determined by aspect ratio */
}
.slider-track {
  position: relative;
  height: 40px;
  line-height: 40px;
  background-color: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  border-radius: var(--el-border-radius-base);
  margin-top: 10px;
  text-align: center;
  overflow: hidden;
}
.slider-tip {
  color: var(--el-text-color-placeholder);
  transition: color 0.2s;
}
.slider-thumb {
  position: absolute;
  top: 0;
  left: 0;
  width: 50px;
  height: 100%;
  background-color: #fff;
  border: 1px solid var(--el-border-color);
  border-radius: var(--el-border-radius-base);
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--el-text-color-regular);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  transition: background-color 0.2s, border-color 0.2s, box-shadow 0.2s;
}
.slider-thumb.is-dragging,
.slider-thumb:hover {
  background-color: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: #fff;
}
.slider-thumb:active {
  cursor: grabbing;
}
.thumb-icon {
  font-weight: bold;
}
</style> 