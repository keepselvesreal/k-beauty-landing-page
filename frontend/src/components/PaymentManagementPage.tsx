import React, { useState, useEffect } from 'react';
import './PaymentManagementPage.css';

interface RefundRequest {
  refund_id: string;
  order_id: string;
  order_number: string;
  customer_name: string;
  total_price: number;
  refund_reason: string;
  refund_status: string;
  refund_requested_at: string;
}

const PaymentManagementPage: React.FC = () => {
  const [refunds, setRefunds] = useState<RefundRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authToken] = useState(sessionStorage.getItem('token') || '');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  useEffect(() => {
    if (!authToken) {
      setError('관리자 인증이 필요합니다. 다시 로그인해주세요.');
      setLoading(false);
      return;
    }
    fetchRefundRequests();
  }, [authToken]);

  const fetchRefundRequests = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`${API_BASE_URL}/api/admin/refunds`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.status === 401) {
        setError('인증이 필요합니다. 다시 로그인해주세요.');
        window.location.href = '/admin/login';
        return;
      }

      if (response.status === 403) {
        setError('관리자 권한이 필요합니다.');
        return;
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || `환불 요청 조회 실패: ${response.status}`);
      }

      const data = await response.json();
      setRefunds(data.refunds || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : '환불 요청 조회 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      minimumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'refund_requested':
        return 'status-pending';
      case 'refunded':
        return 'status-completed';
      default:
        return 'status-default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'refund_requested':
        return '환불 대기 중';
      case 'refunded':
        return '환불 완료';
      default:
        return status;
    }
  };

  return (
    <div className="payment-management-page">
      <div className="page-header">
        <h1>💳 결제 관리</h1>
        <p>환불 요청 현황을 확인하고 관리합니다.</p>
      </div>

      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button onClick={fetchRefundRequests}>재시도</button>
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>환불 요청 데이터를 불러오는 중...</p>
        </div>
      ) : refunds.length === 0 ? (
        <div className="empty-state">
          <p>환불 요청이 없습니다.</p>
        </div>
      ) : (
        <div className="refund-section">
          <div className="section-header">
            <h2>환불 요청 목록</h2>
            <div className="stats">
              <span className="stat-badge">{refunds.length}건</span>
            </div>
          </div>

          <div className="refund-table-wrapper">
            <table className="refund-table">
              <thead>
                <tr>
                  <th>환불 ID</th>
                  <th>주문 번호</th>
                  <th>고객명</th>
                  <th>환불 금액</th>
                  <th>환불 사유</th>
                  <th>상태</th>
                  <th>요청 날짜</th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                {refunds.map((refund) => (
                  <tr key={refund.refund_id}>
                    <td className="id-cell">
                      <span className="refund-id">{refund.refund_id}</span>
                    </td>
                    <td>
                      <span className="order-number">{refund.order_number}</span>
                    </td>
                    <td>{refund.customer_name}</td>
                    <td className="amount-cell">{formatCurrency(refund.total_price)}</td>
                    <td>{refund.refund_reason}</td>
                    <td>
                      <span className={`status-badge ${getStatusColor(refund.refund_status)}`}>
                        {getStatusLabel(refund.refund_status)}
                      </span>
                    </td>
                    <td className="date-cell">{formatDate(refund.refund_requested_at)}</td>
                    <td className="action-cell">
                      <button className="action-btn btn-approve">승인</button>
                      <button className="action-btn btn-reject">거절</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default PaymentManagementPage;
