-- ============================================
-- K-Beauty Landing Page - Database Schema
-- PostgreSQL
-- ============================================

-- ============================================
-- 1. customers (고객)
-- ============================================
CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  phone VARCHAR(20),
  address TEXT,
  region VARCHAR(50),  -- NCR, Luzon, Visayas, Mindanao
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_customers_email ON customers(email);

-- ============================================
-- 2. fulfillment_partners (배송담당자)
-- ============================================
CREATE TABLE fulfillment_partners (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE,
  phone VARCHAR(20),
  address TEXT,
  region VARCHAR(50),  -- 배송담당자가 담당하는 지역
  is_active BOOLEAN DEFAULT TRUE,
  last_allocated_at TIMESTAMP,  -- 라운드 로빈 용도
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fulfillment_partners_is_active ON fulfillment_partners(is_active);
CREATE INDEX idx_fulfillment_partners_last_allocated_at ON fulfillment_partners(last_allocated_at);

-- ============================================
-- 3. products (상품)
-- ============================================
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  description TEXT,
  price DECIMAL(10, 2) NOT NULL,
  sku VARCHAR(100) UNIQUE,
  image_url VARCHAR(500),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_is_active ON products(is_active);

-- ============================================
-- 4. partner_allocated_inventory (배송담당자별 할당 재고)
-- ============================================
CREATE TABLE partner_allocated_inventory (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  partner_id UUID NOT NULL,
  product_id UUID NOT NULL,
  allocated_quantity INT NOT NULL,  -- 분배받은 총 수량
  remaining_quantity INT NOT NULL,  -- 아직 미배송 수량
  stock_version INT DEFAULT 0,  -- 낙관적 락용
  allocated_date DATE,  -- 분배 날짜
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (partner_id) REFERENCES fulfillment_partners(id),
  FOREIGN KEY (product_id) REFERENCES products(id),
  UNIQUE(partner_id, product_id)
);

CREATE INDEX idx_partner_allocated_inventory_partner_id ON partner_allocated_inventory(partner_id);
CREATE INDEX idx_partner_allocated_inventory_remaining_quantity ON partner_allocated_inventory(remaining_quantity);

-- ============================================
-- 5. orders (주문)
-- ============================================
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_number VARCHAR(50) UNIQUE NOT NULL,
  customer_id UUID NOT NULL,
  fulfillment_partner_id UUID,
  
  -- 가격 정보
  subtotal DECIMAL(10, 2) NOT NULL,  -- 상품 총액
  shipping_fee DECIMAL(10, 2) DEFAULT 0,  -- 배송료
  total_price DECIMAL(10, 2) NOT NULL,  -- 최종 결제액 (subtotal + shipping_fee)
  
  -- 결제 정보
  status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending, paid, payment_failed, cancelled
  paypal_order_id VARCHAR(255),
  paypal_capture_id VARCHAR(255),
  paypal_fee DECIMAL(10, 2),
  profit DECIMAL(10, 2) DEFAULT 80.00,  -- 이윤
  paid_at TIMESTAMP,
  
  -- 배송 정보
  shipping_status VARCHAR(50) DEFAULT 'pending',  -- pending, preparing, shipped, delivered
  shipped_at TIMESTAMP,
  
  -- 어필리에이트
  affiliate_code VARCHAR(100),
  affiliate_commission DECIMAL(10, 2),
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (customer_id) REFERENCES customers(id),
  FOREIGN KEY (fulfillment_partner_id) REFERENCES fulfillment_partners(id)
);

CREATE INDEX idx_orders_order_number ON orders(order_number);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_shipping_status ON orders(shipping_status);
CREATE INDEX idx_orders_fulfillment_partner_id ON orders(fulfillment_partner_id);

-- ============================================
-- 6. order_items (주문 상품)
-- ============================================
CREATE TABLE order_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL,
  product_id UUID NOT NULL,
  quantity INT NOT NULL,
  unit_price DECIMAL(10, 2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(id),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE INDEX idx_order_items_order_id ON order_items(order_id);

-- ============================================
-- 7. shipment_allocations (배송 할당 기록)
-- ============================================
CREATE TABLE shipment_allocations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL,
  order_item_id UUID NOT NULL,
  partner_id UUID NOT NULL,
  quantity INT NOT NULL,  -- 이 배송담당자가 배송한 수량
  allocated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(id),
  FOREIGN KEY (order_item_id) REFERENCES order_items(id),
  FOREIGN KEY (partner_id) REFERENCES fulfillment_partners(id)
);

CREATE INDEX idx_shipment_allocations_order_id ON shipment_allocations(order_id);

-- ============================================
-- 8. shipments (배송 기록)
-- ============================================
CREATE TABLE shipments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL,
  partner_id UUID NOT NULL,
  tracking_number VARCHAR(255),
  status VARCHAR(50) DEFAULT 'preparing',  -- preparing, shipped, in_transit, delivered
  shipped_at TIMESTAMP,  -- 배송 발송 시간
  delivered_at TIMESTAMP,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(id),
  FOREIGN KEY (partner_id) REFERENCES fulfillment_partners(id)
);

CREATE INDEX idx_shipments_order_id ON shipments(order_id);
CREATE INDEX idx_shipments_status ON shipments(status);

-- ============================================
-- 9. email_logs (이메일 발송 로그)
-- ============================================
CREATE TABLE email_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL,
  recipient_email VARCHAR(255),
  email_type VARCHAR(100),  -- order_confirmation, shipping_notification
  status VARCHAR(50),  -- sent, failed
  error_message TEXT,
  sent_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE INDEX idx_email_logs_order_id ON email_logs(order_id);
CREATE INDEX idx_email_logs_status ON email_logs(status);

-- ============================================
-- 10. affiliate_sales (어필리에이트 판매 기록)
-- ============================================
CREATE TABLE affiliate_sales (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  affiliate_code VARCHAR(100) NOT NULL,
  order_id UUID NOT NULL,
  commission_amount DECIMAL(10, 2),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(id)
);

CREATE INDEX idx_affiliate_sales_affiliate_code ON affiliate_sales(affiliate_code);

-- ============================================
-- 11. shipping_rates (지역별 배송료)
-- ============================================
CREATE TABLE shipping_rates (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  region VARCHAR(50) UNIQUE NOT NULL,  -- NCR, Luzon, Visayas, Mindanao
  fee DECIMAL(10, 2) NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 12. settings (시스템 설정)
-- ============================================
CREATE TABLE settings (
  id SERIAL PRIMARY KEY,
  profit_per_order DECIMAL(10, 2) DEFAULT 80.00,
  paypal_fee_rate_avg DECIMAL(5, 4),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================
-- 초기 데이터 삽입
-- ============================================

-- 지역별 배송료
INSERT INTO shipping_rates (region, fee) VALUES
('NCR', 100.00),
('Luzon', 120.00),
('Visayas', 140.00),
('Mindanao', 160.00);

-- 초기 설정
INSERT INTO settings (profit_per_order, paypal_fee_rate_avg) VALUES
(80.00, 0.029)  -- 평균 PayPal 수수료율 2.9%
ON CONFLICT DO NOTHING;
