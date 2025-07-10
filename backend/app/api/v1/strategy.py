"""
策略相关API路由
提供策略创建、管理、监控等功能
"""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.strategy import (
    StrategyType,
    StrategyStatus,
    FrequencyType,
    SignalType,
    StrategyBase,
    StrategyCreate,
    StrategyUpdate,
    StrategyResponse,
    StrategyListResponse,
    StrategyParameter,
    StrategySignal,
    StrategyLog,
    StrategyPerformance,
    StrategyControlRequest,
    StrategyOptimizationRequest,
    StrategyTemplate,
    StrategyStatsResponse,
    StrategyMessage,
    StrategySignalMessage,
    StrategyStatusMessage,
    StrategyLogMessage
)
from app.services.strategy_service import StrategyService

router = APIRouter(prefix="/strategy", tags=["策略"])


@router.post("/", response_model=StrategyResponse, summary="创建策略")
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新的交易策略
    
    - **name**: 策略名称
    - **description**: 策略描述
    - **strategy_type**: 策略类型
    - **code**: 策略代码
    - **parameters**: 策略参数
    - **symbols**: 交易标的
    - **frequency**: 运行频率
    """
    strategy_service = StrategyService(db)
    
    # 检查策略名称是否已存在
    existing_strategy = await strategy_service.get_strategy_by_name(
        current_user.id, strategy_data.name
    )
    if existing_strategy:
        raise HTTPException(
            status_code=400,
            detail="策略名称已存在"
        )
    
    # 验证策略代码
    validation_result = await strategy_service.validate_strategy_code(strategy_data.code)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"策略代码验证失败: {validation_result.error_message}"
        )
    
    strategy = await strategy_service.create_strategy(current_user.id, strategy_data)
    
    return StrategyResponse(
        success=True,
        message="策略创建成功",
        data=strategy
    )


@router.get("/", response_model=StrategyListResponse, summary="获取策略列表")
async def get_strategies(
    strategy_type: Optional[StrategyType] = Query(None, description="策略类型"),
    status: Optional[StrategyStatus] = Query(None, description="策略状态"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户策略列表
    
    - **strategy_type**: 策略类型筛选
    - **status**: 策略状态筛选
    """
    strategy_service = StrategyService(db)
    
    strategies, total = await strategy_service.get_user_strategies(
        user_id=current_user.id,
        strategy_type=strategy_type,
        status=status,
        skip=skip,
        limit=limit
    )
    
    return StrategyListResponse(
        strategies=strategies,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{strategy_id}", response_model=StrategyBase, summary="获取策略详情")
async def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取策略详细信息
    
    - **strategy_id**: 策略ID
    """
    strategy_service = StrategyService(db)
    
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    return strategy


@router.put("/{strategy_id}", response_model=StrategyResponse, summary="更新策略")
async def update_strategy(
    strategy_id: int,
    strategy_update: StrategyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新策略信息
    
    - **strategy_id**: 策略ID
    """
    strategy_service = StrategyService(db)
    
    # 验证策略所有权
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    # 如果策略正在运行，不允许修改核心参数
    if strategy.status == StrategyStatus.RUNNING and (
        strategy_update.code or strategy_update.parameters or strategy_update.symbols
    ):
        raise HTTPException(
            status_code=400,
            detail="运行中的策略不允许修改代码、参数或标的"
        )
    
    # 如果修改了代码，需要重新验证
    if strategy_update.code:
        validation_result = await strategy_service.validate_strategy_code(strategy_update.code)
        if not validation_result.is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"策略代码验证失败: {validation_result.error_message}"
            )
    
    updated_strategy = await strategy_service.update_strategy(strategy_id, strategy_update)
    
    return StrategyResponse(
        success=True,
        message="策略更新成功",
        data=updated_strategy
    )


