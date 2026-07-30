const fileInput = document.getElementById('fileInput');
const modelSelect = document.getElementById('modelSelect');
const approachSelect = document.getElementById('approachSelect');
const btnExtract = document.getElementById('btnExtract');
const statusText = document.getElementById('statusText');
const resultsSection = document.getElementById('results');
const cardsGrid = document.getElementById('cardsGrid');
const jsonOutput = document.getElementById('jsonOutput');
const btnCopy = document.getElementById('btnCopy');
const btnExportPdf = document.getElementById('btnExportPdf');

function tr(key, vars) {
  if (window.I18n && typeof window.I18n.t === 'function') {
    return window.I18n.t(key, vars);
  }
  return key;
}

const EXPORT_SECTIONS = [
  { key: 'diagnostic_strategique', title: 'Diagnostic Strategique' },
  { key: 'diagnostic_financier', title: 'Diagnostic Financier' },
  { key: 'diagnostic_rh', title: 'Diagnostic RH' },
  { key: 'diagnostic_data', title: 'Maturite Data' },
  { key: 'diagnostic_cyber_gouvernance', title: 'Cyber & Gouvernance' }
];

function hasFieldValue(fieldData) {
  if (!fieldData) return false;
  if (Array.isArray(fieldData.valeur)) return fieldData.valeur.length > 0;
  return fieldData.valeur !== null && fieldData.valeur !== undefined && String(fieldData.valeur).trim() !== '';
}

function fieldToText(fieldData) {
  if (!fieldData || !hasFieldValue(fieldData)) return 'Non specifie';
  if (Array.isArray(fieldData.valeur)) return fieldData.valeur.join(', ');
  return String(fieldData.valeur);
}

