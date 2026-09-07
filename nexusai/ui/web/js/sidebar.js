/**
 * NexusAI Web UI - Streamlined Navigation & Recent Chats
 */

const Sidebar = {
  sidebarEl: null,
  newChatBtnEl: null,
  sidebarToggleBtnEl: null,
  threadsListEl: null,
  refreshThreadsBtnEl: null,

  init() {
    this.sidebarEl = document.getElementById('sidebar');
    this.newChatBtnEl = document.getElementById('newChatBtn');
    this.sidebarToggleBtnEl = document.getElementById('sidebarToggleBtn');
    this.threadsListEl = document.getElementById('threadsList');
    this.refreshThreadsBtnEl = document.getElementById('refreshThreadsBtn');

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

    if (this.refreshThreadsBtnEl) {
      this.refreshThreadsBtnEl.addEventListener('click', () => {
        this.loadThreads();
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
    this.updateActiveThreadUI(null);
    Chat.showWelcome();
    Modal.toast('Fresh reasoning session started.', 'info');
  },

  async loadThreads() {
    if (!this.threadsListEl) return;
    if (!Storage.getToken()) {
      this.threadsListEl.innerHTML = '<div class="threads-empty-state">Sign in to view chats</div>';
      return;
    }

    try {
      const threads = await API.listThreads();
      this.renderThreads(threads);
    } catch (err) {
      console.warn('Failed to load threads:', err);
      this.threadsListEl.innerHTML = '<div class="threads-empty-state">Unable to load chats</div>';
    }
  },

  renderThreads(threads) {
    if (!this.threadsListEl) return;
    this.threadsListEl.innerHTML = '';

    if (!threads || threads.length === 0) {
      this.threadsListEl.innerHTML = '<div class="threads-empty-state">No previous chats</div>';
      return;
    }

    const activeThreadId = Storage.getThreadId();

    threads.forEach(t => {
      const item = document.createElement('div');
      item.className = `thread-item ${t.id === activeThreadId ? 'active' : ''}`;
      item.dataset.threadId = t.id;
      item.title = t.title || 'Untitled Chat';

      item.innerHTML = `
        <div class="thread-main">
          <span class="thread-icon">💬</span>
          <span class="thread-title-text">${Chat.escapeHtml(t.title || 'Untitled Chat')}</span>
        </div>
        <div class="thread-actions">
          <button class="thread-delete-btn" title="Delete conversation" onclick="event.stopPropagation(); Sidebar.deleteThread('${t.id}')">✕</button>
        </div>
      `;

      item.addEventListener('click', () => {
        this.selectThread(t);
      });

      this.threadsListEl.appendChild(item);
    });
  },

  async selectThread(thread) {
    Storage.setThreadId(thread.id);
    this.updateActiveThreadUI(thread.id);
    await Chat.loadThread(thread.id, thread.title);
  },

  updateActiveThreadUI(activeId) {
    if (!this.threadsListEl) return;
    this.threadsListEl.querySelectorAll('.thread-item').forEach(item => {
      if (item.dataset.threadId === activeId) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    const activeTitleEl = document.getElementById('activeThreadTitle');
    if (activeTitleEl) {
      if (activeId) {
        activeTitleEl.style.display = 'inline-block';
      } else {
        activeTitleEl.style.display = 'none';
        activeTitleEl.textContent = '';
      }
    }
  },

  async deleteThread(threadId) {
    if (!confirm('Are you sure you want to delete this chat?')) return;
    try {
      await API.deleteThread(threadId);
      Modal.toast('Chat deleted.', 'info');
      if (Storage.getThreadId() === threadId) {
        this.startNewSession();
      }
      await this.loadThreads();
    } catch (err) {
      Modal.toast(`Failed to delete chat: ${err.message}`, 'error');
    }
  }
};
