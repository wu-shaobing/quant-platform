# 多阶段构建 - 基础镜像
FROM node:18-alpine as base

# 设置环境变量
ENV NODE_ENV=production \
    PNPM_HOME="/pnpm" \
    PATH="$PNPM_HOME:$PATH"

# 安装pnpm
RUN corepack enable && corepack prepare pnpm@8.10.0 --activate

# 创建非root用户
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

WORKDIR /app

# 开发阶段
FROM base as development

ENV NODE_ENV=development

# 复制package文件
COPY package.json pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install --frozen-lockfile

# 复制源代码
COPY . .

# 设置权限
RUN chown -R nextjs:nodejs /app
USER nextjs

EXPOSE 3000

CMD ["pnpm", "dev", "--host", "0.0.0.0"]

# 测试阶段
FROM development as test

# 运行测试
RUN pnpm test:unit --run
RUN pnpm lint
RUN pnpm type-check

# 构建阶段
FROM base as builder

# 复制package文件
COPY package.json pnpm-lock.yaml ./

# 安装依赖
RUN pnpm install --frozen-lockfile --prod=false

# 复制源代码
COPY . .

# 构建应用
RUN pnpm build

# 生产阶段
FROM nginx:1.25-alpine as production

# 安装curl用于健康检查
RUN apk add --no-cache curl

# 创建nginx用户目录
RUN mkdir -p /var/cache/nginx /var/run /var/log/nginx \
    && chown -R nginx:nginx /var/cache/nginx /var/run /var/log/nginx

# 复制构建产物
COPY --from=builder --chown=nginx:nginx /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/nginx.conf

# 创建非特权端口配置
RUN sed -i 's/listen 80;/listen 8080;/' /etc/nginx/conf.d/default.conf || true

# 切换到非root用户
USER nginx

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:80/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
