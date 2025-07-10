"""
用户数据模式

定义用户相关的 Pydantic 模型，用于 API 请求和响应的数据验证
参考 easy_fastapi 的设计模式和最佳实践
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class UserRole(str, Enum):
    """用户角色枚举"""
    ADMIN = "admin"
    TRADER = "trader"
    VIEWER = "viewer"
    ANALYST = "analyst"


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


# 基础用户模型
class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: str = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$", description="手机号码")
    role: UserRole = Field(UserRole.VIEWER, description="用户角色")
    is_active: bool = Field(True, description="是否激活")
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v


# 用户创建模型
class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('两次密码输入不一致')
        return v
    
    @validator('password')
    def validate_password(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        return v


# 用户更新模型
class UserUpdate(BaseModel):
    """用户更新模型"""
    email: Optional[str] = None
    full_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, pattern=r"^1[3-9]\d{9}$")
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# 密码更新模型
class PasswordUpdate(BaseModel):
    """密码更新模型"""
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    confirm_new_password: str = Field(..., description="确认新密码")
    
    @validator('confirm_new_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次新密码输入不一致')
        return v


# 用户响应模型
class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    login_count: int = 0
    
    class Config:
        from_attributes = True


# 用户详情响应模型
class UserDetailResponse(UserResponse):
    """用户详情响应模型"""
    permissions: List[str] = []
    trading_permissions: Dict[str, bool] = {}
    risk_limits: Dict[str, Any] = {}


# 用户列表响应模型
class UserListResponse(BaseModel):
    """用户列表响应模型"""
    users: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# 认证相关模型
class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")
    verification_token: Optional[str] = Field(None, description="滑轨验证令牌")


class TokenResponse(BaseModel):
    """Token响应模型"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """刷新Token请求模型"""
    refresh_token: str = Field(..., description="刷新令牌")


class PasswordResetRequest(BaseModel):
    """密码重置请求模型"""
    email: str = Field(..., description="邮箱地址")


class PasswordResetConfirm(BaseModel):
    """密码重置确认模型"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次密码输入不一致')
        return v


# API密钥相关模型
class ApiKeyCreate(BaseModel):
    """API密钥创建模型"""
    name: str = Field(..., max_length=100, description="密钥名称")
    permissions: List[str] = Field(default_factory=list, description="权限列表")
    expires_at: Optional[datetime] = Field(None, description="过期时间")


class ApiKeyResponse(BaseModel):
    """API密钥响应模型"""
    id: int
    name: str
    key: str
    permissions: List[str]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 用户会话模型
class UserSessionResponse(BaseModel):
    """用户会话响应模型"""
    id: int
    session_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    expires_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


# 登录日志模型
class LoginLogResponse(BaseModel):
    """登录日志响应模型"""
    id: int
    user_id: int
    ip_address: str
    user_agent: str
    login_time: datetime
    logout_time: Optional[datetime] = None
    is_success: bool
    failure_reason: Optional[str] = None
    
    class Config:
        from_attributes = True


# 用户统计模型
class UserStatsResponse(BaseModel):
    """用户统计响应模型"""
    total_users: int
    active_users: int
    new_users_today: int
    new_users_this_week: int
    new_users_this_month: int
    role_distribution: Dict[str, int]
    login_stats: Dict[str, int]