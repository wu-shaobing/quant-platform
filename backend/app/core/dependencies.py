# 依赖注入
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db as get_async_session
from app.core.security import security, security_manager, permission_checker
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.market_service import MarketService


# 数据库会话依赖
async def get_db() -> Generator[AsyncSession, None, None]:
    """获取数据库会话依赖"""
    async with get_async_session() as session:
        yield session


# 认证服务依赖
def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db)


# 行情服务依赖
def get_market_service(db: AsyncSession = Depends(get_db)) -> MarketService:
    """获取行情服务实例"""
    return MarketService(db)


# 当前用户依赖
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """获取当前认证用户"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 验证令牌
        payload = security_manager.verify_token(credentials.credentials)
        if payload is None:
            raise credentials_exception
        
        # 检查令牌类型
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的令牌类型",
            )
        
        # 获取用户ID
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # 从数据库获取用户
        user = await auth_service.get_user_by_id(db, user_id)
        if user is None:
            raise credentials_exception
        
        # 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户账户已禁用",
            )
        
        return user
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise credentials_exception


# 活跃用户依赖
async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户账户已禁用"
        )
    return current_user


# 管理员用户依赖
async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前管理员用户"""
    if not permission_checker.is_admin(current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：需要管理员权限"
        )
    return current_user


# 交易员用户依赖
async def get_current_trader_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前交易员用户"""
    if not permission_checker.is_trader(current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：需要交易员权限"
        )
    return current_user


# 超级管理员用户依赖
async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前超级管理员用户"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足：需要超级管理员权限"
        )
    return current_user


# 权限检查依赖工厂
def require_permission(permission: str):
    """创建权限检查依赖"""
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not permission_checker.check_permission(current_user.permissions, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {permission} 权限"
            )
        return current_user
    
    return permission_dependency


# 角色检查依赖工厂
def require_role(role: str):
    """创建角色检查依赖"""
    async def role_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not permission_checker.check_role(current_user.roles, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要 {role} 角色"
            )
        return current_user
    
    return role_dependency


# 多权限检查依赖工厂
def require_any_permission(*permissions: str):
    """创建多权限检查依赖（满足任一权限即可）"""
    async def permission_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not any(
            permission_checker.check_permission(current_user.permissions, perm) 
            for perm in permissions
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要以下权限之一：{', '.join(permissions)}"
            )
        return current_user
    
    return permission_dependency


# 多角色检查依赖工厂
def require_any_role(*roles: str):
    """创建多角色检查依赖（满足任一角色即可）"""
    async def role_dependency(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        if not any(
            permission_checker.check_role(current_user.roles, role) 
            for role in roles
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足：需要以下角色之一：{', '.join(roles)}"
            )
        return current_user
    
    return role_dependency


# 可选用户依赖（不强制认证）
async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """获取当前用户（可选，不强制认证）"""
    
    if not credentials:
        return None
    
    try:
        # 验证令牌
        payload = security_manager.verify_token(credentials.credentials)
        if payload is None:
            return None
        
        # 获取用户ID
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        # 从数据库获取用户
        user = await auth_service.get_user_by_id(db, user_id)
        if user is None or not user.is_active:
            return None
        
        return user
        
    except Exception:
        return None


# 分页参数依赖
class PaginationParams:
    """分页参数"""
    
    def __init__(
        self,
        page: int = 1,
        size: int = 20,
        max_size: int = 100
    ):
        self.page = max(1, page)
        self.size = min(max_size, max(1, size))
        self.offset = (self.page - 1) * self.size
        self.limit = self.size


def get_pagination_params(
    page: int = 1,
    size: int = 20
) -> PaginationParams:
    """获取分页参数依赖"""
    return PaginationParams(page=page, size=size)


# 排序参数依赖
class SortParams:
    """排序参数"""
    
    def __init__(
        self,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()
        
        # 验证排序顺序
        if self.sort_order not in ["asc", "desc"]:
            self.sort_order = "desc"


def get_sort_params(
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> SortParams:
    """获取排序参数依赖"""
    return SortParams(sort_by=sort_by, sort_order=sort_order)


# API密钥认证依赖
async def get_user_by_api_key(
    api_key: str,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> User:
    """通过API密钥获取用户"""
    
    user = await auth_service.get_user_by_api_key(db, api_key)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户账户已禁用"
        )
    
    return user


# 限流依赖（占位符，实际实现需要Redis）
class RateLimiter:
    """限流器"""
    
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
    
    async def __call__(self, request):
        # 这里应该实现基于Redis的限流逻辑
        # 暂时返回True，表示不限流
        return True


def rate_limit(calls: int = 100, period: int = 60):
    """创建限流依赖"""
    return RateLimiter(calls=calls, period=period)


# WebSocket认证依赖
async def get_current_user_from_websocket(
    websocket,
    db: AsyncSession = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[User]:
    """从WebSocket获取当前用户"""
    try:
        # 从查询参数或头部获取token
        token = None

        # 尝试从查询参数获取
        if hasattr(websocket, 'query_params') and 'token' in websocket.query_params:
            token = websocket.query_params['token']

        # 尝试从头部获取
        elif hasattr(websocket, 'headers') and 'authorization' in websocket.headers:
            auth_header = websocket.headers['authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]

        if not token:
            return None

        # 验证令牌
        payload = security_manager.verify_token(token)
        if payload is None:
            return None

        # 获取用户ID
        user_id = payload.get("sub")
        if user_id is None:
            return None

        # 从数据库获取用户
        user = await auth_service.get_user_by_id(db, user_id)
        if user is None or not user.is_active:
            return None

        return user

    except Exception:
        return None


# 导出主要组件
__all__ = [
    "get_db",
    "get_auth_service",
    "get_market_service",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "get_current_trader_user",
    "get_current_superuser",
    "get_current_user_optional",
    "get_current_user_from_websocket",
    "require_permission",
    "require_role",
    "require_any_permission",
    "require_any_role",
    "get_pagination_params",
    "get_sort_params",
    "get_user_by_api_key",
    "rate_limit",
    "PaginationParams",
    "SortParams",
]