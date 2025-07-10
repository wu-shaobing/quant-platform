#!/usr/bin/env node

/**
 * 前端项目状态检查工具
 * 检查项目完成度、依赖状态、配置正确性等
 */

const fs = require('fs')
const path = require('path')

class ProjectChecker {
  constructor() {
    this.projectRoot = path.resolve(__dirname, '..')
    this.results = {
      dependencies: { status: 'unknown', details: [] },
      configuration: { status: 'unknown', details: [] },
      components: { status: 'unknown', details: [] },
      apis: { status: 'unknown', details: [] },
      stores: { status: 'unknown', details: [] },
      types: { status: 'unknown', details: [] },
      overall: { status: 'unknown', score: 0 }
    }
  }

  // 检查依赖
  checkDependencies() {
    console.log('🔍 检查依赖状态...')
    
    try {
      const packageJson = JSON.parse(
        fs.readFileSync(path.join(this.projectRoot, 'package.json'), 'utf8')
      )
      
      const requiredDeps = [
        'vue', 'typescript', 'vite', 'pinia', 'vue-router',
        'element-plus', 'echarts', '@vueuse/core'
      ]
      
      const missingDeps = requiredDeps.filter(dep => 
        !packageJson.dependencies[dep] && !packageJson.devDependencies[dep]
      )
      
      if (missingDeps.length === 0) {
        this.results.dependencies.status = 'good'
        this.results.dependencies.details.push('✅ 所有必需依赖已安装')
      } else {
        this.results.dependencies.status = 'warning'
        this.results.dependencies.details.push(`⚠️ 缺少依赖: ${missingDeps.join(', ')}`)
      }
      
      // 检查node_modules
      const nodeModulesExists = fs.existsSync(path.join(this.projectRoot, 'node_modules'))
      if (nodeModulesExists) {
        this.results.dependencies.details.push('✅ node_modules 目录存在')
      } else {
        this.results.dependencies.status = 'error'
        this.results.dependencies.details.push('❌ node_modules 目录不存在，请运行 npm install')
      }
      
    } catch (error) {
      this.results.dependencies.status = 'error'
      this.results.dependencies.details.push(`❌ 读取package.json失败: ${error.message}`)
    }
  }

  // 检查配置文件
  checkConfiguration() {
    console.log('🔍 检查配置文件...')
    
    const configFiles = [
      'vite.config.ts',
      'tsconfig.json', 
      'tailwind.config.js',
      '.env.development'
    ]
    
    let validConfigs = 0
    
    configFiles.forEach(file => {
      const filePath = path.join(this.projectRoot, file)
      if (fs.existsSync(filePath)) {
        this.results.configuration.details.push(`✅ ${file} 存在`)
        validConfigs++
      } else {
        this.results.configuration.details.push(`⚠️ ${file} 缺失`)
      }
    })
    
    if (validConfigs === configFiles.length) {
      this.results.configuration.status = 'good'
    } else if (validConfigs >= configFiles.length * 0.7) {
      this.results.configuration.status = 'warning'
    } else {
      this.results.configuration.status = 'error'
    }
  }

  // 检查组件完成度
  checkComponents() {
    console.log('🔍 检查组件完成度...')
    
    const componentDirs = [
      'src/components/charts',
      'src/components/trading', 
      'src/components/common',
      'src/components/market'
    ]
    
    let totalComponents = 0
    let validComponents = 0
    
    componentDirs.forEach(dir => {
      const dirPath = path.join(this.projectRoot, dir)
      if (fs.existsSync(dirPath)) {
        const files = fs.readdirSync(dirPath, { recursive: true })
        const vueFiles = files.filter(file => file.endsWith('.vue'))
        totalComponents += vueFiles.length
        
        vueFiles.forEach(file => {
          const filePath = path.join(dirPath, file)
          const content = fs.readFileSync(filePath, 'utf8')
          
          // 简单检查组件是否有基本结构
          if (content.includes('<template>') && content.includes('<script')) {
            validComponents++
          }
        })
        
        this.results.components.details.push(`✅ ${dir}: ${vueFiles.length} 个组件`)
      } else {
        this.results.components.details.push(`⚠️ ${dir}: 目录不存在`)
      }
    })
    
    const completionRate = totalComponents > 0 ? (validComponents / totalComponents) : 0
    
    if (completionRate >= 0.8) {
      this.results.components.status = 'good'
    } else if (completionRate >= 0.5) {
      this.results.components.status = 'warning'
    } else {
      this.results.components.status = 'error'
    }
    
    this.results.components.details.push(
      `📊 组件完成度: ${validComponents}/${totalComponents} (${(completionRate * 100).toFixed(1)}%)`
    )
  }

  // 检查API层
  checkApis() {
    console.log('🔍 检查API层...')
    
    const apiFiles = [
      'src/api/http.ts',
      'src/api/market.ts',
      'src/api/trading.ts',
      'src/api/user.ts',
      'src/services/mock.service.ts'
    ]
    
    let validApis = 0
    
    apiFiles.forEach(file => {
      const filePath = path.join(this.projectRoot, file)
      if (fs.existsSync(filePath)) {
        const content = fs.readFileSync(filePath, 'utf8')
        
        // 检查是否有export
        if (content.includes('export')) {
          validApis++
          this.results.apis.details.push(`✅ ${file}`)
        } else {
          this.results.apis.details.push(`⚠️ ${file}: 可能为空文件`)
        }
      } else {
        this.results.apis.details.push(`❌ ${file}: 文件不存在`)
      }
    })
    
    if (validApis === apiFiles.length) {
      this.results.apis.status = 'good'
    } else if (validApis >= apiFiles.length * 0.7) {
      this.results.apis.status = 'warning'
    } else {
      this.results.apis.status = 'error'
    }
  }

