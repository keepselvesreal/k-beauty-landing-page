export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  images: string[];
}

export interface Review {
  id: string;
  name: string;
  avatar: string;
  rating: number;
  text: string;
}

export interface OrderFormState {
  fullName: string;
  email: string;
  phone: string;
  region: string;
  address: string;
  detailedAddress: string;
}

export interface FormErrors {
  phone?: string;
  email?: string;
}
