/**
 * @file OrderForm.checkoutButton.test.tsx
 * @component OrderForm - Checkout 버튼 활성화 기능
 * @suite AT 1.6: 재고 확인 및 결제 시작 (TC 1.6.1)
 * @case 🟢 Happy Path (정상 동작)
 *
 * 설명:
 * 고객이 모든 필수 정보를 입력했을 때, Checkout 버튼이 활성화되는지 검증하는 테스트.
 *
 * 필수 정보:
 * - fullName: 고객명
 * - email: 이메일
 * - phone: 전화번호
 * - region: 지역
 * - address: 주소
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import OrderForm from '../../../src/components/OrderForm';

beforeEach(() => {
  // Google Maps API를 mock하기 위해 window.google을 제거
  (window as any).google = undefined;
});

afterEach(() => {
  jest.clearAllMocks();
});

describe('OrderForm - Checkout 버튼 활성화/비활성화 (AT 1.6)', () => {
  describe('TC 1.6.1: 필수 정보가 모두 입력되면 Checkout 버튼이 활성화', () => {
    it('모든 필수 정보가 입력되었을 때, Checkout 버튼이 활성화되어야 한다', async () => {
      // ========== Given ==========
      // OrderForm이 렌더링되고 모든 필드가 초기 상태인 상태
      const user = userEvent.setup();
      render(<OrderForm />);

      // ========== When ==========
      // 사용자가 모든 필수 필드에 유효한 값을 입력
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

      // ========== Then ==========
      // Checkout 버튼이 활성화 상태여야 함 (disabled 속성이 없어야 함)
      const checkoutButton = screen.getByRole('button', { name: /Checkout/i });
      expect(checkoutButton).not.toHaveAttribute('disabled');
      expect(checkoutButton).toBeEnabled();
    });
  });

  // 필수 필드 누락 테스트 케이스
  const missingFieldTestCases = [
    {
      field: 'fullName',
      inputs: {
        fullName: '',
        email: 'hong@example.com',
        phone: '09123456789',
        region: 'NCR',
        address: 'Manila City',
      },
    },
    {
      field: 'email',
      inputs: {
        fullName: '홍길동',
        email: '',
        phone: '09123456789',
        region: 'NCR',
        address: 'Manila City',
      },
    },
    {
      field: 'phone',
      inputs: {
        fullName: '홍길동',
        email: 'hong@example.com',
        phone: '',
        region: 'NCR',
        address: 'Manila City',
      },
    },
    {
      field: 'address',
      inputs: {
        fullName: '홍길동',
        email: 'hong@example.com',
        phone: '09123456789',
        region: 'NCR',
        address: '',
      },
    },
    {
      field: 'detailedAddress',
      inputs: {
        fullName: '홍길동',
        email: 'hong@example.com',
        phone: '09123456789',
        region: 'NCR',
        address: 'Manila City',
        detailedAddress: '',
      },
    },
  ];

  describe('TC 1.6.2: 필수 필드 누락 시 Checkout 버튼이 비활성화', () => {
    it.each(missingFieldTestCases)(
      '$field 필드가 누락되었을 때, Checkout 버튼이 비활성화되어야 한다',
      async ({ inputs }) => {
        // ========== Given ==========
        // OrderForm이 렌더링되고 초기 상태
        const user = userEvent.setup();
        render(<OrderForm />);

        // ========== When ==========
        // 사용자가 필드들을 입력 (하나는 비어있음)
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

        if (inputs.fullName) await user.type(fullNameInput, inputs.fullName);
        if (inputs.email) await user.type(emailInput, inputs.email);
        if (inputs.phone) await user.type(phoneInput, inputs.phone);
        if (inputs.region) await user.selectOptions(regionSelect, inputs.region);
        if (inputs.address) await user.type(addressInput, inputs.address);
        if (inputs.detailedAddress) await user.type(detailedAddressInput, inputs.detailedAddress);

        // ========== Then ==========
        // Checkout 버튼이 비활성화 상태여야 함 (disabled 속성을 가져야 함)
        const checkoutButton = screen.getByRole('button', { name: /Checkout/i });
        expect(checkoutButton).toHaveAttribute('disabled');
        expect(checkoutButton).toBeDisabled();
      }
    );
  });
});
