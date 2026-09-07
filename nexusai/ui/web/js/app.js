/**
 * NexusAI Web UI - Main App Bootloader & Auth Orchestrator
 */

const App = {
  async init() {
    console.log('🚀 Initializing NexusAI Workspace UI...');

    try {
      Chat.init();
    } catch (e) {
      console.error('Chat.init error:', e);
    }

    try {
      Sidebar.init();
    } catch (e) {
      console.error('Sidebar.init error:', e);
    }

    try {
      Modal.init();
    } catch (e) {
      console.error('Modal.init error:', e);
    }

    // Always ensure welcome screen is rendered if feed is empty
    const feed = document.getElementById('messagesInner');
    if (feed && feed.children.length === 0) {
      Chat.showWelcome();
    }

    // Async health check (non-blocking)
    this.checkSystemHealth().catch(err => console.warn('Health check warning:', err));

    // Ensure user is authenticated (auto-provisions demo developer session if fresh visit)
    await this.checkAuthentication();
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

  async checkAuthentication() {
    let token = Storage.getToken();

    // If no session exists, require the user to sign in
    if (!token) {
      this.updateUserDisplay();
      Modal.openAuthModal();
      return;
    }


    // Verify existing token
    try {
      const user = await API.getMe();
      Storage.setUser(user);
      this.updateUserDisplay();
    } catch (err) {
      console.warn('Session expired or invalid, prompting login...');
      Storage.setToken('');
      Storage.setUser(null);
      this.updateUserDisplay();
      Modal.openAuthModal();
    }
  },

  signOut() {
    Storage.setToken('');
    Storage.setUser(null);
    Storage.setThreadId(null);
    this.updateUserDisplay();
    Chat.showWelcome();
    Modal.toast('Signed out. Please sign in or use demo login.', 'info');
    Modal.openAuthModal();
  },

  updateUserDisplay() {
    const user = Storage.getUser();
    const token = Storage.getToken();
    const nameEl = document.getElementById('userName');
    const roleEl = document.getElementById('userRole');
    const avatarEl = document.getElementById('userAvatar');
    const headerAuthBtn = document.getElementById('headerAuthBtn');
    const sidebarSignOutBtn = document.getElementById('sidebarSignOutBtn');

    if (token && user) {
      if (nameEl) nameEl.textContent = user.email || 'Developer User';
      if (roleEl) roleEl.textContent = 'OAuth2 Isolated';
      if (avatarEl) {
        avatarEl.textContent = (user.email || 'D')[0].toUpperCase();
      }
      if (headerAuthBtn) {
        headerAuthBtn.textContent = 'Sign Out';
        headerAuthBtn.style.display = 'inline-flex';
      }
      if (sidebarSignOutBtn) {
        sidebarSignOutBtn.style.display = 'inline-flex';
      }
    } else {
      if (nameEl) nameEl.textContent = 'Not Signed In';
      if (roleEl) roleEl.textContent = 'Guest Session';
      if (avatarEl) avatarEl.textContent = '?';
      if (headerAuthBtn) {
        headerAuthBtn.textContent = 'Sign In';
        headerAuthBtn.style.display = 'inline-flex';
      }
      if (sidebarSignOutBtn) {
        sidebarSignOutBtn.style.display = 'none';
      }
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
