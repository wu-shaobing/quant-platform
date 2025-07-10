#!/usr/bin/env python3
"""
检查数据库状态
"""
import sqlite3
import sys
from pathlib import Path

def check_database():
    """检查数据库表结构"""
    db_path = "quant_dev.db"
    
    if not Path(db_path).exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"📊 数据库文件: {db_path}")
        print(f"📋 表数量: {len(tables)}")
        
        if tables:
            print("\n🗂️ 表列表:")
            for table in tables:
                table_name = table[0]
                print(f"  - {table_name}")
                
                # 获取表结构
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                print(f"    列数: {len(columns)}")
        else:
            print("⚠️ 数据库中没有表")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")
        return False

if __name__ == "__main__":
    print("🔍 检查数据库状态...")
    print("=" * 40)
    
    success = check_database()
    
    if success:
        print("\n✅ 数据库检查完成")
    else:
        print("\n❌ 数据库检查失败")
        sys.exit(1)
