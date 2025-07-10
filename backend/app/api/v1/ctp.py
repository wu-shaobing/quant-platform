"""
CTP交易接口API
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.ctp_service import ctp_service, ctp_market_service
from app.services.risk_service import RiskService
from app.schemas.trading import OrderRequest, OrderResponse
from app.core.websocket import websocket_manager
from app.core.ctp_config import CTPStatus
from app.core.performance_optimizer import performance_optimizer
from app.core.security_hardening import (
    security_hardening,
    jwt_security_manager,
    advanced_encryption,
    AuditEvent,
    AuditEventType,
    SecurityLevel
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ctp", tags=["CTP交易接口"])


@router.get("/status", summary="获取CTP连接状态")
async def get_ctp_status(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    获取CTP连接状态
    
    返回交易和行情连接状态、登录状态、错误信息等
    """
    try:
        status = ctp_service.get_status()
        return {
            "success": True,
            "data": {
                "trade_connected": status.trade_connected,
                "md_connected": status.md_connected,
                "trade_logged_in": status.trade_logged_in,
                "md_logged_in": status.md_logged_in,
                "is_ready": status.is_ready,
                "trade_ready": status.trade_ready,
                "md_ready": status.md_ready,
                "trade_connect_time": status.trade_connect_time,
                "md_connect_time": status.md_connect_time,
                "trade_login_time": status.trade_login_time,
                "md_login_time": status.md_login_time,
                "last_error": status.last_error,
                "error_count": status.error_count,
                "order_count": status.order_count,
                "trade_count": status.trade_count,
                "subscribe_count": status.subscribe_count
            }
        }
    except Exception as e:
        logger.error(f"获取CTP状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取CTP状态失败: {str(e)}"
        )


