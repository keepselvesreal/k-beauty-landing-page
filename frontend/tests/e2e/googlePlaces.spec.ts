import { test, expect } from '@playwright/test';

/**
 * @file googlePlaces.spec.ts
 * @description Google Places API E2E 통합 테스트
 *
 * 목적:
 * - 실제 브라우저 환경에서 Google Places API가 정상적으로 작동하는지 확인
 */

test.describe('OrderForm - Google Places API E2E 테스트', () => {
  test.beforeEach(async ({ page }) => {
    // OrderForm 페이지로 이동
    await page.goto('/');

    // Google Maps API 로드 대기
    await page.waitForFunction(
      () => {
        return (
          (window as any).google &&
          (window as any).google.maps &&
          (window as any).google.maps.places
        );
      },
      { timeout: 30000 }
    );

    console.log('✅ Google Maps API 로드 완료');
  });

  /**
   * TC-E2E.1: 실제 주소 검색 및 선택
   *
   * Given: OrderForm 페이지가 로드되고 Google Places API가 준비됨
   * When: "Manila"를 검색하고 자동완성 결과를 선택
   * Then: formState.address가 선택한 주소로 업데이트됨
   */
  test('TC-E2E.1: Manila 검색 후 자동완성 결과 선택 시 주소가 업데이트되어야 한다', async ({
    page,
  }) => {
    // ============================================
    // Given: 주소 입력 필드가 활성화되어 있음
    // ============================================
    const addressInput = page.getByPlaceholder(/Search with Google Places/i);
    await expect(addressInput).toBeEnabled({ timeout: 10000 });

    // 초기 상태 확인 (주소 필드가 비어있음)
    const initialValue = await addressInput.inputValue();
    expect(initialValue).toBe('');
    console.log('✅ Given: 주소 입력 필드가 비어있는 상태로 준비됨');

    // ============================================
    // When: "Manila"를 검색하고 첫 번째 자동완성 결과를 선택
    // ============================================

    // 1. "Manila" 입력 (type 사용으로 타이핑 이벤트 발생)
    await addressInput.type('Manila', { delay: 100 });
    console.log('✅ When: "Manila" 입력 완료');

    // 2. 자동완성 항목이 표시될 때까지 대기
    // Google Places API 응답 시간이 가변적이므로 충분한 시간 할당
    await page.waitForFunction(
      () => {
        const items = document.querySelectorAll('.pac-item');
        return items.length > 0 && (items[0] as HTMLElement).offsetParent !== null;
      },
      { timeout: 15000 }
    );
    console.log('✅ When: 자동완성 드롭다운 표시됨');

    // 3. 첫 번째 자동완성 결과가 필리핀 주소인지 확인
    const firstSuggestion = page.locator('.pac-item').first();
    const suggestionText = await firstSuggestion.textContent();
    expect(suggestionText).toContain('Philippines');
    console.log('✅ When: 첫 번째 결과가 필리핀 주소임 확인:', suggestionText);

    // 4. 첫 번째 자동완성 항목을 클릭 (force click으로 포인터 이벤트 무시)
    try {
      await firstSuggestion.click({ force: true, timeout: 5000 });
      console.log('✅ When: 자동완성 항목 클릭 완료 (force click)');
    } catch (error) {
      // force click 실패 시 JavaScript로 직접 click 이벤트 발생
      await page.evaluate(() => {
        const item = document.querySelector('.pac-item') as HTMLElement;
        if (item) {
          item.click();
        }
      });
      console.log('✅ When: 자동완성 항목 클릭 완료 (JavaScript click)');
    }

    // ============================================
    // Then: formState.address가 업데이트되어야 함
    // ============================================

    // 주소 필드가 업데이트될 때까지 대기
    // Google Places place_changed 이벤트가 비동기적으로 발생하므로 시간 할당
    await page.waitForFunction(
      (selector) => {
        const input = document.querySelector(selector) as HTMLInputElement;
        // input 값이 업데이트되고, "Manila"보다 길어야 함 (formatted_address 로드됨)
        return input && input.value.length > 10 && input.value !== 'Manila';
      },
      'input[name="address"]',
      { timeout: 10000 }
    );

    // formState.address가 올바르게 업데이트되었는지 검증
    const updatedValue = await addressInput.inputValue();
    expect(updatedValue).not.toBe(''); // 비어있지 않음
    expect(updatedValue).not.toBe('Manila'); // 단순 입력값이 아님
    expect(updatedValue).toContain('Manila'); // Manila 포함
    expect(updatedValue).toContain('Philippines'); // Philippines 포함
    console.log('✅ Then: 주소 필드가 정상적으로 업데이트됨:', updatedValue);
    console.log('🎉 TC-E2E.1 테스트 완료!');
  });

  /**
   * TC-E2E.2: 여러 지역 연속 검색
   *
   * Given: OrderForm 페이지가 로드되고 Google Places API가 준비됨
   * When: Cebu를 검색하고 선택한 후, 필드를 초기화하고 Davao를 검색하고 선택
   * Then: 각 검색 후 formState.address가 올바르게 업데이트됨
   */
  test('TC-E2E.2: 여러 지역을 연속으로 검색하고 선택할 수 있어야 한다', async ({
    page,
  }) => {
    const addressInput = page.getByPlaceholder(/Search with Google Places/i);
    await expect(addressInput).toBeEnabled({ timeout: 10000 });

    // ============================================
    // When (1): Cebu 검색 및 선택
    // ============================================
    await addressInput.type('Cebu', { delay: 100 });
    console.log('✅ When: "Cebu" 입력 완료');

    // 자동완성 항목 대기
    await page.waitForFunction(
      () => {
        const items = document.querySelectorAll('.pac-item');
        return items.length > 0 && (items[0] as HTMLElement).offsetParent !== null;
      },
      { timeout: 15000 }
    );

    const cebuSuggestion = page.locator('.pac-item').first();
    await cebuSuggestion.click({ force: true, timeout: 5000 }).catch(() => {
      page.evaluate(() => {
        const item = document.querySelector('.pac-item') as HTMLElement;
        if (item) item.click();
      });
    });

    // Cebu 주소가 업데이트될 때까지 대기
    await page.waitForFunction(
      (selector) => {
        const input = document.querySelector(selector) as HTMLInputElement;
        return input && input.value.length > 10 && input.value !== 'Cebu';
      },
      'input[name="address"]',
      { timeout: 10000 }
    );

    const cebuAddress = await addressInput.inputValue();
    expect(cebuAddress).toContain('Cebu');
    expect(cebuAddress).toContain('Philippines');
    console.log('✅ Then: Cebu 주소 업데이트됨:', cebuAddress);

    // ============================================
    // When (2): 필드 초기화 후 Davao 검색
    // ============================================
    await addressInput.clear();
    await page.waitForTimeout(500); // 초기화 안정화
    console.log('✅ When: 주소 필드 초기화 완료');

    await addressInput.type('Davao', { delay: 100 });
    console.log('✅ When: "Davao" 입력 완료');

    // 자동완성 항목 대기
    await page.waitForFunction(
      () => {
        const items = document.querySelectorAll('.pac-item');
        return items.length > 0 && (items[0] as HTMLElement).offsetParent !== null;
      },
      { timeout: 15000 }
    );

    const davaoSuggestion = page.locator('.pac-item').first();
    await davaoSuggestion.click({ force: true, timeout: 5000 }).catch(() => {
      page.evaluate(() => {
        const item = document.querySelector('.pac-item') as HTMLElement;
        if (item) item.click();
      });
    });

    // Davao 주소가 업데이트될 때까지 대기
    await page.waitForFunction(
      (selector) => {
        const input = document.querySelector(selector) as HTMLInputElement;
        return input && input.value.length > 10 && input.value !== 'Davao';
      },
      'input[name="address"]',
      { timeout: 10000 }
    );

    const davaoAddress = await addressInput.inputValue();
    expect(davaoAddress).toContain('Davao');
    expect(davaoAddress).toContain('Philippines');
    console.log('✅ Then: Davao 주소 업데이트됨:', davaoAddress);
    console.log('🎉 TC-E2E.2 테스트 완료!');
  });

  /**
   * TC-E2E.3: 필리핀 지역 제약 검증
   *
   * Given: OrderForm 페이지가 로드되고 Google Places API가 준비됨
   * When: "Sydney" (호주)를 검색
   * Then: 필리핀 주소만 반환되는지 확인
   */
  test('TC-E2E.3: 필리핀 외 국가 검색 시 필리핀 주소만 반환되어야 한다', async ({
    page,
  }) => {
    const addressInput = page.getByPlaceholder(/Search with Google Places/i);
    await expect(addressInput).toBeEnabled({ timeout: 10000 });

    // ============================================
    // When: Sydney (호주) 검색
    // ============================================
    await addressInput.type('Sydney', { delay: 100 });
    console.log('✅ When: "Sydney" 입력 완료');

    // 자동완성 항목 대기
    await page.waitForFunction(
      () => {
        const items = document.querySelectorAll('.pac-item');
        return items.length > 0 && (items[0] as HTMLElement).offsetParent !== null;
      },
      { timeout: 15000 }
    );

    // ============================================
    // Then: 모든 결과가 필리핀 주소인지 확인
    // ============================================
    const suggestions = page.locator('.pac-item');
    const suggestionCount = await suggestions.count();
    console.log(`✅ Then: ${suggestionCount}개의 자동완성 결과 발견`);

    for (let i = 0; i < Math.min(suggestionCount, 5); i++) {
      const text = await suggestions.nth(i).textContent();
      expect(text).toContain('Philippines');
      console.log(`  ✓ 항목 ${i + 1}: ${text}`);
    }

    console.log('🎉 TC-E2E.3 테스트 완료!');
  });

  /**
   * TC-E2E.4: 전체 폼 제출 흐름
   *
   * Given: OrderForm 페이지가 로드되고 모든 필드가 준비됨
   * When: 모든 필드를 입력하고 Google Places 주소를 선택
   * Then: Checkout 버튼이 활성화됨
   */
  test('TC-E2E.4: 모든 필드를 입력하고 주소를 선택하면 Checkout 버튼이 활성화되어야 한다', async ({
    page,
  }) => {
    // ============================================
    // Given: 모든 필드가 활성화되어 있음
    // ============================================
    await expect(page.getByPlaceholder(/Search with Google Places/i)).toBeEnabled({
      timeout: 10000,
    });

    const fullNameInput = page.locator('input[name="fullName"]');
    const emailInput = page.locator('input[name="email"]');
    const phoneInput = page.locator('input[name="phone"]');
    const addressInput = page.getByPlaceholder(/Search with Google Places/i);
    const detailedAddressInput = page.locator('textarea[name="detailedAddress"]');
    const checkoutButton = page.getByRole('button', { name: /Checkout/i });

    // 초기 상태: Checkout 버튼이 비활성화되어 있어야 함
    await expect(checkoutButton).toBeDisabled();
    console.log('✅ Given: Checkout 버튼이 초기 상태에서 비활성화됨');

    // ============================================
    // When: 모든 필드 입력
    // ============================================

    // 1. 이름 입력
    await fullNameInput.type('John Doe', { delay: 50 });
    console.log('✅ When: 이름 입력 완료');

    // 2. 이메일 입력
    await emailInput.type('john@example.com', { delay: 50 });
    console.log('✅ When: 이메일 입력 완료');

    // 3. 전화번호 입력 (필리핀 형식)
    await phoneInput.type('09123456789', { delay: 50 });
    console.log('✅ When: 전화번호 입력 완료');

    // 4. 주소 검색 및 선택
    await addressInput.type('Manila', { delay: 100 });
    console.log('✅ When: "Manila" 입력 완료');

    // 자동완성 대기
    await page.waitForFunction(
      () => {
        const items = document.querySelectorAll('.pac-item');
        return items.length > 0 && (items[0] as HTMLElement).offsetParent !== null;
      },
      { timeout: 15000 }
    );

    const addressSuggestion = page.locator('.pac-item').first();
    await addressSuggestion.click({ force: true, timeout: 5000 }).catch(() => {
      page.evaluate(() => {
        const item = document.querySelector('.pac-item') as HTMLElement;
        if (item) item.click();
      });
    });

    // 주소 업데이트 대기
    await page.waitForFunction(
      (selector) => {
        const input = document.querySelector(selector) as HTMLInputElement;
        return input && input.value.length > 10 && input.value !== 'Manila';
      },
      'input[name="address"]',
      { timeout: 10000 }
    );
    console.log('✅ When: 주소 선택 완료');

    // 5. 상세 주소 입력
    await detailedAddressInput.type('Unit 101, Building A', { delay: 50 });
    console.log('✅ When: 상세 주소 입력 완료');

    // ============================================
    // Then: Checkout 버튼이 활성화되어야 함
    // ============================================
    await expect(checkoutButton).toBeEnabled({ timeout: 5000 });
    console.log('✅ Then: Checkout 버튼이 활성화됨');

    // 최종 입력값 확인
    const finalValues = {
      fullName: await fullNameInput.inputValue(),
      email: await emailInput.inputValue(),
      phone: await phoneInput.inputValue(),
      address: await addressInput.inputValue(),
      detailedAddress: await detailedAddressInput.inputValue(),
    };

    console.log('✅ Then: 최종 입력값 확인:', finalValues);
    console.log('🎉 TC-E2E.4 테스트 완료!');
  });
});
