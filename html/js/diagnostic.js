const fileInput = document.getElementById('fileInput');
const modelSelect = document.getElementById('modelSelect');
const approachSelect = document.getElementById('approachSelect');
const btnExtract = document.getElementById('btnExtract');
const statusText = document.getElementById('statusText');
const resultsSection = document.getElementById('results');
const cardsGrid = document.getElementById('cardsGrid');
const jsonOutput = document.getElementById('jsonOutput');
const btnCopy = document.getElementById('btnCopy');

function buildCards(data) {
  cardsGrid.innerHTML = '';
  
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
            ${hasData ? 'DONNÉES TROUVÉES' : 'NON TROUVÉ'}
          </span>
        </h3>
        <div style="display:flex; flex-direction:column; gap:12px;">
    `;

    fields.forEach(f => {
      const fieldData = sectionData[f];
      const label = f.replace(/_/g, ' ').toUpperCase();
      let value = '<span style="color:var(--muted); font-style:italic;">Non spécifié</span>';
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
                SOURCE • PAGE ${fieldData.source.page}
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
        <h3 style="font-family:var(--display); font-size:20px; margin-bottom:16px;">Questions utilisées pour cette extraction</h3>
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
    alert("Veuillez sélectionner un fichier.");
    return;
  }

  if (pollInterval) {
    clearTimeout(pollInterval);
    pollInterval = undefined;
  }

  btnExtract.disabled = true;
  setFormLocked(true);
  btnExtract.textContent = "TRAITEMENT...";
  statusText.style.display = "block";
  statusText.textContent = "Statut: Envoi au serveur (FastAPI)...";
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
      statusText.textContent = `Statut: Job créé (ID: ${data.job_id}). Traitement en arrière-plan...`;
      setStored("holokia_job_id", data.job_id);
      setStored("holokia_status", statusText.textContent);
      pollJobStatus(data.job_id);
    } else {
      showResults(data);
    }
  } catch(e) {
    statusText.textContent = "Erreur: Serveur FastAPI injoignable ou erreur serveur.";
    btnExtract.disabled = false;
    setFormLocked(false);
    btnExtract.textContent = "LANCER L'EXTRACTION";
    setStored("holokia_processing", "0");
    setStored("holokia_job_id", null);
    setStored("holokia_status", statusText.textContent);
  }
});

async function pollJobStatus(jobId) {
  let delay = 1500;
  const tick = async () => {
    try {
      const res = await Auth.apiFetch(`${API_URL}/status/${jobId}`);
      const data = await res.json();
      
      if (data.status === "completed") {
        pollInterval = undefined;
        showResults(data.result);
      } else if (data.status === "failed") {
        pollInterval = undefined;
        statusText.textContent = `Erreur: ${data.error}`;
        btnExtract.disabled = false;
        setFormLocked(false);
        btnExtract.textContent = "LANCER L'EXTRACTION";
        setStored("holokia_processing", "0");
        setStored("holokia_job_id", null);
        setStored("holokia_status", statusText.textContent);
      } else {
        statusText.textContent = `Statut: ${data.status.toUpperCase()}...`;
        setStored("holokia_status", statusText.textContent);
        delay = Math.min(5000, Math.round(delay * 1.2));
        pollInterval = window.setTimeout(tick, delay);
      }
    } catch(e) {
      pollInterval = undefined;
      statusText.textContent = "Erreur: Impossible de récupérer le statut du job.";
      btnExtract.disabled = false;
      setFormLocked(false);
      btnExtract.textContent = "LANCER L'EXTRACTION";
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
  let statusMsg = "Statut: Terminé !";
  if (data && data.storage) {
    if (data.storage.extraction_id) {
      statusMsg += " · Enregistré dans l'historique";
    } else if (data.storage.supabase_enabled && data.storage.error) {
      statusMsg += ` · Historique: ${data.storage.error}`;
    } else if (data.storage.supabase_enabled) {
      statusMsg += " · Historique: non enregistré";
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
  btnExtract.textContent = "LANCER L'EXTRACTION";
}

btnCopy.addEventListener('click', () => {
  navigator.clipboard.writeText(jsonOutput.textContent).then(() => {
    const oldText = btnCopy.textContent;
    btnCopy.textContent = "COPIÉ !";
    setTimeout(() => btnCopy.textContent = oldText, 2000);
  });
});

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
    btnExtract.textContent = "TRAITEMENT...";
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
  questionsList.innerHTML = '<div style="text-align:center; font-family:var(--mono); font-size:12px; color:var(--muted);">Chargement...</div>';
  try {
    const res = await Auth.apiFetch(`${API_URL}/questions`);
    const data = await res.json();
    if (!data.ok) throw new Error(data.error || "Erreur inconnue");
    
    // Grouper par catégorie
    const grouped = {};
    data.data.forEach(q => {
      if (!grouped[q.categorie]) grouped[q.categorie] = [];
      grouped[q.categorie].push(q);
    });
    
    if (Object.keys(grouped).length === 0) {
      questionsList.innerHTML = '<div style="text-align:center; font-family:var(--mono); font-size:12px; color:var(--muted);">Aucune question trouvée.</div>';
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
              <button onclick="deleteQuestion('${q.id}')" style="background:none; border:none; color:var(--red); font-size:11px; cursor:pointer; font-family:var(--mono);">Supprimer</button>
            </div>
          </div>
        `;
      });
      html += `</div></div>`;
    }
    questionsList.innerHTML = html;
  } catch (e) {
    questionsList.innerHTML = `<div style="color:var(--red); font-size:12px;">Erreur: ${e.message}</div>`;
  }
}

if (addQuestionForm) {
  addQuestionForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = addQuestionForm.querySelector('button');
    btn.textContent = 'AJOUT...';
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
      alert("Erreur: " + err.message);
    } finally {
      btn.textContent = 'AJOUTER';
      btn.disabled = false;
    }
  });
}

async function deleteQuestion(id) {
  if (!confirm("Voulez-vous vraiment supprimer cette question ?")) return;
  try {
    const res = await Auth.apiFetch(`${API_URL}/questions/${id}`, { method: 'DELETE' });
    const data = await res.json();
    if (!data.ok) throw new Error(data.error);
    await loadQuestions();
  } catch (err) {
    alert("Erreur: " + err.message);
  }
}

if (btnResetQuestions) {
  btnResetQuestions.addEventListener('click', async () => {
    if (!confirm("Attention, cela supprimera toutes vos questions personnalisées pour revenir à celles par défaut. Continuer ?")) return;
    btnResetQuestions.textContent = 'RÉINITIALISATION...';
    try {
      const res = await Auth.apiFetch(`${API_URL}/questions/reset`, { method: 'POST' });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error);
      await loadQuestions();
    } catch (err) {
      alert("Erreur: " + err.message);
    } finally {
      btnResetQuestions.textContent = 'RÉINITIALISER AUX DÉFAUTS';
    }
  });
}
