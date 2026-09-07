/**
 * NexusAI Web UI - Modals (Credentials Vault, Auth / Login / Signup, Agents) & Toasts
 */

const Modal = {
  vaultModalEl: null,
  authModalEl: null,
  agentsModalEl: null,
  toastContainerEl: null,
  authMode: 'signin', // 'signin' | 'signup'

  init() {
    this.vaultModalEl = document.getElementById('vaultModal');
    this.authModalEl = document.getElementById('authModal');
    this.agentsModalEl = document.getElementById('agentsModal');
    this.toastContainerEl = document.getElementById('toastContainer');

    this.bindEvents();
  },

  bindEvents() {
    // Open Credentials Modal
    const openVaultBtn = document.getElementById('openVaultBtn');
    if (openVaultBtn) {
      openVaultBtn.addEventListener('click', () => this.openVaultModal());
    }
    const headerVaultBtn = document.getElementById('headerVaultBtn');
    if (headerVaultBtn) {
      headerVaultBtn.addEventListener('click', () => this.openVaultModal());
    }
    const navVaultBtn = document.getElementById('navVaultBtn');
    if (navVaultBtn) {
      navVaultBtn.addEventListener('click', () => this.openVaultModal());
    }

    // Open Agents Modal
    const navAgentsBtn = document.getElementById('navAgentsBtn');
    if (navAgentsBtn) {
      navAgentsBtn.addEventListener('click', () => {
        if (this.agentsModalEl) this.agentsModalEl.classList.add('open');
      });
    }

    // Open Auth Modal via Header or Profile
    const headerAuthBtn = document.getElementById('headerAuthBtn');
    if (headerAuthBtn) {
      headerAuthBtn.addEventListener('click', () => {
        if (Storage.getToken()) {
          App.signOut();
        } else {
          this.openAuthModal();
        }
      });
    }

    const sidebarSignOutBtn = document.getElementById('sidebarSignOutBtn');
    if (sidebarSignOutBtn) {
      sidebarSignOutBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        App.signOut();
      });
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

    // Credentials Modal tabs switching
    this.vaultModalEl.querySelectorAll('.modal-tab-btn').forEach(tabBtn => {
      tabBtn.addEventListener('click', () => {
        const targetTab = tabBtn.dataset.tab;
        this.vaultModalEl.querySelectorAll('.modal-tab-btn').forEach(b => b.classList.remove('active'));
        this.vaultModalEl.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');

        tabBtn.classList.add('active');
        const activePane = this.vaultModalEl.querySelector(`.tab-pane[data-pane="${targetTab}"]`);
        if (activePane) activePane.style.display = 'flex';
      });
    });

    // Auth Modal tab switching (Sign In vs Create Account)
    const tabSignInBtn = document.getElementById('tabSignInBtn');
    const tabSignUpBtn = document.getElementById('tabSignUpBtn');
    const authSubmitBtn = document.getElementById('authSubmitBtn');
    const authModalTitle = document.getElementById('authModalTitle');

    if (tabSignInBtn && tabSignUpBtn) {
      tabSignInBtn.addEventListener('click', () => {
        this.authMode = 'signin';
        tabSignInBtn.classList.add('active');
        tabSignUpBtn.classList.remove('active');
        if (authSubmitBtn) authSubmitBtn.textContent = 'Sign In';
        if (authModalTitle) authModalTitle.textContent = 'Sign In to NexusAI';
      });

      tabSignUpBtn.addEventListener('click', () => {
        this.authMode = 'signup';
        tabSignUpBtn.classList.add('active');
        tabSignInBtn.classList.remove('active');
        if (authSubmitBtn) authSubmitBtn.textContent = 'Create Account';
        if (authModalTitle) authModalTitle.textContent = 'Create NexusAI Account';
      });
    }

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

    // Auth Form Submit (Email & Password Login / Signup)
    const authForm = document.getElementById('authForm');
    if (authForm) {
      authForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('authEmailInput').value.trim();
        const password = document.getElementById('authPasswordInput').value;
        if (!email) return;

        try {
          let res;
          if (this.authMode === 'signup') {
            res = await API.signup(email, password);
            this.toast(`Account created for ${res.user.email}!`, 'success');
          } else {
            res = await API.login(email, password);
            this.toast(`Signed in as ${res.user.email}!`, 'success');
          }

          Storage.setToken(res.access_token);
          Storage.setUser(res.user);
          App.updateUserDisplay();
          this.authModalEl.classList.remove('open');
          authForm.reset();
        } catch (err) {
          this.toast(err.message, 'error');
        }
      });
    }

    // Instant 1-Click Admin Login (using pre-registered admin in DB)
    const instantDemoLoginBtn = document.getElementById('instantDemoLoginBtn');
    if (instantDemoLoginBtn) {
      instantDemoLoginBtn.addEventListener('click', async () => {
        try {
          const res = await API.login('admin@nexusai.com', 'Admin@123');
          Storage.setToken(res.access_token);
          Storage.setUser(res.user);
          App.updateUserDisplay();
          this.toast(`Signed in as Admin (${res.user.email})`, 'success');
          this.authModalEl.classList.remove('open');

        } catch (err) {
          this.toast(`Admin login error: ${err.message}`, 'error');
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
    const emailInput = document.getElementById('authEmailInput');
    if (emailInput) emailInput.focus();
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
