const THEME_KEY = 'holokia_theme';
const THEMES = ['dark', 'light'];

function getStoredTheme() {
  try {
    const t = localStorage.getItem(THEME_KEY);
    if (t && THEMES.includes(t)) return t;
  } catch (_) {}
  return null;
}

function getSystemTheme() {
  try {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  } catch (_) {
    return 'dark';
  }
}

function applyTheme(theme) {
  const t = THEMES.includes(theme) ? theme : 'dark';
  document.documentElement.setAttribute('data-theme', t);
  try {
    localStorage.setItem(THEME_KEY, t);
  } catch (_) {}

  const toggles = document.querySelectorAll('[data-theme-toggle]');
  toggles.forEach(btn => {
    const next = t === 'dark' ? 'light' : 'dark';
    btn.setAttribute('aria-label', next === 'dark' ? 'Activer le mode sombre' : 'Activer le mode clair');
    btn.setAttribute('title', next === 'dark' ? 'Mode sombre' : 'Mode clair');
    btn.setAttribute('aria-pressed', t === 'dark' ? 'true' : 'false');
    btn.innerHTML = t === 'dark'
      ? '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z"/></svg>'
      : '<svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><path d="M12 1v2"/><path d="M12 21v2"/><path d="M4.22 4.22l1.42 1.42"/><path d="M18.36 18.36l1.42 1.42"/><path d="M1 12h2"/><path d="M21 12h2"/><path d="M4.22 19.78l1.42-1.42"/><path d="M18.36 5.64l1.42-1.42"/></svg>';
  });
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  applyTheme(current === 'dark' ? 'light' : 'dark');
}

document.addEventListener('DOMContentLoaded', () => {
  const initial = getStoredTheme() || getSystemTheme();
  applyTheme(initial);
  document.querySelectorAll('[data-theme-toggle]').forEach(btn => {
    btn.addEventListener('click', toggleTheme);
  });
});
