let charts = {
  line: null,
  donut: null,
  radar: null,
  bar: null
};

function setErr(msg) {
  const box = document.getElementById('errBox');
  if (!box) return;
  if (!msg) {
    box.style.display = 'none';
    box.textContent = '';
    return;
  }
  box.style.display = 'block';
  box.textContent = msg;
}

function safeNum(n, fallback = 0) {
  return typeof n === 'number' && Number.isFinite(n) ? n : fallback;
}

function dayKey(dateStr) {
  try {
    const d = new Date(dateStr);
    if (Number.isNaN(d.getTime())) return '';
    return d.toISOString().slice(0, 10);
  } catch {
    return '';
  }
}

function getProviderModel(ext) {
  const modelVal = (ext && ext.model) ? String(ext.model).trim() : '';
  const providerVal = (ext && ext.provider) ? String(ext.provider).trim() : '';
  if (window.ModelLabels && typeof window.ModelLabels.resolveKey === 'function') {
    const key = window.ModelLabels.resolveKey({ model: modelVal, provider: providerVal });
    return key || modelVal || providerVal || 'inconnu';
  }
  return (ext && (ext.model || ext.provider)) ? String(ext.model || ext.provider) : '' || 'inconnu';
}

function getProviderModelLabel(ext) {
  const modelVal = (ext && ext.model) ? String(ext.model).trim() : '';
  const providerVal = (ext && ext.provider) ? String(ext.provider).trim() : '';
  if (window.ModelLabels && typeof window.ModelLabels.resolve === 'function') {
    return window.ModelLabels.resolve({ model: modelVal, provider: providerVal });
  }
  return (ext && (ext.model || ext.provider)) ? String(ext.model || ext.provider) : '' || 'inconnu';
}

function getCompany(ext) {
  const c = ext && ext.company ? String(ext.company).trim() : '';
  return c || '—';
}

function getDocName(ext) {
  const f = ext && ext.document_file ? String(ext.document_file).trim() : '';
  return f || '';
}

function extractSections(ext) {
  const ui = ext && ext.ui_result && typeof ext.ui_result === 'object' ? ext.ui_result : null;
  const raw = ext && ext.result && typeof ext.result === 'object' ? ext.result : null;
  const src = ui || (raw && raw.result && typeof raw.result === 'object' ? raw.result : raw) || null;
  if (!src || typeof src !== 'object') return null;
  return {
    strategic: src.diagnostic_strategique,
    financier: src.diagnostic_financier,
    rh: src.diagnostic_rh,
    data: src.diagnostic_data,
    cyber: src.diagnostic_cyber_gouvernance
  };
}

function avgConfidenceInSection(sectionObj) {
  if (!sectionObj || typeof sectionObj !== 'object') return null;
  let total = 0;
  let count = 0;
  for (const v of Object.values(sectionObj)) {
    if (v && typeof v === 'object') {
      const c = v.confiance;
      if (typeof c === 'number' && Number.isFinite(c)) {
        total += c;
        count += 1;
      }
    }
  }
  if (!count) return null;
  return total / count;
}

function isValueFilled(val) {
  if (Array.isArray(val)) return val.length > 0;
  if (val === null || val === undefined) return false;
  return String(val).trim() !== '';
}

function completenessInSection(sectionObj, minConfidence = 0.6) {
  if (!sectionObj || typeof sectionObj !== 'object') return null;
  let total = 0;
  let filled = 0;
  for (const v of Object.values(sectionObj)) {
    if (v && typeof v === 'object') {
      total += 1;
      const okValue = isValueFilled(v.valeur);
      const conf = v.confiance;
      const okConf = typeof conf === 'number' && Number.isFinite(conf) ? conf >= minConfidence : true;
      if (okValue && okConf) filled += 1;
    }
  }
  if (!total) return null;
  return filled / total;
}

