import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate, Counter, Trend } from 'k6/metrics';

// 自定义指标
const errorRate = new Rate('errors');
const wsConnections = new Counter('websocket_connections');
const wsMessages = new Counter('websocket_messages');
const apiResponseTime = new Trend('api_response_time');
const wsLatency = new Trend('websocket_latency');

// 测试配置 - 扩展为更严格的负载测试
export let options = {
  scenarios: {
    // API负载测试
    api_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 50 },   // 2分钟内增加到50用户
        { duration: '5m', target: 50 },   // 保持50用户5分钟
        { duration: '2m', target: 100 },  // 2分钟内增加到100用户
        { duration: '5m', target: 100 },  // 保持100用户5分钟
        { duration: '2m', target: 200 },  // 2分钟内增加到200用户
        { duration: '5m', target: 200 },  // 保持200用户5分钟
        { duration: '3m', target: 0 },    // 3分钟内减少到0用户
      ],
      exec: 'apiLoadTest',
    },
    // WebSocket压力测试
    websocket_stress: {
      executor: 'constant-vus',
      vus: 100,
      duration: '10m',
      exec: 'websocketStressTest',
    },
    // 高频交易模拟
    high_frequency_trading: {
      executor: 'constant-arrival-rate',
      rate: 1000, // 每秒1000个请求
      timeUnit: '1s',
      duration: '5m',
      preAllocatedVUs: 50,
      maxVUs: 100,
      exec: 'highFrequencyTest',
    },
    // 数据库压力测试
    database_stress: {
      executor: 'ramping-arrival-rate',
      startRate: 100,
      stages: [
        { duration: '2m', target: 500 },  // 增加到每秒500请求
        { duration: '5m', target: 500 },  // 保持每秒500请求
        { duration: '2m', target: 1000 }, // 增加到每秒1000请求
        { duration: '3m', target: 1000 }, // 保持每秒1000请求
        { duration: '2m', target: 0 },    // 减少到0
      ],
      preAllocatedVUs: 100,
      maxVUs: 200,
      exec: 'databaseStressTest',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'], // 95%请求<500ms, 99%请求<1000ms
    http_req_failed: ['rate<0.05'],                  // 错误率<5%
    errors: ['rate<0.05'],                           // 自定义错误率<5%
    websocket_connections: ['count>500'],            // WebSocket连接数>500
    websocket_messages: ['count>10000'],             // WebSocket消息数>10000
    api_response_time: ['p(95)<300'],                // API响应时间95%<300ms
    ws_latency: ['p(95)<100'],                       // WebSocket延迟95%<100ms
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const WS_URL = __ENV.WS_URL || 'ws://localhost:8000';

// 测试数据
const TEST_SYMBOLS = ['rb2405', 'hc2405', 'i2405', 'j2405', 'cu2405', 'al2405', 'au2406', 'ag2406'];
const TEST_USERS = [
  { username: 'testuser1', password: 'testpass123' },
  { username: 'testuser2', password: 'testpass123' },
  { username: 'testuser3', password: 'testpass123' },
  { username: 'trader1', password: 'trader123' },
  { username: 'trader2', password: 'trader123' },
];

// API负载测试
export function apiLoadTest() {
  testAuthAPI();
  testMarketDataAPI();
  testTradingAPI();
  testCTPAPI();
  
  sleep(Math.random() * 2 + 1); // 1-3秒随机间隔
}

// WebSocket压力测试
export function websocketStressTest() {
  testWebSocketConnection();
  sleep(5);
}

// 高频交易模拟
export function highFrequencyTest() {
  testHighFrequencyTrading();
}

// 数据库压力测试
export function databaseStressTest() {
  testDatabaseOperations();
}

function testAuthAPI() {
  let user = TEST_USERS[Math.floor(Math.random() * TEST_USERS.length)];
  let loginPayload = JSON.stringify(user);
  
  let params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  let startTime = Date.now();
  let response = http.post(`${BASE_URL}/api/v1/auth/login`, loginPayload, params);
  let endTime = Date.now();
  
  apiResponseTime.add(endTime - startTime);
  
  let success = check(response, {
    'login status is 200': (r) => r.status === 200,
    'login response time < 500ms': (r) => r.timings.duration < 500,
    'login has access token': (r) => r.json('access_token') !== undefined,
  });
  
  errorRate.add(!success);
  
  if (success && response.json('access_token')) {
    // 测试token验证
    let token = response.json('access_token');
    let authParams = {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    };
    
    let profileResponse = http.get(`${BASE_URL}/api/v1/auth/profile`, authParams);
    check(profileResponse, {
      'profile status is 200': (r) => r.status === 200,
      'profile has user info': (r) => r.json('username') !== undefined,
    });
    
    // 测试权限验证
    let permissionsResponse = http.get(`${BASE_URL}/api/v1/auth/permissions`, authParams);
    check(permissionsResponse, {
      'permissions status is 200': (r) => r.status === 200,
    });
  }
}

function testMarketDataAPI() {
  let symbol = TEST_SYMBOLS[Math.floor(Math.random() * TEST_SYMBOLS.length)];
  
  // 测试实时行情
  let startTime = Date.now();
  let tickResponse = http.get(`${BASE_URL}/api/v1/market/ticks/${symbol}`);
  let endTime = Date.now();
  
  apiResponseTime.add(endTime - startTime);
  
  let success = check(tickResponse, {
    'tick data status is 200': (r) => r.status === 200,
    'tick data response time < 200ms': (r) => r.timings.duration < 200,
    'tick data has content': (r) => r.body.length > 0,
    'tick data has symbol': (r) => r.json('symbol') === symbol,
  });
  
  errorRate.add(!success);
  
  // 测试K线数据
  let klineResponse = http.get(`${BASE_URL}/api/v1/market/klines/${symbol}?interval=1m&limit=100`);
  check(klineResponse, {
    'kline data status is 200': (r) => r.status === 200,
    'kline data is array': (r) => Array.isArray(r.json()),
  });
  
  // 测试深度数据
  let depthResponse = http.get(`${BASE_URL}/api/v1/market/depth/${symbol}`);
  check(depthResponse, {
    'depth data status is 200': (r) => r.status === 200,
    'depth data has bids': (r) => r.json('bids') !== undefined,
    'depth data has asks': (r) => r.json('asks') !== undefined,
  });
}

function testTradingAPI() {
  // 获取认证token
  let user = TEST_USERS[Math.floor(Math.random() * TEST_USERS.length)];
  let loginResponse = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify(user), {
    headers: { 'Content-Type': 'application/json' }
  });
  
  if (loginResponse.status === 200) {
    let token = loginResponse.json('access_token');
    let authParams = {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    };
    
    // 测试获取持仓
    let positionsResponse = http.get(`${BASE_URL}/api/v1/trading/positions`, authParams);
    check(positionsResponse, {
      'positions status is 200': (r) => r.status === 200,
      'positions is array': (r) => Array.isArray(r.json()),
    });
    
    // 测试获取订单
    let ordersResponse = http.get(`${BASE_URL}/api/v1/trading/orders`, authParams);
    check(ordersResponse, {
      'orders status is 200': (r) => r.status === 200,
      'orders is array': (r) => Array.isArray(r.json()),
    });
    
    // 测试获取账户信息
    let accountResponse = http.get(`${BASE_URL}/api/v1/trading/account`, authParams);
    check(accountResponse, {
      'account status is 200': (r) => r.status === 200,
      'account has balance': (r) => r.json('balance') !== undefined,
    });
    
    // 测试风险检查
    let riskResponse = http.get(`${BASE_URL}/api/v1/trading/risk`, authParams);
    check(riskResponse, {
      'risk status is 200': (r) => r.status === 200,
    });
  }
}