@router.delete("/{strategy_id}", summary="删除策略")
async def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除策略
    
    - **strategy_id**: 策略ID
    """
    strategy_service = StrategyService(db)
    
    # 验证策略所有权
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    # 运行中的策略不允许删除
    if strategy.status == StrategyStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="运行中的策略不允许删除，请先停止策略"
        )
    
    await strategy_service.delete_strategy(strategy_id)
    
    return {"message": "策略删除成功"}


@router.post("/{strategy_id}/start", summary="启动策略")
async def start_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    启动策略运行
    
    - **strategy_id**: 策略ID
    """
    strategy_service = StrategyService(db)
    
    # 验证策略所有权
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    if strategy.status == StrategyStatus.RUNNING:
        raise HTTPException(status_code=400, detail="策略已在运行中")
    
    if strategy.status != StrategyStatus.STOPPED:
        raise HTTPException(status_code=400, detail="只有已停止的策略可以启动")
    
    success = await strategy_service.start_strategy(strategy_id)
    
    return {
        "success": success,
        "message": "策略启动成功" if success else "策略启动失败"
    }


@router.post("/{strategy_id}/stop", summary="停止策略")
async def stop_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    停止策略运行
    
    - **strategy_id**: 策略ID
    """
    strategy_service = StrategyService(db)
    
    # 验证策略所有权
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    if strategy.status != StrategyStatus.RUNNING:
        raise HTTPException(status_code=400, detail="只有运行中的策略可以停止")
    
    success = await strategy_service.stop_strategy(strategy_id)
    
    return {
        "success": success,
        "message": "策略停止成功" if success else "策略停止失败"
    }


@router.post("/{strategy_id}/pause", summary="暂停策略")
async def pause_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    暂停策略运行
    
    - **strategy_id**: 策略ID
    """
    strategy_service = StrategyService(db)
    
    # 验证策略所有权
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    if strategy.status != StrategyStatus.RUNNING:
        raise HTTPException(status_code=400, detail="只有运行中的策略可以暂停")
    
    success = await strategy_service.pause_strategy(strategy_id)
    
    return {
        "success": success,
        "message": "策略暂停成功" if success else "策略暂停失败"
    }


@router.post("/{strategy_id}/resume", summary="恢复策略")
async def resume_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    恢复策略运行
    
    - **strategy_id**: 策略ID
    """
    strategy_service = StrategyService(db)
    
    # 验证策略所有权
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    if strategy.status != StrategyStatus.PAUSED:
        raise HTTPException(status_code=400, detail="只有暂停的策略可以恢复")
    
    success = await strategy_service.resume_strategy(strategy_id)
    
    return {
        "success": success,
        "message": "策略恢复成功" if success else "策略恢复失败"
    }


@router.get("/{strategy_id}/performance", response_model=StrategyPerformance, summary="获取策略绩效")
async def get_strategy_performance(
    strategy_id: int,
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取策略绩效分析
    
    - **strategy_id**: 策略ID
    - **start_date**: 开始日期
    - **end_date**: 结束日期
    """
    strategy_service = StrategyService(db)
    
    # 验证策略所有权
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    # 如果没有指定时间范围，默认查询最近30天
    if not start_date:
        start_date = datetime.now() - timedelta(days=30)
    if not end_date:
        end_date = datetime.now()
    
    performance = await strategy_service.get_strategy_performance(
        strategy_id, start_date, end_date
    )
    
    return performance