  // 检查状态管理
  checkStores() {
    console.log('🔍 检查状态管理...')
    
    const storeFiles = [
      'src/stores/modules/market.ts',
      'src/stores/modules/trading.ts',
      'src/stores/modules/auth.ts',
      'src/stores/modules/user.ts'
    ]
    
    let validStores = 0
    
    storeFiles.forEach(file => {
      const filePath = path.join(this.projectRoot, file)
      if (fs.existsSync(filePath)) {
        const content = fs.readFileSync(filePath, 'utf8')
        
        // 检查是否是Pinia store
        if (content.includes('defineStore')) {
          validStores++
          this.results.stores.details.push(`✅ ${file}`)
        } else {
          this.results.stores.details.push(`⚠️ ${file}: 不是有效的Pinia store`)
        }
      } else {
        this.results.stores.details.push(`❌ ${file}: 文件不存在`)
      }
    })
    
    if (validStores === storeFiles.length) {
      this.results.stores.status = 'good'
    } else if (validStores >= storeFiles.length * 0.7) {
      this.results.stores.status = 'warning'
    } else {
      this.results.stores.status = 'error'
    }
  }

  // 检查类型定义
  checkTypes() {
    console.log('🔍 检查类型定义...')
    
    const typeFiles = [
      'src/types/market.ts',
      'src/types/trading.ts',
      'src/types/user.ts',
      'src/types/common.ts'
    ]
    
    let validTypes = 0
    
    typeFiles.forEach(file => {
      const filePath = path.join(this.projectRoot, file)
      if (fs.existsSync(filePath)) {
        const content = fs.readFileSync(filePath, 'utf8')
        
        // 检查是否有类型定义
        if (content.includes('interface') || content.includes('type')) {
          validTypes++
          this.results.types.details.push(`✅ ${file}`)
        } else {
          this.results.types.details.push(`⚠️ ${file}: 可能缺少类型定义`)
        }
      } else {
        this.results.types.details.push(`❌ ${file}: 文件不存在`)
      }
    })
    
    if (validTypes === typeFiles.length) {
      this.results.types.status = 'good'
    } else if (validTypes >= typeFiles.length * 0.7) {
      this.results.types.status = 'warning'
    } else {
      this.results.types.status = 'error'
    }
  }

  // 计算总体评分
  calculateOverallScore() {
    const weights = {
      dependencies: 0.2,
      configuration: 0.15,
      components: 0.25,
      apis: 0.2,
      stores: 0.15,
      types: 0.05
    }
    
    const statusScores = {
      good: 100,
      warning: 60,
      error: 20,
      unknown: 0
    }
    
    let totalScore = 0
    Object.keys(weights).forEach(category => {
      const status = this.results[category].status
      totalScore += statusScores[status] * weights[category]
    })
    
    this.results.overall.score = Math.round(totalScore)
    
    if (totalScore >= 85) {
      this.results.overall.status = 'excellent'
    } else if (totalScore >= 70) {
      this.results.overall.status = 'good'
    } else if (totalScore >= 50) {
      this.results.overall.status = 'fair'
    } else {
      this.results.overall.status = 'poor'
    }
  }

  // 生成报告
  generateReport() {
    console.log('\n' + '='.repeat(60))
    console.log('📊 前端项目状态报告')
    console.log('='.repeat(60))
    
    // 总体状态
    const statusEmojis = {
      excellent: '🌟',
      good: '✅',
      fair: '⚠️',
      poor: '❌'
    }
    
    console.log(`\n${statusEmojis[this.results.overall.status]} 总体评分: ${this.results.overall.score}/100 (${this.results.overall.status.toUpperCase()})`)
    
    // 详细结果
    Object.keys(this.results).forEach(category => {
      if (category === 'overall') return
      
      const result = this.results[category]
      const emoji = result.status === 'good' ? '✅' : result.status === 'warning' ? '⚠️' : '❌'
      
      console.log(`\n${emoji} ${category.toUpperCase()}:`)
      result.details.forEach(detail => {
        console.log(`  ${detail}`)
      })
    })
    
    // 建议
    console.log('\n📋 改进建议:')
    Object.keys(this.results).forEach(category => {
      if (category === 'overall') return
      
      const result = this.results[category]
      if (result.status === 'error') {
        console.log(`  🔧 ${category}: 需要立即修复`)
      } else if (result.status === 'warning') {
        console.log(`  🔨 ${category}: 建议优化`)
      }
    })
    
    console.log('\n' + '='.repeat(60))
  }

  // 运行所有检查
  async run() {
    console.log('🚀 开始检查前端项目状态...\n')
    
    this.checkDependencies()
    this.checkConfiguration()
    this.checkComponents()
    this.checkApis()
    this.checkStores()
    this.checkTypes()
    this.calculateOverallScore()
    this.generateReport()
  }
}

// 运行检查
const checker = new ProjectChecker()
checker.run().catch(console.error)