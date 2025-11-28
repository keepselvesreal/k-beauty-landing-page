import React, { useState } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { PRODUCT } from '../constants';

const ProductHero: React.FC = () => {
  const [currentImageIdx, setCurrentImageIdx] = useState(0);

  const nextImage = () => {
    setCurrentImageIdx((prev) => (prev + 1) % PRODUCT.images.length);
  };

  const prevImage = () => {
    setCurrentImageIdx((prev) => (prev === 0 ? PRODUCT.images.length - 1 : prev - 1));
  };

  return (
    <section className="max-w-6xl mx-auto px-4 py-12 md:py-16">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
        {/* Left: Image Carousel */}
        <div className="relative group">
          <div className="aspect-square bg-[#F9F5F2] rounded-3xl overflow-hidden flex items-center justify-center relative">
            <img
              src={PRODUCT.images[currentImageIdx]}
              alt={PRODUCT.name}
              className="w-full h-full object-cover transition-transform duration-500 hover:scale-105"
            />

            {/* Carousel Controls */}
            <button
              onClick={prevImage}
              className="absolute left-4 bg-white/80 hover:bg-white p-2 rounded-full shadow-sm text-gray-600 transition-all opacity-0 group-hover:opacity-100"
            >
              <ChevronLeft size={24} />
            </button>
            <button
              onClick={nextImage}
              className="absolute right-4 bg-white/80 hover:bg-white p-2 rounded-full shadow-sm text-gray-600 transition-all opacity-0 group-hover:opacity-100"
            >
              <ChevronRight size={24} />
            </button>
          </div>

          {/* Dots */}
          <div className="flex justify-center mt-6 space-x-2">
            {PRODUCT.images.map((_, idx) => (
              <button
                key={idx}
                onClick={() => setCurrentImageIdx(idx)}
                className={`w-2.5 h-2.5 rounded-full transition-colors ${
                  idx === currentImageIdx ? 'bg-[#C49A9A]' : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Right: Product Details */}
        <div className="space-y-6">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 leading-tight">
            {PRODUCT.name}
          </h1>
          <p className="text-gray-600 leading-relaxed text-lg">{PRODUCT.description}</p>
          <div className="text-4xl font-bold text-[#C49A9A]">
            {PRODUCT.currency}
            {PRODUCT.price}
          </div>
        </div>
      </div>
    </section>
  );
};

export default ProductHero;
