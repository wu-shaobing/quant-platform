import http from 'k6/http';
import ws from 'k6/ws';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// 自定义指标
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time');
const wsConnections = new Counter('ws_connections');
const wsMessages = new Counter('ws_messages');

// 测试配置
export const options = {
  stages: [
    { duration: '2m', target: 10 },   // 预热阶段
    { duration: '5m', target: 50 },   // 负载增加
    { duration: '10m', target: 100 }, // 稳定负载
    { duration: '5m', target: 200 },  // 峰值负载
    { duration: '5m', target: 100 },  // 负载下降
    { duration: '2m', target: 0 },    // 冷却阶段
  ],
  thresholds: {
    http_req_duration: ['p(95)<1000'], // 95%的请求响应时间小于1秒
    http_req_failed: ['rate<0.01'],    // 错误率小于1%
    error_rate: ['rate<0.01'],
    response_time: ['p(95)<1000'],
  },
};

// 基础URL
const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';
const WS_URL = BASE_URL.replace('http', 'ws') + '/ws';

// 测试数据
const testUsers = [
  { username: 'test_user_1', password: 'test_password_1' },
  { username: 'test_user_2', password: 'test_password_2' },
  { username: 'test_user_3', password: 'test_password_3' },
];

// 获取随机用户
function getRandomUser() {
  return testUsers[Math.floor(Math.random() * testUsers.length)];
}

// 登录并获取token
function login() {
  const user = getRandomUser();
  const loginData = {
    username: user.username,
    password: user.password,
  };

  const response = http.post(`${BASE_URL}/api/v1/auth/login`, JSON.stringify(loginData), {
    headers: { 'Content-Type': 'application/json' },
  });

  const success = check(response, {
    'login status is 200': (r) => r.status === 200,
    'login response has token': (r) => r.json('access_token') !== undefined,
  });

  errorRate.add(!success);
  responseTime.add(response.timings.duration);

  if (success) {
    return response.json('access_token');
  }
  return null;
}

// API测试场景
export default function () {
  // 1. 健康检查
  const healthResponse = http.get(`${BASE_URL}/health`);
  check(healthResponse, {
    'health check status is 200': (r) => r.status === 200,
  });

  // 2. 用户登录
  const token = login();
  if (!token) {
    return;
  }

  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  // 3. 获取用户信息
  const userResponse = http.get(`${BASE_URL}/api/v1/users/me`, { headers });
  check(userResponse, {
    'get user info status is 200': (r) => r.status === 200,
  });

  // 4. 获取账户信息
  const accountResponse = http.get(`${BASE_URL}/api/v1/ctp/account`, { headers });
  check(accountResponse, {
    'get account info status is 200': (r) => r.status === 200,
  });

  // 5. 获取持仓信息
  const positionsResponse = http.get(`${BASE_URL}/api/v1/ctp/positions`, { headers });
  check(positionsResponse, {
    'get positions status is 200': (r) => r.status === 200,
  });

  // 6. 获取策略列表
  const strategiesResponse = http.get(`${BASE_URL}/api/v1/strategies`, { headers });
  check(strategiesResponse, {
    'get strategies status is 200': (r) => r.status === 200,
  });

  // 7. 获取行情数据
  const marketDataResponse = http.get(`${BASE_URL}/api/v1/market/instruments`, { headers });
  check(marketDataResponse, {
    'get market data status is 200': (r) => r.status === 200,
  });

  // 8. 创建测试订单
  const orderData = {
    instrument_id: 'rb2405',
    direction: 'buy',
    offset_flag: 'open',
    price: 3500.0,
    volume: 1,
    order_type: 'limit',
  };

  const orderResponse = http.post(`${BASE_URL}/api/v1/ctp/orders`, JSON.stringify(orderData), { headers });
  check(orderResponse, {
    'create order status is 200 or 201': (r) => r.status === 200 || r.status === 201,
  });

  // 9. 获取订单历史
  const ordersResponse = http.get(`${BASE_URL}/api/v1/ctp/orders`, { headers });
  check(ordersResponse, {
    'get orders status is 200': (r) => r.status === 200,
  });

  // 10. 获取交易历史
  const tradesResponse = http.get(`${BASE_URL}/api/v1/ctp/trades`, { headers });
  check(tradesResponse, {
    'get trades status is 200': (r) => r.status === 200,
  });

  sleep(1);
}

// WebSocket测试场景
export function wsTest() {
  const token = login();
  if (!token) {
    return;
  }

  const url = `${WS_URL}?token=${token}`;
  
  const response = ws.connect(url, {}, function (socket) {
    wsConnections.add(1);

    socket.on('open', function () {
      console.log('WebSocket连接已建立');
      
      // 订阅行情数据
      socket.send(JSON.stringify({
        type: 'subscribe',
        channel: 'market_data',
        instruments: ['rb2405', 'hc2405']
      }));
      wsMessages.add(1);
    });

    socket.on('message', function (message) {
      const data = JSON.parse(message);
      wsMessages.add(1);
      
      check(data, {
        'WebSocket message is valid': (d) => d.type !== undefined,
      });
    });

    socket.on('close', function () {
      console.log('WebSocket连接已关闭');
    });

    socket.on('error', function (e) {
      console.log('WebSocket错误:', e.error());
      errorRate.add(1);
    });

    // 保持连接30秒
    sleep(30);
  });

  check(response, {
    'WebSocket连接成功': (r) => r && r.status === 101,
  });
}

// 压力测试场景
export function stressTest() {
  const token = login();
  if (!token) {
    return;
  }

  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  // 并发创建多个订单
  const promises = [];
  for (let i = 0; i < 10; i++) {
    const orderData = {
      instrument_id: 'rb2405',
      direction: Math.random() > 0.5 ? 'buy' : 'sell',
      offset_flag: 'open',
      price: 3500 + Math.random() * 100,
      volume: Math.floor(Math.random() * 5) + 1,
      order_type: 'limit',
    };

    promises.push(
      http.asyncRequest('POST', `${BASE_URL}/api/v1/ctp/orders`, JSON.stringify(orderData), { headers })
    );
  }

  // 等待所有请求完成
  const responses = http.batch(promises);
  
  responses.forEach((response, index) => {
    check(response, {
      [`batch order ${index} status is 200 or 201`]: (r) => r.status === 200 || r.status === 201,
    });
    
    errorRate.add(response.status >= 400);
    responseTime.add(response.timings.duration);
  });
}

// 数据库压力测试
export function dbStressTest() {
  const token = login();
  if (!token) {
    return;
  }

  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  // 大量查询请求
  const endpoints = [
    '/api/v1/ctp/orders',
    '/api/v1/ctp/trades',
    '/api/v1/ctp/positions',
    '/api/v1/strategies',
    '/api/v1/market/instruments',
  ];

  endpoints.forEach(endpoint => {
    for (let i = 0; i < 5; i++) {
      const response = http.get(`${BASE_URL}${endpoint}?page=${i}&size=50`, { headers });
      
      check(response, {
        [`${endpoint} query ${i} status is 200`]: (r) => r.status === 200,
        [`${endpoint} query ${i} response time < 2s`]: (r) => r.timings.duration < 2000,
      });
      
      errorRate.add(response.status >= 400);
      responseTime.add(response.timings.duration);
    }
  });
}

// 导出不同的测试场景
export { wsTest, stressTest, dbStressTest };
