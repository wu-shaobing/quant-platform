"""
回测相关API路由
提供策略回测、结果分析、报告生成等功能
"""
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_user_optional
from app.models.user import User
from app.schemas.backtest import (
    BacktestStatus,
    RebalanceFrequency,
    BenchmarkType,
    BacktestConfigBase,
    BacktestCreate,
    BacktestUpdate,
    BacktestResponse,
    BacktestListResponse,
    BacktestResult,
    BacktestDetailResponse,
    DailyReturnData,
    BacktestPositionData,
    BacktestTradeData,
    BacktestAnalysisRequest,
    BacktestOptimizationConfig,
    BacktestReport,
    BacktestStatsResponse,
    BacktestMessage,
    BacktestProgressMessage,
    BacktestCompleteMessage,
    BacktestErrorMessage
)
from app.services.backtest_service import BacktestService

router = APIRouter(tags=["回测"])


@router.post("/", response_model=BacktestResponse, summary="创建回测任务")
async def create_backtest(
    backtest_data: BacktestCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新的回测任务
    
    - **name**: 回测名称
    - **strategy_id**: 策略ID
    - **start_date**: 回测开始日期
    - **end_date**: 回测结束日期
    - **initial_capital**: 初始资金
    - **symbols**: 回测标的
    - **benchmark**: 基准指标
    - **commission_rate**: 手续费率
    - **slippage_rate**: 滑点率
    """
    backtest_service = BacktestService(db)
    
    # 验证回测参数
    if backtest_data.start_date >= backtest_data.end_date:
        raise HTTPException(
            status_code=400,
            detail="回测开始日期必须早于结束日期"
        )
    
    if backtest_data.initial_capital <= 0:
        raise HTTPException(
            status_code=400,
            detail="初始资金必须大于0"
        )
    
    # 验证策略存在且属于当前用户
    if backtest_data.strategy_id:
        strategy = await backtest_service.get_strategy_by_id(backtest_data.strategy_id)
        if not strategy or strategy.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="策略不存在")
    
    # 创建回测任务
    backtest = await backtest_service.create_backtest(current_user.id, backtest_data)
    
    # 在后台启动回测任务
    background_tasks.add_task(
        backtest_service.run_backtest_task,
        backtest.id
    )
    
    return BacktestResponse(
        success=True,
        message="回测任务创建成功，正在后台运行",
        data=BacktestConfigBase.model_validate(backtest)
    )


@router.get("/", response_model=BacktestListResponse, summary="获取回测列表")
async def get_backtests(
    status: Optional[BacktestStatus] = Query(None, description="回测状态"),
    skip: int = Query(0, ge=0, description="跳过记录数"),
    limit: int = Query(20, ge=1, le=100, description="返回记录数"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户回测列表
    
    - **status**: 回测状态筛选
    """
    backtest_service = BacktestService(db)
    
    # 如果未登录则返回空列表，方便前端开发
    if not current_user:
        return BacktestListResponse(backtests=[], total=0)

    backtests, total = await backtest_service.get_user_backtests(
        user_id=current_user.id,
        status=status,
        skip=skip,
        limit=limit
    )
    
    return BacktestListResponse(
        backtests=[BacktestConfigBase.model_validate(bt) for bt in backtests],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{backtest_id}", response_model=BacktestDetailResponse, summary="获取回测详情")
async def get_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取回测详细信息
    
    - **backtest_id**: 回测ID
    """
    backtest_service = BacktestService(db)
    
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    # 获取回测结果
    result = None
    if backtest.status == BacktestStatus.COMPLETED:
        result = await backtest_service.get_backtest_result(backtest_id)
    
    return BacktestDetailResponse(
        config=BacktestConfigBase.model_validate(backtest),
        result=BacktestResult.model_validate(result) if result else None
    )


@router.put("/{backtest_id}", response_model=BacktestResponse, summary="更新回测配置")
async def update_backtest(
    backtest_id: int,
    backtest_update: BacktestUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    更新回测配置（仅限未开始的回测）
    
    - **backtest_id**: 回测ID
    """
    backtest_service = BacktestService(db)
    
    # 验证回测所有权
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    # 只有未开始的回测可以修改
    if backtest.status != BacktestStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail="只有未开始的回测可以修改配置"
        )
    
    updated_backtest = await backtest_service.update_backtest(backtest_id, backtest_update)
    
    return BacktestResponse(
        success=True,
        message="回测配置更新成功",
        data=BacktestConfigBase.model_validate(updated_backtest)
    )


@router.delete("/{backtest_id}", summary="删除回测")
async def delete_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    删除回测任务
    
    - **backtest_id**: 回测ID
    """
    backtest_service = BacktestService(db)
    
    # 验证回测所有权
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    # 运行中的回测不允许删除
    if backtest.status == BacktestStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="运行中的回测不允许删除，请先停止回测"
        )
    
    await backtest_service.delete_backtest(backtest_id)
    
    return {"message": "回测删除成功"}


@router.post("/{backtest_id}/start", summary="启动回测")
async def start_backtest(
    backtest_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    启动回测任务
    
    - **backtest_id**: 回测ID
    """
    backtest_service = BacktestService(db)
    
    # 验证回测所有权
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status == BacktestStatus.RUNNING:
        raise HTTPException(status_code=400, detail="回测已在运行中")
    
    if backtest.status not in [BacktestStatus.PENDING, BacktestStatus.FAILED]:
        raise HTTPException(status_code=400, detail="只有待运行或失败的回测可以启动")
    
    # 在后台启动回测任务
    background_tasks.add_task(
        backtest_service.run_backtest_task,
        backtest_id
    )
    
    # 更新状态为运行中
    await backtest_service.update_backtest_status(backtest_id, BacktestStatus.RUNNING)
    
    return {"message": "回测任务已启动"}


@router.post("/{backtest_id}/stop", summary="停止回测")
async def stop_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    停止回测任务
    
    - **backtest_id**: 回测ID
    """
    backtest_service = BacktestService(db)
    
    # 验证回测所有权
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status != BacktestStatus.RUNNING:
        raise HTTPException(status_code=400, detail="只有运行中的回测可以停止")
    
    success = await backtest_service.stop_backtest(backtest_id)
    
    return {
        "success": success,
        "message": "回测停止成功" if success else "回测停止失败"
    }


@router.get("/{backtest_id}/result", response_model=BacktestResult, summary="获取回测结果")
async def get_backtest_result(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取回测结果
    
    - **backtest_id**: 回测ID
    """
    backtest_service = BacktestService(db)
    
    # 验证回测所有权
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status != BacktestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="回测尚未完成")
    
    result = await backtest_service.get_backtest_result(backtest_id)
    if not result:
        raise HTTPException(status_code=404, detail="回测结果不存在")
    
    return BacktestResult.model_validate(result)


