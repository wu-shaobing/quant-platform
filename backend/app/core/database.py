"""
数据库连接和会话管理
支持异步操作和连接池管理
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass
from sqlalchemy import event, pool, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """数据库模型基类"""
    pass


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        self.engine: Optional[Engine] = None
        self.async_session_maker: Optional[async_sessionmaker] = None
        self._initialized = False
    
    def initialize(self, database_url: str = None):
        """初始化数据库引擎和会话工厂"""
        if self.engine is None:
            # 强制使用 SQLite, 绕过所有外部配置
            db_url = "sqlite+aiosqlite:///./quant_dev.db"
            
            # 创建异步引擎
            # 注意: SQLite 不支持 pool_size 和 max_overflow
            engine_kwargs = {
                "echo": settings.DEBUG,
                "future": True,
            }
            
            # 根据数据库类型配置连接池 - 性能优化
            if "postgresql" in db_url:
                engine_kwargs.update({
                    "poolclass": QueuePool,
                    "pool_size": 50,  # 增加连接池大小以支持高频交易
                    "max_overflow": 100,  # 增加溢出连接数
                    "pool_timeout": 10,  # 减少超时时间
                    "pool_recycle": 1800,  # 减少连接回收时间
                    "pool_pre_ping": True,  # 启用连接预检
                })
            elif "sqlite" in db_url:
                engine_kwargs.update({
                    "connect_args": {
                        "check_same_thread": False,
                        "timeout": 20,  # 增加超时时间
                        "isolation_level": None,  # 自动提交模式
                    },
                    "poolclass": pool.StaticPool,
                })
            
            self.engine = create_async_engine(db_url, **engine_kwargs)
            logger.info(f"数据库引擎已创建，使用驱动: {self.engine.driver}")
            
            # 创建会话工厂
            self.async_session_maker = async_sessionmaker(
                bind=self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )
            
            self._initialized = True
            logger.info(f"Database initialized: {db_url}")
    
    async def create_tables(self):
        """创建数据库表"""
        if not self.engine:
            raise RuntimeError("Database not initialized")
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created")
    
    async def drop_tables(self):
        """删除数据库表"""
        if not self.engine:
            raise RuntimeError("Database not initialized")
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.info("Database tables dropped")
    
    async def health_check(self) -> bool:
        """数据库健康检查"""
        if not self.engine:
            return False
        
        try:
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def get_connection_info(self) -> dict:
        """获取数据库连接信息"""
        if not self.engine:
            return {"status": "not_initialized"}
        
        pool = self.engine.pool
        return {
            "status": "connected",
            "pool_size": getattr(pool, 'size', lambda: 0)(),
            "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
            "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
            "overflow": getattr(pool, 'overflow', lambda: 0)(),
            "total_connections": getattr(pool, 'size', lambda: 0)() + getattr(pool, 'overflow', lambda: 0)(),
        }
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话"""
        if not self.async_session_maker:
            raise RuntimeError("Database not initialized")
        
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")


# 全局数据库管理器实例
db_manager = DatabaseManager()


# 数据库会话依赖
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话的依赖注入函数"""
    async with db_manager.get_session() as session:
        yield session


# 初始化和清理函数
async def init_db():
    """初始化数据库"""
    db_manager.initialize()
    await db_manager.create_tables()


async def cleanup_db():
    """清理数据库连接"""
    await db_manager.close()


# 数据库事件监听器
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """SQLite性能优化设置 - 针对高频交易优化"""
    if 'sqlite' in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        # 基础设置
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")  # WAL模式提高并发性能
        cursor.execute("PRAGMA synchronous=NORMAL")  # 平衡安全性和性能

        # 性能优化设置
        cursor.execute("PRAGMA cache_size=50000")  # 增加缓存大小到50MB
        cursor.execute("PRAGMA temp_store=MEMORY")  # 临时表存储在内存
        cursor.execute("PRAGMA mmap_size=268435456")  # 启用256MB内存映射
        cursor.execute("PRAGMA page_size=4096")  # 优化页面大小
        cursor.execute("PRAGMA wal_autocheckpoint=1000")  # WAL自动检查点
        cursor.execute("PRAGMA optimize")  # 自动优化

        # 高频交易优化
        cursor.execute("PRAGMA busy_timeout=30000")  # 30秒忙等待
        cursor.execute("PRAGMA locking_mode=NORMAL")  # 正常锁定模式
        cursor.execute("PRAGMA read_uncommitted=1")  # 允许脏读以提高性能

        cursor.close()


@event.listens_for(Engine, "first_connect")
def receive_first_connect(dbapi_connection, connection_record):
    """首次连接时的设置"""
    logger.info("Database first connection established")


@event.listens_for(Engine, "checkout")
def receive_checkout(dbapi_connection, connection_record, connection_proxy):
    """连接检出时的监控"""
    logger.debug("Database connection checked out")


@event.listens_for(Engine, "checkin")
def receive_checkin(dbapi_connection, connection_record):
    """连接检入时的监控"""
    logger.debug("Database connection checked in")


# 数据库连接测试
async def test_connection():
    """测试数据库连接"""
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row.test == 1:
                print("✅ Database connection successful")
                return True
            else:
                print("❌ Database connection failed: Invalid response")
                return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# 导出主要组件
__all__ = [
    "Base",
    "db_manager",
    "get_db",
    "init_db",
    "cleanup_db",
    "test_connection",
]