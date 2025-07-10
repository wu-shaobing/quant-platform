@property
def DATABASE_URL(self) -> str:
    """
    构建数据库连接URL
    优先使用PostgreSQL，如果未配置则使用SQLite
    """
    if self.POSTGRES_USER and self.POSTGRES_PASSWORD and self.POSTGRES_SERVER:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    return f"sqlite+aiosqlite:///./{self.SQLITE_DB_NAME}"

class Config:
    env_file = ".env"
    case_sensitive = True 