function cleanPdfText(text) {
  return String(text || '')
    .replace(/[^\x20-\x7E\u00A0-\u017F]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function labelFromKey(key) {
  return String(key || '').replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase());
}

function getExportFileName(data) {
  const company = (((data || {}).meta || {}).entreprise || 'diagnostic').toString();
  const safe = company.replace(/[<>:"/\\|?*\x00-\x1F]/g, '_').replace(/\s+/g, '_');
  return `Holokia_Diagnostic_${safe}.pdf`;
}

async function loadLogoDataUrl() {
  const candidates = [
    'logo/cropped-logo_holokia_noir.avif',
    'logo/cropped-logo_holokia_noir.jpg'
  ];
  for (const src of candidates) {
    try {
      const img = await new Promise((resolve, reject) => {
        const el = new Image();
        el.crossOrigin = 'anonymous';
        el.onload = () => resolve(el);
        el.onerror = reject;
        el.src = src;
      });
      const canvas = document.createElement('canvas');
      canvas.width = img.naturalWidth || img.width;
      canvas.height = img.naturalHeight || img.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      return canvas.toDataURL('image/png');
    } catch (_) {}
  }
  return null;
}

async function exportDiagnosticPdf(data) {
  if (!data) {
    alert(tr('diagnostic.export_no_data'));
    return;
  }
  if (!window.jspdf || !window.jspdf.jsPDF) {
    alert(tr('diagnostic.export_lib_missing'));
    return;
  }

  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 14;
  const contentWidth = pageWidth - (margin * 2);
  const lineHeight = 5;
  let y = margin;

  const ensureSpace = (needed = 10) => {
    if (y + needed > pageHeight - margin) {
      pdf.addPage();
      y = margin;
    }
  };

  const drawWrapped = (text, x, size = 10, color = [20, 20, 20], gapAfter = 2) => {
    const safe = cleanPdfText(text);
    if (!safe) return;
    pdf.setFont('helvetica', 'normal');
    pdf.setFontSize(size);
    pdf.setTextColor(color[0], color[1], color[2]);
    const lines = pdf.splitTextToSize(safe, contentWidth - (x - margin));
    lines.forEach((line) => {
      ensureSpace(lineHeight + 1);
      pdf.text(line, x, y);
      y += lineHeight;
    });
    y += gapAfter;
  };

  const drawSectionTitle = (title) => {
    ensureSpace(12);
    pdf.setDrawColor(60, 87, 243);
    pdf.setLineWidth(0.6);
    pdf.line(margin, y, pageWidth - margin, y);
    y += 6;
    pdf.setFont('helvetica', 'bold');
    pdf.setFontSize(14);
    pdf.setTextColor(20, 20, 20);
    pdf.text(cleanPdfText(title), margin, y);
    y += 7;
  };

  const logoDataUrl = await loadLogoDataUrl();
  if (logoDataUrl) {
    try {
      pdf.addImage(logoDataUrl, 'PNG', margin, y, 30, 16);
    } catch (_) {}
  }

  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(20);
  pdf.setTextColor(20, 20, 20);
  pdf.text(cleanPdfText(tr('diagnostic.pdf_title')), margin + 36, y + 8);
  y += 20;

  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(10);
  pdf.setTextColor(90, 90, 90);
  const meta = (data && data.meta) || {};
  drawWrapped(tr('diagnostic.pdf_company', { company: meta.entreprise || tr('common.not_specified') }), margin, 10, [70, 70, 70], 0);
  drawWrapped(tr('diagnostic.pdf_export_date', { date: new Date().toLocaleString() }), margin, 10, [70, 70, 70], 0);
  drawWrapped(tr('diagnostic.pdf_model', { model: meta.modele_utilise || tr('common.not_specified'), provider: meta.provider || tr('common.not_specified') }), margin, 10, [70, 70, 70], 4);

  const recs = Array.isArray(data.recommandations) ? data.recommandations : [];
  if (recs.length > 0) {
    drawSectionTitle(tr('diagnostic.pdf_recommendations'));
    recs.slice(0, 3).forEach((rec, idx) => {
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(11);
      ensureSpace(8);
      pdf.text(`${idx + 1}. ${cleanPdfText(rec.titre || 'Action')}`, margin, y);
      y += 5;
      drawWrapped(rec.action || '', margin + 4, 10, [30, 30, 30], 1);
      if (rec.raison) {
        drawWrapped(tr('diagnostic.pdf_justification', { reason: rec.raison }), margin + 4, 9, [90, 90, 90], 2);
      }
      y += 1;
    });
  }

  EXPORT_SECTIONS.forEach((section) => {
    const sectionData = data[section.key] || {};
    const fields = Object.keys(sectionData);
    if (fields.length === 0) return;

    drawSectionTitle(section.title);
    fields.forEach((fieldKey) => {
      const fieldData = sectionData[fieldKey];
      pdf.setFont('helvetica', 'bold');
      pdf.setFontSize(10);
      ensureSpace(7);
      pdf.setTextColor(20, 20, 20);
      pdf.text(cleanPdfText(labelFromKey(fieldKey)), margin, y);
      y += 5;

      drawWrapped(fieldToText(fieldData), margin + 4, 10, [35, 35, 35], 1);
      if (fieldData && fieldData.source) {
        const page = fieldData.source.page != null ? `${tr('common.page')} ${fieldData.source.page}` : tr('common.page');
        drawWrapped(`${tr('common.source')}: ${page}`, margin + 4, 9, [60, 87, 243], 0);
        if (fieldData.source.extrait) {
          drawWrapped(`Extrait: ${fieldData.source.extrait}`, margin + 4, 8, [100, 100, 100], 2);
        } else {
          y += 2;
        }
      } else {
        y += 2;
      }
    });
  });

  pdf.save(getExportFileName(data));
}

function buildCards(data) {
  cardsGrid.innerHTML = '';

  const recs = Array.isArray(data && data.recommandations) ? data.recommandations : [];
  if (recs.length > 0) {
    let recHtml = `
      <div style="grid-column: 1 / -1; background:var(--paper-2); border:1px solid var(--line); padding:24px;">
        <h3 style="font-family:var(--display); font-size:24px; margin-bottom:12px;">${tr('diagnostic.actions_title')}</h3>
        <div style="font-family:var(--mono); font-size:11px; color:var(--muted); margin-bottom:16px;">${tr('diagnostic.actions_subtitle')}</div>
        <ol style="margin:0; padding-left:18px; display:flex; flex-direction:column; gap:12px;">
    `;
    recs.slice(0, 3).forEach((r) => {
      const title = r && r.titre ? String(r.titre) : 'Action';
      const action = r && r.action ? String(r.action) : '';
      const reason = r && r.raison ? String(r.raison) : '';
      const cat = r && r.categorie ? String(r.categorie) : '';
      recHtml += `
        <li>
          <div style="font-family:var(--mono); font-size:10px; color:var(--muted); margin-bottom:4px; text-transform:uppercase; letter-spacing:0.5px;">${cat}${reason ? ` • ${reason}` : ''}</div>
          <div style="font-size:14px; color:var(--ink); font-weight:600; margin-bottom:4px;">${title}</div>
          <div style="font-size:13px; color:var(--ink-2); line-height:1.5;">${action}</div>
        </li>
      `;
    });
    recHtml += `</ol></div>`;
    cardsGrid.innerHTML += recHtml;
  }
  
  const sections = [
    { key: 'diagnostic_strategique', title: 'Stratégique' },
    { key: 'diagnostic_financier', title: 'Financier' },
    { key: 'diagnostic_rh', title: 'RH' },
    { key: 'diagnostic_data', title: 'Maturité Data' },
    { key: 'diagnostic_cyber_gouvernance', title: 'Cyber & Gouvernance' }
  ];

  sections.forEach((sec) => {
    const sectionData = data[sec.key] || {};
    const fields = Object.keys(sectionData);
    
    // Check if at least one field has a value
    const hasData = fields.some(f => {
      const fieldData = sectionData[f];
      if(!fieldData) return false;
      if(Array.isArray(fieldData.valeur)) return fieldData.valeur.length > 0;
      return fieldData.valeur !== null && fieldData.valeur !== undefined && String(fieldData.valeur).trim() !== '';
    });

    let html = `
      <div style="background:var(--paper-2); border:1px solid var(--line); padding:24px;">
        <h3 style="font-family:var(--display); font-size:24px; margin-bottom:16px; display:flex; justify-content:space-between;">
          ${sec.title}
          <span style="font-family:var(--mono); font-size:12px; color:${hasData ? 'var(--green)' : 'var(--red)'};">
            ${hasData ? tr('diagnostic.data_found') : tr('diagnostic.not_found')}
          </span>
        </h3>
        <div style="display:flex; flex-direction:column; gap:12px;">
    `;

    fields.forEach(f => {
      const fieldData = sectionData[f];
      const label = f.replace(/_/g, ' ').toUpperCase();
      let value = `<span style="color:var(--muted); font-style:italic;">${tr('common.not_specified')}</span>`;
      let sourceHtml = '';

      if (fieldData) {
        const isFound = Array.isArray(fieldData.valeur) 
          ? fieldData.valeur.length > 0 
          : (fieldData.valeur !== null && fieldData.valeur !== undefined && String(fieldData.valeur).trim() !== '');

        if (isFound) {
          if (Array.isArray(fieldData.valeur)) {
            // Affichage en tags pour les listes
            value = `<div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:6px;">` + 
                    fieldData.valeur.map(v => `<span style="background:var(--paper); border:1px solid var(--line); padding:4px 8px; border-radius:4px; font-size:12px; color:var(--ink);">${v}</span>`).join('') + 
                    `</div>`;
          } else {
            let textVal = String(fieldData.valeur);
            if (textVal.length > 100) {
              // Affichage sous forme de paragraphe lisible pour les textes longs
              value = `<div style="color:var(--ink); font-weight:400; line-height:1.6; font-size:13px; background:var(--glass); padding:12px; border-radius:6px; border:1px solid var(--line); margin-top:6px; text-align:justify;">${textVal}</div>`;
            } else {
              // Affichage classique pour les textes courts
              value = `<strong style="color:var(--ink); font-weight:500; font-size:14px;">${textVal}</strong>`;
            }
          }
        }

        if (fieldData.source && fieldData.source.extrait) {
          sourceHtml = `
            <div style="margin-top:10px; padding:10px 14px; background:rgba(60,87,243,0.12); border-left:3px solid var(--blue); border-radius:0 6px 6px 0; font-size:11px; color:var(--muted); line-height:1.5;">
              <div style="font-family:var(--mono); color:var(--blue); font-weight:500; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                ${tr('common.source').toUpperCase()} • ${tr('common.page').toUpperCase()} ${fieldData.source.page}
              </div>
              <div style="font-style:italic; opacity:0.9;">"${fieldData.source.extrait}"</div>
            </div>
          `;
        }
      }

      html += `
        <div style="border-bottom:1px solid rgba(10,10,10,0.05); padding-bottom:12px; margin-bottom:12px;">
          <div style="font-family:var(--mono); font-size:10px; color:var(--muted); margin-bottom:4px; text-transform:uppercase; letter-spacing:0.5px;">${label}</div>
          <div style="font-size:14px; line-height:1.4;">${value}</div>
          ${sourceHtml}
        </div>
      `;
    });

    html += `</div></div>`;
    cardsGrid.innerHTML += html;
  });

  // T8.26 : Afficher les questions utilisées si présentes
  if (data.meta && data.meta.questions_utilisees && data.meta.questions_utilisees.length > 0) {
    let qHtml = `
      <div style="grid-column: 1 / -1; background:var(--paper-3); border:1px solid var(--line); padding:24px; margin-top: 10px;">
        <h3 style="font-family:var(--display); font-size:20px; margin-bottom:16px;">${tr('diagnostic.questions_used')}</h3>
        <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: var(--ink); line-height: 1.6;">
    `;
    data.meta.questions_utilisees.forEach(q => {
      qHtml += `<li><strong>${q.champ}</strong> : ${q.question}</li>`;
    });
    qHtml += `</ul></div>`;
    cardsGrid.innerHTML += qHtml;
  }
}

let pollInterval;

function setFormLocked(isLocked) {
  if (modelSelect) modelSelect.disabled = isLocked;
  if (approachSelect) approachSelect.disabled = isLocked;
}

function setStored(key, value) {
  try {
    if (value === undefined || value === null) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, String(value));
    }
  } catch (_) {}
}

function getStored(key) {
  try {
    return localStorage.getItem(key);
  } catch (_) {
    return null;
  }
}

function setStoredJson(key, obj) {
  try {
    if (obj === undefined || obj === null) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, JSON.stringify(obj));
    }
  } catch (_) {}
}

