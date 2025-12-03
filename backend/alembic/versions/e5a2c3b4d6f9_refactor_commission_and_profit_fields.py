"""Refactor commission and profit fields for clarity

- Rename Order.profit to Order.total_profit
- Rename Order.affiliate_id to Order.marketing_affiliate_id
- Rename Order.affiliate_commission to Order.marketing_commission
- Add Order.shipping_commission, cancellation_approved_at, refund_approved_at
- Add OrderItem profit and commission fields
- Add ShipmentAllocation.shipping_commission
- Rename AffiliateSale.commission_amount to AffiliateSale.marketing_commission
- Update Settings fields (profit_per_order→profit_per_unit, add commission rates)
- Add Product.profit_per_unit
- Create ShippingCommissionPayment table

Revision ID: e5a2c3b4d6f9
Revises: d8e5d38e78c4
Create Date: 2025-12-03 10:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5a2c3b4d6f9'
down_revision: Union[str, None] = '3791e7e3ee49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================
    # 1. Settings 테이블: profit_per_order → profit_per_unit
    # ============================================
    op.add_column('settings', sa.Column('profit_per_unit', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('settings', sa.Column('marketing_commission_rate', sa.Numeric(precision=5, scale=4), nullable=True))
    op.add_column('settings', sa.Column('shipping_commission_rate', sa.Numeric(precision=5, scale=4), nullable=True))
    op.add_column('settings', sa.Column('paypal_transaction_fee_rate', sa.Numeric(precision=5, scale=4), nullable=True))

    # profit_per_order 데이터를 profit_per_unit으로 마이그레이션
    op.execute('UPDATE settings SET profit_per_unit = profit_per_order WHERE profit_per_unit IS NULL')

    # 기본값 설정
    op.execute("UPDATE settings SET marketing_commission_rate = 0.2 WHERE marketing_commission_rate IS NULL")
    op.execute("UPDATE settings SET shipping_commission_rate = 0.2 WHERE shipping_commission_rate IS NULL")

    # 기존 필드 삭제
    op.drop_column('settings', 'profit_per_order')

    # profit_per_unit은 NOT NULL로 설정
    op.alter_column('settings', 'profit_per_unit', nullable=False)
    op.alter_column('settings', 'marketing_commission_rate', nullable=False)
    op.alter_column('settings', 'shipping_commission_rate', nullable=False)

    # ============================================
    # 2. Product 테이블: profit_per_unit 추가
    # ============================================
    op.add_column('products', sa.Column('profit_per_unit', sa.Numeric(precision=10, scale=2), server_default='80.0'))

    # ============================================
    # 3. Order 테이블: 필드 재구성
    # ============================================
    # 새로운 필드 추가
    op.add_column('orders', sa.Column('total_profit', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('orders', sa.Column('marketing_commission', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('orders', sa.Column('shipping_commission', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('orders', sa.Column('paypal_transaction_fee', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('orders', sa.Column('marketing_affiliate_id', sa.UUID(), nullable=True))
    op.add_column('orders', sa.Column('cancellation_approved_at', sa.DateTime(), nullable=True))
    op.add_column('orders', sa.Column('refund_approved_at', sa.DateTime(), nullable=True))

    # 기존 데이터 마이그레이션
    op.execute('UPDATE orders SET total_profit = profit WHERE total_profit IS NULL')
    op.execute('UPDATE orders SET marketing_commission = affiliate_commission WHERE marketing_commission IS NULL')
    op.execute('UPDATE orders SET paypal_transaction_fee = paypal_fee WHERE paypal_transaction_fee IS NULL')
    op.execute('UPDATE orders SET marketing_affiliate_id = affiliate_id WHERE marketing_affiliate_id IS NULL')

    # 기존 필드 삭제
    op.drop_constraint('orders_affiliate_id_fkey', 'orders', type_='foreignkey')
    op.drop_column('orders', 'profit')
    op.drop_column('orders', 'affiliate_commission')
    op.drop_column('orders', 'affiliate_id')
    op.drop_column('orders', 'paypal_fee')

    # 새로운 외래키 추가
    op.create_foreign_key(
        'orders_marketing_affiliate_id_fkey',
        'orders',
        'affiliates',
        ['marketing_affiliate_id'],
        ['id']
    )
    op.create_index(op.f('ix_orders_marketing_affiliate_id'), 'orders', ['marketing_affiliate_id'])

    # ============================================
    # 4. OrderItem 테이블: profit 및 commission 필드 추가
    # ============================================
    op.add_column('order_items', sa.Column('profit_per_item', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('order_items', sa.Column('marketing_commission_unit', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('order_items', sa.Column('shipping_commission_unit', sa.Numeric(precision=10, scale=2), nullable=True))

    # ============================================
    # 5. ShipmentAllocation 테이블: shipping_commission 추가
    # ============================================
    op.add_column('shipment_allocations', sa.Column('shipping_commission', sa.Numeric(precision=10, scale=2), nullable=True))

    # ============================================
    # 6. AffiliateSale 테이블: commission_amount → marketing_commission
    # ============================================
    op.add_column('affiliate_sales', sa.Column('marketing_commission', sa.Numeric(precision=10, scale=2), nullable=True))

    # 기존 데이터 마이그레이션
    op.execute('UPDATE affiliate_sales SET marketing_commission = commission_amount WHERE marketing_commission IS NULL')

    # 기존 필드 삭제
    op.drop_column('affiliate_sales', 'commission_amount')

    # ============================================
    # 7. ShippingCommissionPayment 테이블 생성 (신규)
    # ============================================
    op.create_table(
        'shipping_commission_payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('fulfillment_partner_id', sa.UUID(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='pending'),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('payment_method', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['fulfillment_partner_id'], ['fulfillment_partners.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_shipping_commission_payments_fulfillment_partner_id'),
                   'shipping_commission_payments', ['fulfillment_partner_id'], unique=False)


def downgrade() -> None:
    # ============================================
    # 1. ShippingCommissionPayment 테이블 삭제
    # ============================================
    op.drop_index(op.f('ix_shipping_commission_payments_fulfillment_partner_id'),
                  table_name='shipping_commission_payments')
    op.drop_table('shipping_commission_payments')

    # ============================================
    # 2. AffiliateSale 테이블: commission_amount 복구
    # ============================================
    op.add_column('affiliate_sales', sa.Column('commission_amount', sa.Numeric(precision=10, scale=2), nullable=True))

    # 데이터 복구
    op.execute('UPDATE affiliate_sales SET commission_amount = marketing_commission WHERE commission_amount IS NULL')

    # 새 필드 삭제
    op.drop_column('affiliate_sales', 'marketing_commission')

    # ============================================
    # 3. ShipmentAllocation 테이블: shipping_commission 삭제
    # ============================================
    op.drop_column('shipment_allocations', 'shipping_commission')

    # ============================================
    # 4. OrderItem 테이블: profit 및 commission 필드 삭제
    # ============================================
    op.drop_column('order_items', 'shipping_commission_unit')
    op.drop_column('order_items', 'marketing_commission_unit')
    op.drop_column('order_items', 'profit_per_item')

    # ============================================
    # 5. Order 테이블: 필드 복구
    # ============================================
    # 외래키 삭제
    op.drop_index(op.f('ix_orders_marketing_affiliate_id'), table_name='orders')
    op.drop_constraint('orders_marketing_affiliate_id_fkey', 'orders', type_='foreignkey')

    # 기존 필드 재추가
    op.add_column('orders', sa.Column('profit', sa.Numeric(precision=10, scale=2), nullable=True, server_default='80.0'))
    op.add_column('orders', sa.Column('affiliate_commission', sa.Numeric(precision=10, scale=2), nullable=True))
    op.add_column('orders', sa.Column('affiliate_id', sa.UUID(), nullable=True))
    op.add_column('orders', sa.Column('paypal_fee', sa.Numeric(precision=10, scale=2), nullable=True))

    # 데이터 복구
    op.execute('UPDATE orders SET profit = total_profit WHERE profit IS NULL')
    op.execute('UPDATE orders SET affiliate_commission = marketing_commission WHERE affiliate_commission IS NULL')
    op.execute('UPDATE orders SET affiliate_id = marketing_affiliate_id WHERE affiliate_id IS NULL')
    op.execute('UPDATE orders SET paypal_fee = paypal_transaction_fee WHERE paypal_fee IS NULL')

    # 외래키 복구
    op.create_foreign_key('orders_affiliate_id_fkey', 'orders', 'affiliates', ['affiliate_id'], ['id'])
    op.create_index(op.f('ix_orders_affiliate_id'), 'orders', ['affiliate_id'])

    # 새 필드 삭제
    op.drop_column('orders', 'cancellation_approved_at')
    op.drop_column('orders', 'refund_approved_at')
    op.drop_column('orders', 'marketing_affiliate_id')
    op.drop_column('orders', 'paypal_transaction_fee')
    op.drop_column('orders', 'shipping_commission')
    op.drop_column('orders', 'marketing_commission')
    op.drop_column('orders', 'total_profit')

    # ============================================
    # 6. Product 테이블: profit_per_unit 삭제
    # ============================================
    op.drop_column('products', 'profit_per_unit')

    # ============================================
    # 7. Settings 테이블: 필드 복구
    # ============================================
    # 기존 필드 재추가
    op.add_column('settings', sa.Column('profit_per_order', sa.Numeric(precision=10, scale=2), nullable=True, server_default='80.0'))

    # 데이터 복구
    op.execute('UPDATE settings SET profit_per_order = profit_per_unit WHERE profit_per_order IS NULL')

    # 새 필드 삭제
    op.drop_column('settings', 'paypal_transaction_fee_rate')
    op.drop_column('settings', 'shipping_commission_rate')
    op.drop_column('settings', 'marketing_commission_rate')
    op.drop_column('settings', 'profit_per_unit')
