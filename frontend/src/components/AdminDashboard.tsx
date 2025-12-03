import React, { useState, useEffect } from 'react';
import './AdminDashboard.css';
import InventoryManagementPage from './InventoryManagementPage';
import StaffAccountManagement from './StaffAccountManagement';
import ShippingManagementPage from './ShippingManagementPage';
import PaymentManagementPage from './PaymentManagementPage';
import InquiryManagementPage from './InquiryManagementPage';
import { AdminDashboardResponse } from '../types';

type PageType = 'dashboard' | 'inventory' | 'payment' | 'shipment' | 'inquiry' | 'accounts';

const AdminDashboard: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<PageType>('dashboard');
  const [dashboardData, setDashboardData] = useState<AdminDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);


  // API 호출
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const token = sessionStorage.getItem('token');

        if (!token) {
          setError('인증 토큰을 찾을 수 없습니다.');
          setLoading(false);
          return;
        }

        const apiBaseUrl = process.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const response = await fetch(`${apiBaseUrl}/api/admin/dashboard`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error('API Error Response:', errorText);
          throw new Error(`Failed to fetch dashboard data: ${response.status} ${response.statusText}`);
        }

        const responseText = await response.text();
        console.log('Raw API Response:', responseText);

        const data: AdminDashboardResponse = JSON.parse(responseText);
        setDashboardData(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : '대시보드 데이터를 불러올 수 없습니다.');
        console.error('Dashboard fetch error:', err);
      } finally {
        setLoading(false);
      }
    };

    if (currentPage === 'dashboard') {
      fetchDashboardData();
    }
  }, [currentPage]);

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
        return <PaymentManagementPage />;
      case 'inquiry':
        return <InquiryManagementPage />;
      default:
        return (
          <DashboardHub
            loading={loading}
            error={error}
            data={dashboardData}
          />
        );
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
  loading: boolean;
  error: string | null;
  data: AdminDashboardResponse | null;
}

const DashboardHub: React.FC<DashboardHubProps> = ({
  loading,
  error,
  data,
}) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      minimumFractionDigits: 0,
    }).format(value);
  };

  if (loading) {
    return (
      <div className="dashboard-hub">
        <div className="dashboard-header">
          <h2>대시보드</h2>
        </div>
        <div style={{ textAlign: 'center', padding: '40px' }}>로딩 중...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="dashboard-hub">
        <div className="dashboard-header">
          <h2>대시보드</h2>
        </div>
        <div style={{ textAlign: 'center', padding: '40px', color: 'red' }}>
          오류: {error || '데이터를 불러올 수 없습니다.'}
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-hub">
      <div className="dashboard-header">
        <h2>대시보드</h2>
      </div>

      {/* 주요 지표 카드 */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">총 주문 수</div>
          <div className="metric-value">{data.summary.total_orders.toLocaleString()}</div>
          <div className="metric-unit">건</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">총 이윤</div>
          <div className="metric-value">{formatCurrency(Number(data.summary.total_profit))}</div>
        </div>
      </div>

      {/* 인플루언서 커미션 */}
      <div className="commission-section">
        <h3>💰 인플루언서 수수료</h3>
        <div className="commission-table-wrapper">
          <table className="commission-table">
            <thead>
              <tr>
                <th>인플루언서명</th>
                <th>지급 완료액</th>
                <th>지급 예정액</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {data.influencer_commissions.pending.map((item: any) => (
                <tr key={item.influencer_id}>
                  <td>{item.influencer_name}</td>
                  <td>{formatCurrency(Number(item.completed_amount))}</td>
                  <td>{formatCurrency(Number(item.pending_amount))}</td>
                  <td>
                    <button
                      onClick={() => {
                        alert(`인플루언서 ${item.influencer_name}에게 ₩${formatCurrency(Number(item.pending_amount))} 지급 완료!`);
                      }}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: item.pending_amount > 0 ? '#28a745' : '#ccc',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: item.pending_amount > 0 ? 'pointer' : 'not-allowed',
                        fontSize: '12px',
                        fontWeight: 'bold',
                      }}
                      disabled={item.pending_amount <= 0}
                    >
                      지급
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 배송담당자 커미션 */}
      <div className="commission-section">
        <h3>🚚 배송담당자 수수료</h3>
        <div className="commission-table-wrapper">
          <table className="commission-table">
            <thead>
              <tr>
                <th>배송담당자명</th>
                <th>지급 완료액</th>
                <th>지급 예정액</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {data.fulfillment_commissions.pending.map((item: any) => (
                <tr key={item.partner_id}>
                  <td>{item.partner_name}</td>
                  <td>{formatCurrency(Number(item.completed_amount))}</td>
                  <td>{formatCurrency(Number(item.pending_amount))}</td>
                  <td>
                    <button
                      onClick={() => {
                        alert(`배송담당자 ${item.partner_name}에게 ₩${formatCurrency(Number(item.pending_amount))} 지급 완료!`);
                      }}
                      style={{
                        padding: '6px 12px',
                        backgroundColor: item.pending_amount > 0 ? '#28a745' : '#ccc',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: item.pending_amount > 0 ? 'pointer' : 'not-allowed',
                        fontSize: '12px',
                        fontWeight: 'bold',
                      }}
                      disabled={item.pending_amount <= 0}
                    >
                      지급
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 환불 요청 목록 */}
      <div className="refund-section">
        <h3>⚠️ 환불 요청</h3>
        <div className="refund-table-wrapper">
          <table className="refund-table">
            <thead>
              <tr>
                <th>환불 ID</th>
                <th>주문번호</th>
                <th>고객명</th>
                <th>환불금액</th>
                <th>사유</th>
                <th>신청일</th>
              </tr>
            </thead>
            <tbody>
              {data.refund_requests.length > 0 ? (
                data.refund_requests.map((request: any) => (
                  <tr key={request.refund_id}>
                    <td>{request.refund_id}</td>
                    <td>{request.order_number}</td>
                    <td>{request.customer_name}</td>
                    <td>{formatCurrency(Number(request.refund_amount))}</td>
                    <td>{request.refund_reason}</td>
                    <td>{new Date(request.requested_at).toLocaleDateString('ko-KR')}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} style={{ textAlign: 'center', padding: '20px' }}>
                    환불 요청이 없습니다.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
