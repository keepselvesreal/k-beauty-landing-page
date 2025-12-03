import React, { useEffect, useState } from 'react';
import { FulfillmentPartnerOrdersResponse, FulfillmentPartnerOrder } from '../types';
import { api } from '../utils/api';
import ShipmentForm from './ShipmentForm';
import Toast from './Toast';
import InquiryModal from './InquiryModal';
import './FulfillmentPartnerDashboard.css';

const FulfillmentPartnerDashboard: React.FC = () => {
  const [data, setData] = useState<FulfillmentPartnerOrdersResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedOrder, setSelectedOrder] = useState<FulfillmentPartnerOrder | null>(null);
  const [isShipmentFormOpen, setIsShipmentFormOpen] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [isInquiryModalOpen, setIsInquiryModalOpen] = useState(false);

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

  const handleOpenShipmentForm = (order: FulfillmentPartnerOrder) => {
    setSelectedOrder(order);
    setIsShipmentFormOpen(true);
  };

  const handleCloseShipmentForm = () => {
    setIsShipmentFormOpen(false);
    setSelectedOrder(null);
  };

  const handleShipmentSuccess = () => {
    setToast({
      type: 'success',
      message: '배송 정보가 등록되었으며 고객에게 이메일이 발송되었습니다.',
    });
    // 주문 목록 새로고침
    loadOrders();
  };

  const handleShipmentError = (message: string) => {
    setToast({
      type: 'error',
      message: `배송 정보 등록에 실패했습니다: ${message}`,
    });
  };

  const handleCompleteDelivery = async (orderId: string) => {
    try {
      await api.completeDelivery(orderId);
      setToast({
        type: 'success',
        message: '배송이 완료되었습니다.',
      });
      await loadOrders();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to complete delivery';
      setToast({
        type: 'error',
        message: `배송 완료 처리에 실패했습니다: ${message}`,
      });
    } finally {
      setLoading(false);
    }
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
        <div className="header-buttons">
          <button className="inquiry-btn" onClick={() => setIsInquiryModalOpen(true)}>
            문의하기
          </button>
          <button className="logout-btn" onClick={handleLogout}>로그아웃</button>
        </div>
      </header>

      <div className="dashboard-content">
        <div className="stats-section">
          <div className="stat-card">
            <div className="stat-value">{data?.orders.length || 0}</div>
            <div className="stat-label">배송 주문</div>
          </div>
        </div>

        <section className="orders-section">
          <h2>📦 배송 주문 목록</h2>

          {data && data.orders.length === 0 ? (
            <div className="empty-state">
              <p>배송 주문이 없습니다.</p>
            </div>
          ) : (
            <div className="orders-table-wrapper">
              <table className="orders-table">
                <thead>
                  <tr>
                    <th>주문번호</th>
                    <th>구매자 이름</th>
                    <th>배송 지역</th>
                    <th>배송 주소</th>
                    <th>총액</th>
                    <th>배송 상태</th>
                    <th>배송정보</th>
                    <th>배송완료</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.orders.map((order) => (
                    <OrderTableRow
                      key={order.order_id}
                      order={order}
                      onShipmentClick={handleOpenShipmentForm}
                      onCompleteDelivery={handleCompleteDelivery}
                    />
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      {selectedOrder && (
        <ShipmentForm
          order={selectedOrder}
          isOpen={isShipmentFormOpen}
          onClose={handleCloseShipmentForm}
          onSuccess={handleShipmentSuccess}
          onError={handleShipmentError}
        />
      )}

      <InquiryModal
        isOpen={isInquiryModalOpen}
        onClose={() => setIsInquiryModalOpen(false)}
        inquiryType="fulfillment_partner"
        prefilledEmail={data?.partner_email}
      />

      {toast && (
        <Toast
          type={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

interface OrderTableRowProps {
  order: FulfillmentPartnerOrder;
  onShipmentClick: (order: FulfillmentPartnerOrder) => void;
  onCompleteDelivery: (orderId: string) => void;
}

const getStatusLabel = (status: string) => {
  const statusMap: { [key: string]: string } = {
    'preparing': '배송 준비',
    'in_transit': '배송 중',
    'shipped': '배송 완료',
    'delivered': '배송 완료'
  };
  return statusMap[status] || status;
};

const OrderTableRow: React.FC<OrderTableRowProps> = ({ order, onShipmentClick, onCompleteDelivery }) => {
  const fullAddress = order.customer_detailed_address
    ? `${order.customer_address}, ${order.customer_detailed_address}`
    : order.customer_address;

  const isPreparing = order.status === 'preparing';
  const isInTransit = order.status === 'in_transit';
  const isDelivered = order.status === 'delivered';

  return (
    <tr>
      <td className="order-number-col">{order.order_number}</td>
      <td className="customer-name-col">{order.customer_name}</td>
      <td className="region-col">{order.customer_region}</td>
      <td className="address-col">{fullAddress}</td>
      <td className="total-price-col">${parseFloat(String(order.total_price)).toFixed(2)}</td>
      <td className="status-col">
        <span className={`status-badge status-${order.status}`}>
          {getStatusLabel(order.status)}
        </span>
      </td>
      <td className="action-col">
        {isPreparing && (
          <button
            className="action-btn ship-info-btn"
            onClick={() => onShipmentClick(order)}
            title="배송 정보 입력"
          >
            배송정보
          </button>
        )}
      </td>
      <td className="action-col">
        {isPreparing && (
          <button
            className="action-btn complete-btn disabled"
            disabled
            title="먼저 배송 정보를 입력한 후 사용할 수 있습니다"
          >
            배송완료
          </button>
        )}
        {isInTransit && (
          <button
            className="action-btn complete-btn"
            onClick={() => onCompleteDelivery(order.order_id)}
            title="배송 완료"
          >
            배송완료
          </button>
        )}
        {isDelivered && (
          <span className="status-completed">배송 완료됨</span>
        )}
      </td>
    </tr>
  );
};

export default FulfillmentPartnerDashboard;
