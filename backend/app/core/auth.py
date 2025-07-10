"""
认证和授权相关的依赖注入函数
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import verify_token
from app.models.user import User
from app.services.auth_service import AuthService

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """获取当前认证用户"""
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 暂时返回一个模拟用户对象，避免数据库依赖
    from app.models.user import User
    mock_user = User()
    mock_user.id = user_id
    mock_user.username = f"user_{user_id}"
    mock_user.email = f"user_{user_id}@example.com"
    mock_user.is_active = True
    mock_user.is_admin = False
    return mock_user

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前管理员用户"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """获取可选的当前用户（用于公开接口）"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        
        # 这里应该查询数据库获取用户，暂时返回None
        return None
    except JWTError:
        return None

# 供其他中间件使用的便捷函数
def get_user_from_token(token: str) -> Optional[User]:
    """通过JWT令牌获取用户(简化版本，不查询数据库)"""
    from jose import JWTError
    payload = verify_token(token)
    if not payload:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    # 构造模拟用户对象
    mock_user = User()
    mock_user.id = user_id
    mock_user.username = f"user_{user_id}"
    mock_user.email = f"user_{user_id}@example.com"
    mock_user.is_active = True
    mock_user.is_admin = False
    return mock_user 