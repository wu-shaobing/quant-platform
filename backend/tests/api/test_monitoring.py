"""
监控API测试
"""
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import create_app
from app.monitoring.ctp_alerts import Alert, AlertLevel, AlertStatus


@pytest.fixture
def client():
    """创建测试客户端"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """认证头部"""
    # 这里应该使用实际的JWT token，简化测试使用模拟
    return {"Authorization": "Bearer test-token"}


class TestMonitoringAPI:
    """监控API测试类"""
    
    @patch('app.api.v1.monitoring.get_current_user')
    @patch('app.monitoring.metrics_collector')
    def test_get_metrics(self, mock_collector, mock_auth, client):
        """测试获取指标"""
        # 模拟用户认证
        mock_auth.return_value = AsyncMock()
        
        # 模拟指标数据
        mock_collector.get_metrics_summary.return_value = {
            "connection_status": {"trade": True, "md": True},
            "connection_uptime": {"trade": 3600.0, "md": 3600.0},
            "order_stats": {
                "total": 100,
                "success": 95,
                "error": 5,
                "success_rate": 0.95,
                "error_rate": 0.05,
                "avg_response_time": 0.5
            },
            "trade_count": 50,
            "market_data": {
                "total": 10000,
                "delay": 0.1,
                "subscriptions": 50
            },
            "system": {
                "memory_usage": 1073741824,  # 1GB
                "cpu_usage": 45.5
            },
            "errors": {
                "connection": 1,
                "trading": 2,
                "market_data": 0
            },
            "last_update": datetime.now().isoformat()
        }
        
        response = client.get("/api/v1/monitoring/metrics", headers={"Authorization": "Bearer test-token"})
        
        assert response.status_code == 200
        data = response.json()
        assert "connection_status" in data
        assert "order_stats" in data
        assert "trade_count" in data
        assert data["trade_count"] == 50
    
    @patch('app.monitoring.metrics_collector')
    def test_get_health_status(self, mock_collector, client):
        """测试获取健康状态（无需认证）"""
        # 模拟健康状态数据
        mock_collector.get_health_status.return_value = {
            "status": "healthy",
            "reason": "All systems operational",
            "connections": {"trade": True, "md": True},
            "error_rate": 0.05,
            "last_update": datetime.now().isoformat(),
            "uptime": {"trade": 3600.0, "md": 3600.0}
        }
        
        response = client.get("/api/v1/monitoring/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["connections"]["trade"] is True
    
    @patch('app.monitoring.metrics_collector')
    def test_readiness_check(self, mock_collector, client):
        """测试就绪检查"""
        # 模拟健康状态
        mock_collector.get_health_status.return_value = {
            "status": "healthy"
        }
        
        response = client.get("/api/v1/monitoring/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
    
    @patch('app.monitoring.metrics_collector')
    def test_readiness_check_not_ready(self, mock_collector, client):
        """测试就绪检查 - 未就绪"""
        # 模拟不健康状态
        mock_collector.get_health_status.return_value = {
            "status": "unhealthy",
            "reason": "Database connection failed"
        }
        
        response = client.get("/api/v1/monitoring/ready")
        
        assert response.status_code == 503
        data = response.json()
        assert "Service not ready" in data["detail"]
    
    def test_liveness_check(self, client):
        """测试存活检查"""
        response = client.get("/api/v1/monitoring/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
    
    @patch('app.api.v1.monitoring.get_current_user')
    @patch('app.monitoring.alert_manager')
    def test_get_active_alerts(self, mock_manager, mock_auth, client):
        """测试获取活跃告警"""
        # 模拟用户认证
        mock_auth.return_value = AsyncMock()
        
        # 模拟活跃告警
        mock_manager.get_active_alerts.return_value = [
            {
                "id": "alert-1",
                "title": "连接断开",
                "description": "CTP连接断开",
                "level": "critical",
                "status": "active",
                "source": "ctp",
                "category": "connection",
                "tags": {"broker": "CITIC"},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "resolved_at": None,
                "count": 1
            }
        ]
        
        response = client.get("/api/v1/monitoring/alerts", headers={"Authorization": "Bearer test-token"})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "连接断开"
        assert data[0]["level"] == "critical"
    
    @patch('app.api.v1.monitoring.get_current_user')
    @patch('app.monitoring.alert_manager')
    def test_get_alert_history(self, mock_manager, mock_auth, client):
        """测试获取告警历史"""
        # 模拟用户认证
        mock_auth.return_value = AsyncMock()
        
        # 模拟告警历史
        mock_manager.get_alert_history.return_value = [
            {
                "id": "alert-1",
                "title": "内存使用过高",
                "description": "内存使用超过阈值",
                "level": "warning",
                "status": "resolved",
                "source": "ctp",
                "category": "system",
                "tags": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "resolved_at": datetime.now().isoformat(),
                "count": 1
            }
        ]
        
        response = client.get("/api/v1/monitoring/alerts/history?hours=24", headers={"Authorization": "Bearer test-token"})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "内存使用过高"
        assert data[0]["status"] == "resolved"
    
    @patch('app.api.v1.monitoring.get_current_user')
    @patch('app.monitoring.alert_manager')
    def test_create_manual_alert(self, mock_manager, mock_auth, client):
        """测试创建手动告警"""
        # 模拟用户认证
        mock_user = AsyncMock()
        mock_user.username = "testuser"
        mock_user.id = 1
        mock_auth.return_value = mock_user
        
        # 模拟告警管理器
        mock_manager.alerts = {}
        mock_manager._send_notifications = AsyncMock()
        
        alert_data = {
            "title": "手动告警",
            "description": "这是一个手动创建的告警",
            "level": "warning",
            "category": "manual",
            "tags": {"source": "user"}
        }
        
        response = client.post("/api/v1/monitoring/alerts", json=alert_data, headers={"Authorization": "Bearer test-token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "手动告警"
        assert data["level"] == "warning"
        assert data["tags"]["created_by"] == "testuser"
    
    @patch('app.api.v1.monitoring.get_current_user')
    @patch('app.monitoring.alert_manager')
    def test_create_manual_alert_invalid_level(self, mock_manager, mock_auth, client):
        """测试创建手动告警 - 无效级别"""
        # 模拟用户认证
        mock_auth.return_value = AsyncMock()
        
        alert_data = {
            "title": "手动告警",
            "description": "描述",
            "level": "invalid_level",  # 无效级别
            "category": "manual"
        }
        
        response = client.post("/api/v1/monitoring/alerts", json=alert_data, headers={"Authorization": "Bearer test-token"})
        
        assert response.status_code == 400
        assert "Invalid alert level" in response.json()["detail"]
    
    @patch('app.api.v1.monitoring.get_current_user')
    @patch('app.monitoring.alert_manager')
    def test_resolve_alert(self, mock_manager, mock_auth, client):
        """测试解决告警"""
        # 模拟用户认证
        mock_user = AsyncMock()
        mock_user.username = "testuser"
        mock_user.id = 1
        mock_auth.return_value = mock_user
        
        # 模拟现有告警
        mock_alert = Alert(
            id="test-alert",
            title="测试告警",
            description="描述",
            level=AlertLevel.WARNING
        )
        mock_manager.alerts = {"test-alert": mock_alert}
        mock_manager.resolve_alert = AsyncMock()
        
        response = client.put("/api/v1/monitoring/alerts/test-alert/resolve", headers={"Authorization": "Bearer test-token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Alert resolved successfully"
        
        # 验证解决者信息被添加
        assert mock_alert.tags["resolved_by"] == "testuser"
        assert mock_alert.tags["resolver_id"] == "1"
    
    @patch('app.api.v1.monitoring.get_current_user')
    @patch('app.monitoring.alert_manager')
    def test_resolve_alert_not_found(self, mock_manager, mock_auth, client):
        """测试解决不存在的告警"""
        # 模拟用户认证
        mock_auth.return_value = AsyncMock()
        
        # 空的告警列表
        mock_manager.alerts = {}
        
        response = client.put("/api/v1/monitoring/alerts/nonexistent/resolve", headers={"Authorization": "Bearer test-token"})
        
        assert response.status_code == 404
        assert "Alert not found" in response.json()["detail"]
    
    @patch('app.api.v1.monitoring.get_current_user')
    @patch('app.monitoring.metrics_collector')
    def test_get_connection_metrics(self, mock_collector, mock_auth, client):
        """测试获取连接指标详情"""
        # 模拟用户认证
        mock_auth.return_value = AsyncMock()
        
        # 模拟指标数据
        mock_collector.get_metrics_summary.return_value = {
            "connection_status": {"trade": True, "md": False},
            "connection_uptime": {"trade": 3600.0, "md": 0.0},
            "last_update": datetime.now().isoformat()
        }
        
        response = client.get("/api/v1/monitoring/metrics/connection", headers={"Authorization": "Bearer test-token"})
        
        assert response.status_code == 200
        data = response.json()
        assert "connection_status" in data
        assert "connection_uptime" in data
        assert data["connection_status"]["trade"] is True
        assert data["connection_status"]["md"] is False
    
    @patch('app.api.v1.monitoring.get_current_user')
    @patch('app.monitoring.metrics_collector')
    def test_start_metrics_collection(self, mock_collector, mock_auth, client):
        """测试启动指标收集"""
        # 模拟用户认证
        mock_auth.return_value = AsyncMock()
        
        # 模拟启动方法
        mock_collector.start_collection = AsyncMock()
        
        response = client.post("/api/v1/monitoring/metrics/start", headers={"Authorization": "Bearer test-token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Metrics collection started"
        mock_collector.start_collection.assert_called_once()
    
    @patch('app.api.v1.monitoring.get_current_user')
    @patch('app.monitoring.alert_manager')
    def test_start_alert_monitoring(self, mock_manager, mock_auth, client):
        """测试启动告警监控"""
        # 模拟用户认证
        mock_auth.return_value = AsyncMock()
        
        # 模拟启动方法
        mock_manager.start_monitoring = AsyncMock()
        
        response = client.post("/api/v1/monitoring/alerts/start", headers={"Authorization": "Bearer test-token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Alert monitoring started"
        mock_manager.start_monitoring.assert_called_once()
    
    @patch('app.api.v1.monitoring.get_current_user')
    @patch('app.monitoring.metrics_collector')
    @patch('app.monitoring.alert_manager')
    def test_get_monitoring_status(self, mock_alert_manager, mock_collector, mock_auth, client):
        """测试获取监控系统状态"""
        # 模拟用户认证
        mock_auth.return_value = AsyncMock()
        
        # 模拟监控状态
        mock_collector.running = True
        mock_collector.metrics_port = 9090
        mock_collector.collection_interval = 30
        
        mock_alert_manager.running = True
        mock_alert_manager.check_interval = 60
        mock_alert_manager.get_active_alerts.return_value = [{"id": "alert-1"}]
        mock_alert_manager.channels = [AsyncMock(), AsyncMock()]
        mock_alert_manager.rules = [AsyncMock(), AsyncMock(), AsyncMock()]
        
        response = client.get("/api/v1/monitoring/status", headers={"Authorization": "Bearer test-token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["metrics_collection_running"] is True
        assert data["alert_monitoring_running"] is True
        assert data["metrics_port"] == 9090
        assert data["collection_interval"] == 30
        assert data["alert_check_interval"] == 60
        assert data["active_alert_count"] == 1
        assert data["notification_channels"] == 2
        assert data["alert_rules"] == 3
    
    def test_unauthorized_access(self, client):
        """测试未授权访问"""
        response = client.get("/api/v1/monitoring/metrics")
        assert response.status_code == 401
        
        response = client.get("/api/v1/monitoring/alerts")
        assert response.status_code == 401
        
        response = client.post("/api/v1/monitoring/alerts", json={})
        assert response.status_code == 401
