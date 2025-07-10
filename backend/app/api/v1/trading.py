"""
交易相关API路由
提供下单、撤单、查询持仓、查询成交等功能
"""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.trading import (
    Direction,
    Offset,
    OrderType,
    OrderStatus,
    PositionDirection,
    OrderData,
    TradeData,
    PositionData,
    AccountData,
    OrderRequest,
    CancelRequest,
    ModifyRequest,
    BatchOrderRequest,
    OrderQueryRequest,
    TradeQueryRequest,
    PositionQueryRequest,
    OrderResponse,
    OrderListResponse,
    TradeListResponse,
    PositionListResponse,
    AccountResponse,
    RiskLimitData,
    RiskCheckResult,
    OrderUpdateMessage,
    TradeUpdateMessage,
    WebSocketMessage
)
from app.services.trading_service import TradingService
from app.services.risk_service import RiskService

router = APIRouter(tags=["交易"])


@router.post("/orders", response_model=OrderResponse, summary="提交订单")
async def submit_order(
    order_request: OrderRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    提交交易订单
    
    - **symbol**: 合约代码
    - **direction**: 交易方向（买入/卖出）
    - **offset**: 开平仓方向
    - **order_type**: 订单类型（限价/市价等）
    - **volume**: 交易数量
    - **price**: 价格（限价单必填）
    - **time_condition**: 时间条件
    - **volume_condition**: 数量条件
    """
    trading_service = TradingService(db)
    risk_service = RiskService(db)
    
    # 风险检查
    risk_check = await risk_service.check_order_risk(
        user_id=current_user.id,
        order_request=order_request
    )
    
    if not risk_check.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"风险检查失败: {risk_check.message}"
        )
    
    # 提交订单
    order = await trading_service.submit_order(
        user_id=current_user.id,
        order_request=order_request
    )
    
    return OrderResponse(
        success=True,
        message="订单提交成功",
        data=OrderData.model_validate(order)
    )


@router.post("/orders/batch", response_model=List[OrderResponse], summary="批量提交订单")
async def submit_batch_orders(
    batch_request: BatchOrderRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量提交交易订单
    
    - **orders**: 订单列表
    - **fail_on_error**: 是否在出错时停止后续订单
    """
    trading_service = TradingService(db)
    risk_service = RiskService(db)
    
    results = []
    
    for order_request in batch_request.orders:
        try:
            # 风险检查
            risk_check = await risk_service.check_order_risk(
                user_id=current_user.id,
                order_request=order_request
            )
            
            if not risk_check.is_valid:
                if batch_request.fail_on_error:
                    raise HTTPException(
                        status_code=400,
                        detail=f"订单 {order_request.symbol} 风险检查失败: {risk_check.message}"
                    )
                else:
                    results.append(OrderResponse(
                        success=False,
                        message=f"风险检查失败: {risk_check.message}",
                        data=None
                    ))
                    continue
            
            # 提交订单
            order = await trading_service.submit_order(
                user_id=current_user.id,
                order_request=order_request
            )
            
            results.append(OrderResponse(
                success=True,
                message="订单提交成功",
                data=OrderData.model_validate(order)
            ))
            
        except Exception as e:
            if batch_request.fail_on_error:
                raise HTTPException(status_code=400, detail=str(e))
            else:
                results.append(OrderResponse(
                    success=False,
                    message=str(e),
                    data=None
                ))
    
    return results


@router.delete("/orders/{order_id}", summary="撤销订单")
async def cancel_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    撤销指定订单
    
    - **order_id**: 订单ID
    """
    trading_service = TradingService(db)
    
    # 验证订单所有权
    order = await trading_service.get_order_by_id(order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if order.status not in [OrderStatus.SUBMITTING, OrderStatus.NOTTRADED, OrderStatus.PARTTRADED]:
        raise HTTPException(status_code=400, detail="订单状态不允许撤销")
    
    success = await trading_service.cancel_order(order_id)
    
    return {
        "success": success,
        "message": "撤单请求已提交" if success else "撤单失败"
    }


@router.post("/orders/cancel-batch", summary="批量撤销订单")
async def cancel_batch_orders(
    order_ids: List[str],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    批量撤销订单
    
    - **order_ids**: 订单ID列表
    """
    trading_service = TradingService(db)
    
    results = []
    for order_id in order_ids:
        try:
            # 验证订单所有权
            order = await trading_service.get_order_by_id(order_id)
            if not order or order.user_id != current_user.id:
                results.append({
                    "order_id": order_id,
                    "success": False,
                    "message": "订单不存在"
                })
                continue
            
            if order.status not in [OrderStatus.SUBMITTING, OrderStatus.NOTTRADED, OrderStatus.PARTTRADED]:
                results.append({
                    "order_id": order_id,
                    "success": False,
                    "message": "订单状态不允许撤销"
                })
                continue
            
            success = await trading_service.cancel_order(order_id)
            results.append({
                "order_id": order_id,
                "success": success,
                "message": "撤单请求已提交" if success else "撤单失败"
            })
            
        except Exception as e:
            results.append({
                "order_id": order_id,
                "success": False,
                "message": str(e)
            })
    
    return {"results": results}


@router.put("/orders/{order_id}", response_model=OrderResponse, summary="修改订单")
async def modify_order(
    order_id: str,
    modify_request: ModifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    修改订单价格或数量
    
    - **order_id**: 订单ID
    - **new_price**: 新价格（可选）
    - **new_volume**: 新数量（可选）
    """
    trading_service = TradingService(db)
    
    # 验证订单所有权
    order = await trading_service.get_order_by_id(order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    if order.status not in [OrderStatus.NOTTRADED, OrderStatus.PARTTRADED]:
        raise HTTPException(status_code=400, detail="订单状态不允许修改")
    
    modified_order = await trading_service.modify_order(order_id, modify_request)
    
    return OrderResponse(
        success=True,
        message="订单修改成功",
        data=OrderData.model_validate(modified_order)
    )


@router.get("/orders", response_model=OrderListResponse, summary="查询订单")
async def get_orders(
    symbol: Optional[str] = Query(None, description="合约代码"),
    status: Optional[OrderStatus] = Query(None, description="订单状态"),
    direction: Optional[Direction] = Query(None, description="交易方向"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询用户订单
    
    - **symbol**: 合约代码筛选
    - **status**: 订单状态筛选
    - **direction**: 交易方向筛选
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    """
    trading_service = TradingService(db)
    
    # 如果没有指定时间范围，默认查询最近30天
    if not start_time:
        start_time = datetime.now() - timedelta(days=30)
    if not end_time:
        end_time = datetime.now()
    
    query_request = OrderQueryRequest(
        user_id=current_user.id,
        symbol=symbol,
        status=status,
        direction=direction,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )
    
    orders, total = await trading_service.get_orders(query_request)
    
    return OrderListResponse(
        orders=[OrderData.model_validate(order) for order in orders],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/orders/{order_id}", response_model=OrderData, summary="获取订单详情")
async def get_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取订单详细信息
    
    - **order_id**: 订单ID
    """
    trading_service = TradingService(db)
    
    order = await trading_service.get_order_by_id(order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    
    return OrderData.model_validate(order)


@router.get("/trades", response_model=TradeListResponse, summary="查询成交记录")
async def get_trades(
    symbol: Optional[str] = Query(None, description="合约代码"),
    direction: Optional[Direction] = Query(None, description="交易方向"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询用户成交记录
    
    - **symbol**: 合约代码筛选
    - **direction**: 交易方向筛选
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    """
    trading_service = TradingService(db)
    
    # 如果没有指定时间范围，默认查询最近30天
    if not start_time:
        start_time = datetime.now() - timedelta(days=30)
    if not end_time:
        end_time = datetime.now()
    
    query_request = TradeQueryRequest(
        user_id=current_user.id,
        symbol=symbol,
        direction=direction,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit
    )
    
    trades, total = await trading_service.get_trades(query_request)
    
    return TradeListResponse(
        trades=[TradeData.model_validate(trade) for trade in trades],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/positions", response_model=PositionListResponse, summary="查询持仓")
async def get_positions(
    symbol: Optional[str] = Query(None, description="合约代码"),
    direction: Optional[PositionDirection] = Query(None, description="持仓方向"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询用户持仓
    
    - **symbol**: 合约代码筛选
    - **direction**: 持仓方向筛选
    """
    trading_service = TradingService(db)
    
    query_request = PositionQueryRequest(
        user_id=current_user.id,
        symbol=symbol,
        direction=direction
    )
    
    positions = await trading_service.get_positions(query_request)
    
    return PositionListResponse(
        positions=[PositionData.model_validate(pos) for pos in positions]
    )


@router.get("/account", response_model=AccountResponse, summary="查询账户信息")
async def get_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询用户账户信息
    """
    trading_service = TradingService(db)
    
    account = await trading_service.get_account(current_user.id)
    if not account:
        raise HTTPException(status_code=404, detail="账户信息不存在")
    
    return AccountResponse(
        data=AccountData.model_validate(account)
    )


@router.get("/risk-limits", response_model=RiskLimitData, summary="查询风控限制")
async def get_risk_limits(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    查询用户风控限制设置
    """
    risk_service = RiskService(db)
    
    risk_limits = await risk_service.get_user_risk_limits(current_user.id)
    if not risk_limits:
        raise HTTPException(status_code=404, detail="风控限制信息不存在")
    
    return RiskLimitData.model_validate(risk_limits)


@router.put("/risk-limits", response_model=RiskLimitData, summary="更新风控限制")
async def update_risk_limits(
    risk_limits: RiskLimitData,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新用户风控限制设置
    """
    risk_service = RiskService(db)
    
    updated_limits = await risk_service.update_user_risk_limits(
        current_user.id, 
        risk_limits
    )
    
    return RiskLimitData.model_validate(updated_limits)


# WebSocket相关端点
@router.websocket("/ws")
async def trading_websocket(websocket: WebSocket):
    """
    交易WebSocket连接
    
    实时推送：
    - 订单状态更新
    - 成交回报
    - 持仓变化
    - 账户资金变化
    """
    await websocket.accept()
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            message = WebSocketMessage(**data)
            
            if message.type == "ping":
                # 心跳响应
                response = WebSocketMessage(
                    type="pong",
                    data={"timestamp": datetime.now().isoformat()}
                )
                await websocket.send_json(response.model_dump())
                
            elif message.type == "subscribe_orders":
                # 订阅订单更新
                response = WebSocketMessage(
                    type="subscription_success",
                    data={"message": "订单更新订阅成功"}
                )
                await websocket.send_json(response.model_dump())
                
            elif message.type == "subscribe_trades":
                # 订阅成交更新
                response = WebSocketMessage(
                    type="subscription_success",
                    data={"message": "成交更新订阅成功"}
                )
                await websocket.send_json(response.model_dump())
                
            else:
                # 未知消息类型
                error_response = WebSocketMessage(
                    type="error",
                    data={"message": f"未知消息类型: {message.type}"}
                )
                await websocket.send_json(error_response.model_dump())
                
    except WebSocketDisconnect:
        print("交易WebSocket连接已断开")
    except Exception as e:
        print(f"交易WebSocket错误: {e}")
        error_response = WebSocketMessage(
            type="error",
            data={"message": str(e)}
        )
        try:
            await websocket.send_json(error_response.model_dump())
        except:
            pass


@router.get("/test", summary="测试端点")
async def test_endpoint():
    """
    测试端点，不需要认证
    """
    return {
        "success": True,
        "message": "交易API正常工作",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@router.get("/health", summary="健康检查")
async def health_check():
    """
    交易模块健康检查
    """
    return {
        "status": "healthy",
        "module": "trading",
        "timestamp": datetime.now().isoformat()
    }


@router.get("/mock/account", summary="模拟账户信息")
async def get_mock_account():
    """
    获取模拟账户信息（开发用）
    """
    return {
        "success": True,
        "message": "获取账户信息成功",
        "data": {
            "account_id": "DEMO_001",
            "broker_id": "DEMO",
            "total_asset": 1000000.0,
            "available_cash": 800000.0,
            "frozen_cash": 0.0,
            "total_market_value": 200000.0,
            "total_profit_loss": 5000.0,
            "day_profit_loss": 1200.0,
            "commission": 50.0,
            "margin_used": 200000.0,
            "risk_ratio": 0.2,
            "currency": "CNY",
            "status": "ACTIVE",
            "last_update_time": datetime.now().isoformat()
        }
    }


@router.get("/mock/orders", summary="模拟订单列表")
async def get_mock_orders():
    """
    获取模拟订单列表（开发用）
    """
    return {
        "success": True,
        "message": "获取订单列表成功",
        "data": [
            {
                "order_id": "DEMO_001",
                "symbol": "IF2501",
                "exchange": "CFFEX",
                "direction": "BUY",
                "offset": "OPEN",
                "order_type": "LIMIT",
                "volume": 1,
                "price": 4200.0,
                "status": "ALL_FILLED",
                "traded": 1,
                "order_time": datetime.now().isoformat(),
                "update_time": datetime.now().isoformat()
            },
            {
                "order_id": "DEMO_002",
                "symbol": "IC2501",
                "exchange": "CFFEX",
                "direction": "SELL",
                "offset": "OPEN",
                "order_type": "LIMIT",
                "volume": 1,
                "price": 6850.0,
                "status": "SUBMITTED",
                "traded": 0,
                "order_time": datetime.now().isoformat(),
                "update_time": datetime.now().isoformat()
            }
        ],
        "total": 2,
        "page": 1,
        "limit": 100
    }


@router.get("/mock/trades", summary="模拟成交记录")
async def get_mock_trades():
    """
    获取模拟成交记录（开发用）
    """
    return {
        "success": True,
        "message": "获取成交记录成功",
        "data": [
            {
                "trade_id": "TRADE_001",
                "order_id": "DEMO_001",
                "symbol": "IF2501",
                "exchange": "CFFEX",
                "direction": "BUY",
                "offset": "OPEN",
                "volume": 1,
                "price": 4200.0,
                "commission": 5.0,
                "trade_time": datetime.now().isoformat()
            }
        ],
        "total": 1,
        "page": 1,
        "limit": 100
    }


@router.get("/mock/positions", summary="模拟持仓信息")
async def get_mock_positions():
    """
    获取模拟持仓信息（开发用）
    """
    return {
        "success": True,
        "message": "获取持仓信息成功",
        "data": [
            {
                "symbol": "IF2501",
                "exchange": "CFFEX",
                "direction": "BUY",
                "volume": 2,
                "avg_price": 4180.0,
                "market_price": 4200.0,
                "profit_loss": 400.0,
                "margin": 83600.0,
                "today_volume": 1,
                "yesterday_volume": 1,
                "frozen_volume": 0,
                "last_update_time": datetime.now().isoformat()
            },
            {
                "symbol": "IC2501",
                "exchange": "CFFEX",
                "direction": "SELL",
                "volume": 1,
                "avg_price": 6850.0,
                "market_price": 6820.0,
                "profit_loss": 300.0,
                "margin": 68200.0,
                "today_volume": 0,
                "yesterday_volume": 1,
                "frozen_volume": 0,
                "last_update_time": datetime.now().isoformat()
            }
        ],
        "total": 2
    }