function getStoredJson(key) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (_) {
    return null;
  }
}

btnExtract.addEventListener('click', async () => {
  if(!fileInput.files[0]) {
    alert(tr('diagnostic.pick_file'));
    return;
  }

  if (pollInterval) {
    clearTimeout(pollInterval);
    pollInterval = undefined;
  }

  btnExtract.disabled = true;
  setFormLocked(true);
  btnExtract.textContent = tr('diagnostic.processing_btn');
  statusText.style.display = "block";
  statusText.textContent = tr('diagnostic.sending_status');
  setStored("holokia_processing", "1");
  setStored("holokia_status", statusText.textContent);
  setStored("holokia_hash", "#demo");
  resultsSection.style.display = "none";

  const fd = new FormData();
  fd.append('file', fileInput.files[0]);
  
  const selectedModel = modelSelect.value;
  let provider = 'ollama';
  let model = selectedModel;
  
  if(['groq','gpt-4o'].includes(selectedModel)){
    provider = selectedModel === 'gpt-4o' ? 'openai' : selectedModel;
    model = selectedModel === 'groq' ? 'llama-3.1-8b-instant' : '';
  } else if (selectedModel === 'qwen3:8b') {
    provider = 'ollama';
    model = 'qwen3:8b';
  }
  
  fd.append('provider', provider);
  if(model) fd.append('model', model);
  fd.append('approach', approachSelect ? approachSelect.value : 'agent');
  
  const isAsync = document.querySelector('input[name="asyncMode"]:checked').value === "true";
  fd.append('async_mode', isAsync);
  setStored("holokia_async", isAsync ? "1" : "0");

  try {
    const response = await Auth.apiFetch(`${API_URL}/extract`, {
      method: 'POST',
      body: fd
    });
    
    const data = await response.json();
    
    if (isAsync && data.job_id) {
      statusText.textContent = tr('diagnostic.job_created', { jobId: data.job_id });
      setStored("holokia_job_id", data.job_id);
      setStored("holokia_status", statusText.textContent);
      pollJobStatus(data.job_id);
    } else {
      showResults(data);
    }
  } catch(e) {
    statusText.textContent = tr('diagnostic.server_unreachable');
    btnExtract.disabled = false;
    setFormLocked(false);
    btnExtract.textContent = tr('diagnostic.extract_btn');
    setStored("holokia_processing", "0");
    setStored("holokia_job_id", null);
    setStored("holokia_status", statusText.textContent);
  }
});

