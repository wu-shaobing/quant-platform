"""
CTP安全加固功能测试
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from app.core.security_hardening import (
    SecurityHardening,
    JWTSecurityManager,
    AdvancedDataEncryption,
    AuditEvent,
    AuditEventType,
    SecurityLevel
)
from app.core.ctp_security_config import (
    SecurityHardeningConfig,
    JWTSecurityConfig,
    EncryptionConfig,
    EncryptionAlgorithm
)


class TestJWTSecurityManager:
    """JWT安全管理器测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.jwt_manager = JWTSecurityManager()
    
    @pytest.mark.asyncio
    async def test_create_secure_token(self):
        """测试创建安全令牌"""
        with patch('app.core.auth.create_access_token') as mock_access, \
             patch('app.core.auth.create_refresh_token') as mock_refresh:
            
            mock_access.return_value = "mock_access_token"
            mock_refresh.return_value = "mock_refresh_token"
            
            tokens = await self.jwt_manager.create_secure_token(
                user_id=1,
                permissions=["trading", "query"],
                device_fingerprint="test_fingerprint"
            )
            
            assert "access_token" in tokens
            assert "refresh_token" in tokens
            assert "token_type" in tokens
            assert "expires_in" in tokens
            assert tokens["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_validate_token_security(self):
        """测试令牌安全验证"""
        with patch('app.core.auth.verify_token') as mock_verify:
            mock_verify.return_value = {
                "sub": "1",
                "permissions": ["trading"],
                "device_fingerprint": "test_fingerprint",
                "token_type": "access",
                "jti": "test_jti"
            }
            
            valid, result = await self.jwt_manager.validate_token_security(
                token="test_token",
                device_fingerprint="test_fingerprint"
            )
            
            assert valid is True
            assert "payload" in result
    
    @pytest.mark.asyncio
    async def test_revoke_token(self):
        """测试令牌撤销"""
        token = "test_token_to_revoke"
        await self.jwt_manager.revoke_token(token)
        
        assert token in self.jwt_manager.token_blacklist
    
    @pytest.mark.asyncio
    async def test_refresh_token_security(self):
        """测试安全令牌刷新"""
        # 先添加一个刷新令牌到存储
        jti = "test_jti"
        self.jwt_manager.refresh_token_store[jti] = {
            "user_id": 1,
            "created_at": datetime.now(),
            "device_fingerprint": "test_fingerprint"
        }
        
        with patch('app.core.auth.verify_token') as mock_verify, \
             patch.object(self.jwt_manager, 'create_secure_token') as mock_create:
            
            mock_verify.return_value = {
                "sub": "1",
                "token_type": "refresh",
                "jti": jti
            }
            
            mock_create.return_value = {
                "access_token": "new_access_token",
                "refresh_token": "new_refresh_token"
            }
            
            success, result = await self.jwt_manager.refresh_token_security(
                refresh_token="test_refresh_token",
                device_fingerprint="test_fingerprint"
            )
            
            assert success is True
            assert "access_token" in result


class TestAdvancedDataEncryption:
    """高级数据加密测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.encryption = AdvancedDataEncryption()
    
    @pytest.mark.asyncio
    async def test_encrypt_decrypt_field(self):
        """测试字段加密解密"""
        field_name = "password"
        original_value = "test_password_123"
        
        # 测试加密
        encrypted_value = await self.encryption.encrypt_field(
            field_name=field_name,
            value=original_value,
            algorithm="AES-256-GCM"
        )
        
        assert encrypted_value != original_value
        assert isinstance(encrypted_value, str)
        
        # 测试解密
        decrypted_value = await self.encryption.decrypt_field(
            field_name=field_name,
            encrypted_value=encrypted_value
        )
        
        assert decrypted_value == original_value
    
    @pytest.mark.asyncio
    async def test_multiple_algorithms(self):
        """测试多种加密算法"""
        field_name = "api_key"
        original_value = "test_api_key_value"
        
        algorithms = ["AES-256-GCM", "ChaCha20-Poly1305", "Fernet"]
        
        for algorithm in algorithms:
            try:
                encrypted_value = await self.encryption.encrypt_field(
                    field_name=field_name,
                    value=original_value,
                    algorithm=algorithm
                )
                
                decrypted_value = await self.encryption.decrypt_field(
                    field_name=field_name,
                    encrypted_value=encrypted_value
                )
                
                assert decrypted_value == original_value
            except ImportError:
                # 如果加密库不可用，应该回退到其他算法
                pass
    
    def test_field_key_derivation(self):
        """测试字段密钥派生"""
        field_name = "test_field"
        key = self.encryption._derive_field_key(field_name)
        
        assert isinstance(key, bytes)
        assert len(key) == 32  # 256位密钥
        
        # 相同字段名应该生成相同密钥
        key2 = self.encryption._derive_field_key(field_name)
        assert key == key2
        
        # 不同字段名应该生成不同密钥
        key3 = self.encryption._derive_field_key("different_field")
        assert key != key3


class TestSecurityHardening:
    """安全加固主类测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.security = SecurityHardening()
    
    @pytest.mark.asyncio
    async def test_audit_logging(self):
        """测试审计日志"""
        audit_event = AuditEvent(
            event_type=AuditEventType.LOGIN,
            user_id=1,
            ip_address="192.168.1.100",
            user_agent="TestAgent",
            endpoint="/api/v1/auth/login",
            method="POST",
            request_data={"username": "test_user"},
            response_status=200,
            risk_level=SecurityLevel.LOW
        )
        
        # 记录审计事件
        await self.security.audit_logger.log_event(audit_event)
        
        # 查询审计事件
        events = await self.security.audit_logger.query_events(
            start_date=datetime.now() - timedelta(hours=1),
            end_date=datetime.now(),
            user_id=1
        )
        
        assert len(events) > 0
        assert events[0]["event_type"] == "LOGIN"
        assert events[0]["user_id"] == 1
    
    def test_access_control(self):
        """测试访问控制"""
        # 测试IP白名单
        test_ip = "192.168.1.100"
        self.security.access_controller.add_to_whitelist(test_ip)
        assert test_ip in self.security.access_controller.ip_whitelist
        
        # 测试IP黑名单
        bad_ip = "10.0.0.1"
        self.security.access_controller.add_to_blacklist(bad_ip)
        assert bad_ip in self.security.access_controller.ip_blacklist
        
        # 测试用户阻止
        user_id = 123
        self.security.access_controller.block_user(user_id)
        assert user_id in self.security.access_controller.blocked_users
    
    def test_threat_detection(self):
        """测试威胁检测"""
        # 测试SQL注入检测
        malicious_input = "'; DROP TABLE users; --"
        is_threat = self.security.detect_sql_injection(malicious_input)
        assert is_threat is True
        
        # 测试正常输入
        normal_input = "normal user input"
        is_threat = self.security.detect_sql_injection(normal_input)
        assert is_threat is False
        
        # 测试XSS检测
        xss_input = "<script>alert('xss')</script>"
        is_threat = self.security.detect_xss(xss_input)
        assert is_threat is True


class TestSecurityConfig:
    """安全配置测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = SecurityHardeningConfig()
        
        assert config.security_level == SecurityLevel.HIGH
        assert config.jwt_config.access_token_lifetime == 3600
        assert config.encryption_config.default_algorithm == EncryptionAlgorithm.AES_256_GCM
        assert config.enable_security_headers is True
    
    def test_config_serialization(self):
        """测试配置序列化"""
        config = SecurityHardeningConfig()
        
        # 转换为字典
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "jwt_config" in config_dict
        assert "encryption_config" in config_dict
        
        # 转换为JSON
        config_json = config.to_json()
        assert isinstance(config_json, str)
        assert "jwt_config" in config_json
    
    def test_config_deserialization(self):
        """测试配置反序列化"""
        original_config = SecurityHardeningConfig()
        config_dict = original_config.to_dict()
        
        # 从字典重建配置
        rebuilt_config = SecurityHardeningConfig.from_dict(config_dict)
        
        assert rebuilt_config.security_level == original_config.security_level
        assert rebuilt_config.jwt_config.access_token_lifetime == original_config.jwt_config.access_token_lifetime


class TestSecurityIntegration:
    """安全功能集成测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.security = SecurityHardening()
        self.jwt_manager = JWTSecurityManager()
        self.encryption = AdvancedDataEncryption()
    
    @pytest.mark.asyncio
    async def test_end_to_end_security_flow(self):
        """测试端到端安全流程"""
        # 1. 创建安全令牌
        with patch('app.core.auth.create_access_token') as mock_access, \
             patch('app.core.auth.create_refresh_token') as mock_refresh:
            
            mock_access.return_value = "test_access_token"
            mock_refresh.return_value = "test_refresh_token"
            
            tokens = await self.jwt_manager.create_secure_token(
                user_id=1,
                permissions=["trading"],
                device_fingerprint="test_device"
            )
            
            assert "access_token" in tokens
        
        # 2. 加密敏感数据
        sensitive_data = "sensitive_trading_account_123"
        encrypted_data = await self.encryption.encrypt_field(
            field_name="trading_account",
            value=sensitive_data
        )
        
        assert encrypted_data != sensitive_data
        
        # 3. 记录审计事件
        audit_event = AuditEvent(
            event_type=AuditEventType.ORDER_SUBMIT,
            user_id=1,
            ip_address="192.168.1.100",
            user_agent="TradingApp",
            endpoint="/api/v1/trading/order",
            method="POST",
            request_data={"symbol": "rb2501", "quantity": 1},
            response_status=200,
            risk_level=SecurityLevel.MEDIUM
        )
        
        await self.security.audit_logger.log_event(audit_event)
        
        # 4. 验证审计日志
        events = await self.security.audit_logger.query_events(
            start_date=datetime.now() - timedelta(minutes=1),
            end_date=datetime.now(),
            user_id=1
        )
        
        assert len(events) > 0
        assert events[0]["event_type"] == "ORDER_SUBMIT"
    
    @pytest.mark.asyncio
    async def test_security_performance(self):
        """测试安全功能性能"""
        import time
        
        # 测试加密性能
        test_data = "performance_test_data" * 100
        
        start_time = time.time()
        encrypted = await self.encryption.encrypt_field("test_field", test_data)
        encrypt_time = time.time() - start_time
        
        start_time = time.time()
        decrypted = await self.encryption.decrypt_field("test_field", encrypted)
        decrypt_time = time.time() - start_time
        
        # 验证性能要求（加密+解密应该在100ms内完成）
        total_time = encrypt_time + decrypt_time
        assert total_time < 0.1  # 100ms
        assert decrypted == test_data
        
        # 测试JWT令牌验证性能
        with patch('app.core.auth.verify_token') as mock_verify:
            mock_verify.return_value = {
                "sub": "1",
                "token_type": "access",
                "jti": "test_jti"
            }
            
            start_time = time.time()
            for _ in range(100):
                await self.jwt_manager.validate_token_security("test_token")
            validation_time = time.time() - start_time
            
            # 100次验证应该在1秒内完成
            assert validation_time < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
