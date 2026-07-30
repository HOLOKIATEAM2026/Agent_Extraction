const I18n = {
  currentLang: 'fr',
  fallbackLang: 'fr',
  translations: {},
  cache: {},
  languageMeta: {
    fr: { label: 'Français', code: 'FR' },
    en: { label: 'English', code: 'EN' },
    es: { label: 'Español', code: 'ES' }
  },

  async init() {
    let saved = 'fr';
    try {
      saved = localStorage.getItem('holokia_lang') || 'fr';
    } catch (_) {}
    this.currentLang = ['fr', 'en', 'es'].includes(saved) ? saved : 'fr';
    await this.load(this.currentLang);
    this.applyTranslations(document);
    this.updateLanguageSwitcher();
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
    this.updateLanguageSwitcher();
    document.documentElement.lang = lang;
    document.dispatchEvent(new CustomEvent('i18n:updated', { detail: { lang } }));
  },

  updateLanguageSwitcher() {
    const meta = this.languageMeta[this.currentLang] || this.languageMeta.fr;
    document.querySelectorAll('.lang-switcher').forEach((switcher) => {
      const trigger = switcher.querySelector('.lang-trigger');
      const label = switcher.querySelector('.lang-trigger-label');
      const code = switcher.querySelector('.lang-trigger-code');
      if (label) label.textContent = meta.label;
      if (code) code.textContent = meta.code;
      if (trigger) trigger.setAttribute('aria-label', `Language: ${meta.label}`);

      switcher.querySelectorAll('.lang-option').forEach((option) => {
        const active = option.dataset.lang === this.currentLang;
        option.classList.toggle('active', active);
        option.setAttribute('aria-selected', active ? 'true' : 'false');
      });
      switcher.classList.remove('open');
      if (trigger) trigger.setAttribute('aria-expanded', 'false');
    });
  },

  injectStyles() {
    if (document.getElementById('i18n-styles')) return;
    const style = document.createElement('style');
    style.id = 'i18n-styles';
    style.textContent = `
      .lang-switcher {
        position: relative;
        display: flex;
        align-items: center;
      }
      .lang-trigger {
        min-width: 132px;
        padding: 7px 10px;
        border: 1px solid var(--line, var(--border));
        border-radius: 10px;
        background: color-mix(in srgb, var(--paper-2, #fff) 92%, transparent);
        color: var(--ink, var(--text));
        display: inline-flex;
        align-items: center;
        gap: 8px;
        cursor: pointer;
        font-family: var(--mono);
        font-size: 10px;
        transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
      }
      .lang-trigger:hover,
      .lang-switcher.open .lang-trigger {
        border-color: rgba(60,87,243,0.55);
        background: rgba(60,87,243,0.10);
        box-shadow: 0 12px 28px rgba(60,87,243,0.16);
      }
      .lang-trigger:focus-visible,
      .lang-option:focus-visible {
        outline: 2px solid rgba(60,87,243,0.55);
        outline-offset: 2px;
      }
      .lang-trigger-icon {
        font-size: 14px;
        line-height: 1;
      }
      .lang-trigger-text {
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        gap: 1px;
        flex: 1;
        min-width: 0;
      }
      .lang-trigger-label {
        color: var(--ink, var(--text));
        font-size: 11px;
        white-space: nowrap;
      }
      .lang-trigger-code {
        color: var(--muted);
        font-size: 9px;
        letter-spacing: 0.08em;
      }
      .lang-trigger-caret {
        color: var(--muted);
        transition: transform 0.2s ease;
      }
      .lang-switcher.open .lang-trigger-caret {
        transform: rotate(180deg);
      }
      .lang-menu {
        position: absolute;
        top: calc(100% + 8px);
        right: 0;
        min-width: 180px;
        padding: 8px;
        border: 1px solid var(--line, var(--border));
        border-radius: 14px;
        background: color-mix(in srgb, var(--paper-2, #fff) 96%, transparent);
        backdrop-filter: blur(16px);
        box-shadow: 0 18px 42px rgba(15, 23, 42, 0.18);
        display: none;
        flex-direction: column;
        gap: 4px;
        z-index: 120;
      }
      .lang-switcher.open .lang-menu {
        display: flex;
      }
      .lang-option {
        width: 100%;
        border: 0;
        background: transparent;
        color: var(--ink, var(--text));
        border-radius: 10px;
        padding: 10px 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        cursor: pointer;
        font-family: var(--mono);
        font-size: 11px;
        transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
      }
      .lang-option:hover {
        background: rgba(60,87,243,0.10);
        transform: translateX(1px);
      }
      .lang-option.active {
        background: rgba(60,87,243,0.14);
        color: var(--blue);
      }
      .lang-option-code {
        color: var(--muted);
        font-size: 10px;
        letter-spacing: 0.08em;
      }
      .lang-option.active .lang-option-code {
        color: var(--blue);
      }
      @media (max-width: 768px) {
        .lang-trigger {
          min-width: 110px;
          padding: 6px 9px;
        }
        .lang-trigger-label {
          font-size: 10px;
        }
        .lang-menu {
          right: auto;
          left: 0;
          min-width: 160px;
        }
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
    const trigger = e.target.closest('.lang-trigger');
    if (trigger) {
      const switcher = trigger.closest('.lang-switcher');
      const willOpen = !switcher.classList.contains('open');
      document.querySelectorAll('.lang-switcher.open').forEach((el) => {
        el.classList.remove('open');
        const openTrigger = el.querySelector('.lang-trigger');
        if (openTrigger) openTrigger.setAttribute('aria-expanded', 'false');
      });
      switcher.classList.toggle('open', willOpen);
      trigger.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
      return;
    }

    const option = e.target.closest('.lang-option');
    if (option && option.dataset.lang) {
      I18n.switchLang(option.dataset.lang).catch((err) => console.error('I18n switch error:', err));
      return;
    }

    if (!e.target.closest('.lang-switcher')) {
      document.querySelectorAll('.lang-switcher.open').forEach((el) => {
        el.classList.remove('open');
        const openTrigger = el.querySelector('.lang-trigger');
        if (openTrigger) openTrigger.setAttribute('aria-expanded', 'false');
      });
    }
  });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.lang-switcher.open').forEach((el) => {
        el.classList.remove('open');
        const openTrigger = el.querySelector('.lang-trigger');
        if (openTrigger) openTrigger.setAttribute('aria-expanded', 'false');
      });
    }
  });
});
