import React, { useState } from 'react';
import './AdminDashboard.css';
import InventoryManagementPage from './InventoryManagementPage';
import StaffAccountManagement from './StaffAccountManagement';
import ShippingManagementPage from './ShippingManagementPage';

type PageType = 'dashboard' | 'inventory' | 'payment' | 'shipment' | 'inquiry' | 'accounts';

interface RefundRequest {
  refund_id: string;
  order_id: string;
  reason: string;
  status: string;
  requested_at: string;
}

const AdminDashboard: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard');

  // 더미 데이터
  const dashboardMetrics = {
    total_orders: 1250,
    total_profit: 125000000,
    pending_commission_influencer: 45000000,
    pending_commission_fulfillment: 32000000,
    completed_commission_influencer: 180000000,
    completed_commission_fulfillment: 120000000,
  };

  const refundRequests: RefundRequest[] = [
    {
      refund_id: 'REF-001',
      order_id: 'ORD-2024-001',
      reason: '상품 불량',
      status: '대기 중',
      requested_at: '2024-12-01',
    },
    {
      refund_id: 'REF-002',
      order_id: 'ORD-2024-002',
      reason: '사이즈 오류',
      status: '승인됨',
      requested_at: '2024-11-28',
    },
    {
      refund_id: 'REF-003',
      order_id: 'ORD-2024-003',
      reason: '변심',
      status: '거절됨',
      requested_at: '2024-11-25',
    },
  ];

  const menuItems = [
    { id: 'dashboard', label: '대시보드', icon: '📊' },
    { id: 'inventory', label: '재고 관리', icon: '📦' },
    { id: 'payment', label: '결제 관리', icon: '💳' },
    { id: 'shipment', label: '배송 관리', icon: '🚚' },
    { id: 'inquiry', label: '문의 관리', icon: '💬' },
    { id: 'accounts', label: '계정 관리', icon: '👥' },
  ];

  const renderPage = () => {
    switch (currentPage) {
      case 'inventory':
        return <InventoryManagementPage />;
      case 'accounts':
        return <StaffAccountManagement />;
      case 'shipment':
        return <ShippingManagementPage />;
      case 'payment':
      case 'inquiry':
        return (
          <div className="admin-dashboard">
            <div className="dashboard-header">
              <h1>{menuItems.find(m => m.id === currentPage)?.label}</h1>
            </div>
            <div className="empty-state">
              <p>준비 중인 페이지입니다.</p>
            </div>
          </div>
        );
      default:
        return <DashboardHub metrics={dashboardMetrics} refundRequests={refundRequests} />;
    }
  };

  return (
    <div className="admin-dashboard-container">
      {/* 헤더 네비게이션 */}
      <div className="admin-nav-header">
        <h1 className="admin-title">관리자 대시보드</h1>
        <nav className="admin-nav-menu">
          {menuItems.map((item) => (
            <button
              key={item.id}
              className={`nav-menu-item ${currentPage === item.id ? 'active' : ''}`}
              onClick={() => setCurrentPage(item.id as PageType)}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* 콘텐츠 영역 */}
      <div className="admin-content">
        {renderPage()}
      </div>
    </div>
  );
};

// 대시보드 허브 컴포넌트
interface DashboardHubProps {
  metrics: any;
  refundRequests: RefundRequest[];
}

const DashboardHub: React.FC<DashboardHubProps> = ({ metrics, refundRequests }) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      minimumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="dashboard-hub">
      <div className="dashboard-header">
        <h2>대시보드</h2>
      </div>

      {/* 주요 지표 카드 */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">총 주문 수</div>
          <div className="metric-value">{metrics.total_orders.toLocaleString()}</div>
          <div className="metric-unit">건</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">총 이윤</div>
          <div className="metric-value">{formatCurrency(metrics.total_profit)}</div>
        </div>
      </div>

      {/* 지급 예정 수수료 */}
      <div className="commission-section">
        <h3>지급 예정 수수료</h3>
        <div className="commission-grid">
          <div className="commission-card">
            <div className="commission-label">인플루언서</div>
            <div className="commission-amount">{formatCurrency(metrics.pending_commission_influencer)}</div>
          </div>
          <div className="commission-card">
            <div className="commission-label">배송담당자</div>
            <div className="commission-amount">{formatCurrency(metrics.pending_commission_fulfillment)}</div>
          </div>
        </div>
      </div>

      {/* 지급 완료 수수료 */}
      <div className="commission-section">
        <h3>지급 완료 수수료</h3>
        <div className="commission-grid">
          <div className="commission-card">
            <div className="commission-label">인플루언서</div>
            <div className="commission-amount">{formatCurrency(metrics.completed_commission_influencer)}</div>
          </div>
          <div className="commission-card">
            <div className="commission-label">배송담당자</div>
            <div className="commission-amount">{formatCurrency(metrics.completed_commission_fulfillment)}</div>
          </div>
        </div>
      </div>

      {/* 환불 요청 목록 */}
      <div className="refund-section">
        <h3>환불 요청</h3>
        <div className="refund-table-wrapper">
          <table className="refund-table">
            <thead>
              <tr>
                <th>환불 ID</th>
                <th>주문 ID</th>
                <th>사유</th>
                <th>상태</th>
                <th>신청일</th>
              </tr>
            </thead>
            <tbody>
              {refundRequests.map((request) => (
                <tr key={request.refund_id}>
                  <td>{request.refund_id}</td>
                  <td>{request.order_id}</td>
                  <td>{request.reason}</td>
                  <td>
                    <span className={`status-badge status-${request.status}`}>
                      {request.status}
                    </span>
                  </td>
                  <td>{request.requested_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
