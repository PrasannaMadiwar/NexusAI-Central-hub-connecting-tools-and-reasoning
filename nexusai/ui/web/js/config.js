/**
 * NexusAI Web UI - Configuration & Storage Helpers
 */

const CONFIG = {
  API_BASE: window.location.origin,
  STORAGE_KEYS: {
    AUTH_TOKEN: 'nexusai_auth_token',
    USER_INFO: 'nexusai_user_info',
    CURRENT_THREAD_ID: 'nexusai_current_thread_id'
  },
  DEFAULT_USER_EMAIL: 'developer@nexusai.local'
};

const Storage = {
  getToken() {
    return localStorage.getItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN) || '';
  },
  setToken(token) {
    localStorage.setItem(CONFIG.STORAGE_KEYS.AUTH_TOKEN, token);
  },
  getUser() {
    const raw = localStorage.getItem(CONFIG.STORAGE_KEYS.USER_INFO);
    return raw ? JSON.parse(raw) : null;
  },
  setUser(user) {
    localStorage.setItem(CONFIG.STORAGE_KEYS.USER_INFO, JSON.stringify(user));
  },
  getThreadId() {
    return localStorage.getItem(CONFIG.STORAGE_KEYS.CURRENT_THREAD_ID) || null;
  },
  setThreadId(id) {
    if (id) {
      localStorage.setItem(CONFIG.STORAGE_KEYS.CURRENT_THREAD_ID, id);
    } else {
      localStorage.removeItem(CONFIG.STORAGE_KEYS.CURRENT_THREAD_ID);
    }
  }
};
