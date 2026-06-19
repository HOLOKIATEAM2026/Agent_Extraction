// auth.js
// Supabase Client Initialization
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

const Auth = {
  async register(email, password, nom) {
    const { data, error } = await supabase.auth.signUp({
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
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password
    });
    if (error) throw error;
    return data;
  },

  async logout() {
    const { error } = await supabase.auth.signOut();
    if (error) throw error;
    window.location.href = "login.html";
  },

  async getSession() {
    const { data, error } = await supabase.auth.getSession();
    if (error) throw error;
    return data.session;
  },

  async getUser() {
    const { data: { user }, error } = await supabase.auth.getUser();
    if (error) throw error;
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
    return session.user;
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
