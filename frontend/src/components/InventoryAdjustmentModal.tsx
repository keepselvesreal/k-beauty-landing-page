import React, { useState, useEffect } from 'react';
import './InventoryAdjustmentModal.css';

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

interface HistoryItem {
  log_id: string;
  old_quantity: number;
  new_quantity: number;
  reason: string | null;
  adjusted_at: string;
}

interface InventoryHistoryResponse {
  inventory_id: string;
  partner_name: string;
  product_name: string;
  history: HistoryItem[];
}

interface InventoryAdjustmentModalProps {
  inventory: InventoryItem;
  token: string;
  onClose: () => void;
  onSuccess: () => void;
  onError: (error: string) => void;
}

const InventoryAdjustmentModal: React.FC<InventoryAdjustmentModalProps> = ({
  inventory,
  token,
  onClose,
  onSuccess,
  onError,
}) => {
  const [newQuantity, setNewQuantity] = useState(inventory.current_quantity.toString());
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

  // 조정 이력 조회
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        setLoadingHistory(true);
        const response = await fetch(
          `${API_BASE_URL}/api/admin/inventory/${inventory.inventory_id}/history?limit=5`,
          {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          }
        );

        if (!response.ok) {
          // 이력이 없을 수도 있으므로, 에러로 처리하지 않음
          console.warn('Failed to fetch history');
          setHistory([]);
          return;
        }

        const data: InventoryHistoryResponse = await response.json();
        setHistory(data.history || []);
      } catch (err) {
        console.error('Error fetching history:', err);
        setHistory([]);
      } finally {
        setLoadingHistory(false);
      }
    };

    fetchHistory();
  }, [inventory.inventory_id, token]);

  // 유효성 검사
  const validateForm = (): boolean => {
    setError('');

    const qty = parseInt(newQuantity, 10);
    if (isNaN(qty)) {
      setError('수량은 숫자여야 합니다.');
      return false;
    }

    if (qty < 0) {
      setError('수량은 음수일 수 없습니다.');
      return false;
    }

    return true;
  };

  // 저장 핸들러
  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSuccess('');
    setError('');

    if (!validateForm()) {
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(
        `${API_BASE_URL}/api/admin/inventory/${inventory.inventory_id}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            new_quantity: parseInt(newQuantity, 10),
            reason: reason || null,
          }),
        }
      );

      if (response.status === 401) {
        onError('인증이 만료되었습니다. 다시 로그인해주세요.');
        return;
      }

      if (response.status === 403) {
        onError('관리자 권한이 필요합니다.');
        return;
      }

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || '재고 수정에 실패했습니다.');
      }

      setSuccess('재고가 성공적으로 수정되었습니다.');
      setTimeout(() => {
        onSuccess();
      }, 1000);
    } catch (err) {
      const message = err instanceof Error ? err.message : '재고 수정 중 오류가 발생했습니다.';
      setError(message);
      onError(message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const quantityChange = parseInt(newQuantity, 10) - inventory.current_quantity;
  const quantityChangeText =
    quantityChange > 0 ? `+${quantityChange}` : `${quantityChange}`;
  const quantityChangeClass =
    quantityChange > 0 ? 'increase' : quantityChange < 0 ? 'decrease' : 'no-change';

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* 헤더 */}
        <div className="modal-header">
          <div>
            <h2>재고 수정</h2>
            <p className="subtitle">
              {inventory.partner_name} - {inventory.product_name}
            </p>
          </div>
          <button className="btn-close" onClick={onClose}>
            ✕
          </button>
        </div>

        {/* 내용 */}
        <div className="modal-body">
          <div className="form-section">
            {/* 현재 수량 */}
            <div className="form-group">
              <label>현재 수량</label>
              <div className="current-quantity">
                <strong>{inventory.current_quantity}</strong>
              </div>
            </div>

            {/* 새 수량 입력 */}
            <div className="form-group">
              <label htmlFor="newQuantity">
                새로운 수량 <span className="required">*</span>
              </label>
              <input
                id="newQuantity"
                type="number"
                min="0"
                value={newQuantity}
                onChange={(e) => {
                  setNewQuantity(e.target.value);
                  setError('');
                }}
                disabled={loading}
                className={error ? 'error' : ''}
              />
            </div>

            {/* 수량 변화 표시 */}
            {!isNaN(parseInt(newQuantity, 10)) && (
              <div className={`quantity-change ${quantityChangeClass}`}>
                {quantityChangeText}
              </div>
            )}

            {/* 조정 사유 */}
            <div className="form-group">
              <label htmlFor="reason">조정 사유 (선택적)</label>
              <textarea
                id="reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                disabled={loading}
                placeholder="조정 사유를 입력해주세요"
                rows={3}
              />
            </div>

            {/* 에러 메시지 */}
            {error && <div className="error-message">{error}</div>}
            {success && <div className="success-message">{success}</div>}
          </div>

          {/* 조정 이력 */}
          <div className="history-section">
            <h3>최근 조정 이력</h3>
            {loadingHistory ? (
              <div className="history-loading">로딩 중...</div>
            ) : history.length === 0 ? (
              <div className="no-history">조정 이력이 없습니다.</div>
            ) : (
              <div className="history-list">
                {history.map((item) => (
                  <div key={item.log_id} className="history-item">
                    <div className="history-date">{formatDate(item.adjusted_at)}</div>
                    <div className="history-change">
                      {item.old_quantity} → {item.new_quantity}
                    </div>
                    {item.reason && (
                      <div className="history-reason">{item.reason}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* 푸터 */}
        <div className="modal-footer">
          <button
            className="btn-cancel"
            onClick={onClose}
            disabled={loading}
          >
            취소
          </button>
          <button
            className="btn-save"
            onClick={handleSave}
            disabled={loading || parseInt(newQuantity, 10) === inventory.current_quantity}
          >
            {loading ? '저장 중...' : '저장'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default InventoryAdjustmentModal;
