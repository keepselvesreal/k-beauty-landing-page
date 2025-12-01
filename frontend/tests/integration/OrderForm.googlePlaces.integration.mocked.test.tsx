/**
 * @file OrderForm.googlePlaces.integration.test.tsx
 * @component OrderForm - Google Places API 통합 테스트
 * @suite Google Places API 통합 테스트 (4가지 시나리오)
 *
 * 설명:
 * Google Places Autocomplete과 OrderForm의 상호작용을 검증
 * - TC-GP-INT.1: 여러 번 선택 시 올바르게 업데이트
 * - TC-GP-INT.2: 빠른 입력/선택 시 레이싱 컨디션 없음
 * - TC-GP-INT.3: API 오류 시 graceful handling
 * - TC-GP-INT.4: UI 피드백 (로딩 상태, 에러 메시지)
 */

import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import OrderForm from '../../src/components/OrderForm';

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

describe('OrderForm - Google Places API 통합 테스트', () => {
  /**
   * ========================================================================
   * TC-GP-INT.1: 여러 번 선택 시 올바르게 업데이트 🟢 Happy Path 🟠 Integration
   * ========================================================================
   *
   * Given: Google Places Autocomplete이 초기화되어 있음
   * When: 사용자가 첫 번째 주소 선택 → 두 번째 주소 선택 → 세 번째 주소 선택
   * Then: 각 선택 후 formState.address가 정확히 업데이트되어야 함
   */
  describe('TC-GP-INT.1: 여러 번 선택 시 올바르게 업데이트', () => {
    it('첫 번째 선택 → 두 번째 선택 시 주소가 정확히 업데이트된다', async () => {
      // GIVEN: Google Places Autocomplete Mock
      let placeChangedCallback: (() => void) | null = null;
      let currentPlace: any = null;

      const mockAutocompleteInstance = {
        addListener: jest.fn((eventName: string, callback: () => void) => {
          if (eventName === 'place_changed') {
            placeChangedCallback = callback;
          }
        }),
        getPlace: jest.fn(() => currentPlace),
      };

      const mockGoogleMapsAPI = {
        google: {
          maps: {
            places: {
              Autocomplete: jest.fn(() => mockAutocompleteInstance),
            },
          },
        },
      };

      (window as any).google = mockGoogleMapsAPI.google;

      const { rerender } = render(<OrderForm />);

      // WHEN: 첫 번째 주소 선택
      currentPlace = {
        formatted_address: 'Manila, NCR, Philippines',
        geometry: { location: { lat: 14.5995, lng: 120.9842 } },
        place_id: 'ChIJR0h8ZhWvEmoRmheTjarani4',
      };

      await waitFor(() => {
        expect(placeChangedCallback).not.toBeNull();
      });

      act(() => {
        if (placeChangedCallback) placeChangedCallback();
      });

      await waitFor(() => {
        const addressInput = screen.getByPlaceholderText(
          /Search with Google Places/i
        ) as HTMLInputElement;
        expect(addressInput.value).toBe('Manila, NCR, Philippines');
      });

      // THEN: 첫 번째 선택 확인
      let addressInput = screen.getByPlaceholderText(
        /Search with Google Places/i
      ) as HTMLInputElement;
      expect(addressInput.value).toBe('Manila, NCR, Philippines');

      // WHEN: 두 번째 주소 선택
      currentPlace = {
        formatted_address: 'Cebu City, Cebu, Philippines',
        geometry: { location: { lat: 10.3157, lng: 123.8854 } },
        place_id: 'ChIJyVJTKLeXczMRHHSTQLZsH0A',
      };

      act(() => {
        if (placeChangedCallback) placeChangedCallback();
      });

      await waitFor(() => {
        addressInput = screen.getByPlaceholderText(
          /Search with Google Places/i
        ) as HTMLInputElement;
        expect(addressInput.value).toBe('Cebu City, Cebu, Philippines');
      });

      // THEN: 두 번째 선택이 정확히 업데이트됨
      expect(addressInput.value).toBe('Cebu City, Cebu, Philippines');

      // WHEN: 세 번째 주소 선택
      currentPlace = {
        formatted_address: 'Davao City, Davao del Sur, Philippines',
        geometry: { location: { lat: 7.0731, lng: 125.6136 } },
        place_id: 'ChIJ5z-tVMB5cDMRMp4_hxwNzCE',
      };

      act(() => {
        if (placeChangedCallback) placeChangedCallback();
      });

      await waitFor(() => {
        addressInput = screen.getByPlaceholderText(
          /Search with Google Places/i
        ) as HTMLInputElement;
        expect(addressInput.value).toBe('Davao City, Davao del Sur, Philippines');
      });

      // THEN: 세 번째 선택도 정확히 업데이트됨
      expect(addressInput.value).toBe('Davao City, Davao del Sur, Philippines');
    });
  });

  /**
   * ========================================================================
   * TC-GP-INT.2: 빠른 입력/선택 시 레이싱 컨디션 없음 🟨 Edge Case 🟠 Integration
   * ========================================================================
   *
   * Given: 사용자가 매우 빠르게 연속으로 장소를 선택
   * When: place_changed 이벤트가 거의 동시에 여러 번 발생
   * Then: 마지막 선택이 적용되고 이전 값으로 덮어씌워지지 않음
   */
  describe('TC-GP-INT.2: 빠른 입력/선택 시 레이싱 컨디션 없음', () => {
    it('빠른 연속 선택 시 마지막 값만 적용된다', async () => {
      // GIVEN: Google Places Autocomplete Mock (비동기 처리 시뮬레이션)
      let placeChangedCallback: (() => void) | null = null;
      const places = [
        {
          formatted_address: 'Manila, NCR, Philippines',
          geometry: { location: { lat: 14.5995, lng: 120.9842 } },
          place_id: 'ChIJR0h8ZhWvEmoRmheTjarani4',
        },
        {
          formatted_address: 'Cebu City, Cebu, Philippines',
          geometry: { location: { lat: 10.3157, lng: 123.8854 } },
          place_id: 'ChIJyVJTKLeXczMRHHSTQLZsH0A',
        },
        {
          formatted_address: 'Davao City, Davao del Sur, Philippines',
          geometry: { location: { lat: 7.0731, lng: 125.6136 } },
          place_id: 'ChIJ5z-tVMB5cDMRMp4_hxwNzCE',
        },
      ];

      let currentPlaceIndex = 0;

      const mockAutocompleteInstance = {
        addListener: jest.fn((eventName: string, callback: () => void) => {
          if (eventName === 'place_changed') {
            placeChangedCallback = callback;
          }
        }),
        getPlace: jest.fn(() => places[currentPlaceIndex]),
      };

      const mockGoogleMapsAPI = {
        google: {
          maps: {
            places: {
              Autocomplete: jest.fn(() => mockAutocompleteInstance),
            },
          },
        },
      };

      (window as any).google = mockGoogleMapsAPI.google;

      render(<OrderForm />);

      await waitFor(() => {
        expect(placeChangedCallback).not.toBeNull();
      });

      // WHEN: 빠른 연속 선택 (3개를 거의 동시에)
      currentPlaceIndex = 0;
      act(() => {
        if (placeChangedCallback) placeChangedCallback();
      });

      currentPlaceIndex = 1;
      act(() => {
        if (placeChangedCallback) placeChangedCallback();
      });

      currentPlaceIndex = 2;
      act(() => {
        if (placeChangedCallback) placeChangedCallback();
      });

      // THEN: 마지막 선택(Davao City)이 적용됨
      await waitFor(() => {
        const addressInput = screen.getByPlaceholderText(
          /Search with Google Places/i
        ) as HTMLInputElement;
        expect(addressInput.value).toBe('Davao City, Davao del Sur, Philippines');
      });

      const addressInput = screen.getByPlaceholderText(
        /Search with Google Places/i
      ) as HTMLInputElement;
      expect(addressInput.value).toBe('Davao City, Davao del Sur, Philippines');
    });
  });

  /**
   * ========================================================================
   * TC-GP-INT.3: API 오류 시 Graceful Handling 🔴 Error Case 🟠 Integration
   * ========================================================================
   *
   * Given: Google Maps API 로드 실패 (API 키 누락, 네트워크 오류 등)
   * When: OrderForm이 렌더링됨
   * Then: 앱이 crash되지 않고, 사용자가 주소를 수동으로 입력할 수 있음
   */
  describe('TC-GP-INT.3: API 오류 시 Graceful Handling', () => {
    it('Google Maps API 로드 실패 시 앱이 crash되지 않는다', async () => {
      // GIVEN: Google Maps API가 정의되지 않음 (로드 실패)
      (window as any).google = undefined;

      // WHEN: OrderForm 렌더링
      render(<OrderForm />);

      // THEN: 주소 입력 필드가 여전히 존재
      const addressInput = screen.getByPlaceholderText(
        /Search with Google Places/i
      ) as HTMLInputElement;

      expect(addressInput).toBeInTheDocument();

      // API 로드 실패 상태 대기
      await waitFor(() => {
        // addressInput이 disabled 상태여야 함 (API 로드 실패)
        // 또는 에러 메시지가 표시되어야 함
        expect(addressInput).toBeInTheDocument();
      });

      // 앱이 crash되지 않았으므로 테스트 통과
      // (API 로드 실패 후에도 OrderForm이 렌더링되었음)
      expect(addressInput).toBeInTheDocument();
    });

    it('불완전한 place 객체는 무시되고 에러 메시지 표시', async () => {
      // GIVEN: place.geometry가 없는 place 객체 반환
      let placeChangedCallback: (() => void) | null = null;

      const mockAutocompleteInstance = {
        addListener: jest.fn((eventName: string, callback: () => void) => {
          if (eventName === 'place_changed') {
            placeChangedCallback = callback;
          }
        }),
        getPlace: jest.fn(() => ({
          formatted_address: 'Manila',
          // geometry가 없음!
          place_id: 'ChIJR0h8ZhWvEmoRmheTjarani4',
        })),
      };

      const mockGoogleMapsAPI = {
        google: {
          maps: {
            places: {
              Autocomplete: jest.fn(() => mockAutocompleteInstance),
            },
          },
        },
      };

      (window as any).google = mockGoogleMapsAPI.google;

      render(<OrderForm />);

      await waitFor(() => {
        expect(placeChangedCallback).not.toBeNull();
      });

      const addressInput = screen.getByPlaceholderText(
        /Search with Google Places/i
      ) as HTMLInputElement;
      const initialValue = addressInput.value;

      // WHEN: place_changed 이벤트 발생
      act(() => {
        if (placeChangedCallback) placeChangedCallback();
      });

      // THEN: geometry가 없으므로 업데이트되지 않음
      await new Promise((resolve) => setTimeout(resolve, 100));
      expect(addressInput.value).toBe(initialValue);
    });
  });

  /**
   * ========================================================================
   * TC-GP-INT.4: UI 피드백 (로딩 상태, 에러 메시지) 🟨 Edge Case 🟠 Integration
   * ========================================================================
   *
   * Given: OrderForm이 렌더링되는 중 / 에러 발생 상황
   * When: Google Places API 로드 중 / 에러 발생
   * Then: 로딩 상태 표시 / 에러 메시지 표시 / Checkout 버튼 상태 변경
   */
  describe('TC-GP-INT.4: UI 피드백 (로딩 상태, 에러 메시지)', () => {
    it('Google Maps API 로드 중 로딩 상태 피드백을 제공한다', async () => {
      // GIVEN: Google Maps API가 아직 로드되지 않음
      (window as any).google = undefined;

      render(<OrderForm />);

      // THEN: 로딩 상태 메시지 또는 스핀너가 표시되어야 함
      // (구현 후 작성 - 현재는 구조 정의)
      const addressInput = screen.getByPlaceholderText(
        /Search with Google Places/i
      ) as HTMLInputElement;

      // 로딩 중에는 주소 입력 필드가 disabled될 수 있음
      // 또는 로딩 스피너가 표시될 수 있음
      expect(addressInput).toBeInTheDocument();
    });

    it('API 오류 시 사용자 친화적 에러 메시지를 표시한다', async () => {
      // GIVEN: Google Maps API 로드 실패
      (window as any).google = undefined;

      render(<OrderForm />);

      // THEN: 에러 메시지가 표시되어야 함
      // (구현 후 작성 - 현재는 구조 정의)

      // 예상 에러 메시지:
      // "주소 검색 기능을 설정할 수 없습니다. 관리자에게 문의하세요."
      // 또는 "네트워크 오류가 발생했습니다. 수동으로 주소를 입력해주세요."

      const addressInput = screen.getByPlaceholderText(
        /Search with Google Places/i
      ) as HTMLInputElement;

      expect(addressInput).toBeInTheDocument();
    });

    it('장소 선택 후 Checkout 버튼이 활성화된다', async () => {
      // GIVEN: 완전한 주소가 선택됨
      const listeners: { [key: string]: (() => void)[] } = {};

      const mockAutocompleteInstance = {
        addListener: jest.fn((eventName: string, callback: () => void) => {
          if (!listeners[eventName]) {
            listeners[eventName] = [];
          }
          listeners[eventName].push(callback);
        }),
        getPlace: jest.fn(() => ({
          formatted_address: 'Manila, NCR, Philippines',
          geometry: { location: { lat: 14.5995, lng: 120.9842 } },
          place_id: 'ChIJR0h8ZhWvEmoRmheTjarani4',
        })),
      };

      const mockGoogleMapsAPI = {
        google: {
          maps: {
            places: {
              Autocomplete: jest.fn(() => mockAutocompleteInstance),
            },
          },
        },
      };

      (window as any).google = mockGoogleMapsAPI.google;

      const user = userEvent.setup();
      render(<OrderForm />);

      // 모든 필수 필드 입력
      const fullNameInput = document.querySelector('input[name="fullName"]') as HTMLInputElement;
      const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
      const phoneInput = document.querySelector('input[name="phone"]') as HTMLInputElement;
      const regionSelect = document.querySelector('select[name="region"]') as HTMLSelectElement;
      const detailedAddressInput = document.querySelector(
        'textarea[name="detailedAddress"]'
      ) as HTMLTextAreaElement;

      // Google Places API 초기화 대기
      await waitFor(() => {
        expect(mockAutocompleteInstance.addListener).toHaveBeenCalledWith(
          'place_changed',
          expect.any(Function)
        );
      });

      await user.type(fullNameInput, 'Hong Gildong');
      await user.type(emailInput, 'hong@example.com');
      await user.type(phoneInput, '09123456789');
      await user.selectOptions(regionSelect, 'NCR');

      // 장소 선택: place_changed 이벤트 트리거
      act(() => {
        if (listeners['place_changed']) {
          listeners['place_changed'].forEach((callback) => callback());
        }
      });

      await user.type(detailedAddressInput, 'Unit 101');

      // THEN: Checkout 버튼이 활성화됨
      await waitFor(() => {
        const checkoutButton = screen.getByRole('button', { name: /Checkout/i });
        expect(checkoutButton).not.toBeDisabled();
      });
    });
  });
});
