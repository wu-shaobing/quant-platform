<template>
  <el-dialog
    v-model="visible"
    width="800px"
    top="10vh"
    :before-close="handleClose"
    title="订单详情"
  >
    <div v-if="order">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="订单编号">{{ order.orderNo }}</el-descriptions-item>
        <el-descriptions-item label="订单ID">{{ order.id }}</el-descriptions-item>
        <el-descriptions-item label="股票">{{ order.stockCode }} {{ order.stockName }}</el-descriptions-item>
        <el-descriptions-item label="方向">
          <el-tag :type="order.side === 'buy' ? 'danger' : 'success'">
            {{ order.side === 'buy' ? '买入' : '卖出' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusType(order.status)">{{ statusLabel(order.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="委托数量">{{ formatNumber(order.quantity) }}</el-descriptions-item>
        <el-descriptions-item label="委托价格">{{ formatPrice(order.price) }}</el-descriptions-item>
        <el-descriptions-item label="成交数量">{{ formatNumber(order.filledQuantity) }}</el-descriptions-item>
        <el-descriptions-item label="成交均价">{{ formatPrice(order.filledPrice) }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(order.createTime) }}</el-descriptions-item>
        <el-descriptions-item label="更新时间">{{ formatDateTime(order.updateTime) }}</el-descriptions-item>
        <el-descriptions-item v-if="order.rejectReason" label="拒绝原因" :span="2">
          <el-text type="danger">{{ order.rejectReason }}</el-text>
        </el-descriptions-item>
      </el-descriptions>
    </div>
    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElTag, ElDescriptions, ElDescriptionsItem, ElText } from 'element-plus'
import type { Order } from '@/types/trading'
import { formatNumber, formatPrice, formatDateTime } from '@/utils/formatters'

interface Props {
  modelValue: boolean
  order: Order | null
}
const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', v: boolean): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v)
})

const handleClose = () => {
  visible.value = false
}

const statusLabel = (status: string) => {
  const map: Record<string, string> = {
    pending: '待成交',
    partial: '部分成交',
    filled: '已成交',
    cancelled: '已撤销',
    rejected: '已拒绝'
  }
  return map[status] || status
}
const statusType = (status: string) => {
  const map: Record<string, string> = {
    pending: 'warning',
    partial: 'info',
    filled: 'success',
    cancelled: 'default',
    rejected: 'danger'
  }
  return map[status] || 'default'
}
</script>

<style scoped>
/* 简单样式占位 */
</style> 