// 지역별 배송료 정보
export const SHIPPING_RATES = {
  NCR: 100,
  Luzon: 120,
  Visayas: 140,
  Mindanao: 160,
} as const;

export const SHIPPING_REGIONS = [
  { id: 'NCR', label: 'NCR', rate: SHIPPING_RATES.NCR },
  { id: 'Luzon', label: 'Luzon', rate: SHIPPING_RATES.Luzon },
  { id: 'Visayas', label: 'Visayas', rate: SHIPPING_RATES.Visayas },
  { id: 'Mindanao', label: 'Mindanao', rate: SHIPPING_RATES.Mindanao },
] as const;

export type ShippingRegionId = keyof typeof SHIPPING_RATES;