async function pollJobStatus(jobId) {
  let delay = 800;
  let failures = 0;
  const tick = async () => {
    try {
      const res = await Auth.apiFetch(`${API_URL}/status/${jobId}`);
      if (!res.ok) {
        let text = "";
        try {
          text = await res.text();
        } catch (_) {}
        throw { status: res.status, text };
      }
      const data = await res.json();
      
      if (data.status === "completed") {
        pollInterval = undefined;
        showResults(data.result);
      } else if (data.status === "failed") {
        pollInterval = undefined;
        statusText.textContent = `Erreur: ${data.error}`;
        btnExtract.disabled = false;
        setFormLocked(false);
        btnExtract.textContent = tr('diagnostic.extract_btn');
        setStored("holokia_processing", "0");
        setStored("holokia_job_id", null);
        setStored("holokia_status", statusText.textContent);
      } else {
        failures = 0;
        const statusUpper = data.status.toUpperCase();
        let extra = "";
        if (data.status === "queued") extra = tr('diagnostic.queued_extra');
        else if (data.status === "processing") extra = tr('diagnostic.processing_extra');
        statusText.textContent = `Statut: ${statusUpper}${extra}`;
        setStored("holokia_status", statusText.textContent);
        delay = Math.min(2000, Math.round(delay * 1.1));
        pollInterval = window.setTimeout(tick, delay);
      }
    } catch(e) {
      failures += 1;
      const status = e && typeof e === "object" ? e.status : undefined;
      const retriable = status === 502 || status === 503 || status === 504;
      if (retriable && failures <= 12) {
        delay = Math.min(8000, Math.round(delay * 1.4) + 200);
        const seconds = Math.max(1, Math.round(delay / 1000));
        statusText.textContent = tr('diagnostic.server_busy', { status, seconds });
        setStored("holokia_status", statusText.textContent);
        pollInterval = window.setTimeout(tick, delay);
        return;
      }

      pollInterval = undefined;
      statusText.textContent = tr('diagnostic.job_status_error');
      btnExtract.disabled = false;
      setFormLocked(false);
      btnExtract.textContent = tr('diagnostic.extract_btn');
      setStored("holokia_processing", "0");
      setStored("holokia_job_id", null);
      setStored("holokia_status", statusText.textContent);
    }
  };

  if (pollInterval) {
    clearTimeout(pollInterval);
  }
  pollInterval = window.setTimeout(tick, delay);
}

