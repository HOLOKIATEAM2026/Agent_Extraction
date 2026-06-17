/* ══════════════════════════════════════════
   HOLOKIA — Multi-Docs Logic
   ══════════════════════════════════════════ */

// ── STATE ──
let multiId        = null;
let multiFiles     = [];
let multiQuestions = [];
let lastResults    = null;

// ── DOM REFS ──
const multiFileInput    = document.getElementById('multiFileInput');
const multiDropZone     = document.getElementById('multiDropZone');
const multiFileList     = document.getElementById('multiFileList');
const multiQuestionList = document.getElementById('multiQuestionList');
const headerDocs        = document.getElementById('headerDocs');
const headerQuestions   = document.getElementById('headerQuestions');
const tbDocsCount       = document.getElementById('tbDocsCount');
const tbQuestionsCount  = document.getElementById('tbQuestionsCount');
const multiStatus       = document.getElementById('multiStatus');
const modelSelect       = document.getElementById('modelSelect');

const btnHistoryToggle  = document.getElementById('btnHistoryToggle');
const btnCloseHistory   = document.getElementById('btnCloseHistory');
const historyDrawer     = document.getElementById('historyDrawer');
const historyOverlay    = document.getElementById('historyOverlay');

const btnDocsToggle     = document.getElementById('btnDocsToggle');
const docsPanel         = document.getElementById('docsPanel');

const btnQuestionsToggle= document.getElementById('btnQuestionsToggle');
const questionsPanel    = document.getElementById('questionsPanel');

const btnMultiExtract   = document.getElementById('btnMultiExtract');
const btnNewMulti       = document.getElementById('btnNewMulti');

// ── TOGGLES ──
if (btnHistoryToggle) {
  btnHistoryToggle.addEventListener('click', () => {
    if (historyDrawer) historyDrawer.classList.add('open');
    if (historyOverlay) historyOverlay.classList.add('open');
  });
}

if (btnCloseHistory) btnCloseHistory.addEventListener('click', closeHistory);
if (historyOverlay) historyOverlay.addEventListener('click', closeHistory);

function closeHistory() {
  if (historyDrawer) historyDrawer.classList.remove('open');
  if (historyOverlay) historyOverlay.classList.remove('open');
}

if (btnDocsToggle) {
  btnDocsToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    docsPanel.classList.toggle('visible');
    btnDocsToggle.classList.toggle('active');
    questionsPanel.classList.remove('visible');
    btnQuestionsToggle.classList.remove('active');
  });
}

if (btnQuestionsToggle) {
  btnQuestionsToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    questionsPanel.classList.toggle('visible');
    btnQuestionsToggle.classList.toggle('active');
    docsPanel.classList.remove('visible');
    btnDocsToggle.classList.remove('active');
  });
}

document.addEventListener('click', (e) => {
  if (docsPanel && !docsPanel.contains(e.target) && btnDocsToggle && !btnDocsToggle.contains(e.target)) {
    docsPanel.classList.remove('visible');
    btnDocsToggle.classList.remove('active');
  }
  if (questionsPanel && !questionsPanel.contains(e.target) && btnQuestionsToggle && !btnQuestionsToggle.contains(e.target)) {
    questionsPanel.classList.remove('visible');
    btnQuestionsToggle.classList.remove('active');
  }
});

