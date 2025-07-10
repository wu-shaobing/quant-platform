# CTP安全加固文档

## 概述

本文档描述了CTP交易系统的安全加固措施，包括API安全增强、数据加密、系统安全和认证授权强化等方面。

## 安全架构

### 1. 多层安全防护

```
┌─────────────────────────────────────────────────────────────┐
│                    客户端请求                                │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 安全中间件层                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ CORS安全    │ │ 速率限制    │ │ IP白名单                │ │
│  │ 中间件      │ │ 中间件      │ │ 中间件                  │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  API安全层                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ JWT认证     │ │ 权限控制    │ │ 审计日志                │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  数据加密层                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ 传输加密    │ │ 存储加密    │ │ 敏感字段加密            │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  CTP交易层                                  │
└─────────────────────────────────────────────────────────────┘
```

## 安全组件详解

### 1. 安全中间件 (SecurityMiddleware)

#### 功能特性
- **速率限制**: 防止API滥用和DDoS攻击
- **IP白名单**: 限制访问来源
- **安全响应头**: 防止XSS、点击劫持等攻击
- **请求审计**: 记录所有API访问

#### 配置参数
```python
# 速率限制配置
MAX_REQUESTS_PER_MINUTE = 1000  # 每分钟最大请求数
MAX_REQUESTS_PER_HOUR = 10000   # 每小时最大请求数

# IP白名单配置
ALLOWED_IP_RANGES = [
    "127.0.0.0/8",      # 本地回环
    "192.168.0.0/16",   # 私有网络
    "10.0.0.0/8",       # 私有网络
    "172.16.0.0/12"     # 私有网络
]
```

#### 安全响应头
```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
```

### 2. 数据加密服务 (EncryptionService)

#### 加密算法
- **对称加密**: Fernet (AES 128 CBC + HMAC SHA256)
- **密钥派生**: PBKDF2 (100,000 iterations)
- **随机盐**: 32字节安全随机数

#### CTP敏感字段加密
```python
# 订单敏感字段
ORDER_SENSITIVE_FIELDS = [
    "password", "broker_id", "user_id", "investor_id",
    "auth_code", "app_id", "trading_day"
]

# 账户敏感字段  
ACCOUNT_SENSITIVE_FIELDS = [
    "password", "broker_id", "user_id", "investor_id",
    "auth_code", "front_address", "name_server"
]
```

#### 使用示例
```python
# 加密CTP订单数据
encrypted_order = encryption_service.encrypt_ctp_order({
    "user_id": "123456",
    "password": "secret",
    "broker_id": "9999",
    "instrument_id": "rb2405"
})

# 解密CTP订单数据
decrypted_order = encryption_service.decrypt_ctp_order(encrypted_order)
```

### 3. 登录安全跟踪 (LoginAttemptTracker)

#### 功能特性
- **失败尝试计数**: 记录每个用户的失败登录次数
- **账户锁定**: 超过阈值自动锁定账户
- **自动解锁**: 锁定期满自动解锁
- **IP跟踪**: 记录登录尝试的IP地址

#### 配置参数
```python
MAX_LOGIN_ATTEMPTS = 5          # 最大失败尝试次数
LOGIN_LOCKOUT_DURATION = 1800   # 锁定时长(秒)
```

### 4. 速率限制器 (RateLimiter)

#### 限制策略
- **按IP限制**: 每个IP独立计算
- **按端点限制**: 不同API端点独立限制
- **滑动窗口**: 使用滑动时间窗口算法

#### 限制级别
```python
# 全局限制
GLOBAL_RATE_LIMIT = {
    "requests_per_minute": 1000,
    "requests_per_hour": 10000
}

# 敏感端点限制
SENSITIVE_ENDPOINTS_LIMIT = {
    "/api/v1/auth/login": {"requests_per_minute": 10},
    "/api/v1/ctp/order": {"requests_per_minute": 100},
    "/api/v1/ctp/connect": {"requests_per_minute": 5}
}
```

## 安全API端点

### 1. 安全统计
```http
GET /api/v1/security/stats
Authorization: Bearer <token>
```

