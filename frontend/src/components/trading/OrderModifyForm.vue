<template>
  <el-dialog
    v-model="visible"
    width="600px"
    :before-close="handleClose"
    title="修改订单"
  >
    <el-form :model="form" label-width="90px" :rules="rules" ref="formRef">
      <el-form-item label="委托价格" prop="price">
        <el-input-number v-model="form.price" :min="0" :precision="2" :step="0.01" />
      </el-form-item>
      <el-form-item label="委托数量" prop="quantity">
        <el-input-number v-model="form.quantity" :min="1" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, computed, ref } from 'vue'
import { ElMessage, FormInstance, FormRules } from 'element-plus'
import type { Order } from '@/types/trading'

interface Props {
  modelValue: boolean
  order: Order | null
}
const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
  (e: 'save', order: Partial<Order>): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v)
})

const form = reactive({
  price: props.order?.price ?? 0,
  quantity: props.order?.quantity ?? 0
})

const rules: FormRules = {
  price: [{ required: true, message: '请输入价格', trigger: 'blur' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }]
}

const formRef = ref<FormInstance>()

const handleSave = () => {
  if (!formRef.value) return
  formRef.value.validate((valid) => {
    if (!valid) return
    emit('save', { price: form.price, quantity: form.quantity })
    ElMessage.success('修改成功')
    handleClose()
  })
}

const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
</style> 