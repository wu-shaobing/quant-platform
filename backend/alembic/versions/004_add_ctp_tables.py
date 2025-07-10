"""Add CTP tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """Create CTP related tables"""
    
    # Create ctp_orders table
    op.create_table('ctp_orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('order_ref', sa.String(length=13), nullable=False, comment='报单引用'),
        sa.Column('order_sys_id', sa.String(length=21), nullable=True, comment='报单编号'),
        sa.Column('instrument_id', sa.String(length=31), nullable=False, comment='合约代码'),
        sa.Column('exchange_id', sa.String(length=9), nullable=False, comment='交易所代码'),
        sa.Column('direction', sa.String(length=1), nullable=False, comment='买卖方向'),
        sa.Column('offset_flag', sa.String(length=1), nullable=False, comment='开平标志'),
        sa.Column('order_price_type', sa.String(length=1), nullable=False, comment='报单价格条件'),
        sa.Column('limit_price', sa.Numeric(precision=15, scale=4), nullable=False, comment='价格'),
        sa.Column('volume_total_original', sa.Integer(), nullable=False, comment='数量'),
        sa.Column('time_condition', sa.String(length=1), nullable=False, comment='有效期类型'),
        sa.Column('volume_condition', sa.String(length=1), nullable=False, comment='成交量类型'),
        sa.Column('min_volume', sa.Integer(), nullable=False, comment='最小成交量'),
        sa.Column('contingent_condition', sa.String(length=1), nullable=False, comment='触发条件'),
        sa.Column('stop_price', sa.Numeric(precision=15, scale=4), nullable=False, comment='止损价'),
        sa.Column('force_close_reason', sa.String(length=1), nullable=False, comment='强平原因'),
        sa.Column('is_auto_suspend', sa.Boolean(), nullable=False, comment='自动挂起标志'),
        sa.Column('order_status', sa.String(length=1), nullable=False, comment='报单状态'),
        sa.Column('volume_traded', sa.Integer(), nullable=False, comment='今成交数量'),
        sa.Column('volume_total', sa.Integer(), nullable=False, comment='剩余数量'),
        sa.Column('insert_date', sa.String(length=9), nullable=True, comment='报单日期'),
        sa.Column('insert_time', sa.String(length=9), nullable=True, comment='委托时间'),
        sa.Column('active_time', sa.String(length=9), nullable=True, comment='激活时间'),
        sa.Column('suspend_time', sa.String(length=9), nullable=True, comment='挂起时间'),
        sa.Column('update_time', sa.String(length=9), nullable=True, comment='最后修改时间'),
        sa.Column('cancel_time', sa.String(length=9), nullable=True, comment='撤销时间'),
        sa.Column('front_id', sa.Integer(), nullable=True, comment='前置编号'),
        sa.Column('session_id', sa.Integer(), nullable=True, comment='会话编号'),
        sa.Column('user_product_info', sa.String(length=11), nullable=True, comment='用户端产品信息'),
        sa.Column('status_msg', sa.String(length=81), nullable=True, comment='状态信息'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for ctp_orders
    op.create_index('idx_ctp_orders_user_id', 'ctp_orders', ['user_id'])
    op.create_index('idx_ctp_orders_order_ref', 'ctp_orders', ['order_ref'])
    op.create_index('idx_ctp_orders_order_sys_id', 'ctp_orders', ['order_sys_id'])
    op.create_index('idx_ctp_orders_instrument_id', 'ctp_orders', ['instrument_id'])
    op.create_index('idx_ctp_orders_status', 'ctp_orders', ['order_status'])
    op.create_index('idx_ctp_orders_created_at', 'ctp_orders', ['created_at'])
    op.create_unique_constraint('uq_ctp_orders_order_ref', 'ctp_orders', ['order_ref'])
    
    # Create ctp_trades table
    op.create_table('ctp_trades',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('trade_id', sa.String(length=21), nullable=False, comment='成交编号'),
        sa.Column('order_ref', sa.String(length=13), nullable=False, comment='报单引用'),
        sa.Column('order_sys_id', sa.String(length=21), nullable=True, comment='报单编号'),
        sa.Column('instrument_id', sa.String(length=31), nullable=False, comment='合约代码'),
        sa.Column('exchange_id', sa.String(length=9), nullable=False, comment='交易所代码'),
        sa.Column('direction', sa.String(length=1), nullable=False, comment='买卖方向'),
        sa.Column('offset_flag', sa.String(length=1), nullable=False, comment='开平标志'),
        sa.Column('price', sa.Numeric(precision=15, scale=4), nullable=False, comment='价格'),
        sa.Column('volume', sa.Integer(), nullable=False, comment='数量'),
        sa.Column('trade_date', sa.String(length=9), nullable=True, comment='成交时期'),
        sa.Column('trade_time', sa.String(length=9), nullable=True, comment='成交时间'),
        sa.Column('trade_type', sa.String(length=1), nullable=True, comment='成交类型'),
        sa.Column('price_source', sa.String(length=1), nullable=True, comment='成交价来源'),
        sa.Column('trader_id', sa.String(length=21), nullable=True, comment='交易员代码'),
        sa.Column('order_local_id', sa.String(length=13), nullable=True, comment='本地报单编号'),
        sa.Column('clearing_part_id', sa.String(length=11), nullable=True, comment='结算会员编号'),
        sa.Column('business_unit', sa.String(length=21), nullable=True, comment='业务单元'),
        sa.Column('sequence_no', sa.Integer(), nullable=True, comment='序号'),
        sa.Column('trading_day', sa.String(length=9), nullable=True, comment='交易日'),
        sa.Column('settlement_id', sa.Integer(), nullable=True, comment='结算编号'),
        sa.Column('broker_order_seq', sa.Integer(), nullable=True, comment='经纪公司报单编号'),
        sa.Column('trade_source', sa.String(length=1), nullable=True, comment='成交来源'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for ctp_trades
    op.create_index('idx_ctp_trades_user_id', 'ctp_trades', ['user_id'])
    op.create_index('idx_ctp_trades_trade_id', 'ctp_trades', ['trade_id'])
    op.create_index('idx_ctp_trades_order_ref', 'ctp_trades', ['order_ref'])
    op.create_index('idx_ctp_trades_instrument_id', 'ctp_trades', ['instrument_id'])
    op.create_index('idx_ctp_trades_created_at', 'ctp_trades', ['created_at'])
    op.create_unique_constraint('uq_ctp_trades_trade_id', 'ctp_trades', ['trade_id'])
    
    # Create ctp_positions table
    op.create_table('ctp_positions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('instrument_id', sa.String(length=31), nullable=False, comment='合约代码'),
        sa.Column('broker_id', sa.String(length=11), nullable=False, comment='经纪公司代码'),
        sa.Column('investor_id', sa.String(length=13), nullable=False, comment='投资者代码'),
        sa.Column('position_direction', sa.String(length=1), nullable=False, comment='持仓多空方向'),
        sa.Column('hedge_flag', sa.String(length=1), nullable=False, comment='投机套保标志'),
        sa.Column('position_date', sa.String(length=1), nullable=False, comment='持仓日期'),
        sa.Column('yd_position', sa.Integer(), nullable=False, comment='上日持仓'),
        sa.Column('position', sa.Integer(), nullable=False, comment='今日持仓'),
        sa.Column('long_frozen', sa.Integer(), nullable=False, comment='多头冻结'),
        sa.Column('short_frozen', sa.Integer(), nullable=False, comment='空头冻结'),
        sa.Column('long_frozen_amount', sa.Numeric(precision=15, scale=4), nullable=False, comment='开仓冻结金额'),
        sa.Column('short_frozen_amount', sa.Numeric(precision=15, scale=4), nullable=False, comment='开仓冻结金额'),
        sa.Column('yd_long_frozen', sa.Integer(), nullable=False, comment='昨日多头冻结'),
        sa.Column('yd_short_frozen', sa.Integer(), nullable=False, comment='昨日空头冻结'),
        sa.Column('position_cost', sa.Numeric(precision=15, scale=4), nullable=False, comment='持仓成本'),
        sa.Column('pre_margin', sa.Numeric(precision=15, scale=4), nullable=False, comment='上次占用的保证金'),
        sa.Column('use_margin', sa.Numeric(precision=15, scale=4), nullable=False, comment='占用的保证金'),
        sa.Column('frozen_margin', sa.Numeric(precision=15, scale=4), nullable=False, comment='冻结的保证金'),
        sa.Column('frozen_cash', sa.Numeric(precision=15, scale=4), nullable=False, comment='冻结的资金'),
        sa.Column('frozen_commission', sa.Numeric(precision=15, scale=4), nullable=False, comment='冻结的手续费'),
        sa.Column('cash_in', sa.Numeric(precision=15, scale=4), nullable=False, comment='资金差额'),
        sa.Column('commission', sa.Numeric(precision=15, scale=4), nullable=False, comment='手续费'),
        sa.Column('close_profit', sa.Numeric(precision=15, scale=4), nullable=False, comment='平仓盈亏'),
        sa.Column('position_profit', sa.Numeric(precision=15, scale=4), nullable=False, comment='持仓盈亏'),
        sa.Column('pre_settlement_price', sa.Numeric(precision=15, scale=4), nullable=False, comment='上次结算价'),
        sa.Column('settlement_price', sa.Numeric(precision=15, scale=4), nullable=False, comment='本次结算价'),
        sa.Column('trading_day', sa.String(length=9), nullable=True, comment='交易日'),
        sa.Column('settlement_id', sa.Integer(), nullable=True, comment='结算编号'),
        sa.Column('open_cost', sa.Numeric(precision=15, scale=4), nullable=False, comment='开仓成本'),
        sa.Column('exchange_margin', sa.Numeric(precision=15, scale=4), nullable=False, comment='交易所保证金'),
        sa.Column('combine_position', sa.Integer(), nullable=False, comment='组合成交形成的持仓'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for ctp_positions
    op.create_index('idx_ctp_positions_user_id', 'ctp_positions', ['user_id'])
    op.create_index('idx_ctp_positions_instrument_id', 'ctp_positions', ['instrument_id'])
    op.create_index('idx_ctp_positions_direction', 'ctp_positions', ['position_direction'])
    op.create_unique_constraint('idx_ctp_positions_unique', 'ctp_positions', ['user_id', 'instrument_id', 'position_direction'])
    
    # Create ctp_accounts table
    op.create_table('ctp_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, comment='用户ID'),
        sa.Column('broker_id', sa.String(length=11), nullable=False, comment='经纪公司代码'),
        sa.Column('account_id', sa.String(length=13), nullable=False, comment='投资者帐号'),
        sa.Column('pre_mortgage', sa.Numeric(precision=15, scale=4), nullable=False, comment='上次质押金额'),
        sa.Column('pre_credit', sa.Numeric(precision=15, scale=4), nullable=False, comment='上次信用额度'),
        sa.Column('pre_deposit', sa.Numeric(precision=15, scale=4), nullable=False, comment='上次存款额'),
        sa.Column('pre_balance', sa.Numeric(precision=15, scale=4), nullable=False, comment='上次结算准备金'),
        sa.Column('pre_margin', sa.Numeric(precision=15, scale=4), nullable=False, comment='上次占用的保证金'),
        sa.Column('interest_base', sa.Numeric(precision=15, scale=4), nullable=False, comment='利息基数'),
        sa.Column('interest', sa.Numeric(precision=15, scale=4), nullable=False, comment='利息收入'),
        sa.Column('deposit', sa.Numeric(precision=15, scale=4), nullable=False, comment='入金金额'),
        sa.Column('withdraw', sa.Numeric(precision=15, scale=4), nullable=False, comment='出金金额'),
        sa.Column('frozen_margin', sa.Numeric(precision=15, scale=4), nullable=False, comment='冻结的保证金'),
        sa.Column('frozen_cash', sa.Numeric(precision=15, scale=4), nullable=False, comment='冻结的资金'),
        sa.Column('frozen_commission', sa.Numeric(precision=15, scale=4), nullable=False, comment='冻结的手续费'),
        sa.Column('curr_margin', sa.Numeric(precision=15, scale=4), nullable=False, comment='当前保证金总额'),
        sa.Column('cash_in', sa.Numeric(precision=15, scale=4), nullable=False, comment='资金差额'),
        sa.Column('commission', sa.Numeric(precision=15, scale=4), nullable=False, comment='手续费'),
        sa.Column('close_profit', sa.Numeric(precision=15, scale=4), nullable=False, comment='平仓盈亏'),
        sa.Column('position_profit', sa.Numeric(precision=15, scale=4), nullable=False, comment='持仓盈亏'),
        sa.Column('balance', sa.Numeric(precision=15, scale=4), nullable=False, comment='期货结算准备金'),
        sa.Column('available', sa.Numeric(precision=15, scale=4), nullable=False, comment='可用资金'),
        sa.Column('withdraw_quota', sa.Numeric(precision=15, scale=4), nullable=False, comment='可取资金'),
        sa.Column('reserve', sa.Numeric(precision=15, scale=4), nullable=False, comment='基本准备金'),
        sa.Column('trading_day', sa.String(length=9), nullable=True, comment='交易日'),
        sa.Column('settlement_id', sa.Integer(), nullable=True, comment='结算编号'),
        sa.Column('credit', sa.Numeric(precision=15, scale=4), nullable=False, comment='信用额度'),
        sa.Column('mortgage', sa.Numeric(precision=15, scale=4), nullable=False, comment='质押金额'),
        sa.Column('exchange_margin', sa.Numeric(precision=15, scale=4), nullable=False, comment='交易所保证金'),
        sa.Column('delivery_margin', sa.Numeric(precision=15, scale=4), nullable=False, comment='投资者交割保证金'),
        sa.Column('exchange_delivery_margin', sa.Numeric(precision=15, scale=4), nullable=False, comment='交易所交割保证金'),
        sa.Column('reserve_balance', sa.Numeric(precision=15, scale=4), nullable=False, comment='保底期货结算准备金'),
        sa.Column('created_at', sa.DateTime(), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(), nullable=False, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for ctp_accounts
    op.create_index('idx_ctp_accounts_user_id', 'ctp_accounts', ['user_id'])
    op.create_index('idx_ctp_accounts_account_id', 'ctp_accounts', ['account_id'])
    op.create_index('idx_ctp_accounts_trading_day', 'ctp_accounts', ['trading_day'])
    op.create_unique_constraint('idx_ctp_accounts_unique', 'ctp_accounts', ['user_id', 'account_id', 'trading_day'])


def downgrade():
    """Drop CTP related tables"""
    op.drop_table('ctp_accounts')
    op.drop_table('ctp_positions')
    op.drop_table('ctp_trades')
    op.drop_table('ctp_orders')
