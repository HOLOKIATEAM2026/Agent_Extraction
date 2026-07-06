// auth.js
// Supabase Client Initialization
let supabaseClient = null;
let supabaseClientPromise = null;
let logoutDialogInitialized = false;
let logoutDialogResolve = null;
let logoutDialogLastFocus = null;

async function getSupabaseClient() {
  if (supabaseClient) return supabaseClient;
  if (supabaseClientPromise) return supabaseClientPromise;

  supabaseClientPromise = new Promise((resolve, reject) => {
    const init = () => {
      try {
        if (typeof SUPABASE_URL === 'undefined' || typeof SUPABASE_ANON_KEY === 'undefined') {
          throw new Error("SUPABASE_URL / SUPABASE_ANON_KEY manquants (config.js n'est pas chargé)");
        }
        if (!window.supabase || typeof window.supabase.createClient !== 'function') {
          throw new Error("Supabase JS n'est pas chargé");
        }
        supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        window.supabaseClient = supabaseClient;
        resolve(supabaseClient);
      } catch (e) {
        reject(e);
      }
    };

    if (!document.querySelector('script[data-supabase-js="1"]')) {
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2';
      s.async = false;
      s.setAttribute('data-supabase-js', '1');
      s.onload = () => init();
      s.onerror = () => reject(new Error("Impossible de charger le CDN Supabase"));
      document.head.appendChild(s);
    }

    const start = Date.now();
    const timer = setInterval(() => {
      if (window.supabase && typeof window.supabase.createClient === 'function') {
        clearInterval(timer);
        init();
      } else if (Date.now() - start > 8000) {
        clearInterval(timer);
        reject(new Error("Timeout: Supabase JS n'est pas disponible"));
      }
    }, 50);
  });

  return supabaseClientPromise;
}

function ensureLogoutDialog() {
  if (logoutDialogInitialized) return;
  logoutDialogInitialized = true;

  const style = document.createElement('style');
  style.id = 'holokia-logout-dialog-style';
  style.textContent = `
.holokia-modal-overlay{position:fixed;inset:0;background:var(--overlay,rgba(0,0,0,0.55));display:flex;align-items:center;justify-content:center;z-index:10000;padding:16px}
.holokia-modal-overlay[hidden]{display:none}
.holokia-modal{width:min(440px,100%);background:var(--paper-2,var(--surface,#292929));border:1px solid var(--line,var(--border,rgba(255,255,255,0.14)));border-radius:16px;box-shadow:0 24px 60px rgba(0,0,0,0.35);padding:18px 18px 16px;color:var(--ink,var(--text,#F1F5FF))}
.holokia-modal-title{margin:0 0 6px;font-family:var(--display,system-ui);font-size:22px;letter-spacing:0.02em}
.holokia-modal-desc{margin:0 0 14px;font-family:var(--body,system-ui);font-size:13px;line-height:1.6;color:var(--muted,var(--ink-2,#A7B3C8))}
.holokia-modal-actions{display:flex;justify-content:flex-end;gap:10px}
.holokia-btn{appearance:none;border-radius:12px;padding:10px 12px;font-family:var(--mono,system-ui);font-size:11px;letter-spacing:0.08em;text-transform:uppercase;cursor:pointer;transition:transform .12s,opacity .12s,background .12s,border-color .12s}
.holokia-btn:active{transform:translateY(1px)}
.holokia-btn:focus-visible{outline:none;box-shadow:0 0 0 4px var(--focus,rgba(60,87,243,0.25))}
.holokia-btn-secondary{background:transparent;border:1px solid var(--line,var(--border,rgba(255,255,255,0.14)));color:var(--ink,var(--text,#F1F5FF))}
.holokia-btn-secondary:hover{background:var(--glass,var(--ghost,rgba(241,245,255,0.06)))}
.holokia-btn-danger{background:var(--red,#FF3D8D);border:1px solid rgba(255,61,141,0.35);color:var(--on-accent,#fff)}
.holokia-btn-danger:hover{opacity:.92}
  `.trim();
  document.head.appendChild(style);

  const overlay = document.createElement('div');
  overlay.id = 'holokiaLogoutOverlay';
  overlay.className = 'holokia-modal-overlay';
  overlay.hidden = true;
  overlay.innerHTML = `
    <div class="holokia-modal" role="dialog" aria-modal="true" aria-labelledby="holokiaLogoutTitle" aria-describedby="holokiaLogoutDesc">
      <h2 class="holokia-modal-title" id="holokiaLogoutTitle">Confirmer la déconnexion</h2>
      <p class="holokia-modal-desc" id="holokiaLogoutDesc">Voulez-vous vraiment vous déconnecter ?</p>
      <div class="holokia-modal-actions">
        <button type="button" class="holokia-btn holokia-btn-secondary" id="holokiaLogoutCancel">Annuler</button>
        <button type="button" class="holokia-btn holokia-btn-danger" id="holokiaLogoutConfirm">Déconnexion</button>
      </div>
    </div>
  `.trim();
  document.body.appendChild(overlay);

  const close = (ok) => {
    const el = document.getElementById('holokiaLogoutOverlay');
    if (el) el.hidden = true;
    const resolve = logoutDialogResolve;
    logoutDialogResolve = null;
    if (logoutDialogLastFocus && typeof logoutDialogLastFocus.focus === 'function') logoutDialogLastFocus.focus();
    logoutDialogLastFocus = null;
    if (resolve) resolve(ok);
  };

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) close(false);
  });

  const btnCancel = overlay.querySelector('#holokiaLogoutCancel');
  const btnConfirm = overlay.querySelector('#holokiaLogoutConfirm');
  if (btnCancel) btnCancel.addEventListener('click', () => close(false));
  if (btnConfirm) btnConfirm.addEventListener('click', () => close(true));

  window.addEventListener('keydown', (e) => {
    const el = document.getElementById('holokiaLogoutOverlay');
    if (!el || el.hidden) return;
    if (e.key === 'Escape') close(false);
  });
}

