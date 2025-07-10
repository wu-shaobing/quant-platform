"""
CTP告警系统测试
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from app.monitoring.ctp_alerts import (
    CTPAlertManager, Alert, AlertRule, AlertLevel, AlertStatus,
    EmailNotification, WebhookNotification, DingTalkNotification
)


class TestAlert:
    """告警数据类测试"""
    
    def test_alert_creation(self):
        """测试告警创建"""
        alert = Alert(
            id="test-alert-1",
            title="测试告警",
            description="这是一个测试告警",
            level=AlertLevel.WARNING,
            category="test"
        )
        
        assert alert.id == "test-alert-1"
        assert alert.title == "测试告警"
        assert alert.level == AlertLevel.WARNING
        assert alert.status == AlertStatus.ACTIVE
        assert alert.count == 1
    
    def test_alert_to_dict(self):
        """测试告警转字典"""
        alert = Alert(
            id="test-alert-1",
            title="测试告警",
            description="这是一个测试告警",
            level=AlertLevel.ERROR,
            tags={"broker": "CITIC", "type": "connection"}
        )
        
        alert_dict = alert.to_dict()
        
        assert alert_dict["id"] == "test-alert-1"
        assert alert_dict["title"] == "测试告警"
        assert alert_dict["level"] == "error"
        assert alert_dict["status"] == "active"
        assert alert_dict["tags"]["broker"] == "CITIC"


class TestAlertRule:
    """告警规则测试"""
    
    def test_rule_creation(self):
        """测试规则创建"""
        rule = AlertRule(
            name="high_error_rate",
            condition=lambda m: m.get("error_rate", 0) > 0.1,
            level=AlertLevel.ERROR,
            description="错误率过高",
            cooldown=300
        )
        
        assert rule.name == "high_error_rate"
        assert rule.level == AlertLevel.ERROR
        assert rule.cooldown == 300
        assert rule.trigger_count == 0
    
    def test_rule_should_trigger_true(self):
        """测试规则应该触发"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get("value", 0) > 10,
            level=AlertLevel.WARNING,
            description="测试规则"
        )
        
        metrics = {"value": 15}
        assert rule.should_trigger(metrics) is True
        assert rule.trigger_count == 1
    
    def test_rule_should_trigger_false(self):
        """测试规则不应该触发"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get("value", 0) > 10,
            level=AlertLevel.WARNING,
            description="测试规则"
        )
        
        metrics = {"value": 5}
        assert rule.should_trigger(metrics) is False
        assert rule.trigger_count == 0
    
    def test_rule_cooldown(self):
        """测试规则冷却时间"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: True,  # 总是触发
            level=AlertLevel.WARNING,
            description="测试规则",
            cooldown=1  # 1秒冷却
        )
        
        metrics = {}
        
        # 第一次应该触发
        assert rule.should_trigger(metrics) is True
        
        # 立即再次检查，应该不触发（冷却中）
        assert rule.should_trigger(metrics) is False
    
    def test_rule_reset(self):
        """测试规则重置"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: True,
            level=AlertLevel.WARNING,
            description="测试规则"
        )
        
        # 触发规则
        rule.should_trigger({})
        assert rule.trigger_count == 1
        assert rule.last_triggered is not None
        
        # 重置规则
        rule.reset()
        assert rule.trigger_count == 0
        assert rule.last_triggered is None


class TestEmailNotification:
    """邮件通知测试"""
    
    @pytest.fixture
    def email_notification(self):
        """创建邮件通知实例"""
        return EmailNotification(
            smtp_host="smtp.test.com",
            smtp_port=587,
            username="test@test.com",
            password="password",
            from_email="alerts@test.com",
            to_emails=["admin@test.com"]
        )
    
    @pytest.fixture
    def sample_alert(self):
        """示例告警"""
        return Alert(
            id="test-alert",
            title="测试告警",
            description="这是一个测试告警",
            level=AlertLevel.ERROR,
            tags={"broker": "CITIC"}
        )
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, email_notification, sample_alert):
        """测试发送邮件成功"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            result = await email_notification.send(sample_alert)
            
            assert result is True
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once()
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_failure(self, email_notification, sample_alert):
        """测试发送邮件失败"""
        with patch('smtplib.SMTP', side_effect=Exception("SMTP Error")):
            result = await email_notification.send(sample_alert)
            assert result is False


