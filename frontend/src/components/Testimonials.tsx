import React from 'react';
import { Star } from 'lucide-react';
import { REVIEWS } from '../constants';

const Testimonials: React.FC = () => {
  return (
    <section className="bg-[#F9F5F2] py-20">
      <div className="max-w-6xl mx-auto px-4">
        <h2 className="text-2xl md:text-3xl font-bold text-center text-gray-900 mb-12">
          What Our Customers Are Saying
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {REVIEWS.map((review) => (
            <div
              key={review.id}
              className="bg-white p-8 rounded-2xl shadow-sm hover:shadow-md transition-shadow flex flex-col items-center text-center"
            >
              <div className="w-20 h-20 rounded-full overflow-hidden mb-4 border-2 border-[#F9F5F2]">
                <img src={review.avatar} alt={review.name} className="w-full h-full object-cover" />
              </div>
              <h3 className="font-bold text-gray-900 text-lg mb-2">{review.name}</h3>
              <div className="flex space-x-1 mb-4 text-[#C49A9A]">
                {[...Array(5)].map((_, i) => (
                  <Star
                    key={i}
                    size={16}
                    fill={i < review.rating ? 'currentColor' : 'none'}
                    className={i < review.rating ? 'text-[#C49A9A]' : 'text-gray-300'}
                  />
                ))}
              </div>
              <p className="text-gray-500 text-sm leading-relaxed">{review.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Testimonials;
