import React, { useState, useEffect } from 'react';
import './ShippingManagementPage.css';
import Toast from './Toast';

interface Shipment {
  shipment_id: string;
  order_id: string;
  order_number: string;
  customer_name: string;
  customer_address: string;
  total_price: number;
  status: string;
  carrier: string | null;
  tracking_number: string | null;
  partner_name: string;
  shipped_at: string | null;
  delivered_at: string | null;
}

interface ToastMessage {
  type: 'success' | 'error' | 'info';
  text: string;
}

const ShippingManagementPage: React.FC = () => {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedShipment, setSelectedShipment] = useState<Shipment | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const [authToken] = useState(sessionStorage.getItem('token') || '');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // 배송 목록 조회
  const fetchShipments = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/admin/shipments`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      if (response.status === 401) {
        setToast({ type: 'error', text: '인증이 필요합니다. 다시 로그인해주세요.' });
        window.location.href = '/auth/login';
        return;
      }

      if (response.status === 403) {
        setToast({ type: 'error', text: '관리자 권한이 필요합니다.' });
        return;
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || '배송 조회에 실패했습니다.');
      }

      const data = await response.json();
      setShipments(data.shipments);
    } catch (error) {
      const message = error instanceof Error ? error.message : '배송 조회 중 오류가 발생했습니다.';
      setToast({ type: 'error', text: message });
      console.error('Error fetching shipments:', error);
    } finally {
      setLoading(false);
    }
  };

  // 초기 로드
  useEffect(() => {
    fetchShipments();
  }, []);

  // 배송 완료 처리
  const handleCompleteShipment = async (shipmentId: string) => {
    try {
      setCompletingId(shipmentId);
      const response = await fetch(`${API_BASE_URL}/api/admin/shipments/${shipmentId}/complete`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || '배송 완료 처리에 실패했습니다.');
      }

      setToast({ type: 'success', text: '배송이 완료되었습니다.' });
      setShowModal(false);
      setSelectedShipment(null);
      fetchShipments();
    } catch (error) {
      const message = error instanceof Error ? error.message : '배송 완료 처리 중 오류가 발생했습니다.';
      setToast({ type: 'error', text: message });
    } finally {
      setCompletingId(null);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatCurrency = (price: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      minimumFractionDigits: 0,
    }).format(price);
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'preparing':
        return 'badge-preparing';
      case 'shipped':
        return 'badge-shipped';
      case 'delivered':
        return 'badge-delivered';
      default:
        return 'badge-unknown';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'preparing':
        return '배송 준비 중';
      case 'shipped':
        return '배송 중';
      case 'delivered':
        return '배송 완료';
      default:
        return status;
    }
  };

  if (loading) {
    return <div className="shipping-page loading">로딩 중...</div>;
  }

  return (
    <div className="shipping-page">
      <div className="page-header">
        <h1>배송 관리</h1>
        <button className="btn-refresh" onClick={fetchShipments} disabled={loading}>
          새로고침
        </button>
      </div>

      {shipments.length === 0 ? (
        <div className="empty-state">
          <p>배송 정보가 없습니다.</p>
        </div>
      ) : (
        <div className="shipments-table-wrapper">
          <table className="shipments-table">
            <thead>
              <tr>
                <th>주문 번호</th>
                <th>배송 담당자</th>
                <th>배송 상태</th>
              </tr>
            </thead>
            <tbody>
              {shipments.map((shipment) => (
                <tr
                  key={shipment.shipment_id}
                  className="shipment-row"
                  onClick={() => {
                    setSelectedShipment(shipment);
                    setShowModal(true);
                  }}
                >
                  <td className="order-number">{shipment.order_number}</td>
                  <td className="partner-name">{shipment.partner_name}</td>
                  <td className="status">
                    <span className={`status-badge ${getStatusBadgeClass(shipment.status)}`}>
                      {getStatusLabel(shipment.status)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 상세 정보 모달 */}
      {showModal && selectedShipment && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>배송 상세 정보</h2>
            </div>

            <div className="modal-body">
              <div className="info-section">
                <h3>주문 정보</h3>
                <div className="info-item">
                  <span className="label">주문 번호:</span>
                  <span className="value">{selectedShipment.order_number}</span>
                </div>
              </div>

              <div className="info-section">
                <h3>고객 정보</h3>
                <div className="info-item">
                  <span className="label">고객명:</span>
                  <span className="value">{selectedShipment.customer_name}</span>
                </div>
                <div className="info-item">
                  <span className="label">배송 주소:</span>
                  <span className="value">{selectedShipment.customer_address}</span>
                </div>
              </div>

              <div className="info-section">
                <h3>결제 정보</h3>
                <div className="info-item">
                  <span className="label">총액:</span>
                  <span className="value">{formatCurrency(selectedShipment.total_price)}</span>
                </div>
              </div>

              <div className="info-section">
                <h3>배송 정보</h3>
                <div className="info-item">
                  <span className="label">배송 상태:</span>
                  <span className={`status-badge ${getStatusBadgeClass(selectedShipment.status)}`}>
                    {getStatusLabel(selectedShipment.status)}
                  </span>
                </div>
                <div className="info-item">
                  <span className="label">배송담당자:</span>
                  <span className="value">{selectedShipment.partner_name}</span>
                </div>

                {selectedShipment.status === 'shipped' && (
                  <>
                    <div className="info-item">
                      <span className="label">택배사:</span>
                      <span className="value">{selectedShipment.carrier || '-'}</span>
                    </div>
                    <div className="info-item">
                      <span className="label">송장 번호:</span>
                      <span className="value">{selectedShipment.tracking_number || '-'}</span>
                    </div>
                  </>
                )}

                <div className="info-item">
                  <span className="label">발송일시:</span>
                  <span className="value">{formatDate(selectedShipment.shipped_at)}</span>
                </div>

                {selectedShipment.delivered_at && (
                  <div className="info-item">
                    <span className="label">완료일시:</span>
                    <span className="value">{formatDate(selectedShipment.delivered_at)}</span>
                  </div>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <button
                className="btn btn-secondary"
                onClick={() => setShowModal(false)}
                disabled={completingId !== null}
              >
                닫기
              </button>
              {selectedShipment.status !== 'delivered' && (
                <button
                  className="btn btn-primary"
                  onClick={() => handleCompleteShipment(selectedShipment.shipment_id)}
                  disabled={completingId !== null}
                >
                  {completingId === selectedShipment.shipment_id ? '처리 중...' : '배송 완료'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {toast && (
        <Toast
          type={toast.type}
          message={toast.text}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
};

export default ShippingManagementPage;
