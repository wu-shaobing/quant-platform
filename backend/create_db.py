#!/usr/bin/env python3
"""
数据库初始化脚本
直接使用SQLAlchemy创建所有表结构
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine
from app.core.database import Base
from app.models import *  # 导入所有模型


async def create_tables():
    """创建所有数据库表"""
    # 使用SQLite数据库
    database_url = "sqlite+aiosqlite:///./quant_dev.db"
    
    print(f"🔗 连接数据库: {database_url}")
    
    # 创建异步引擎
    engine = create_async_engine(
        database_url,
        echo=True,  # 显示SQL语句
        future=True
    )
    
    try:
        # 创建所有表
        async with engine.begin() as conn:
            print("📋 创建数据库表结构...")
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ 数据库表创建成功!")
        
        # 显示创建的表
        async with engine.begin() as conn:
            result = await conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = result.fetchall()
            
            print(f"\n📊 已创建 {len(tables)} 个表:")
            for table in tables:
                print(f"  - {table[0]}")
                
    except Exception as e:
        print(f"❌ 创建表失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await engine.dispose()
    
    return True


async def main():
    """主函数"""
    print("🚀 初始化量化投资平台数据库...")
    print("=" * 50)
    
    success = await create_tables()
    
    if success:
        print("=" * 50)
        print("✅ 数据库初始化完成!")
        print("\n📝 下一步:")
        print("  1. 运行 'python scripts/init_db.py' 创建初始数据")
        print("  2. 启动后端服务: 'uvicorn app.main:app --reload'")
    else:
        print("❌ 数据库初始化失败!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