### 2. 速率限制状态
```http
GET /api/v1/security/rate-limit/status
Authorization: Bearer <token>
```

### 3. IP白名单管理
```http
POST /api/v1/security/ip-whitelist/check
POST /api/v1/security/ip-whitelist/update
Authorization: Bearer <token>
```

### 4. 账户解锁
```http
POST /api/v1/security/unlock-account/{username}
Authorization: Bearer <token>
```

### 5. 数据加密/解密
```http
POST /api/v1/security/encrypt
POST /api/v1/security/decrypt
Authorization: Bearer <token>
```

## 部署配置

### 1. 环境变量
```bash
# 安全配置
SECRET_KEY=your-production-secret-key
ENCRYPTION_MASTER_KEY=your-encryption-master-key
ENABLE_IP_WHITELIST=true
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com

# 数据库加密
DATABASE_ENCRYPTION_KEY=your-database-encryption-key
```

### 2. 生产环境配置
```python
# settings.py
class ProductionSettings(Settings):
    ENVIRONMENT = "production"
    DEBUG = False
    ENABLE_IP_WHITELIST = True
    
    # 更严格的速率限制
    MAX_REQUESTS_PER_MINUTE = 500
    MAX_REQUESTS_PER_HOUR = 5000
    
    # 更短的会话超时
    SESSION_TIMEOUT = 1800  # 30分钟
    
    # 启用所有安全功能
    ENABLE_SECURITY_HEADERS = True
    ENABLE_AUDIT_LOGGING = True
```

## 安全监控

### 1. 安全事件监控
- 异常登录尝试
- 速率限制触发
- IP白名单违规
- 权限提升尝试
- 数据访问异常

### 2. 告警配置
```python
# 告警阈值
SECURITY_ALERT_THRESHOLDS = {
    "failed_login_rate": 10,        # 每分钟失败登录次数
    "rate_limit_violations": 5,     # 速率限制违规次数
    "ip_whitelist_violations": 1,   # IP白名单违规次数
    "permission_denials": 10        # 权限拒绝次数
}
```

### 3. 日志格式
```json
{
    "timestamp": "2024-01-01T12:00:00Z",
    "event_type": "SECURITY_VIOLATION",
    "severity": "HIGH",
    "client_ip": "192.168.1.100",
    "user_id": "user123",
    "endpoint": "/api/v1/ctp/order",
    "details": {
        "violation_type": "rate_limit_exceeded",
        "current_rate": 150,
        "limit": 100
    }
}
```

## 安全测试

### 1. 渗透测试
- SQL注入测试
- XSS攻击测试
- CSRF攻击测试
- 权限绕过测试
- 会话劫持测试

### 2. 性能测试
- 加密/解密性能
- 速率限制性能
- 中间件开销测试

### 3. 压力测试
- 高并发访问测试
- DDoS攻击模拟
- 资源耗尽测试

## 安全最佳实践

### 1. 密钥管理
- 使用环境变量存储密钥
- 定期轮换加密密钥
- 使用硬件安全模块(HSM)
- 密钥分离和备份

### 2. 网络安全
- 使用HTTPS/TLS 1.3
- 配置防火墙规则
- 启用DDoS防护
- 网络隔离和VPN

### 3. 应用安全
- 输入验证和清理
- 输出编码和转义
- 安全的会话管理
- 定期安全审计

### 4. 数据安全
- 敏感数据加密存储
- 数据传输加密
- 数据备份加密
- 数据销毁策略

## 合规要求

### 1. 金融行业标准
- PCI DSS合规
- SOX合规
- 银监会监管要求
- 证监会监管要求

### 2. 数据保护法规
- GDPR合规
- 网络安全法合规
- 个人信息保护法合规

## 应急响应

### 1. 安全事件响应流程
1. 事件检测和确认
2. 影响评估和分类
3. 应急响应和处置
4. 恢复和验证
5. 事后分析和改进

### 2. 安全事件类型
- 数据泄露
- 系统入侵
- 服务中断
- 权限滥用
- 恶意软件感染

### 3. 联系方式
- 安全团队: security@company.com
- 应急热线: +86-xxx-xxxx-xxxx
- 监管报告: compliance@company.com
