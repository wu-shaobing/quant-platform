# 量化投资前端可视化平台

一个现代化的量化投资前端可视化平台，基于 Vue 3 + TypeScript + Vite 构建。

## 🚀 功能特性

- **现代化技术栈**: Vue 3, TypeScript, Vite, Pinia
- **组件化设计**: Element Plus + 自定义组件
- **实时数据**: WebSocket 实时行情推送
- **图表可视化**: ECharts 专业金融图表
- **响应式布局**: 支持多设备适配
- **类型安全**: 完整的 TypeScript 类型定义
- **测试覆盖**: Vitest 单元测试
- **代码质量**: ESLint + Prettier 代码规范

## 📦 核心模块

### 🏪 市场模块
- 实时行情展示
- K线图表分析
- 深度图可视化
- 市场资讯推送

### 📈 交易模块
- 订单管理系统
- 持仓管理
- 快速交易面板
- 风险控制

### 🎯 策略模块
- 策略开发环境
- 策略回测系统
- 策略市场
- 策略监控

### 📊 投资组合
- 组合管理
- 绩效分析
- 资产配置
- 风险评估

### ⚠️ 风险管理
- 实时风险监控
- VaR 计算
- 压力测试
- 风险预警

## 🛠️ 技术栈

- **框架**: Vue 3.5+ (Composition API)
- **语言**: TypeScript 5.8+
- **构建工具**: Vite 6.2+
- **状态管理**: Pinia 2.1+
- **路由**: Vue Router 4.5+
- **UI 组件**: Element Plus 2.10+
- **图表库**: ECharts 5.6+
- **样式**: Tailwind CSS 3.4+
- **HTTP 客户端**: Axios 1.9+
- **WebSocket**: Socket.io-client 4.8+
- **工具函数**: VueUse 11.2+
- **数值计算**: Decimal.js, Big.js
- **测试框架**: Vitest 3.2+
- **代码规范**: ESLint 9+ + Prettier 3.5+

## 📁 项目结构

```
src/
├── api/                 # API 接口定义
├── assets/             # 静态资源
├── components/         # 通用组件
│   ├── charts/        # 图表组件
│   ├── common/        # 公共组件
│   ├── trading/       # 交易组件
│   └── ...
├── composables/        # 组合式函数
│   ├── core/          # 核心功能
│   ├── trading/       # 交易相关
│   └── ...
├── layouts/           # 布局组件
├── plugins/           # 插件配置
├── router/            # 路由配置
├── services/          # 业务服务
├── stores/            # 状态管理
├── types/             # 类型定义
├── utils/             # 工具函数
├── views/             # 页面组件
└── workers/           # Web Workers
```

## 🚀 快速开始

### 环境要求

- Node.js 18.0+
- npm 8.0+ 或 yarn 1.22+

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

### 构建生产版本

```bash
npm run build:prod
```

### 预览构建结果

```bash
npm run preview
```

## 🧪 测试

### 运行单元测试

```bash
npm run test
```

### 运行测试并生成覆盖率报告

```bash
npm run test:coverage
```

### 测试 UI 界面

```bash
npm run test:ui
```

## 📝 代码规范

### 代码检查

```bash
npm run lint
```

### 代码格式化

```bash
npm run format
```

### 类型检查

```bash
npm run type-check
```

## 🔧 配置说明

### 环境变量

创建 `.env.local` 文件配置本地环境变量：

```env
# API 配置
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_BASE_URL=ws://localhost:8000/ws

# 功能开关
VITE_ENABLE_MOCK=true
VITE_ENABLE_DEBUG=true
```

### Vite 配置

主要配置在 `vite.config.ts` 中：
- 路径别名配置
- 代理配置
- 构建优化
- 插件配置

### TypeScript 配置

- `tsconfig.json`: 项目根配置
- `tsconfig.app.json`: 应用配置
- `tsconfig.node.json`: Node.js 配置

## 📱 兼容性

- **浏览器**: Chrome 90+, Firefox 90+, Safari 14+, Edge 90+
- **移动端**: iOS Safari 14+, Chrome Mobile 90+
- **Node.js**: 18.0+

## 🤝 开发规范

### Git 提交规范

```bash
feat: 新功能
fix: 修复问题
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建配置等
```

### 组件开发规范

1. 使用 Composition API
2. 统一的类型定义
3. 完善的 Props 验证
4. 合理的事件命名
5. 响应式设计

### 状态管理规范

1. 按功能模块划分 Store
2. 使用 Pinia 组合式语法
3. 合理的持久化配置
4. 统一的错误处理

## 📈 性能优化

- **代码分割**: 路由级别的懒加载
- **资源优化**: 图片压缩、字体优化
- **缓存策略**: HTTP 缓存、本地存储
- **包体积**: Tree-shaking、压缩优化
- **运行时**: 虚拟滚动、防抖节流

## 🔒 安全考虑

- **XSS 防护**: 内容转义、CSP 配置
- **CSRF 防护**: Token 验证
- **权限控制**: 路由守卫、组件权限
- **数据加密**: 敏感信息加密存储

## 📚 相关文档

- [Vue 3 官方文档](https://vuejs.org/)
- [TypeScript 官方文档](https://www.typescriptlang.org/)
- [Vite 官方文档](https://vitejs.dev/)
- [Element Plus 官方文档](https://element-plus.org/)
- [ECharts 官方文档](https://echarts.apache.org/)

## 📄 许可证

MIT License

## 👥 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 🐛 问题反馈

如果发现问题或有改进建议，请创建 [Issue](../../issues)。
