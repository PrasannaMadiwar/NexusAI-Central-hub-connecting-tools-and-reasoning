/**
 * NexusAI Web UI - Chat Stream & Markdown Formatter
 */

const Chat = {
  feedEl: null,
  innerEl: null,
  inputEl: null,
  sendBtnEl: null,

  init() {
    this.feedEl = document.getElementById('messagesFeed');
    this.innerEl = document.getElementById('messagesInner');
    this.inputEl = document.getElementById('chatInput');
    this.sendBtnEl = document.getElementById('sendBtn');

    this.bindEvents();
  },

  bindEvents() {
    // Auto-expand input textarea
    this.inputEl.addEventListener('input', () => {
      this.inputEl.style.height = 'auto';
      this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 180) + 'px';
      this.sendBtnEl.disabled = !this.inputEl.value.trim();
    });

    // Handle Enter to submit (Shift+Enter for newline)
    this.inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        this.submitCurrentMessage();
      }
    });

    this.sendBtnEl.addEventListener('click', () => {
      this.submitCurrentMessage();
    });
  },

  scrollToBottom() {
    if (this.feedEl) {
      this.feedEl.scrollTop = this.feedEl.scrollHeight;
    }
  },

  clearFeed() {
    if (this.innerEl) {
      this.innerEl.innerHTML = '';
    }
  },

  showWelcome() {
    this.clearFeed();
    const activeTitleEl = document.getElementById('activeThreadTitle');
    if (activeTitleEl) {
      activeTitleEl.textContent = '';
      activeTitleEl.style.display = 'none';
    }

    const welcomeHtml = `
      <div class="welcome-hero" id="welcomeHero">
        <div class="welcome-gradient-text">Hello, Developer</div>
        <div class="welcome-subtitle">How can NexusAI assist your workflow today?</div>
        
        <div class="prompt-suggestions">
          <div class="suggestion-card" onclick="Chat.applyPrompt('Schedule a 30-min Zoom sync with the product team tomorrow at 3 PM')">
            <div class="suggestion-title">📅 Schedule Zoom Meeting</div>
            <div class="suggestion-desc">Create meetings via Zoom OAuth & Google Calendar</div>
          </div>
          <div class="suggestion-card" onclick="Chat.applyPrompt('Check my unread Gmail emails and summarize any high priority messages')">
            <div class="suggestion-title">✉️ Summarize Inbox</div>
            <div class="suggestion-desc">Inspect recent Gmail messages and drafts</div>
          </div>
          <div class="suggestion-card" onclick="Chat.applyPrompt('Write and execute a Python script to calculate Fibonacci sequence and plot timings')">
            <div class="suggestion-title">⚡ Daytona Sandboxed Code</div>
            <div class="suggestion-desc">Run Python calculations securely in sandbox</div>
          </div>
          <div class="suggestion-card" onclick="Chat.applyPrompt('What tools, credentials, and subagents are currently connected to my workspace?')">
            <div class="suggestion-title">🔍 Workspace Audit</div>
            <div class="suggestion-desc">Query MongoDB vault and active subagents</div>
          </div>
        </div>
      </div>
    `;
    this.innerEl.innerHTML = welcomeHtml;
  },

  async loadThread(threadId, threadTitle = 'Chat') {
    this.clearFeed();
    const activeTitleEl = document.getElementById('activeThreadTitle');
    if (activeTitleEl) {
      activeTitleEl.textContent = `• ${threadTitle}`;
      activeTitleEl.style.display = 'inline-block';
    }

    // Loading history state
    const loadingRow = document.createElement('div');
    loadingRow.className = 'message-row assistant';
    loadingRow.innerHTML = `
      <div class="message-avatar">✨</div>
      <div class="message-content">
        <div class="reasoning-indicator">
          <div class="thinking-pulse"></div>
          <span>Loading chat history...</span>
        </div>
      </div>
    `;
    this.innerEl.appendChild(loadingRow);

    try {
      const messages = await API.getMessages(threadId);
      this.clearFeed();

      if (!messages || messages.length === 0) {
        this.appendAssistantMessage('This chat has no saved messages yet. Send a message to resume!');
      } else {
        messages.forEach(m => {
          if (m.role === 'user') {
            this.appendUserMessage(m.content);
          } else {
            this.appendAssistantMessage(m.content);
          }
        });
      }
      this.scrollToBottom();
    } catch (err) {
      this.clearFeed();
      this.appendAssistantMessage(`⚠️ Could not load history for this chat: ${err.message}`);
      Modal.toast(`Failed to load chat: ${err.message}`, 'error');
    }
  },

  applyPrompt(text) {
    this.inputEl.value = text;
    this.inputEl.dispatchEvent(new Event('input'));
    this.inputEl.focus();
  },

  appendUserMessage(text) {
    const hero = document.getElementById('welcomeHero');
    if (hero) hero.remove();

    const row = document.createElement('div');
    row.className = 'message-row user';
    row.innerHTML = `
      <div class="message-avatar">U</div>
      <div class="message-content">
        <div class="message-author-name">You</div>
        <div class="message-body">${this.escapeHtml(text)}</div>
      </div>
    `;
    this.innerEl.appendChild(row);
    this.scrollToBottom();
  },

  appendAssistantMessage(content, toolCalls = []) {
    const hero = document.getElementById('welcomeHero');
    if (hero) hero.remove();

    const row = document.createElement('div');
    row.className = 'message-row assistant';

    let toolsHtml = '';
    if (toolCalls && toolCalls.length > 0) {
      toolsHtml = toolCalls.map(tool => `
        <div class="tool-execution-card">
          <div class="tool-header" onclick="this.nextElementSibling.classList.toggle('hidden')">
            <div class="tool-badge-pill">
              <span>⚡</span>
              <span>${this.escapeHtml(tool.name || 'subagent_execution')}</span>
            </div>
            <span class="tool-status-tag">Success</span>
          </div>
          <div class="tool-content-body">
            <strong>Input:</strong> ${this.escapeHtml(JSON.stringify(tool.args || {}, null, 2))}
            ${tool.output ? `<br><strong>Output:</strong> ${this.escapeHtml(typeof tool.output === 'string' ? tool.output : JSON.stringify(tool.output, null, 2))}` : ''}
          </div>
        </div>
      `).join('');
    }

    const formattedBody = this.renderMarkdown(content);

    row.innerHTML = `
      <div class="message-avatar">✨</div>
      <div class="message-content">
        <div class="message-author-name">NexusAI Orchestrator</div>
        ${toolsHtml}
        <div class="message-body">${formattedBody}</div>
      </div>
    `;
    this.innerEl.appendChild(row);
    this.scrollToBottom();
  },

  showThinking() {
    const row = document.createElement('div');
    row.className = 'message-row assistant thinking-row';
    row.id = 'thinkingRow';
    row.innerHTML = `
      <div class="message-avatar">✨</div>
      <div class="message-content">
        <div class="reasoning-indicator">
          <div class="thinking-pulse"></div>
          <span>NexusAI is orchestrating subagents & reasoning...</span>
        </div>
      </div>
    `;
    this.innerEl.appendChild(row);
    this.scrollToBottom();
  },

  hideThinking() {
    const el = document.getElementById('thinkingRow');
    if (el) el.remove();
  },

  async submitCurrentMessage() {
    const text = this.inputEl.value.trim();
    if (!text) return;

    let threadId = Storage.getThreadId();
    let isNewThread = false;

    if (!threadId) {
      // Auto-create thread in the background
      try {
        const title = text.slice(0, 32) + (text.length > 32 ? '...' : '');
        const newThread = await API.createThread(title);
        threadId = newThread.id;
        Storage.setThreadId(threadId);
        isNewThread = true;
        const activeTitleEl = document.getElementById('activeThreadTitle');
        if (activeTitleEl) {
          activeTitleEl.textContent = `• ${title}`;
          activeTitleEl.style.display = 'inline-block';
        }
      } catch (err) {
        Modal.toast(`Failed to initialize session: ${err.message}`, 'error');
        return;
      }
    }

    const activeThreadId = Storage.getThreadId();
    this.inputEl.value = '';
    this.inputEl.style.height = 'auto';
    this.sendBtnEl.disabled = true;

    this.appendUserMessage(text);
    this.showThinking();

    try {
      const response = await API.sendChat(activeThreadId, text);
      this.hideThinking();
      const content = response.response || response.error || 'Request completed.';
      this.appendAssistantMessage(content, response.tool_calls || []);

      if (isNewThread) {
        Sidebar.loadThreads();
      }
    } catch (err) {
      this.hideThinking();
      this.appendAssistantMessage(`❌ **Error executing request**: ${err.message}\n\n*Please ensure your database pooler and credentials are configured.*`);
      Modal.toast(err.message, 'error');
    } finally {
      this.sendBtnEl.disabled = false;
      this.inputEl.focus();
    }
  },

  escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  },

  renderMarkdown(text) {
    if (!text) return '';
    let html = this.escapeHtml(text);

    // Code blocks with syntax copy button
    html = html.replace(/```([a-zA-Z0-9_\-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const id = 'code_' + Math.random().toString(36).substring(2, 9);
      return `
        <pre><div class="code-header"><span>${lang || 'code'}</span><button class="copy-code-btn" onclick="Chat.copyCode('${id}')">📋 Copy</button></div><code id="${id}">${code.trim()}</code></pre>
      `;
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Bold & Italic
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Unordered lists
    html = html.replace(/^\s*[\-\*]\s+(.*$)/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/gims, '<ul>$1</ul>');

    // Blockquotes
    html = html.replace(/^>\s+(.*$)/gim, '<blockquote>$1</blockquote>');

    // Line breaks to paragraphs
    const paragraphs = html.split(/\n\n+/);
    html = paragraphs.map(p => {
      if (p.startsWith('<pre') || p.startsWith('<ul') || p.startsWith('<h') || p.startsWith('<blockquote')) {
        return p;
      }
      return `<p>${p.replace(/\n/g, '<br>')}</p>`;
    }).join('');

    return html;
  },

  copyCode(elementId) {
    const codeEl = document.getElementById(elementId);
    if (!codeEl) return;
    navigator.clipboard.writeText(codeEl.innerText).then(() => {
      Modal.toast('Code copied to clipboard!', 'success');
    });
  }
};