@router.post("/initialize", summary="初始化CTP连接")
async def initialize_ctp(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    初始化CTP连接
    
    连接交易和行情服务器，完成登录认证
    """
    try:
        # 检查用户权限（可以添加管理员权限检查）
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户未激活"
            )
        
        # 初始化CTP连接
        success = await ctp_service.initialize()
        
        if success:
            return {
                "success": True,
                "message": "CTP连接初始化成功",
                "data": ctp_service.get_status().dict()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="CTP连接初始化失败"
            )
            
    except Exception as e:
        logger.error(f"初始化CTP连接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"初始化CTP连接失败: {str(e)}"
        )


@router.post("/disconnect", summary="断开CTP连接")
async def disconnect_ctp(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    断开CTP连接
    """
    try:
        await ctp_service.disconnect()
        return {
            "success": True,
            "message": "CTP连接已断开"
        }
    except Exception as e:
        logger.error(f"断开CTP连接失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"断开CTP连接失败: {str(e)}"
        )


@router.post("/reconnect", summary="重新连接CTP")
async def reconnect_ctp(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    重新连接CTP
    """
    try:
        success = await ctp_service.reconnect()
        
        if success:
            return {
                "success": True,
                "message": "CTP重新连接成功",
                "data": ctp_service.get_status().dict()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="CTP重新连接失败"
            )
            
    except Exception as e:
        logger.error(f"重新连接CTP失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重新连接CTP失败: {str(e)}"
        )


@router.post("/orders", response_model=OrderResponse, summary="提交CTP订单")
async def submit_ctp_order(
    order_request: OrderRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    """
    通过CTP接口提交订单
    
    - **symbol**: 合约代码
    - **direction**: 交易方向（BUY/SELL）
    - **offset**: 开平标志（OPEN/CLOSE/CLOSE_TODAY/CLOSE_YESTERDAY）
    - **order_type**: 订单类型（LIMIT/MARKET）
    - **volume**: 交易数量
    - **price**: 价格（限价单必填）
    """
    try:
        # 风险检查
        risk_service = RiskService(db)
        risk_check = await risk_service.check_order_risk(
            user_id=current_user.id,
            order_request=order_request
        )
        
        if not risk_check.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"风险检查失败: {risk_check.message}"
            )
        
        # 提交订单到CTP
        order_response = await ctp_service.submit_order(order_request, current_user.id)
        
        # 通过WebSocket推送订单更新
        await websocket_manager.broadcast_to_user(
            current_user.id,
            {
                "type": "order_update",
                "data": order_response.data
            }
        )
        
        return order_response
        
    except Exception as e:
        logger.error(f"提交CTP订单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交订单失败: {str(e)}"
        )


@router.delete("/orders/{order_ref}", summary="撤销CTP订单")
async def cancel_ctp_order(
    order_ref: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    撤销CTP订单
    
    - **order_ref**: 报单引用
    """
    try:
        success = await ctp_service.cancel_order(order_ref, current_user.id)
        
        if success:
            # 通过WebSocket推送订单更新
            await websocket_manager.broadcast_to_user(
                current_user.id,
                {
                    "type": "order_cancelled",
                    "data": {"order_ref": order_ref}
                }
            )
            
            return {
                "success": True,
                "message": f"订单 {order_ref} 撤销成功"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"订单 {order_ref} 撤销失败"
            )
            
    except Exception as e:
        logger.error(f"撤销CTP订单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"撤销订单失败: {str(e)}"
        )


@router.get("/orders", summary="查询CTP订单")
async def query_ctp_orders(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    查询用户的CTP订单
    """
    try:
        orders = await ctp_service.query_orders(current_user.id)
        return {
            "success": True,
            "data": orders,
            "count": len(orders)
        }
    except Exception as e:
        logger.error(f"查询CTP订单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询订单失败: {str(e)}"
        )


@router.get("/trades", summary="查询CTP成交")
async def query_ctp_trades(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    查询用户的CTP成交记录
    """
    try:
        trades = await ctp_service.query_trades(current_user.id)
        return {
            "success": True,
            "data": trades,
            "count": len(trades)
        }
    except Exception as e:
        logger.error(f"查询CTP成交失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询成交失败: {str(e)}"
        )


@router.get("/positions", summary="查询CTP持仓")
async def query_ctp_positions(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    查询用户的CTP持仓
    """
    try:
        positions = await ctp_service.query_positions(current_user.id)
        return {
            "success": True,
            "data": positions,
            "count": len(positions)
        }
    except Exception as e:
        logger.error(f"查询CTP持仓失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询持仓失败: {str(e)}"
        )


@router.get("/account", summary="查询CTP账户")
async def query_ctp_account(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    查询用户的CTP账户资金
    """
    try:
        account = await ctp_service.query_account(current_user.id)
        return {
            "success": True,
            "data": account
        }
    except Exception as e:
        logger.error(f"查询CTP账户失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询账户失败: {str(e)}"
        )


@router.post("/market/subscribe", summary="订阅行情数据")
async def subscribe_market_data(
    symbols: List[str],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    订阅行情数据
    
    - **symbols**: 合约代码列表
    """
    try:
        success = await ctp_service.subscribe_market_data(symbols)
        
        if success:
            return {
                "success": True,
                "message": f"订阅行情成功: {symbols}",
                "data": {"symbols": symbols}
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="订阅行情失败"
            )
            
    except Exception as e:
        logger.error(f"订阅行情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"订阅行情失败: {str(e)}"
        )


@router.post("/market/unsubscribe", summary="取消订阅行情数据")
async def unsubscribe_market_data(
    symbols: List[str],
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    取消订阅行情数据
    
    - **symbols**: 合约代码列表
    """
    try:
        success = await ctp_service.unsubscribe_market_data(symbols)
        
        if success:
            return {
                "success": True,
                "message": f"取消订阅行情成功: {symbols}",
                "data": {"symbols": symbols}
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="取消订阅行情失败"
            )
            
    except Exception as e:
        logger.error(f"取消订阅行情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"取消订阅行情失败: {str(e)}"
        )


@router.get("/market/tick/{symbol}", summary="获取最新行情")
async def get_tick_data(
    symbol: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    获取指定合约的最新行情数据
    
    - **symbol**: 合约代码
    """
    try:
        tick_data = await ctp_service.get_tick_data(symbol)
        
        if tick_data:
            return {
                "success": True,
                "data": tick_data
            }
        else:
            return {
                "success": False,
                "message": f"未找到合约 {symbol} 的行情数据",
                "data": None
            }
            
    except Exception as e:
        logger.error(f"获取行情数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取行情数据失败: {str(e)}"
        )


@router.post("/performance/optimize", summary="执行CTP性能优化")
async def optimize_ctp_performance(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    执行CTP性能优化

    包括数据库查询优化、缓存预热、索引创建等
    """
    try:
        # 检查用户权限（只有管理员可以执行优化）
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以执行性能优化"
            )

        # 执行数据库查询优化
        await performance_optimizer.optimize_database_queries(db)

        # 预热缓存
        await performance_optimizer.warm_cache()

        # 启动性能监控
        await performance_optimizer.start_monitoring()

        logger.info(f"用户 {current_user.username} 执行了CTP性能优化")

        return {
            "success": True,
            "message": "CTP性能优化执行成功",
            "optimizations": [
                "数据库索引优化",
                "缓存预热",
                "性能监控启动"
            ]
        }

    except Exception as e:
        logger.error(f"CTP性能优化失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"性能优化失败: {str(e)}"
        )


@router.get("/performance/report", summary="获取CTP性能报告")
async def get_ctp_performance_report(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    获取CTP性能报告

    包括查询统计、缓存命中率、系统资源使用情况等
    """
    try:
        # 获取优化报告
        report = await performance_optimizer.get_optimization_report()

        return {
            "success": True,
            "message": "性能报告获取成功",
            "data": report
        }

    except Exception as e:
        logger.error(f"获取性能报告失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取性能报告失败: {str(e)}"
        )


@router.get("/performance/metrics", summary="获取实时性能指标")
async def get_ctp_performance_metrics(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    获取实时性能指标

    包括延迟统计、吞吐量、资源使用率等
    """
    try:
        # 获取性能报告
        performance_report = performance_optimizer.get_performance_report()

        # 获取查询统计
        query_stats = performance_optimizer.db_optimizer.get_query_statistics()

        return {
            "success": True,
            "message": "实时性能指标获取成功",
            "data": {
                "performance_metrics": performance_report,
                "query_statistics": query_stats,
                "timestamp": performance_report.get("current_metrics", {}).get("timestamp", "")
            }
        }

    except Exception as e:
        logger.error(f"获取实时性能指标失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取实时性能指标失败: {str(e)}"
        )


@router.post("/performance/cache/warm", summary="预热缓存")
async def warm_ctp_cache(
    symbols: List[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    预热CTP缓存

    为指定合约或热门合约预热缓存数据
    """
    try:
        # 如果没有指定合约，使用默认热门合约
        if not symbols:
            symbols = ['rb2501', 'i2501', 'hc2501', 'j2501']

        # 预热缓存
        await performance_optimizer.warm_cache()

        logger.info(f"用户 {current_user.username} 预热了缓存，合约: {symbols}")

        return {
            "success": True,
            "message": f"缓存预热成功，预热了 {len(symbols)} 个合约",
            "symbols": symbols
        }

    except Exception as e:
        logger.error(f"缓存预热失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"缓存预热失败: {str(e)}"
        )


# ==================== 安全加固API端点 ====================

@router.post("/security/token/refresh", summary="安全刷新令牌")
async def refresh_security_token(
    refresh_token: str,
    device_fingerprint: str = None,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """安全刷新JWT令牌"""
    try:
        # 使用JWT安全管理器刷新令牌
        success, result = await jwt_security_manager.refresh_token_security(
            refresh_token, device_fingerprint
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.get("error", "Token refresh failed")
            )

        # 记录审计日志
        await security_hardening.audit_logger.log_event(AuditEvent(
            event_type=AuditEventType.LOGIN,
            user_id=current_user.id,
            ip_address="unknown",  # 在中间件中会被更新
            user_agent="API",
            endpoint="/api/v1/ctp/security/token/refresh",
            method="POST",
            request_data={"device_fingerprint": device_fingerprint},
            response_status=200,
            risk_level=SecurityLevel.MEDIUM
        ))

        return {
            "status": "success",
            "message": "令牌刷新成功",
            "tokens": result
        }

    except Exception as e:
        logger.error(f"令牌刷新失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失败: {str(e)}"
        )


@router.post("/security/token/revoke", summary="撤销令牌")
async def revoke_security_token(
    token: str = None,
    revoke_all: bool = False,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """撤销JWT令牌"""
    try:
        if revoke_all:
            # 撤销用户的所有令牌
            await jwt_security_manager.revoke_user_tokens(current_user.id)
            message = "所有令牌已撤销"
        else:
            # 撤销指定令牌
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="必须提供token或设置revoke_all=true"
                )
            await jwt_security_manager.revoke_token(token)
            message = "令牌已撤销"

        # 记录审计日志
        await security_hardening.audit_logger.log_event(AuditEvent(
            event_type=AuditEventType.LOGOUT,
            user_id=current_user.id,
            ip_address="unknown",
            user_agent="API",
            endpoint="/api/v1/ctp/security/token/revoke",
            method="POST",
            request_data={"revoke_all": revoke_all},
            response_status=200,
            risk_level=SecurityLevel.MEDIUM
        ))

        return {
            "status": "success",
            "message": message
        }

    except Exception as e:
        logger.error(f"令牌撤销失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌撤销失败: {str(e)}"
        )


@router.get("/security/audit/events", summary="查询审计事件")
async def get_audit_events(
    start_date: str = None,
    end_date: str = None,
    event_type: str = None,
    risk_level: str = None,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """查询审计事件"""
    try:
        from datetime import datetime, timedelta

        # 解析日期参数
        if start_date:
            start_dt = datetime.fromisoformat(start_date)
        else:
            start_dt = datetime.now() - timedelta(days=7)  # 默认查询最近7天

        if end_date:
            end_dt = datetime.fromisoformat(end_date)
        else:
            end_dt = datetime.now()

        # 解析枚举参数
        event_type_enum = None
        if event_type:
            try:
                event_type_enum = AuditEventType(event_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的事件类型: {event_type}"
                )

        risk_level_enum = None
        if risk_level:
            try:
                risk_level_enum = SecurityLevel(risk_level)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"无效的风险级别: {risk_level}"
                )

        # 查询审计事件
        events = await security_hardening.audit_logger.query_events(
            start_date=start_dt,
            end_date=end_dt,
            event_type=event_type_enum,
            user_id=current_user.id,  # 只查询当前用户的事件
            risk_level=risk_level_enum
        )

        # 限制返回数量
        events = events[:limit]

        return {
            "status": "success",
            "events": events,
            "total": len(events),
            "query_params": {
                "start_date": start_dt.isoformat(),
                "end_date": end_dt.isoformat(),
                "event_type": event_type,
                "risk_level": risk_level,
                "limit": limit
            }
        }

    except Exception as e:
        logger.error(f"查询审计事件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询审计事件失败: {str(e)}"
        )


@router.post("/security/encrypt", summary="加密敏感数据")
async def encrypt_sensitive_data(
    field_name: str,
    value: str,
    algorithm: str = "AES-256-GCM",
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """加密敏感数据字段"""
    try:
        # 验证字段名是否允许加密
        allowed_fields = [
            "password", "api_key", "private_key", "bank_account",
            "id_number", "phone", "email", "trading_account"
        ]

        if field_name not in allowed_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"字段 {field_name} 不允许加密"
            )

        # 加密数据
        encrypted_value = await advanced_encryption.encrypt_field(
            field_name, value, algorithm
        )

        # 记录审计日志
        await security_hardening.audit_logger.log_event(AuditEvent(
            event_type=AuditEventType.DATA_EXPORT,
            user_id=current_user.id,
            ip_address="unknown",
            user_agent="API",
            endpoint="/api/v1/ctp/security/encrypt",
            method="POST",
            request_data={"field_name": field_name, "algorithm": algorithm},
            response_status=200,
            risk_level=SecurityLevel.HIGH
        ))

        return {
            "status": "success",
            "message": "数据加密成功",
            "field_name": field_name,
            "algorithm": algorithm,
            "encrypted_value": encrypted_value
        }

    except Exception as e:
        logger.error(f"数据加密失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据加密失败: {str(e)}"
        )


@router.post("/security/decrypt", summary="解密敏感数据")
async def decrypt_sensitive_data(
    field_name: str,
    encrypted_value: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """解密敏感数据字段"""
    try:
        # 验证字段名是否允许解密
        allowed_fields = [
            "password", "api_key", "private_key", "bank_account",
            "id_number", "phone", "email", "trading_account"
        ]

        if field_name not in allowed_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"字段 {field_name} 不允许解密"
            )

        # 解密数据
        decrypted_value = await advanced_encryption.decrypt_field(
            field_name, encrypted_value
        )

        # 记录审计日志
        await security_hardening.audit_logger.log_event(AuditEvent(
            event_type=AuditEventType.DATA_EXPORT,
            user_id=current_user.id,
            ip_address="unknown",
            user_agent="API",
            endpoint="/api/v1/ctp/security/decrypt",
            method="POST",
            request_data={"field_name": field_name},
            response_status=200,
            risk_level=SecurityLevel.CRITICAL  # 解密操作风险更高
        ))

        return {
            "status": "success",
            "message": "数据解密成功",
            "field_name": field_name,
            "decrypted_value": decrypted_value
        }

    except Exception as e:
        logger.error(f"数据解密失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"数据解密失败: {str(e)}"
        )


@router.get("/security/status", summary="获取安全状态")
async def get_security_status(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """获取系统安全状态"""
    try:
        # 获取安全配置状态
        security_status = {
            "security_enabled": security_hardening.security_enabled,
            "threat_detection_enabled": security_hardening.threat_detection_enabled,
            "rate_limiting": {
                "default": security_hardening.access_controller.rate_limits["default"],
                "trading": security_hardening.access_controller.rate_limits["trading"],
                "query": security_hardening.access_controller.rate_limits["query"]
            },
            "ip_whitelist_count": len(security_hardening.access_controller.ip_whitelist),
            "ip_blacklist_count": len(security_hardening.access_controller.ip_blacklist),
            "blocked_users_count": len(security_hardening.access_controller.blocked_users),
            "token_blacklist_count": len(jwt_security_manager.token_blacklist),
            "active_refresh_tokens": len(jwt_security_manager.refresh_token_store)
        }

        return {
            "status": "success",
            "security_status": security_status
        }

    except Exception as e:
        logger.error(f"获取安全状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取安全状态失败: {str(e)}"
        )


@router.post("/security/ip/whitelist", summary="管理IP白名单")
async def manage_ip_whitelist(
    action: str,  # add, remove, list
    ip_address: str = None,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """管理IP白名单"""
    try:
        if action == "add":
            if not ip_address:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="添加IP时必须提供ip_address"
                )
            security_hardening.access_controller.add_to_whitelist(ip_address)
            message = f"IP {ip_address} 已添加到白名单"

        elif action == "remove":
            if not ip_address:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="移除IP时必须提供ip_address"
                )
            security_hardening.access_controller.ip_whitelist.discard(ip_address)
            message = f"IP {ip_address} 已从白名单移除"

        elif action == "list":
            return {
                "status": "success",
                "whitelist": list(security_hardening.access_controller.ip_whitelist)
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的操作，支持: add, remove, list"
            )

        # 记录审计日志
        await security_hardening.audit_logger.log_event(AuditEvent(
            event_type=AuditEventType.CONFIG_CHANGE,
            user_id=current_user.id,
            ip_address="unknown",
            user_agent="API",
            endpoint="/api/v1/ctp/security/ip/whitelist",
            method="POST",
            request_data={"action": action, "ip_address": ip_address},
            response_status=200,
            risk_level=SecurityLevel.HIGH
        ))

        return {
            "status": "success",
            "message": message
        }

    except Exception as e:
        logger.error(f"管理IP白名单失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"管理IP白名单失败: {str(e)}"
        )
