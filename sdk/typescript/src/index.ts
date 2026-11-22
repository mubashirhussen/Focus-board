import * as crypto from 'crypto';

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: string;
  priority: string;
  category: string;
  due_date?: string;
  project_id?: number;
  user_id: number;
  created_at?: string;
  updated_at?: string;
}

export interface CreateTaskInput {
  title: string;
  description?: string;
  due_date?: string;
  priority?: 'low' | 'medium' | 'high';
  category?: string;
  project_id?: number;
}

export interface FocusBoardClientOptions {
  apiKey: string;
  baseUrl?: string;
}

export class FocusBoardClient {
  private apiKey: string;
  private baseUrl: string;

  constructor(options: FocusBoardClientOptions) {
    if (!options.apiKey) {
      throw new Error('FocusBoard API Key is required');
    }
    this.apiKey = options.apiKey;
    this.baseUrl = (options.baseUrl || 'http://localhost:8000/api/v1/public/v1').replace(/\/+$/, '');
  }

  private async request<T>(method: string, path: string, body?: any, headers?: Record<string, string>): Promise<T> {
    const url = `${this.baseUrl}/${path.replace(/^\/+/, '')}`;
    const reqHeaders: Record<string, string> = {
      'X-API-Key': this.apiKey,
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      ...headers,
    };

    const res = await fetch(url, {
      method,
      headers: reqHeaders,
      body: body ? JSON.stringify(body) : undefined,
    });

    if (res.status === 204) {
      return null as any;
    }

    if (!res.ok) {
      const errorText = await res.text();
      let errorDetail = errorText;
      try {
        const parsed = JSON.parse(errorText);
        errorDetail = parsed.detail || errorText;
      } catch {}
      throw new Error(`FocusBoard API error (${res.status}): ${errorDetail}`);
    }

    return (await res.json()) as T;
  }

  async listTasks(params?: { status?: string; projectId?: number; limit?: number; offset?: number }): Promise<Task[]> {
    const query = new URLSearchParams();
    if (params?.status) query.set('status', params.status);
    if (params?.projectId) query.set('project_id', String(params.projectId));
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    return this.request<Task[]>('GET', `tasks?${query.toString()}`);
  }

  async createTask(input: CreateTaskInput, idempotencyKey?: string): Promise<Task> {
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers['Idempotency-Key'] = idempotencyKey;
    }
    return this.request<Task>('POST', 'tasks', input, headers);
  }

  async getTask(taskId: string): Promise<Task> {
    return this.request<Task>('GET', `tasks/${taskId}`);
  }

  async updateTask(taskId: string, input: Partial<CreateTaskInput> & { status?: string }): Promise<Task> {
    return this.request<Task>('PATCH', `tasks/${taskId}`, input);
  }

  async deleteTask(taskId: string): Promise<void> {
    await this.request<void>('DELETE', `tasks/${taskId}`);
  }

  async listProjects(): Promise<any[]> {
    return this.request<any[]>('GET', 'projects');
  }

  async getPortfolioAnalytics(): Promise<any> {
    return this.request<any>('GET', 'analytics/portfolio');
  }

  static verifyWebhookSignature(payloadString: string, signatureHeader: string, secretKey: string): boolean {
    try {
      const parts: Record<string, string> = {};
      signatureHeader.split(',').forEach((item) => {
        const [k, v] = item.split('=');
        if (k && v) parts[k.trim()] = v.trim();
      });

      const ts = parts['t'];
      const sig = parts['v1'];
      if (!ts || !sig) return false;

      const toSign = `${ts}.${payloadString}`;
      const expectedSig = crypto.createHmac('sha256', secretKey).update(toSign).digest('hex');
      return crypto.timingSafeEqual(Buffer.from(expectedSig), Buffer.from(sig));
    } catch {
      return false;
    }
  }
}
