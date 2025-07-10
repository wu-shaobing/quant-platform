"""
市场数据API路由
提供行情数据、合约信息、市场统计等功能
"""
from typing import List, Optional, Union
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_current_user_optional, get_market_service
from app.models.user import User
from app.schemas import (
    Exchange,
    ProductClass,
    Interval,
    ContractData,
    TickData,
    BarData,
    DepthData,
    MarketStatsData,
    SubscribeRequest,
    MarketDataRequest,
    MarketSearchRequest,
    TickDataResponse,
    BarDataResponse,
    ContractListResponse,
    WebSocketMessage,
    MarketDataMessage,
    SubscriptionMessage,
    MarketOverviewResponse,
)
from app.services.market_service import MarketService

router = APIRouter(tags=["市场数据"])


@router.get("/contracts", response_model=ContractListResponse, summary="获取所有合约信息")
async def get_all_contracts(
    market_service: MarketService = Depends(get_market_service),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=1000, description="每页数量"),
):
    """
    获取所有可交易的合约信息，支持分页。
    """
    return await market_service.get_all_contracts(page, page_size)


@router.get("/contracts/{symbol}", response_model=ContractData, summary="获取单个合约信息")
async def get_contract(
    symbol: str,
    market_service: MarketService = Depends(get_market_service),
):
    """
    根据合约代码获取详细的合约信息。
    """
    return await market_service.get_contract(symbol)


@router.get("/tick/{symbol}/latest", response_model=TickDataResponse, summary="获取最新Tick数据")
async def get_tick_data(
    symbol: str,
    market_service: MarketService = Depends(get_market_service),
    limit: int = Query(100, ge=1, le=1000, description="返回的Tick数量"),
):
    """
    获取指定合约最新的Tick数据流。
    """
    ticks = await market_service.get_tick_data(symbol, limit)
    return {"data": ticks, "total": len(ticks), "symbol": symbol, "exchange": "SHFE"}


@router.get("/bars/{symbol}", response_model=BarDataResponse, summary="获取K线数据")
async def get_bar_data(
    symbol: str,
    request: MarketDataRequest = Depends(),
    market_service: MarketService = Depends(get_market_service),
):
    """
    获取K线数据，支持不同时间周期和时间范围。
    """
    bars = await market_service.get_bar_data(request)
    return {
        "data": bars,
        "total": len(bars),
        "symbol": symbol,
        "exchange": "SHFE",
        "interval": request.interval,
    }


@router.post("/search", response_model=ContractListResponse, summary="搜索合约")
async def search_contracts(
    request: MarketSearchRequest,
    market_service: MarketService = Depends(get_market_service),
):
    """
    根据关键词搜索合约。
    """
    return await market_service.search_contracts(request)


@router.get("/overview", response_model=MarketOverviewResponse, summary="获取市场概览")
async def get_market_overview(
    market_service: MarketService = Depends(get_market_service),
):
    """
    获取市场概览数据，例如涨跌幅排名、成交量排名等。
    """
    return await market_service.get_market_overview()


