/**
 * NexusAI Web UI - Streamlined Navigation
 */

const Sidebar = {
  sidebarEl: null,
  newChatBtnEl: null,
  sidebarToggleBtnEl: null,

  init() {
    this.sidebarEl = document.getElementById('sidebar');
    this.newChatBtnEl = document.getElementById('newChatBtn');
    this.sidebarToggleBtnEl = document.getElementById('sidebarToggleBtn');

    this.bindEvents();
  },

  bindEvents() {
    if (this.newChatBtnEl) {
      this.newChatBtnEl.addEventListener('click', () => {
        this.startNewSession();
      });
    }

    if (this.sidebarToggleBtnEl) {
      this.sidebarToggleBtnEl.addEventListener('click', () => {
        this.toggleSidebar();
      });
    }

    const navWorkspaceBtn = document.getElementById('navWorkspaceBtn');
    if (navWorkspaceBtn) {
      navWorkspaceBtn.addEventListener('click', () => {
        this.setActiveNav(navWorkspaceBtn);
      });
    }

    const navVaultBtn = document.getElementById('navVaultBtn');
    if (navVaultBtn) {
      navVaultBtn.addEventListener('click', () => {
        Modal.openVaultModal();
      });
    }

    const navAgentsBtn = document.getElementById('navAgentsBtn');
    if (navAgentsBtn) {
      navAgentsBtn.addEventListener('click', () => {
        const agentsModal = document.getElementById('agentsModal');
        if (agentsModal) agentsModal.classList.add('open');
      });
    }
  },

  setActiveNav(el) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    el.classList.add('active');
  },

  toggleSidebar() {
    this.sidebarEl.classList.toggle('collapsed');
  },

  startNewSession() {
    Storage.setThreadId(null);
    Chat.showWelcome();
    Modal.toast('Fresh reasoning session started.', 'info');
  }
};
