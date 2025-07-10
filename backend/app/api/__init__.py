"""
API模块
提供所有API路由的统一入口
"""
from fastapi import APIRouter
from .v1 import api_router as v1_router

# 创建主API路由器
api_router = APIRouter()

# 注册v1版本API，统一加 /api 前缀
api_router.include_router(v1_router, prefix="/api")

__all__ = ["api_router"]