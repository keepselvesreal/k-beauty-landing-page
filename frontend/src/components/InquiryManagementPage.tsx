import React, { useEffect, useState } from 'react';
import { api, InquiryDetail, InquiriesListResponse } from '../utils/api';
import Toast from './Toast';
import './InquiryManagementPage.css';

interface InquiryModalState {
  isOpen: boolean;
  inquiry: InquiryDetail | null;
}

const InquiryManagementPage: React.FC = () => {
  const [inquiries, setInquiries] = useState<InquiryDetail[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // 필터링
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  // 페이지네이션
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [total, setTotal] = useState(0);

  // 상세 보기 모달
  const [detailModal, setDetailModal] = useState<InquiryModalState>({
    isOpen: false,
    inquiry: null,
  });

  // 문의 목록 로드
  const loadInquiries = async (page: number = 1) => {
    try {
      setLoading(true);
      setError(null);

      const type = selectedType || undefined;
      const status = selectedStatus || undefined;

      const result: InquiriesListResponse = await api.getInquiries(
        page,
        pageSize,
        type,
        status
      );

      setInquiries(result.inquiries);
      setTotal(result.total);
      setCurrentPage(page);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load inquiries';
      setError(message);
      setToast({ type: 'error', message });
    } finally {
      setLoading(false);
    }
  };

  // 초기 로드 및 필터 변경 시
  useEffect(() => {
    loadInquiries(1);
  }, [selectedType, selectedStatus]);

  // 상태 변경
  const handleStatusChange = async (inquiryId: string, newStatus: string) => {
    try {
      const updated = await api.updateInquiryStatus(inquiryId, newStatus);

      // 목록 업데이트
      setInquiries(inquiries.map(i => i.id === inquiryId ? updated : i));

      // 상세 보기 업데이트
      if (detailModal.inquiry?.id === inquiryId) {
        setDetailModal({
          ...detailModal,
          inquiry: updated,
        });
      }

      setToast({ type: 'success', message: '상태가 변경되었습니다' });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update status';
      setToast({ type: 'error', message });
    }
  };

  // 상세 보기 열기
  const handleOpenDetail = (inquiry: InquiryDetail) => {
    setDetailModal({
      isOpen: true,
      inquiry,
    });
  };

  // 상세 보기 닫기
  const handleCloseDetail = () => {
    setDetailModal({
      isOpen: false,
      inquiry: null,
    });
  };

  // 페이지 변경
  const totalPages = Math.ceil(total / pageSize);

  const getInquiryTypeLabel = (type: string) => {
    switch (type) {
      case 'influencer':
        return '인플루언서';
      case 'fulfillment_partner':
        return '배송담당자';
      case 'customer':
        return '고객';
      default:
        return type;
    }
  };

  const getStatusBadgeClass = (status: string) => {
    return status === 'unread' ? 'status-unread' : 'status-read';
  };

  return (
    <div className="inquiry-management-page">
      <div className="page-header">
        <h1>문의 관리</h1>
        <p className="page-subtitle">고객, 인플루언서, 배송담당자의 문의를 관리합니다</p>
      </div>

      {/* 필터 섹션 */}
      <div className="filter-section">
        <div className="filter-group">
          <label>문의 타입</label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="filter-select"
          >
            <option value="">전체</option>
            <option value="customer">고객</option>
            <option value="influencer">인플루언서</option>
            <option value="fulfillment_partner">배송담당자</option>
          </select>
        </div>

        <div className="filter-group">
          <label>상태</label>
          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="filter-select"
          >
            <option value="">전체</option>
            <option value="unread">미읽음</option>
            <option value="read">읽음</option>
          </select>
        </div>

        <div className="filter-info">
          <span>총 {total}건</span>
        </div>
      </div>

      {/* 로딩 상태 */}
      {loading && <div className="loading">로드 중...</div>}

      {/* 에러 상태 */}
      {error && <div className="error-message">{error}</div>}

      {/* 문의 목록 */}
      {!loading && inquiries.length === 0 ? (
        <div className="empty-state">
          <p>문의가 없습니다.</p>
        </div>
      ) : (
        <>
          <div className="inquiries-table-container">
            <table className="inquiries-table">
              <thead>
                <tr>
                  <th>타입</th>
                  <th>이메일</th>
                  <th>상태</th>
                  <th>생성일</th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                {inquiries.map((inquiry) => (
                  <tr key={inquiry.id}>
                    <td className="type-cell">
                      <span className="type-badge">
                        {getInquiryTypeLabel(inquiry.inquiry_type)}
                      </span>
                    </td>
                    <td className="email-cell">{inquiry.reply_to_email}</td>
                    <td className="status-cell">
                      <span className={`status-badge ${getStatusBadgeClass(inquiry.status)}`}>
                        {inquiry.status === 'unread' ? '미읽음' : '읽음'}
                      </span>
                    </td>
                    <td className="date-cell">
                      {new Date(inquiry.created_at).toLocaleDateString('ko-KR', {
                        month: 'short',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </td>
                    <td className="action-cell">
                      <button
                        className="btn-detail"
                        onClick={() => handleOpenDetail(inquiry)}
                      >
                        상세보기
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 페이지네이션 */}
          {totalPages > 1 && (
            <div className="pagination">
              <button
                className="pagination-btn"
                onClick={() => loadInquiries(currentPage - 1)}
                disabled={currentPage === 1}
              >
                이전
              </button>

              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  className={`pagination-btn ${currentPage === page ? 'active' : ''}`}
                  onClick={() => loadInquiries(page)}
                >
                  {page}
                </button>
              ))}

              <button
                className="pagination-btn"
                onClick={() => loadInquiries(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                다음
              </button>
            </div>
          )}
        </>
      )}

      {/* 상세 보기 모달 */}
      {detailModal.isOpen && detailModal.inquiry && (
        <InquiryDetailModal
          inquiry={detailModal.inquiry}
          onClose={handleCloseDetail}
          onStatusChange={handleStatusChange}
        />
      )}

      {/* 토스트 알림 */}
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

interface InquiryDetailModalProps {
  inquiry: InquiryDetail;
  onClose: () => void;
  onStatusChange: (inquiryId: string, newStatus: string) => void;
}

const InquiryDetailModal: React.FC<InquiryDetailModalProps> = ({
  inquiry,
  onClose,
  onStatusChange,
}) => {
  const getInquiryTypeLabel = (type: string) => {
    switch (type) {
      case 'influencer':
        return '인플루언서';
      case 'fulfillment_partner':
        return '배송담당자';
      case 'customer':
        return '고객';
      default:
        return type;
    }
  };

  const handleStatusToggle = () => {
    const newStatus = inquiry.status === 'unread' ? 'read' : 'unread';
    onStatusChange(inquiry.id, newStatus);
  };

  return (
    <div className="inquiry-detail-modal-overlay" onClick={onClose}>
      <div
        className="inquiry-detail-modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <h2>문의 상세</h2>
          <button className="modal-close" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="modal-body">
          <div className="detail-row">
            <label>문의 ID</label>
            <div className="detail-value">{inquiry.id}</div>
          </div>

          <div className="detail-row">
            <label>문의 타입</label>
            <div className="detail-value">
              <span className="type-badge">{getInquiryTypeLabel(inquiry.inquiry_type)}</span>
            </div>
          </div>

          <div className="detail-row">
            <label>회신받을 이메일</label>
            <div className="detail-value email">{inquiry.reply_to_email}</div>
          </div>

          <div className="detail-row">
            <label>상태</label>
            <div className="detail-value">
              <span className={`status-badge ${inquiry.status === 'unread' ? 'status-unread' : 'status-read'}`}>
                {inquiry.status === 'unread' ? '미읽음' : '읽음'}
              </span>
            </div>
          </div>

          <div className="detail-row">
            <label>생성일</label>
            <div className="detail-value">
              {new Date(inquiry.created_at).toLocaleDateString('ko-KR', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              })}
            </div>
          </div>

          <div className="detail-row full-width">
            <label>문의 내용</label>
            <div className="detail-value message">{inquiry.message}</div>
          </div>
        </div>

        <div className="modal-footer">
          <button
            className={`btn-status-toggle ${inquiry.status === 'unread' ? 'btn-mark-read' : 'btn-mark-unread'}`}
            onClick={handleStatusToggle}
          >
            {inquiry.status === 'unread' ? '읽음으로 표시' : '미읽음으로 표시'}
          </button>
          <button className="btn-close" onClick={onClose}>
            닫기
          </button>
        </div>
      </div>
    </div>
  );
};

export default InquiryManagementPage;
