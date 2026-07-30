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
    this.enhanceSwitchers();
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
    this.syncSwitcherLabels();
  },

  enhanceSwitchers() {
    document.querySelectorAll('.lang-switcher').forEach((switcher, index) => {
      if (switcher.dataset.i18nEnhanced === '1') return;
      switcher.dataset.i18nEnhanced = '1';
      switcher.classList.add('lang-switcher-dropdown');

      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'lang-current';
      toggle.setAttribute('aria-haspopup', 'true');
      toggle.setAttribute('aria-expanded', 'false');
      toggle.innerHTML = `
        <span class="lang-current-icon" aria-hidden="true">🌐</span>
        <span class="lang-current-label">FR</span>
        <span class="lang-current-caret" aria-hidden="true">▾</span>
      `;

      const menu = document.createElement('div');
      menu.className = 'lang-menu';
      menu.setAttribute('role', 'menu');

      const buttons = Array.from(switcher.querySelectorAll('.lang-btn'));
      buttons.forEach((btn) => {
        btn.type = 'button';
        btn.classList.add('lang-menu-btn');
        menu.appendChild(btn);
      });

      switcher.innerHTML = '';
      switcher.appendChild(toggle);
      switcher.appendChild(menu);

      toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        const willOpen = !switcher.classList.contains('open');
        document.querySelectorAll('.lang-switcher.open').forEach((other) => {
          other.classList.remove('open');
          const otherToggle = other.querySelector('.lang-current');
          if (otherToggle) otherToggle.setAttribute('aria-expanded', 'false');
        });
        switcher.classList.toggle('open', willOpen);
        toggle.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
      });

      menu.addEventListener('click', () => {
        switcher.classList.remove('open');
        toggle.setAttribute('aria-expanded', 'false');
      });

      if (index === 0) {
        document.addEventListener('click', (e) => {
          document.querySelectorAll('.lang-switcher.open').forEach((openSwitcher) => {
            if (!openSwitcher.contains(e.target)) {
              openSwitcher.classList.remove('open');
              const openToggle = openSwitcher.querySelector('.lang-current');
              if (openToggle) openToggle.setAttribute('aria-expanded', 'false');
            }
          });
        });
      }
    });
    this.syncSwitcherLabels();
  },

  syncSwitcherLabels() {
    document.querySelectorAll('.lang-switcher').forEach((switcher) => {
      const label = switcher.querySelector('.lang-current-label');
      if (label) label.textContent = String(this.currentLang || 'fr').toUpperCase();
    });
  },

  injectStyles() {
    if (document.getElementById('i18n-styles')) return;
    const style = document.createElement('style');
    style.id = 'i18n-styles';
    style.textContent = `
      .lang-switcher {
        position: relative;
        display: inline-flex;
        align-items: center;
        align-items: center;
      .lang-current,
      .lang-btn {
        font-family: var(--mono);
      }
      .lang-current {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        min-width: 68px;
        justify-content: center;
        padding: 6px 10px;
        border: 1px solid var(--line, var(--border));
        border-radius: 8px;
        border-radius: 6px;
        color: var(--muted);
        font-size: 10px;
        color: var(--ink, var(--text));
        font-family: var(--mono);
        transition: all 0.2s ease;
      .lang-current:hover,
      .lang-switcher.open .lang-current {
        border-color: var(--blue);
        background: rgba(60,87,243,0.10);
      }
      .lang-current-icon,
      .lang-current-caret {
        opacity: 0.85;
      }
      .lang-current-label {
        font-weight: 600;
        letter-spacing: 0.08em;
      }
      .lang-menu {
        position: absolute;
        top: calc(100% + 8px);
        right: 0;
        min-width: 78px;
        padding: 6px;
        border: 1px solid var(--line, var(--border));
        border-radius: 10px;
        background: var(--paper-2, var(--surface));
        box-shadow: 0 12px 32px rgba(0,0,0,0.18);
        display: none;
        flex-direction: column;
        gap: 4px;
        z-index: 220;
      }
      .lang-switcher.open .lang-menu {
        display: flex;
      }
      .lang-btn {
        width: 100%;
        padding: 7px 10px;
        border: 1px solid transparent;
        border-radius: 8px;
        background: transparent;
        color: var(--muted);
        font-size: 10px;
        cursor: pointer;
        text-align: left;
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
