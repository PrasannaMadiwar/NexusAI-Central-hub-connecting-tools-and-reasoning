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

    // Google Service select → dynamic hint update
    const googleServiceSelect = document.getElementById('googleServiceSelect');
    const googleUploadHint = document.getElementById('googleUploadHint');
    const hintMap = {
      'gmail': 'Upload your Gmail OAuth2 token.json file. This is NOT a service account — it must be a user OAuth token.',
      'google_calendar': 'Upload your Calendar Service Account JSON (originally callender_api_agent_key.json).',
      'google_meet': 'Upload your Google Drive/Meet Service Account JSON for transcript access.',
    };
    if (googleServiceSelect && googleUploadHint) {
      googleServiceSelect.addEventListener('change', () => {
        googleUploadHint.textContent = hintMap[googleServiceSelect.value] || '';
      });
    }

    // Google JSON Upload Submit
    const googleUploadForm = document.getElementById('googleUploadForm');
    if (googleUploadForm) {
      const displayNames = {
        'gmail': 'Gmail (token.json)',
        'google_calendar': 'Google Calendar (Service Account)',
        'google_meet': 'Google Meet / Drive (Service Account)',
      };
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
          const name = displayNames[service] || service;
          this.toast(`${name} credentials uploaded & encrypted!`, 'success');
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
          App.showAppLayout();
          authForm.reset();
        } catch (err) {
          this.toast(err.message, 'error');
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

      // Map MongoDB service keys to proper display names matching original engine JSON files
      const serviceDisplayNames = {
        'zoom': 'Zoom (Server-to-Server OAuth)',
        'gmail': 'Gmail (token.json — OAuth2)',
        'google_calendar': 'Google Calendar (callender_api_agent_key.json)',
        'google_meet': 'Google Meet / Drive (Service Account JSON)',
      };

      listEl.innerHTML = '';
      services.forEach(srv => {
        const found = activeCreds.find(c => c.service === srv);
        let srvIconSvg = '<svg class="ui-icon ui-icon-md" viewBox="0 0 24 24"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>';
        if (srv === 'zoom' || srv === 'google_meet') {
          srvIconSvg = '<svg class="ui-icon ui-icon-md" viewBox="0 0 24 24"><polygon points="23 7 16 12 23 17 23 7"/><rect width="15" height="14" x="1" y="5" rx="2" ry="2"/></svg>';
        } else if (srv === 'google_calendar') {
          srvIconSvg = '<svg class="ui-icon ui-icon-md" viewBox="0 0 24 24"><rect width="18" height="18" x="3" y="4" rx="2" ry="2"/><line x1="16" x2="16" y1="2" y2="6"/><line x1="8" x2="8" y1="2" y2="6"/><line x1="3" x2="21" y1="10" y2="10"/></svg>';
        }

        const displayName = serviceDisplayNames[srv] || srv.replace('_', ' ');
        const card = document.createElement('div');
        card.className = 'credential-card';
        card.innerHTML = `
          <div class="cred-info">
            <div class="cred-icon-box">
              ${srvIconSvg}
            </div>
            <div>
              <div style="font-weight: 600;">${displayName}</div>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${found ? `Type: ${found.auth_type}` : 'Not configured'}</div>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="cred-badge ${found ? 'connected' : 'missing'}">
              ${found ? 'Encrypted in MongoDB' : 'Missing'}
            </span>
            ${found ? `<button class="btn-icon" style="color: #ffffff;" title="Delete" onclick="Modal.deleteCred('${srv}')"><svg class="ui-icon ui-icon-sm" viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg></button>` : ''}
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
    App.showAuthScreen();
    const emailInput = document.getElementById('authEmailInput');
    if (emailInput) emailInput.focus();
  },

  toast(message, type = 'info') {
    if (!this.toastContainerEl) return;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    let iconSvg = '<svg class="ui-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="16" y2="12"/><line x1="12" x2="12.01" y1="8" y2="8"/></svg>';
    if (type === 'success') {
      iconSvg = '<svg class="ui-icon" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>';
    } else if (type === 'error') {
      iconSvg = '<svg class="ui-icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/></svg>';
    }

    toast.innerHTML = `<span style="display:inline-flex;align-items:center;">${iconSvg}</span><span>${Chat.escapeHtml(message)}</span>`;
    this.toastContainerEl.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 250);
    }, 4000);
  }
};