// ── UTILS ──
function esc(s) {
  return String(s)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function getExt(filename) {
  return filename.split('.').pop().toUpperCase().slice(0, 4);
}

function updateHeader() {
  const dCount = multiFiles.length;
  const qCount = multiQuestions.length;
  
  if (headerDocs) headerDocs.innerHTML = `<span class="dot dot-teal"></span> ${dCount} doc${dCount > 1 ? 's' : ''}`;
  if (headerQuestions) headerQuestions.innerHTML = `<span class="dot dot-amber"></span> ${qCount} question${qCount > 1 ? 's' : ''}`;
  
  if (tbDocsCount) tbDocsCount.innerText = `${dCount} doc${dCount > 1 ? 's' : ''}`;
  if (tbQuestionsCount) tbQuestionsCount.innerText = `${qCount} question${qCount > 1 ? 's' : ''}`;
  
  if (btnMultiExtract) {
    if (dCount > 0 && qCount > 0) {
      btnMultiExtract.style.opacity = '1';
      btnMultiExtract.style.pointerEvents = 'auto';
    } else {
      btnMultiExtract.style.opacity = '0.5';
      btnMultiExtract.style.pointerEvents = 'none';
    }
  }
}

// ── LOCAL STORAGE PERSISTENCE ──
function saveMultiState() {
  const state = {
    id: multiId,
    files: multiFiles.map(f => ({ name: f.name, isVirtual: true })),
    questions: multiQuestions,
    model: modelSelect ? modelSelect.value : 'groq',
    results: lastResults
  };
  localStorage.setItem('holokia_multi_state', JSON.stringify(state));
  saveMultiToHistory();
}

function clearMultiState() {
  localStorage.removeItem('holokia_multi_state');
  multiId = null;
  multiFiles = [];
  multiQuestions = [];
  lastResults = null;
  const list = document.getElementById('multiFileList');
  if (list) list.innerHTML = '';
  const qList = document.getElementById('multiQuestionList');
  if (qList) qList.innerHTML = '';
  updateHeader();
  renderMultiHistory();
  const container = document.getElementById('multiResultsContainer');
  if (container) {
    container.innerHTML = `
      <div class="results-empty">
        <div class="empty-icon-box">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18"/>
            <line x1="3" y1="9" x2="21" y2="9"/>
            <line x1="9" y1="21" x2="9" y2="9"/>
          </svg>
        </div>
        <div class="results-empty-text">Aucun résultat</div>
        <div class="results-empty-sub">
          Ajoutez vos documents et vos questions via le menu en haut, puis lancez l'analyse pour voir les résultats s'afficher ici.
        </div>
      </div>
    `;
  }
}

function initMulti() {
  try {
    const saved = localStorage.getItem('holokia_multi_state');
    if (saved) {
      const state = JSON.parse(saved);
      if (state.id) multiId = state.id;
      if (state.model && modelSelect) modelSelect.value = state.model;
      if (state.files && state.files.length > 0) handleMultiFiles(state.files, true);
      if (state.questions && state.questions.length > 0) state.questions.forEach(q => addQuestion(q, true));
      if (state.results) {
        lastResults = state.results;
        renderResults(state.results);
      }
      saveMultiState();
    }
  } catch (e) {
    console.error("Erreur au chargement de l'état multi:", e);
  }
  renderMultiHistory();
}

// ── HISTORY FUNCTIONS ──
let cachedMultiHistory = [];

async function loadMultiHistory() {
  try {
    const res = await fetch(`${API_URL}/history/multi`);
    const data = await res.json();
    if (data.ok && data.data) {
      cachedMultiHistory = data.data.map(h => {
        if (h.created_at) h.date = h.created_at;
        return h;
      });
      return cachedMultiHistory;
    }
  } catch (e) {
    console.error("Erreur chargement historique multi:", e);
  }
  return JSON.parse(localStorage.getItem('holokia_multi_history') || '[]');
}

async function saveMultiToHistory() {
  if (multiFiles.length === 0 && multiQuestions.length === 0 && !lastResults) return;
  
  if (!multiId) {
    multiId = Date.now().toString();
  }
  
  const title = multiFiles.length > 0 
    ? multiFiles.map(f => f.name.split('.')[0]).join(', ') 
    : 'Nouvelle comparaison';
  
  const existingIdx = cachedMultiHistory.findIndex(h => h.id === multiId);
  const creationDate = existingIdx >= 0 && cachedMultiHistory[existingIdx].date 
    ? cachedMultiHistory[existingIdx].date 
    : new Date().toISOString();
  
  const sessionData = {
    id: multiId,
    title: title.length > 30 ? title.substring(0, 27) + '...' : title,
    date: creationDate,
    files: multiFiles.map(f => ({ name: f.name, isVirtual: true })),
    questions: multiQuestions,
    model: modelSelect ? modelSelect.value : 'groq',
    results: lastResults
  };
  
  try {
    await fetch(`${API_URL}/history/multi`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sessionData)
    });
  } catch (e) {
    console.error("Erreur sauvegarde historique multi:", e);
    let hist = JSON.parse(localStorage.getItem('holokia_multi_history') || '[]');
    const eIdx = hist.findIndex(h => h.id === multiId);
    if (eIdx >= 0) hist[eIdx] = sessionData;
    else hist.unshift(sessionData);
    localStorage.setItem('holokia_multi_history', JSON.stringify(hist));
  }
  
  renderMultiHistory();
}

