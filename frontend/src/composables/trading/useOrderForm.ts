import { reactive, ref } from 'vue'
import { tradingApi } from '@/api'
import { useTradingStore } from '@/stores/modules/trading'
import type { OrderFormData } from '@/types/trading'

export const useOrderForm = () => {
  const tradingStore = useTradingStore()
  const submitting = ref(false)
  
  // 表单数据
  const form = reactive<OrderFormData>({
    symbol: '',
    side: 'buy',
    orderType: 'limit',
    price: 0,
    quantity: 0,
    timeInForce: 'GTC',
    clientOrderId: ''
  })

  // 验证规则
  const rules = {
    symbol: [
      { required: true, message: '请选择股票代码', trigger: 'blur' }
    ],
    price: [
      { 
        required: true, 
        message: '请输入委托价格', 
        trigger: 'blur',
        validator: (rule: any, value: number, callback: Function) => {
          if (form.orderType !== 'market' && (!value || value <= 0)) {
            callback(new Error('委托价格必须大于0'))
          } else {
            callback()
          }
        }
      }
    ],
    quantity: [
      { 
        required: true, 
        message: '请输入委托数量', 
        trigger: 'blur',
        validator: (rule: any, value: number, callback: Function) => {
          if (!value || value <= 0) {
            callback(new Error('委托数量必须大于0'))
          } else if (value % 100 !== 0) {
            callback(new Error('委托数量必须是100的整数倍'))
          } else {
            callback()
          }
        }
      }
    ]
  }

  // 表单验证
  const validateForm = async () => {
    // 这里应该调用实际的表单验证
    return Promise.resolve()
  }

  // 提交订单
  const submitOrder = async () => {
    submitting.value = true
    
    try {
      // 生成客户端订单ID
      form.clientOrderId = generateOrderId()
      
      // 调用API提交订单
      const result = await tradingApi.createOrder({
        symbol: form.symbol,
        side: form.side,
        orderType: form.orderType,
        quantity: form.quantity,
        price: form.orderType === 'market' ? undefined : form.price,
        timeInForce: form.timeInForce,
        clientOrderId: form.clientOrderId
      })
      
      // 更新本地订单状态
      await tradingStore.fetchOrders()
      await tradingStore.fetchPositions()
      
      return result
    } catch (error) {
      console.error('提交订单失败:', error)
      throw error
    } finally {
      submitting.value = false
    }
  }

  // 重置表单
  const resetForm = () => {
    Object.assign(form, {
      symbol: '',
      side: 'buy',
      orderType: 'limit',
      price: 0,
      quantity: 0,
      timeInForce: 'GTC',
      clientOrderId: ''
    })
  }

  // 生成订单ID
  const generateOrderId = () => {
    const timestamp = Date.now()
    const random = Math.random().toString(36).substr(2, 9)
    return `${timestamp}-${random}`
  }

  // 计算预估手续费
  const calculateFee = (amount: number) => {
    // 简化的手续费计算
    const feeRate = 0.0003 // 万分之三
    const minFee = 5 // 最低5元
    return Math.max(amount * feeRate, minFee)
  }

  // 计算预估总金额
  const calculateTotalAmount = () => {
    const amount = form.price * form.quantity
    const fee = calculateFee(amount)
    return amount + fee
  }

  return {
    form,
    rules,
    submitting,
    validateForm,
    submitOrder,
    resetForm,
    calculateFee,
    calculateTotalAmount
  }
}