function computeCompletenessMetrics(extractions, minConfidence = 0.6) {
  const perExt = [];
  for (const ext of extractions) {
    const sec = extractSections(ext);
    if (!sec) continue;
    const parts = [];
    const vals = [
      completenessInSection(sec.strategic, minConfidence),
      completenessInSection(sec.financier, minConfidence),
      completenessInSection(sec.rh, minConfidence),
      completenessInSection(sec.data, minConfidence),
      completenessInSection(sec.cyber, minConfidence)
    ];
    for (const v of vals) {
      if (v != null) parts.push(v);
    }
    if (parts.length) perExt.push(parts.reduce((a, b) => a + b, 0) / parts.length);
  }
  if (!perExt.length) return { overall: null };
  const overall = perExt.reduce((a, b) => a + b, 0) / perExt.length;
  return { overall };
}

function computeConfidenceMetrics(extractions) {
  const perSec = { strategic: [], financier: [], rh: [], data: [], cyber: [] };
  const perExt = [];

  for (const ext of extractions) {
    const sec = extractSections(ext);
    if (!sec) continue;
    const vals = {
      strategic: avgConfidenceInSection(sec.strategic),
      financier: avgConfidenceInSection(sec.financier),
      rh: avgConfidenceInSection(sec.rh),
      data: avgConfidenceInSection(sec.data),
      cyber: avgConfidenceInSection(sec.cyber)
    };
    const parts = [];
    for (const k of Object.keys(perSec)) {
      if (vals[k] != null) {
        perSec[k].push(vals[k]);
        parts.push(vals[k]);
      }
    }
    if (parts.length) {
      perExt.push(parts.reduce((a, b) => a + b, 0) / parts.length);
    }
  }

  const avg = (arr) => arr.length ? (arr.reduce((a, b) => a + b, 0) / arr.length) : null;
  return {
    overall: avg(perExt),
    bySection: {
      strategic: avg(perSec.strategic),
      financier: avg(perSec.financier),
      rh: avg(perSec.rh),
      data: avg(perSec.data),
      cyber: avg(perSec.cyber)
    }
  };
}

function groupCounts(items) {
  const map = new Map();
  for (const it of items) {
    map.set(it, (map.get(it) || 0) + 1);
  }
  return map;
}

function topN(map, n = 8) {
  return Array.from(map.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, n);
}

function destroyCharts() {
  for (const k of Object.keys(charts)) {
    if (charts[k]) {
      charts[k].destroy();
      charts[k] = null;
    }
  }
}

