/**
 * NexusAI Web UI - Modals (Single Unified Credentials, Auth Gate) & Toasts
 */

const Modal = {
  vaultModalEl: null,
  toastContainerEl: null,
  authMode: 'signin', // 'signin' | 'signup'

  init() {
    this.vaultModalEl = document.getElementById('vaultModal');
    this.toastContainerEl = document.getElementById('toastContainer');
    this.bindEvents();
  },

  bindEvents() {
    // Single Credentials entry point
    const headerVaultBtn = document.getElementById('headerVaultBtn');
    if (headerVaultBtn) {
      headerVaultBtn.addEventListener('click', () => this.openVaultModal());
    }

    // Header Auth / Sign Out button
    const headerAuthBtn = document.getElementById('headerAuthBtn');
    if (headerAuthBtn) {
      headerAuthBtn.addEventListener('click', () => {
        if (Storage.getToken()) {
          App.signOut();
        } else {
          App.showAuthScreen();
        }
      });
    }

    // Sidebar Sign Out button
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

    // Service dropdown toggle in Unified Credentials Form
    const serviceSelect = document.getElementById('unifiedServiceSelect');
    const googleFields = document.getElementById('googleCredFields');
    const zoomFields = document.getElementById('zoomCredFields');

    if (serviceSelect) {
      serviceSelect.addEventListener('change', () => {
        const isZoom = serviceSelect.value === 'zoom';
        if (googleFields) googleFields.style.display = isZoom ? 'none' : 'flex';
        if (zoomFields) zoomFields.style.display = isZoom ? 'flex' : 'none';
      });
    }

    // Unified Credentials Form Submit
    const unifiedCredForm = document.getElementById('unifiedCredForm');
    if (unifiedCredForm) {
      unifiedCredForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const service = serviceSelect ? serviceSelect.value : 'gmail';

        if (service === 'zoom') {
          const accountId = (document.getElementById('zoomAccountId')?.value || '').trim();
          const clientId = (document.getElementById('zoomClientId')?.value || '').trim();
          const clientSecret = (document.getElementById('zoomClientSecret')?.value || '').trim();

          if (!accountId || !clientId || !clientSecret) {
            this.toast('Please fill in all Zoom credentials.', 'error');
            return;
          }

          try {
            await API.saveZoomCredentials(accountId, clientId, clientSecret);
            this.toast('Zoom credentials saved.', 'success');
            document.getElementById('zoomAccountId').value = '';
            document.getElementById('zoomClientId').value = '';
            document.getElementById('zoomClientSecret').value = '';
            this.loadCredentialsStatus();
          } catch (err) {
            this.toast(`Failed to save Zoom credentials: ${err.message}`, 'error');
          }
        } else {
          const fileInput = document.getElementById('googleJsonFile');
          if (!fileInput.files || fileInput.files.length === 0) {
            this.toast('Please select a JSON credential file.', 'error');
            return;
          }

          try {
            await API.uploadGoogleCredentials(service, fileInput.files[0]);
            this.toast('Credentials uploaded successfully.', 'success');
            fileInput.value = '';
            this.loadCredentialsStatus();
          } catch (err) {
            this.toast(`Upload failed: ${err.message}`, 'error');
          }
        }
      });
    }

    // Auth Screen Tabs (Sign In vs Create Account)
    const tabSignInBtn = document.getElementById('tabSignInBtn');
    const tabSignUpBtn = document.getElementById('tabSignUpBtn');
    const authSubmitBtn = document.getElementById('authSubmitBtn');

    if (tabSignInBtn && tabSignUpBtn) {
      tabSignInBtn.addEventListener('click', () => {
        this.authMode = 'signin';
        tabSignInBtn.classList.add('active');
        tabSignUpBtn.classList.remove('active');
        if (authSubmitBtn) authSubmitBtn.textContent = 'Sign In';
      });

      tabSignUpBtn.addEventListener('click', () => {
        this.authMode = 'signup';
        tabSignUpBtn.classList.add('active');
        tabSignInBtn.classList.remove('active');
        if (authSubmitBtn) authSubmitBtn.textContent = 'Create Account';
      });
    }

    // Auth Form Submit
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
            this.toast(`Welcome back!`, 'success');
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
    if (this.vaultModalEl) {
      this.vaultModalEl.classList.add('open');
      await this.loadCredentialsStatus();
    }
  },

  async loadCredentialsStatus() {
    const listEl = document.getElementById('credentialsStatusList');
    if (!listEl) return;

    listEl.innerHTML = '<div style="color: var(--text-muted); font-size: 0.85rem;">Loading...</div>';

    try {
      const res = await API.listCredentials();
      const services = ['gmail', 'google_calendar', 'google_meet', 'zoom'];
      const activeCreds = Array.isArray(res) ? res : (res.credentials || []);

      const serviceDisplayNames = {
        'gmail': 'Gmail',
        'google_calendar': 'Google Calendar',
        'google_meet': 'Google Meet / Drive',
        'zoom': 'Zoom',
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

        const displayName = serviceDisplayNames[srv] || srv;
        const card = document.createElement('div');
        card.className = 'credential-card';
        card.innerHTML = `
          <div class="cred-info">
            <div class="cred-icon-box">
              ${srvIconSvg}
            </div>
            <div style="font-weight: 500; font-size: 0.9rem;">${displayName}</div>
          </div>
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="cred-badge ${found ? 'connected' : 'missing'}">
              ${found ? 'Connected' : 'Not configured'}
            </span>
            ${found ? `<button class="btn-icon" style="color: var(--text-muted);" title="Remove" onclick="Modal.deleteCred('${srv}')"><svg class="ui-icon ui-icon-sm" viewBox="0 0 24 24"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/></svg></button>` : ''}
          </div>
        `;
        listEl.appendChild(card);
      });

    } catch (err) {
      listEl.innerHTML = `<div style="color: var(--danger); font-size: 0.85rem;">Error loading credentials: ${err.message}</div>`;
    }
  },

  async deleteCred(service) {
    if (!confirm(`Remove ${service} credentials?`)) return;
    try {
      await API.deleteCredential(service);
      this.toast(`${service} credentials removed.`, 'info');
      this.loadCredentialsStatus();
    } catch (err) {
      this.toast(err.message, 'error');
    }
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
    }, 3500);
  }
};
