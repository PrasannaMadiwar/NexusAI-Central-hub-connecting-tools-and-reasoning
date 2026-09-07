/**
 * NexusAI Web UI - Main App Bootloader
 */

const App = {
  async init() {
    console.log('🚀 Initializing NexusAI ChatGPT / Gemini UI...');

    Chat.init();
    Sidebar.init();
    Modal.init();

    await this.checkSystemHealth();
    await this.ensureAuthentication();
    await Sidebar.renderThreads();

    const currentThreadId = Storage.getThreadId();
    if (currentThreadId) {
      await Sidebar.selectThread(currentThreadId);
    } else {
      Chat.showWelcome();
    }
  },

  async checkSystemHealth() {
    const statusTextEl = document.getElementById('systemStatusText');
    try {
      const health = await API.getHealth();
      if (statusTextEl) {
        statusTextEl.textContent = `Online • ${health.database} • ${health.vault}`;
      }
    } catch (err) {
      if (statusTextEl) {
        statusTextEl.textContent = 'Backend Offline';
        statusTextEl.style.color = 'var(--danger)';
      }
    }
  },

  async ensureAuthentication() {
    let token = Storage.getToken();
    if (!token) {
      try {
        // Automatically request a developer demo token from the backend
        const authData = await API.getDemoToken('developer@nexusai.local');
        Storage.setToken(authData.access_token);
        Storage.setUser(authData.user);
      } catch (err) {
        console.warn('Could not auto-fetch demo token:', err);
      }
    } else {
      try {
        const user = await API.getMe();
        Storage.setUser(user);
      } catch (err) {
        console.warn('Saved token expired or invalid, refreshing demo token...');
        try {
          const authData = await API.getDemoToken('developer@nexusai.local');
          Storage.setToken(authData.access_token);
          Storage.setUser(authData.user);
        } catch (_) {}
      }
    }

    this.updateUserDisplay();
  },

  updateUserDisplay() {
    const user = Storage.getUser();
    const nameEl = document.getElementById('userName');
    const avatarEl = document.getElementById('userAvatar');

    if (user) {
      if (nameEl) nameEl.textContent = user.email || 'Developer User';
      if (avatarEl) {
        const initial = (user.email || 'D')[0].toUpperCase();
        avatarEl.textContent = initial;
      }
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
