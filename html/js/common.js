const observer = new IntersectionObserver(entries => {
  entries.forEach((e,i) => {
    if(e.isIntersecting){
      e.target.style.transitionDelay = (i * 0.08) + 's';
      e.target.classList.add('visible');
    }
  });
},{threshold:0.1});
document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

// animate bench bars on scroll
const benchObs = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if(e.isIntersecting){
      e.target.querySelectorAll('.bench-bar').forEach(bar => {
        const w = bar.style.width;
        bar.style.width = '0';
        requestAnimationFrame(() => {
          requestAnimationFrame(() => { bar.style.width = w; });
        });
      });
      benchObs.unobserve(e.target);
    }
  });
},{threshold:0.3});
document.querySelectorAll('.tech-panel').forEach(p => benchObs.observe(p));

const MODEL_LABEL_MAP = [
  {
    key: 'gpt-4o',
    label: 'GPT-4o',
    match: (m, p) =>
      ['gpt-4o', 'openai'].includes(m) ||
      (typeof m === 'string' && m.toLowerCase().includes('gpt-4o')) ||
      (typeof p === 'string' && p.toLowerCase() === 'openai' && (!m || typeof m === 'string' && !m.toLowerCase().includes('groq')))
  },
  {
    key: 'llama-3.3-70b-versatile',
    label: 'LLaMA 3.3 70B',
    match: (m, p) =>
      typeof m === 'string' && (m === 'llama-3.3-70b-versatile' || m.toLowerCase().includes('llama 3.3') || m.toLowerCase().includes('llama-3.3') || m.toLowerCase().includes('llama3.3') || m.toLowerCase().includes('llama3 3.3') || m.toLowerCase().includes('llama-3.3-70b'))
  },
  {
    key: 'llama-3.1-8b-instant',
    label: 'LLaMA 3.1 8B',
    match: (m, p) =>
      m === 'groq' ||
      m === 'llama-3.1-8b-instant' ||
      (typeof m === 'string' && (m.toLowerCase().includes('llama 3.1') || m.toLowerCase().includes('llama-3.1') || m.toLowerCase().includes('llama3.1') || m.toLowerCase().includes('llama3 3.1') || m.toLowerCase().includes('llama-3.1-8b'))) ||
      (typeof p === 'string' && p.toLowerCase() === 'groq' && (!m || (typeof m === 'string' && !m.toLowerCase().includes('llama 3.3') && !m.toLowerCase().includes('llama-3.3') && !m.toLowerCase().includes('llama3.3') && !m.toLowerCase().includes('llama-3.3-70b'))))
  },
  {
    key: 'mistral',
    label: 'Mistral 7B',
    match: (m, p) =>
      (typeof m === 'string' && m.toLowerCase().includes('mistral')) ||
      (typeof p === 'string' && p.toLowerCase().includes('ollama') && typeof m === 'string' && m.toLowerCase().includes('mistral'))
  },
  {
    key: 'qwen3:8b',
    label: 'Qwen 3 8B',
    match: (m, p) =>
      (typeof m === 'string' && m.toLowerCase().includes('qwen')) ||
      (typeof p === 'string' && p.toLowerCase().includes('ollama') && typeof m === 'string' && m.toLowerCase().includes('qwen'))
  }
];

window.ModelLabels = {
  allOptions() {
    return MODEL_LABEL_MAP.map(o => ({ key: o.key, label: o.label }));
  },
  _extractModelAndProvider(extOrModel, provider) {
    let modelVal = '';
    let providerVal = '';
    if (extOrModel && typeof extOrModel === 'object') {
      const ext = extOrModel;
      const extractMetaModel = (obj) => {
        if (!obj || typeof obj !== 'object') return '';
        const meta = obj.meta;
        if (meta && typeof meta === 'object') {
          const v = meta.modele_utilise || meta.model || meta.model_name || meta.modelName;
          if (typeof v === 'string' && v.trim()) return v.trim();
          const p = meta.provider;
          if (typeof p === 'string' && p.trim() && !providerVal) providerVal = p.trim();
        }
        return '';
      };
      modelVal = String(ext.model || '').trim();
      providerVal = String(ext.provider || '').trim();
      const altModels = [
        extractMetaModel(ext.ui_result),
        extractMetaModel(ext.result),
        typeof ext.result === 'object' && ext.result && typeof ext.result.result === 'object' ? extractMetaModel(ext.result.result) : '',
        typeof ext.result === 'object' && ext.result && typeof ext.result.final === 'object' ? extractMetaModel(ext.result.final) : '',
      ].filter(Boolean);
      const hasBadGenericTop = ['groq', 'openai', 'ollama'].includes(modelVal.toLowerCase()) || !modelVal;
      if (altModels.length && hasBadGenericTop) {
        const specific = altModels.find(v => {
          const s = String(v).toLowerCase();
          return (
            s.includes('llama') || s.includes('gpt') || s.includes('mistral') || s.includes('qwen') ||
            s.includes('llama-3') || s.includes('llama3') || s.includes('gpt-4o') ||
            s.includes('8b') || s.includes('70b') || s.includes('4o')
          );
        });
        modelVal = specific || altModels[0] || modelVal;
      } else if (altModels.length && !modelVal) {
        modelVal = altModels[0];
      }
      if (!providerVal && extOrModel && typeof extOrModel === 'object') {
        const providers = [
          (ext.ui_result && ext.ui_result.meta && ext.ui_result.meta.provider) || '',
          (ext.result && ext.result.meta && ext.result.meta.provider) || '',
        ].filter(Boolean);
        if (providers.length) providerVal = String(providers[0]).trim();
      }
    } else {
      modelVal = String(extOrModel || '').trim();
      providerVal = String(provider || '').trim();
    }
    return { modelVal, providerVal };
  },
  resolve(extOrModel, provider) {
    const { modelVal, providerVal } = this._extractModelAndProvider(extOrModel, provider);
    const m = modelVal;
    const p = providerVal;
    const found = MODEL_LABEL_MAP.find(o => o.match(m, p));
    if (found) return found.label;
    if (m) return m;
    return p || '—';
  },
  resolveKey(extOrModel, provider) {
    const { modelVal, providerVal } = this._extractModelAndProvider(extOrModel, provider);
    const m = modelVal;
    const p = providerVal;
    const found = MODEL_LABEL_MAP.find(o => o.match(m, p));
    if (found) return found.key;
    return m || p || '';
  }
};