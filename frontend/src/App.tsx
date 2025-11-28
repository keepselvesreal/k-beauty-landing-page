import React from 'react';
import Header from './components/Header';
import ProductHero from './components/ProductHero';
import Testimonials from './components/Testimonials';
import OrderForm from './components/OrderForm';

const App: React.FC = () => {
  return (
    <div className="min-h-screen bg-white">
      <Header />
      <main>
        <ProductHero />
        <Testimonials />
        <OrderForm />
      </main>

      {/* Footer / Copyright */}
      <footer className="py-8 text-center text-gray-400 text-sm border-t border-gray-100 mt-12">
        <p>&copy; {new Date().getFullYear()} Santa Here. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default App;
