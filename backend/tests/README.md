# 行情数据处理测试文档

## 概述

本文档描述了量化投资平台行情数据处理模块的完整测试体系，包括单元测试、集成测试、性能测试和压力测试。

## 测试架构

### 1. 测试文件结构

```
tests/
├── conftest.py                           # pytest配置和夹具
├── utils/
│   └── market_data_generator.py          # 行情数据生成器
├── test_market_data_comprehensive.py     # 综合测试套件
├── integration/
│   └── test_market_data_integration.py   # 集成测试
└── performance/
    └── test_market_data_performance.py   # 性能测试
```

### 2. 核心测试组件

#### 行情数据生成器 (MarketDataGenerator)
- **位置**: `tests/utils/market_data_generator.py`
- **功能**: 生成真实的模拟行情数据
- **特性**:
  - 支持多种期货合约（黑色系、有色金属、贵金属、农产品、化工）
  - 几何布朗运动价格模拟
  - 真实交易时段模拟
  - 可配置波动率
  - 支持Tick、K线、深度数据生成

#### 综合测试套件 (TestMarketDataProcessing)
- **位置**: `tests/test_market_data_comprehensive.py`
- **覆盖范围**:
  - 数据接收测试（基础、批量、并发）
  - 数据清洗和验证测试
  - 数据存储测试
  - 缓存功能测试
  - WebSocket实时通信测试
  - 性能测试
  - 集成测试

## 测试用例详情

### 1. 数据接收测试

#### 基础数据接收 (test_data_reception_basic)
- 测试单个Tick数据的接收和处理
- 验证数据格式和类型正确性
- 确保处理统计正确更新

#### 批量数据处理 (test_data_reception_batch)
- 测试批量Tick数据的高效处理
- 验证批量处理的性能指标
- 确保数据完整性

#### 并发数据处理 (test_data_reception_concurrent)
- 测试多线程/协程并发处理能力
- 验证并发安全性
- 测试资源竞争处理

### 2. 数据清洗和验证测试

#### 无效价格处理 (test_data_cleaning_invalid_prices)
- 测试零价格、负价格的处理
- 验证价格范围验证
- 确保异常数据被正确过滤

#### 极值处理 (test_data_cleaning_extreme_values)
- 测试价格跳空、异常波动的处理
- 验证极值检测算法
- 确保数据平滑处理

#### 时间戳验证 (test_data_cleaning_timestamp_validation)
- 测试时间戳格式验证
- 验证时间序列连续性
- 确保时区处理正确

### 3. 数据存储测试

#### Tick数据存储 (test_data_storage_tick_data)
- 测试Tick数据的数据库存储
- 验证存储性能和完整性
- 测试存储错误处理

#### K线数据存储 (test_data_storage_kline_data)
- 测试K线数据的存储和聚合
- 验证OHLC数据正确性
- 测试时间窗口处理

#### 深度数据存储 (test_data_storage_depth_data)
- 测试市场深度数据存储
- 验证买卖盘数据结构
- 测试深度数据压缩

### 4. 缓存功能测试

#### 内存缓存 (test_caching_tick_cache)
- 测试Tick数据内存缓存
- 验证缓存容量限制
- 测试LRU淘汰策略

#### Redis缓存 (test_caching_redis_integration)
- 测试Redis分布式缓存
- 验证缓存过期机制
- 测试缓存一致性

#### 缓存性能 (test_caching_performance)
- 测试缓存读写性能
- 验证缓存命中率
- 测试缓存并发访问

### 5. WebSocket实时通信测试

#### 客户端管理 (test_websocket_client_management)
- 测试WebSocket客户端连接管理
- 验证客户端订阅机制
- 测试连接断开处理

#### 数据推送 (test_websocket_selective_push)
- 测试选择性数据推送
- 验证订阅过滤机制
- 测试推送性能

#### 错误处理 (test_websocket_error_handling)
- 测试WebSocket错误处理
- 验证客户端重连机制
- 测试异常恢复

### 6. 性能测试

#### 高频处理 (test_performance_high_frequency)
- 测试高频Tick数据处理能力
- 目标: >10,000 TPS
- 验证延迟: <0.1ms平均延迟

#### 内存优化 (test_performance_memory_optimization)
- 测试内存使用优化
- 验证内存泄漏防护
- 目标: <100MB内存增长

#### 并发性能 (test_performance_concurrent_processing)
- 测试并发处理性能
- 验证多核利用率
- 测试负载均衡

