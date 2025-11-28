# Database Schema Documentation

## 개요
12개 테이블로 구성된 K-Beauty Landing Page의 완전한 DB 스키마

---

## 1. customers (고객)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 고객 ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 이메일 주소 |
| name | VARCHAR(255) | NOT NULL | 고객명 |
| phone | VARCHAR(20) | | 전화번호 |
| address | TEXT | | 배송 주소 |
| region | VARCHAR(50) | | 지역 (NCR, Luzon, Visayas, Mindanao) |
| created_at | TIMESTAMP | DEFAULT NOW | 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW | 수정일시 |

**인덱스**: `idx_customers_email` (email)

---

## 2. fulfillment_partners (배송담당자)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 배송담당자 ID |
| name | VARCHAR(255) | NOT NULL | 담당자명 |
| email | VARCHAR(255) | UNIQUE | 이메일 |
| phone | VARCHAR(20) | | 전화번호 |
| address | TEXT | | 주소 |
| region | VARCHAR(50) | | 담당 지역 |
| is_active | BOOLEAN | DEFAULT TRUE | 활성 여부 |
| last_allocated_at | TIMESTAMP | | 마지막 할당 시간 (라운드 로빈) |
| created_at | TIMESTAMP | DEFAULT NOW | 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW | 수정일시 |

**인덱스**: 
- `idx_fulfillment_partners_is_active` (is_active)
- `idx_fulfillment_partners_last_allocated_at` (last_allocated_at)

---

## 3. products (상품)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 상품 ID |
| name | VARCHAR(255) | NOT NULL | 상품명 |
| description | TEXT | | 상품 설명 |
| price | DECIMAL(10,2) | NOT NULL | 가격 |
| sku | VARCHAR(100) | UNIQUE | 상품 SKU |
| image_url | VARCHAR(500) | | 이미지 URL |
| is_active | BOOLEAN | DEFAULT TRUE | 판매 여부 |
| created_at | TIMESTAMP | DEFAULT NOW | 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW | 수정일시 |

**인덱스**: `idx_products_is_active` (is_active)

---

## 4. partner_allocated_inventory (배송담당자별 할당 재고)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 재고 ID |
| partner_id | UUID | FK | 배송담당자 ID |
| product_id | UUID | FK | 상품 ID |
| allocated_quantity | INT | NOT NULL | 분배받은 총 수량 |
| remaining_quantity | INT | NOT NULL | 미배송 남은 수량 |
| stock_version | INT | DEFAULT 0 | 낙관적 락 버전 |
| allocated_date | DATE | | 분배 날짜 |
| created_at | TIMESTAMP | DEFAULT NOW | 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW | 수정일시 |

**제약**: 
- UNIQUE(partner_id, product_id) - 배송담당자당 상품당 1개 레코드

**인덱스**:
- `idx_partner_allocated_inventory_partner_id` (partner_id)
- `idx_partner_allocated_inventory_remaining_quantity` (remaining_quantity)

---

## 5. orders (주문)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 주문 ID |
| order_number | VARCHAR(50) | UNIQUE | 주문번호 |
| customer_id | UUID | FK | 고객 ID |
| fulfillment_partner_id | UUID | FK | 배송담당자 ID |
| subtotal | DECIMAL(10,2) | NOT NULL | 상품 총액 |
| shipping_fee | DECIMAL(10,2) | DEFAULT 0 | 배송료 |
| total_price | DECIMAL(10,2) | NOT NULL | 최종 결제액 |
| status | VARCHAR(50) | DEFAULT 'pending' | 결제상태 (pending, paid, payment_failed, cancelled) |
| paypal_order_id | VARCHAR(255) | | PayPal 주문 ID |
| paypal_capture_id | VARCHAR(255) | | PayPal 캡처 ID |
| paypal_fee | DECIMAL(10,2) | | PayPal 수수료 |
| profit | DECIMAL(10,2) | DEFAULT 80 | 이윤 |
| paid_at | TIMESTAMP | | 결제 완료 시간 |
| shipping_status | VARCHAR(50) | DEFAULT 'pending' | 배송상태 (pending, preparing, shipped, delivered) |
| shipped_at | TIMESTAMP | | 배송 발송 시간 |
| affiliate_code | VARCHAR(100) | | 어필리에이트 코드 |
| affiliate_commission | DECIMAL(10,2) | | 어필리에이트 커미션 |
| created_at | TIMESTAMP | DEFAULT NOW | 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW | 수정일시 |

**인덱스**:
- `idx_orders_order_number` (order_number)
- `idx_orders_customer_id` (customer_id)
- `idx_orders_status` (status)
- `idx_orders_shipping_status` (shipping_status)
- `idx_orders_fulfillment_partner_id` (fulfillment_partner_id)

---

## 6. order_items (주문 상품)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 주문상품 ID |
| order_id | UUID | FK | 주문 ID |
| product_id | UUID | FK | 상품 ID |
| quantity | INT | NOT NULL | 수량 |
| unit_price | DECIMAL(10,2) | NOT NULL | 단가 |
| created_at | TIMESTAMP | DEFAULT NOW | 생성일시 |

