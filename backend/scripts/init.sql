-- 量化投资平台数据库初始化脚本
-- 创建必要的扩展和初始数据

-- 启用必要的PostgreSQL扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "timescaledb" CASCADE;

-- 创建数据库用户（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'quant_user') THEN
        CREATE ROLE quant_user LOGIN PASSWORD 'quant_password';
    END IF;
END
$$;

-- 授予权限
GRANT CONNECT ON DATABASE quant_db TO quant_user;
GRANT USAGE ON SCHEMA public TO quant_user;
GRANT CREATE ON SCHEMA public TO quant_user;

-- 设置时区
SET timezone = 'Asia/Shanghai';

-- 创建基础表结构（这些将由Alembic管理，这里只是占位符）
-- 实际的表结构将通过SQLAlchemy模型和Alembic迁移创建

-- 创建索引模板
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_market_data_symbol_time 
-- ON market_data(symbol, created_at DESC);

-- 插入初始数据
-- INSERT INTO settings (key, value, description) VALUES
-- ('system.version', '1.0.0', '系统版本'),
-- ('market.trading_hours', '09:30-15:00', '交易时间'),
-- ('risk.max_position_ratio', '0.1', '最大持仓比例')
-- ON CONFLICT (key) DO NOTHING;

-- 设置数据库参数优化
ALTER SYSTEM SET shared_preload_libraries = 'timescaledb';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET work_mem = '4MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- 创建数据库函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 提交设置
SELECT pg_reload_conf(); 