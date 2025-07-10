"""
用户服务单元测试
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import UserService
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


@pytest.mark.unit
@pytest.mark.asyncio
class TestUserService:
    """用户服务测试类"""

    @pytest.fixture
    def user_service(self):
        """创建用户服务实例"""
        return UserService()

    @pytest.fixture
    def mock_db_session(self):
        """模拟数据库会话"""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def sample_user_create(self):
        """示例用户创建数据"""
        return UserCreate(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
            full_name="Test User"
        )

    @pytest.fixture
    def sample_user_model(self):
        """示例用户模型"""
        user = Mock(spec=User)
        user.id = "test-user-id"
        user.username = "testuser"
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.is_active = True
        user.hashed_password = get_password_hash("testpassword123")
        return user

    async def test_create_user_success(self, user_service, mock_db_session, sample_user_create):
        """测试成功创建用户"""
        # 模拟数据库操作
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None
        mock_db_session.add = Mock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # 执行测试
        with patch('app.services.user_service.User') as mock_user_class:
            mock_user_instance = Mock()
            mock_user_instance.id = "new-user-id"
            mock_user_class.return_value = mock_user_instance
            
            result = await user_service.create_user(mock_db_session, sample_user_create)

            # 验证结果
            assert result is not None
            assert result.id == "new-user-id"
            mock_db_session.add.assert_called_once()
            mock_db_session.commit.assert_called_once()

    async def test_create_user_duplicate_username(self, user_service, mock_db_session, sample_user_create):
        """测试创建重复用户名的用户"""
        # 模拟用户名已存在
        existing_user = Mock()
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = existing_user

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="用户名已存在"):
            await user_service.create_user(mock_db_session, sample_user_create)

    async def test_get_user_by_id_success(self, user_service, mock_db_session, sample_user_model):
        """测试通过ID获取用户成功"""
        # 模拟数据库查询
        mock_db_session.get.return_value = sample_user_model

        # 执行测试
        result = await user_service.get_user_by_id(mock_db_session, "test-user-id")

        # 验证结果
        assert result == sample_user_model
        mock_db_session.get.assert_called_once_with(User, "test-user-id")

    async def test_get_user_by_id_not_found(self, user_service, mock_db_session):
        """测试通过ID获取用户失败"""
        # 模拟用户不存在
        mock_db_session.get.return_value = None

        # 执行测试
        result = await user_service.get_user_by_id(mock_db_session, "nonexistent-id")

        # 验证结果
        assert result is None

    async def test_get_user_by_username_success(self, user_service, mock_db_session, sample_user_model):
        """测试通过用户名获取用户成功"""
        # 模拟数据库查询
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_user_model

        # 执行测试
        result = await user_service.get_user_by_username(mock_db_session, "testuser")

        # 验证结果
        assert result == sample_user_model

    async def test_authenticate_user_success(self, user_service, mock_db_session, sample_user_model):
        """测试用户认证成功"""
        # 模拟数据库查询
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_user_model

        # 模拟密码验证
        with patch('app.services.user_service.verify_password', return_value=True):
            result = await user_service.authenticate_user(mock_db_session, "testuser", "testpassword123")

        # 验证结果
        assert result == sample_user_model

    async def test_authenticate_user_wrong_password(self, user_service, mock_db_session, sample_user_model):
        """测试用户认证密码错误"""
        # 模拟数据库查询
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = sample_user_model

        # 模拟密码验证失败
        with patch('app.services.user_service.verify_password', return_value=False):
            result = await user_service.authenticate_user(mock_db_session, "testuser", "wrongpassword")

        # 验证结果
        assert result is None

    async def test_authenticate_user_not_found(self, user_service, mock_db_session):
        """测试用户认证用户不存在"""
        # 模拟用户不存在
        mock_db_session.execute.return_value.scalar_one_or_none.return_value = None

        # 执行测试
        result = await user_service.authenticate_user(mock_db_session, "nonexistent", "password")

        # 验证结果
        assert result is None

    async def test_update_user_success(self, user_service, mock_db_session, sample_user_model):
        """测试更新用户成功"""
        # 准备更新数据
        user_update = UserUpdate(full_name="Updated Name", email="updated@example.com")
        
        # 模拟数据库操作
        mock_db_session.get.return_value = sample_user_model
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # 执行测试
        result = await user_service.update_user(mock_db_session, "test-user-id", user_update)

        # 验证结果
        assert result == sample_user_model
        assert sample_user_model.full_name == "Updated Name"
        assert sample_user_model.email == "updated@example.com"
        mock_db_session.commit.assert_called_once()

    async def test_update_user_not_found(self, user_service, mock_db_session):
        """测试更新不存在的用户"""
        # 模拟用户不存在
        mock_db_session.get.return_value = None
        user_update = UserUpdate(full_name="Updated Name")

        # 执行测试
        result = await user_service.update_user(mock_db_session, "nonexistent-id", user_update)

        # 验证结果
        assert result is None

    async def test_delete_user_success(self, user_service, mock_db_session, sample_user_model):
        """测试删除用户成功"""
        # 模拟数据库操作
        mock_db_session.get.return_value = sample_user_model
        mock_db_session.delete = Mock()
        mock_db_session.commit = AsyncMock()

        # 执行测试
        result = await user_service.delete_user(mock_db_session, "test-user-id")

        # 验证结果
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_user_model)
        mock_db_session.commit.assert_called_once()

    async def test_delete_user_not_found(self, user_service, mock_db_session):
        """测试删除不存在的用户"""
        # 模拟用户不存在
        mock_db_session.get.return_value = None

        # 执行测试
        result = await user_service.delete_user(mock_db_session, "nonexistent-id")

        # 验证结果
        assert result is False

    async def test_is_user_active(self, user_service, mock_db_session, sample_user_model):
        """测试检查用户是否激活"""
        # 模拟数据库查询
        mock_db_session.get.return_value = sample_user_model

        # 执行测试
        result = await user_service.is_user_active(mock_db_session, "test-user-id")

        # 验证结果
        assert result is True

    async def test_is_user_active_inactive_user(self, user_service, mock_db_session, sample_user_model):
        """测试检查非激活用户"""
        # 设置用户为非激活状态
        sample_user_model.is_active = False
        mock_db_session.get.return_value = sample_user_model

        # 执行测试
        result = await user_service.is_user_active(mock_db_session, "test-user-id")

        # 验证结果
        assert result is False

    async def test_is_user_active_not_found(self, user_service, mock_db_session):
        """测试检查不存在用户的激活状态"""
        # 模拟用户不存在
        mock_db_session.get.return_value = None

        # 执行测试
        result = await user_service.is_user_active(mock_db_session, "nonexistent-id")

        # 验证结果
        assert result is False
