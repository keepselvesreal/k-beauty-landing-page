/**
 * @file exceptions.ts
 * @description 프런트엔드 커스텀 예외 클래스
 *
 * 백엔드와 동일한 패턴으로 에러 코드 + 메시지 구조 사용
 */

/**
 * 기본 애플리케이션 에러
 *
 * @example
 * throw new AppError('API_KEY_MISSING', '주소 검색 기능을 사용할 수 없습니다.');
 */
export class AppError extends Error {
  constructor(
    public code: string,
    public message: string,
    public statusCode?: number,
  ) {
    super(message);
    this.name = this.constructor.name;
    Object.setPrototypeOf(this, AppError.prototype);
  }
}

/**
 * Google Places API 관련 에러
 */
export class GooglePlacesError extends AppError {
  constructor(code: string, message: string) {
    super(code, message);
    Object.setPrototypeOf(this, GooglePlacesError.prototype);
  }
}

/**
 * 고객 생성 관련 에러
 */
export class CustomerError extends AppError {
  constructor(code: string, message: string) {
    super(code, message);
    Object.setPrototypeOf(this, CustomerError.prototype);
  }
}

/**
 * 주문 생성 관련 에러
 */
export class OrderError extends AppError {
  constructor(code: string, message: string) {
    super(code, message);
    Object.setPrototypeOf(this, OrderError.prototype);
  }
}

/**
 * 결제 관련 에러
 */
export class PaymentError extends AppError {
  constructor(code: string, message: string) {
    super(code, message);
    Object.setPrototypeOf(this, PaymentError.prototype);
  }
}

/**
 * 에러 코드 상수 (백엔드와 동일하게 유지)
 */
export const ErrorCodes = {
  // Google Places API
  GOOGLE_PLACES_API_NOT_LOADED: 'GOOGLE_PLACES_API_NOT_LOADED',
  GOOGLE_PLACES_INVALID_PLACE: 'GOOGLE_PLACES_INVALID_PLACE',
  GOOGLE_PLACES_NETWORK_ERROR: 'GOOGLE_PLACES_NETWORK_ERROR',
  GOOGLE_PLACES_TIMEOUT: 'GOOGLE_PLACES_TIMEOUT',

  // 고객
  CUSTOMER_CREATION_FAILED: 'CUSTOMER_CREATION_FAILED',
  CUSTOMER_INVALID_EMAIL: 'CUSTOMER_INVALID_EMAIL',

  // 주문
  ORDER_CREATION_FAILED: 'ORDER_CREATION_FAILED',
  ORDER_INSUFFICIENT_INVENTORY: 'ORDER_INSUFFICIENT_INVENTORY',

  // 결제
  PAYMENT_PROCESSING_FAILED: 'PAYMENT_PROCESSING_FAILED',
  PAYMENT_INVALID_AMOUNT: 'PAYMENT_INVALID_AMOUNT',

  // 네트워크
  NETWORK_ERROR: 'NETWORK_ERROR',
  NETWORK_TIMEOUT: 'NETWORK_TIMEOUT',
};

/**
 * 에러 메시지 상수 (사용자 친화적)
 */
export const ErrorMessages = {
  // Google Places API
  GOOGLE_PLACES_API_NOT_LOADED: '주소 검색 기능을 설정할 수 없습니다. 관리자에게 문의하세요.',
  GOOGLE_PLACES_INVALID_PLACE: '정확한 주소를 선택해주세요.',
  GOOGLE_PLACES_NETWORK_ERROR: '네트워크 오류가 발생했습니다. 수동으로 주소를 입력하거나 다시 시도하세요.',
  GOOGLE_PLACES_TIMEOUT: '주소 검색 시간 초과. 수동으로 주소를 입력해주세요.',

  // 고객
  CUSTOMER_CREATION_FAILED: '고객 정보 저장에 실패했습니다.',
  CUSTOMER_INVALID_EMAIL: '유효한 이메일 주소를 입력해주세요.',

  // 주문
  ORDER_CREATION_FAILED: '주문 생성에 실패했습니다.',
  ORDER_INSUFFICIENT_INVENTORY: '죄송합니다. 재고가 부족합니다.',

  // 결제
  PAYMENT_PROCESSING_FAILED: '결제 처리에 실패했습니다. 다시 시도해주세요.',
  PAYMENT_INVALID_AMOUNT: '유효한 금액을 입력해주세요.',

  // 네트워크
  NETWORK_ERROR: '네트워크 오류가 발생했습니다.',
  NETWORK_TIMEOUT: '요청 시간이 초과되었습니다.',
};

/**
 * 에러 헬퍼 함수
 */
export const createErrorMessage = (code: keyof typeof ErrorMessages): string => {
  return ErrorMessages[code] || '알 수 없는 오류가 발생했습니다.';
};

/**
 * API 응답 에러를 AppError로 변환
 *
 * @example
 * try {
 *   const response = await fetch('/api/customers');
 *   if (!response.ok) {
 *     throw parseApiError(response);
 *   }
 * } catch (error) {
 *   if (error instanceof AppError) {
 *     console.error(error.code, error.message);
 *   }
 * }
 */
export const parseApiError = (
  response: Response,
  fallbackCode: string = 'API_ERROR',
): AppError => {
  const statusCode = response.status;
  const statusText = response.statusText;

  // HTTP 상태 코드에 따른 기본 에러 코드 매핑
  let code = fallbackCode;

  if (statusCode === 400) {
    code = 'BAD_REQUEST';
  } else if (statusCode === 401) {
    code = 'UNAUTHORIZED';
  } else if (statusCode === 403) {
    code = 'FORBIDDEN';
  } else if (statusCode === 404) {
    code = 'NOT_FOUND';
  } else if (statusCode === 422) {
    code = 'VALIDATION_ERROR';
  } else if (statusCode === 500) {
    code = 'SERVER_ERROR';
  }

  const message = `API Error: ${statusCode} ${statusText}`;

  return new AppError(code, message, statusCode);
};
