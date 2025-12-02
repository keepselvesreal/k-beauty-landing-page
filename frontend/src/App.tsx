import React, { useMemo, useState, useEffect } from 'react';
import Header from './components/Header';
import ProductHero from './components/ProductHero';
import Testimonials from './components/Testimonials';
import OrderForm from './components/OrderForm';
import OrderConfirmation from './components/OrderConfirmation';
import AdminPanel from './components/AdminPanel';
import FulfillmentPartnerLogin from './components/FulfillmentPartnerLogin';
import FulfillmentPartnerDashboard from './components/FulfillmentPartnerDashboard';
import InfluencerDashboard from './components/InfluencerDashboard';
import ChangePassword from './components/ChangePassword';
import { api, CurrentUser } from './utils/api';

const App: React.FC = () => {
  const [isLoggedIn, setIsLoggedIn] = useState(api.isLoggedIn());
  const [currentUser, setCurrentUser] = useState<CurrentUser | null>(null);
  const [userLoading, setUserLoading] = useState(false);

  // URL 경로 확인
  const currentPath = window.location.pathname;

  // 주문 번호 추출 (예: /order-confirmation/ORD-xxx)
  const isOrderConfirmationPage = currentPath.startsWith('/order-confirmation/');
  const isAdminPage = currentPath === '/admin';
  const isLoginPage = currentPath === '/auth/login';
  const isDashboardPage = currentPath === '/dashboard';
  const isSettingsPage = currentPath === '/settings';

  const orderNumber = isOrderConfirmationPage
    ? currentPath.split('/order-confirmation/')[1]
    : null;

  // 로그인 상태 변경 시 사용자 정보 조회
  useEffect(() => {
    if (isLoggedIn && !currentUser) {
      const fetchUser = async () => {
        try {
          setUserLoading(true);
          const user = await api.getCurrentUser();
          setCurrentUser(user);
        } catch (err) {
          // 토큰이 만료되었거나 유효하지 않으면 로그아웃
          setIsLoggedIn(false);
          setCurrentUser(null);
          api.logout();
        } finally {
          setUserLoading(false);
        }
      };
      fetchUser();
    }
  }, [isLoggedIn, currentUser]);

  const handleLoginSuccess = () => {
    setIsLoggedIn(true);
    window.location.href = '/dashboard';
  };

  return (
    <div className="min-h-screen bg-white">
      {!isAdminPage && !isLoginPage && !isDashboardPage && !isSettingsPage && <Header />}
      <main>
        {isLoginPage ? (
          <FulfillmentPartnerLogin onLoginSuccess={handleLoginSuccess} />
        ) : isSettingsPage && isLoggedIn ? (
          userLoading ? (
            <div className="flex items-center justify-center h-screen">
              <div className="text-lg">로드 중...</div>
            </div>
          ) : (
            <ChangePassword />
          )
        ) : isDashboardPage && isLoggedIn ? (
          userLoading ? (
            <div className="flex items-center justify-center h-screen">
              <div className="text-lg">로드 중...</div>
            </div>
          ) : currentUser ? (
            currentUser.role === 'fulfillment-partner' ? (
              <FulfillmentPartnerDashboard />
            ) : currentUser.role === 'influencer' ? (
              <InfluencerDashboard />
            ) : (
              <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                  <h1 className="text-3xl font-bold mb-4">어드민 대시보드</h1>
                  <p className="text-gray-600">어드민 대시보드 개발 중입니다.</p>
                </div>
              </div>
            )
          ) : (
            <div className="flex items-center justify-center h-screen">
              <div className="text-lg text-red-600">사용자 정보를 불러올 수 없습니다.</div>
            </div>
          )
        ) : isAdminPage ? (
          <AdminPanel />
        ) : isOrderConfirmationPage && orderNumber ? (
          <OrderConfirmation orderNumber={orderNumber} />
        ) : (
          <>
            <ProductHero />
            <Testimonials />
            <OrderForm />
          </>
        )}
      </main>

      {!isAdminPage && !isLoginPage && !isDashboardPage && !isSettingsPage && (
        <footer className="py-8 text-center text-gray-400 text-sm border-t border-gray-100 mt-12">
          <p>&copy; {new Date().getFullYear()} Santa Here. All rights reserved.</p>
        </footer>
      )}
    </div>
  );
};

export default App;
