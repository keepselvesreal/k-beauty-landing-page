import React, { useEffect, useState } from 'react';
import { FulfillmentPartnerOrdersResponse, FulfillmentPartnerOrder } from '../types';
import { api } from '../utils/api';
import './FulfillmentPartnerDashboard.css';

const FulfillmentPartnerDashboard: React.FC = () => {
  const [data, setData] = useState<FulfillmentPartnerOrdersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.getFulfillmentPartnerOrders();
      setData(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load orders';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    api.logout();
    window.location.href = '/';
  };

  if (loading) {
    return (
      <div className="dashboard">
        <div className="loading">로드 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard">
        <div className="error">
          <p>오류: {error}</p>
          <button onClick={() => window.location.href = '/'}>홈으로</button>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>배송담당자 대시보드</h1>
          <p className="partner-info">
            <strong>{data?.partner_name}</strong>
          </p>
        </div>
        <button className="logout-btn" onClick={handleLogout}>로그아웃</button>
      </header>

      <div className="dashboard-content">
        <div className="stats-section">
          <div className="stat-card">
            <div className="stat-value">{data?.orders.length || 0}</div>
            <div className="stat-label">배송 대기 중인 주문</div>
          </div>
        </div>

        <section className="orders-section">
          <h2>📦 배송 대기 주문 목록</h2>

          {data && data.orders.length === 0 ? (
            <div className="empty-state">
              <p>배송 대기 중인 주문이 없습니다.</p>
            </div>
          ) : (
            <div className="orders-grid">
              {data?.orders.map((order) => (
                <OrderCard key={order.order_id} order={order} />
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};

const OrderCard: React.FC<{ order: FulfillmentPartnerOrder }> = ({ order }) => {
  const createdDate = new Date(order.created_at).toLocaleDateString('ko-KR', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <div className="order-card">
      <div className="order-header">
        <div>
          <div className="order-number">{order.order_number}</div>
          <div className="order-date">{createdDate}</div>
        </div>
        <div className="order-status">
          <span className={`status-badge status-${order.status}`}>
            {order.status === 'preparing' ? '배송 준비' : order.status}
          </span>
        </div>
      </div>

      <div className="order-customer">
        <strong>고객:</strong> {order.customer_email}
      </div>

      <div className="order-address">
        <strong>배송주소:</strong> {order.shipping_address}
      </div>

      <div className="order-products">
        <strong>상품 목록:</strong>
        <ul>
          {order.products.map((product, idx) => (
            <li key={idx}>
              <span className="product-name">{product.name}</span>
              <span className="product-qty">x {product.quantity}</span>
              <span className="product-price">${parseFloat(String(product.unit_price)).toFixed(2)}</span>
            </li>
          ))}
        </ul>
      </div>

      <div className="order-footer">
        <div className="order-total">
          <strong>총액:</strong>
          <span>${parseFloat(String(order.total_price)).toFixed(2)}</span>
        </div>
        <button className="ship-btn">배송 정보 입력</button>
      </div>
    </div>
  );
};

export default FulfillmentPartnerDashboard;
