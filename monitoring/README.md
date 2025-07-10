# CTP监控告警系统

## 概述

CTP监控告警系统为量化交易平台提供全面的监控和告警功能，包括：

- **实时指标收集**: 连接状态、交易性能、系统资源等
- **智能告警规则**: 基于阈值和条件的自动告警
- **多渠道通知**: 邮件、Webhook、钉钉等通知方式
- **可视化监控**: Prometheus + Grafana 监控仪表板
- **健康检查**: Kubernetes 就绪性和存活性检查

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CTP应用       │    │   监控收集器     │    │   告警管理器     │
│                 │───▶│                 │───▶│                 │
│ - 交易接口      │    │ - 指标收集      │    │ - 规则引擎      │
│ - 行情数据      │    │ - 健康检查      │    │ - 通知发送      │
│ - 风险管理      │    │ - Prometheus    │    │ - 告警管理      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Prometheus    │    │   通知渠道       │
                       │                 │    │                 │
                       │ - 指标存储      │    │ - 邮件          │
                       │ - 查询接口      │    │ - Webhook       │
                       │ - 告警规则      │    │ - 钉钉          │
                       └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Grafana       │
                       │                 │
                       │ - 可视化仪表板  │
                       │ - 告警面板      │
                       │ - 用户界面      │
                       └─────────────────┘
```

## 核心组件

### 1. 指标收集器 (CTPMetricsCollector)

负责收集和管理各类系统指标：

- **连接指标**: CTP连接状态、运行时间、重连次数
- **交易指标**: 订单数量、成功率、响应时间、交易量
- **行情指标**: 数据接收量、延迟、订阅数量
- **系统指标**: CPU使用率、内存使用量、错误计数

### 2. 告警管理器 (CTPAlertManager)

提供智能告警功能：

- **告警规则**: 基于条件的自动触发规则
- **告警去重**: 避免重复告警，支持告警聚合
- **通知渠道**: 多种通知方式，支持扩展
- **告警历史**: 完整的告警记录和状态管理

### 3. 通知渠道

支持多种通知方式：

- **邮件通知**: SMTP邮件发送，支持HTML模板
- **Webhook通知**: HTTP POST通知，支持自定义格式
- **钉钉通知**: 钉钉机器人消息，支持Markdown格式

## 配置说明

### 环境变量配置

```bash
# 监控配置
CTP_METRICS_ENABLED=true
CTP_METRICS_PORT=9090
CTP_HEALTH_CHECK_INTERVAL=30

# 告警配置
CTP_ALERT_ENABLED=true

# 邮件告警
ALERT_EMAIL_ENABLED=true
ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
ALERT_EMAIL_SMTP_PORT=587
ALERT_EMAIL_USERNAME=your_email@gmail.com
ALERT_EMAIL_PASSWORD=your_password
ALERT_EMAIL_FROM=alerts@your-domain.com
ALERT_EMAIL_TO=admin@your-domain.com

# Webhook告警
ALERT_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
ALERT_WEBHOOK_HEADERS={"Content-Type": "application/json"}

# 钉钉告警
ALERT_DINGTALK_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=TOKEN
ALERT_DINGTALK_SECRET=your_secret
```

### 告警规则配置

系统预置了以下告警规则：

1. **连接断开告警**: CTP连接断开时触发
2. **高错误率告警**: 订单错误率超过10%时触发
3. **内存使用告警**: 内存使用超过2GB时触发
4. **CPU使用告警**: CPU使用率超过80%时触发
5. **行情延迟告警**: 行情数据延迟超过5秒时触发

## API接口

### 指标接口

```http
GET /api/v1/monitoring/metrics          # 获取所有指标
GET /api/v1/monitoring/health           # 健康检查
GET /api/v1/monitoring/ready            # 就绪检查
GET /api/v1/monitoring/live             # 存活检查
```

### 告警接口

```http
GET /api/v1/monitoring/alerts           # 获取活跃告警
GET /api/v1/monitoring/alerts/history   # 获取告警历史
POST /api/v1/monitoring/alerts          # 创建手动告警
PUT /api/v1/monitoring/alerts/{id}/resolve  # 解决告警
```

### 控制接口

```http
POST /api/v1/monitoring/metrics/start   # 启动指标收集
POST /api/v1/monitoring/metrics/stop    # 停止指标收集
POST /api/v1/monitoring/alerts/start    # 启动告警监控
POST /api/v1/monitoring/alerts/stop     # 停止告警监控
GET /api/v1/monitoring/status           # 获取监控状态
```

## 部署指南

### 1. Docker Compose 部署

```bash
# 启动监控栈
docker-compose -f docker-compose.production.yml up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 2. Kubernetes 部署

