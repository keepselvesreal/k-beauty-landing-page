import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import OrderConfirmation from '../../../src/components/OrderConfirmation';
import { Order, Customer } from '../../../src/types';

// Mock API calls
global.fetch = jest.fn();

// Mock i18n
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

// Mock lucide-react
jest.mock('lucide-react', () => ({
  Copy: () => <div>Copy</div>,
  CheckCircle: () => <div>CheckCircle</div>,
  X: () => <div>X</div>,
}));

// Mock RequestModal
jest.mock('../../../src/components/RequestModal', () => {
  return function MockRequestModal() {
    return <div>RequestModal</div>;
  };
});

describe('OrderConfirmation - Button Enable/Disable Logic', () => {
  const mockOrder: Order = {
    id: '123',
    order_number: 'ORD-123',
    customer_id: 'cust-123',
    payment_status: 'paid',
    shipping_status: 'preparing',
    subtotal: 50,
    shipping_fee: 100,
    total_price: 150,
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  };

  const mockCustomer: Customer = {
    id: 'cust-123',
    name: 'John Doe',
    email: 'john@example.com',
    phone: '+639123456789',
    region: 'NCR',
    address: '123 Main St',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({
        ...mockOrder,
        customer: mockCustomer,
        order_items: [],
      }),
    });
  });

  describe('TC-2.1.1: 취소 버튼 - 배송 준비 중일 때만 활성화', () => {
    it('배송 준비 중일 때 취소 버튼이 활성화되어야 함', async () => {
      render(<OrderConfirmation orderNumber="ORD-123" />);

      // 로딩 완료 대기
      const cancelButton = await screen.findByRole('button', { name: /cancelRequest/i });

      expect(cancelButton).not.toBeDisabled();
    });

    it('배송 중일 때 취소 버튼이 비활성화되어야 함', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockOrder,
          shipping_status: 'shipped',
          customer: mockCustomer,
          order_items: [],
        }),
      });

      render(<OrderConfirmation orderNumber="ORD-123" />);

      const cancelButton = await screen.findByRole('button', { name: /cancelRequest/i });

      expect(cancelButton).toBeDisabled();
    });

    it('배송 완료일 때 취소 버튼이 비활성화되어야 함', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockOrder,
          shipping_status: 'delivered',
          customer: mockCustomer,
          order_items: [],
        }),
      });

      render(<OrderConfirmation orderNumber="ORD-123" />);

      const cancelButton = await screen.findByRole('button', { name: /cancelRequest/i });

      expect(cancelButton).toBeDisabled();
    });
  });

  describe('TC-2.1.3: 취소 이미 요청된 상태에서 버튼 비활성화', () => {
    it('취소 요청 중(cancel_requested)일 때 취소 버튼이 비활성화되어야 함', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockOrder,
          cancellation_status: 'cancel_requested',
          customer: mockCustomer,
          order_items: [],
        }),
      });

      render(<OrderConfirmation orderNumber="ORD-123" />);

      const cancelButton = await screen.findByRole('button', { name: /cancelRequest/i });

      expect(cancelButton).toBeDisabled();
    });

    it('취소됨(cancelled)일 때 취소 버튼이 비활성화되어야 함', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockOrder,
          cancellation_status: 'cancelled',
          customer: mockCustomer,
          order_items: [],
        }),
      });

      render(<OrderConfirmation orderNumber="ORD-123" />);

      const cancelButton = await screen.findByRole('button', { name: /cancelRequest/i });

      expect(cancelButton).toBeDisabled();
    });
  });

  describe('TC-2.2.1: 환불 버튼 - 배송 완료일 때만 활성화', () => {
    it('배송 완료일 때 환불 버튼이 활성화되어야 함', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockOrder,
          shipping_status: 'delivered',
          customer: mockCustomer,
          order_items: [],
        }),
      });

      render(<OrderConfirmation orderNumber="ORD-123" />);

      const refundButton = await screen.findByRole('button', { name: /refundRequest/i });

      expect(refundButton).not.toBeDisabled();
    });

    it('배송 준비 중일 때 환불 버튼이 비활성화되어야 함', async () => {
      render(<OrderConfirmation orderNumber="ORD-123" />);

      const refundButton = await screen.findByRole('button', { name: /refundRequest/i });

      expect(refundButton).toBeDisabled();
    });

    it('배송 중일 때 환불 버튼이 비활성화되어야 함', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockOrder,
          shipping_status: 'shipped',
          customer: mockCustomer,
          order_items: [],
        }),
      });

      render(<OrderConfirmation orderNumber="ORD-123" />);

      const refundButton = await screen.findByRole('button', { name: /refundRequest/i });

      expect(refundButton).toBeDisabled();
    });
  });

  describe('TC-2.2.3: 환불 이미 요청된 상태에서 버튼 비활성화', () => {
    it('환불 요청 중(refund_requested)일 때 환불 버튼이 비활성화되어야 함', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockOrder,
          shipping_status: 'delivered',
          refund_status: 'refund_requested',
          customer: mockCustomer,
          order_items: [],
        }),
      });

      render(<OrderConfirmation orderNumber="ORD-123" />);

      const refundButton = await screen.findByRole('button', { name: /refundRequest/i });

      expect(refundButton).toBeDisabled();
    });

    it('환불됨(refunded)일 때 환불 버튼이 비활성화되어야 함', async () => {
      (global.fetch as jest.Mock).mockResolvedValue({
        ok: true,
        json: async () => ({
          ...mockOrder,
          shipping_status: 'delivered',
          refund_status: 'refunded',
          customer: mockCustomer,
          order_items: [],
        }),
      });

      render(<OrderConfirmation orderNumber="ORD-123" />);

      const refundButton = await screen.findByRole('button', { name: /refundRequest/i });

      expect(refundButton).toBeDisabled();
    });
  });
});

