import { fileURLToPath } from 'url';
import path from 'path';
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import dotenv from 'dotenv';

// .env 파일 로드
dotenv.config();

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(() => {
  // VITE_API_BASE_URL 환경 변수 필수 확인
  const apiBaseUrl = process.env.VITE_API_BASE_URL;
  if (!apiBaseUrl) {
    throw new Error(
      '❌ VITE_API_BASE_URL 환경 변수가 설정되지 않았습니다.\n' +
      '   .env 파일에 VITE_API_BASE_URL을 설정해주세요.\n' +
      '   예: VITE_API_BASE_URL=http://localhost:8000'
    );
  }

  return {
    server: {
      port: 3000,
      host: '0.0.0.0',
    },
    define: {
      'process.env.VITE_API_BASE_URL': JSON.stringify(apiBaseUrl),
    },
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, 'src'),
      },
    },
  };
});
