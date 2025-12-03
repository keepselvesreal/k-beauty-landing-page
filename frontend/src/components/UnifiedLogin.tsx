import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../utils/api';
import './UnifiedLogin.css';

interface UnifiedLoginProps {
  onLoginSuccess: () => void;
}

interface TestAccount {
  email: string;
  password: string;
  role: string;
  name: string;
}

const UnifiedLogin: React.FC<UnifiedLoginProps> = ({ onLoginSuccess }) => {
  const { t, i18n } = useTranslation();
  const [role, setRole] = useState('fulfillment-partner');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testAccounts, setTestAccounts] = useState<TestAccount[]>([]);
  const [loadingTestAccounts, setLoadingTestAccounts] = useState(true);

  // 테스트 계정 로드
  useEffect(() => {
    const fetchTestAccounts = async () => {
      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/auth/test-accounts`);
        if (response.ok) {
          const accounts = await response.json();
          setTestAccounts(accounts);
        }
      } catch (err) {
        console.error('Failed to load test accounts:', err);
      } finally {
        setLoadingTestAccounts(false);
      }
    };

    fetchTestAccounts();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      await api.loginFulfillmentPartner(email, password, role);
      onLoginSuccess();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleTestAccountClick = (account: TestAccount, password: string) => {
    setEmail(account.email);
    setPassword(password);
    setRole(account.role);
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'tl' : 'en';
    i18n.changeLanguage(newLang);
    localStorage.setItem('language', newLang);
  };

  const getRoleLabel = (roleValue: string) => {
    switch (roleValue) {
      case 'fulfillment-partner':
        return t('fulfillmentPartner');
      case 'influencer':
        return t('influencer');
      case 'admin':
        return t('admin');
      default:
        return roleValue;
    }
  };

  return (
    <div className="login-container">
      <div className="login-box">
        <div className="login-header">
          <div>
            <h1>{t('fulfillmentPartnerLogin')}</h1>
            <p className="subtitle">{t('accessDashboard')}</p>
          </div>
          <button className="language-toggle" onClick={toggleLanguage}>
            {i18n.language === 'en' ? '🇵🇭 Tagalog' : '🇬🇧 English'}
          </button>
        </div>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="role">{t('selectRole')}</label>
            <select
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              disabled={loading}
            >
              <option value="fulfillment-partner">{t('fulfillmentPartner')}</option>
              <option value="influencer">{t('influencer')}</option>
              <option value="admin">{t('admin')}</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="email">{t('email')}</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder={t('enterEmail')}
              required
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">{t('password')}</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={t('enterPassword')}
              required
              disabled={loading}
            />
          </div>

          <button type="submit" disabled={loading} className="login-btn">
            {loading ? t('loggingIn') : t('login')}
          </button>
        </form>

        {/* 테스트 계정 */}
        <div className="demo-info">
          <h3>{t('testAccount')}</h3>
          {loadingTestAccounts ? (
            <p className="loading-text">로딩 중...</p>
          ) : testAccounts.length > 0 ? (
            <div className="test-accounts-table">
              <table>
                <thead>
                  <tr>
                    <th>{t('email')}</th>
                    <th>{t('selectRole')}</th>
                    <th>이름</th>
                    <th>액션</th>
                  </tr>
                </thead>
                <tbody>
                  {testAccounts.map((account, index) => (
                    <tr key={index}>
                      <td className="email-cell">{account.email}</td>
                      <td>{getRoleLabel(account.role)}</td>
                      <td>{account.name}</td>
                      <td>
                        <button
                          type="button"
                          className="use-btn"
                          onClick={() => {
                            handleTestAccountClick(account, account.password);
                          }}
                        >
                          사용
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="no-accounts-text">등록된 테스트 계정이 없습니다.</p>
          )}
        </div>

        <div className="back-link">
          <a href="/">{t('backToHome')}</a>
        </div>
      </div>
    </div>
  );
};

export default UnifiedLogin;
