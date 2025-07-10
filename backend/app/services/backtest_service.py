# 回测服务
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.backtest import BacktestTask as Backtest
from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.backtest import (
    BacktestCreate, BacktestUpdate, BacktestStatus, 
    BacktestAnalysisRequest, BacktestOptimizationConfig
)
from app.utils.exceptions import DataNotFoundError


class BacktestService:
    """回测服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_backtest(self, user_id: int, backtest_data: BacktestCreate) -> Backtest:
        """创建回测任务"""
        backtest = Backtest(
            user_id=user_id,
            name=backtest_data.name,
            description=backtest_data.description,
            strategy_id=backtest_data.strategy_id,
            start_date=backtest_data.start_date,
            end_date=backtest_data.end_date,
            initial_capital=backtest_data.initial_capital,
            symbols=backtest_data.symbols,
            benchmark=backtest_data.benchmark,
            commission_rate=backtest_data.commission_rate,
            slippage_rate=backtest_data.slippage_rate,
            rebalance_frequency=backtest_data.rebalance_frequency,
            max_position_size=backtest_data.max_position_size,
            parameters=backtest_data.parameters,
            status=BacktestStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.db.add(backtest)
        await self.db.commit()
        await self.db.refresh(backtest)
        
        return backtest
    
    async def get_backtest_by_id(self, backtest_id: int) -> Optional[Backtest]:
        """根据ID获取回测"""
        result = await self.db.execute(
            select(Backtest).where(Backtest.id == backtest_id)
        )
        return result.scalar_one_or_none()
    
    async def get_strategy_by_id(self, strategy_id: int) -> Optional[Strategy]:
        """根据ID获取策略"""
        result = await self.db.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_backtests(
        self, 
        user_id: int,
        status: Optional[BacktestStatus] = None,
        strategy_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Backtest], int]:
        """获取用户回测列表"""
        # 构建查询条件
        conditions = [Backtest.user_id == user_id]
        
        if status:
            conditions.append(Backtest.status == status)
        if strategy_id:
            conditions.append(Backtest.strategy_id == strategy_id)
        
        # 查询回测列表
        query = select(Backtest).where(and_(*conditions)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        backtests = result.scalars().all()
        
        # 查询总数
        count_query = select(func.count(Backtest.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return list(backtests), total
    
    async def update_backtest(self, backtest_id: int, backtest_update: BacktestUpdate) -> Backtest:
        """更新回测配置"""
        backtest = await self.get_backtest_by_id(backtest_id)
        if not backtest:
            raise DataNotFoundError("回测不存在")
        
        # 更新字段
        update_data = backtest_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(backtest, field, value)
        
        backtest.updated_at = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(backtest)
        
        return backtest
    
    async def delete_backtest(self, backtest_id: int) -> bool:
        """删除回测"""
        backtest = await self.get_backtest_by_id(backtest_id)
        if not backtest:
            raise DataNotFoundError("回测不存在")
        
        await self.db.delete(backtest)
        await self.db.commit()
        
        return True
    
    async def start_backtest(self, backtest_id: int) -> bool:
        """启动回测"""
        backtest = await self.get_backtest_by_id(backtest_id)
        if not backtest:
            raise DataNotFoundError("回测不存在")
        
        backtest.status = BacktestStatus.RUNNING
        backtest.started_at = datetime.now()
        backtest.updated_at = datetime.now()
        
        await self.db.commit()
        
        return True
    
    async def stop_backtest(self, backtest_id: int) -> bool:
        """停止回测"""
        backtest = await self.get_backtest_by_id(backtest_id)
        if not backtest:
            raise DataNotFoundError("回测不存在")
        
        backtest.status = BacktestStatus.STOPPED
        backtest.updated_at = datetime.now()
        
        await self.db.commit()
        
        return True
    
    async def complete_backtest(self, backtest_id: int, result_data: Dict[str, Any]) -> bool:
        """完成回测"""
        backtest = await self.get_backtest_by_id(backtest_id)
        if not backtest:
            raise DataNotFoundError("回测不存在")
        
        backtest.status = BacktestStatus.COMPLETED
        backtest.completed_at = datetime.now()
        backtest.updated_at = datetime.now()
        backtest.result = result_data
        
        await self.db.commit()
        
        return True
    
    async def run_backtest_task(self, backtest_id: int) -> None:
        """运行回测任务（后台任务）"""
        try:
            # 更新状态为运行中
            await self.start_backtest(backtest_id)
            
            # TODO: 实现实际的回测逻辑
            # 1. 获取历史数据
            # 2. 运行策略
            # 3. 计算绩效指标
            # 4. 保存结果
            
            # 模拟回测运行时间
            import asyncio
            await asyncio.sleep(5)
            
            # 模拟回测结果
            result_data = {
                "total_return": 0.15,
                "annual_return": 0.12,
                "max_drawdown": 0.08,
                "sharpe_ratio": 1.2,
                "win_rate": 0.65,
                "total_trades": 100,
                "profit_loss_ratio": 1.8,
                "volatility": 0.15
            }
            
            # 完成回测
            await self.complete_backtest(backtest_id, result_data)
            
        except Exception as e:
            # 回测失败
            backtest = await self.get_backtest_by_id(backtest_id)
            if backtest:
                backtest.status = BacktestStatus.FAILED
                backtest.error_message = str(e)
                backtest.updated_at = datetime.now()
                await self.db.commit()
    
    async def get_backtest_result(self, backtest_id: int) -> Optional[Dict[str, Any]]:
        """获取回测结果"""
        backtest = await self.get_backtest_by_id(backtest_id)
        if not backtest:
            raise DataNotFoundError("回测不存在")
        
        return backtest.result
    
    async def get_daily_returns(self, backtest_id: int) -> List[Dict[str, Any]]:
        """获取每日收益数据"""
        # TODO: 实现每日收益查询
        return []
    
    async def get_backtest_positions(
        self, 
        backtest_id: int, 
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取回测持仓记录"""
        # TODO: 实现持仓记录查询
        return []
    
    async def get_backtest_trades(
        self, 
        backtest_id: int, 
        symbol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取回测交易记录"""
        # TODO: 实现交易记录查询
        return []
    
    async def analyze_backtest(
        self, 
        backtest_id: int, 
        analysis_request: BacktestAnalysisRequest
    ) -> Dict[str, Any]:
        """分析回测结果"""
        # TODO: 实现回测分析
        return {
            "analysis_type": analysis_request.analysis_type,
            "metrics": {},
            "charts": [],
            "insights": []
        }
    
    async def start_optimization_task(
        self, 
        backtest_id: int, 
        optimization_config: BacktestOptimizationConfig
    ) -> str:
        """启动参数优化任务"""
        # TODO: 实现参数优化
        import uuid
        task_id = str(uuid.uuid4())
        return task_id
    
    async def run_optimization_task(self, task_id: str) -> None:
        """运行参数优化任务"""
        # TODO: 实现参数优化逻辑
        pass
    
    async def generate_report(
        self, 
        backtest_id: int, 
        report_format: str = "json"
    ) -> Dict[str, Any]:
        """生成回测报告"""
        backtest = await self.get_backtest_by_id(backtest_id)
        if not backtest:
            raise DataNotFoundError("回测不存在")
        
        # TODO: 实现报告生成
        return {
            "backtest_id": backtest_id,
            "name": backtest.name,
            "format": report_format,
            "generated_at": datetime.now().isoformat(),
            "summary": backtest.result or {},
            "sections": []
        }
    
    async def compare_backtests(self, backtest_ids: List[int]) -> Dict[str, Any]:
        """对比多个回测结果"""
        # TODO: 实现回测对比
        return {
            "backtest_ids": backtest_ids,
            "comparison_metrics": {},
            "charts": [],
            "insights": []
        }
    
    async def get_user_backtest_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户回测统计"""
        # 查询各状态回测数量
        result = await self.db.execute(
            select(Backtest.status, func.count(Backtest.id))
            .where(Backtest.user_id == user_id)
            .group_by(Backtest.status)
        )
        status_counts = dict(result.all())
        
        # 查询最近回测
        recent_result = await self.db.execute(
            select(Backtest)
            .where(Backtest.user_id == user_id)
            .order_by(desc(Backtest.created_at))
            .limit(5)
        )
        recent_backtests = recent_result.scalars().all()
        
        return {
            "total_backtests": sum(status_counts.values()),
            "pending_backtests": status_counts.get(BacktestStatus.PENDING, 0),
            "running_backtests": status_counts.get(BacktestStatus.RUNNING, 0),
            "completed_backtests": status_counts.get(BacktestStatus.COMPLETED, 0),
            "failed_backtests": status_counts.get(BacktestStatus.FAILED, 0),
            "recent_backtests": [
                {
                    "id": bt.id,
                    "name": bt.name,
                    "status": bt.status,
                    "created_at": bt.created_at.isoformat()
                }
                for bt in recent_backtests
            ]
        }