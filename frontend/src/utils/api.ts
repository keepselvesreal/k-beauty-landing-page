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

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  message: string;
}

export interface InquiryRequest {
  inquiry_type: string;
  message: string;
  reply_to_email?: string;
}

export interface InquiryResponse {
  status: string;
  message: string;
  inquiry_id?: string;
}

export interface InquiryDetail {
  id: string;
  inquiry_type: string;
  sender_id?: string;
  reply_to_email: string;
  message: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface InquiriesListResponse {
  total: number;
  page: number;
  page_size: number;
  inquiries: InquiryDetail[];
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

  // 문의 생성 (모든 사용자 - 토큰 선택사항)
  async createInquiry(request: InquiryRequest): Promise<InquiryResponse> {
    const token = sessionStorage.getItem('token');

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // 토큰이 있으면 헤더에 추가 (없어도 괜찮음)
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}/api/inquiries`, {
      method: 'POST',
      headers,
      credentials: 'include',
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      if (response.status === 401) {
        sessionStorage.removeItem('token');
        throw new Error('Unauthorized - please log in again');
      }
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to create inquiry');
    }

    return await response.json();
  },

  // 관리자용 문의 목록 조회
  async getInquiries(
    page: number = 1,
    pageSize: number = 20,
    inquiryType?: string,
    status?: string
  ): Promise<InquiriesListResponse> {
    const token = sessionStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    if (inquiryType) params.append('inquiry_type', inquiryType);
    if (status) params.append('status_filter', status);

    const response = await fetch(`${API_BASE_URL}/api/inquiries/admin/list?${params}`, {
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
      throw new Error(error.detail?.message || 'Failed to fetch inquiries');
    }

    return await response.json();
  },

  // 문의 상태 변경 (관리자)
  async updateInquiryStatus(inquiryId: string, status: string): Promise<InquiryDetail> {
    const token = sessionStorage.getItem('token');
    if (!token) {
      throw new Error('No authentication token found');
    }

    const response = await fetch(`${API_BASE_URL}/api/inquiries/admin/${inquiryId}/status`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ status }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        sessionStorage.removeItem('token');
        throw new Error('Unauthorized - please log in again');
      }
      const error = await response.json();
      throw new Error(error.detail?.message || 'Failed to update inquiry status');
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
