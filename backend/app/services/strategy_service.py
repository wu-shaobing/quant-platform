# 策略服务
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.models.strategy import Strategy
from app.models.user import User
from app.schemas.strategy import (
    StrategyCreate, StrategyUpdate, StrategyType, StrategyStatus,
    StrategySignal, StrategyLog, StrategyPerformance, FrequencyType,
    StrategyOptimizationRequest, StrategyTemplate
)
from app.utils.exceptions import DataNotFoundError


class ValidationResult:
    """代码验证结果"""
    def __init__(self, is_valid: bool, error_message: str = ""):
        self.is_valid = is_valid
        self.error_message = error_message


class StrategyService:
    """策略服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_strategy(self, user_id: int, strategy_data: StrategyCreate) -> Strategy:
        """创建策略"""
        strategy = Strategy(
            user_id=user_id,
            name=strategy_data.name,
            description=strategy_data.description,
            strategy_type=strategy_data.strategy_type,
            frequency=strategy_data.frequency,
            symbols=strategy_data.symbols,
            code=strategy_data.code,
            parameters=strategy_data.parameters,
            risk_limits=strategy_data.risk_limits,
            status=StrategyStatus.INACTIVE,
            created_at=datetime.now()
        )
        
        self.db.add(strategy)
        await self.db.commit()
        await self.db.refresh(strategy)
        
        return strategy
    
    async def get_strategy_by_id(self, strategy_id: int) -> Optional[Strategy]:
        """根据ID获取策略"""
        result = await self.db.execute(
            select(Strategy).where(Strategy.id == strategy_id)
        )
        return result.scalar_one_or_none()
    
    async def get_strategy_by_name(self, user_id: int, name: str) -> Optional[Strategy]:
        """根据名称获取用户策略"""
        result = await self.db.execute(
            select(Strategy).where(
                and_(Strategy.user_id == user_id, Strategy.name == name)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_user_strategies(
        self, 
        user_id: int,
        strategy_type: Optional[StrategyType] = None,
        status: Optional[StrategyStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Strategy], int]:
        """获取用户策略列表"""
        # 构建查询条件
        conditions = [Strategy.user_id == user_id]
        
        if strategy_type:
            conditions.append(Strategy.strategy_type == strategy_type)
        if status:
            conditions.append(Strategy.status == status)
        
        # 查询策略列表
        query = select(Strategy).where(and_(*conditions)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        strategies = result.scalars().all()
        
        # 查询总数
        count_query = select(func.count(Strategy.id)).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return list(strategies), total
    
    async def update_strategy(self, strategy_id: int, strategy_update: StrategyUpdate) -> Strategy:
        """更新策略"""
        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy:
            raise DataNotFoundError("策略不存在")
        
        # 更新字段
        update_data = strategy_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(strategy, field, value)
        
        strategy.updated_at = datetime.now()
        
        await self.db.commit()
        await self.db.refresh(strategy)
        
        return strategy
    
    async def delete_strategy(self, strategy_id: int) -> bool:
        """删除策略"""
        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy:
            raise DataNotFoundError("策略不存在")
        
        await self.db.delete(strategy)
        await self.db.commit()
        
        return True
    
    async def start_strategy(self, strategy_id: int) -> bool:
        """启动策略"""
        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy:
            raise DataNotFoundError("策略不存在")
        
        strategy.status = StrategyStatus.ACTIVE
        strategy.last_run = datetime.now()
        strategy.updated_at = datetime.now()
        
        await self.db.commit()
        
        # TODO: 启动策略执行引擎
        
        return True
    
    async def stop_strategy(self, strategy_id: int) -> bool:
        """停止策略"""
        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy:
            raise DataNotFoundError("策略不存在")
        
        strategy.status = StrategyStatus.STOPPED
        strategy.updated_at = datetime.now()
        
        await self.db.commit()
        
        # TODO: 停止策略执行引擎
        
        return True
    
    async def pause_strategy(self, strategy_id: int) -> bool:
        """暂停策略"""
        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy:
            raise DataNotFoundError("策略不存在")
        
        strategy.status = StrategyStatus.PAUSED
        strategy.updated_at = datetime.now()
        
        await self.db.commit()
        
        return True
    
    async def resume_strategy(self, strategy_id: int) -> bool:
        """恢复策略"""
        strategy = await self.get_strategy_by_id(strategy_id)
        if not strategy:
            raise DataNotFoundError("策略不存在")
        
        strategy.status = StrategyStatus.ACTIVE
        strategy.updated_at = datetime.now()
        
        await self.db.commit()
        
        return True
    
    async def validate_strategy_code(self, code: str) -> ValidationResult:
        """验证策略代码"""
        try:
            # 基本语法检查
            compile(code, '<strategy>', 'exec')
            
            # TODO: 更详细的策略代码验证
            # - 检查必需的函数和类
            # - 检查导入的模块
            # - 检查风险控制逻辑
            
            return ValidationResult(True)
        except SyntaxError as e:
            return ValidationResult(False, f"语法错误: {str(e)}")
        except Exception as e:
            return ValidationResult(False, f"验证失败: {str(e)}")
    
    async def get_strategy_performance(
        self, 
        strategy_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取策略绩效"""
        # TODO: 实现策略绩效计算
        return {
            "total_return": 0.0,
            "annual_return": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "win_rate": 0.0,
            "total_trades": 0
        }
    
    async def get_strategy_signals(
        self,
        strategy_id: int,
        signal_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[StrategySignal]:
        """获取策略信号"""
        # TODO: 实现策略信号查询
        return []
    
    async def get_strategy_logs(
        self,
        strategy_id: int,
        level: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[StrategyLog]:
        """获取策略日志"""
        # TODO: 实现策略日志查询
        return []
    
    async def start_optimization(
        self, 
        strategy_id: int, 
        optimization_request: StrategyOptimizationRequest
    ) -> str:
        """启动策略参数优化"""
        # TODO: 实现策略参数优化
        import uuid
        task_id = str(uuid.uuid4())
        return task_id
    
    async def get_strategy_templates(
        self, 
        strategy_type: Optional[StrategyType] = None
    ) -> List[StrategyTemplate]:
        """获取策略模板"""
        # TODO: 实现策略模板查询
        return []
    
    async def get_user_strategy_stats(self, user_id: int) -> Dict[str, Any]:
        """获取用户策略统计"""
        # 查询各状态策略数量
        result = await self.db.execute(
            select(Strategy.status, func.count(Strategy.id))
            .where(Strategy.user_id == user_id)
            .group_by(Strategy.status)
        )
        status_counts = dict(result.all())
        
        # 查询策略类型分布
        result = await self.db.execute(
            select(Strategy.strategy_type, func.count(Strategy.id))
            .where(Strategy.user_id == user_id)
            .group_by(Strategy.strategy_type)
        )
        type_distribution = dict(result.all())
        
        return {
            "total_strategies": sum(status_counts.values()),
            "active_strategies": status_counts.get(StrategyStatus.ACTIVE, 0),
            "paused_strategies": status_counts.get(StrategyStatus.PAUSED, 0),
            "stopped_strategies": status_counts.get(StrategyStatus.STOPPED, 0),
            "error_strategies": status_counts.get(StrategyStatus.ERROR, 0),
            "strategy_type_distribution": type_distribution,
            "performance_summary": {},
            "top_performers": []
        }