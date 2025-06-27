/**
 * 表单验证规则类型
 */
export interface ValidationRule {
  required?: boolean
  message?: string
  validator?: (value: any) => boolean | string | Promise<boolean | string>
  trigger?: 'blur' | 'change' | 'submit'
}

/**
 * 验证结果类型
 */
export interface ValidationResult {
  valid: boolean
  message?: string
}

/**
 * 基础验证函数类型
 */
type ValidatorFunction = (value: any, ...args: any[]) => boolean | string

/**
 * 异步验证函数类型
 */
type AsyncValidatorFunction = (value: any, ...args: any[]) => Promise<boolean | string>

/**
 * 通用验证规则创建器
 */
export function createRule(
  validator: ValidatorFunction | AsyncValidatorFunction,
  message: string,
  trigger: 'blur' | 'change' | 'submit' = 'blur'
): ValidationRule {
  return {
    validator,
    message,
    trigger
  }
}

/**
 * 必填验证
 */
export function required(message = '此字段为必填项'): ValidationRule {
  return {
    required: true,
    message,
    validator: (value: any) => {
      if (value === null || value === undefined) return false
      if (typeof value === 'string') return value.trim().length > 0
      if (Array.isArray(value)) return value.length > 0
      return true
    }
  }
}

/**
 * 字符串长度验证
 */
export function length(
  min?: number,
  max?: number,
  message?: string
): ValidationRule {
  return createRule(
    (value: string) => {
      if (!value) return true // 空值由 required 规则处理
      
      const len = value.length
      
      if (min !== undefined && len < min) {
        return message || `长度不能少于${min}个字符`
      }
      
      if (max !== undefined && len > max) {
        return message || `长度不能超过${max}个字符`
      }
      
      return true
    },
    message || '长度不符合要求'
  )
}

/**
 * 数值范围验证
 */
export function range(
  min?: number,
  max?: number,
  message?: string
): ValidationRule {
  return createRule(
    (value: number | string) => {
      if (value === null || value === undefined || value === '') return true
      
      const num = typeof value === 'string' ? parseFloat(value) : value
      
      if (isNaN(num)) {
        return '请输入有效的数字'
      }
      
      if (min !== undefined && num < min) {
        return message || `值不能小于${min}`
      }
      
      if (max !== undefined && num > max) {
        return message || `值不能大于${max}`
      }
      
      return true
    },
    message || '数值超出范围'
  )
}

/**
 * 正则表达式验证
 */
export function pattern(
  regex: RegExp,
  message = '格式不正确'
): ValidationRule {
  return createRule(
    (value: string) => {
      if (!value) return true
      return regex.test(value)
    },
    message
  )
}

/**
 * 邮箱验证
 */
export function email(message = '请输入有效的邮箱地址'): ValidationRule {
  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
  return pattern(emailRegex, message)
}

/**
 * 手机号验证
 */
export function phone(message = '请输入有效的手机号码'): ValidationRule {
  const phoneRegex = /^1[3-9]\d{9}$/
  return pattern(phoneRegex, message)
}

/**
 * 身份证号验证
 */
export function idCard(message = '请输入有效的身份证号'): ValidationRule {
  return createRule(
    (value: string) => {
      if (!value) return true
      
      // 18位身份证号正则
      const idCardRegex = /^[1-9]\d{5}(18|19|20)\d{2}((0[1-9])|(1[0-2]))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$/
      
      if (!idCardRegex.test(value)) {
        return false
      }
      
      // 校验码验证
      const weights = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
      const checkCodes = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
      
      let sum = 0
      for (let i = 0; i < 17; i++) {
        sum += parseInt(value[i]) * weights[i]
      }
      
      const checkCode = checkCodes[sum % 11]
      return value[17].toUpperCase() === checkCode
    },
    message
  )
}

/**
 * 密码强度验证
 */
