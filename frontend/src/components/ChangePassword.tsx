import React, { useState } from 'react';
import { api } from '../utils/api';
import Toast from './Toast';
import './ChangePassword.css';

const ChangePassword: React.FC = () => {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // 유효성 검사
    if (!currentPassword.trim()) {
      setToast({ type: 'error', message: '현재 비밀번호를 입력해주세요' });
      return;
    }

    if (!newPassword.trim()) {
      setToast({ type: 'error', message: '새 비밀번호를 입력해주세요' });
      return;
    }

    if (newPassword.length < 6) {
      setToast({ type: 'error', message: '새 비밀번호는 6자 이상이어야 합니다' });
      return;
    }

    if (newPassword !== confirmPassword) {
      setToast({ type: 'error', message: '새 비밀번호가 일치하지 않습니다' });
      return;
    }

    if (currentPassword === newPassword) {
      setToast({ type: 'error', message: '새 비밀번호는 현재 비밀번호와 달라야 합니다' });
      return;
    }

    try {
      setLoading(true);
      await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });

      setToast({ type: 'success', message: '비밀번호가 성공적으로 변경되었습니다' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to change password';
      setToast({ type: 'error', message });
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    window.history.back();
  };

  return (
    <div className="change-password">
      <header className="password-header">
        <div className="header-left">
          <h1>비밀번호 변경</h1>
        </div>
        <div className="header-buttons">
          <button className="back-btn" onClick={handleBack}>
            뒤로가기
          </button>
        </div>
      </header>

      <div className="password-content">
        <div className="password-card">
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="currentPassword">현재 비밀번호</label>
              <input
                id="currentPassword"
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="현재 비밀번호를 입력하세요"
                disabled={loading}
              />
            </div>

            <div className="form-group">
              <label htmlFor="newPassword">새 비밀번호</label>
              <input
                id="newPassword"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="새 비밀번호를 입력하세요"
                disabled={loading}
              />
              <small>6자 이상의 비밀번호를 설정해주세요</small>
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">새 비밀번호 확인</label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="새 비밀번호를 다시 입력하세요"
                disabled={loading}
              />
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="btn-submit"
                disabled={loading || !currentPassword || !newPassword || !confirmPassword}
              >
                {loading ? '변경 중...' : '비밀번호 변경'}
              </button>
            </div>
          </form>
        </div>

        <div className="password-info">
          <h3>보안 안내</h3>
          <ul>
            <li>비밀번호는 6자 이상이어야 합니다</li>
            <li>정기적으로 비밀번호를 변경해주세요</li>
            <li>개인정보 보호를 위해 타인과 공유하지 마세요</li>
          </ul>
        </div>
      </div>

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

export default ChangePassword;