function showResults(data, options) {
  const scroll = !(options && options.scroll === false);
  let statusMsg = tr('diagnostic.completed');
  if (data && data.storage) {
    if (data.storage.extraction_id) {
      statusMsg += tr('diagnostic.history_saved');
    } else if (data.storage.supabase_enabled && data.storage.error) {
      statusMsg += tr('diagnostic.history_error', { error: data.storage.error });
    } else if (data.storage.supabase_enabled) {
      statusMsg += tr('diagnostic.history_not_saved');
    }
  }
  statusText.textContent = statusMsg;
  setStored("holokia_status", statusText.textContent);
  setStored("holokia_processing", "0");
  setStored("holokia_job_id", null);
  
  // Retrait de la gestion du hash "#results"
  // setStored("holokia_hash", "#results");
  // if (location.hash !== "#results") {
  //   location.hash = "#results";
  // }
  
  // Appel de la nouvelle fonction pour générer les cartes visuelles
  buildCards(data);

  // Garder le JSON brut mais formatté pour la section développeur
  jsonOutput.textContent = JSON.stringify(data, null, 2);
  setStoredJson("holokia_last_result", data);
  
  resultsSection.style.display = "block";
  if (scroll) {
    resultsSection.scrollIntoView({behavior: 'smooth'});
  }
  btnExtract.disabled = false;
  setFormLocked(false);
  btnExtract.textContent = tr('diagnostic.extract_btn');
}