export function password(
  options: {
    minLength?: number
    requireUppercase?: boolean
    requireLowercase?: boolean
    requireNumbers?: boolean
    requireSpecialChars?: boolean
  } = {},
  message?: string
): ValidationRule {
  const {
    minLength = 8,
    requireUppercase = true,
    requireLowercase = true,
    requireNumbers = true,
    requireSpecialChars = true
  } = options

  return createRule(
    (value: string) => {
      if (!value) return true
      
      if (value.length < minLength) {
        return `密码长度不能少于${minLength}位`
      }
      
      if (requireUppercase && !/[A-Z]/.test(value)) {
        return '密码必须包含大写字母'
      }
      
      if (requireLowercase && !/[a-z]/.test(value)) {
        return '密码必须包含小写字母'
      }
      
      if (requireNumbers && !/\d/.test(value)) {
        return '密码必须包含数字'
      }
      
      if (requireSpecialChars && !/[!@#$%^&*(),.?":{}|<>]/.test(value)) {
        return '密码必须包含特殊字符'
      }
      
      return true
    },
    message || '密码强度不符合要求'
  )
}

/**
 * 确认密码验证
 */
export function confirmPassword(
  getOriginalPassword: () => string,
  message = '两次输入的密码不一致'
): ValidationRule {
  return createRule(
    (value: string) => {
      if (!value) return true
      return value === getOriginalPassword()
    },
    message
  )
}

/**
 * URL验证
 */
export function url(message = '请输入有效的URL地址'): ValidationRule {
  const urlRegex = /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/
  return pattern(urlRegex, message)
}

/**
 * 数字验证 (整数)
 */
export function integer(message = '请输入整数'): ValidationRule {
  return pattern(/^-?\d+$/, message)
}

/**
 * 数字验证 (正整数)
 */
export function positiveInteger(message = '请输入正整数'): ValidationRule {
  return pattern(/^[1-9]\d*$/, message)
}

/**
 * 数字验证 (非负整数)
 */
export function nonNegativeInteger(message = '请输入非负整数'): ValidationRule {
  return pattern(/^(0|[1-9]\d*)$/, message)
}

/**
 * 数字验证 (小数)
 */
export function decimal(
  precision?: number,
  message?: string
): ValidationRule {
  const regex = precision 
    ? new RegExp(`^-?\\d+(\\.\\d{1,${precision}})?$`)
    : /^-?\d+(\.\d+)?$/
    
  return pattern(
    regex, 
    message || (precision ? `请输入有效的小数(最多${precision}位小数)` : '请输入有效的小数')
  )
}

/**
 * 金融相关验证规则
 */
export const FinancialValidators = {
  /**
   * 股票代码验证
   */
  stockCode(message = '请输入有效的股票代码'): ValidationRule {
    return createRule(
      (value: string) => {
        if (!value) return true
        
        // A股代码格式: 6位数字
        const aStockRegex = /^[0-9]{6}$/
        
        // 港股代码格式: 5位数字
        const hkStockRegex = /^[0-9]{5}$/
        
        // 美股代码格式: 1-5位字母
        const usStockRegex = /^[A-Z]{1,5}$/
        
        return aStockRegex.test(value) || hkStockRegex.test(value) || usStockRegex.test(value.toUpperCase())
      },
      message
    )
  },

  /**
   * 价格验证
   */
  price(
    min = 0,
    max = 999999,
    precision = 2,
    message?: string
  ): ValidationRule {
    return createRule(
      (value: number | string) => {
        if (value === null || value === undefined || value === '') return true
        
        const num = typeof value === 'string' ? parseFloat(value) : value
        
        if (isNaN(num)) {
          return '请输入有效的价格'
        }
        
        if (num < min) {
          return `价格不能小于${min}`
        }
        
        if (num > max) {
          return `价格不能大于${max}`
        }
        
        // 检查小数位数
        const decimalPlaces = (num.toString().split('.')[1] || '').length
        if (decimalPlaces > precision) {
          return `价格最多${precision}位小数`
        }
        
        return true
      },
      message || '请输入有效的价格'
    )
  },

  /**
   * 数量验证 (股票交易数量，通常为100的倍数)
   */
  quantity(
    min = 100,
    max = 999999999,
    multiple = 100,
    message?: string
  ): ValidationRule {
    return createRule(
      (value: number | string) => {
        if (value === null || value === undefined || value === '') return true
        
        const num = typeof value === 'string' ? parseInt(value) : value
        
        if (isNaN(num) || !Number.isInteger(num)) {
          return '请输入有效的整数数量'
        }
        
        if (num < min) {
          return `数量不能小于${min}`
        }
        
        if (num > max) {
          return `数量不能大于${max}`
        }
        
        if (multiple > 1 && num % multiple !== 0) {
          return `数量必须是${multiple}的倍数`
        }
        
        return true
      },
      message || '请输入有效的数量'
    )
  },

  /**
   * 银行卡号验证
   */
  bankCard(message = '请输入有效的银行卡号'): ValidationRule {
    return createRule(
      (value: string) => {
        if (!value) return true
        
        // 移除空格
        const cardNumber = value.replace(/\s/g, '')
        
        // 长度检查 (通常16-19位)
        if (!/^\d{16,19}$/.test(cardNumber)) {
          return false
        }
        
        // Luhn算法验证
        let sum = 0
        let isEven = false
        
        for (let i = cardNumber.length - 1; i >= 0; i--) {
          let digit = parseInt(cardNumber[i])
          
          if (isEven) {
            digit *= 2
            if (digit > 9) {
              digit -= 9
            }
          }
          
          sum += digit
          isEven = !isEven
        }
        
        return sum % 10 === 0
      },
      message
    )
  },

  /**
   * 资金密码验证 (6位数字)
   */
  fundPassword(message = '资金密码必须是6位数字'): ValidationRule {
    return pattern(/^\d{6}$/, message)
  },

  /**
   * 风险等级验证
   */
  riskLevel(message = '请选择有效的风险等级'): ValidationRule {
    const validLevels = ['conservative', 'moderate', 'balanced', 'growth', 'aggressive']
    
    return createRule(
      (value: string) => {
        if (!value) return true
        return validLevels.includes(value)
      },
      message
    )
  },

  /**
   * 投资期限验证 (月数)
   */
  investmentPeriod(
    min = 1,
    max = 120,
    message?: string
  ): ValidationRule {
    return createRule(
      (value: number | string) => {
        if (value === null || value === undefined || value === '') return true
        
        const num = typeof value === 'string' ? parseInt(value) : value
        
        if (isNaN(num) || !Number.isInteger(num)) {
          return '请输入有效的投资期限(月)'
        }
        
        if (num < min) {
          return `投资期限不能少于${min}个月`
        }
        
        if (num > max) {
          return `投资期限不能超过${max}个月`
        }
        
        return true
      },
      message || '请输入有效的投资期限'
    )
  }
}

/**
 * 自定义验证器组合
 */
export function combine(...rules: ValidationRule[]): ValidationRule[] {
  return rules
}

/**
 * 异步验证器 - 检查用户名是否已存在
 */
export function uniqueUsername(
  checkFunction: (username: string) => Promise<boolean>,
  message = '用户名已存在'
): ValidationRule {
  return createRule(
    async (value: string) => {
      if (!value) return true
      
      const isUnique = await checkFunction(value)
      return isUnique || message
    },
    message
  )
}

/**
 * 异步验证器 - 检查邮箱是否已注册
 */
export function uniqueEmail(
  checkFunction: (email: string) => Promise<boolean>,
  message = '邮箱已被注册'
): ValidationRule {
  return createRule(
    async (value: string) => {
      if (!value) return true
      
      // 先检查邮箱格式
      const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/
      if (!emailRegex.test(value)) {
        return '请输入有效的邮箱地址'
      }
      
      const isUnique = await checkFunction(value)
      return isUnique || message
    },
    message
  )
}

/**
 * 条件验证器 - 根据条件决定是否执行验证
 */
export function conditional(
  condition: () => boolean,
  rule: ValidationRule
): ValidationRule {
  return {
    ...rule,
    validator: (value: any) => {
      if (!condition()) return true
      return rule.validator ? rule.validator(value) : true
    }
  }
}

/**
 * 表单验证工具类
 */
export class FormValidator {
  private rules: Record<string, ValidationRule[]> = {}

  /**
   * 添加字段验证规则
   */
  addField(field: string, rules: ValidationRule[]): void {
    this.rules[field] = rules
  }

  /**
   * 验证单个字段
   */
  async validateField(field: string, value: any): Promise<ValidationResult> {
    const fieldRules = this.rules[field]
    if (!fieldRules) {
      return { valid: true }
    }

    for (const rule of fieldRules) {
      if (rule.required && (value === null || value === undefined || value === '')) {
        return {
          valid: false,
          message: rule.message || '此字段为必填项'
        }
      }

      if (rule.validator) {
        const result = await rule.validator(value)
        if (result !== true) {
          return {
            valid: false,
            message: typeof result === 'string' ? result : rule.message
          }
        }
      }
    }

    return { valid: true }
  }

  /**
   * 验证整个表单
   */
  async validateForm(data: Record<string, any>): Promise<{
    valid: boolean
    errors: Record<string, string>
  }> {
    const errors: Record<string, string> = {}

    for (const [field, rules] of Object.entries(this.rules)) {
      const result = await this.validateField(field, data[field])
      if (!result.valid && result.message) {
        errors[field] = result.message
      }
    }

    return {
      valid: Object.keys(errors).length === 0,
      errors
    }
  }

  /**
   * 清除字段规则
   */
  removeField(field: string): void {
    delete this.rules[field]
  }

  /**
   * 清除所有规则
   */
  clear(): void {
    this.rules = {}
  }
} 