#!/bin/bash

# 前端开发环境设置脚本

echo "🚀 正在设置前端开发环境..."

# 检查Node.js版本
NODE_VERSION=$(node -v)
echo "📦 Node.js版本: $NODE_VERSION"

if [[ ! "$NODE_VERSION" =~ ^v(18|20|21) ]]; then
    echo "❌ 需要Node.js 18+版本"
    exit 1
fi

# 检查包管理器
if command -v pnpm &> /dev/null; then
    PACKAGE_MANAGER="pnpm"
    echo "📦 使用包管理器: pnpm"
elif command -v yarn &> /dev/null; then
    PACKAGE_MANAGER="yarn"
    echo "📦 使用包管理器: yarn"
else
    PACKAGE_MANAGER="npm"
    echo "📦 使用包管理器: npm"
fi

# 安装依赖
echo "📥 正在安装依赖..."
$PACKAGE_MANAGER install

# 检查环境配置文件
if [ ! -f ".env.development" ]; then
    echo "⚠️  .env.development 文件不存在，正在创建..."
    cp .env.example .env.development 2>/dev/null || echo "VITE_USE_MOCK=true" > .env.development
fi

# 运行类型检查
echo "🔍 正在运行类型检查..."
$PACKAGE_MANAGER run type-check

# 运行代码检查
echo "🧹 正在运行代码检查..."
$PACKAGE_MANAGER run lint

echo "✅ 前端开发环境设置完成！"
echo ""
echo "🎯 可用命令："
echo "  $PACKAGE_MANAGER run dev      - 启动开发服务器"
echo "  $PACKAGE_MANAGER run build    - 构建生产版本"
echo "  $PACKAGE_MANAGER run test     - 运行测试"
echo "  $PACKAGE_MANAGER run preview  - 预览构建结果"
echo ""
echo "🔧 开发配置："
echo "  - Mock数据: 已启用"
echo "  - 热重载: 已启用"
echo "  - TypeScript: 已启用"
echo "  - ESLint: 已启用"
echo ""
echo "🌟 现在可以运行 '$PACKAGE_MANAGER run dev' 启动开发服务器"