```bash
# 应用配置
kubectl apply -f k8s/

# 检查部署状态
kubectl get pods -n quant-platform

# 查看服务
kubectl get svc -n quant-platform
```

### 3. 监控访问

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **应用监控**: http://localhost:8000/api/v1/monitoring/health

## 监控仪表板

### Grafana 仪表板

系统提供预配置的Grafana仪表板：

1. **CTP连接监控**: 连接状态、运行时间、重连统计
2. **交易性能监控**: 订单统计、成功率、响应时间
3. **行情数据监控**: 数据量、延迟、订阅状态
4. **系统资源监控**: CPU、内存、网络、磁盘
5. **告警面板**: 活跃告警、告警历史、通知状态

### 自定义仪表板

可以根据业务需求创建自定义仪表板：

```json
{
  "dashboard": {
    "title": "自定义CTP监控",
    "panels": [
      {
        "title": "订单成功率",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(ctp_orders_total{status=\"success\"}[5m]) / rate(ctp_orders_total[5m])"
          }
        ]
      }
    ]
  }
}
```

## 故障排查

### 常见问题

1. **指标收集不工作**
   - 检查环境变量配置
   - 确认监控服务已启动
   - 查看应用日志

2. **告警不发送**
   - 验证通知渠道配置
   - 检查网络连接
   - 确认告警规则条件

3. **Prometheus无法抓取指标**
   - 检查防火墙设置
   - 确认指标端口开放
   - 验证Prometheus配置

### 日志查看

```bash
# 应用日志
docker-compose logs -f backend

# Prometheus日志
docker-compose logs -f prometheus

# Grafana日志
docker-compose logs -f grafana
```

## 性能优化

### 指标收集优化

- 调整收集间隔: `CTP_HEALTH_CHECK_INTERVAL`
- 限制指标数量: 只收集必要指标
- 使用批量更新: 减少锁竞争

### 告警优化

- 设置合理的冷却时间
- 使用告警聚合减少噪音
- 优化告警规则条件

### 存储优化

- 配置Prometheus数据保留期
- 使用远程存储（如Cortex）
- 定期清理历史数据

## 扩展开发

### 自定义指标

```python
from app.monitoring import metrics_collector

# 记录自定义指标
await metrics_collector.record_custom_metric(
    name="custom_metric",
    value=100,
    labels={"type": "business"}
)
```

### 自定义告警规则

```python
from app.monitoring.ctp_alerts import AlertRule, AlertLevel

# 创建自定义规则
custom_rule = AlertRule(
    name="custom_alert",
    condition=lambda m: m.get("custom_value", 0) > 100,
    level=AlertLevel.WARNING,
    description="自定义告警规则"
)

alert_manager.add_rule(custom_rule)
```

### 自定义通知渠道

```python
from app.monitoring.ctp_alerts import NotificationChannel

class CustomNotification(NotificationChannel):
    async def send(self, alert):
        # 实现自定义通知逻辑
        pass

alert_manager.add_channel(CustomNotification())
```

## 安全考虑

- 使用HTTPS加密通信
- 限制监控接口访问权限
- 保护敏感配置信息
- 定期更新依赖组件
- 监控访问日志

## 维护指南

### 定期维护任务

1. **每日检查**
   - 监控系统状态
   - 查看告警情况
   - 检查磁盘空间

2. **每周维护**
   - 清理过期数据
   - 更新告警规则
   - 性能分析

3. **每月维护**
   - 系统更新
   - 配置优化
   - 容量规划
