export default {
  // 通用
  common: {
    confirm: '确认',
    cancel: '取消',
    save: '保存',
    delete: '删除',
    edit: '编辑',
    add: '添加',
    search: '搜索',
    reset: '重置',
    submit: '提交',
    back: '返回',
    next: '下一步',
    previous: '上一步',
    loading: '加载中...',
    noData: '暂无数据',
    success: '操作成功',
    error: '操作失败',
    warning: '警告',
    info: '提示',
    total: '共',
    items: '条',
    page: '页',
    refresh: '刷新',
    export: '导出',
    import: '导入',
    download: '下载',
    upload: '上传',
    copy: '复制',
    copySuccess: '复制成功',
    copyFailed: '复制失败'
  },

  // 导航
  nav: {
    dashboard: '仪表盘',
    market: '行情中心',
    trading: '交易中心',
    strategy: '策略中心',
    backtest: '回测分析',
    portfolio: '投资组合',
    risk: '风险管理',
    settings: '设置中心',
    help: '帮助中心',
    logout: '退出登录'
  },

  // 认证
  auth: {
    login: '登录',
    register: '注册',
    logout: '退出',
    username: '用户名',
    password: '密码',
    confirmPassword: '确认密码',
    email: '邮箱',
    phone: '手机号',
    captcha: '验证码',
    rememberMe: '记住我',
    forgotPassword: '忘记密码？',
    noAccount: '还没有账号？',
    hasAccount: '已有账号？',
    loginSuccess: '登录成功',
    loginFailed: '登录失败',
    logoutSuccess: '退出成功'
  },

  // 仪表盘
  dashboard: {
    title: '仪表盘',
    overview: '概览',
    todayPnl: '今日盈亏',
    totalPnl: '总盈亏',
    totalAssets: '总资产',
    availableCash: '可用资金',
    marketValue: '市值',
    positionCount: '持仓数量',
    todayTrades: '今日交易',
    winRate: '胜率',
    quickActions: '快速操作',
    recentTrades: '最近交易',
    topPositions: '主要持仓',
    marketNews: '市场资讯'
  },

  // 行情
  market: {
    title: '行情中心',
    search: '搜索股票',
    watchlist: '自选股',
    ranking: '排行榜',
    sector: '板块',
    index: '指数',
    news: '资讯',
    symbol: '代码',
    name: '名称',
    price: '价格',
    change: '涨跌',
    changePercent: '涨跌幅',
    volume: '成交量',
    turnover: '成交额',
    high: '最高',
    low: '最低',
    open: '开盘',
    close: '收盘',
    prevClose: '昨收',
    amplitude: '振幅',
    pe: '市盈率',
    pb: '市净率',
    marketCap: '市值',
    addToWatchlist: '加入自选',
    removeFromWatchlist: '移出自选'
  },

  // 交易
  trading: {
    title: '交易中心',
    buy: '买入',
    sell: '卖出',
    orderType: '订单类型',
    limitOrder: '限价单',
    marketOrder: '市价单',
    stopOrder: '止损单',
    stopProfitOrder: '止盈单',
    price: '价格',
    quantity: '数量',
    amount: '金额',
    commission: '手续费',
    positions: '持仓',
    orders: '订单',
    trades: '成交',
    account: '账户',
    orderStatus: {
      pending: '待成交',
      partiallyFilled: '部分成交',
      filled: '已成交',
      cancelled: '已撤单',
      rejected: '已拒绝'
    },
    positionSide: {
      long: '多头',
      short: '空头'
    }
  },

  // 策略
  strategy: {
    title: '策略中心',
    create: '创建策略',
    edit: '编辑策略',
    delete: '删除策略',
    start: '启动策略',
    stop: '停止策略',
    monitor: '监控',
    performance: '绩效',
    parameters: '参数',
    signals: '信号',
    status: {
      running: '运行中',
      stopped: '已停止',
      error: '错误'
    }
  },

  // 回测
  backtest: {
    title: '回测分析',
    create: '创建回测',
    run: '运行回测',
    results: '回测结果',
    history: '回测历史',
    compare: '对比分析',
    optimize: '参数优化',
    startDate: '开始日期',
    endDate: '结束日期',
    initialCapital: '初始资金',
    totalReturn: '总收益',
    annualizedReturn: '年化收益',
    maxDrawdown: '最大回撤',
    sharpeRatio: '夏普比率',
    winRate: '胜率',
    profitFactor: '盈利因子'
  },

  // 投资组合
  portfolio: {
    title: '投资组合',
    analysis: '组合分析',
    allocation: '资产配置',
    performance: '绩效分析',
    risk: '风险分析',
    rebalance: '再平衡',
    benchmark: '基准',
    correlation: '相关性',
    diversification: '分散度'
  },

  // 风险管理
  risk: {
    title: '风险管理',
    monitor: '风险监控',
    limits: '风险限额',
    alerts: '风险警报',
    reports: '风险报告',
    var: 'VaR',
    stress: '压力测试',
    scenario: '情景分析'
  },

  // 设置
  settings: {
    title: '设置中心',
    profile: '个人资料',
    account: '账户设置',
    security: '安全设置',
    notifications: '通知设置',
    trading: '交易设置',
    appearance: '外观设置',
    language: '语言',
    theme: '主题',
    timezone: '时区'
  },

  // 错误页面
  error: {
    404: {
      title: '页面不存在',
      description: '抱歉，您访问的页面不存在',
      backHome: '返回首页'
    },
    403: {
      title: '访问被拒绝',
      description: '抱歉，您没有权限访问此页面',
      backHome: '返回首页'
    },
    500: {
      title: '服务器错误',
      description: '抱歉，服务器出现错误',
      retry: '重试'
    },
    network: {
      title: '网络连接失败',
      description: '请检查您的网络连接',
      retry: '重试'
    }
  }
} 