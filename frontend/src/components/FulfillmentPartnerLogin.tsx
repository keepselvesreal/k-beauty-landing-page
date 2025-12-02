import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { api } from '../utils/api';
import './FulfillmentPartnerLogin.css';

interface FulfillmentPartnerLoginProps {
  onLoginSuccess: () => void;
}

const FulfillmentPartnerLogin: React.FC<FulfillmentPartnerLoginProps> = ({ onLoginSuccess }) => {
  const { t, i18n } = useTranslation();
  const [role, setRole] = useState('fulfillment-partner');
  const [email, setEmail] = useState('ncr.partner@example.com');
  const [password, setPassword] = useState('password123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      await api.loginFulfillmentPartner(email, password);
      onLoginSuccess();
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const toggleLanguage = () => {
    const newLang = i18n.language === 'en' ? 'tl' : 'en';
    i18n.changeLanguage(newLang);
    localStorage.setItem('language', newLang);
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

        <div className="demo-info">
          <h3>{t('testAccount')}</h3>
          <p><strong>{t('email')}:</strong> ncr.partner@example.com</p>
          <p><strong>{t('password')}:</strong> password123</p>
        </div>

        <div className="back-link">
          <a href="/">{t('backToHome')}</a>
        </div>
      </div>
    </div>
  );
};

export default FulfillmentPartnerLogin;
