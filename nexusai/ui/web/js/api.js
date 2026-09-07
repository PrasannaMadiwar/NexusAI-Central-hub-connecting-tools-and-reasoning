/**
 * NexusAI Web UI - API Client
 */

const API = {
  async request(endpoint, options = {}) {
    const token = Storage.getToken();
    const headers = {
      ...options.headers
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    if (!response.ok) {
      let errorMsg = `HTTP ${response.status}: ${response.statusText}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMsg = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch (_) {}
      throw new Error(errorMsg);
    }

    return response.json();
  },

  // Health
  async getHealth() {
    return this.request('/health');
  },

  // Auth (Email & Password Login / Signup)
  async login(email, password = '') {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },

  async signup(email, password = '') {
    return this.request('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password })
    });
  },

  async getDemoToken(email = 'developer@nexusai.local') {
    return this.request(`/api/auth/demo-token?email=${encodeURIComponent(email)}`);
  },


  // User Profile
  async getMe() {
    return this.request('/api/user/me');
  },

  // Threads
  async listThreads() {
    return this.request('/api/threads');
  },

  async createThread(title = 'New Conversation') {
    return this.request('/api/threads', {
      method: 'POST',
      body: JSON.stringify({ title })
    });
  },

  async getMessages(threadId) {
    return this.request(`/api/threads/${threadId}/messages`);
  },

  // Chat Orchestrator
  async sendChat(threadId, message) {
    return this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        thread_id: threadId,
        message: message
      })
    });
  },

  // Credentials Vault
  async listCredentials() {
    return this.request('/api/credentials');
  },

  async saveZoomCredentials(accountId, clientId, clientSecret) {
    return this.request('/api/credentials/zoom', {
      method: 'POST',
      body: JSON.stringify({
        account_id: accountId,
        client_id: clientId,
        client_secret: clientSecret
      })
    });
  },

  async uploadGoogleCredentials(service, file) {
    const formData = new FormData();
    formData.append('service', service);
    formData.append('file', file);

    return this.request('/api/credentials/upload-json', {
      method: 'POST',
      body: formData
    });
  },

  async deleteCredential(service) {
    return this.request(`/api/credentials/${service}`, {
      method: 'DELETE'
    });
  }
};