const Auth = {
  async register(email, password, nom) {
    const client = await getSupabaseClient();
    const { data, error } = await client.auth.signUp({
      email,
      password,
      options: {
        data: {
          nom: nom
        }
      }
    });
    if (error) throw error;
    return data;
  },

  async login(email, password) {
    const client = await getSupabaseClient();
    const { data, error } = await client.auth.signInWithPassword({
      email,
      password
    });
    if (error) throw error;
    return data;
  },

  async logout() {
    let client = null;
    try {
      client = await getSupabaseClient();
    } catch (e) {
      window.location.href = 'login.html';
      return;
    }
    const { error } = await client.auth.signOut();
    if (error) throw error;
    window.location.href = 'login.html';
  },

  async getSession() {
    try {
      const client = await getSupabaseClient();
      const { data, error } = await client.auth.getSession();
      if (error) return null;
      return data.session;
    } catch (e) {
      return null;
    }
  },

  async getUser() {
    try {
      const client = await getSupabaseClient();
      const { data: { user }, error } = await client.auth.getUser();
      if (error) return null;
      return user;
    } catch (e) {
      return null;
    }
  },

  // Récupérer le token pour l'envoyer à FastAPI
  async getToken() {
    const session = await this.getSession();
    return session ? session.access_token : null;
  },

  // Protéger une page : redirige vers login.html si non connecté
  async protectRoute() {
    const session = await this.getSession();
    if (!session) {
      window.location.href = "login.html";
      return null;
    }
    this.injectLogoutButton();
    this.updateUserName(session.user);
    return session.user;
  },

  async confirmLogout() {
    ensureLogoutDialog();
    const overlay = document.getElementById('holokiaLogoutOverlay');
    if (!overlay) return window.confirm('Voulez-vous vraiment vous déconnecter ?');
    if (logoutDialogResolve) return false;

    logoutDialogLastFocus = document.activeElement;
    overlay.hidden = false;
    const btnCancel = overlay.querySelector('#holokiaLogoutCancel');
    if (btnCancel && typeof btnCancel.focus === 'function') btnCancel.focus();

    return new Promise((resolve) => {
      logoutDialogResolve = resolve;
    });
  },

  // Affiche le nom de l'utilisateur ou le bouton de connexion pour les pages non protégées
  async updateAuthUI() {
    const session = await this.getSession();
    if (session) {
      this.injectLogoutButton();
      this.updateUserName(session.user);
    } else {
      const navStatus = document.querySelector('.nav-status') || document.querySelector('.nav-badge');
      if (navStatus) {
        navStatus.innerHTML = '<a href="login.html" style="color: var(--blue); text-decoration: none; font-weight: 500;">Se connecter</a>';
        navStatus.style.cursor = "";
        navStatus.onclick = null;
      }
    }
  },

  updateUserName(user) {
    // Essaie d'abord .nav-status (index, etc), puis .nav-badge (chat, multi, diagnostic)
    const navStatus = document.querySelector('.nav-status') || document.querySelector('.nav-badge');
    if (navStatus) {
      // Récupérer le nom depuis les user_metadata, sinon utiliser l'email
      const userName = user.user_metadata?.nom || user.email.split('@')[0];
      const profileHref = "profil.html";
      navStatus.innerHTML = `<a href="${profileHref}" style="font-weight: 500; color: var(--blue); text-decoration: none; display: inline-flex; align-items: center; gap: 6px;">👤 ${userName}</a>`;
      navStatus.style.cursor = "pointer";
      navStatus.onclick = (e) => {
        if (e && (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey)) {
          return;
        }
        window.location.href = profileHref;
      };
    }
  },

  injectLogoutButton() {
    const navLinks = document.querySelector('.nav-links');
    if (navLinks && !document.getElementById('logoutBtn')) {
      const li = document.createElement('li');
      const a = document.createElement('a');
      a.href = "#";
      a.id = "logoutBtn";
      a.textContent = "Déconnexion";
      a.style.color = "var(--red)";
      a.onclick = async (e) => {
        e.preventDefault();
        const ok = await this.confirmLogout();
        if (ok) this.logout();
      };
      li.appendChild(a);
      navLinks.appendChild(li);
    }
  },

  // Helper pour faire des requêtes API avec le token
  async apiFetch(url, options = {}) {
    const token = await this.getToken();
    const headers = {
      ...options.headers
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return fetch(url, {
      ...options,
      headers
    });
  }
};

// Exposer globalement pour une utilisation facile dans les autres scripts
window.Auth = Auth;
window.supabaseClient = supabaseClient;
