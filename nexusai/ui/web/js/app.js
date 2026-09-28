/**
 * NexusAI Web UI - Main App Bootloader & Auth Orchestrator
 */

const App = {
  authScreenEl: null,
  appLayoutEl: null,

  async init() {
    console.log('Initializing NexusAI Workspace UI...');
    this.authScreenEl = document.getElementById('authScreen');
    this.appLayoutEl = document.getElementById('appLayout');

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

    // Async health check (non-blocking)
    this.checkSystemHealth().catch(err => console.warn('Health check warning:', err));

    // Ensure user is authenticated (strictly gates system behind login screen)
    await this.checkAuthentication();

    // If authenticated, populate chats list and restore conversation
    const token = Storage.getToken();
    if (token) {
      const threads = await Sidebar.loadThreads();
      let activeThreadId = Storage.getThreadId();
      if (!activeThreadId && threads && threads.length > 0) {
        activeThreadId = threads[0].id;
        Storage.setThreadId(activeThreadId);
        Sidebar.updateActiveThreadUI(activeThreadId);
      }

      if (activeThreadId) {
        try {
          const selectedThread = threads ? threads.find(t => t.id === activeThreadId) : null;
          const title = selectedThread ? selectedThread.title : 'Chat';
          await Chat.loadThread(activeThreadId, title);
        } catch (_) {
          Chat.showWelcome();
        }
      } else {
        const feed = document.getElementById('messagesInner');
        if (feed && feed.children.length === 0) {
          Chat.showWelcome();
        }
      }
    }
  },

  showAuthScreen() {
    if (this.authScreenEl) this.authScreenEl.style.display = 'flex';
    if (this.appLayoutEl) this.appLayoutEl.style.display = 'none';
  },

  async showAppLayout() {
    if (this.authScreenEl) this.authScreenEl.style.display = 'none';
    if (this.appLayoutEl) this.appLayoutEl.style.display = 'flex';
    
    const threads = await Sidebar.loadThreads();
    let activeThreadId = Storage.getThreadId();
    if (!activeThreadId && threads && threads.length > 0) {
      activeThreadId = threads[0].id;
      Storage.setThreadId(activeThreadId);
      Sidebar.updateActiveThreadUI(activeThreadId);
    }

    if (activeThreadId) {
      const selectedThread = threads ? threads.find(t => t.id === activeThreadId) : null;
      const title = selectedThread ? selectedThread.title : 'Chat';
      Chat.loadThread(activeThreadId, title).catch(() => Chat.showWelcome());
    } else {
      const feed = document.getElementById('messagesInner');
      if (feed && feed.children.length === 0) {
        Chat.showWelcome();
      }
    }
  },

  async checkSystemHealth() {
    // Background health check without cluttering UI
    try {
      await API.getHealth();
    } catch (err) {
      console.warn('Backend Offline:', err);
    }
  },

  async checkAuthentication() {
    let token = Storage.getToken();

    // If no session exists, strictly gate the user at the login screen
    if (!token) {
      this.updateUserDisplay();
      this.showAuthScreen();
      return;
    }

    // Verify existing token with backend
    try {
      const user = await API.getMe();
      Storage.setUser(user);
      this.updateUserDisplay();
      this.showAppLayout();
    } catch (err) {
      console.warn('Session expired or invalid, displaying login gate...');
      Storage.setToken('');
      Storage.setUser(null);
      this.updateUserDisplay();
      this.showAuthScreen();
    }
  },

  signOut() {
    Storage.setToken('');
    Storage.setUser(null);
    Storage.setThreadId(null);
    this.updateUserDisplay();
    Chat.showWelcome();
    this.showAuthScreen();
    Sidebar.loadThreads();
    Modal.toast('Signed out.', 'info');
  },

  updateUserDisplay() {
    const user = Storage.getUser();
    const token = Storage.getToken();
    const nameEl = document.getElementById('userName');
    const avatarEl = document.getElementById('userAvatar');
    const headerAuthBtn = document.getElementById('headerAuthBtn');
    const sidebarSignOutBtn = document.getElementById('sidebarSignOutBtn');

    if (token && user) {
      if (nameEl) nameEl.textContent = user.email || 'User';
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
