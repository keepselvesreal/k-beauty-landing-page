/**
 * @file OrderForm.checkout.integration.test.tsx
 * @component OrderForm - Checkout 1-4단계 통합 테스트
 * @suite AT 1.6: 주문 생성 및 결제 시작 (TC 1.6.1~1.6.5)
 *
 * 설명:
 * Checkout 버튼 클릭 시 1-4단계 API 호출 흐름을 검증 (Integration 테스트):
 * 1단계: 고객 생성 (POST /api/customers)
 * 2단계: 주문 생성 (POST /api/orders)
 * 3단계: PayPal 초기화 (POST /api/orders/{order_id}/initiate-payment)
 * 4단계: PayPal 리다이렉션 (window.location.href)
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import OrderForm from '../../src/components/OrderForm';
import { API_BASE_URL } from '../../src/constants';

// fetch를 mock합니다
global.fetch = jest.fn();

beforeEach(() => {
  // Google Maps API를 mock하기 위해 window.google을 제거
  (window as any).google = undefined;
  // fetch 모킹 초기화
  (global.fetch as jest.Mock).mockClear();
  // console.error를 모킹 (에러 테스트에서 노이즈 제거)
  jest.spyOn(console, 'error').mockImplementation();
});

afterEach(() => {
  jest.clearAllMocks();
  jest.restoreAllMocks();
});

describe('OrderForm - Checkout 1-4단계 통합 테스트 (AT 1.6)', () => {
  // ========================================================================
  // TC-1.6.1: Checkout 정상 흐름 (1-4단계 모두 성공) 🟢 Happy Path 🟠 Integration
  // ========================================================================
  describe('TC-1.6.1: Checkout 정상 흐름 - 1-4단계 모두 성공', () => {
    it('모든 필수 정보가 입력되고 Checkout 클릭 시 1-4단계 API가 순서대로 호출되어야 한다', async () => {
      // ========== GIVEN ==========
      // 모든 필수 폼 필드가 유효하게 입력됨
      // 고객 생성, 주문 생성, PayPal 초기화 API 모두 성공 (모킹)
      const user = userEvent.setup();
      const mockNavigate = jest.fn();

      // fetch 모킹: 순서대로 응답
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          // 1단계: 고객 생성 응답
          ok: true,
          json: async () => ({
            id: 'customer-uuid-001',
            email: 'hong@example.com',
            name: '홍길동',
          }),
        })
        .mockResolvedValueOnce({
          // 2단계: 주문 생성 응답
          ok: true,
          json: async () => ({
            id: 'order-uuid-001',
            order_number: 'ORD-20251201-001',
            payment_status: 'pending',
            shipping_status: 'preparing',
          }),
        })
        .mockResolvedValueOnce({
          // 3단계: PayPal 초기화 응답
          ok: true,
          json: async () => ({
            paypal_order_id: 'PAYID-SUCCESS-001',
            approval_url: 'https://www.sandbox.paypal.com/checkoutnow?token=EC-001',
          }),
        });

      render(<OrderForm onNavigate={mockNavigate} />);

      // ========== WHEN ==========
      // 모든 필수 필드 입력
      const fullNameInput = document.querySelector('input[name="fullName"]') as HTMLInputElement;
      const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
      const phoneInput = document.querySelector('input[name="phone"]') as HTMLInputElement;
      const regionSelect = document.querySelector('select[name="region"]') as HTMLSelectElement;
      const addressInput = screen.getByPlaceholderText(
        /Search with Google Places/i
      ) as HTMLInputElement;
      const detailedAddressInput = document.querySelector(
        'textarea[name="detailedAddress"]'
      ) as HTMLTextAreaElement;

      await user.type(fullNameInput, '홍길동');
      await user.type(emailInput, 'hong@example.com');
      await user.type(phoneInput, '09123456789');
      await user.selectOptions(regionSelect, 'NCR');
      await user.type(addressInput, 'Manila City');
      await user.type(detailedAddressInput, 'Unit 123');

      // Checkout 버튼 클릭
      const checkoutButton = screen.getByRole('button', { name: /Checkout/i });
      await user.click(checkoutButton);

      // 모든 API 호출 완료를 기다림
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(3);
      });

      // ========== THEN ==========
      // 1단계: POST /api/customers 호출 (올바른 데이터)
      expect(global.fetch).toHaveBeenNthCalledWith(
        1,
        `${API_BASE_URL}/api/customers`,
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
      const customerBody = JSON.parse((global.fetch as jest.Mock).mock.calls[0][1].body);
      expect(customerBody).toMatchObject({
        email: 'hong@example.com',
        name: '홍길동',
        phone: '09123456789',
        region: 'NCR',
      });

      // 2단계: POST /api/orders 호출 (customerId, productId, quantity, region)
      expect(global.fetch).toHaveBeenNthCalledWith(
        2,
        `${API_BASE_URL}/api/orders`,
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        })
      );
      const orderBody = JSON.parse((global.fetch as jest.Mock).mock.calls[1][1].body);
      expect(orderBody).toMatchObject({
        customer_id: 'customer-uuid-001',
        product_id: 'rice-sunscreen-50ml', // constants.ts의 PRODUCT.id
        quantity: 1,
        region: 'NCR',
      });

      // 3단계: POST /api/orders/{order_id}/initiate-payment 호출
      expect(global.fetch).toHaveBeenNthCalledWith(
        3,
        `${API_BASE_URL}/api/orders/order-uuid-001/initiate-payment`,
        expect.objectContaining({
          method: 'POST',
        })
      );

      // 4단계: onNavigate가 approval_url로 호출됨
      expect(mockNavigate).toHaveBeenCalledWith(
        'https://www.sandbox.paypal.com/checkoutnow?token=EC-001'
      );
    });
  });

  // ========================================================================
  // TC-1.6.2: 고객 생성 실패 🔴 Error Case 🟠 Integration
  // ========================================================================
  describe('TC-1.6.2: 고객 생성 실패', () => {
    it('고객 생성 API가 실패하면 이후 단계는 호출되지 않아야 한다', async () => {
      // ========== GIVEN ==========
      // 모든 필수 폼 필드 입력됨
      // POST /api/customers가 실패 (Status 400)
      const user = userEvent.setup();
      const mockNavigate = jest.fn();

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        statusText: 'Bad Request',
      });

      render(<OrderForm onNavigate={mockNavigate} />);

      // ========== WHEN ==========
      const fullNameInput = document.querySelector('input[name="fullName"]') as HTMLInputElement;
      const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
      const phoneInput = document.querySelector('input[name="phone"]') as HTMLInputElement;
      const regionSelect = document.querySelector('select[name="region"]') as HTMLSelectElement;
      const addressInput = screen.getByPlaceholderText(/Search with Google Places/i) as HTMLInputElement;
      const detailedAddressInput = document.querySelector('textarea[name="detailedAddress"]') as HTMLTextAreaElement;

      await user.type(fullNameInput, '홍길동');
      await user.type(emailInput, 'hong@example.com');
      await user.type(phoneInput, '09123456789');
      await user.selectOptions(regionSelect, 'NCR');
      await user.type(addressInput, 'Manila City');
      await user.type(detailedAddressInput, 'Unit 123');

      const checkoutButton = screen.getByRole('button', { name: /Checkout/i });
      await user.click(checkoutButton);

      // 고객 생성 API 호출 완료를 기다림
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(1);
      });

      // ========== THEN ==========
      // POST /api/customers 호출 → 실패
      expect(global.fetch).toHaveBeenCalledTimes(1);
      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/customers`,
        expect.any(Object)
      );

      // 이후 단계 (주문 생성, 결제) 호출 안 됨
      expect(global.fetch).not.toHaveBeenCalledWith(
        `${API_BASE_URL}/api/orders`,
        expect.any(Object)
      );

      // onNavigate 호출 안 됨
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  // ========================================================================
  // TC-1.6.3: 주문 생성 실패 🔴 Error Case 🟠 Integration
  // ========================================================================
  describe('TC-1.6.3: 주문 생성 실패', () => {
    it('주문 생성 API가 실패하면 PayPal 초기화는 호출되지 않아야 한다', async () => {
      // ========== GIVEN ==========
      // 고객 생성은 성공
      // POST /api/orders가 실패 (Status 400, 재고 부족 등)
      const user = userEvent.setup();
      const mockNavigate = jest.fn();

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          // 고객 생성 성공
          ok: true,
          json: async () => ({ id: 'customer-uuid-001' }),
        })
        .mockResolvedValueOnce({
          // 주문 생성 실패
          ok: false,
          statusText: 'Bad Request',
        });

      render(<OrderForm onNavigate={mockNavigate} />);

      // ========== WHEN ==========
      const fullNameInput = document.querySelector('input[name="fullName"]') as HTMLInputElement;
      const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
      const phoneInput = document.querySelector('input[name="phone"]') as HTMLInputElement;
      const regionSelect = document.querySelector('select[name="region"]') as HTMLSelectElement;
      const addressInput = screen.getByPlaceholderText(/Search with Google Places/i) as HTMLInputElement;
      const detailedAddressInput = document.querySelector('textarea[name="detailedAddress"]') as HTMLTextAreaElement;

      await user.type(fullNameInput, '홍길동');
      await user.type(emailInput, 'hong@example.com');
      await user.type(phoneInput, '09123456789');
      await user.selectOptions(regionSelect, 'NCR');
      await user.type(addressInput, 'Manila City');
      await user.type(detailedAddressInput, 'Unit 123');

      const checkoutButton = screen.getByRole('button', { name: /Checkout/i });
      await user.click(checkoutButton);

      // 주문 생성 API 호출 실패 완료를 기다림
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(2);
      });

      // ========== THEN ==========
      // 1단계 성공, 2단계 실패
      expect(global.fetch).toHaveBeenCalledTimes(2);

      // PayPal 초기화는 호출 안 됨
      expect(global.fetch).not.toHaveBeenCalledWith(
        expect.stringContaining('/initiate-payment'),
        expect.any(Object)
      );

      // onNavigate 호출 안 됨
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  // ========================================================================
  // TC-1.6.4: PayPal 초기화 실패 🔴 Error Case 🟠 Integration
  // ========================================================================
  describe('TC-1.6.4: PayPal 초기화 실패', () => {
    it('PayPal 초기화 API가 실패하면 리다이렉션이 발생하지 않아야 한다', async () => {
      // ========== GIVEN ==========
      // 고객 생성, 주문 생성 성공
      // POST /api/orders/{order_id}/initiate-payment가 실패 (Status 500)
      const user = userEvent.setup();
      const mockNavigate = jest.fn();

      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          // 고객 생성 성공
          ok: true,
          json: async () => ({ id: 'customer-uuid-001' }),
        })
        .mockResolvedValueOnce({
          // 주문 생성 성공
          ok: true,
          json: async () => ({ id: 'order-uuid-001' }),
        })
        .mockResolvedValueOnce({
          // PayPal 초기화 실패
          ok: false,
          statusText: 'Internal Server Error',
        });

      render(<OrderForm onNavigate={mockNavigate} />);

      // ========== WHEN ==========
      const fullNameInput = document.querySelector('input[name="fullName"]') as HTMLInputElement;
      const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
      const phoneInput = document.querySelector('input[name="phone"]') as HTMLInputElement;
      const regionSelect = document.querySelector('select[name="region"]') as HTMLSelectElement;
      const addressInput = screen.getByPlaceholderText(/Search with Google Places/i) as HTMLInputElement;
      const detailedAddressInput = document.querySelector('textarea[name="detailedAddress"]') as HTMLTextAreaElement;

      await user.type(fullNameInput, '홍길동');
      await user.type(emailInput, 'hong@example.com');
      await user.type(phoneInput, '09123456789');
      await user.selectOptions(regionSelect, 'NCR');
      await user.type(addressInput, 'Manila City');
      await user.type(detailedAddressInput, 'Unit 123');

      const checkoutButton = screen.getByRole('button', { name: /Checkout/i });
      await user.click(checkoutButton);

      // PayPal 초기화 API 호출 실패 완료를 기다림
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledTimes(3);
      });

      // ========== THEN ==========
      // 1, 2, 3단계 모두 호출됨
      expect(global.fetch).toHaveBeenCalledTimes(3);

      // onNavigate 호출 안 됨
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });

  // ========================================================================
  // TC-1.6.5: 네트워크 타임아웃 🔴 Error Case 🟠 Integration
  // ========================================================================
  describe('TC-1.6.5: 네트워크 타임아웃', () => {
    it('fetch 에러가 발생하면 리다이렉션이 발생하지 않아야 한다', async () => {
      // ========== GIVEN ==========
      // fetch가 타임아웃 (모킹)
      const user = userEvent.setup();
      const mockNavigate = jest.fn();

      (global.fetch as jest.Mock).mockRejectedValueOnce(
        new Error('Network timeout')
      );

      render(<OrderForm onNavigate={mockNavigate} />);

      // ========== WHEN ==========
      const fullNameInput = document.querySelector('input[name="fullName"]') as HTMLInputElement;
      const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
      const phoneInput = document.querySelector('input[name="phone"]') as HTMLInputElement;
      const regionSelect = document.querySelector('select[name="region"]') as HTMLSelectElement;
      const addressInput = screen.getByPlaceholderText(/Search with Google Places/i) as HTMLInputElement;
      const detailedAddressInput = document.querySelector('textarea[name="detailedAddress"]') as HTMLTextAreaElement;

      await user.type(fullNameInput, '홍길동');
      await user.type(emailInput, 'hong@example.com');
      await user.type(phoneInput, '09123456789');
      await user.selectOptions(regionSelect, 'NCR');
      await user.type(addressInput, 'Manila City');
      await user.type(detailedAddressInput, 'Unit 123');

      const checkoutButton = screen.getByRole('button', { name: /Checkout/i });
      await user.click(checkoutButton);

      // 네트워크 에러 처리 완료를 기다림
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalled();
      });

      // ========== THEN ==========
      // fetch 호출됨 (에러 발생)
      expect(global.fetch).toHaveBeenCalled();

      // onNavigate 호출 안 됨
      expect(mockNavigate).not.toHaveBeenCalled();
    });
  });
});
