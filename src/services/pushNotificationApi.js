import { apiClient } from './api';

export const pushNotificationApi = {
  getPublicKey: () => apiClient.get('/push/public-key'),
  subscribe: (subscription, deviceInfo) => {
    const key = subscription.getKey ? subscription.getKey('p256dh') : null;
    const auth = subscription.getKey ? subscription.getKey('auth') : null;
    return apiClient.post('/push/subscribe', {
      endpoint: subscription.endpoint,
      p256dh: key ? btoa(String.fromCharCode.apply(null, new Uint8Array(key))) : 'mock_p256dh',
      auth: auth ? btoa(String.fromCharCode.apply(null, new Uint8Array(auth))) : 'mock_auth',
      device_info: deviceInfo || navigator.userAgent,
    });
  },
  unsubscribe: (endpoint) => apiClient.delete(`/push/unsubscribe?endpoint=${encodeURIComponent(endpoint)}`),
  testPush: (title, message) => apiClient.post('/push/test', { title, message }),
};