async function renderMultiHistory() {
  const histList = document.getElementById('multiHistoryList');
  if (!histList) return;
  
  const hist = await loadMultiHistory();
  histList.innerHTML = '';
  
  if (hist.length === 0) {
    histList.innerHTML = '<div style="font-family:var(--mono);font-size:9px;color:var(--muted);padding:8px;text-align:center;">Aucun historique</div>';
    return;
  }
  
  hist.forEach(h => {
    const item = document.createElement('div');
    item.className = `history-item ${h.id === multiId ? 'active' : ''}`;
    
    const dateObj = new Date(h.date || h.created_at);
    const dateStr = dateObj.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
    
    item.innerHTML = `
      <div class="history-title" title="${esc(h.title)}">${esc(h.title)}</div>
      <div class="history-date">${dateStr}</div>
      <button class="history-delete" title="Supprimer">✕</button>
    `;
    
    item.addEventListener('click', (e) => {
      if (!e.target.classList.contains('history-delete')) {
        loadMultiSession(h.id);
      }
    });
    
    const deleteBtn = item.querySelector('.history-delete');
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteMultiSession(h.id);
    });
    
    histList.appendChild(item);
  });
}

async function deleteMultiSession(id) {
  if (!confirm("Voulez-vous vraiment supprimer cet historique ?")) return;
  
  try {
    await fetch(`${API_URL}/history/multi/${id}`, { method: 'DELETE' });
  } catch (e) {
    console.error("Erreur suppression historique multi:", e);
    let hist = JSON.parse(localStorage.getItem('holokia_multi_history') || '[]');
    hist = hist.filter(h => h.id !== id);
    localStorage.setItem('holokia_multi_history', JSON.stringify(hist));
  }
  
  if (id === multiId) {
    if (btnNewMulti) btnNewMulti.click();
  } else {
    renderMultiHistory();
  }
}

async function loadMultiSession(id) {
  const hist = await loadMultiHistory();
  const session = hist.find(h => h.id === id);
  if (!session) return;
  
  multiId = session.id;
  
  multiFiles = [];
  multiQuestions = [];
  lastResults = null;
  if (multiFileList) multiFileList.innerHTML = '';
  if (multiQuestionList) multiQuestionList.innerHTML = '';
  
  if (session.model && modelSelect) modelSelect.value = session.model;
  if (session.files && session.files.length > 0) handleMultiFiles(session.files, true);
  if (session.questions && session.questions.length > 0) session.questions.forEach(q => addQuestion(q, true));
  
  if (session.results) {
    lastResults = session.results;
    renderResults(session.results);
  } else {
    restoreEmptyState();
  }
  
  updateHeader();
  saveMultiState();
  renderMultiHistory();
}

function restoreEmptyState() {
  const container = document.getElementById('multiResultsContainer');
  if (container) {
    container.innerHTML = `
      <div class="results-empty">
        <div class="empty-icon-box">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--muted)" stroke-width="1.5">
            <rect x="3" y="3" width="18" height="18"/>
            <line x1="3" y1="9" x2="21" y2="9"/>
            <line x1="9" y1="21" x2="9" y2="9"/>
          </svg>
        </div>
        <div class="results-empty-text">Aucun résultat</div>
        <div class="results-empty-sub">
          Ajoutez vos documents et vos questions via le menu en haut, puis lancez l'analyse pour voir les résultats s'afficher ici.
        </div>
      </div>
    `;
  }
}

if (btnNewMulti) {
  btnNewMulti.addEventListener('click', () => {
    multiId = null;
    multiFiles = [];
    multiQuestions = [];
    lastResults = null;
    if (multiFileList) multiFileList.innerHTML = '';
    if (multiQuestionList) multiQuestionList.innerHTML = '';
    restoreEmptyState();
    updateHeader();
    saveMultiState();
    renderMultiHistory();
  });
}

// ── FILES ──
function handleMultiFiles(files, isVirtual = false) {
  Array.from(files).forEach(f => {
    const ext = f.name.split('.').pop().toLowerCase();
    if (!['pdf','docx','txt','md'].includes(ext)) return;
    if (multiFiles.find(x => x.name === f.name)) return;
    
    const fileObj = isVirtual ? { name: f.name, isVirtual: true } : f;
    multiFiles.push(fileObj);

    if (multiFileList) {
      const li = document.createElement('li');
      li.className = 'file-item';
      li.innerHTML = `
        <span class="file-ext">${getExt(f.name)}</span>
        <span class="file-name" title="${esc(f.name)}">${esc(f.name)}</span>
        <button class="file-remove" title="Supprimer" data-name="${esc(f.name)}">✕</button>
      `;
      multiFileList.appendChild(li);
      
      li.querySelector('.file-remove').onclick = () => {
        multiFiles = multiFiles.filter(x => x.name !== f.name);
        li.remove();
        updateHeader();
        saveMultiState();
      };
    }
  });

  updateHeader();
  saveMultiState();
}