@router.get("/{strategy_id}/signals", response_model=List[StrategySignal], summary="获取策略信号")
async def get_strategy_signals(
    strategy_id: int,
    signal_type: Optional[SignalType] = Query(None, description="信号类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取策略信号记录
    
    - **strategy_id**: 策略ID
    - **signal_type**: 信号类型筛选
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    - **limit**: 返回记录数限制
    """
    strategy_service = StrategyService(db)
    
    # 验证策略所有权
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    # 如果没有指定时间范围，默认查询最近24小时
    if not start_time:
        start_time = datetime.now() - timedelta(hours=24)
    if not end_time:
        end_time = datetime.now()
    
    signals = await strategy_service.get_strategy_signals(
        strategy_id=strategy_id,
        signal_type=signal_type,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return signals


@router.get("/{strategy_id}/logs", response_model=List[StrategyLog], summary="获取策略日志")
async def get_strategy_logs(
    strategy_id: int,
    level: Optional[str] = Query(None, description="日志级别"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回记录数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取策略运行日志
    
    - **strategy_id**: 策略ID
    - **level**: 日志级别筛选
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    - **limit**: 返回记录数限制
    """
    strategy_service = StrategyService(db)
    
    # 验证策略所有权
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    # 如果没有指定时间范围，默认查询最近24小时
    if not start_time:
        start_time = datetime.now() - timedelta(hours=24)
    if not end_time:
        end_time = datetime.now()
    
    logs = await strategy_service.get_strategy_logs(
        strategy_id=strategy_id,
        level=level,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return logs


@router.post("/{strategy_id}/optimize", summary="策略参数优化")
async def optimize_strategy(
    strategy_id: int,
    optimization_request: StrategyOptimizationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    启动策略参数优化任务
    
    - **strategy_id**: 策略ID
    - **parameters**: 优化参数范围
    - **objective**: 优化目标
    - **method**: 优化方法
    """
    strategy_service = StrategyService(db)
    
    # 验证策略所有权
    strategy = await strategy_service.get_strategy_by_id(strategy_id)
    if not strategy or strategy.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    # 启动优化任务
    task_id = await strategy_service.start_optimization(strategy_id, optimization_request)
    
    return {
        "task_id": task_id,
        "message": "参数优化任务已启动"
    }


@router.get("/templates", response_model=List[StrategyTemplate], summary="获取策略模板")
async def get_strategy_templates(
    strategy_type: Optional[StrategyType] = Query(None, description="策略类型"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取策略模板列表
    
    - **strategy_type**: 策略类型筛选
    """
    strategy_service = StrategyService(db)
    
    templates = await strategy_service.get_strategy_templates(strategy_type)
    
    return templates


@router.post("/upload", summary="上传策略文件")
async def upload_strategy_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    上传策略代码文件
    
    - **file**: Python策略文件
    """
    if not file.filename.endswith('.py'):
        raise HTTPException(
            status_code=400,
            detail="只支持Python文件(.py)"
        )
    
    # 读取文件内容
    content = await file.read()
    code = content.decode('utf-8')
    
    strategy_service = StrategyService(db)
    
    # 验证策略代码
    validation_result = await strategy_service.validate_strategy_code(code)
    if not validation_result.is_valid:
        raise HTTPException(
            status_code=400,
            detail=f"策略代码验证失败: {validation_result.error_message}"
        )
    
    return {
        "filename": file.filename,
        "code": code,
        "validation": validation_result,
        "message": "文件上传成功"
    }


# WebSocket相关端点
@router.websocket("/ws")
async def strategy_websocket(websocket: WebSocket):
    """
    策略WebSocket连接
    
    实时推送：
    - 策略状态变化
    - 策略信号
    - 策略绩效更新
    - 策略日志
    """
    await websocket.accept()
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            message = StrategyMessage(**data)
            
            if message.type == "ping":
                # 心跳响应
                response = StrategyMessage(
                    type="pong",
                    strategy_id=0,
                    data={"timestamp": datetime.now().isoformat()}
                )
                await websocket.send_json(response.model_dump())
                
            elif message.type == "subscribe_strategy":
                # 订阅策略更新
                strategy_id = message.data.get("strategy_id", 0)
                response = StrategyMessage(
                    type="subscription_success",
                    strategy_id=strategy_id,
                    data={
                        "strategy_id": strategy_id,
                        "message": "策略更新订阅成功"
                    }
                )
                await websocket.send_json(response.model_dump())
                
            else:
                # 未知消息类型
                error_response = StrategyMessage(
                    type="error",
                    strategy_id=0,
                    data={"message": f"未知消息类型: {message.type}"}
                )
                await websocket.send_json(error_response.model_dump())
                
    except WebSocketDisconnect:
        print("策略WebSocket连接已断开")
    except Exception as e:
        print(f"策略WebSocket错误: {e}")
        error_response = StrategyMessage(
            type="error",
            strategy_id=0,
            data={"message": str(e)}
        )
        try:
            await websocket.send_json(error_response.model_dump())
        except:
            pass


@router.get("/stats", response_model=StrategyStatsResponse, summary="获取策略统计")
async def get_strategy_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户策略统计信息
    """
    strategy_service = StrategyService(db)
    
    stats = await strategy_service.get_user_strategy_stats(current_user.id)
    
    return StrategyStatsResponse(**stats)


@router.get("/health", summary="健康检查")
async def health_check():
    """
    策略服务健康检查
    """
    return {
        "status": "healthy",
        "service": "strategy",
        "timestamp": datetime.now().isoformat(),
        "supported_types": [st.value for st in StrategyType],
        "supported_frequencies": [ft.value for ft in FrequencyType]
    }