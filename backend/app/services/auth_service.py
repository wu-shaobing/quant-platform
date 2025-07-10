"""
认证服务模块

提供用户认证相关的业务逻辑，包括：
- 用户注册和登录
- Token管理和刷新
- 密码重置
- 用户信息管理
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from fastapi import HTTPException, status
import secrets
import hashlib

from ..core.security import SecurityManager, create_access_token, verify_password, get_password_hash
from ..core.database import get_db as get_async_session
from ..models.user import User, UserSession, UserLoginLog, UserRole, UserStatus
from ..schemas.user import UserCreate, UserUpdate, UserResponse, TokenResponse, LoginRequest
from ..utils.exceptions import AuthenticationError, ValidationError, ConflictError
from ..utils.validators import UserValidator
from ..utils.formatters import format_api_response
from ..utils.helpers import generate_uuid, now, get_logger


logger = get_logger(__name__)


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.security = SecurityManager()
    
    async def register_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """
        用户注册
        
        Args:
            user_data: 用户注册数据
            
        Returns:
            注册结果
        """
        logger.info(f"用户注册请求: {user_data.username}")
        
        # 验证用户输入
        validation_errors = []
        
        # 验证用户名
        username_result = UserValidator.validate_username(user_data.username)
        if not username_result:
            validation_errors.append(username_result.error_message)
        
        # 验证邮箱
        if user_data.email:
            email_result = UserValidator.validate_email(user_data.email)
            if not email_result:
                validation_errors.append(email_result.error_message)
        
        # 验证手机号
        if user_data.phone:
            phone_result = UserValidator.validate_phone(user_data.phone)
            if not phone_result:
                validation_errors.append(phone_result.error_message)
        
        # 验证密码
        password_result = UserValidator.validate_password(user_data.password)
        if not password_result:
            validation_errors.append(password_result.error_message)
        
        if validation_errors:
            raise ValidationError(f"输入验证失败: {'; '.join(validation_errors)}")
        
        # 检查用户名是否已存在
        existing_user = await self._get_user_by_username(user_data.username)
        if existing_user:
            raise ConflictError("用户名已存在")
        
        # 检查邮箱是否已存在
        if user_data.email:
            existing_email = await self._get_user_by_email(user_data.email)
            if existing_email:
                raise ConflictError("邮箱已被注册")
        
        # 检查手机号是否已存在
        if user_data.phone:
            existing_phone = await self._get_user_by_phone(user_data.phone)
            if existing_phone:
                raise ConflictError("手机号已被注册")
        
        # 创建新用户
        hashed_password = get_password_hash(user_data.password)
        
        new_user = User(
            id=generate_uuid(),
            username=user_data.username,
            email=user_data.email,
            phone=user_data.phone,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=UserRole.USER,  # 默认角色
            status=UserStatus.ACTIVE,  # 默认激活（实际应用中可能需要邮箱验证）
            created_at=now(),
            last_login_at=None
        )
        
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        logger.info(f"用户注册成功: {new_user.username} (ID: {new_user.id})")
        
        # 返回用户信息（不包含密码）
        user_response = UserResponse.from_orm(new_user)
        return format_api_response(
            data=user_response.dict(),
            message="注册成功"
        )
    
    async def login_user(self, login_data: LoginRequest) -> Dict[str, Any]:
        """
        用户登录
        
        Args:
            login_data: 登录数据
            
        Returns:
            登录结果（包含访问令牌）
        """
        logger.info(f"用户登录请求: {login_data.username}")
        
        # 验证滑轨验证码（如果提供了验证令牌）
        if login_data.verification_token:
            from ..api.captcha import CaptchaStorage
            token_data = CaptchaStorage.get(f"verified:{login_data.verification_token}")
            if not token_data or not token_data.get("verified"):
                raise AuthenticationError("滑轨验证失败，请重新验证")
            # 验证成功后删除令牌（一次性使用）
            CaptchaStorage.remove(f"verified:{login_data.verification_token}")
        
        # 获取用户信息
        user = await self._get_user_by_username(login_data.username)
        if not user:
            raise AuthenticationError("用户名或密码错误")
        
        # 检查用户状态
        if user.status == UserStatus.INACTIVE:
            raise AuthenticationError("账户已被禁用")
        elif user.status == UserStatus.SUSPENDED:
            raise AuthenticationError("账户已被暂停")
        
        # 验证密码
        if not verify_password(login_data.password, user.hashed_password):
            # 记录失败的登录尝试
            await self._record_failed_login(user.id)
            raise AuthenticationError("用户名或密码错误")
        
        # 检查账户是否被锁定
        if await self._is_account_locked(user.id):
            raise AuthenticationError("账户已被锁定，请稍后再试")
        
        # 更新最后登录时间
        await self._update_last_login(user.id)
        
        # 生成访问令牌
        access_token = create_access_token(
            data={"sub": user.username, "user_id": str(user.id), "role": user.role.value}
        )
        
        # 清除失败的登录记录
        await self._clear_failed_logins(user.id)
        
        logger.info(f"用户登录成功: {user.username}")
        
        # 返回用户信息和令牌
        user_response = UserResponse.from_orm(user)
        return format_api_response(
            data={
                "user": user_response.dict(),
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            },
            message="登录成功"
        )
    
    async def logout_user(self, user_id: str) -> Dict[str, Any]:
        """
        用户登出
        
        Args:
            user_id: 用户ID
            
        Returns:
            登出结果
        """
        logger.info(f"用户登出: {user_id}")
        
        # 这里可以添加令牌黑名单逻辑
        # 目前简单返回成功消息
        
        return format_api_response(
            data=None,
            message="登出成功"
        )
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户资料
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户资料
        """
        user = await self._get_user_by_id(user_id)
        if not user:
            raise ValidationError("用户不存在")
        
        user_response = UserResponse.from_orm(user)
        return format_api_response(
            data=user_response.dict(),
            message="获取成功"
        )
    
    async def update_user_profile(self, user_id: str, update_data: UserUpdate) -> Dict[str, Any]:
        """
        更新用户资料
        
        Args:
            user_id: 用户ID
            update_data: 更新数据
            
        Returns:
            更新结果
        """
        logger.info(f"更新用户资料: {user_id}")
        
        user = await self._get_user_by_id(user_id)
        if not user:
            raise ValidationError("用户不存在")
        
        # 验证输入数据
        validation_errors = []
        
        if update_data.email and update_data.email != user.email:
            email_result = UserValidator.validate_email(update_data.email)
            if not email_result:
                validation_errors.append(email_result.error_message)
            else:
                # 检查邮箱是否已被其他用户使用
                existing_email = await self._get_user_by_email(update_data.email)
                if existing_email and existing_email.id != user.id:
                    validation_errors.append("邮箱已被其他用户使用")
        
        if update_data.phone and update_data.phone != user.phone:
            phone_result = UserValidator.validate_phone(update_data.phone)
            if not phone_result:
                validation_errors.append(phone_result.error_message)
            else:
                # 检查手机号是否已被其他用户使用
                existing_phone = await self._get_user_by_phone(update_data.phone)
                if existing_phone and existing_phone.id != user.id:
                    validation_errors.append("手机号已被其他用户使用")
        
        if validation_errors:
            raise ValidationError(f"输入验证失败: {'; '.join(validation_errors)}")
        
        # 更新用户信息
        update_fields = {}
        if update_data.email is not None:
            update_fields["email"] = update_data.email
        if update_data.phone is not None:
            update_fields["phone"] = update_data.phone
        if update_data.full_name is not None:
            update_fields["full_name"] = update_data.full_name
        if update_data.avatar_url is not None:
            update_fields["avatar_url"] = update_data.avatar_url
        
        if update_fields:
            update_fields["updated_at"] = now()
            
            stmt = update(User).where(User.id == user_id).values(**update_fields)
            await self.db.execute(stmt)
            await self.db.commit()
        
        # 获取更新后的用户信息
        updated_user = await self._get_user_by_id(user_id)
        user_response = UserResponse.from_orm(updated_user)
        
        logger.info(f"用户资料更新成功: {user_id}")
        
        return format_api_response(
            data=user_response.dict(),
            message="更新成功"
        )
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> Dict[str, Any]:
        """
        修改密码
        
        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            修改结果
        """
        logger.info(f"用户修改密码: {user_id}")
        
        user = await self._get_user_by_id(user_id)
        if not user:
            raise ValidationError("用户不存在")
        
        # 验证旧密码
        if not verify_password(old_password, user.hashed_password):
            raise AuthenticationError("旧密码错误")
        
        # 验证新密码
        password_result = UserValidator.validate_password(new_password)
        if not password_result:
            raise ValidationError(password_result.error_message)
        
        # 检查新密码是否与旧密码相同
        if verify_password(new_password, user.hashed_password):
            raise ValidationError("新密码不能与旧密码相同")
        
        # 更新密码
        new_hashed_password = get_password_hash(new_password)
        stmt = update(User).where(User.id == user_id).values(
            hashed_password=new_hashed_password,
            updated_at=now()
        )
        await self.db.execute(stmt)
        await self.db.commit()
        
        logger.info(f"用户密码修改成功: {user_id}")
        
        return format_api_response(
            data=None,
            message="密码修改成功"
        )
    
    async def reset_password(self, username: str, email: str) -> Dict[str, Any]:
        """
        重置密码
        
        Args:
            username: 用户名
            email: 邮箱
            
        Returns:
            重置结果
        """
        logger.info(f"密码重置请求: {username}")
        
        user = await self._get_user_by_username(username)
        if not user or user.email != email:
            # 为了安全，不暴露用户是否存在
            return format_api_response(
                data=None,
                message="如果用户存在，重置链接已发送到邮箱"
            )
        
        # 生成重置令牌（这里简化处理，实际应该发送邮件）
        reset_token = secrets.token_urlsafe(32)
        
        # 在实际应用中，应该：
        # 1. 将重置令牌存储到数据库（带过期时间）
        # 2. 发送包含重置链接的邮件
        # 3. 提供重置密码的API端点
        
        logger.info(f"密码重置令牌已生成: {username}")
        
        return format_api_response(
            data={"reset_token": reset_token},  # 仅用于演示，实际不应返回
            message="重置链接已发送到邮箱"
        )
    
    async def get_user_list(
        self, 
        page: int = 1, 
        page_size: int = 20,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取用户列表（管理员功能）
        
        Args:
            page: 页码
            page_size: 每页数量
            role: 角色筛选
            status: 状态筛选
            search: 搜索关键词
            
        Returns:
            用户列表
        """
        # 构建查询条件
        conditions = []
        
        if role:
            conditions.append(User.role == role)
        
        if status:
            conditions.append(User.status == status)
        
        if search:
            search_term = f"%{search}%"
            conditions.append(
                User.username.ilike(search_term) |
                User.full_name.ilike(search_term) |
                User.email.ilike(search_term)
            )
        
        # 构建查询
        stmt = select(User)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        # 计算总数
        count_stmt = select(User.id)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        
        total_result = await self.db.execute(count_stmt)
        total = len(total_result.all())
        
        # 分页查询
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size).order_by(User.created_at.desc())
        
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        # 转换为响应格式
        user_list = [UserResponse.from_orm(user).dict() for user in users]
        
        return format_api_response(
            data={
                "items": user_list,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            },
            message="获取成功"
        )
    
    # ==================== 私有方法 ====================
    
    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户"""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _get_user_by_phone(self, phone: str) -> Optional[User]:
        """根据手机号获取用户"""
        stmt = select(User).where(User.phone == phone)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def _update_last_login(self, user_id: str) -> None:
        """更新最后登录时间"""
        stmt = update(User).where(User.id == user_id).values(
            last_login_at=now(),
            updated_at=now()
        )
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def _record_failed_login(self, user_id: str) -> None:
        """记录失败的登录尝试"""
        # 这里可以实现失败登录记录逻辑
        # 例如存储到缓存或数据库中
        logger.warning(f"登录失败记录: {user_id}")
    
    async def _clear_failed_logins(self, user_id: str) -> None:
        """清除失败的登录记录"""
        # 清除失败登录记录
        logger.info(f"清除失败登录记录: {user_id}")
    
    async def _is_account_locked(self, user_id: str) -> bool:
        """检查账户是否被锁定"""
        # 这里可以实现账户锁定逻辑
        # 例如连续失败登录次数超过阈值时锁定账户
        return False