function testCTPAPI() {
  // 获取认证token
  let user = TEST_USERS[Math.floor(Math.random() * TEST_USERS.length)];
  let loginResponse = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify(user), {
    headers: { 'Content-Type': 'application/json' }
  });

  if (loginResponse.status === 200) {
    let token = loginResponse.json('access_token');
    let authParams = {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    };

    // 测试CTP连接状态
    let statusResponse = http.get(`${BASE_URL}/api/v1/ctp/status`, authParams);
    check(statusResponse, {
      'ctp status is 200': (r) => r.status === 200,
      'ctp has connection status': (r) => r.json('connected') !== undefined,
    });

    // 测试CTP账户信息
    let ctpAccountResponse = http.get(`${BASE_URL}/api/v1/ctp/account`, authParams);
    check(ctpAccountResponse, {
      'ctp account status is 200': (r) => r.status === 200,
    });

    // 测试CTP持仓信息
    let ctpPositionsResponse = http.get(`${BASE_URL}/api/v1/ctp/positions`, authParams);
    check(ctpPositionsResponse, {
      'ctp positions status is 200': (r) => r.status === 200,
    });
  }
}

function testWebSocketConnection() {
  let url = `${WS_URL}/ws/market`;
  let symbols = TEST_SYMBOLS.slice(0, 3); // 订阅前3个合约
  let messageCount = 0;
  let connectionStartTime = Date.now();

  let response = ws.connect(url, {}, function (socket) {
    wsConnections.add(1);

    socket.on('open', function open() {
      console.log(`WebSocket连接已建立 - VU: ${__VU}`);

      // 订阅行情数据
      socket.send(JSON.stringify({
        action: 'subscribe',
        symbols: symbols
      }));
    });

    socket.on('message', function (message) {
      let messageTime = Date.now();
      wsMessages.add(1);
      messageCount++;

      try {
        let data = JSON.parse(message);

        // 计算延迟（如果消息包含时间戳）
        if (data.timestamp) {
          let latency = messageTime - new Date(data.timestamp).getTime();
          wsLatency.add(latency);
        }

        check(data, {
          'websocket message has symbol': (d) => d.symbol !== undefined,
          'websocket message has price': (d) => d.last_price !== undefined,
          'websocket message has timestamp': (d) => d.timestamp !== undefined,
        });
      } catch (e) {
        console.error(`WebSocket消息解析错误: ${e}`);
        errorRate.add(1);
      }
    });

    socket.on('error', function (e) {
      console.error(`WebSocket错误: ${e}`);
      errorRate.add(1);
    });

    socket.on('close', function close() {
      console.log(`WebSocket连接已关闭 - VU: ${__VU}, 收到消息: ${messageCount}`);
    });

    // 保持连接并定期发送心跳
    for (let i = 0; i < 10; i++) {
      sleep(1);

      // 发送心跳
      if (i % 3 === 0) {
        socket.send(JSON.stringify({
          action: 'ping',
          timestamp: Date.now()
        }));
      }

      // 随机取消订阅和重新订阅
      if (i === 5) {
        socket.send(JSON.stringify({
          action: 'unsubscribe',
          symbols: [symbols[0]]
        }));
      }

      if (i === 7) {
        socket.send(JSON.stringify({
          action: 'subscribe',
          symbols: [symbols[0]]
        }));
      }
    }
  });

  check(response, {
    'websocket connection successful': (r) => r && r.status === 101,
  });
}