btnCopy.addEventListener('click', () => {
  navigator.clipboard.writeText(jsonOutput.textContent).then(() => {
    const oldText = btnCopy.textContent;
    btnCopy.textContent = tr('common.copied');
    setTimeout(() => btnCopy.textContent = oldText, 2000);
  });
});

if (btnExportPdf) {
  btnExportPdf.addEventListener('click', async () => {
    const current = getStoredJson("holokia_last_result");
    await exportDiagnosticPdf(current);
  });
}

(() => {
  const storedStatus = getStored("holokia_status");
  if (storedStatus) {
    statusText.style.display = "block";
    statusText.textContent = storedStatus;
  }
  const isProcessing = getStored("holokia_processing") === "1";
  const jobId = getStored("holokia_job_id");
  const lastResult = getStoredJson("holokia_last_result");

  if (isProcessing && jobId) {
    btnExtract.disabled = true;
    setFormLocked(true);
    btnExtract.textContent = tr('diagnostic.processing_btn');
    resultsSection.style.display = "none";
    pollJobStatus(jobId);
    return;
  }

  // Restaurer le dernier résultat s'il existe
  if (lastResult && !isProcessing) {
    // Afficher les résultats précédents sans faire défiler la page
    buildCards(lastResult);
    jsonOutput.textContent = JSON.stringify(lastResult, null, 2);
    resultsSection.style.display = "block";
  } else {
    // On s'assure que la section résultats est bien cachée au démarrage
    resultsSection.style.display = "none";
  }
})();

// ==========================================
// T8.22 - PANNEAU LATÉRAL "MES QUESTIONS"
// ==========================================
const btnOpenQuestions = document.getElementById('btnOpenQuestions');
const btnCloseQuestions = document.getElementById('btnCloseQuestions');
const questionsPanel = document.getElementById('questionsPanel');
const questionsOverlay = document.getElementById('questionsOverlay');
const questionsList = document.getElementById('questionsList');
const addQuestionForm = document.getElementById('addQuestionForm');
const btnResetQuestions = document.getElementById('btnResetQuestions');

function toggleQuestionsPanel(show) {
  if (show) {
    questionsOverlay.style.display = 'block';
    setTimeout(() => {
      questionsOverlay.style.opacity = '1';
      questionsPanel.style.right = '0';
    }, 10);
    loadQuestions();
  } else {
    questionsOverlay.style.opacity = '0';
    questionsPanel.style.right = '-450px';
    setTimeout(() => {
      questionsOverlay.style.display = 'none';
    }, 300);
  }
}

if (btnOpenQuestions) btnOpenQuestions.addEventListener('click', () => toggleQuestionsPanel(true));
if (btnCloseQuestions) btnCloseQuestions.addEventListener('click', () => toggleQuestionsPanel(false));
if (questionsOverlay) questionsOverlay.addEventListener('click', () => toggleQuestionsPanel(false));

