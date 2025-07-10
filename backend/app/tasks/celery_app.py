"""
Celery应用配置
"""
import os
from celery import Celery
from app.core.config import settings

# 创建Celery应用
celery_app = Celery(
    "quant_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        'app.tasks.trading_tasks',
        'app.tasks.backtest_tasks'
    ]
)

# Celery配置
celery_app.conf.update(
    # 任务序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务路由
    task_routes={
        'app.tasks.trading_tasks.*': {'queue': 'trading'},
        'app.tasks.backtest_tasks.*': {'queue': 'backtest'},
    },
    
    # 任务结果过期时间
    result_expires=3600,
    
    # 任务重试配置
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # 任务限制
    task_time_limit=300,  # 5分钟
    task_soft_time_limit=240,  # 4分钟
    
    # 监控配置
    worker_send_task_events=True,
    task_send_sent_event=True,
)

# 任务发现
celery_app.autodiscover_tasks()

if __name__ == '__main__':
    celery_app.start()
