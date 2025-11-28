/**
 * @file OrderForm.totalAmount.test.tsx
 * @component OrderForm - 총액 계산 기능
 * @suite AT 1.5: 배송료 계산 및 총액 업데이트
 *
 * 설명:
 * 고객이 주문 정보(지역, 수량 등)를 변경했을 때, Price Summary의
 * 총액(Total Amount)이 올바르게 계산되는지 검증한다.
 *
 * 검증 공식:
 * totalAmount = (상품가격 × 수량) + 선택된지역의배송료
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import OrderForm from '../../src/components/OrderForm';
import { REGIONS } from '../../src/constants';
import { PRODUCT } from '../../src/constants';

beforeEach(() => {
  // Google Maps API를 mock하기 위해 window.google을 제거
  (window as any).google = undefined;
});

afterEach(() => {
  jest.clearAllMocks();
});

describe('TC 1.5.5: 지역 변경 시 총액 계산)', () => {
  it('지역을 변경했을 때, 총액이 공식에 따라 올바르게 계산되어야 한다', async () => {
    // ========== Given ==========
    // OrderForm이 렌더링되고 초기 상태 (지역: NCR, 수량: 1)
    const user = userEvent.setup();
    render(<OrderForm />);

    const regionSelect = screen.getByLabelText(/Region/i) as HTMLSelectElement;

    // ========== When & Then ==========
    // 모든 지역에 대해 총액 공식 검증
    for (const region of REGIONS) {
      await user.selectOptions(regionSelect, region.id);

      const expectedTotal = PRODUCT.price * 1 + region.rate;
      const totalAmountText = screen.getByText('Total Amount').nextElementSibling;
      expect(totalAmountText).toHaveTextContent(`₱${expectedTotal.toFixed(2)}`);
    }
  });
});

// TC 1.5.6 수량 변경 시 총액 계산 추가 가능