if (multiDropZone) {
  multiDropZone.addEventListener('click', () => multiFileInput.click());
  multiDropZone.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') multiFileInput.click(); });
  multiDropZone.addEventListener('dragover',  e => { e.preventDefault(); multiDropZone.classList.add('dragover'); });
  multiDropZone.addEventListener('dragleave', ()  => multiDropZone.classList.remove('dragover'));
  multiDropZone.addEventListener('drop', e => {
    e.preventDefault();
    multiDropZone.classList.remove('dragover');
    handleMultiFiles(e.dataTransfer.files);
  });
}

if (multiFileInput) {
  multiFileInput.addEventListener('change', e => { handleMultiFiles(e.target.files); multiFileInput.value = ''; });
}

// ── QUESTIONS ──
function addQuestion(q, skipSave = false) {
  q = q.trim();
  if (!q || multiQuestions.includes(q)) return;
  multiQuestions.push(q);

  if (multiQuestionList) {
    const num = multiQuestions.length;
    const li = document.createElement('li');
    li.className = 'question-item';
    li.dataset.q = q;
    li.innerHTML = `
      <span class="q-num">${String(num).padStart(2,'0')}</span>
      <span class="q-text">${esc(q)}</span>
      <button class="btn-remove" title="Supprimer">×</button>
    `;
    li.querySelector('.btn-remove').onclick = () => {
      multiQuestions = multiQuestions.filter(x => x !== q);
      li.remove();
      multiQuestionList.querySelectorAll('.question-item').forEach((item, i) => {
        item.querySelector('.q-num').textContent = String(i + 1).padStart(2, '0');
      });
      updateHeader();
      saveMultiState();
    };
    multiQuestionList.appendChild(li);
  }
  updateHeader();
  if (!skipSave) saveMultiState();
}

const btnAddPredef = document.getElementById('btnAddPredef');
if (btnAddPredef) {
  btnAddPredef.addEventListener('click', () => {
    const sel = document.getElementById('multiPredefSelect');
    if (sel) {
      addQuestion(sel.value);
      sel.value = '';
    }
  });
}

const btnAddCustom = document.getElementById('btnAddCustom');
if (btnAddCustom) {
  btnAddCustom.addEventListener('click', () => {
    const inp = document.getElementById('multiCustomQuestion');
    if (inp) {
      addQuestion(inp.value);
      inp.value = '';
    }
  });
}

const multiCustomQuestion = document.getElementById('multiCustomQuestion');
if (multiCustomQuestion) {
  multiCustomQuestion.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      addQuestion(e.target.value);
      e.target.value = '';
    }
  });
}

if (modelSelect) {
  modelSelect.addEventListener('change', saveMultiState);
}

// ── LAUNCH ──
if (btnMultiExtract) {
  btnMultiExtract.addEventListener('click', async () => {
    if (multiFiles.length === 0)     { alert('Veuillez ajouter au moins un document.'); return; }
    if (multiQuestions.length === 0) { alert('Veuillez ajouter au moins une question.'); return; }

    const container = document.getElementById('multiResultsContainer');
    const model     = modelSelect ? modelSelect.value : 'groq';

    if (multiStatus) multiStatus.classList.add('visible');
    btnMultiExtract.disabled = true;
    
    if (container) {
      container.innerHTML = `
        <div class="loading-state">
          <div class="loading-spinner-lg"></div>
          <div class="loading-text">Analyse de ${multiFiles.length} document(s) en cours…</div>
        </div>
      `;
    }

    const formData = new FormData();
    const realFiles = multiFiles.filter(f => !f.isVirtual);
    realFiles.forEach(f => formData.append('files', f));
    
    if (realFiles.length === 0 && multiFiles.length > 0) {
      const fileNames = multiFiles.map(f => f.name);
      formData.append('cached_files', JSON.stringify(fileNames));
    }
    
    formData.append('questions', JSON.stringify(multiQuestions));
    
    const provider = 'groq';
    const modelName = 'llama-3.1-8b-instant';
    formData.append('provider', provider);
    formData.append('model', modelName);

    try {
      const response = await fetch(`${API_URL}/extract-multi`, {
        method: 'POST',
        body: formData
      });
      let data = null;
      try {
        data = await response.json();
      } catch (e) {
        data = null;
      }

      if (!response.ok) {
        const msg = (data && (data.error || data.detail)) ? (data.error || data.detail) : `HTTP ${response.status}`;
        if (typeof msg === 'string' && msg.toLowerCase().includes('cache expir')) {
          clearMultiState();
          alert(msg);
          return;
        }
        if (container) container.innerHTML = `<div class="error-block">Erreur serveur (${response.status}) : ${esc(msg)}</div>`;
        return;
      }

      if (data && data.ok) {
        renderResults(data.results);
        return;
      }

      const msg = data && (data.error || data.detail) ? (data.error || data.detail) : 'Inconnue';
      if (container) container.innerHTML = `<div class="error-block">Erreur serveur : ${esc(msg)}</div>`;

    } catch (err) {
      if (container) container.innerHTML = `<div class="error-block">Erreur réseau : ${esc(err && err.message ? err.message : 'Inconnue')}</div>`;
    } finally {
      if (multiStatus) multiStatus.classList.remove('visible');
      btnMultiExtract.disabled = false;
    }
  });
}

