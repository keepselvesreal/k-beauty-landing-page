import { Product, Review } from './types';

// API 설정
export const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const PRODUCT: Product = {
  id: 'rice-sunscreen-50ml',
  name: 'Santa Here Rice Sunscreen 50ml',
  description:
    'A moisturizing chemical sunscreen that is comfortable on the skin with SPF 50+ PA++++. Enriched with 30% Rice Extract and Grain Fermented Extracts that deeply hydrate and nourish the skin, making it perfect for sensitive skin.',
  price: 750,
  currency: '₱',
  images: [
    'https://images.unsplash.com/photo-1620916566398-39f1143ab7be?q=80&w=1887&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1556228720-1987df367681?q=80&w=1887&auto=format&fit=crop',
    'https://images.unsplash.com/photo-1611930022073-b7a4ba5fcccd?q=80&w=1887&auto=format&fit=crop',
  ],
};

export const REVIEWS: Review[] = [
  {
    id: '1',
    name: 'Maria Dela Cruz',
    avatar: 'https://i.pravatar.cc/150?img=1',
    rating: 5,
    text: 'No white cast and feels so light on my skin! My new holy grail sunscreen. Highly recommended!',
  },
  {
    id: '2',
    name: 'Sofia Reyes',
    avatar: 'https://i.pravatar.cc/150?img=5',
    rating: 5,
    text: "I have sensitive skin and this doesn't break me out at all. It's so hydrating and sits well under makeup.",
  },
  {
    id: '3',
    name: 'Isabella Santos',
    avatar: 'https://i.pravatar.cc/150?img=9',
    rating: 4,
    text: 'Love this sunscreen! Very moisturizing. Shipping was fast and it came in a bigger box.',
  },
];

// 지역별 배송료 (구조화된 형태)
export const REGIONS = [
  { id: 'NCR', label: 'NCR', rate: 100 },
  { id: 'Luzon', label: 'Luzon', rate: 120 },
  { id: 'Visayas', label: 'Visayas', rate: 140 },
  { id: 'Mindanao', label: 'Mindanao', rate: 160 },
];
