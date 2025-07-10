"""
认证相关API路由
提供用户登录、注册、令牌管理等功能
"""
from datetime import timedelta
from typing import List, Optional
import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    require_permission
)
from app.core.security import SecurityManager
from app.models.user import User, ApiKey
from app.schemas.user import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserCreate,
    UserResponse,
    UserUpdate,
    PasswordUpdate,
    PasswordResetRequest,
    PasswordResetConfirm,
    ApiKeyCreate,
    ApiKeyResponse,
    UserSessionResponse,
    LoginLogResponse,
    UserStatsResponse,
)
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.core.cache import get_redis

router = APIRouter(prefix="/auth", tags=["认证"])
security = HTTPBearer()
settings = get_settings()


def get_client_ip(request: Request) -> str:
    """获取客户端真实IP地址"""
    # 检查代理头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For 可能包含多个IP，取第一个
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 检查Cloudflare头
    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        return cf_connecting_ip
    
    # 最后使用客户端IP
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """获取用户代理字符串"""
    return request.headers.get("User-Agent", "Unknown")


async def is_token_blacklisted(token: str) -> bool:
    """检查令牌是否在黑名单中"""
    redis = await get_redis()
    if redis:
        return await redis.exists(f"blacklist:token:{token}")
    return False


async def blacklist_token(token: str, expires_in: int = 3600) -> None:
    """将令牌加入黑名单"""
    redis = await get_redis()
    if redis:
        await redis.setex(f"blacklist:token:{token}", expires_in, "1")


@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户登录接口
    
    - **username**: 用户名或邮箱
    - **password**: 密码
    - **remember_me**: 是否记住登录状态（影响token过期时间）
    """
    auth_service = AuthService(db)
    
    # 验证用户凭据
    user = await auth_service.authenticate_user(
        username=login_data.username,
        password=login_data.password
    )
    
    if not user:
        # 记录失败的登录尝试
        await auth_service.create_login_log(
            user_id=None,
            username=login_data.username,
            success=False,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            failure_reason="Invalid credentials"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        await auth_service.create_login_log(
            user_id=user.id,
            username=login_data.username,
            success=False,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            failure_reason="Account disabled"
        )
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="账户已被禁用"
        )
    
    # 创建访问令牌
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES * (7 if login_data.remember_me else 1)
    )
    
    security_manager = SecurityManager()
    access_token = security_manager.create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    refresh_token = security_manager.create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    # 记录成功登录日志
    await auth_service.create_login_log(
        user_id=user.id,
        username=login_data.username,
        success=True,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request)
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        user_id=user.id,
        username=user.username
    )


@router.post("/refresh", response_model=TokenResponse, summary="刷新令牌")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    刷新访问令牌
    
    - **refresh_token**: 刷新令牌
    """
    # 检查令牌是否在黑名单中
    if await is_token_blacklisted(refresh_data.refresh_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已失效"
        )
    
    security_manager = SecurityManager()
    
    try:
        payload = security_manager.verify_token(refresh_data.refresh_token)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        auth_service = AuthService(db)
        user = await auth_service.get_user_by_id(int(user_id))
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用"
            )
        
        # 创建新的访问令牌
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security_manager.create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds()),
            user_id=user.id,
            username=user.username
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="刷新令牌无效或已过期"
        )


@router.post("/register", response_model=UserResponse, status_code=201, summary="用户注册")
async def register_user(
    user_in: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    用户注册接口
    
    - **username**: 用户名（唯一）
    - **email**: 邮箱地址（唯一）
    - **password**: 密码
    - **full_name**: 全名（可选）
    """
    auth_service = AuthService(db)
    
    # 检查用户名是否已存在
    existing_user = await auth_service.get_user_by_username(user_in.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    existing_email = await auth_service.get_user_by_email(user_in.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )
    
    # 创建用户
    user = await auth_service.create_user(user_in)
    
    # 发送欢迎邮件
    try:
        email_service = EmailService()
        await email_service.send_welcome_email(user.email, user.username)
    except Exception as e:
        # 邮件发送失败不影响注册流程
        print(f"发送欢迎邮件失败: {e}")
    
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前登录用户的详细信息
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse, summary="更新当前用户信息")
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新当前用户的基本信息
    
    - **full_name**: 全名
    - **email**: 邮箱地址
    - **phone**: 电话号码
    """
    auth_service = AuthService(db)
    
    # 如果要更新邮箱，检查新邮箱是否已被使用
    if user_update.email and user_update.email != current_user.email:
        existing_email = await auth_service.get_user_by_email(user_update.email)
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
    
    updated_user = await auth_service.update_user(current_user.id, user_update)
    return UserResponse.model_validate(updated_user)


@router.post("/change-password", summary="修改密码")
async def change_password(
    password_data: PasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改当前用户密码
    
    - **current_password**: 当前密码
    - **new_password**: 新密码
    """
    auth_service = AuthService(db)
    
    # 验证当前密码
    security_manager = SecurityManager()
    if not security_manager.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前密码错误"
        )
    
    # 更新密码
    await auth_service.update_password(current_user.id, password_data.new_password)
    
    return {"message": "密码修改成功"}


@router.post("/forgot-password", summary="忘记密码")
async def forgot_password(
    request_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    发送密码重置邮件
    
    - **email**: 注册邮箱地址
    """
    auth_service = AuthService(db)
    email_service = EmailService()
    
    user = await auth_service.get_user_by_email(request_data.email)
    if not user:
        # 为了安全，即使用户不存在也返回成功消息
        return {"message": "如果邮箱存在，重置链接已发送"}
    
    # 生成重置令牌
    security_manager = SecurityManager()
    reset_token = security_manager.create_password_reset_token(user.email)
    
    # 存储重置令牌到Redis（15分钟有效期）
    redis = await get_redis()
    if redis:
        await redis.setex(f"reset_token:{reset_token}", 900, user.email)
    
    # 发送重置邮件
    try:
        await email_service.send_password_reset_email(user.email, reset_token)
    except Exception as e:
        print(f"发送重置邮件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送重置邮件失败，请稍后重试"
        )
    
    return {"message": "重置链接已发送到您的邮箱"}


@router.post("/reset-password", summary="重置密码")
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
):
    """
    通过重置令牌重置密码
    
    - **token**: 密码重置令牌
    - **new_password**: 新密码
    """
    # 验证重置令牌
    redis = await get_redis()
    if not redis:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务暂时不可用"
        )
    
    email = await redis.get(f"reset_token:{reset_data.token}")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="重置令牌无效或已过期"
        )
    
    email = email.decode('utf-8')
    
    # 获取用户
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新密码
    await auth_service.update_password(user.id, reset_data.new_password)
    
    # 删除已使用的重置令牌
    await redis.delete(f"reset_token:{reset_data.token}")
    
    # 发送密码重置成功通知邮件
    try:
        email_service = EmailService()
        await email_service.send_password_reset_success_email(user.email)
    except Exception as e:
        print(f"发送通知邮件失败: {e}")
    
    return {"message": "密码重置成功"}


