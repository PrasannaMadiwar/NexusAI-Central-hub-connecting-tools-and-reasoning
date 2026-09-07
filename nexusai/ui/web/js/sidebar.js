/**
 * NexusAI Web UI - Sidebar Thread Management
 */

const Sidebar = {
  sidebarEl: null,
  threadListEl: null,
  newChatBtnEl: null,
  sidebarToggleBtnEl: null,
  currentThreadTitleEl: null,

  init() {
    this.sidebarEl = document.getElementById('sidebar');
    this.threadListEl = document.getElementById('threadList');
    this.newChatBtnEl = document.getElementById('newChatBtn');
    this.sidebarToggleBtnEl = document.getElementById('sidebarToggleBtn');
    this.currentThreadTitleEl = document.getElementById('currentThreadTitle');

    this.bindEvents();
  },

  bindEvents() {
    this.newChatBtnEl.addEventListener('click', () => {
      this.startNewChat();
    });

    if (this.sidebarToggleBtnEl) {
      this.sidebarToggleBtnEl.addEventListener('click', () => {
        this.toggleSidebar();
      });
    }
  },

  toggleSidebar() {
    this.sidebarEl.classList.toggle('collapsed');
  },

  startNewChat() {
    Storage.setThreadId(null);
    this.renderThreads();
    Chat.showWelcome();
    this.currentThreadTitleEl.textContent = 'New Conversation';
  },

  updateCurrentThreadTitle(title) {
    if (this.currentThreadTitleEl) {
      this.currentThreadTitleEl.textContent = title;
    }
    this.renderThreads();
  },

  async renderThreads() {
    try {
      const threads = await API.listThreads();
      const currentId = Storage.getThreadId();

      this.threadListEl.innerHTML = '';
      if (!threads || threads.length === 0) {
        this.threadListEl.innerHTML = `
          <li style="padding: 12px; font-size: 0.8rem; color: var(--text-muted); text-align: center;">
            No conversations yet
          </li>
        `;
        return;
      }

      threads.forEach(thread => {
        const li = document.createElement('li');
        li.className = `thread-item ${thread.id === currentId ? 'active' : ''}`;
        li.innerHTML = `
          <span class="thread-title">💬 ${Chat.escapeHtml(thread.title || 'Untitled Thread')}</span>
          <button class="thread-delete-btn" title="Delete conversation">🗑️</button>
        `;

        li.addEventListener('click', (e) => {
          if (e.target.classList.contains('thread-delete-btn')) {
            e.stopPropagation();
            this.deleteThread(thread.id);
          } else {
            this.selectThread(thread.id, thread.title);
          }
        });

        this.threadListEl.appendChild(li);
      });

      // Update current title
      if (currentId) {
        const active = threads.find(t => t.id === currentId);
        if (active && this.currentThreadTitleEl) {
          this.currentThreadTitleEl.textContent = active.title || 'Conversation';
        }
      }
    } catch (err) {
      console.error('Failed to load threads:', err);
    }
  },

  async selectThread(threadId, threadTitle) {
    Storage.setThreadId(threadId);
    this.renderThreads();
    if (this.currentThreadTitleEl) {
      this.currentThreadTitleEl.textContent = threadTitle || 'Conversation';
    }

    Chat.clearFeed();
    try {
      const messages = await API.getMessages(threadId);
      if (!messages || messages.length === 0) {
        Chat.showWelcome();
      } else {
        messages.forEach(msg => {
          if (msg.role === 'user') {
            Chat.appendUserMessage(msg.content);
          } else {
            Chat.appendAssistantMessage(msg.content, msg.tool_calls || []);
          }
        });
      }
    } catch (err) {
      Modal.toast(`Failed to load messages: ${err.message}`, 'error');
    }
  },

  async deleteThread(threadId) {
    if (!confirm('Are you sure you want to delete this conversation thread?')) return;

    try {
      // If active thread deleted, reset
      if (Storage.getThreadId() === threadId) {
        this.startNewChat();
      }
      this.renderThreads();
      Modal.toast('Thread deleted.', 'info');
    } catch (err) {
      Modal.toast(err.message, 'error');
    }
  }
};
