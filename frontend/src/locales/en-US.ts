export default {
  // Common
  common: {
    confirm: 'Confirm',
    cancel: 'Cancel',
    save: 'Save',
    delete: 'Delete',
    edit: 'Edit',
    add: 'Add',
    search: 'Search',
    reset: 'Reset',
    submit: 'Submit',
    back: 'Back',
    next: 'Next',
    previous: 'Previous',
    loading: 'Loading...',
    noData: 'No Data',
    success: 'Success',
    error: 'Error',
    warning: 'Warning',
    info: 'Info',
    total: 'Total',
    items: 'items',
    page: 'Page',
    refresh: 'Refresh',
    export: 'Export',
    import: 'Import',
    download: 'Download',
    upload: 'Upload',
    copy: 'Copy',
    copySuccess: 'Copied successfully',
    copyFailed: 'Copy failed'
  },

  // Navigation
  nav: {
    dashboard: 'Dashboard',
    market: 'Market',
    trading: 'Trading',
    strategy: 'Strategy',
    backtest: 'Backtest',
    portfolio: 'Portfolio',
    risk: 'Risk',
    settings: 'Settings',
    help: 'Help',
    logout: 'Logout'
  },

  // Authentication
  auth: {
    login: 'Login',
    register: 'Register',
    logout: 'Logout',
    username: 'Username',
    password: 'Password',
    confirmPassword: 'Confirm Password',
    email: 'Email',
    phone: 'Phone',
    captcha: 'Captcha',
    rememberMe: 'Remember Me',
    forgotPassword: 'Forgot Password?',
    noAccount: 'No account yet?',
    hasAccount: 'Already have an account?',
    loginSuccess: 'Login successful',
    loginFailed: 'Login failed',
    logoutSuccess: 'Logout successful'
  },

  // Dashboard
  dashboard: {
    title: 'Dashboard',
    overview: 'Overview',
    todayPnl: 'Today P&L',
    totalPnl: 'Total P&L',
    totalAssets: 'Total Assets',
    availableCash: 'Available Cash',
    marketValue: 'Market Value',
    positionCount: 'Positions',
    todayTrades: 'Today Trades',
    winRate: 'Win Rate',
    quickActions: 'Quick Actions',
    recentTrades: 'Recent Trades',
    topPositions: 'Top Positions',
    marketNews: 'Market News'
  },

  // Market
  market: {
    title: 'Market Center',
    search: 'Search Stocks',
    watchlist: 'Watchlist',
    ranking: 'Rankings',
    sector: 'Sectors',
    index: 'Indices',
    news: 'News',
    symbol: 'Symbol',
    name: 'Name',
    price: 'Price',
    change: 'Change',
    changePercent: 'Change %',
    volume: 'Volume',
    turnover: 'Turnover',
    high: 'High',
    low: 'Low',
    open: 'Open',
    close: 'Close',
    prevClose: 'Prev Close',
    amplitude: 'Amplitude',
    pe: 'P/E',
    pb: 'P/B',
    marketCap: 'Market Cap',
    addToWatchlist: 'Add to Watchlist',
    removeFromWatchlist: 'Remove from Watchlist'
  },

  // Trading
  trading: {
    title: 'Trading Center',
    buy: 'Buy',
    sell: 'Sell',
    orderType: 'Order Type',
    limitOrder: 'Limit Order',
    marketOrder: 'Market Order',
    stopOrder: 'Stop Order',
    stopProfitOrder: 'Take Profit Order',
    price: 'Price',
    quantity: 'Quantity',
    amount: 'Amount',
    commission: 'Commission',
    positions: 'Positions',
    orders: 'Orders',
    trades: 'Trades',
    account: 'Account',
    orderStatus: {
      pending: 'Pending',
      partiallyFilled: 'Partially Filled',
      filled: 'Filled',
      cancelled: 'Cancelled',
      rejected: 'Rejected'
    },
    positionSide: {
      long: 'Long',
      short: 'Short'
    }
  },

  // Strategy
  strategy: {
    title: 'Strategy Center',
    create: 'Create Strategy',
    edit: 'Edit Strategy',
    delete: 'Delete Strategy',
    start: 'Start Strategy',
    stop: 'Stop Strategy',
    monitor: 'Monitor',
    performance: 'Performance',
    parameters: 'Parameters',
    signals: 'Signals',
    status: {
      running: 'Running',
      stopped: 'Stopped',
      error: 'Error'
    }
  },

  // Backtest
  backtest: {
    title: 'Backtest Analysis',
    create: 'Create Backtest',
    run: 'Run Backtest',
    results: 'Backtest Results',
    history: 'Backtest History',
    compare: 'Compare Analysis',
    optimize: 'Parameter Optimization',
    startDate: 'Start Date',
    endDate: 'End Date',
    initialCapital: 'Initial Capital',
    totalReturn: 'Total Return',
    annualizedReturn: 'Annualized Return',
    maxDrawdown: 'Max Drawdown',
    sharpeRatio: 'Sharpe Ratio',
    winRate: 'Win Rate',
    profitFactor: 'Profit Factor'
  },

  // Portfolio
  portfolio: {
    title: 'Portfolio',
    analysis: 'Portfolio Analysis',
    allocation: 'Asset Allocation',
    performance: 'Performance Analysis',
    risk: 'Risk Analysis',
    rebalance: 'Rebalance',
    benchmark: 'Benchmark',
    correlation: 'Correlation',
    diversification: 'Diversification'
  },

  // Risk Management
  risk: {
    title: 'Risk Management',
    monitor: 'Risk Monitor',
    limits: 'Risk Limits',
    alerts: 'Risk Alerts',
    reports: 'Risk Reports',
    var: 'VaR',
    stress: 'Stress Test',
    scenario: 'Scenario Analysis'
  },

  // Settings
  settings: {
    title: 'Settings',
    profile: 'Profile',
    account: 'Account Settings',
    security: 'Security Settings',
    notifications: 'Notification Settings',
    trading: 'Trading Settings',
    appearance: 'Appearance Settings',
    language: 'Language',
    theme: 'Theme',
    timezone: 'Timezone'
  },

  // Error Pages
  error: {
    404: {
      title: 'Page Not Found',
      description: 'Sorry, the page you are looking for does not exist',
      backHome: 'Back to Home'
    },
    403: {
      title: 'Access Denied',
      description: 'Sorry, you do not have permission to access this page',
      backHome: 'Back to Home'
    },
    500: {
      title: 'Server Error',
      description: 'Sorry, there was a server error',
      retry: 'Retry'
    },
    network: {
      title: 'Network Connection Failed',
      description: 'Please check your network connection',
      retry: 'Retry'
    }
  }
} 