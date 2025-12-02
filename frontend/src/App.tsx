import React, { useMemo } from 'react';
import Header from './components/Header';
import ProductHero from './components/ProductHero';
import Testimonials from './components/Testimonials';
import OrderForm from './components/OrderForm';
import OrderConfirmation from './components/OrderConfirmation';
import AdminPanel from './components/AdminPanel';

const App: React.FC = () => {
  // URL 경로 확인
  const currentPath = useMemo(() => {
    return window.location.pathname;
  }, []);

  // 주문 번호 추출 (예: /order-confirmation/ORD-xxx)
  const isOrderConfirmationPage = currentPath.startsWith('/order-confirmation/');
  const isAdminPage = currentPath === '/admin';
  const orderNumber = isOrderConfirmationPage
    ? currentPath.split('/order-confirmation/')[1]
    : null;

  return (
    <div className="min-h-screen bg-white">
      {!isAdminPage && <Header />}
      <main>
        {isAdminPage ? (
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

      {/* Footer / Copyright */}
      <footer className="py-8 text-center text-gray-400 text-sm border-t border-gray-100 mt-12">
        <p>&copy; {new Date().getFullYear()} Santa Here. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default App;