function renderCharts(extractions) {
  destroyCharts();

  const metrics = computeConfidenceMetrics(extractions);

  const byDay = new Map();
  for (const ext of extractions) {
    const d = dayKey(ext.created_at);
    if (!d) continue;
    const m = computeConfidenceMetrics([ext]);
    const conf = m.overall;
    if (conf == null) continue;
    const v = byDay.get(d) || { total: 0, count: 0 };
    v.total += conf;
    v.count += 1;
    byDay.set(d, v);
  }

  const lineLabels = Array.from(byDay.keys()).sort();
  const lineData = lineLabels.map(k => {
    const v = byDay.get(k);
    return v && v.count ? (v.total / v.count) * 100 : 0;
  });

  const lineCanvas = document.getElementById('lineChart');
  if (lineCanvas) {
    charts.line = new Chart(lineCanvas, {
      type: 'line',
      data: {
        labels: lineLabels,
        datasets: [{
          label: 'Confiance moyenne (%)',
          data: lineData,
          borderColor: '#3C57F3',
          backgroundColor: 'rgba(60,87,243,0.18)',
          tension: 0.35,
          fill: true,
          pointRadius: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: { min: 0, max: 100 }
        },
        plugins: { legend: { display: true } }
      }
    });
  }

  const modelKeys = extractions.map(getProviderModel);
  const modelLabels = extractions.map(getProviderModelLabel);
  const merged = new Map();
  for (let i = 0; i < modelKeys.length; i++) {
    const k = modelKeys[i];
    const lbl = modelLabels[i];
    if (!merged.has(k)) {
      merged.set(k, { count: 0, label: lbl || k });
    }
    merged.get(k).count += 1;
  }
  const donutLabels = Array.from(merged.values()).map(v => v.label);
  const donutData = Array.from(merged.values()).map(v => v.count);
  const donutTooltips = Array.from(merged.values()).map(v => `${v.label}: ${v.count} analyse(s)`);
  const donutCanvas = document.getElementById('donutChart');
  if (donutCanvas) {
    charts.donut = new Chart(donutCanvas, {
      type: 'doughnut',
      data: {
        labels: donutLabels,
        datasets: [{
          data: donutData,
          backgroundColor: [
            '#3C57F3',
            '#7525E0',
            '#f39c12',
            '#ff4d4d',
            '#7f8c8d',
            '#9b59b6'
          ]
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' },
          tooltip: {
            callbacks: {
              label(ctx) {
                if (ctx.datasetIndex === 0 && Array.isArray(donutTooltips) && donutTooltips[ctx.dataIndex]) {
                  return donutTooltips[ctx.dataIndex];
                }
                const label = ctx.label || '';
                const val = typeof ctx.parsed === 'number' ? ctx.parsed : 0;
                return `${label}: ${val} analyse(s)`;
              }
            }
          }
        }
      }
    });
  }

  const radarCanvas = document.getElementById('radarChart');
  if (radarCanvas) {
    const r = metrics.bySection;
    const labels = ['Stratégique', 'Financier', 'RH', 'Data', 'Cyber'];
    const data = [
      safeNum(r.strategic, 0) * 5,
      safeNum(r.financier, 0) * 5,
      safeNum(r.rh, 0) * 5,
      safeNum(r.data, 0) * 5,
      safeNum(r.cyber, 0) * 5
    ];
    charts.radar = new Chart(radarCanvas, {
      type: 'radar',
      data: {
        labels,
        datasets: [{
          label: 'Maturité (0–5)',
          data,
          borderColor: '#7525E0',
          backgroundColor: 'rgba(117,37,224,0.16)',
          pointBackgroundColor: '#7525E0'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { r: { min: 0, max: 5, ticks: { stepSize: 1 } } },
        plugins: { legend: { display: true } }
      }
    });
  }

  const companies = extractions.map(getCompany).filter(c => c && c !== '—');
  const companyCounts = groupCounts(companies);
  const top = topN(companyCounts, 8);
  const barLabels = top.map(([k]) => k);
  const barData = top.map(([, v]) => v);
  const barCanvas = document.getElementById('barChart');
  if (barCanvas) {
    charts.bar = new Chart(barCanvas, {
      type: 'bar',
      data: {
        labels: barLabels,
        datasets: [{
          label: 'Analyses',
          data: barData,
          backgroundColor: 'rgba(60,87,243,0.18)',
          borderColor: '#3C57F3',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true, precision: 0 } },
        plugins: { legend: { display: true } }
      }
    });
  }
}

function setKpis(extractions) {
  const kpiCount = document.getElementById('kpiCount');
  const kpiCountHint = document.getElementById('kpiCountHint');
  const kpiConfidence = document.getElementById('kpiConfidence');
  const kpiCompleteness = document.getElementById('kpiCompleteness');
  const kpiQuality = document.getElementById('kpiQuality');

  const count = extractions.length;
  if (kpiCount) kpiCount.textContent = String(count);

  if (kpiCountHint) {
    const docs = new Set(extractions.map(getDocName).filter(Boolean));
    const companies = new Set(extractions.map(getCompany).filter(c => c && c !== '—'));
    const parts = [];
    if (docs.size) parts.push(`${docs.size} document(s) distinct(s)`);
    if (companies.size) parts.push(`${companies.size} entreprise(s)`);
    kpiCountHint.textContent = parts.join(' · ');
  }

  const metrics = computeConfidenceMetrics(extractions);
  if (kpiConfidence) {
    if (metrics.overall == null) kpiConfidence.textContent = '—';
    else kpiConfidence.textContent = `${(metrics.overall * 100).toFixed(1)}%`;
  }

  const comp = computeCompletenessMetrics(extractions, 0.6);
  if (kpiCompleteness) {
    if (comp.overall == null) kpiCompleteness.textContent = '—';
    else kpiCompleteness.textContent = `${(comp.overall * 100).toFixed(1)}%`;
  }

  if (kpiQuality) {
    if (metrics.overall == null || comp.overall == null) kpiQuality.textContent = '—';
    else kpiQuality.textContent = `${(metrics.overall * comp.overall * 100).toFixed(1)}%`;
  }
}

function fillSelect(select, items, options = {}) {
  if (!select) return;
  const withAll = options.withAll !== false;
  const allLabel = typeof options.allLabel === 'string' ? options.allLabel : 'Toutes';
  select.innerHTML = '';
  if (withAll) {
    const opt = document.createElement('option');
    opt.value = '';
    opt.textContent = allLabel;
    select.appendChild(opt);
  }
  for (const it of items) {
    const opt = document.createElement('option');
    if (it && typeof it === 'object' && (it.value != null || it.text != null)) {
      opt.value = it.value != null ? String(it.value) : (it.text != null ? String(it.text) : '');
      opt.textContent = it.text != null ? String(it.text) : (it.value != null ? String(it.value) : '');
    } else {
      opt.value = it;
      opt.textContent = it;
    }
    select.appendChild(opt);
  }
}

function applyFilters(all) {
  const company = (document.getElementById('companyFilter') || {}).value || '';
  const model = String((document.getElementById('modelFilter') || {}).value || '').trim();
  const from = (document.getElementById('fromDate') || {}).value || '';
  const to = (document.getElementById('toDate') || {}).value || '';

  const fromTs = from ? new Date(from).getTime() : null;
  const toTs = to ? new Date(to + 'T23:59:59').getTime() : null;

  return all.filter(ext => {
    if (company && getCompany(ext) !== company) return false;
    if (model) {
      const extKey = String(getProviderModel(ext) || '').toLowerCase();
      const extLabel = String(getProviderModelLabel(ext) || '').toLowerCase();
      const rawModel = String(ext?.model || '').toLowerCase();
      const rawProvider = String(ext?.provider || '').toLowerCase();
      const wanted = model.toLowerCase();
      const ok =
        extKey === wanted ||
        extLabel.includes(wanted) ||
        rawModel.includes(wanted) ||
        rawProvider.includes(wanted);
      if (!ok) return false;
    }
    const ts = ext.created_at ? new Date(ext.created_at).getTime() : null;
    if (fromTs != null && ts != null && ts < fromTs) return false;
    if (toTs != null && ts != null && ts > toTs) return false;
    return true;
  });
}

async function loadAllExtractions() {
  setErr('');
  const res = await Auth.apiFetch(`${API_URL}/extractions?limit=200`);
  const data = await res.json();
  if (!data || !data.ok) {
    throw new Error((data && data.error) ? data.error : 'Erreur chargement extractions');
  }
  return Array.isArray(data.data) ? data.data : [];
}

function updateUI(allExtractions) {
  const companyEl = document.getElementById('companyFilter');
  const modelEl = document.getElementById('modelFilter');
  const prevCompany = companyEl ? companyEl.value : '';
  const prevModel = modelEl ? modelEl.value : '';

  const companySet = new Set(allExtractions.map(getCompany).filter(c => c && c !== '—'));
  const modelKeyLabel = new Map();
  for (const ext of allExtractions) {
    const k = getProviderModel(ext);
    if (!k || k === 'inconnu') continue;
    const lbl = getProviderModelLabel(ext);
    if (!modelKeyLabel.has(k)) {
      modelKeyLabel.set(k, lbl || k);
    }
  }
  const modelItems = Array.from(modelKeyLabel.entries())
    .sort((a, b) => (a[1] > b[1] ? 1 : a[1] < b[1] ? -1 : 0))
    .map(([key, label]) => ({ value: key, text: label }));

  fillSelect(companyEl, Array.from(companySet).sort(), { withAll: true, allLabel: 'Toutes' });
  fillSelect(modelEl, modelItems, { withAll: true, allLabel: 'Tous' });
  if (companyEl && prevCompany) companyEl.value = prevCompany;
  if (modelEl && prevModel) modelEl.value = prevModel;

  const filtered = applyFilters(allExtractions);
  setKpis(filtered);
  renderCharts(filtered);

  if (!filtered.length) {
    setErr("Aucune donnée pour ces filtres. Essayez d’élargir la période ou de retirer un filtre.");
  } else {
    setErr('');
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const all = await loadAllExtractions();
    updateUI(all);
    document.getElementById('btnApply').addEventListener('click', () => updateUI(all));
  } catch (e) {
    setErr(e && e.message ? e.message : 'Erreur chargement dashboard');
  }
});
