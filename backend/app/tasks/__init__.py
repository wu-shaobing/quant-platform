"""
异步任务模块
"""
from .celery_app import celery_app
from .trading_tasks import (
    process_order_async,
    process_trade_async,
    generate_trading_report,
    calculate_portfolio_metrics
)
from .backtest_tasks import (
    run_backtest_async,
    generate_backtest_report
)

__all__ = [
    'celery_app',
    'process_order_async',
    'process_trade_async', 
    'generate_trading_report',
    'calculate_portfolio_metrics',
    'run_backtest_async',
    'generate_backtest_report'
]