### 7. 集成测试

#### 端到端流程 (test_complete_data_pipeline)
- 测试完整数据处理流程
- 验证组件间协作
- 测试数据一致性

#### 多交易所集成 (test_multi_exchange_data_handling)
- 测试多交易所数据处理
- 验证交易所特定逻辑
- 测试数据标准化

#### 故障恢复 (test_data_recovery_after_failure)
- 测试系统故障恢复能力
- 验证数据完整性保护
- 测试自动重试机制

## 性能基准

### 吞吐量指标
- **Tick数据处理**: ≥10,000 条/秒
- **K线生成**: ≥1,000 条/秒
- **WebSocket推送**: ≥50,000 消息/秒

### 延迟指标
- **数据处理延迟**: <0.1ms (平均)
- **WebSocket推送延迟**: <10ms (99分位)
- **数据库存储延迟**: <1ms (平均)

### 资源使用
- **内存增长**: <100MB (持续运行)
- **CPU使用率**: <50% (正常负载)
- **网络带宽**: <100Mbps (峰值)

## 测试数据

### 支持的合约类型
- **黑色系**: rb2405, hc2405, i2405, j2405, jm2405
- **有色金属**: cu2405, al2405, zn2405, pb2405, ni2405
- **贵金属**: au2406, ag2406
- **农产品**: c2405, m2405, y2405, p2405, a2405
- **化工**: MA2405, TA2405, PF2405, PP2405, V2405

### 数据特征
- **价格范围**: 基于真实市场价格
- **波动率**: 0.01-0.05 (可配置)
- **成交量**: 1-50,000 (随机分布)
- **时间间隔**: 50ms-1s (可配置)

## 运行测试

### 环境要求
```bash
# 安装依赖
pip install -r requirements-dev.txt

# 设置环境变量
export TESTING=true
export LOG_LEVEL=DEBUG
```

### 运行单个测试
```bash
# 运行基础数据生成测试
python -m pytest tests/test_market_data_comprehensive.py::TestMarketDataProcessing::test_data_reception_basic -v

# 运行性能测试
python -m pytest tests/performance/test_market_data_performance.py::TestMarketDataThroughput -v

# 运行集成测试
python -m pytest tests/integration/test_market_data_integration.py -v
```

### 运行完整测试套件
```bash
# 运行所有行情数据测试
python -m pytest tests/test_market_data_comprehensive.py -v

# 运行性能测试（标记为slow）
python -m pytest -m "performance" -v

# 运行集成测试
python -m pytest -m "integration" -v
```

### 生成测试报告
```bash
# 生成HTML报告
python -m pytest tests/ --html=reports/test_report.html --self-contained-html

# 生成覆盖率报告
python -m pytest tests/ --cov=app.services.market_data_service --cov-report=html
```

## 测试配置

### pytest配置 (pytest.ini)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    performance: marks tests as performance tests
    stress: marks tests as stress tests
```

### 测试夹具 (conftest.py)
- 数据库会话夹具
- Redis连接夹具
- 行情数据服务夹具
- 模拟WebSocket夹具
- 测试数据生成夹具

## 持续集成

### GitHub Actions配置
```yaml
name: Market Data Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run tests
        run: python -m pytest tests/test_market_data_comprehensive.py -v
```

## 故障排除

### 常见问题

1. **导入错误**
   - 确保PYTHONPATH包含项目根目录
   - 检查依赖包是否正确安装

2. **数据库连接错误**
   - 确保测试数据库配置正确
   - 检查数据库权限设置

3. **Redis连接错误**
   - 确保Redis服务运行
   - 检查Redis连接配置

4. **性能测试失败**
   - 检查系统资源使用情况
   - 调整性能基准阈值

### 调试技巧

1. **启用详细日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **使用pytest调试模式**
   ```bash
   python -m pytest tests/ -v -s --pdb
   ```

3. **性能分析**
   ```bash
   python -m pytest tests/ --profile
   ```

## 贡献指南

### 添加新测试
1. 在相应的测试文件中添加测试方法
2. 使用适当的测试夹具
3. 添加必要的断言和验证
4. 更新文档

### 测试命名规范
- 测试类: `Test<功能名>`
- 测试方法: `test_<具体功能>_<测试场景>`
- 测试文件: `test_<模块名>.py`

### 代码覆盖率要求
- 核心功能: >90%
- 工具函数: >80%
- 异常处理: >70%
