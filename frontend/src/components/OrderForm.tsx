import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Minus, Plus } from 'lucide-react';
import { PRODUCT, REGIONS, API_BASE_URL } from '../constants';
import { OrderFormState, FormErrors } from '../types';
import {
  GooglePlacesError,
  CustomerError,
  OrderError,
  PaymentError,
  ErrorCodes,
  ErrorMessages,
  parseApiError,
} from '../utils/exceptions';

// Validation 함수들
const validatePhone = (phone: string) => {
  // Philippines 휴대폰 번호 형식 검증 (09XXXXXXXXX 또는 +639XXXXXXXXX)
  const phoneRegex = /^(09|\+639)\d{9}$/;
  return phoneRegex.test(phone.replace(/\s/g, ''));
};

const isFormValid = (formState: OrderFormState) => {
  return (
    formState.fullName.trim() !== '' &&
    formState.email.trim() !== '' &&
    formState.phone.trim() !== '' &&
    formState.region.trim() !== '' &&
    formState.address.trim() !== '' &&
    formState.detailedAddress.trim() !== ''
  );
};

interface OrderFormProps {
  onNavigate?: (url: string) => void;
}

const OrderForm: React.FC<OrderFormProps> = ({
  onNavigate = (url: string) => {
    window.location.href = url;
  },
}) => {
  const [quantity, setQuantity] = useState(1);
  const [formState, setFormState] = useState<OrderFormState>({
    fullName: '',
    email: '',
    phone: '',
    region: 'NCR',
    address: '',
    detailedAddress: '',
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [isLoadingAddressAPI, setIsLoadingAddressAPI] = useState(true);
  const [addressError, setAddressError] = useState<string>('');
  const addressInputRef = useRef<HTMLInputElement>(null);

  // Google Places Autocomplete 초기화
  useEffect(() => {
    if (!addressInputRef.current) return;

    // Google Maps API 로드 대기
    const checkGoogleMapsLoaded = () => {
      if (
        !(window as any).google ||
        !(window as any).google.maps ||
        !(window as any).google.maps.places
      ) {
        setTimeout(checkGoogleMapsLoaded, 100);
        return;
      }

      try {
        const autocomplete = new (window as any).google.maps.places.Autocomplete(
          addressInputRef.current,
          {
            types: ['geocode'],
            componentRestrictions: { country: 'ph' },
            language: 'en',
          }
        );

        // place_changed 이벤트 리스너
        autocomplete.addListener('place_changed', () => {
          const place = autocomplete.getPlace();
          if (!place.geometry || !place.place_id) {
            // graceful handling: 불완전한 주소는 무시하고 에러 메시지 표시
            setAddressError(ErrorMessages.GOOGLE_PLACES_INVALID_PLACE);
            return;
          }

          // 유효한 주소 선택 시 에러 메시지 제거
          setAddressError('');

          // place_id를 window 객체에 저장 (테스트에서 접근 가능)
          (window as any).selectedPlaceId = place.place_id;

          // 주소 필드 업데이트
          setFormState((prev) => ({
            ...prev,
            address: place.formatted_address || '',
          }));
        });

        // API 로드 완료
        setIsLoadingAddressAPI(false);
      } catch (error) {
        // graceful handling: API 초기화 실패 시에도 사용자가 수동으로 입력 가능
        setAddressError(ErrorMessages.GOOGLE_PLACES_API_NOT_LOADED);
        setIsLoadingAddressAPI(false);
      }
    };

    checkGoogleMapsLoaded();
  }, []);

  const productTotal = quantity * PRODUCT.price;
  // 선택한 지역에서 배송료 찾기
  const currentShippingFee = REGIONS.find((r) => r.id === formState.region)?.rate || 0;
  const totalAmount = productTotal + currentShippingFee;

  const handleQuantityChange = (delta: number) => {
    setQuantity((prev) => Math.max(1, prev + delta));
  };

  const handleBlur = (field: keyof OrderFormState) => {
    if (field === 'phone') {
      if (formState.phone && !validatePhone(formState.phone)) {
        setErrors((prev) => ({ ...prev, phone: 'Please enter a valid phone number.' }));
      } else {
        setErrors((prev) => {
          const newErrors = { ...prev };
          delete newErrors.phone;
          return newErrors;
        });
      }
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormState((prev) => ({ ...prev, [name]: value }));

    // 휴대폰 번호가 유효해지면 에러 제거
    if (name === 'phone' && validatePhone(value)) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors.phone;
        return newErrors;
      });
    }
  };

  // 폼 유효성을 메모이제이션으로 최적화
  const formIsValid = useMemo(() => isFormValid(formState), [formState]);

  // 주문 데이터를 생성하는 헬퍼 함수
  const createOrderPayload = () => {
    return {
      customer_name: formState.fullName,
      email: formState.email,
      phone: formState.phone,
      region: formState.region,
      address: formState.address,
      detailed_address: formState.detailedAddress,
    };
  };

  // Checkout 버튼 클릭 핸들러
  const handleCheckout = async () => {
    if (!formIsValid) {
      // eslint-disable-next-line no-console
      console.warn('폼이 유효하지 않습니다');
      return;
    }

    try {
      // ============================================
      // 1단계: 고객 생성 (또는 기존 고객 조회)
      // ============================================
      // eslint-disable-next-line no-console
      console.log('1단계: 고객 생성 중...');

      const customerResponse = await fetch(`${API_BASE_URL}/api/customers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formState.email,
          name: formState.fullName,
          phone: formState.phone,
          address: formState.address,
          region: formState.region,
        }),
      });

      if (!customerResponse.ok) {
        const appError = parseApiError(customerResponse, ErrorCodes.CUSTOMER_CREATION_FAILED);
        setErrors((prev) => ({
          ...prev,
          general: ErrorMessages.CUSTOMER_CREATION_FAILED,
        }));
        // eslint-disable-next-line no-console
        console.error('고객 생성 실패:', appError);
        return;
      }

      const customer = await customerResponse.json();
      // eslint-disable-next-line no-console
      console.log('고객 생성 성공:', customer);
      const customerId = customer.id;

      // ============================================
      // 2단계: 주문 생성
      // ============================================
      // eslint-disable-next-line no-console
      console.log('2단계: 주문 생성 중...');

      const PRODUCT_ID = PRODUCT.id;

      const orderResponse = await fetch(`${API_BASE_URL}/api/orders`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          customer_id: customerId,
          product_id: PRODUCT_ID,
          quantity,
          region: formState.region,
        }),
      });

      if (!orderResponse.ok) {
        const appError = parseApiError(orderResponse, ErrorCodes.ORDER_CREATION_FAILED);
        setErrors((prev) => ({
          ...prev,
          general: ErrorMessages.ORDER_CREATION_FAILED,
        }));
        // eslint-disable-next-line no-console
        console.error('주문 생성 실패:', appError);
        return;
      }

      const order = await orderResponse.json();
      // eslint-disable-next-line no-console
      console.log('주문 생성 성공:', order);
      const orderId = order.id;

      // ============================================
      // 3단계: PayPal 결제 초기화
      // ============================================
      // eslint-disable-next-line no-console
      console.log('3단계: PayPal 결제 초기화 중...');

      const paypalResponse = await fetch(`${API_BASE_URL}/api/orders/${orderId}/initiate-payment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!paypalResponse.ok) {
        const appError = parseApiError(paypalResponse, ErrorCodes.PAYMENT_PROCESSING_FAILED);
        setErrors((prev) => ({
          ...prev,
          general: ErrorMessages.PAYMENT_PROCESSING_FAILED,
        }));
        // eslint-disable-next-line no-console
        console.error('결제 초기화 실패:', appError);
        return;
      }

      const paypalData = await paypalResponse.json();
      const approvalUrl = paypalData.approval_url;

      // eslint-disable-next-line no-console
      console.log('PayPal 승인 URL:', approvalUrl);

      // ============================================
      // 4단계: 이메일 localStorage 저장
      // ============================================
      // 결제 완료 후 주문 확인 페이지에서 자동으로 인증할 수 있도록 저장
      localStorage.setItem('customer_email', formState.email);

      // eslint-disable-next-line no-console
      console.log('4단계: 고객 이메일 저장됨');

      // ============================================
      // 5단계: PayPal 리다이렉션
      // ============================================
      // eslint-disable-next-line no-console
      console.log('5단계: PayPal로 리다이렉션 중...');

      // 사용자를 PayPal 승인 페이지로 리다이렉션
      onNavigate(approvalUrl);
    } catch (error) {
      // graceful handling: 예상하지 못한 에러 처리
      const errorMessage = error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.';
      setErrors((prev) => ({
        ...prev,
        general: errorMessage,
      }));
      // eslint-disable-next-line no-console
      console.error('주문 생성 중 오류 발생:', error);
    }
  };

  return (
    <section className="max-w-6xl mx-auto px-4 py-16">
      <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">Get Yours Now</h2>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        {/* Left Column: Form Fields */}
        <div className="lg:col-span-7 space-y-10">
          {/* Order Details */}
          <div>
            <h3 className="text-lg font-bold text-gray-800 mb-6">Order Details</h3>
            <div className="flex items-center justify-between py-4 border-b border-gray-100">
              <span className="text-gray-600">Quantity</span>
              <div className="flex items-center border border-gray-200 rounded-md">
                <button
                  onClick={() => handleQuantityChange(-1)}
                  className="p-3 text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <Minus size={16} />
                </button>
                <span className="w-12 text-center font-medium text-gray-900">{quantity}</span>
                <button
                  onClick={() => handleQuantityChange(1)}
                  className="p-3 text-gray-500 hover:text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <Plus size={16} />
                </button>
              </div>
            </div>
          </div>

          {/* Customer Information */}
          <div className="space-y-6">
            <h3 className="text-lg font-bold text-gray-800">Customer Information</h3>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-600 block">Full Name</label>
              <input
                type="text"
                name="fullName"
                value={formState.fullName}
                onChange={handleChange}
                onBlur={() => handleBlur('fullName')}
                className="w-full px-4 py-3 border border-gray-200 rounded-md focus:outline-none focus:border-[#C49A9A] focus:ring-1 focus:ring-[#C49A9A] transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-600 block">Email</label>
              <input
                type="email"
                name="email"
                value={formState.email}
                onChange={handleChange}
                className="w-full px-4 py-3 border border-gray-200 rounded-md focus:outline-none focus:border-[#C49A9A] focus:ring-1 focus:ring-[#C49A9A] transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-600 block">Phone Number</label>
              <input
                type="tel"
                name="phone"
                value={formState.phone}
                onChange={handleChange}
                onBlur={() => handleBlur('phone')}
                className={`w-full px-4 py-3 border rounded-md focus:outline-none transition-all ${
                  errors.phone
                    ? 'border-red-400 focus:border-red-500 focus:ring-1 focus:ring-red-500 bg-red-50'
                    : 'border-gray-200 focus:border-[#C49A9A] focus:ring-1 focus:ring-[#C49A9A]'
                }`}
              />
              {errors.phone && (
                <p className="text-xs text-red-500 mt-1 flex items-center">{errors.phone}</p>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="region-select" className="text-sm font-medium text-gray-600 block">
                Region
              </label>
              <div className="relative">
                <select
                  id="region-select"
                  name="region"
                  value={formState.region}
                  onChange={handleChange}
                  className="w-full px-4 py-3 border border-gray-200 rounded-md appearance-none bg-white focus:outline-none focus:border-[#C49A9A] focus:ring-1 focus:ring-[#C49A9A] transition-all"
                >
                  {REGIONS.map((region) => (
                    <option key={region.id} value={region.id}>
                      {region.label} ({PRODUCT.currency}
                      {region.rate})
                    </option>
                  ))}
                </select>
                <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-gray-400">
                  <svg
                    width="10"
                    height="6"
                    viewBox="0 0 10 6"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                  >
                    <path
                      d="M1 1L5 5L9 1"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-600 block">
                Address (Street, Barangay)
              </label>

              {/* 로딩 상태 피드백 */}
              {isLoadingAddressAPI && (
                <p className="text-sm text-gray-500 flex items-center gap-1">
                  <span className="inline-block w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
                  주소 검색을 준비 중입니다...
                </p>
              )}

              {/* 에러 메시지 */}
              {addressError && (
                <p className="text-sm text-red-600 flex items-center gap-1">
                  <span>⚠️</span>
                  {addressError}
                </p>
              )}

              <input
                ref={addressInputRef}
                type="text"
                name="address"
                value={formState.address}
                onChange={handleChange}
                placeholder="Search with Google Places..."
                disabled={isLoadingAddressAPI}
                className={`
                  w-full px-4 py-3 border rounded-md focus:outline-none focus:ring-1 transition-all placeholder:text-gray-300
                  ${addressError ? 'border-red-400 bg-red-50 focus:border-red-500 focus:ring-red-500' : 'border-gray-200 focus:border-[#C49A9A] focus:ring-[#C49A9A]'}
                  ${isLoadingAddressAPI ? 'opacity-50 cursor-not-allowed' : ''}
                `}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-600 block">
                Detailed Address (Unit No., Building, etc.)
              </label>
              <textarea
                name="detailedAddress"
                value={formState.detailedAddress}
                onChange={handleChange}
                rows={4}
                className="w-full px-4 py-3 border border-gray-200 rounded-md focus:outline-none focus:border-[#C49A9A] focus:ring-1 focus:ring-[#C49A9A] transition-all resize-none"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Sticky Summary */}
        <div className="lg:col-span-5">
          <div className="bg-[#F9F5F2] p-8 rounded-2xl sticky top-24">
            <h3 className="text-lg font-bold text-gray-800 mb-6">Price Summary</h3>

            <div className="space-y-4 mb-6">
              <div className="flex justify-between text-gray-600">
                <span>Product Price</span>
                <span>
                  {PRODUCT.currency}
                  {productTotal.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Shipping Fee</span>
                <span>
                  {PRODUCT.currency}
                  {currentShippingFee.toFixed(2)}
                </span>
              </div>
            </div>

            <div className="pt-6 border-t border-gray-200 flex justify-between items-center mb-8">
              <span className="font-bold text-gray-900">Total Amount</span>
              <span className="font-bold text-xl text-[#C49A9A]">
                {PRODUCT.currency}
                {totalAmount.toFixed(2)}
              </span>
            </div>

            <button
              disabled={!formIsValid}
              onClick={handleCheckout}
              className={`w-full font-bold py-4 rounded-md transition-transform active:scale-[0.98] shadow-sm ${
                formIsValid
                  ? 'bg-[#C49A9A] text-white hover:bg-[#b08585] hover:shadow-md cursor-pointer'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Checkout
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default OrderForm;
