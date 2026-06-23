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
  const model = (ext && (ext.model || ext.provider)) ? String(ext.model || ext.provider) : '';
  return model || 'inconnu';
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
          borderColor: '#0047ff',
          backgroundColor: 'rgba(0,71,255,0.12)',
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

  const models = extractions.map(getProviderModel);
  const modelCounts = groupCounts(models);
  const donutLabels = Array.from(modelCounts.keys());
  const donutData = donutLabels.map(k => modelCounts.get(k));
  const donutCanvas = document.getElementById('donutChart');
  if (donutCanvas) {
    charts.donut = new Chart(donutCanvas, {
      type: 'doughnut',
      data: {
        labels: donutLabels,
        datasets: [{
          data: donutData,
          backgroundColor: [
            '#0047ff',
            '#00c896',
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
        plugins: { legend: { position: 'bottom' } }
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
          borderColor: '#00c896',
          backgroundColor: 'rgba(0,200,150,0.12)',
          pointBackgroundColor: '#00c896'
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
          backgroundColor: 'rgba(0,71,255,0.18)',
          borderColor: '#0047ff',
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
  const kpiCompanies = document.getElementById('kpiCompanies');
  const kpiConfidence = document.getElementById('kpiConfidence');

  const count = extractions.length;
  if (kpiCount) kpiCount.textContent = String(count);

  if (kpiCountHint) {
    const docs = new Set(extractions.map(getDocName).filter(Boolean));
    kpiCountHint.textContent = docs.size ? `${docs.size} document(s) distinct(s)` : '';
  }

  const companies = new Set(extractions.map(getCompany).filter(c => c && c !== '—'));
  if (kpiCompanies) kpiCompanies.textContent = String(companies.size);

  const metrics = computeConfidenceMetrics(extractions);
  if (kpiConfidence) {
    if (metrics.overall == null) kpiConfidence.textContent = '—';
    else kpiConfidence.textContent = `${(metrics.overall * 100).toFixed(1)}%`;
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
    opt.value = it;
    opt.textContent = it;
    select.appendChild(opt);
  }
}

function applyFilters(all) {
  const company = (document.getElementById('companyFilter') || {}).value || '';
  const model = (document.getElementById('modelFilter') || {}).value || '';
  const from = (document.getElementById('fromDate') || {}).value || '';
  const to = (document.getElementById('toDate') || {}).value || '';

  const fromTs = from ? new Date(from).getTime() : null;
  const toTs = to ? new Date(to + 'T23:59:59').getTime() : null;

  return all.filter(ext => {
    if (company && getCompany(ext) !== company) return false;
    if (model && getProviderModel(ext) !== model) return false;
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
  const modelSet = new Set(allExtractions.map(getProviderModel));

  fillSelect(companyEl, Array.from(companySet).sort(), { withAll: true, allLabel: 'Toutes' });
  fillSelect(modelEl, Array.from(modelSet).sort(), { withAll: true, allLabel: 'Tous' });
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
