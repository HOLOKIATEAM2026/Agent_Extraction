// auth.js
// Supabase Client Initialization
const supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const Auth = {
  async register(email, password, nom) {
    const { data, error } = await supabaseClient.auth.signUp({
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
    const { data, error } = await supabaseClient.auth.signInWithPassword({
      email,
      password
    });
    if (error) throw error;
    return data;
  },

  async logout() {
    const { error } = await supabaseClient.auth.signOut();
    if (error) throw error;
    window.location.href = 'login.html';
  },

  async getSession() {
    const { data, error } = await supabaseClient.auth.getSession();
    if (error) return null;
    return data.session;
  },

  async getUser() {
    const { data: { user }, error } = await supabaseClient.auth.getUser();
    if (error) return null;
    return user;
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
      const navStatus = document.querySelector('.nav-status');
      if (navStatus) {
        navStatus.innerHTML = '<a href="login.html" style="color: var(--blue); text-decoration: none; font-weight: 500;">Se connecter</a>';
      }
    }
  },

  updateUserName(user) {
    const navStatus = document.querySelector('.nav-status');
    if (navStatus) {
      // Récupérer le nom depuis les user_metadata, sinon utiliser l'email
      const userName = user.user_metadata?.nom || user.email.split('@')[0];
      navStatus.innerHTML = `<span style="font-weight: 500; color: var(--blue);">👤 ${userName}</span>`;
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
window.supabaseClient = supabase;
