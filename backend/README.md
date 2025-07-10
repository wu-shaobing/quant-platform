# 量化投资后端

基于FastAPI的量化投资后端平台。

## 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境
```bash
cp .env.example .env
```

### 启动服务
```bash
uvicorn app.main:app --reload
```

### API文档
- http://localhost:8000/docs

## 项目结构
```
backend/
├── app/
│   ├── api/          # API路由
│   ├── core/         # 核心配置
│   ├── models/       # 数据模型
│   ├── services/     # 业务服务
│   └── schemas/      # 数据模式
└── tests/           # 测试文件
```
