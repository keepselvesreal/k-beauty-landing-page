import React, { useState, useEffect } from 'react';
import './AdminDashboard.css';
import InventoryAdjustmentModal from './InventoryAdjustmentModal';
import Toast from './Toast';

interface InventoryItem {
  inventory_id: string;
  partner_id: string;
  partner_name: string;
  product_id: string;
  product_name: string;
  current_quantity: number;
  allocated_quantity: number;
  last_adjusted_at: string;
}

interface InventoryListResponse {
  inventories: InventoryItem[];
  total_count: number;
}

interface ToastMessage {
  type: 'success' | 'error' | 'info';
  text: string;
}

const InventoryManagementPage: React.FC = () => {
  const [inventories, setInventories] = useState<InventoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedInventory, setSelectedInventory] = useState<InventoryItem | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const [authToken] = useState(sessionStorage.getItem('token') || '');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // 재고 목록 조회
  const fetchInventories = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/admin/inventory`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      });

      if (response.status === 401) {
        setToast({ type: 'error', text: '인증이 필요합니다. 다시 로그인해주세요.' });
        // 로그인 페이지로 리다이렉트
        window.location.href = '/admin/login';
        return;
      }

      if (response.status === 403) {
        setToast({ type: 'error', text: '관리자 권한이 필요합니다.' });
        return;
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || '재고 조회에 실패했습니다.');
      }

      const data: InventoryListResponse = await response.json();
      setInventories(data.inventories);
      setToast({ type: 'success', text: `${data.total_count}개의 재고를 불러왔습니다.` });
    } catch (error) {
      const message = error instanceof Error ? error.message : '재고 조회 중 오류가 발생했습니다.';
      setToast({ type: 'error', text: message });
      console.error('Error fetching inventories:', error);
    } finally {
      setLoading(false);
    }
  };

  // 초기 로드
  useEffect(() => {
    fetchInventories();
  }, []);

  // 모달 닫기
  const handleCloseModal = () => {
    setShowModal(false);
    setSelectedInventory(null);
  };

  // 조정 완료 후 재고 다시 조회
  const handleAdjustmentSuccess = () => {
    setToast({ type: 'success', text: '재고가 수정되었습니다.' });
    handleCloseModal();
    fetchInventories();
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

  if (loading) {
    return <div className="admin-dashboard loading">로딩 중...</div>;
  }

  return (
    <div className="admin-dashboard">
      <div className="dashboard-header">
        <h1>재고 관리</h1>
        <button
          className="btn-refresh"
          onClick={fetchInventories}
          disabled={loading}
        >
          새로고침
        </button>
      </div>

      {inventories.length === 0 ? (
        <div className="empty-state">
          <p>등록된 재고가 없습니다.</p>
        </div>
      ) : (
        <div className="inventory-table-wrapper">
          <table className="inventory-table">
            <thead>
              <tr>
                <th>배송담당자명</th>
                <th>상품명</th>
                <th>현재 수량</th>
                <th>할당 수량</th>
                <th>마지막 수정</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {inventories.map((item) => (
                <tr key={item.inventory_id}>
                  <td>{item.partner_name}</td>
                  <td>{item.product_name}</td>
                  <td className="quantity">{item.current_quantity}</td>
                  <td className="allocated">{item.allocated_quantity}</td>
                  <td>{formatDate(item.last_adjusted_at)}</td>
                  <td className="actions">
                    <button
                      className="btn-adjust"
                      onClick={() => {
                        setSelectedInventory(item);
                        setShowModal(true);
                      }}
                    >
                      수정
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && selectedInventory && (
        <InventoryAdjustmentModal
          inventory={selectedInventory}
          token={authToken}
          onClose={handleCloseModal}
          onSuccess={handleAdjustmentSuccess}
          onError={(error) => setToast({ type: 'error', text: error })}
        />
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

export default InventoryManagementPage;