class TestWebhookNotification:
    """Webhook通知测试"""
    
    @pytest.fixture
    def webhook_notification(self):
        """创建Webhook通知实例"""
        return WebhookNotification(
            webhook_url="https://hooks.test.com/webhook",
            headers={"Content-Type": "application/json"}
        )
    
    @pytest.fixture
    def sample_alert(self):
        """示例告警"""
        return Alert(
            id="test-alert",
            title="测试告警",
            description="这是一个测试告警",
            level=AlertLevel.WARNING
        )
    
    @pytest.mark.asyncio
    async def test_send_webhook_success(self, webhook_notification, sample_alert):
        """测试发送Webhook成功"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            result = await webhook_notification.send(sample_alert)
            assert result is True
    
    @pytest.mark.asyncio
    async def test_send_webhook_failure(self, webhook_notification, sample_alert):
        """测试发送Webhook失败"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            result = await webhook_notification.send(sample_alert)
            assert result is False


class TestDingTalkNotification:
    """钉钉通知测试"""
    
    @pytest.fixture
    def dingtalk_notification(self):
        """创建钉钉通知实例"""
        return DingTalkNotification(
            webhook_url="https://oapi.dingtalk.com/robot/send?access_token=test",
            secret="test_secret"
        )
    
    @pytest.fixture
    def sample_alert(self):
        """示例告警"""
        return Alert(
            id="test-alert",
            title="测试告警",
            description="这是一个测试告警",
            level=AlertLevel.CRITICAL
        )
    
    @pytest.mark.asyncio
    async def test_send_dingtalk_success(self, dingtalk_notification, sample_alert):
        """测试发送钉钉通知成功"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            result = await dingtalk_notification.send(sample_alert)
            assert result is True


class TestCTPAlertManager:
    """CTP告警管理器测试"""
    
    @pytest.fixture
    def alert_manager(self):
        """创建告警管理器实例"""
        manager = CTPAlertManager()
        # 清空默认规则和通道，避免干扰测试
        manager.rules.clear()
        manager.channels.clear()
        return manager
    
    def test_add_rule(self, alert_manager):
        """测试添加规则"""
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: True,
            level=AlertLevel.INFO,
            description="测试规则"
        )
        
        alert_manager.add_rule(rule)
        assert len(alert_manager.rules) == 1
        assert alert_manager.rules[0] == rule
    
    def test_add_channel(self, alert_manager):
        """测试添加通知渠道"""
        channel = WebhookNotification("https://test.com/webhook")
        
        alert_manager.add_channel(channel)
        assert len(alert_manager.channels) == 1
        assert alert_manager.channels[0] == channel
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, alert_manager):
        """测试启动和停止监控"""
        # 启动监控
        await alert_manager.start_monitoring()
        assert alert_manager.running is True
        
        # 等待一小段时间
        await asyncio.sleep(0.1)
        
        # 停止监控
        await alert_manager.stop_monitoring()
        assert alert_manager.running is False
    
    @pytest.mark.asyncio
    async def test_trigger_alert_new(self, alert_manager):
        """测试触发新告警"""
        # 添加测试规则
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: m.get("trigger", False),
            level=AlertLevel.WARNING,
            description="测试规则"
        )
        alert_manager.add_rule(rule)
        
        # 添加模拟通知渠道
        mock_channel = AsyncMock()
        mock_channel.send.return_value = True
        alert_manager.add_channel(mock_channel)
        
        # 触发告警
        metrics = {"trigger": True}
        await alert_manager._trigger_alert(rule, metrics)
        
        # 验证告警被创建
        assert len(alert_manager.alerts) == 1
        alert = list(alert_manager.alerts.values())[0]
        assert alert.title == "test_rule"
        assert alert.level == AlertLevel.WARNING
        assert alert.count == 1
        
        # 验证通知被发送
        mock_channel.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_trigger_alert_existing(self, alert_manager):
        """测试触发现有告警"""
        # 创建现有告警
        existing_alert = Alert(
            id="existing-alert",
            title="test_rule",
            description="测试规则",
            level=AlertLevel.WARNING,
            category="system"
        )
        alert_manager.alerts["existing-alert"] = existing_alert
        
        # 添加测试规则
        rule = AlertRule(
            name="test_rule",
            condition=lambda m: True,
            level=AlertLevel.WARNING,
            description="测试规则"
        )
        
        # 触发告警
        await alert_manager._trigger_alert(rule, {})
        
        # 验证现有告警被更新
        assert existing_alert.count == 2
        assert existing_alert.updated_at > existing_alert.created_at
    
    @pytest.mark.asyncio
    async def test_resolve_alert(self, alert_manager):
        """测试解决告警"""
        # 创建告警
        alert = Alert(
            id="test-alert",
            title="测试告警",
            description="测试描述",
            level=AlertLevel.ERROR
        )
        alert_manager.alerts["test-alert"] = alert
        
        # 解决告警
        await alert_manager.resolve_alert("test-alert")
        
        # 验证告警状态
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None
    
    @pytest.mark.asyncio
    async def test_get_active_alerts(self, alert_manager):
        """测试获取活跃告警"""
        # 创建活跃告警
        active_alert = Alert(
            id="active-alert",
            title="活跃告警",
            description="描述",
            level=AlertLevel.WARNING,
            status=AlertStatus.ACTIVE
        )
        
        # 创建已解决告警
        resolved_alert = Alert(
            id="resolved-alert",
            title="已解决告警",
            description="描述",
            level=AlertLevel.INFO,
            status=AlertStatus.RESOLVED
        )
        
        alert_manager.alerts["active-alert"] = active_alert
        alert_manager.alerts["resolved-alert"] = resolved_alert
        
        # 获取活跃告警
        active_alerts = await alert_manager.get_active_alerts()
        
        assert len(active_alerts) == 1
        assert active_alerts[0]["id"] == "active-alert"
    
    @pytest.mark.asyncio
    async def test_get_alert_history(self, alert_manager):
        """测试获取告警历史"""
        # 创建最近的告警
        recent_alert = Alert(
            id="recent-alert",
            title="最近告警",
            description="描述",
            level=AlertLevel.ERROR,
            created_at=datetime.now() - timedelta(hours=1)
        )
        
        # 创建较早的告警
        old_alert = Alert(
            id="old-alert",
            title="较早告警",
            description="描述",
            level=AlertLevel.WARNING,
            created_at=datetime.now() - timedelta(days=2)
        )
        
        alert_manager.alerts["recent-alert"] = recent_alert
        alert_manager.alerts["old-alert"] = old_alert
        
        # 获取24小时内的告警历史
        history = await alert_manager.get_alert_history(hours=24)
        
        assert len(history) == 1
        assert history[0]["id"] == "recent-alert"
    
    @pytest.mark.asyncio
    async def test_monitoring_loop_error_handling(self, alert_manager):
        """测试监控循环错误处理"""
        # 模拟指标收集器错误
        with patch('app.monitoring.ctp_alerts.metrics_collector') as mock_collector:
            mock_collector.get_metrics_summary.side_effect = Exception("Test error")
            
            # 启动监控
            await alert_manager.start_monitoring()
            
            # 等待一小段时间让循环运行
            await asyncio.sleep(0.1)
            
            # 停止监控
            await alert_manager.stop_monitoring()
            
            # 验证管理器仍然可以正常工作
            assert alert_manager.running is False
    
    @pytest.mark.asyncio
    async def test_send_notifications_error_handling(self, alert_manager):
        """测试发送通知错误处理"""
        # 添加会失败的通知渠道
        failing_channel = AsyncMock()
        failing_channel.send.side_effect = Exception("Notification failed")
        alert_manager.add_channel(failing_channel)
        
        # 创建告警
        alert = Alert(
            id="test-alert",
            title="测试告警",
            description="描述",
            level=AlertLevel.ERROR
        )
        
        # 发送通知（应该处理错误而不崩溃）
        await alert_manager._send_notifications(alert)
        
        # 验证方法被调用
        failing_channel.send.assert_called_once_with(alert)
