import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Copy, CheckCircle } from 'lucide-react';
import { Order, Customer } from '../types';
import { API_BASE_URL, PRODUCT } from '../constants';

interface OrderConfirmationProps {
  orderNumber: string;
}

const OrderConfirmation: React.FC<OrderConfirmationProps> = ({ orderNumber }) => {
  const { t } = useTranslation();
  const [order, setOrder] = useState<Order | null>(null);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchOrder();
  }, [orderNumber]);

  const fetchOrder = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/orders/${orderNumber}`);

      if (!response.ok) {
        throw new Error('Failed to fetch order');
      }

      const data = await response.json();
      setOrder(data);
      setCustomer(data.customer);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getOrderStatus = (): string => {
    if (!order) return '';

    // 취소됨
    if (order.cancellation_status === 'cancelled') {
      return t('cancelled');
    }

    // 취소 요청 중
    if (order.cancellation_status === 'cancel_requested') {
      return t('requested');
    }

    // 환불됨
    if (order.refund_status === 'refunded') {
      return t('refunded');
    }

    // 환불 요청 중
    if (order.refund_status === 'refund_requested') {
      return t('requested');
    }

    // 배송 상태 기반
    switch (order.shipping_status) {
      case 'delivered':
        return t('delivered');
      case 'shipped':
        return t('shipped');
      case 'preparing':
        return t('preparing');
      default:
        return t('preparing');
    }
  };

  const getStatusColor = (): string => {
    const status = getOrderStatus();
    if (status === t('cancelled') || status === t('refunded')) return 'text-red-600';
    if (status === t('delivered')) return 'text-green-600';
    return 'text-blue-600';
  };

  const copyUrl = () => {
    const url = `${window.location.origin}/order-confirmation/${orderNumber}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 3000);
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-PH', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">{t('orderConfirmation')}...</p>
      </div>
    );
  }

  if (error || !order || !customer) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-red-600">{error || 'Order not found'}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white py-12 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">{t('orderConfirmation')}</h1>
        </div>

        {/* Save URL Section */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
          <p className="text-sm text-gray-700 mb-4">{t('saveOrderUrl')}</p>

          <div className="bg-white border border-gray-300 rounded p-3 mb-4 break-all text-sm text-gray-600">
            {`${window.location.origin}/order-confirmation/${orderNumber}`}
          </div>

          <button
            onClick={copyUrl}
            className="flex items-center gap-2 bg-[#C49A9A] text-white px-4 py-2 rounded-md hover:bg-[#b08585] transition-colors w-full justify-center"
          >
            <Copy size={16} />
            {t('copyUrl')}
          </button>

          {copied && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded">
              <p className="text-sm text-green-800">
                ✅ {t('urlCopied')}
              </p>
              <p className="text-sm text-green-700 mt-2">{t('pasteToSave')}</p>
            </div>
          )}
        </div>

        {/* Order Information */}
        <div className="border-t border-gray-200 pt-6 mb-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4">{t('orderInformation')}</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-gray-600">{t('orderNumber')}:</span>
              <span className="text-gray-900 font-medium">{order.order_number}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">{t('orderDate')}:</span>
              <span className="text-gray-900">{formatDate(order.created_at)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">{t('status')}:</span>
              <span className={`font-medium ${getStatusColor()}`}>⬤ {getOrderStatus()}</span>
            </div>

            {/* Action Buttons */}
            <div className="pt-4 border-t border-gray-100 space-y-3">
              {/* Cancel Request Button */}
              <div>
                <button
                  className={`w-full px-4 py-2 rounded-md transition-colors text-sm font-medium ${
                    order.shipping_status === 'shipped' ||
                    order.shipping_status === 'delivered' ||
                    order.cancellation_status === 'cancelled' ||
                    order.cancellation_status === 'cancel_requested'
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-[#C49A9A] text-white hover:bg-[#b08585]'
                  }`}
                  disabled={
                    order.shipping_status === 'shipped' ||
                    order.shipping_status === 'delivered' ||
                    order.cancellation_status === 'cancelled' ||
                    order.cancellation_status === 'cancel_requested'
                  }
                >
                  {t('cancelRequest')}
                </button>
                {(order.shipping_status === 'shipped' ||
                  order.shipping_status === 'delivered') && (
                  <p className="text-xs text-gray-600 mt-1">
                    ℹ️ Cancellation is only available before your order is shipped.
                  </p>
                )}
                {order.cancellation_status === 'cancel_requested' && (
                  <p className="text-xs text-yellow-600 mt-1">
                    ⏳ Your cancellation request is pending approval.
                  </p>
                )}
                {order.cancellation_status === 'cancelled' && (
                  <p className="text-xs text-green-600 mt-1">
                    ✓ Your order has been cancelled.
                  </p>
                )}
              </div>

              {/* Refund Request Button */}
              <div>
                <button
                  className={`w-full px-4 py-2 rounded-md transition-colors text-sm font-medium ${
                    order.shipping_status !== 'delivered' ||
                    order.refund_status === 'refund_requested' ||
                    order.refund_status === 'refunded'
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-[#C49A9A] text-white hover:bg-[#b08585]'
                  }`}
                  disabled={
                    order.shipping_status !== 'delivered' ||
                    order.refund_status === 'refund_requested' ||
                    order.refund_status === 'refunded'
                  }
                >
                  {t('refundRequest')}
                </button>
                {order.shipping_status !== 'delivered' && (
                  <p className="text-xs text-gray-600 mt-1">
                    ℹ️ Refund requests are available after your order has been delivered.
                  </p>
                )}
                {order.refund_status === 'refund_requested' && (
                  <p className="text-xs text-yellow-600 mt-1">
                    ⏳ Your refund request is pending approval.
                  </p>
                )}
                {order.refund_status === 'refunded' && (
                  <p className="text-xs text-green-600 mt-1">
                    ✓ Your refund has been processed.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Customer Information */}
        <div className="border-t border-gray-200 pt-6 mb-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4">{t('customerInformation')}</h2>
          <div className="space-y-3">
            <div>
              <span className="text-gray-600 text-sm">{t('name')}</span>
              <p className="text-gray-900">{customer.name}</p>
            </div>
            <div>
              <span className="text-gray-600 text-sm">{t('email')}</span>
              <p className="text-gray-900">{customer.email}</p>
            </div>
            <div>
              <span className="text-gray-600 text-sm">{t('phoneNumber')}</span>
              <p className="text-gray-900">{customer.phone}</p>
            </div>
            <div>
              <span className="text-gray-600 text-sm">{t('region')}</span>
              <p className="text-gray-900">{customer.region}</p>
            </div>
            <div>
              <span className="text-gray-600 text-sm">{t('address')}</span>
              <p className="text-gray-900">{customer.address}</p>
            </div>
          </div>
        </div>

        {/* Order Summary */}
        <div className="border-t border-gray-200 pt-6 mb-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4">{t('orderSummary')}</h2>
          <div className="space-y-3">
            <div className="space-y-2">
              <p className="text-gray-700 font-medium">{PRODUCT.name}</p>
              <div className="flex justify-between text-sm text-gray-600">
                <span>{t('quantity')}:</span>
                <span>{order.order_items && order.order_items.length > 0 ? order.order_items[0].quantity : 1}</span>
              </div>
              <div className="flex justify-between text-sm text-gray-600">
                <span>{t('unitPrice')}:</span>
                <span>{PRODUCT.currency}{PRODUCT.price}</span>
              </div>
            </div>

            <div className="border-t border-gray-100 pt-3 flex justify-between">
              <span className="text-gray-600 font-semibold">{t('subtotal')}</span>
              <span className="font-semibold text-[#C49A9A]">{PRODUCT.currency}{Number(order.subtotal).toFixed(2)}</span>
            </div>

            <div className="flex justify-between">
              <span className="text-gray-600">{t('shippingFee')}</span>
              <span className="font-semibold text-[#C49A9A]">{PRODUCT.currency}{Number(order.shipping_fee).toFixed(2)}</span>
            </div>

            <div className="border-t border-gray-100 pt-3 flex justify-between items-center">
              <span className="text-lg font-bold text-gray-900">{t('total')}</span>
              <span className="text-2xl font-bold text-[#C49A9A]">{PRODUCT.currency}{Number(order.total_price).toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Request Status */}
        <div className="border-t border-gray-200 pt-6 mb-6">
          <h2 className="text-lg font-bold text-gray-800 mb-4">{t('requestStatus')}</h2>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">{t('cancellationStatus')}:</span>
              <span className="text-gray-900 font-medium">
                {order.cancellation_status === 'cancel_requested'
                  ? `⏳ ${t('requested')}`
                  : order.cancellation_status === 'cancelled'
                    ? `✓ ${t('cancelled')}`
                    : t('noRequest')}
              </span>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-gray-600">{t('refundStatus')}:</span>
              <span className="text-gray-900 font-medium">
                {order.refund_status === 'refund_requested'
                  ? `⏳ ${t('requested')}`
                  : order.refund_status === 'refunded'
                    ? `✓ ${t('refunded')}`
                    : t('noRequest')}
              </span>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

export default OrderConfirmation;
