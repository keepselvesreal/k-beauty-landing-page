import { FulfillmentPartnerOrdersResponse, ShipmentRequest, ShipmentResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface CurrentUser {
  user_id: string;
  email: string;
  role: string;
}

export interface InfluencerDashboard {
  affiliate_code: string;
  affiliate_url: string;
  total_clicks: number;
  total_sales: number;
  cumulative_revenue: number;
  pending_commission: number;
  next_payment_date: string;
}

export interface InfluencerInquiryRequest {
  message: string;
}

export interface InfluencerInquiryResponse {
  status: string;
  message: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  message: string;
}

export const api = {
  // 통합 로그인 (모든 역할)
  async loginFulfillmentPartner(email: string, password: string, role: string = 'fulfillment-partner') {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email, password, role }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Login failed');
    }

    const data = await response.json();
    sessionStorage.setItem('token', data.access_token);
    return data;
  },

  // 통합 사용자 정보 조회 (모든 역할)
  async getCurrentUser(): Promise<CurrentUser> {
    const token = sessionStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });

    if (!response.ok) {
      if (response.status === 401) {
        sessionStorage.removeItem('token');
        throw new Error('Unauthorized - please log in again');
      }
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to fetch user info');
    }

    return await response.json();
  },

  // 배송담당자 주문 목록 조회
  async getFulfillmentPartnerOrders(): Promise<FulfillmentPartnerOrdersResponse> {
    const token = sessionStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/api/fulfillment-partner/orders`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });

    if (!response.ok) {
      if (response.status === 401) {
        sessionStorage.removeItem('token');
        throw new Error('Unauthorized - please log in again');
      }
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to fetch orders');
    }

    return await response.json();
  },

  // 배송 정보 입력 (배송담당자)
  async processShipment(orderId: string, shipmentData: ShipmentRequest): Promise<ShipmentResponse> {
    const token = sessionStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/api/fulfillment-partner/orders/${orderId}/ship`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(shipmentData),
    });

    if (!response.ok) {
      if (response.status === 401) {
        sessionStorage.removeItem('token');
        throw new Error('Unauthorized - please log in again');
      }
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to process shipment');
    }

    return await response.json();
  },

  // 인플루언서 대시보드 조회
  async getInfluencerDashboard(): Promise<InfluencerDashboard> {
    const token = sessionStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/api/influencer/dashboard`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });

    if (!response.ok) {
      if (response.status === 401) {
        sessionStorage.removeItem('token');
        throw new Error('Unauthorized - please log in again');
      }
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to fetch dashboard');
    }

    return await response.json();
  },

  // 인플루언서 문의 발송
  async sendInfluencerInquiry(message: string): Promise<InfluencerInquiryResponse> {
    const token = sessionStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/api/influencer/inquiry`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ message }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        sessionStorage.removeItem('token');
        throw new Error('Unauthorized - please log in again');
      }
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to send inquiry');
    }

    return await response.json();
  },

  // 통합 비밀번호 변경 (모든 역할 지원)
  async changePassword(request: ChangePasswordRequest): Promise<ChangePasswordResponse> {
    const token = sessionStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/change-password`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      if (response.status === 401) {
        sessionStorage.removeItem('token');
        throw new Error('Unauthorized - please log in again');
      }
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to change password');
    }

    return await response.json();
  },

  // 로그아웃
  logout() {
    sessionStorage.removeItem('token');
  },

  // 토큰 확인
  isLoggedIn(): boolean {
    return !!sessionStorage.getItem('token');
  },
};
