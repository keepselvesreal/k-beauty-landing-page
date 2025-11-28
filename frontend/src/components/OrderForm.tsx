import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Minus, Plus } from 'lucide-react';
import { PRODUCT, REGIONS } from '../constants';
import { OrderFormState, FormErrors } from '../types';

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

const OrderForm: React.FC = () => {
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

      const autocomplete = new (window as any).google.maps.places.Autocomplete(
        addressInputRef.current,
        {
          types: ['geocode'],
          componentRestrictions: { country: 'ph' },
        }
      );

      // place_changed 이벤트 리스너
      autocomplete.addListener('place_changed', () => {
        const place = autocomplete.getPlace();
        if (!place.geometry || !place.place_id) return;

        // place_id를 window 객체에 저장 (테스트에서 접근 가능)
        (window as any).selectedPlaceId = place.place_id;

        // 주소 필드 업데이트
        setFormState((prev) => ({
          ...prev,
          address: place.formatted_address || '',
        }));
      });
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
      const orderData = createOrderPayload();

      const response = await fetch('/api/orders/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(orderData),
      });

      if (!response.ok) {
        throw new Error(`API 호출 실패: ${response.statusText}`);
      }

      const result = await response.json();
      // eslint-disable-next-line no-console
      console.log('주문 생성 성공:', result);
      // TODO: 결제 페이지로 리디렉션 또는 다음 단계로 진행
    } catch (error) {
      // eslint-disable-next-line no-console
      console.error('주문 생성 중 오류 발생:', error);
      // TODO: 사용자에게 에러 메시지 표시
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
              <input
                ref={addressInputRef}
                type="text"
                name="address"
                value={formState.address}
                onChange={handleChange}
                placeholder="Search with Google Places..."
                className="w-full px-4 py-3 border border-gray-200 rounded-md focus:outline-none focus:border-[#C49A9A] focus:ring-1 focus:ring-[#C49A9A] transition-all placeholder:text-gray-300"
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
