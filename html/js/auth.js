// auth.js
// Supabase Client Initialization
let supabaseClient = null;
let supabaseClientPromise = null;

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
      a.onclick = (e) => {
        e.preventDefault();
        this.logout();
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
