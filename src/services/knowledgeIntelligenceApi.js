import { apiClient } from './api.js';

export const knowledgeIntelligenceApi = {
  getOverview: (workspaceId = null) => {
    const url = workspaceId ? `/knowledge/overview?workspace_id=${workspaceId}` : '/knowledge/overview';
    return apiClient.get(url);
  },

  listDocuments: (params = {}) => {
    const query = new URLSearchParams();
    if (params.workspaceId) query.append('workspace_id', params.workspaceId);
    if (params.category) query.append('category', params.category);
    if (params.documentType) query.append('document_type', params.documentType);
    if (params.status) query.append('status', params.status);
    const qs = query.toString();
    return apiClient.get(`/knowledge/documents${qs ? `?${qs}` : ''}`);
  },
  getDocument: (docId) => apiClient.get(`/knowledge/documents/${docId}`),
  createDocument: (data) => apiClient.post('/knowledge/documents', data),
  updateDocument: (docId, data) => apiClient.patch(`/knowledge/documents/${docId}`, data),
  deleteDocument: (docId) => apiClient.delete(`/knowledge/documents/${docId}`),
  getDocumentVersions: (docId) => apiClient.get(`/knowledge/documents/${docId}/versions`),

  listCollections: (workspaceId = null) => {
    const url = workspaceId ? `/knowledge/collections?workspace_id=${workspaceId}` : '/knowledge/collections';
    return apiClient.get(url);
  },
  createCollection: (data) => apiClient.post('/knowledge/collections', data),

  getGraph: (entityType = null) => {
    const url = entityType ? `/knowledge/graph?entity_type=${entityType}` : '/knowledge/graph';
    return apiClient.get(url);
  },
  createGraphEntity: (data) => apiClient.post('/knowledge/graph/entities', data),
  createGraphRelationship: (data) => apiClient.post('/knowledge/graph/relationships', data),

  semanticSearch: (query, workspaceId = null, category = null) =>
    apiClient.post('/knowledge/search', { query, workspace_id: workspaceId, category }),

  queryAiAssistant: (question, workspaceId = null) =>
    apiClient.post('/knowledge/assistant/query', { question, workspace_id: workspaceId }),

  listMemories: (memoryType = null) => {
    const url = memoryType ? `/knowledge/memories?memory_type=${memoryType}` : '/knowledge/memories';
    return apiClient.get(url);
  },
  createMemory: (data) => apiClient.post('/knowledge/memories', data),

  listGaps: (status = null) => {
    const url = status ? `/knowledge/gaps?status=${status}` : '/knowledge/gaps';
    return apiClient.get(url);
  },
  createGap: (data) => apiClient.post('/knowledge/gaps', data),
  updateGap: (gapId, data) => apiClient.patch(`/knowledge/gaps/${gapId}`, data),
};
