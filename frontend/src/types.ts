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

export interface OrderItem {
  id: string;
  product_id: string;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: string;
  order_number: string;
  customer_id: string;
  payment_status: string;
  shipping_status: string;
  cancellation_status?: string;
  refund_status?: string;
  cancellation_reason?: string;
  refund_reason?: string;
  cancellation_requested_at?: string;
  refund_requested_at?: string;
  subtotal: number;
  shipping_fee: number;
  total_price: number;
  created_at: string;
  updated_at: string;
}

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  region: string;
  address: string;
  detailed_address?: string;
}

export interface FulfillmentPartnerOrderProduct {
  name: string;
  quantity: number;
  unit_price: number | string;
}

export interface FulfillmentPartnerOrder {
  order_id: string;
  order_number: string;
  customer_email: string;
  products: FulfillmentPartnerOrderProduct[];
  shipping_address: string;
  total_price: number | string;
  status: string;
  created_at: string;
}

export interface FulfillmentPartnerOrdersResponse {
  partner_id: string;
  partner_name: string;
  partner_email: string;
  orders: FulfillmentPartnerOrder[];
}

export interface ShipmentRequest {
  carrier: string;
  tracking_number: string;
}

export interface ShipmentResponse {
  order_id: string;
  order_number: string;
  status: string;
  carrier: string;
  tracking_number: string;
  shipped_at: string;
  email_status: string;
}

// ============================================
// 관리자 대시보드
// ============================================
export interface DashboardSummary {
  total_orders: number;
  total_profit: number;
}

export interface InfluencerCommissionItem {
  influencer_id: string;
  influencer_name: string;
  pending_amount: number;
  completed_amount: number;
}

export interface InfluencerCommissionData {
  pending: InfluencerCommissionItem[];
  pending_total: number;
  completed_total: number;
}

export interface FulfillmentCommissionItem {
  partner_id: string;
  partner_name: string;
  pending_amount: number;
  completed_amount: number;
}

export interface FulfillmentCommissionData {
  pending: FulfillmentCommissionItem[];
  pending_total: number;
  completed_total: number;
}

export interface RefundRequestItem {
  refund_id: string;
  order_id: string;
  order_number: string;
  customer_name: string;
  refund_amount: number;
  refund_reason: string;
  requested_at: string;
}

export interface AdminDashboardResponse {
  summary: DashboardSummary;
  influencer_commissions: InfluencerCommissionData;
  fulfillment_commissions: FulfillmentCommissionData;
  refund_requests: RefundRequestItem[];
}
