"""
CTP告警系统
"""
import asyncio
import json
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import aiohttp
import requests
from jinja2 import Template

from app.core.config import settings

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """告警状态"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class Alert:
    """告警数据类"""
    id: str
    title: str
    description: str
    level: AlertLevel
    status: AlertStatus = AlertStatus.ACTIVE
    source: str = "ctp"
    category: str = "system"
    tags: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    count: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "level": self.level.value,
            "status": self.status.value,
            "source": self.source,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "count": self.count
        }


class AlertRule:
    """告警规则"""
    
    def __init__(self, name: str, condition: Callable, level: AlertLevel, 
                 description: str, category: str = "system", 
                 cooldown: int = 300, max_count: int = 10):
        self.name = name
        self.condition = condition
        self.level = level
        self.description = description
        self.category = category
        self.cooldown = cooldown  # 冷却时间（秒）
        self.max_count = max_count  # 最大重复次数
        self.last_triggered = None
        self.trigger_count = 0
    
    def should_trigger(self, metrics: Dict[str, Any]) -> bool:
        """检查是否应该触发告警"""
        try:
            # 检查冷却时间
            if self.last_triggered:
                time_since_last = (datetime.now() - self.last_triggered).total_seconds()
                if time_since_last < self.cooldown:
                    return False
            
            # 检查触发条件
            if self.condition(metrics):
                self.last_triggered = datetime.now()
                self.trigger_count += 1
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error evaluating alert rule {self.name}: {e}")
            return False
    
    def reset(self):
        """重置规则状态"""
        self.last_triggered = None
        self.trigger_count = 0


class NotificationChannel:
    """通知渠道基类"""
    
    async def send(self, alert: Alert) -> bool:
        """发送通知"""
        raise NotImplementedError


class EmailNotification(NotificationChannel):
    """邮件通知"""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, 
                 password: str, from_email: str, to_emails: List[str]):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
        
        # 邮件模板
        self.template = Template("""
        <html>
        <body>
            <h2>CTP系统告警</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><strong>告警标题</strong></td><td>{{ alert.title }}</td></tr>
                <tr><td><strong>告警级别</strong></td><td>{{ alert.level.value.upper() }}</td></tr>
                <tr><td><strong>告警描述</strong></td><td>{{ alert.description }}</td></tr>
                <tr><td><strong>告警来源</strong></td><td>{{ alert.source }}</td></tr>
                <tr><td><strong>告警分类</strong></td><td>{{ alert.category }}</td></tr>
                <tr><td><strong>发生时间</strong></td><td>{{ alert.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</td></tr>
                <tr><td><strong>重复次数</strong></td><td>{{ alert.count }}</td></tr>
            </table>
            
            {% if alert.tags %}
            <h3>标签信息</h3>
            <ul>
            {% for key, value in alert.tags.items() %}
                <li><strong>{{ key }}</strong>: {{ value }}</li>
            {% endfor %}
            </ul>
            {% endif %}
            
            <p><em>此邮件由CTP量化交易平台自动发送</em></p>
        </body>
        </html>
        """)
    
    async def send(self, alert: Alert) -> bool:
        """发送邮件通知"""
        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert.level.value.upper()}] {alert.title}"
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            
            # 渲染HTML内容
            html_content = self.template.render(alert=alert)
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Email alert sent: {alert.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False


class WebhookNotification(NotificationChannel):
    """Webhook通知"""
    
    def __init__(self, webhook_url: str, headers: Dict[str, str] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}
    
    async def send(self, alert: Alert) -> bool:
        """发送Webhook通知"""
        try:
            payload = {
                "alert": alert.to_dict(),
                "timestamp": datetime.now().isoformat(),
                "source": "ctp-platform"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"Webhook alert sent: {alert.title}")
                        return True
                    else:
                        logger.error(f"Webhook failed with status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False


class DingTalkNotification(NotificationChannel):
    """钉钉通知"""
    
    def __init__(self, webhook_url: str, secret: str = None):
        self.webhook_url = webhook_url
        self.secret = secret
    
    async def send(self, alert: Alert) -> bool:
        """发送钉钉通知"""
        try:
            # 构建消息内容
            level_emoji = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🚨"
            }
            
            emoji = level_emoji.get(alert.level, "📢")
            
            text = f"""
{emoji} **CTP系统告警**

**告警标题**: {alert.title}
**告警级别**: {alert.level.value.upper()}
**告警描述**: {alert.description}
**发生时间**: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
**重复次数**: {alert.count}

---
*CTP量化交易平台*
            """.strip()
            
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"CTP告警: {alert.title}",
                    "text": text
                }
            }
            
            # 如果有密钥，添加签名
            if self.secret:
                import time
                import hmac
                import hashlib
                import base64
                import urllib.parse
                
                timestamp = str(round(time.time() * 1000))
                secret_enc = self.secret.encode('utf-8')
                string_to_sign = f'{timestamp}\n{self.secret}'
                string_to_sign_enc = string_to_sign.encode('utf-8')
                hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                
                webhook_url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
            else:
                webhook_url = self.webhook_url
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        logger.info(f"DingTalk alert sent: {alert.title}")
                        return True
                    else:
                        logger.error(f"DingTalk failed with status {response.status}")
                        return False
                        
        except Exception as e:
            logger.error(f"Failed to send DingTalk alert: {e}")
            return False


class CTPAlertManager:
    """CTP告警管理器"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.rules: List[AlertRule] = []
        self.channels: List[NotificationChannel] = []
        self.running = False
        self._check_task = None
        self.check_interval = 60  # 检查间隔（秒）
        
        # 初始化默认告警规则
        self._init_default_rules()
        
        # 初始化通知渠道
        self._init_notification_channels()
    
    def _init_default_rules(self):
        """初始化默认告警规则"""
        
        # 连接断开告警
        self.add_rule(AlertRule(
            name="connection_lost",
            condition=lambda m: not all(m.get("connection_status", {}).values()),
            level=AlertLevel.CRITICAL,
            description="CTP连接断开",
            category="connection",
            cooldown=60
        ))
        
        # 高错误率告警
        self.add_rule(AlertRule(
            name="high_error_rate",
            condition=lambda m: m.get("order_stats", {}).get("error_rate", 0) > 0.1,
            level=AlertLevel.ERROR,
            description="订单错误率过高（>10%）",
            category="trading",
            cooldown=300
        ))
        
        # 内存使用过高告警
        self.add_rule(AlertRule(
            name="high_memory_usage",
            condition=lambda m: m.get("system", {}).get("memory_usage", 0) > 2 * 1024 * 1024 * 1024,  # 2GB
            level=AlertLevel.WARNING,
            description="内存使用过高（>2GB）",
            category="system",
            cooldown=600
        ))
        
        # CPU使用过高告警
        self.add_rule(AlertRule(
            name="high_cpu_usage",
            condition=lambda m: m.get("system", {}).get("cpu_usage", 0) > 80,
            level=AlertLevel.WARNING,
            description="CPU使用率过高（>80%）",
            category="system",
            cooldown=600
        ))
        
        # 行情延迟过高告警
        self.add_rule(AlertRule(
            name="high_market_data_delay",
            condition=lambda m: m.get("market_data", {}).get("delay", 0) > 5.0,
            level=AlertLevel.WARNING,
            description="行情数据延迟过高（>5秒）",
            category="market_data",
            cooldown=300
        ))
    
    def _init_notification_channels(self):
        """初始化通知渠道"""
        try:
            # 邮件通知
            if hasattr(settings, 'ALERT_EMAIL_ENABLED') and settings.ALERT_EMAIL_ENABLED:
                email_channel = EmailNotification(
                    smtp_host=settings.ALERT_EMAIL_SMTP_HOST,
                    smtp_port=settings.ALERT_EMAIL_SMTP_PORT,
                    username=settings.ALERT_EMAIL_USERNAME,
                    password=settings.ALERT_EMAIL_PASSWORD,
                    from_email=settings.ALERT_EMAIL_FROM,
                    to_emails=settings.ALERT_EMAIL_TO.split(',')
                )
                self.add_channel(email_channel)
            
            # Webhook通知
            if hasattr(settings, 'ALERT_WEBHOOK_URL') and settings.ALERT_WEBHOOK_URL:
                webhook_channel = WebhookNotification(
                    webhook_url=settings.ALERT_WEBHOOK_URL,
                    headers=getattr(settings, 'ALERT_WEBHOOK_HEADERS', {})
                )
                self.add_channel(webhook_channel)
            
            # 钉钉通知
            if hasattr(settings, 'ALERT_DINGTALK_WEBHOOK') and settings.ALERT_DINGTALK_WEBHOOK:
                dingtalk_channel = DingTalkNotification(
                    webhook_url=settings.ALERT_DINGTALK_WEBHOOK,
                    secret=getattr(settings, 'ALERT_DINGTALK_SECRET', None)
                )
                self.add_channel(dingtalk_channel)
                
        except Exception as e:
            logger.error(f"Failed to initialize notification channels: {e}")
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def add_channel(self, channel: NotificationChannel):
        """添加通知渠道"""
        self.channels.append(channel)
        logger.info(f"Added notification channel: {type(channel).__name__}")
    
    async def start_monitoring(self):
        """开始监控"""
        if self.running:
            return
        
        self.running = True
        self._check_task = asyncio.create_task(self._monitoring_loop())
        logger.info("CTP alert monitoring started")
    
    async def stop_monitoring(self):
        """停止监控"""
        self.running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass
        logger.info("CTP alert monitoring stopped")
    
    async def _monitoring_loop(self):
        """监控循环"""
        from .ctp_metrics import metrics_collector
        
        while self.running:
            try:
                # 获取当前指标
                metrics = await metrics_collector.get_metrics_summary()
                
                # 检查所有规则
                for rule in self.rules:
                    if rule.should_trigger(metrics):
                        await self._trigger_alert(rule, metrics)
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alert monitoring loop: {e}")
                await asyncio.sleep(10)
    
    async def _trigger_alert(self, rule: AlertRule, metrics: Dict[str, Any]):
        """触发告警"""
        alert_id = f"{rule.name}_{int(datetime.now().timestamp())}"
        
        # 检查是否已存在相同的活跃告警
        existing_alert = None
        for alert in self.alerts.values():
            if (alert.title == rule.name and 
                alert.status == AlertStatus.ACTIVE and
                alert.category == rule.category):
                existing_alert = alert
                break
        
        if existing_alert:
            # 更新现有告警
            existing_alert.count += 1
            existing_alert.updated_at = datetime.now()
            alert = existing_alert
        else:
            # 创建新告警
            alert = Alert(
                id=alert_id,
                title=rule.name,
                description=rule.description,
                level=rule.level,
                category=rule.category,
                tags={
                    "trigger_count": str(rule.trigger_count),
                    "metrics": json.dumps(metrics, default=str)
                }
            )
            self.alerts[alert_id] = alert
        
        # 发送通知
        await self._send_notifications(alert)
        
        logger.warning(f"Alert triggered: {alert.title} (count: {alert.count})")
    
    async def _send_notifications(self, alert: Alert):
        """发送通知"""
        for channel in self.channels:
            try:
                await channel.send(alert)
            except Exception as e:
                logger.error(f"Failed to send notification via {type(channel).__name__}: {e}")
    
    async def resolve_alert(self, alert_id: str):
        """解决告警"""
        if alert_id in self.alerts:
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            alert.updated_at = datetime.now()
            
            logger.info(f"Alert resolved: {alert.title}")
    
    async def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        return [
            alert.to_dict() 
            for alert in self.alerts.values() 
            if alert.status == AlertStatus.ACTIVE
        ]
    
    async def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取告警历史"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert.to_dict()
            for alert in self.alerts.values()
            if alert.created_at >= cutoff_time
        ]


# 全局告警管理器实例
alert_manager = CTPAlertManager()
