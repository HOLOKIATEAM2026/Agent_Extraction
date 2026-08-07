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
  resolve(extOrModel, provider) {
    let modelVal = '';
    let providerVal = '';
    if (extOrModel && typeof extOrModel === 'object') {
      modelVal = String(extOrModel.model || '').trim();
      providerVal = String(extOrModel.provider || '').trim();
    } else {
      modelVal = String(extOrModel || '').trim();
      providerVal = String(provider || '').trim();
    }
    const m = modelVal;
    const p = providerVal;
    const found = MODEL_LABEL_MAP.find(o => o.match(m, p));
    if (found) return found.label;
    if (m) return m;
    return p || '—';
  },
  resolveKey(extOrModel, provider) {
    let modelVal = '';
    let providerVal = '';
    if (extOrModel && typeof extOrModel === 'object') {
      modelVal = String(extOrModel.model || '').trim();
      providerVal = String(extOrModel.provider || '').trim();
    } else {
      modelVal = String(extOrModel || '').trim();
      providerVal = String(provider || '').trim();
    }
    const m = modelVal;
    const p = providerVal;
    const found = MODEL_LABEL_MAP.find(o => o.match(m, p));
    if (found) return found.key;
    return m || p || '';
  }
};