async function loadQuestions() {
  questionsList.innerHTML = `<div style="text-align:center; font-family:var(--mono); font-size:12px; color:var(--muted);">${tr('diagnostic.loading_questions')}</div>`;
  try {
    const res = await Auth.apiFetch(`${API_URL}/questions`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || tr('common.error'));
    
    // Grouper par catégorie
    const grouped = {};
    data.data.forEach(q => {
      if (!grouped[q.categorie]) grouped[q.categorie] = [];
      grouped[q.categorie].push(q);
    });
    
    if (Object.keys(grouped).length === 0) {
      questionsList.innerHTML = `<div style="text-align:center; font-family:var(--mono); font-size:12px; color:var(--muted);">${tr('diagnostic.no_questions')}</div>`;
      return;
    }
    
    let html = '';
    for (const [cat, qs] of Object.entries(grouped)) {
      html += `<div style="margin-bottom:20px;">
        <div style="font-family:var(--mono); font-size:11px; color:var(--blue); margin-bottom:10px; text-transform:uppercase; border-bottom:1px solid var(--line); padding-bottom:5px;">${cat}</div>
        <div style="display:flex; flex-direction:column; gap:10px;">
      `;
      qs.forEach(q => {
        const isDef = q.is_default ? '<span style="font-size:9px; background:var(--glass); border:1px solid var(--line); padding:2px 4px; border-radius:3px;">Défaut</span>' : '<span style="font-size:9px; background:rgba(60,87,243,0.20); color:var(--blue); padding:2px 4px; border-radius:3px;">Personnalisée</span>';
        html += `
          <div style="border:1px solid var(--line); padding:10px; border-radius:4px; font-size:12px; position:relative;">
            <div style="display:flex; justify-content:space-between; margin-bottom:5px;">
              <strong style="font-family:var(--mono); font-size:11px;">${q.champ}</strong>
              ${isDef}
            </div>
            <div style="color:var(--ink); line-height:1.4;">${q.question_text}</div>
            <div style="margin-top:8px; text-align:right;">
              <button onclick="deleteQuestion('${q.id}')" style="background:none; border:none; color:var(--red); font-size:11px; cursor:pointer; font-family:var(--mono);">${tr('common.delete')}</button>
            </div>
          </div>
        `;
      });
      html += `</div></div>`;
    }
    questionsList.innerHTML = html;
  } catch (e) {
    questionsList.innerHTML = `<div style="color:var(--red); font-size:12px;">${tr('common.error')}: ${e.message}</div>`;
  }
}

if (addQuestionForm) {
  addQuestionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = addQuestionForm.querySelector('button');
    btn.textContent = tr('diagnostic.adding');
    btn.disabled = true;
    
    try {
      const payload = {
        categorie: document.getElementById('qCategory').value,
        champ: document.getElementById('qChamp').value,
        question_text: document.getElementById('qText').value,
        type: document.getElementById('qType').value
      };
      
      const res = await Auth.apiFetch(`${API_URL}/questions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error);
      
      addQuestionForm.reset();
      await loadQuestions();
    } catch (err) {
      alert(`${tr('common.error')}: ${err.message}`);
    } finally {
      btn.textContent = tr('diagnostic.add_btn');
      btn.disabled = false;
    }
  });
}

async function deleteQuestion(id) {
  if (!confirm(tr('diagnostic.confirm_delete_question'))) return;
  try {
    const res = await Auth.apiFetch(`${API_URL}/questions/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error);
    await loadQuestions();
  } catch (err) {
    alert(`${tr('common.error')}: ${err.message}`);
  }
}

if (btnResetQuestions) {
  btnResetQuestions.addEventListener('click', async () => {
    if (!confirm(tr('diagnostic.confirm_reset_questions'))) return;
    btnResetQuestions.textContent = tr('diagnostic.resetting');
    try {
      const res = await Auth.apiFetch(`${API_URL}/questions/reset`, { method: 'POST' });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error);
      await loadQuestions();
    } catch (err) {
      alert(`${tr('common.error')}: ${err.message}`);
    } finally {
      btnResetQuestions.textContent = tr('diagnostic.reset_defaults');
    }
  });
}

document.addEventListener('i18n:updated', () => {
  const lastResult = getStoredJson("holokia_last_result");
  if (lastResult) {
    buildCards(lastResult);
  }
  if (btnCopy) btnCopy.textContent = tr('common.copy');
  if (btnExportPdf) btnExportPdf.textContent = tr('common.export_pdf');
  const isProcessing = getStored("holokia_processing") === "1";
  if (!isProcessing && btnExtract) {
    btnExtract.textContent = tr('diagnostic.extract_btn');
  }
  if (questionsOverlay && questionsOverlay.style.display === 'block') {
    loadQuestions();
  }
});
