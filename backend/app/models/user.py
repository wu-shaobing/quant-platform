"""
用户模型
包含用户基本信息、认证信息、权限管理等
"""
import uuid
from datetime import datetime
from typing import Optional, List
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Table, JSON
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.types import GUID


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"          # 管理员
    TRADER = "trader"        # 交易员
    ANALYST = "analyst"      # 分析师
    VIEWER = "viewer"        # 只读用户


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"        # 激活
    INACTIVE = "inactive"    # 未激活
    SUSPENDED = "suspended"  # 暂停
    DELETED = "deleted"      # 已删除


# 用户角色关联表
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

# 角色权限关联表
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # 基本信息
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 个人信息
    full_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 安全信息
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 双因素认证
    totp_secret: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    backup_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON格式存储
    
    # 配置信息
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # 关联关系
    roles: Mapped[List["Role"]] = relationship(
        "Role", 
        secondary=user_roles, 
        back_populates="users",
        lazy="selectin"
    )
    
    api_keys: Mapped[List["ApiKey"]] = relationship(
        "ApiKey", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    @property
    def permissions(self) -> List[str]:
        """获取用户所有权限"""
        perms = []
        for role in self.roles:
            perms.extend([perm.name for perm in role.permissions])
        return list(set(perms))  # 去重
    
    @property
    def role_names(self) -> List[str]:
        """获取用户角色名称列表"""
        return [role.name for role in self.roles]
    
    def has_permission(self, permission: str) -> bool:
        """检查用户是否有指定权限"""
        return permission in self.permissions
    
    def has_role(self, role: str) -> bool:
        """检查用户是否有指定角色"""
        return role in self.role_names
    
    def is_locked(self) -> bool:
        """检查账户是否被锁定"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"


class Role(Base):
    """角色模型"""
    __tablename__ = "roles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 系统角色不可删除
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    users: Mapped[List[User]] = relationship(
        "User", 
        secondary=user_roles, 
        back_populates="roles"
    )
    
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin"
    )
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}', display_name='{self.display_name}')>"


class Permission(Base):
    """权限模型"""
    __tablename__ = "permissions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource: Mapped[str] = mapped_column(String(50), nullable=False)  # 资源类型：user, trading, strategy等
    action: Mapped[str] = mapped_column(String(50), nullable=False)    # 操作类型：read, write, execute等
    
    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # 系统权限不可删除
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    roles: Mapped[List[Role]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions"
    )
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}', resource='{self.resource}', action='{self.action}')>"


class ApiKey(Base):
    """API密钥模型"""
    __tablename__ = "api_keys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 密钥信息
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(10), nullable=False)  # 用于显示的前缀
    
    # 权限和限制
    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # 特定权限
    ip_whitelist: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)  # IP白名单
    rate_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 每分钟请求限制
    
    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # 关联关系
    user: Mapped[User] = relationship("User", back_populates="api_keys")
    
    def is_expired(self) -> bool:
        """检查API密钥是否已过期"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, name='{self.name}', user_id={self.user_id})>"


class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 会话信息
    session_token: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
    
    # 设备信息
    device_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # web, mobile, desktop
    device_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)  # IPv6支持
    
    # 地理位置信息
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 状态信息
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # 关联关系
    user: Mapped[User] = relationship("User", back_populates="sessions")
    
    def is_expired(self) -> bool:
        """检查会话是否已过期"""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, device_type='{self.device_type}')>"


class UserLoginLog(Base):
    """用户登录日志模型"""
    __tablename__ = "user_login_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # 登录信息
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    login_type: Mapped[str] = mapped_column(String(20), nullable=False)  # password, api_key, oauth
    status: Mapped[str] = mapped_column(String(20), nullable=False)      # success, failed, blocked
    failure_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 设备和网络信息
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_fingerprint: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # 地理位置信息
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # 时间信息
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    user: Mapped[Optional[User]] = relationship("User")
    
    def __repr__(self):
        return f"<UserLoginLog(id={self.id}, username='{self.username}', status='{self.status}')>"


# 导出所有模型
__all__ = [
    "User",
    "Role", 
    "Permission",
    "ApiKey",
    "UserSession",
    "UserLoginLog",
    "user_roles",
    "role_permissions",
]