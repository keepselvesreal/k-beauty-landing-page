/**
 * @file OrderForm.googlePlaces.integration.real-api.test.tsx
 * @component OrderForm - Google Places API 실제 API 호출 통합 테스트
 * @suite Google Places API 실제 호출 통합 테스트 (4가지 시나리오)
 *
 * 설명:
 * Google Places Autocomplete 실제 API를 호출하여 OrderForm과의 상호작용을 검증
 * - 환경 변수 VITE_GOOGLE_PLACES_API_KEY 필요
 * - 네트워크 의존성 있음 (느린 테스트)
 * - 실제 Google Maps API 응답 검증
 *
 * 실행 방법:
 * npm test -- --testPathPatterns="real-api" --runInBand
 *
 * 참고:
 * 이 테스트는 CI/CD에서는 제외하고 로컬 개발 또는 별도 E2E 단계에서만 실행 권장
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import OrderForm from '../../src/components/OrderForm';

// 실제 Google Maps API 스크립트 로드 여부 확인
const isGoogleMapsAPIAvailable = () => {
  return (
    (window as any).google &&
    (window as any).google.maps &&
    (window as any).google.maps.places
  );
};

// Google Maps API 로드
const loadGoogleMapsAPI = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (isGoogleMapsAPIAvailable()) {
      resolve();
      return;
    }

    const apiKey = process.env.VITE_GOOGLE_PLACES_API_KEY;
    if (!apiKey) {
      reject(new Error('VITE_GOOGLE_PLACES_API_KEY 환경 변수가 설정되지 않았습니다.'));
      return;
    }

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=places`;
    script.async = true;
    script.defer = true;

    script.onload = () => {
      if (isGoogleMapsAPIAvailable()) {
        resolve();
      } else {
        reject(new Error('Google Maps API 로드는 완료되었지만 places 라이브러리를 사용할 수 없습니다.'));
      }
    };

    script.onerror = () => {
      reject(new Error('Google Maps API 스크립트 로드 실패. API 키를 확인하세요.'));
    };

    document.head.appendChild(script);
  });
};

beforeEach(async () => {
  // console.error를 모킹 (에러 테스트에서 노이즈 제거)
  jest.spyOn(console, 'error').mockImplementation();

  // Google Maps API 로드 (한 번만)
  if (!isGoogleMapsAPIAvailable()) {
    try {
      await loadGoogleMapsAPI();
    } catch (error) {
      console.warn('Google Maps API 로드 실패:', error);
      // 테스트 스킵: API를 사용할 수 없으면 진행 불가
    }
  }
});

afterEach(() => {
  jest.clearAllMocks();
  jest.restoreAllMocks();
});

describe('OrderForm - Google Places API 실제 호출 통합 테스트', () => {
  /**
   * ========================================================================
   * TC-GP-REAL.1: 실제 주소 검색 및 선택 🟢 Happy Path 🟠 Integration
   * ========================================================================
   *
   * Given: 실제 Google Places API가 로드됨
   * When: 사용자가 "Manila" 주소를 검색하고 선택
   * Then: formState.address가 실제 필리핀 주소로 업데이트됨
   */
  describe('TC-GP-REAL.1: 실제 주소 검색 및 선택', () => {
    it('실제 Google Places API에서 필리핀 주소를 검색하고 선택할 수 있다', async () => {
      // API가 없으면 스킵
      if (!isGoogleMapsAPIAvailable()) {
        console.warn('Google Maps API를 사용할 수 없어 테스트를 스킵합니다.');
        return;
      }

      // GIVEN: OrderForm 렌더링
      render(<OrderForm />);

      const addressInput = screen.getByPlaceholderText(
        /Search with Google Places/i
      ) as HTMLInputElement;

      // WHEN: 사용자가 주소 입력
      const user = userEvent.setup();
      await user.type(addressInput, 'Manila City');

      // 자동완성 목록이 나타날 때까지 대기
      // (실제 Google API는 네트워크 호출이므로 시간이 필요)
      await waitFor(
        () => {
          // 자동완성 목록에서 첫 번째 항목 찾기
          const suggestions = document.querySelectorAll('[role="option"]');
          expect(suggestions.length).toBeGreaterThan(0);
        },
        { timeout: 5000 }
      );

      // THEN: 자동완성 목록 중 첫 번째 선택
      const suggestions = document.querySelectorAll('[role="option"]');
      if (suggestions.length > 0) {
        await user.click(suggestions[0] as HTMLElement);

        // 선택 후 address 필드가 업데이트되었는지 확인
        await waitFor(
          () => {
            expect(addressInput.value).toBeTruthy();
            expect(addressInput.value).toContain('Manila');
          },
          { timeout: 3000 }
        );

        expect(addressInput.value).toBeTruthy();
        expect(addressInput.value).toContain('Philippines');
      }
    });
  });

  /**
   * ========================================================================
   * TC-GP-REAL.2: 여러 지역 검색 🟢 Happy Path 🟠 Integration
   * ========================================================================
   *
   * Given: 실제 Google Places API가 로드됨
   * When: 사용자가 여러 지역(Cebu, Davao 등)을 연속으로 검색
   * Then: 각 검색 결과가 정확하게 표시되고 선택 가능
   */
  describe('TC-GP-REAL.2: 여러 지역 검색', () => {
    it('Cebu, Davao 등 여러 필리핀 지역을 검색할 수 있다', async () => {
      // API가 없으면 스킵
      if (!isGoogleMapsAPIAvailable()) {
        console.warn('Google Maps API를 사용할 수 없어 테스트를 스킵합니다.');
        return;
      }

      // GIVEN: OrderForm 렌더링
      render(<OrderForm />);

      const addressInput = screen.getByPlaceholderText(
        /Search with Google Places/i
      ) as HTMLInputElement;

      const user = userEvent.setup();

      // WHEN & THEN: Cebu 검색
      await user.type(addressInput, 'Cebu');

      await waitFor(
        () => {
          const suggestions = document.querySelectorAll('[role="option"]');
          expect(suggestions.length).toBeGreaterThan(0);
        },
        { timeout: 5000 }
      );

      expect(addressInput.value).toBe('Cebu');

      // 입력 필드 초기화
      await user.clear(addressInput);

      // WHEN & THEN: Davao 검색
      await user.type(addressInput, 'Davao');

      await waitFor(
        () => {
          const suggestions = document.querySelectorAll('[role="option"]');
          expect(suggestions.length).toBeGreaterThan(0);
        },
        { timeout: 5000 }
      );

      expect(addressInput.value).toBe('Davao');
    });
  });

  /**
   * ========================================================================
   * TC-GP-REAL.3: 필리핀 지역 제약 검증 🟨 Edge Case 🟠 Integration
   * ========================================================================
   *
   * Given: Google Places Autocomplete이 componentRestrictions { country: 'ph' }로 설정됨
   * When: 사용자가 필리핀 외 국가(Sydney, Tokyo 등)를 검색 시도
   * Then: 검색 결과가 필리핀만 반환되거나 제한됨
   */
  describe('TC-GP-REAL.3: 필리핀 지역 제약 검증', () => {
    it('필리핀 외 국가 검색 시 필리핀 결과만 반환된다', async () => {
      // API가 없으면 스킵
      if (!isGoogleMapsAPIAvailable()) {
        console.warn('Google Maps API를 사용할 수 없어 테스트를 스킵합니다.');
        return;
      }

      // GIVEN: OrderForm 렌더링
      render(<OrderForm />);

      const addressInput = screen.getByPlaceholderText(
        /Search with Google Places/i
      ) as HTMLInputElement;

      const user = userEvent.setup();

      // WHEN: 필리핀 외 국가 검색 시도
      await user.type(addressInput, 'Sydney');

      // 자동완성 목록 대기 (또는 결과 없음)
      await new Promise((resolve) => setTimeout(resolve, 2000));

      // THEN: 결과가 필리핀 주소이거나 없어야 함
      const suggestions = document.querySelectorAll('[role="option"]');

      // 결과가 있으면 필리핀 주소여야 함
      if (suggestions.length > 0) {
        for (const suggestion of suggestions) {
          const text = suggestion.textContent || '';
          expect(text).toContain('Philippines');
        }
      }
    });
  });

  /**
   * ========================================================================
   * TC-GP-REAL.4: 완전한 주소 선택 후 전체 폼 검증 🟢 Happy Path 🟠 Integration
   * ========================================================================
   *
   * Given: 실제 Google Places API에서 주소를 선택함
   * When: OrderForm의 모든 필드를 입력하고 Checkout 준비
   * Then: 모든 필드가 올바르게 채워지고 Checkout 버튼이 활성화됨
   */
  describe('TC-GP-REAL.4: 완전한 주소 선택 후 전체 폼 검증', () => {
    it('실제 주소 선택 후 OrderForm 전체 필드가 올바르게 작동한다', async () => {
      // API가 없으면 스킵
      if (!isGoogleMapsAPIAvailable()) {
        console.warn('Google Maps API를 사용할 수 없어 테스트를 스킵합니다.');
        return;
      }

      // GIVEN: OrderForm 렌더링
      render(<OrderForm />);

      const user = userEvent.setup();

      // 필드들 찾기
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

      // WHEN: 모든 필드 입력
      await user.type(fullNameInput, 'Hong Gildong');
      await user.type(emailInput, 'hong@example.com');
      await user.type(phoneInput, '09123456789');
      await user.selectOptions(regionSelect, 'NCR');

      // 주소 입력
      await user.type(addressInput, 'Manila');

      // 자동완성 목록 대기
      await waitFor(
        () => {
          const suggestions = document.querySelectorAll('[role="option"]');
          expect(suggestions.length).toBeGreaterThan(0);
        },
        { timeout: 5000 }
      );

      // 첫 번째 제안 선택
      const suggestions = document.querySelectorAll('[role="option"]');
      if (suggestions.length > 0) {
        await user.click(suggestions[0] as HTMLElement);

        // 주소 선택 완료 대기
        await waitFor(
          () => {
            expect(addressInput.value).toBeTruthy();
          },
          { timeout: 3000 }
        );
      }

      await user.type(detailedAddressInput, 'Unit 101');

      // THEN: 모든 필드가 입력됨
      expect(fullNameInput.value).toBe('Hong Gildong');
      expect(emailInput.value).toBe('hong@example.com');
      expect(phoneInput.value).toBe('09123456789');
      expect(regionSelect.value).toBe('NCR');
      expect(addressInput.value).toBeTruthy();
      expect(detailedAddressInput.value).toBe('Unit 101');

      // THEN: Checkout 버튼이 활성화됨
      const checkoutButton = screen.getByRole('button', { name: /Checkout/i });
      expect(checkoutButton).not.toBeDisabled();
    });
  });

  /**
   * ========================================================================
   * 주의사항 및 참고
   * ========================================================================
   *
   * 1. 이 테스트는 VITE_GOOGLE_PLACES_API_KEY 환경 변수가 필요합니다
   * 2. 네트워크 호출이 포함되므로 느립니다 (최대 10-15초 소요)
   * 3. Google API의 Rate Limiting이 있으므로 자주 실행하지 마세요
   * 4. CI/CD 파이프라인에서는 제외 권장 (로컬 또는 수동 테스트용)
   *
   * 실행 시간 개선 방법:
   * - timeout 값 조정 (현재 5000ms)
   * - 테스트를 선택적으로 실행
   * - E2E 테스트로 전환 (더 빠른 UI 자동화 도구 사용)
   */
});