@router.get("/tick/{symbol}", response_model=TickDataResponse, summary="获取最新Tick数据")
async def get_latest_tick(
    symbol: str,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定合约的最新Tick数据
    
    - **symbol**: 合约代码
    """
    market_service = MarketService(db)
    
    tick_data = await market_service.get_latest_tick(symbol)
    if not tick_data:
        raise HTTPException(status_code=404, detail="未找到Tick数据")
    
    return TickDataResponse(
        symbol=symbol,
        data=TickData.model_validate(tick_data)
    )


@router.get("/tick/{symbol}/history", response_model=List[TickData], summary="获取历史Tick数据")
async def get_tick_history(
    symbol: str,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=10000, description="返回记录数"),
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取历史Tick数据
    
    - **symbol**: 合约代码
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    - **limit**: 返回记录数限制
    """
    market_service = MarketService(db)
    
    # 如果没有指定时间范围，默认返回最近1小时的数据
    if not start_time:
        start_time = datetime.now() - timedelta(hours=1)
    if not end_time:
        end_time = datetime.now()
    
    tick_data = await market_service.get_tick_history(
        symbol=symbol,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return [TickData.model_validate(tick) for tick in tick_data]


@router.get("/bars/{symbol}", response_model=BarDataResponse, summary="获取K线数据")
async def get_bars(
    symbol: str,
    interval: Interval = Query(..., description="K线周期"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(1000, ge=1, le=10000, description="返回记录数"),
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取K线数据
    
    - **symbol**: 合约代码
    - **interval**: K线周期（1m, 5m, 15m, 30m, 1h, 4h, 1d等）
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    - **limit**: 返回记录数限制
    """
    market_service = MarketService(db)
    
    # 如果没有指定时间范围，根据周期设置默认范围
    if not start_time or not end_time:
        now = datetime.now()
        if interval in [Interval.MIN_1, Interval.MIN_5]:
            default_days = 1
        elif interval in [Interval.MIN_15, Interval.MIN_30, Interval.HOUR_1]:
            default_days = 7
        elif interval == Interval.HOUR_4:
            default_days = 30
        else:  # 日线及以上
            default_days = 365
        
        if not start_time:
            start_time = now - timedelta(days=default_days)
        if not end_time:
            end_time = now
    
    bars = await market_service.get_bars(
        symbol=symbol,
        interval=interval,
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )
    
    return BarDataResponse(
        symbol=symbol,
        interval=interval,
        data=[BarData.model_validate(bar) for bar in bars],
        start_time=start_time,
        end_time=end_time
    )


@router.get("/depth/{symbol}", response_model=DepthData, summary="获取市场深度")
async def get_market_depth(
    symbol: str,
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定合约的市场深度数据
    
    - **symbol**: 合约代码
    """
    market_service = MarketService(db)
    
    depth_data = await market_service.get_market_depth(symbol)
    if not depth_data:
        raise HTTPException(status_code=404, detail="未找到深度数据")
    
    return DepthData.model_validate(depth_data)


@router.get("/stats/{symbol}", response_model=MarketStatsData, summary="获取市场统计")
async def get_market_stats(
    symbol: str,
    period: str = Query("1d", description="统计周期（1d, 7d, 30d）"),
    user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    """
    获取市场统计数据
    
    - **symbol**: 合约代码
    - **period**: 统计周期
    """
    market_service = MarketService(db)
    
    stats = await market_service.get_market_stats(symbol, period)
    if not stats:
        raise HTTPException(status_code=404, detail="未找到统计数据")
    
    return MarketStatsData.model_validate(stats)


@router.get("/exchanges", response_model=List[str], summary="获取交易所列表")
async def get_exchanges(
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取支持的交易所列表
    """
    return [exchange.value for exchange in Exchange]


@router.get("/product-classes", response_model=List[str], summary="获取产品类型列表")
async def get_product_classes(
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取支持的产品类型列表
    """
    return [product_class.value for product_class in ProductClass]


@router.get("/intervals", response_model=List[str], summary="获取K线周期列表")
async def get_intervals(
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    获取支持的K线周期列表
    """
    return [interval.value for interval in Interval]


# WebSocket相关端点
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    市场数据WebSocket连接
    
    支持的消息类型：
    - subscribe: 订阅行情数据
    - unsubscribe: 取消订阅
    - ping: 心跳检测
    """
    await websocket.accept()
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_json()
            message = WebSocketMessage(**data)
            
            if message.type == "subscribe":
                # 处理订阅请求
                subscription = SubscriptionMessage(**message.data)
                
                # TODO: 实现订阅逻辑
                response = WebSocketMessage(
                    type="subscription_success",
                    data={
                        "symbols": subscription.symbols,
                        "data_types": subscription.data_types,
                        "message": "订阅成功"
                    }
                )
                await websocket.send_json(response.model_dump())
                
            elif message.type == "unsubscribe":
                # 处理取消订阅请求
                subscription = SubscriptionMessage(**message.data)
                
                # TODO: 实现取消订阅逻辑
                response = WebSocketMessage(
                    type="unsubscription_success",
                    data={
                        "symbols": subscription.symbols,
                        "data_types": subscription.data_types,
                        "message": "取消订阅成功"
                    }
                )
                await websocket.send_json(response.model_dump())
                
            elif message.type == "ping":
                # 心跳响应
                response = WebSocketMessage(
                    type="pong",
                    data={"timestamp": datetime.now().isoformat()}
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
        print("WebSocket连接已断开")
    except Exception as e:
        print(f"WebSocket错误: {e}")
        error_response = WebSocketMessage(
            type="error",
            data={"message": str(e)}
        )
        try:
            await websocket.send_json(error_response.model_dump())
        except:
            pass


@router.get("/health", summary="健康检查")
async def health_check():
    """
    市场数据服务健康检查
    """
    return {
        "status": "healthy",
        "service": "market",
        "timestamp": datetime.now().isoformat(),
        "supported_exchanges": [e.value for e in Exchange],
        "supported_intervals": [i.value for i in Interval]
    }


# ---------------------- 实际接口实现 ----------------------

@router.get("/news", summary="市场资讯")
async def get_market_news(limit: int = Query(20, ge=1, le=100)):
    """返回市场新闻列表"""
    import time
    import random
    
    # 模拟新闻数据
    news_titles = [
        "央行降准释放流动性，市场预期政策继续宽松",
        "科技股领涨，AI概念股表现强劲",
        "新能源汽车销量创新高，相关产业链受益",
        "房地产政策边际放松，地产股集体上涨",
        "美联储加息预期降温，全球股市普遍上涨",
        "中概股回归港股，互联网巨头估值修复",
        "煤炭钢铁等周期股走强，大宗商品价格上涨",
        "医药生物板块分化，创新药企业受关注",
        "消费股回暖，白酒食品饮料表现亮眼",
        "银行股估值修复，金融板块整体向好"
    ]
    
    news_sources = ["财经网", "证券时报", "上海证券报", "中国证券报", "第一财经", "财新网", "新浪财经", "东方财富网"]
    
    mock_news = []
    current_time = int(time.time())
    
    for i in range(min(limit, len(news_titles))):
        news_id = f"news_{current_time}_{i}"
        title = news_titles[i]
        
        mock_news.append({
            "id": news_id,
            "title": title,
            "summary": f"{title[:30]}...",
            "content": f"详细内容：{title}。本文将从多个角度分析市场影响和投资机会。",
            "source": random.choice(news_sources),
            "publishTime": current_time - i * 3600,  # 每小时一条新闻
            "tags": ["市场", "投资", "股票"],
            "relatedSymbols": ["000001.SZ", "000002.SZ", "600000.SH"],
            "importance": random.choice(["low", "medium", "high"]),
            "url": f"https://example.com/news/{news_id}"
        })
    
    return mock_news


@router.get("/sectors", summary="板块数据")
async def get_sectors():
    """返回板块数据"""
    import random
    
    # 模拟板块数据
    sectors = [
        {"name": "银行", "code": "BK0475", "stocks": 42},
        {"name": "房地产", "code": "BK0451", "stocks": 138},
        {"name": "券商信托", "code": "BK0473", "stocks": 54},
        {"name": "保险", "code": "BK0474", "stocks": 12},
        {"name": "煤炭", "code": "BK0437", "stocks": 31},
        {"name": "钢铁", "code": "BK0432", "stocks": 42},
        {"name": "有色金属", "code": "BK0478", "stocks": 65},
        {"name": "石油石化", "code": "BK0401", "stocks": 48},
        {"name": "电力", "code": "BK0428", "stocks": 67},
        {"name": "新能源", "code": "BK0493", "stocks": 156},
        {"name": "汽车", "code": "BK0481", "stocks": 234},
        {"name": "家电", "code": "BK0438", "stocks": 87},
        {"name": "食品饮料", "code": "BK0438", "stocks": 145},
        {"name": "医药生物", "code": "BK0464", "stocks": 312},
        {"name": "电子", "code": "BK0465", "stocks": 289},
        {"name": "计算机", "code": "BK0466", "stocks": 178},
        {"name": "通信", "code": "BK0467", "stocks": 98},
        {"name": "传媒", "code": "BK0468", "stocks": 67}
    ]
    
    mock_sectors = []
    
    for sector in sectors:
        change_percent = random.uniform(-5.0, 5.0)
        change = random.uniform(-2.0, 2.0)
        volume = random.randint(1000000, 50000000)
        turnover = random.uniform(1000000000, 10000000000)
        
        # 生成领涨股
        leading_symbols = ["000001.SZ", "000002.SZ", "600000.SH", "600036.SH", "000858.SZ"]
        leading_names = ["平安银行", "万科A", "浦发银行", "招商银行", "五粮液"]
        
        idx = random.randint(0, len(leading_symbols) - 1)
        
        mock_sectors.append({
            "name": sector["name"],
            "code": sector["code"],
            "change": round(change, 2),
            "changePercent": round(change_percent, 2),
            "volume": volume,
            "turnover": turnover,
            "stocks": sector["stocks"],
            "stockCount": sector["stocks"],  # 兼容前端字段
            "leadingStock": {
                "symbol": leading_symbols[idx],
                "name": leading_names[idx],
                "changePercent": round(change_percent + random.uniform(-1, 1), 2)
            }
        })
    
    return mock_sectors


@router.get("/overview/ranking", summary="市场排行榜")
async def get_ranking(type: str = Query('change_percent', description="排行类型"), limit: int = Query(50, ge=1, le=100)):
    """获取市场排行榜数据"""
    # 模拟排行榜数据
    if type == 'change_percent':
        # 涨幅榜
        ranking_data = [
            {
                "symbol": "000001",
                "name": "平安银行",
                "currentPrice": 13.20,
                "change": 0.70,
                "changePercent": 5.61,
                "volume": 1500000,
                "turnover": 19800000,
                "rank": 1
            },
            {
                "symbol": "000002", 
                "name": "万科A",
                "currentPrice": 23.50,
                "change": -0.50,
                "changePercent": -2.08,
                "volume": 2300000,
                "turnover": 54050000,
                "rank": 2
            },
            {
                "symbol": "000858",
                "name": "五粮液", 
                "currentPrice": 158.00,
                "change": 8.00,
                "changePercent": 5.33,
                "volume": 890000,
                "turnover": 140620000,
                "rank": 3
            },
            {
                "symbol": "600036",
                "name": "招商银行",
                "currentPrice": 45.20,
                "change": 1.80,
                "changePercent": 4.15,
                "volume": 1200000,
                "turnover": 54240000,
                "rank": 4
            },
            {
                "symbol": "600519",
                "name": "贵州茅台",
                "currentPrice": 1680.00,
                "change": -20.00,
                "changePercent": -1.18,
                "volume": 45000,
                "turnover": 75600000,
                "rank": 5
            }
        ]
    elif type == 'turnover':
        # 成交额榜
        ranking_data = [
            {
                "symbol": "600519",
                "name": "贵州茅台",
                "currentPrice": 1680.00,
                "change": -20.00,
                "changePercent": -1.18,
                "volume": 45000,
                "turnover": 75600000,
                "rank": 1
            },
            {
                "symbol": "000858",
                "name": "五粮液",
                "currentPrice": 158.00,
                "change": 8.00,
                "changePercent": 5.33,
                "volume": 890000,
                "turnover": 140620000,
                "rank": 2
            }
        ]
    else:
        ranking_data = []
    
    return ranking_data[:limit]


@router.get("/indices", summary="获取指数数据")
async def get_indices():
    """获取主要股指数据"""
    import random
    
    # 模拟指数数据，带有小幅随机波动
    base_indices = {
        "SH000001": {"name": "上证指数", "base_price": 3200.50, "base_change": 15.30},
        "SZ399001": {"name": "深证成指", "base_price": 12800.20, "base_change": -25.80},
        "SZ399006": {"name": "创业板指", "base_price": 2580.90, "base_change": 8.60},
        "SH000688": {"name": "科创50", "base_price": 1120.40, "base_change": 12.20}
    }
    
    indices_data = []
    for symbol, data in base_indices.items():
        # 添加小幅随机波动
        price_variation = random.uniform(-0.5, 0.5)
        change_variation = random.uniform(-0.2, 0.2)
        
        current_price = data["base_price"] + price_variation
        current_change = data["base_change"] + change_variation
        change_percent = (current_change / (current_price - current_change)) * 100
        
        indices_data.append({
            "symbol": symbol,
            "name": data["name"],
            "currentPrice": round(current_price, 2),
            "change": round(current_change, 2),
            "changePercent": round(change_percent, 2),
            "volume": random.randint(50000000, 100000000),
            "turnover": random.randint(500000000, 1000000000)
        })
    
    return indices_data


@router.get("/stocks", summary="获取股票列表")
async def get_stocks(
    market: Optional[str] = Query(None, description="市场筛选"),
    industry: Optional[str] = Query(None, description="行业筛选"),
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取股票列表数据，支持市场和行业筛选"""
    import random
    
    # 模拟股票数据
    stock_pool = [
        {"symbol": "000001", "name": "平安银行", "industry": "银行", "market": "sz"},
        {"symbol": "000002", "name": "万科A", "industry": "房地产", "market": "sz"},
        {"symbol": "000858", "name": "五粮液", "industry": "白酒", "market": "sz"},
        {"symbol": "600036", "name": "招商银行", "industry": "银行", "market": "sh"},
        {"symbol": "600519", "name": "贵州茅台", "industry": "白酒", "market": "sh"},
        {"symbol": "600000", "name": "浦发银行", "industry": "银行", "market": "sh"},
        {"symbol": "000166", "name": "申万宏源", "industry": "证券", "market": "sz"},
        {"symbol": "600030", "name": "中信证券", "industry": "证券", "market": "sh"},
        {"symbol": "000725", "name": "京东方A", "industry": "电子", "market": "sz"},
        {"symbol": "600276", "name": "恒瑞医药", "industry": "医药", "market": "sh"},
        {"symbol": "300015", "name": "爱尔眼科", "industry": "医药", "market": "cyb"},
        {"symbol": "300750", "name": "宁德时代", "industry": "电池", "market": "cyb"},
        {"symbol": "688981", "name": "中芯国际", "industry": "半导体", "market": "kcb"},
        {"symbol": "688599", "name": "天合光能", "industry": "光伏", "market": "kcb"}
    ]
    
    # 筛选逻辑
    filtered_stocks = stock_pool
    if market and market != "all":
        filtered_stocks = [s for s in filtered_stocks if s["market"] == market]
    if industry:
        filtered_stocks = [s for s in filtered_stocks if s["industry"] == industry]
    
    # 分页
    start = (page - 1) * pageSize
    end = start + pageSize
    page_stocks = filtered_stocks[start:end]
    
    # 添加实时行情数据
    stocks_data = []
    for stock in page_stocks:
        base_price = random.uniform(10, 200)
        change = random.uniform(-10, 10)
        change_percent = (change / base_price) * 100
        
        stocks_data.append({
            "symbol": stock["symbol"],
            "name": stock["name"],
            "industry": stock["industry"],
            "currentPrice": round(base_price, 2),
            "previousClose": round(base_price - change, 2),
            "change": round(change, 2),
            "changePercent": round(change_percent, 2),
            "high": round(base_price + random.uniform(0, 5), 2),
            "low": round(base_price - random.uniform(0, 5), 2),
            "volume": random.randint(100000, 5000000),
            "turnover": random.randint(1000000, 100000000),
            "openPrice": round(base_price + random.uniform(-2, 2), 2),
            "timestamp": int(datetime.now().timestamp()),
            "status": "trading"
        })
    
    return stocks_data