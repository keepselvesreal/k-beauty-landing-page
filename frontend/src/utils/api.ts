import { FulfillmentPartnerOrdersResponse, ShipmentRequest, ShipmentResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface CurrentUser {
  user_id: string;
  email: string;
  role: string;
}

export const api = {
  // 배송담당자 로그인 (토큰을 메모리에만 저장, 실제로는 HttpOnly 쿠키로 반환됨)
  async loginFulfillmentPartner(email: string, password: string, role: string = 'fulfillment-partner') {
    const response = await fetch(`${API_BASE_URL}/api/auth/fulfillment-partner/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include', // 쿠키 자동 포함
      body: JSON.stringify({ email, password, role }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail?.message || 'Login failed');
    }

    const data = await response.json();
    // 토큰을 메모리에만 저장 (본 프로젝트에서 사용하지 않음)
    // 실제 HttpOnly 쿠키는 백엔드가 관리함
    sessionStorage.setItem('token', data.access_token);
    return data;
  },

  // 현재 사용자 정보 조회
  async getCurrentUser(): Promise<CurrentUser> {
    const token = sessionStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/api/auth/fulfillment-partner/me`, {
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

  // 로그아웃
  logout() {
    sessionStorage.removeItem('token');
  },

  // 토큰 확인
  isLoggedIn(): boolean {
    return !!sessionStorage.getItem('token');
  },
};