**인덱스**: `idx_order_items_order_id` (order_id)

---

## 7. shipment_allocations (배송 할당 기록)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 할당 ID |
| order_id | UUID | FK | 주문 ID |
| order_item_id | UUID | FK | 주문상품 ID |
| partner_id | UUID | FK | 배송담당자 ID |
| quantity | INT | NOT NULL | 배송 수량 |
| allocated_at | TIMESTAMP | DEFAULT NOW | 할당 시간 |

**인덱스**: `idx_shipment_allocations_order_id` (order_id)

---

## 8. shipments (배송 기록)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 배송 ID |
| order_id | UUID | FK | 주문 ID |
| partner_id | UUID | FK | 배송담당자 ID |
| tracking_number | VARCHAR(255) | | 추적번호 |
| status | VARCHAR(50) | DEFAULT 'preparing' | 배송상태 (preparing, shipped, in_transit, delivered) |
| shipped_at | TIMESTAMP | | 배송 발송 시간 |
| delivered_at | TIMESTAMP | | 배송 완료 시간 |
| notes | TEXT | | 메모 |
| created_at | TIMESTAMP | DEFAULT NOW | 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW | 수정일시 |

**인덱스**:
- `idx_shipments_order_id` (order_id)
- `idx_shipments_status` (status)

---

## 9. email_logs (이메일 발송 로그)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 로그 ID |
| order_id | UUID | FK | 주문 ID |
| recipient_email | VARCHAR(255) | | 수신자 이메일 |
| email_type | VARCHAR(100) | | 이메일 유형 (order_confirmation, shipping_notification) |
| status | VARCHAR(50) | | 발송상태 (sent, failed) |
| error_message | TEXT | | 에러 메시지 |
| sent_at | TIMESTAMP | | 발송 시간 |
| created_at | TIMESTAMP | DEFAULT NOW | 생성일시 |

**인덱스**:
- `idx_email_logs_order_id` (order_id)
- `idx_email_logs_status` (status)

---

## 10. affiliate_sales (어필리에이트 판매 기록)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 판매 ID |
| affiliate_code | VARCHAR(100) | NOT NULL | 어필리에이트 코드 |
| order_id | UUID | FK | 주문 ID |
| commission_amount | DECIMAL(10,2) | | 커미션 금액 (이윤의 20%) |
| created_at | TIMESTAMP | DEFAULT NOW | 생성일시 |

**인덱스**: `idx_affiliate_sales_affiliate_code` (affiliate_code)

---

## 11. shipping_rates (지역별 배송료)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | UUID | PK | 배송료 ID |
| region | VARCHAR(50) | UNIQUE NOT NULL | 지역 (NCR, Luzon, Visayas, Mindanao) |
| fee | DECIMAL(10,2) | NOT NULL | 배송료 |
| created_at | TIMESTAMP | DEFAULT NOW | 생성일시 |
| updated_at | TIMESTAMP | DEFAULT NOW | 수정일시 |

---

## 12. settings (시스템 설정)

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| id | SERIAL | PK | 설정 ID |
| profit_per_order | DECIMAL(10,2) | DEFAULT 80 | 주문당 이윤 |
| paypal_fee_rate_avg | DECIMAL(5,4) | | PayPal 평균 수수료율 |
| updated_at | TIMESTAMP | DEFAULT NOW | 수정일시 |

---

## 초기 데이터

### shipping_rates
```sql
INSERT INTO shipping_rates (region, fee) VALUES
('NCR', 100.00),
('Luzon', 120.00),
('Visayas', 140.00),
('Mindanao', 160.00);
```

### settings
```sql
INSERT INTO settings (profit_per_order, paypal_fee_rate_avg) VALUES
(80.00, 0.029);
```

---

## 관계도

```
customers (1) ──── (N) orders
fulfillment_partners (1) ──── (N) orders
fulfillment_partners (1) ──── (N) partner_allocated_inventory
products (1) ──── (N) partner_allocated_inventory
products (1) ──── (N) order_items
orders (1) ──── (N) order_items
orders (1) ──── (N) shipment_allocations
order_items (1) ──── (N) shipment_allocations
fulfillment_partners (1) ──── (N) shipment_allocations
orders (1) ──── (N) shipments
fulfillment_partners (1) ──── (N) shipments
orders (1) ──── (N) email_logs
orders (1) ──── (N) affiliate_sales
```

---

## 주요 특징

1. **UUID 기본 키**: 분산 시스템에 대비
2. **낙관적 락**: `partner_allocated_inventory.stock_version`으로 재고 동시성 처리
3. **인덱스**: 조회 성능 최적화
4. **타임스탬프**: 생성일시와 수정일시로 감사 추적
5. **라운드 로빈**: `fulfillment_partners.last_allocated_at`으로 공정한 주문 분배

