/**
 * @file OrderForm.shippingRate.test.tsx
 * @component OrderForm - 배송료 계산 기능
 * @suite AT 1.5: 배송료 계산 (TC 1.5.1~1.5.4)
 * @case 🟢 Happy Path (정상 동작)
 *
 * 설명:
 * 고객이 지역 드롭다운을 선택했을 때, 해당 지역의 배송료가 즉시 UI의
 * "Shipping Fee" 섹션에 반영되는지 검증하는 매개변수화 테스트.
 *
 * 지역별 배송료:
 * - NCR: ₱100
 * - Luzon: ₱120
 * - Visayas: ₱140
 * - Mindanao: ₱160
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

describe('OrderForm - 배송료 계산 (AT 1.5)', () => {
  // 지역별 배송료 테스트 케이스
  const shippingRegionTestCases = [
    { region: 'NCR', expectedRate: 100 },
    { region: 'Luzon', expectedRate: 120 },
    { region: 'Visayas', expectedRate: 140 },
    { region: 'Mindanao', expectedRate: 160 },
  ];

  describe('지역별 배송료 표시 (매개변수화)', () => {
    it.each(shippingRegionTestCases)(
      '사용자가 $region 지역을 선택했을 때, 배송료가 ₱$expectedRate로 즉시 반영되어야 한다',
      async ({ region, expectedRate }) => {
        // ========== Given ==========
        // OrderForm이 렌더링되고 초기 지역은 NCR(배송료 ₱100)로 설정된 상태
        const user = userEvent.setup();
        render(<OrderForm />);

        // ========== When ==========
        // 사용자가 지역 드롭다운에서 특정 지역을 선택
        const regionSelect = screen.getByLabelText(/Region/i) as HTMLSelectElement;
        await user.selectOptions(regionSelect, region);

        // ========== Then ==========
        // Price Summary의 "Shipping Fee" 섹션에 예상 배송료(₱expectedRate)가 표시되어야 함
        const shippingFeeLabel = screen.getByText('Shipping Fee');
        const shippingFeeSection = shippingFeeLabel.closest('div');
        expect(shippingFeeSection).toHaveTextContent(`₱${expectedRate.toFixed(2)}`);
      }
    );
  });
});
