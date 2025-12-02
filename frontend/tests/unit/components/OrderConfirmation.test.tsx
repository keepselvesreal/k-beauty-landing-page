import React from 'react';
import { render, screen } from '@testing-library/react';
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
