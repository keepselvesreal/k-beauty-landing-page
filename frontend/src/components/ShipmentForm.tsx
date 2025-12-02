import React, { useState } from 'react';
import { FulfillmentPartnerOrder, ShipmentRequest } from '../types';
import { api } from '../utils/api';
import './ShipmentForm.css';

interface ShipmentFormProps {
  order: FulfillmentPartnerOrder;
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  onError: (message: string) => void;
}

const CARRIERS = ['CJ', 'DHL', 'Grab Express', 'Lalamove', 'LBC', '2GO'];

const ShipmentForm: React.FC<ShipmentFormProps> = ({
  order,
  isOpen,
  onClose,
  onSuccess,
  onError,
}) => {
  const [carrier, setCarrier] = useState<string>('');
  const [trackingNumber, setTrackingNumber] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [emailStatus, setEmailStatus] = useState<'pending' | 'sent' | 'failed'>('pending');

  const isFormValid = carrier.trim() !== '' && trackingNumber.trim() !== '';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isFormValid) return;

    try {
      setLoading(true);
      setEmailStatus('pending');

      const shipmentData: ShipmentRequest = {
        carrier: carrier.trim(),
        tracking_number: trackingNumber.trim(),
      };

      const result = await api.processShipment(order.order_id, shipmentData);

      // 이메일 상태 설정
      setEmailStatus(result.email_status === 'sent' ? 'sent' : 'failed');

      // 성공 콜백
      onSuccess();

      // 폼 초기화 및 모달 닫기
      setCarrier('');
      setTrackingNumber('');
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to process shipment';
      onError(message);
      setEmailStatus('failed');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>배송 정보 입력</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        <div className="modal-body">
          <div className="order-summary">
            <div className="summary-item">
              <span className="label">주문번호:</span>
              <span className="value">{order.order_number}</span>
            </div>
            <div className="summary-item">
              <span className="label">고객:</span>
              <span className="value">{order.customer_email}</span>
            </div>
            <div className="summary-item">
              <span className="label">배송주소:</span>
              <span className="value">{order.shipping_address}</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="shipment-form">
            <div className="form-group">
              <label htmlFor="carrier">택배사</label>
              <select
                id="carrier"
                value={carrier}
                onChange={(e) => setCarrier(e.target.value)}
                disabled={loading}
                className="form-control"
              >
                <option value="">택배사를 선택해주세요</option>
                {CARRIERS.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="tracking_number">운송장 번호</label>
              <input
                id="tracking_number"
                type="text"
                value={trackingNumber}
                onChange={(e) => setTrackingNumber(e.target.value)}
                placeholder="운송장 번호를 입력해주세요"
                disabled={loading}
                className="form-control"
              />
            </div>

            <div className="email-status">
              <span className="label">이메일 알림:</span>
              {emailStatus === 'pending' && (
                <span className="status-badge pending">대기 중</span>
              )}
              {emailStatus === 'sent' && (
                <span className="status-badge sent">✓ 발송됨</span>
              )}
              {emailStatus === 'failed' && (
                <span className="status-badge failed">✗ 발송 실패</span>
              )}
            </div>

            <div className="form-actions">
              <button
                type="button"
                onClick={onClose}
                className="btn btn-secondary"
                disabled={loading}
              >
                취소
              </button>
              <button
                type="submit"
                className="btn btn-primary"
                disabled={loading || !isFormValid}
              >
                {loading ? '처리 중...' : '발송 완료'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ShipmentForm;
