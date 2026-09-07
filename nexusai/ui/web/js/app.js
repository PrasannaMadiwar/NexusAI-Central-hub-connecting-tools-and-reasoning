/**
 * NexusAI Web UI - Main App Bootloader & Auth Orchestrator
 */

const App = {
  async init() {
    console.log('🚀 Initializing NexusAI Workspace UI...');

    Chat.init();
    Sidebar.init();
    Modal.init();

    await this.checkSystemHealth();
    await this.checkAuthentication();

    Chat.showWelcome();
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
    const token = Storage.getToken();
    if (!token) {
      this.updateUserDisplay();
      // Prompt user to sign in or create account
      Modal.openAuthModal();
      return;
    }

    try {
      const user = await API.getMe();
      Storage.setUser(user);
      this.updateUserDisplay();
    } catch (err) {
      console.warn('Session expired or invalid, please sign in.');
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
    Modal.toast('Signed out successfully.', 'info');
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
      if (nameEl) nameEl.textContent = user.email || 'User';
      if (roleEl) roleEl.textContent = 'OAuth2 Isolated';
      if (avatarEl) {
        avatarEl.textContent = (user.email || 'U')[0].toUpperCase();
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
