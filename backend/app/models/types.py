"""
通用数据类型定义
提供跨数据库兼容的数据类型
"""
import uuid
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID


class GUID(TypeDecorator):
    """
    通用UUID类型，兼容SQLite和PostgreSQL
    
    在PostgreSQL中使用原生UUID类型
    在SQLite中使用CHAR(36)存储UUID字符串
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        """根据数据库方言加载对应的实现"""
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgresUUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        """处理绑定参数"""
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        """处理查询结果"""
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


# 导出类型
__all__ = ['GUID']