@router.get("/{backtest_id}/daily-returns", response_model=List[DailyReturnData], summary="获取每日收益")
async def get_daily_returns(
    backtest_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取回测每日收益数据
    
    - **backtest_id**: 回测ID
    """
    backtest_service = BacktestService(db)
    
    # 验证回测所有权
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status != BacktestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="回测尚未完成")
    
    daily_returns = await backtest_service.get_daily_returns(backtest_id)
    
    return [DailyReturnData.model_validate(dr) for dr in daily_returns]


@router.get("/{backtest_id}/positions", response_model=List[BacktestPositionData], summary="获取持仓记录")
async def get_backtest_positions(
    backtest_id: int,
    symbol: Optional[str] = Query(None, description="标的代码"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取回测持仓记录
    
    - **backtest_id**: 回测ID
    - **symbol**: 标的代码筛选
    """
    backtest_service = BacktestService(db)
    
    # 验证回测所有权
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status != BacktestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="回测尚未完成")
    
    positions = await backtest_service.get_backtest_positions(backtest_id, symbol)
    
    return [BacktestPositionData.model_validate(pos) for pos in positions]


@router.get("/{backtest_id}/trades", response_model=List[BacktestTradeData], summary="获取交易记录")
async def get_backtest_trades(
    backtest_id: int,
    symbol: Optional[str] = Query(None, description="标的代码"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取回测交易记录
    
    - **backtest_id**: 回测ID
    - **symbol**: 标的代码筛选
    """
    backtest_service = BacktestService(db)
    
    # 验证回测所有权
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status != BacktestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="回测尚未完成")
    
    trades = await backtest_service.get_backtest_trades(backtest_id, symbol)
    
    return [BacktestTradeData.model_validate(trade) for trade in trades]


@router.post("/{backtest_id}/analyze", summary="回测分析")
async def analyze_backtest(
    backtest_id: int,
    analysis_request: BacktestAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    对回测结果进行深度分析
    
    - **backtest_id**: 回测ID
    - **analysis_types**: 分析类型列表
    - **benchmark_symbol**: 基准标的
    - **risk_free_rate**: 无风险利率
    """
    backtest_service = BacktestService(db)
    
    # 验证回测所有权
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status != BacktestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="回测尚未完成")
    
    analysis_result = await backtest_service.analyze_backtest(backtest_id, analysis_request)
    
    return {
        "backtest_id": backtest_id,
        "analysis_result": analysis_result,
        "message": "回测分析完成"
    }


@router.post("/{backtest_id}/optimize", summary="参数优化")
async def optimize_backtest(
    backtest_id: int,
    optimization_config: BacktestOptimizationConfig,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    启动回测参数优化任务
    
    - **backtest_id**: 回测ID
    - **parameter_ranges**: 参数优化范围
    - **objective_function**: 优化目标函数
    - **optimization_method**: 优化方法
    - **max_iterations**: 最大迭代次数
    """
    backtest_service = BacktestService(db)
    
    # 验证回测所有权
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    # 在后台启动优化任务
    task_id = await backtest_service.start_optimization_task(
        backtest_id, 
        optimization_config
    )
    
    background_tasks.add_task(
        backtest_service.run_optimization_task,
        task_id
    )
    
    return {
        "task_id": task_id,
        "message": "参数优化任务已启动"
    }


@router.get("/{backtest_id}/report", response_model=BacktestReport, summary="生成回测报告")
async def generate_backtest_report(
    backtest_id: int,
    report_format: str = Query("json", description="报告格式(json/pdf/html)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    生成回测报告
    
    - **backtest_id**: 回测ID
    - **report_format**: 报告格式
    """
    backtest_service = BacktestService(db)
    
    # 验证回测所有权
    backtest = await backtest_service.get_backtest_by_id(backtest_id)
    if not backtest or backtest.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="回测不存在")
    
    if backtest.status != BacktestStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="回测尚未完成")
    
    report = await backtest_service.generate_report(backtest_id, report_format)
    
    return BacktestReport.model_validate(report)


