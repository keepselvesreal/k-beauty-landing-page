import React, { useEffect, useState } from 'react';
import { api, InfluencerDashboard as InfluencerDashboardData } from '../utils/api';
import Toast from './Toast';
import InquiryModal from './InquiryModal';
import './InfluencerDashboard.css';

const InfluencerDashboard: React.FC = () => {
  const [data, setData] = useState<InfluencerDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [isInquiryModalOpen, setIsInquiryModalOpen] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await api.getInfluencerDashboard();
      setData(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load dashboard';
      setError(message);
      setToast({ type: 'error', message });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    api.logout();
    window.location.href = '/';
  };

  const handleCopyUrl = async () => {
    if (!data?.affiliate_url) return;

    try {
      await navigator.clipboard.writeText(data.affiliate_url);
      setToast({ type: 'success', message: 'URL이 복사되었습니다' });
    } catch (err) {
      setToast({ type: 'error', message: 'URL 복사에 실패했습니다' });
    }
  };

  if (loading) {
    return (
      <div className="influencer-dashboard">
        <div className="loading">로드 중...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="influencer-dashboard">
        <div className="error">
          <p>오류: {error}</p>
          <button onClick={() => window.location.href = '/'}>홈으로</button>
        </div>
      </div>
    );
  }

  return (
    <div className="influencer-dashboard">
      <header className="dashboard-header">
        <div className="header-left">
          <h1>인플루언서 대시보드</h1>
          {data && (
            <p className="affiliate-code">
              <strong>코드: {data.affiliate_code}</strong>
            </p>
          )}
        </div>
        <div className="header-buttons">
          <button className="nav-btn" onClick={() => window.location.href = '/settings'}>
            비밀번호 변경
          </button>
          <button className="logout-btn" onClick={handleLogout}>로그아웃</button>
        </div>
      </header>

      <div className="dashboard-content">
        <section className="stats-grid">
          <div className="stat-card">
            <div className="stat-label">총 클릭 수</div>
            <div className="stat-value">{data?.total_clicks || 0}</div>
          </div>

          <div className="stat-card">
            <div className="stat-label">판매 건수</div>
            <div className="stat-value">{data?.total_sales || 0}</div>
          </div>

          <div className="stat-card">
            <div className="stat-label">누적 수익</div>
            <div className="stat-value">₱{data?.cumulative_revenue?.toFixed(2) || '0.00'}</div>
          </div>

          <div className="stat-card highlight">
            <div className="stat-label">지급 예상 수수료</div>
            <div className="stat-value">₱{data?.pending_commission?.toFixed(2) || '0.00'}</div>
          </div>
        </section>

        <section className="affiliate-url-section">
          <h2>📤 어필리에이트 추적 URL</h2>
          <div className="url-container">
            <input
              type="text"
              value={data?.affiliate_url || ''}
              readOnly
              className="url-input"
            />
            <button className="copy-btn" onClick={handleCopyUrl}>
              복사
            </button>
          </div>
        </section>

        {data?.next_payment_date && (
          <section className="payment-info-section">
            <h2>💰 지급 정보</h2>
            <div className="payment-info">
              <p>지급 예정 날짜: <strong>{new Date(data.next_payment_date).toLocaleDateString('ko-KR')}</strong></p>
            </div>
          </section>
        )}

        <section className="inquiry-section">
          <button className="inquiry-btn" onClick={() => setIsInquiryModalOpen(true)}>
            문의하기
          </button>
        </section>
      </div>

      <InquiryModal
        isOpen={isInquiryModalOpen}
        onClose={() => setIsInquiryModalOpen(false)}
        inquiryType="influencer"
        prefilledEmail={data?.affiliate_code ? `${data.affiliate_code}@affiliate` : undefined}
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

export default InfluencerDashboard;
