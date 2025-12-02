import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';

interface RequestModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (reason: string) => Promise<void>;
  type: 'cancel' | 'refund';
  isLoading?: boolean;
}

const RequestModal: React.FC<RequestModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  type,
  isLoading = false,
}) => {
  const { t } = useTranslation();
  const [reason, setReason] = useState('');
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) {
    return null;
  }

  const handleSubmit = async () => {
    if (!reason.trim()) {
      setError('Please enter a reason');
      return;
    }

    try {
      setError(null);
      await onSubmit(reason);
      setReason('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const handleClose = () => {
    setReason('');
    setError(null);
    onClose();
  };

  const getTitle = () => {
    return type === 'cancel'
      ? t('cancelRequest')
      : t('refundRequest');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-lg max-w-md w-full mx-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
          <h2 className="text-lg font-bold text-gray-900">{getTitle()}</h2>
          <button
            onClick={handleClose}
            disabled={isLoading}
            className="text-gray-500 hover:text-gray-700 transition-colors disabled:opacity-50"
          >
            <X size={20} />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-6">
          <div className="space-y-4">
            {/* Request Reason Label */}
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-2">
                {t('requestReason')}
              </label>

              {/* Textarea */}
              <textarea
                value={reason}
                onChange={(e) => {
                  setReason(e.target.value);
                  setError(null);
                }}
                placeholder={t('enterReason')}
                disabled={isLoading}
                rows={5}
                className={`
                  w-full px-4 py-3 border rounded-md focus:outline-none focus:ring-1 resize-none transition-all
                  ${
                    error
                      ? 'border-red-400 bg-red-50 focus:border-red-500 focus:ring-red-500'
                      : 'border-gray-200 focus:border-[#C49A9A] focus:ring-[#C49A9A]'
                  }
                  ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              />

              {/* Error Message */}
              {error && (
                <p className="text-xs text-red-600 mt-2 flex items-center gap-1">
                  <span>⚠️</span>
                  {error}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 px-6 py-4 flex gap-3">
          <button
            onClick={handleClose}
            disabled={isLoading}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            Cancel
          </button>

          <button
            onClick={handleSubmit}
            disabled={isLoading || !reason.trim()}
            className={`
              flex-1 px-4 py-2 rounded-md font-medium transition-colors
              ${
                isLoading || !reason.trim()
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-[#C49A9A] text-white hover:bg-[#b08585]'
              }
            `}
          >
            {isLoading ? '...' : t('submitRequest')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default RequestModal;
