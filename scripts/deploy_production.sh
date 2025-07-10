#!/bin/bash

# =============================================================================
# CTP量化平台生产环境部署脚本
# =============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 默认配置
ENVIRONMENT=${ENVIRONMENT:-production}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-""}
IMAGE_TAG=${IMAGE_TAG:-latest}
NAMESPACE=${NAMESPACE:-quant-platform-prod}
REPLICAS=${REPLICAS:-3}

# 检查必要工具
check_dependencies() {
    log_info "检查部署依赖..."
    
    local deps=("docker" "kubectl" "helm")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "$dep 未安装或不在PATH中"
            exit 1
        fi
    done
    
    log_info "依赖检查完成"
}

# 验证环境配置
validate_config() {
    log_info "验证环境配置..."
    
    # 检查环境变量文件
    local env_file="$BACKEND_DIR/.env.$ENVIRONMENT"
    if [[ ! -f "$env_file" ]]; then
        log_error "环境配置文件不存在: $env_file"
        log_info "请复制 .env.production.template 并重命名为 .env.$ENVIRONMENT"
        exit 1
    fi
    
    # 检查必要的环境变量
    source "$env_file"
    
    local required_vars=(
        "CTP_DATABASE_URL"
        "CTP_REDIS_URL"
        "CTP_ENCRYPTION_KEY"
        "CTP_JWT_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            log_error "必要的环境变量未设置: $var"
            exit 1
        fi
    done
    
    log_info "环境配置验证完成"
}

# 构建Docker镜像
build_images() {
    log_info "构建Docker镜像..."
    
    # 构建后端镜像
    log_info "构建后端镜像..."
    cd "$BACKEND_DIR"
    docker build -t "quant-platform-backend:$IMAGE_TAG" .
    
    if [[ -n "$DOCKER_REGISTRY" ]]; then
        docker tag "quant-platform-backend:$IMAGE_TAG" "$DOCKER_REGISTRY/quant-platform-backend:$IMAGE_TAG"
        docker push "$DOCKER_REGISTRY/quant-platform-backend:$IMAGE_TAG"
    fi
    
    # 构建前端镜像
    log_info "构建前端镜像..."
    cd "$FRONTEND_DIR"
    docker build -t "quant-platform-frontend:$IMAGE_TAG" .
    
    if [[ -n "$DOCKER_REGISTRY" ]]; then
        docker tag "quant-platform-frontend:$IMAGE_TAG" "$DOCKER_REGISTRY/quant-platform-frontend:$IMAGE_TAG"
        docker push "$DOCKER_REGISTRY/quant-platform-frontend:$IMAGE_TAG"
    fi
    
    log_info "镜像构建完成"
}

# 数据库迁移
run_migrations() {
    log_info "执行数据库迁移..."
    
    cd "$BACKEND_DIR"
    
    # 检查数据库连接
    python -c "
import os
from sqlalchemy import create_engine
from app.core.ctp_production_config import CTPProductionSettings

settings = CTPProductionSettings()
engine = create_engine(settings.database_url)
try:
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print('数据库连接成功')
except Exception as e:
    print(f'数据库连接失败: {e}')
    exit(1)
"
    
    # 运行迁移
    alembic upgrade head
    
    log_info "数据库迁移完成"
}

# 部署到Kubernetes
deploy_k8s() {
    log_info "部署到Kubernetes..."
    
    # 创建命名空间
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # 创建ConfigMap
    kubectl create configmap ctp-config \
        --from-env-file="$BACKEND_DIR/.env.$ENVIRONMENT" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # 创建Secret
    kubectl create secret generic ctp-secrets \
        --from-literal=encryption-key="$CTP_ENCRYPTION_KEY" \
        --from-literal=jwt-secret="$CTP_JWT_SECRET_KEY" \
        --from-literal=database-url="$CTP_DATABASE_URL" \
        --from-literal=redis-url="$CTP_REDIS_URL" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml | kubectl apply -f -
    
    # 部署应用
    envsubst < "$PROJECT_ROOT/k8s/deployment.yaml" | kubectl apply -f -
    envsubst < "$PROJECT_ROOT/k8s/service.yaml" | kubectl apply -f -
    envsubst < "$PROJECT_ROOT/k8s/ingress.yaml" | kubectl apply -f -
    
    log_info "Kubernetes部署完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        log_debug "健康检查尝试 $attempt/$max_attempts"
        
        if kubectl get pods -n "$NAMESPACE" -l app=quant-platform-backend | grep -q "Running"; then
            log_info "后端服务健康检查通过"
            break
        fi
        
        if [[ $attempt -eq $max_attempts ]]; then
            log_error "健康检查失败"
            kubectl get pods -n "$NAMESPACE"
            kubectl logs -n "$NAMESPACE" -l app=quant-platform-backend --tail=50
            exit 1
        fi
        
        sleep 10
        ((attempt++))
    done
    
    log_info "健康检查完成"
}

# 备份当前部署
backup_deployment() {
    log_info "备份当前部署..."
    
    local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # 备份Kubernetes资源
    kubectl get all -n "$NAMESPACE" -o yaml > "$backup_dir/k8s_resources.yaml"
    kubectl get configmap -n "$NAMESPACE" -o yaml > "$backup_dir/configmaps.yaml"
    kubectl get secret -n "$NAMESPACE" -o yaml > "$backup_dir/secrets.yaml"
    
    # 备份数据库
    if command -v pg_dump &> /dev/null; then
        pg_dump "$CTP_DATABASE_URL" > "$backup_dir/database.sql"
    fi
    
    log_info "备份完成: $backup_dir"
}

# 回滚部署
rollback_deployment() {
    log_warn "执行部署回滚..."
    
    kubectl rollout undo deployment/quant-platform-backend -n "$NAMESPACE"
    kubectl rollout undo deployment/quant-platform-frontend -n "$NAMESPACE"
    
    log_info "回滚完成"
}

# 清理资源
cleanup() {
    log_info "清理临时资源..."
    
    # 清理未使用的Docker镜像
    docker image prune -f
    
    # 清理Kubernetes资源
    kubectl delete pods -n "$NAMESPACE" --field-selector=status.phase=Succeeded
    kubectl delete pods -n "$NAMESPACE" --field-selector=status.phase=Failed
    
    log_info "清理完成"
}

# 显示部署状态
show_status() {
    log_info "部署状态:"
    echo "----------------------------------------"
    kubectl get pods -n "$NAMESPACE"
    echo "----------------------------------------"
    kubectl get services -n "$NAMESPACE"
    echo "----------------------------------------"
    kubectl get ingress -n "$NAMESPACE"
    echo "----------------------------------------"
}

# 主函数
main() {
    log_info "开始CTP量化平台生产环境部署"
    log_info "环境: $ENVIRONMENT"
    log_info "命名空间: $NAMESPACE"
    log_info "镜像标签: $IMAGE_TAG"
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-migration)
                SKIP_MIGRATION=true
                shift
                ;;
            --rollback)
                rollback_deployment
                exit 0
                ;;
            --status)
                show_status
                exit 0
                ;;
            --cleanup)
                cleanup
                exit 0
                ;;
            --help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --skip-build      跳过镜像构建"
                echo "  --skip-migration  跳过数据库迁移"
                echo "  --rollback        回滚部署"
                echo "  --status          显示部署状态"
                echo "  --cleanup         清理资源"
                echo "  --help            显示帮助"
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 执行部署步骤
    check_dependencies
    validate_config
    
    if [[ "$SKIP_BUILD" != "true" ]]; then
        build_images
    fi
    
    backup_deployment
    
    if [[ "$SKIP_MIGRATION" != "true" ]]; then
        run_migrations
    fi
    
    deploy_k8s
    health_check
    show_status
    cleanup
    
    log_info "CTP量化平台部署完成!"
    log_info "访问地址: https://your-domain.com"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"
