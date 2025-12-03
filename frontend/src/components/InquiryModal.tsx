import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import './InquiryModal.css';

interface InquiryModalProps {
  isOpen: boolean;
  onClose: () => void;
  inquiryType: 'influencer' | 'fulfillment_partner' | 'customer';
  prefilledEmail?: string;
}

const InquiryModal: React.FC<InquiryModalProps> = ({
  isOpen,
  onClose,
  inquiryType,
  prefilledEmail,
}) => {
  const [message, setMessage] = useState('');
  const [replyToEmail, setReplyToEmail] = useState(prefilledEmail || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // 타입 변경 시 이메일 초기화
  useEffect(() => {
    setReplyToEmail(prefilledEmail || '');
    setError(null);
  }, [prefilledEmail, inquiryType]);

  const getModalTitle = () => {
    switch (inquiryType) {
      case 'influencer':
        return '관리자에게 문의';
      case 'fulfillment_partner':
        return '관리자에게 문의';
      case 'customer':
        return '문의하기';
      default:
        return '문의';
    }
  };

  const getEmailLabel = () => {
    switch (inquiryType) {
      case 'influencer':
        return '회신받을 이메일 (자동 채워짐)';
      case 'fulfillment_partner':
        return '회신받을 이메일 (자동 채워짐)';
      case 'customer':
        return '회신받을 이메일';
      default:
        return '이메일';
    }
  };

  const isEmailAutoFilled =
    inquiryType === 'influencer' || inquiryType === 'fulfillment_partner';

  const handleClearEmail = () => {
    setReplyToEmail('');
  };

  const handleSubmit = async () => {
    if (!message.trim()) {
      setError('메시지를 입력해주세요');
      return;
    }

    if (!replyToEmail.trim()) {
      setError('회신받을 이메일을 입력해주세요');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      await api.createInquiry({
        inquiry_type: inquiryType,
        message: message.trim(),
        reply_to_email: replyToEmail.trim(),
      });

      setSuccess(true);
      setMessage('');
      setReplyToEmail(prefilledEmail || '');

      // 2초 후 자동으로 모달 닫기
      setTimeout(() => {
        setSuccess(false);
        onClose();
      }, 2000);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send inquiry';
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="inquiry-modal-overlay" onClick={onClose}>
      <div className="inquiry-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="inquiry-modal-header">
          <h3>{getModalTitle()}</h3>
          <button
            className="inquiry-modal-close"
            onClick={onClose}
            disabled={isSubmitting}
          >
            ✕
          </button>
        </div>

        <div className="inquiry-modal-body">
          {/* 이메일 필드 */}
          <div className="form-group">
            <label>{getEmailLabel()}</label>
            <div className="email-input-wrapper">
              <input
                type="email"
                value={replyToEmail}
                onChange={(e) => setReplyToEmail(e.target.value)}
                placeholder="example@email.com"
                disabled={isEmailAutoFilled || isSubmitting}
                className={isEmailAutoFilled ? 'auto-filled' : ''}
              />
              {replyToEmail && (
                <button
                  className="email-clear-btn"
                  onClick={handleClearEmail}
                  disabled={isSubmitting}
                  title="일괄 삭제"
                >
                  ✕
                </button>
              )}
            </div>
          </div>

          {/* 메시지 필드 */}
          <div className="form-group">
            <label>문의 내용</label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="문의 내용을 입력해주세요..."
              disabled={isSubmitting}
              rows={6}
            />
          </div>

          {/* 에러 메시지 */}
          {error && <div className="inquiry-error">{error}</div>}

          {/* 성공 메시지 */}
          {success && (
            <div className="inquiry-success">
              ✓ 문의가 저장되었습니다. 감사합니다!
            </div>
          )}
        </div>

        <div className="inquiry-modal-footer">
          <button
            className="btn-cancel"
            onClick={onClose}
            disabled={isSubmitting}
          >
            취소
          </button>
          <button
            className="btn-submit"
            onClick={handleSubmit}
            disabled={!message.trim() || !replyToEmail.trim() || isSubmitting}
          >
            {isSubmitting ? '발송 중...' : '발송'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default InquiryModal;