@router.post("/logout", summary="用户登出")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    用户登出（将当前令牌加入黑名单）
    """
    # 从请求头获取令牌
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        # 将令牌加入黑名单，有效期设置为令牌的剩余有效期
        await blacklist_token(token, expires_in=3600)  # 1小时
    
    return {"message": "登出成功"}


# API密钥管理
@router.post("/api-keys", response_model=ApiKeyResponse, summary="创建API密钥")
async def create_api_key(
    api_key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    为当前用户创建API密钥
    
    - **name**: API密钥名称
    - **permissions**: 权限列表
    - **expires_at**: 过期时间（可选）
    """
    auth_service = AuthService(db)
    api_key = await auth_service.create_api_key(current_user.id, api_key_data)
    
    return ApiKeyResponse.model_validate(api_key)


@router.get("/api-keys", response_model=List[ApiKeyResponse], summary="获取API密钥列表")
async def get_api_keys(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的所有API密钥
    """
    auth_service = AuthService(db)
    api_keys = await auth_service.get_user_api_keys(current_user.id)
    
    return [ApiKeyResponse.model_validate(key) for key in api_keys]


@router.delete("/api-keys/{key_id}", summary="删除API密钥")
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除指定的API密钥
    """
    auth_service = AuthService(db)
    
    # 验证API密钥是否属于当前用户
    api_key = await auth_service.get_api_key_by_id(key_id)
    if not api_key or api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API密钥不存在"
        )
    
    await auth_service.delete_api_key(key_id)
    return {"message": "API密钥删除成功"}


# 管理员功能
@router.get("/users", response_model=List[UserResponse], summary="获取用户列表")
async def get_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取所有用户列表（管理员权限）
    """
    auth_service = AuthService(db)
    users = await auth_service.get_users(skip=skip, limit=limit)
    
    return [UserResponse.model_validate(user) for user in users]


@router.get("/users/{user_id}", response_model=UserResponse, summary="获取用户详情")
async def get_user(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定用户的详细信息（管理员权限）
    """
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}/status", summary="更新用户状态")
async def update_user_status(
    user_id: int,
    is_active: bool,
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    启用或禁用用户账户（管理员权限）
    """
    auth_service = AuthService(db)
    user = await auth_service.get_user_by_id(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    await auth_service.update_user_status(user_id, is_active)
    return {"message": f"用户状态已更新为{'激活' if is_active else '禁用'}"}


@router.get("/stats", response_model=UserStatsResponse, summary="获取用户统计")
async def get_user_stats(
    admin_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户统计信息，仅管理员可访问。
    """
    auth_service = AuthService(db)
    stats = await auth_service.get_user_statistics()
    
    return UserStatsResponse.model_validate(stats)


@router.get("/health", summary="健康检查")
async def health_check():
    """
    认证服务健康检查
    """
    return {
        "status": "healthy",
        "service": "auth",
        "timestamp": "2024-01-01T00:00:00Z"
    }


# 新增：验证码路由
# @router.get("/captcha", summary="获取图片验证码")
# async def get_image_captcha():
#     """
#     生成并返回一个图片验证码。
#     """
#     # 生成随机字符串
#     char_set = string.ascii_uppercase + string.digits
#     captcha_text = "".join(random.sample(char_set, 4))
#     
#     # 生成图片
#     image = ImageCaptcha()
#     img_data = image.generate(captcha_text)
#     
#     # 将图片转为 base64
#     img_base64 = base64.b64encode(img_data.read()).decode('utf-8')
#     
#     # 简单地将验证码文本存储在内存中（生产环境应使用Redis）
#     # 这里我们用一个简化方式，实际项目需要一个更健壮的存储
#     # 为了演示，我们将验证码文本直接返回，这在生产中是不安全的
#     # 一个更好的做法是返回一个captcha_id，并将(id, text)存入Redis
#     
#     return {
#         "captcha_id": "dummy-id-" + "".join(random.sample(string.ascii_lowercase, 6)),
#         "image_base64": "data:image/png;base64," + img_base64,
#         # 警告：仅为演示，生产不应返回
#         "captcha_text": captcha_text 
#     }