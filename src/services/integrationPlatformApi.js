import { apiClient } from './api.js';

export const integrationPlatformApi = {
  listProviders: (category = null) => {
    const url = category ? `/integration-platform/providers?category=${encodeURIComponent(category)}` : '/integration-platform/providers';
    return apiClient.get(url);
  },

  listMarketplaceListings: (category = null) => {
    const url = category ? `/integration-platform/marketplace/listings?category=${encodeURIComponent(category)}` : '/integration-platform/marketplace/listings';
    return apiClient.get(url);
  },

  installMarketplaceApp: (listingId, workspaceId, grantedScopes = ['tasks:read'], consentConfirmed = true) =>
    apiClient.post('/integration-platform/marketplace/install', {
      listing_id: listingId,
      workspace_id: workspaceId,
      granted_scopes: grantedScopes,
      consent_confirmed: consentConfirmed,
    }),

  listWorkspaceInstallations: (workspaceId) =>
    apiClient.get(`/integration-platform/marketplace/installations?workspace_id=${workspaceId}`),

  listConnectors: (workspaceId) =>
    apiClient.get(`/integration-platform/connectors?workspace_id=${workspaceId}`),

  connectConnector: (providerId, workspaceId, accountIdentifier = null) => {
    const query = new URLSearchParams({
      provider_id: providerId,
      workspace_id: workspaceId.toString(),
    });
    if (accountIdentifier) query.append('account_identifier', accountIdentifier);
    return apiClient.post(`/integration-platform/connectors/connect?${query.toString()}`);
  },

  disconnectConnector: (connectorId) =>
    apiClient.post(`/integration-platform/connectors/${connectorId}/disconnect`),

  testWebhookDelivery: (targetUrl, secretKey, eventType = 'task.created', customPayload = null) =>
    apiClient.post('/integration-platform/webhooks/test', {
      target_url: targetUrl,
      secret_key: secretKey,
      event_type: eventType,
      custom_payload: customPayload,
    }),

  getPlatformAnalytics: () => apiClient.get('/integration-platform/analytics'),
};
