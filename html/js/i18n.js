const I18n = {
  currentLang: 'fr',
  fallbackLang: 'fr',
  translations: {},
  cache: {},

  async init() {
    let saved = 'fr';
    try {
      saved = localStorage.getItem('holokia_lang') || 'fr';
    } catch (_) {}
    this.currentLang = ['fr', 'en', 'es'].includes(saved) ? saved : 'fr';
    await this.load(this.currentLang);
    this.applyTranslations(document);
    this.updateButtons();
    this.injectStyles();
    document.documentElement.lang = this.currentLang;
    document.dispatchEvent(new CustomEvent('i18n:updated', { detail: { lang: this.currentLang } }));
  },

  async load(lang) {
    if (this.cache[lang]) {
      this.translations = this.cache[lang];
      return;
    }
    const res = await fetch(`js/locales/${lang}.json`);
    if (!res.ok) {
      if (lang !== this.fallbackLang) {
        return this.load(this.fallbackLang);
      }
      throw new Error(`Unable to load locale ${lang}`);
    }
    const json = await res.json();
    this.cache[lang] = json;
    this.translations = json;
  },

  t(key, vars) {
    const path = String(key || '').split('.');
    let out = this.translations;
    for (const p of path) {
      out = out && typeof out === 'object' ? out[p] : undefined;
    }
    let value = typeof out === 'string' ? out : String(key || '');
    if (vars && typeof vars === 'object') {
      Object.keys(vars).forEach((k) => {
        value = value.replace(new RegExp(`\\{${k}\\}`, 'g'), String(vars[k]));
      });
    }
    return value;
  },

  applyTranslations(root = document) {
    root.querySelectorAll('[data-i18n]').forEach((el) => {
      el.textContent = this.t(el.dataset.i18n);
    });
    root.querySelectorAll('[data-i18n-html]').forEach((el) => {
      el.innerHTML = this.t(el.dataset.i18nHtml);
    });
    root.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
      el.placeholder = this.t(el.dataset.i18nPlaceholder);
    });
    root.querySelectorAll('[data-i18n-title]').forEach((el) => {
      el.title = this.t(el.dataset.i18nTitle);
    });
    root.querySelectorAll('[data-i18n-aria-label]').forEach((el) => {
      el.setAttribute('aria-label', this.t(el.dataset.i18nAriaLabel));
    });
    root.querySelectorAll('[data-i18n-value]').forEach((el) => {
      const translated = this.t(el.dataset.i18nValue);
      el.value = translated;
      if (el.dataset && Object.prototype.hasOwnProperty.call(el.dataset, 'q')) {
        el.dataset.q = translated;
      }
    });
  },

  async switchLang(lang) {
    if (!['fr', 'en', 'es'].includes(lang) || lang === this.currentLang) return;
    this.currentLang = lang;
    try {
      localStorage.setItem('holokia_lang', lang);
    } catch (_) {}
    await this.load(lang);
    this.applyTranslations(document);
    this.updateButtons();
    document.documentElement.lang = lang;
    document.dispatchEvent(new CustomEvent('i18n:updated', { detail: { lang } }));
  },

  updateButtons() {
    document.querySelectorAll('.lang-btn').forEach((btn) => {
      btn.classList.toggle('active', btn.dataset.lang === this.currentLang);
    });
  },

  injectStyles() {
    if (document.getElementById('i18n-styles')) return;
    const style = document.createElement('style');
    style.id = 'i18n-styles';
    style.textContent = `
      .lang-switcher {
        display: flex;
        gap: 4px;
        align-items: center;
      }
      .lang-btn {
        padding: 4px 8px;
        border: 1px solid var(--line, var(--border));
        border-radius: 6px;
        background: transparent;
        color: var(--muted);
        font-size: 10px;
        cursor: pointer;
        font-family: var(--mono);
        transition: all 0.2s ease;
      }
      .lang-btn:hover,
      .lang-btn.active {
        color: var(--blue);
        border-color: var(--blue);
        background: rgba(60,87,243,0.10);
      }
    `;
    document.head.appendChild(style);
  }
};

window.I18n = I18n;
window.t = (key, vars) => I18n.t(key, vars);

document.addEventListener('DOMContentLoaded', () => {
  I18n.init().catch((err) => console.error('I18n init error:', err));
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('.lang-btn');
    if (btn && btn.dataset.lang) {
      I18n.switchLang(btn.dataset.lang).catch((err) => console.error('I18n switch error:', err));
    }
  });
});
