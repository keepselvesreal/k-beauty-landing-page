/**
 * @file OrderForm.checkoutAPI.test.tsx
 * @component OrderForm - Checkout 버튼 API 호출 기능
 * @suite AT 1.6: 재고 확인 및 결제 시작 (TC 1.6.3)
 * @case 🟢 Happy Path (정상 동작)
 *
 * 설명:
 * 고객이 모든 필수 정보를 입력하고 Checkout 버튼을 클릭했을 때,
 * /api/orders/create API가 올바른 데이터와 함께 호출되는지 검증하는 테스트.
 *
 * 필수 정보:
 * - fullName: 고객명
 * - email: 이메일
 * - phone: 전화번호
 * - region: 지역
 * - address: 주소
 * - detailedAddress: 상세주소
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import OrderForm from '../../../src/components/OrderForm';

// fetch를 mock합니다
global.fetch = jest.fn();

beforeEach(() => {
  // Google Maps API를 mock하기 위해 window.google을 제거
  (window as any).google = undefined;
  // fetch 모킹 초기화
  (global.fetch as jest.Mock).mockClear();
  // 성공 응답 설정
  (global.fetch as jest.Mock).mockResolvedValueOnce({
    ok: true,
    json: async () => ({
      order_id: 'ORD-12345',
      status: 'pending_payment',
      email_sent: true,
    }),
  });
});

afterEach(() => {
  jest.clearAllMocks();
});

describe('OrderForm - Checkout 버튼 API 호출 (AT 1.6)', () => {
  describe('TC 1.6.3: "결제하기" 버튼 클릭 시 /api/orders/create API가 호출', () => {
    it('Checkout 버튼 클릭 시 /api/orders/create API가 올바른 데이터와 함께 호출되어야 한다', async () => {
      // ========== Given ==========
      // OrderForm이 렌더링되고 모든 필수 정보가 입력된 상태
      const user = userEvent.setup();
      render(<OrderForm />);

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

      // 모든 필수 필드 입력
      await user.type(fullNameInput, '홍길동');
      await user.type(emailInput, 'hong@example.com');
      await user.type(phoneInput, '09123456789');
      await user.selectOptions(regionSelect, 'NCR');
      await user.type(addressInput, 'Manila City');
      await user.type(detailedAddressInput, 'Unit 123');

      // ========== When ==========
      // Checkout 버튼을 클릭
      const checkoutButton = screen.getByRole('button', { name: /Checkout/i });
      await user.click(checkoutButton);

      // ========== Then ==========
      // /api/orders/create API가 호출되어야 함
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/orders/create'),
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
          body: expect.stringContaining('홍길동'),
        })
      );

      // 요청 body에 올바른 데이터가 포함되어야 함
      const callArgs = (global.fetch as jest.Mock).mock.calls[0];
      const requestBody = JSON.parse(callArgs[1].body);

      expect(requestBody).toMatchObject({
        customer_name: '홍길동',
        email: 'hong@example.com',
        phone: '09123456789',
        region: 'NCR',
        address: 'Manila City',
        detailed_address: 'Unit 123',
      });
    });
  });
});