@router.post("/compare", summary="回测对比")
async def compare_backtests(
    backtest_ids: List[int],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    对比多个回测结果
    
    - **backtest_ids**: 回测ID列表
    """
    backtest_service = BacktestService(db)
    
    # 验证所有回测都属于当前用户且已完成
    for backtest_id in backtest_ids:
        backtest = await backtest_service.get_backtest_by_id(backtest_id)
        if not backtest or backtest.user_id != current_user.id:
            raise HTTPException(status_code=404, detail=f"回测{backtest_id}不存在")
        
        if backtest.status != BacktestStatus.COMPLETED:
            raise HTTPException(status_code=400, detail=f"回测{backtest_id}尚未完成")
    
    comparison_result = await backtest_service.compare_backtests(backtest_ids)
    
    return {
        "backtest_ids": backtest_ids,
        "comparison": comparison_result,
        "message": "回测对比完成"
    }


# WebSocket相关端点
@router.websocket("/ws")
async def backtest_websocket(websocket: WebSocket):
    """
    回测WebSocket连接
    
    实时推送：
    - 回测进度更新
    - 回测状态变化
    - 回测结果
    """
    await websocket.accept()
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            message = BacktestMessage(**data)
            
            if message.type == "ping":
                # 心跳响应
                response = BacktestMessage(
                    type="pong",
                    backtest_id=0,
                    data={"timestamp": datetime.now().isoformat()}
                )
                await websocket.send_json(response.model_dump())
                
            elif message.type == "subscribe_backtest":
                # 订阅回测更新
                backtest_id = message.data.get("backtest_id", 0)
                response = BacktestMessage(
                    type="subscription_success",
                    backtest_id=backtest_id,
                    data={
                        "backtest_id": backtest_id,
                        "message": "回测更新订阅成功"
                    }
                )
                await websocket.send_json(response.model_dump())
                
            else:
                # 未知消息类型
                error_response = BacktestMessage(
                    type="error",
                    backtest_id=0,
                    data={"message": f"未知消息类型: {message.type}"}
                )
                await websocket.send_json(error_response.model_dump())
                
    except WebSocketDisconnect:
        print("回测WebSocket连接已断开")
    except Exception as e:
        print(f"回测WebSocket错误: {e}")
        error_response = BacktestMessage(
            type="error",
            backtest_id=0,
            data={"message": str(e)}
        )
        try:
            await websocket.send_json(error_response.model_dump())
        except:
            pass


@router.get("/stats", response_model=BacktestStatsResponse, summary="获取回测统计")
async def get_backtest_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取用户回测统计信息
    """
    backtest_service = BacktestService(db)
    
    stats = await backtest_service.get_user_backtest_stats(current_user.id)
    
    return BacktestStatsResponse(**stats)


@router.get("/health", summary="健康检查")
async def health_check():
    """
    回测服务健康检查
    """
    return {
        "status": "healthy",
        "service": "backtest",
        "timestamp": datetime.now().isoformat(),
        "supported_benchmarks": [bt.value for bt in BenchmarkType],
        "supported_frequencies": [rf.value for rf in RebalanceFrequency]
    }


# ------------------- 开发用Mock接口 -------------------

@router.get("/mock", summary="Mock回测列表 (开发环境)")
async def get_mock_backtests(limit: int = Query(20, ge=1, le=100)):
    """返回模拟回测列表，便于前端无登录也能调试"""
    import random, time
    mock_list = []
    for i in range(limit):
        mock_list.append({
            "id": i + 1,
            "name": f"策略回测 {i+1}",
            "strategyId": random.randint(1, 10),
            "symbol": random.choice(["AAPL", "TSLA", "GOOG", "MSFT", "AMZN"]),
            "startDate": "2024-01-01",
            "endDate": "2024-06-30",
            "initialCash": 1000000,
            "status": random.choice(["COMPLETED", "RUNNING", "FAILED"]),
            "createTime": time.time() - random.randint(0, 86400*30),
            "updateTime": time.time(),
            "totalReturn": round(random.uniform(-0.1, 0.4), 4),
            "maxDrawdown": round(random.uniform(0.05, 0.2), 4)
        })
    return {
        "success": True,
        "message": "获取回测列表成功",
        "data": mock_list,
        "total": len(mock_list)
    }