function testHighFrequencyTrading() {
  // 模拟高频交易场景
  let symbol = TEST_SYMBOLS[Math.floor(Math.random() * TEST_SYMBOLS.length)];

  // 快速获取行情数据
  let startTime = Date.now();
  let tickResponse = http.get(`${BASE_URL}/api/v1/market/ticks/${symbol}`);
  let endTime = Date.now();

  apiResponseTime.add(endTime - startTime);

  let success = check(tickResponse, {
    'hft tick data status is 200': (r) => r.status === 200,
    'hft tick data response time < 50ms': (r) => r.timings.duration < 50,
  });

  errorRate.add(!success);

  // 如果有有效的行情数据，模拟快速下单
  if (success && tickResponse.json('last_price')) {
    let user = TEST_USERS[Math.floor(Math.random() * TEST_USERS.length)];
    let loginResponse = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify(user), {
      headers: { 'Content-Type': 'application/json' }
    });

    if (loginResponse.status === 200) {
      let token = loginResponse.json('access_token');
      let authParams = {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      };

      // 模拟快速下单（测试订单，不会真实执行）
      let orderPayload = JSON.stringify({
        symbol: symbol,
        side: Math.random() > 0.5 ? 'buy' : 'sell',
        type: 'limit',
        quantity: 1,
        price: tickResponse.json('last_price'),
        test_order: true // 标记为测试订单
      });

      let orderStartTime = Date.now();
      let orderResponse = http.post(`${BASE_URL}/api/v1/trading/orders`, orderPayload, authParams);
      let orderEndTime = Date.now();

      apiResponseTime.add(orderEndTime - orderStartTime);

      check(orderResponse, {
        'hft order response time < 100ms': (r) => r.timings.duration < 100,
        'hft order status is valid': (r) => r.status === 200 || r.status === 201,
      });
    }
  }
}

function testDatabaseOperations() {
  // 测试数据库密集型操作
  let symbol = TEST_SYMBOLS[Math.floor(Math.random() * TEST_SYMBOLS.length)];

  // 测试历史数据查询
  let historyResponse = http.get(`${BASE_URL}/api/v1/market/history/${symbol}?days=30`);
  check(historyResponse, {
    'history data status is 200': (r) => r.status === 200,
    'history data response time < 1000ms': (r) => r.timings.duration < 1000,
  });

  // 测试聚合查询
  let statsResponse = http.get(`${BASE_URL}/api/v1/market/stats/${symbol}`);
  check(statsResponse, {
    'stats data status is 200': (r) => r.status === 200,
    'stats data response time < 500ms': (r) => r.timings.duration < 500,
  });

  // 测试多合约查询
  let multiSymbolResponse = http.get(`${BASE_URL}/api/v1/market/ticks?symbols=${TEST_SYMBOLS.slice(0, 5).join(',')}`);
  check(multiSymbolResponse, {
    'multi symbol status is 200': (r) => r.status === 200,
    'multi symbol response time < 300ms': (r) => r.timings.duration < 300,
  });
}