// ── RENDER RESULTS ──
function renderResults(results) {
  lastResults = results;
  saveMultiState();

  const container = document.getElementById('multiResultsContainer');
  if (!container) return;
  container.innerHTML = '';

  if (results.synthese_comparative) {
    const block = document.createElement('div');
    block.className = 'synthese-block';
    block.innerHTML = `
      <div class="synthese-label">Synthèse Comparative</div>
      <div class="synthese-body">${esc(results.synthese_comparative)}</div>
    `;
    container.appendChild(block);
  }

  const label = document.createElement('div');
  label.className = 'results-label';
  label.textContent = `Résultats par document (${Object.keys(results.results_by_document || {}).length})`;
  container.appendChild(label);

  const grid = document.createElement('div');
  grid.className = 'results-grid';
  container.appendChild(grid);

  const docs = results.results_by_document || {};
  for (const [fname, qRes] of Object.entries(docs)) {
    const qCount = Object.keys(qRes).length;
    const card = document.createElement('div');
    card.className = 'doc-card';
    card.innerHTML = `
      <div class="doc-card-header">
        <div class="doc-card-icon">📄</div>
        <span class="doc-card-name" title="${esc(fname)}">${esc(fname)}</span>
        <span class="doc-card-count">${qCount} réponse${qCount !== 1 ? 's' : ''}</span>
      </div>
    `;

    for (const [q, ans] of Object.entries(qRes)) {
      const val    = ans.valeur || null;
      const page   = ans.source?.page != null ? `<span class="page-badge">p. ${ans.source.page}</span>` : '';
      const conf   = ans.confiance != null ? getConfBadge(ans.confiance) : '';
      
      const answerContent = document.createElement('div');
      answerContent.className = 'qa-answer';
      answerContent.style.flexDirection = 'row';
      answerContent.innerHTML = val ? `${esc(val)} ${page} ${conf}` : '<span class="qa-empty">Non trouvé dans ce document</span>';

      const row    = document.createElement('div');
      row.className = 'qa-row';
      row.innerHTML = `<div class="qa-question">${esc(q)}</div>`;
      row.appendChild(answerContent);
      
      card.appendChild(row);
    }

    grid.appendChild(card);
  }
}

function getConfBadge(conf) {
  const cls = conf >= 0.8 ? 'high' : conf >= 0.5 ? 'medium' : 'low';
  return `<span class="conf-badge conf-${cls}">${Math.round(conf * 100)}%</span>`;
}

function renderDemoResults() {
  const demoData = {
    synthese_comparative: `Analyse comparative de ${multiFiles.length} document(s) sur ${multiQuestions.length} question(s).\n\nServeur non disponible — résultats de démonstration. Lancez votre backend FastAPI sur localhost:8000 pour les vraies extractions.`,
    results_by_document: {}
  };
  multiFiles.forEach(f => {
    demoData.results_by_document[f.name] = {};
    multiQuestions.forEach(q => {
      demoData.results_by_document[f.name][q] = {
        valeur: 'Donnée non disponible (mode démo)',
        source: { page: null },
        confiance: null
      };
    });
  });
  renderResults(demoData);
}

// Initialisation
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initMulti);
} else {
  initMulti();
}
