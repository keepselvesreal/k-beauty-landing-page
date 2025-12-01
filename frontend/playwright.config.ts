import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

// .env 파일 로드
dotenv.config();

/**
 * Playwright E2E 테스트 설정
 * 실제 브라우저 환경에서 Google Places API 통합 테스트 수행
 */
export default defineConfig({
  // 테스트 디렉토리
  testDir: './tests/e2e',

  // 각 테스트 최대 실행 시간 (Google API 로드 대기 포함)
  timeout: 60000,

  // 병렬 실행 설정
  fullyParallel: true,

  // CI 환경에서 재시도
  retries: process.env.CI ? 2 : 0,

  // 워커 수
  workers: process.env.CI ? 1 : undefined,

  // 리포터 설정
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report' }],
  ],

  // 모든 프로젝트에 공통 설정
  use: {
    // 베이스 URL (로컬 개발 서버)
    baseURL: 'http://localhost:3000',

    // 스크린샷 (실패 시에만)
    screenshot: 'only-on-failure',

    // 비디오 (실패 시에만)
    video: 'retain-on-failure',

    // 트레이스 (실패 시에만)
    trace: 'on-first-retry',
  },

  // 브라우저 프로젝트 설정
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // 개발 서버 설정 (테스트 실행 전 자동으로 시작)
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
