/**
 * NexusAI Web UI - Modals (Credentials Vault & User Switcher) & Toasts
 */

const Modal = {
  vaultModalEl: null,
  authModalEl: null,
  toastContainerEl: null,

  init() {
    this.vaultModalEl = document.getElementById('vaultModal');
    this.authModalEl = document.getElementById('authModal');
    this.toastContainerEl = document.getElementById('toastContainer');

    this.bindEvents();
  },

  bindEvents() {
    // Open Credentials Modal
    const openVaultBtn = document.getElementById('openVaultBtn');
    if (openVaultBtn) {
      openVaultBtn.addEventListener('click', () => this.openVaultModal());
    }

    // Open Auth Modal
    const userProfileBar = document.getElementById('userProfileBar');
    if (userProfileBar) {
      userProfileBar.addEventListener('click', () => this.openAuthModal());
    }

    // Close buttons
    document.querySelectorAll('[data-close-modal]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const modal = e.target.closest('.modal-overlay');
        if (modal) modal.classList.remove('open');
      });
    });

    // Close on backdrop click
    document.querySelectorAll('.modal-overlay').forEach(modal => {
      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.classList.remove('open');
        }
      });
    });

    // Modal tabs switching
    document.querySelectorAll('.modal-tab-btn').forEach(tabBtn => {
      tabBtn.addEventListener('click', () => {
        const targetTab = tabBtn.dataset.tab;
        const parentModal = tabBtn.closest('.modal-card');

        parentModal.querySelectorAll('.modal-tab-btn').forEach(b => b.classList.remove('active'));
        parentModal.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');

        tabBtn.classList.add('active');
        const activePane = parentModal.querySelector(`.tab-pane[data-pane="${targetTab}"]`);
        if (activePane) activePane.style.display = 'flex';
      });
    });

    // Zoom Form Submit
    const zoomForm = document.getElementById('zoomForm');
    if (zoomForm) {
      zoomForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const accountId = document.getElementById('zoomAccountId').value.trim();
        const clientId = document.getElementById('zoomClientId').value.trim();
        const clientSecret = document.getElementById('zoomClientSecret').value.trim();

        try {
          await API.saveZoomCredentials(accountId, clientId, clientSecret);
          this.toast('Zoom Server-to-Server OAuth saved & encrypted in MongoDB!', 'success');
          this.loadCredentialsStatus();
          zoomForm.reset();
        } catch (err) {
          this.toast(`Failed to save Zoom: ${err.message}`, 'error');
        }
      });
    }

    // Google JSON Upload Submit
    const googleUploadForm = document.getElementById('googleUploadForm');
    if (googleUploadForm) {
      googleUploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const service = document.getElementById('googleServiceSelect').value;
        const fileInput = document.getElementById('googleJsonFile');
        if (!fileInput.files || fileInput.files.length === 0) {
          this.toast('Please select a Google Service Account / OAuth JSON file.', 'error');
          return;
        }

        try {
          await API.uploadGoogleCredentials(service, fileInput.files[0]);
          this.toast(`${service} credentials uploaded & encrypted!`, 'success');
          this.loadCredentialsStatus();
          googleUploadForm.reset();
        } catch (err) {
          this.toast(`Failed to upload JSON: ${err.message}`, 'error');
        }
      });
    }

    // Auth Form Submit (custom token)
    const authForm = document.getElementById('authForm');
    if (authForm) {
      authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const token = document.getElementById('jwtTokenInput').value.trim();
        if (!token) return;

        Storage.setToken(token);
        try {
          const user = await API.getMe();
          Storage.setUser(user);
          App.updateUserDisplay();
          this.toast(`Authenticated as ${user.email}`, 'success');
          this.authModalEl.classList.remove('open');
          Sidebar.renderThreads();
        } catch (err) {
          this.toast(`Invalid token: ${err.message}`, 'error');
        }
      });
    }

    // Load Demo User Button
    const loadDemoUserBtn = document.getElementById('loadDemoUserBtn');
    if (loadDemoUserBtn) {
      loadDemoUserBtn.addEventListener('click', async () => {
        try {
          const res = await API.getDemoToken('developer@nexusai.local');
          Storage.setToken(res.access_token);
          Storage.setUser(res.user);
          App.updateUserDisplay();
          this.toast(`Demo user authenticated (${res.user.email})`, 'success');
          this.authModalEl.classList.remove('open');
          Sidebar.renderThreads();
        } catch (err) {
          this.toast(`Error fetching demo token: ${err.message}`, 'error');
        }
      });
    }
  },

  async openVaultModal() {
    this.vaultModalEl.classList.add('open');
    await this.loadCredentialsStatus();
  },

  async loadCredentialsStatus() {
    const listEl = document.getElementById('credentialsStatusList');
    if (!listEl) return;

    listEl.innerHTML = '<div style="color: var(--text-muted); font-size: 0.85rem;">Loading stored credentials...</div>';

    try {
      const res = await API.listCredentials();
      const services = ['zoom', 'gmail', 'google_calendar', 'google_meet'];
      const activeCreds = Array.isArray(res) ? res : (res.credentials || []);

      listEl.innerHTML = '';
      services.forEach(srv => {
        const found = activeCreds.find(c => c.service === srv);
        const card = document.createElement('div');
        card.className = 'credential-card';
        card.innerHTML = `
          <div class="cred-info">
            <span style="font-size: 1.2rem;">${srv === 'zoom' ? '📹' : '📧'}</span>
            <div>
              <div style="font-weight: 600; text-transform: capitalize;">${srv.replace('_', ' ')}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${found ? `Type: ${found.auth_type}` : 'Not configured'}</div>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="cred-badge ${found ? 'connected' : 'missing'}">
              ${found ? 'Encrypted in MongoDB' : 'Missing'}
            </span>
            ${found ? `<button class="btn-icon" style="color: var(--danger);" title="Delete" onclick="Modal.deleteCred('${srv}')">🗑️</button>` : ''}
          </div>
        `;
        listEl.appendChild(card);
      });
    } catch (err) {
      listEl.innerHTML = `<div style="color: var(--danger); font-size: 0.85rem;">Error loading credentials: ${err.message}</div>`;
    }
  },

  async deleteCred(service) {
    if (!confirm(`Remove encrypted ${service} credentials from MongoDB vault?`)) return;
    try {
      await API.deleteCredential(service);
      this.toast(`${service} credentials removed.`, 'info');
      this.loadCredentialsStatus();
    } catch (err) {
      this.toast(err.message, 'error');
    }
  },

  openAuthModal() {
    this.authModalEl.classList.add('open');
    const tokenInput = document.getElementById('jwtTokenInput');
    if (tokenInput) {
      tokenInput.value = Storage.getToken();
    }
  },

  toast(message, type = 'info') {
    if (!this.toastContainerEl) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let icon = 'ℹ️';
    if (type === 'success') icon = '✅';
    if (type === 'error') icon = '⚠️';

    toast.innerHTML = `<span>${icon}</span><span>${Chat.escapeHtml(message)}</span>`;
    this.toastContainerEl.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  }
};