describe('OrderConfirmation - Phase 5: Email Authentication', () => {
  const ORDER_NUMBER = 'ORD-550e8400-e29b-41d4-a716-446655440000';
  const mockOrderData = {
    id: '550e8400-e29b-41d4-a716-446655440000',
    order_number: ORDER_NUMBER,
    customer_id: '550e8400-e29b-41d4-a716-446655440001',
    subtotal: 250,
    shipping_fee: 100,
    total_price: 350,
    payment_status: 'pending',
    shipping_status: 'preparing',
    cancellation_status: null,
    refund_status: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
    customer: {
      id: '550e8400-e29b-41d4-a716-446655440001',
      name: '테스트 고객',
      email: 'test.customer@example.com',
      phone: '09123456789',
      region: 'NCR',
      address: 'Manila, Philippines',
    },
    order_items: [
      {
        id: '550e8400-e29b-41d4-a716-446655440002',
        product_id: '550e8400-e29b-41d4-a716-446655440003',
        quantity: 5,
        unit_price: 50,
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('TC-4.1.1: PayPal 결제 직후 localStorage에서 이메일 자동 읽음', () => {
    it('GIVEN: localStorage에 customer_email이 저장 | WHEN: 컴포넌트 마운트 | THEN: 자동으로 API 호출', async () => {
      // ========== GIVEN ==========
      // localStorage에 이메일 저장
      localStorage.setItem('customer_email', 'test.customer@example.com');

      // API 응답 모킹
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrderData,
      });

      // ========== WHEN ==========
      // 컴포넌트 마운트
      render(<OrderConfirmation orderNumber={ORDER_NUMBER} />);

      // ========== THEN ==========
      // 자동으로 API 호출
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalled();
      });

      // 주문 정보 바로 표시 (사용자가 이메일 입력할 필요 없음)
      await waitFor(() => {
        expect(screen.getByText(ORDER_NUMBER)).toBeInTheDocument();
      });
    });
  });

  describe('TC-4.4.1: 나중 재방문 - 사용자 이메일 입력 후 인증', () => {
    it('GIVEN: localStorage에 customer_email 없음 | WHEN: 이메일 입력 후 [Verify] 클릭 | THEN: API 호출 후 주문 정보 표시', async () => {
      // ========== GIVEN ==========
      // localStorage가 비어있음
      expect(localStorage.getItem('customer_email')).toBeNull();

      // API 응답 모킹
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrderData,
      });

      // ========== WHEN ==========
      // 컴포넌트 마운트
      render(<OrderConfirmation orderNumber={ORDER_NUMBER} />);

      // 이메일 입력란 표시 확인
      await waitFor(() => {
        expect(screen.getByPlaceholderText('your@email.com')).toBeInTheDocument();
      });

      // 이메일 입력
      const emailInput = screen.getByPlaceholderText('your@email.com');
      fireEvent.change(emailInput, { target: { value: 'test.customer@example.com' } });

      // [Verify] 버튼 클릭
      const submitButton = await screen.findByRole('button');
      fireEvent.click(submitButton);

      // ========== THEN ==========
      // API 호출
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalled();
      });

      // 일치하면 주문 정보 표시
      await waitFor(() => {
        expect(screen.getByText(ORDER_NUMBER)).toBeInTheDocument();
      });

      // localStorage에 저장 안 됨
      expect(localStorage.getItem('customer_email')).toBeNull();
    });
  });

  describe('TC-4.5.1: 이메일 필드 비어있을 때 [Verify] 클릭 불가', () => {
    it('GIVEN: 이메일 입력란이 비어있음 | WHEN: [Verify] 버튼 클릭 | THEN: 에러 메시지 표시, API 호출 안 됨', async () => {
      // ========== GIVEN ==========
      // localStorage가 비어있음
      localStorage.clear();

      // ========== WHEN ==========
      // 컴포넌트 마운트
      render(<OrderConfirmation orderNumber={ORDER_NUMBER} />);

      // 이메일 입력란이 표시될 때까지 대기
      await waitFor(() => {
        expect(screen.getByPlaceholderText('your@email.com')).toBeInTheDocument();
      });

      // 이메일을 입력하지 않음
      const emailInput = screen.getByPlaceholderText('your@email.com') as HTMLInputElement;
      expect(emailInput.value).toBe('');

      // [Verify] 버튼 클릭
      const submitButton = await screen.findByRole('button');
      fireEvent.click(submitButton);

      // ========== THEN ==========
      // 에러 메시지 표시
      await waitFor(() => {
        expect(screen.getByText('Please enter an email')).toBeInTheDocument();
      });

      // API 호출 안 됨
      expect(global.fetch).not.toHaveBeenCalled();
    });
  });

  describe('TC-4.6.1: 이메일 인증 성공 후 localStorage 삭제', () => {
    it('GIVEN: localStorage에 customer_email 저장 | WHEN: 이메일 인증 성공 | THEN: localStorage 완전히 삭제', async () => {
      // ========== GIVEN ==========
      // localStorage에 이메일 저장
      localStorage.setItem('customer_email', 'test.customer@example.com');
      expect(localStorage.getItem('customer_email')).toBe('test.customer@example.com');

      // API 응답 모킹
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockOrderData,
      });

      // ========== WHEN ==========
      // 컴포넌트 마운트
      render(<OrderConfirmation orderNumber={ORDER_NUMBER} />);

      // API 호출 및 응답 대기
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalled();
      });

      // ========== THEN ==========
      // 인증 성공 후 주문 정보 페이지 렌더링
      await waitFor(() => {
        expect(screen.getByText(ORDER_NUMBER)).toBeInTheDocument();
      });

      // localStorage에서 customer_email 삭제
      expect(localStorage.getItem('customer_email')).toBeNull();
    });
  });
});
