"""
认证API集成测试
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, Mock

from app.core.security import create_access_token


@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.asyncio
class TestAuthAPI:
    """认证API测试类"""

    async def test_login_success(self, client: AsyncClient):
        """测试登录成功"""
        # 准备测试数据
        login_data = {
            "username": "testuser",
            "password": "testpassword123"
        }

        # 模拟用户认证成功
        with patch('app.api.v1.auth.authenticate_user') as mock_auth:
            mock_user = Mock()
            mock_user.id = "test-user-id"
            mock_user.username = "testuser"
            mock_user.is_active = True
            mock_auth.return_value = mock_user

            # 发送请求
            response = await client.post("/api/v1/auth/login", data=login_data)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data

    async def test_login_invalid_credentials(self, client: AsyncClient):
        """测试登录凭据无效"""
        # 准备测试数据
        login_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }

        # 模拟用户认证失败
        with patch('app.api.v1.auth.authenticate_user', return_value=None):
            # 发送请求
            response = await client.post("/api/v1/auth/login", data=login_data)

        # 验证响应
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "用户名或密码错误"

    async def test_login_missing_fields(self, client: AsyncClient):
        """测试登录缺少必填字段"""
        # 准备不完整的测试数据
        login_data = {
            "username": "testuser"
            # 缺少password字段
        }

        # 发送请求
        response = await client.post("/api/v1/auth/login", data=login_data)

        # 验证响应
        assert response.status_code == 422  # Validation error

    async def test_register_success(self, client: AsyncClient):
        """测试注册成功"""
        # 准备测试数据
        register_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword123",
            "full_name": "New User"
        }

        # 模拟用户创建成功
        with patch('app.api.v1.auth.create_user') as mock_create:
            mock_user = Mock()
            mock_user.id = "new-user-id"
            mock_user.username = "newuser"
            mock_user.email = "newuser@example.com"
            mock_user.full_name = "New User"
            mock_user.is_active = True
            mock_create.return_value = mock_user

            # 发送请求
            response = await client.post("/api/v1/auth/register", json=register_data)

        # 验证响应
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    async def test_register_duplicate_username(self, client: AsyncClient):
        """测试注册重复用户名"""
        # 准备测试数据
        register_data = {
            "username": "existinguser",
            "email": "existing@example.com",
            "password": "password123",
            "full_name": "Existing User"
        }

        # 模拟用户名已存在
        with patch('app.api.v1.auth.create_user', side_effect=ValueError("用户名已存在")):
            # 发送请求
            response = await client.post("/api/v1/auth/register", json=register_data)

        # 验证响应
        assert response.status_code == 400
        data = response.json()
        assert "用户名已存在" in data["detail"]

    async def test_register_invalid_email(self, client: AsyncClient):
        """测试注册无效邮箱"""
        # 准备测试数据
        register_data = {
            "username": "testuser",
            "email": "invalid-email",  # 无效邮箱格式
            "password": "password123",
            "full_name": "Test User"
        }

        # 发送请求
        response = await client.post("/api/v1/auth/register", json=register_data)

        # 验证响应
        assert response.status_code == 422  # Validation error

    async def test_register_weak_password(self, client: AsyncClient):
        """测试注册弱密码"""
        # 准备测试数据
        register_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123",  # 弱密码
            "full_name": "Test User"
        }

        # 发送请求
        response = await client.post("/api/v1/auth/register", json=register_data)

        # 验证响应
        assert response.status_code == 422  # Validation error

    async def test_get_current_user_success(self, client: AsyncClient):
        """测试获取当前用户信息成功"""
        # 创建访问令牌
        token = create_access_token(data={"sub": "test-user-id"})
        headers = {"Authorization": f"Bearer {token}"}

        # 模拟获取用户信息
        with patch('app.api.deps.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "test-user-id"
            mock_user.username = "testuser"
            mock_user.email = "test@example.com"
            mock_user.is_active = True
            mock_get_user.return_value = mock_user

            # 发送请求
            response = await client.get("/api/v1/auth/me", headers=headers)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-user-id"
        assert data["username"] == "testuser"

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """测试未授权获取当前用户信息"""
        # 发送请求（不带token）
        response = await client.get("/api/v1/auth/me")

        # 验证响应
        assert response.status_code == 401

    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        """测试无效token获取当前用户信息"""
        # 使用无效token
        headers = {"Authorization": "Bearer invalid-token"}

        # 发送请求
        response = await client.get("/api/v1/auth/me", headers=headers)

        # 验证响应
        assert response.status_code == 401

    async def test_refresh_token_success(self, client: AsyncClient):
        """测试刷新token成功"""
        # 创建访问令牌
        token = create_access_token(data={"sub": "test-user-id"})
        headers = {"Authorization": f"Bearer {token}"}

        # 模拟获取用户信息
        with patch('app.api.deps.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "test-user-id"
            mock_user.username = "testuser"
            mock_user.is_active = True
            mock_get_user.return_value = mock_user

            # 发送请求
            response = await client.post("/api/v1/auth/refresh", headers=headers)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_logout_success(self, client: AsyncClient):
        """测试登出成功"""
        # 创建访问令牌
        token = create_access_token(data={"sub": "test-user-id"})
        headers = {"Authorization": f"Bearer {token}"}

        # 模拟获取用户信息
        with patch('app.api.deps.get_current_active_user') as mock_get_user:
            mock_user = Mock()
            mock_user.id = "test-user-id"
            mock_get_user.return_value = mock_user

            # 发送请求
            response = await client.post("/api/v1/auth/logout", headers=headers)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "登出成功"

    async def test_change_password_success(self, client: AsyncClient):
        """测试修改密码成功"""
        # 创建访问令牌
        token = create_access_token(data={"sub": "test-user-id"})
        headers = {"Authorization": f"Bearer {token}"}

        # 准备测试数据
        password_data = {
            "current_password": "oldpassword123",
            "new_password": "newpassword123"
        }

        # 模拟用户认证和密码更新
        with patch('app.api.deps.get_current_active_user') as mock_get_user, \
             patch('app.api.v1.auth.verify_password', return_value=True), \
             patch('app.api.v1.auth.update_user_password') as mock_update:
            
            mock_user = Mock()
            mock_user.id = "test-user-id"
            mock_get_user.return_value = mock_user
            mock_update.return_value = True

            # 发送请求
            response = await client.post("/api/v1/auth/change-password", 
                                       json=password_data, headers=headers)

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "密码修改成功"

    async def test_change_password_wrong_current(self, client: AsyncClient):
        """测试修改密码当前密码错误"""
        # 创建访问令牌
        token = create_access_token(data={"sub": "test-user-id"})
        headers = {"Authorization": f"Bearer {token}"}

        # 准备测试数据
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword123"
        }

        # 模拟当前密码验证失败
        with patch('app.api.deps.get_current_active_user') as mock_get_user, \
             patch('app.api.v1.auth.verify_password', return_value=False):
            
            mock_user = Mock()
            mock_user.id = "test-user-id"
            mock_get_user.return_value = mock_user

            # 发送请求
            response = await client.post("/api/v1/auth/change-password", 
                                       json=password_data, headers=headers)

        # 验证响应
        assert response.status_code == 400
        data = response.json()
        assert "当前密码错误" in data["detail"]
