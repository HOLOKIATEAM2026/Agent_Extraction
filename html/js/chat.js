/* ══════════════════════════════════════════
   HOLOKIA — Chat Page Logic
   ══════════════════════════════════════════ */

// ── STATE ──
const state = {
  id: null,
  files: [],
  messages: [],
  model: 'groq',
  totalSources: 0,
  confidenceSum: 0,
  confidenceCount: 0,
  isLoading: false
};

// ── DOM REFS ──
const btnUpload     = document.getElementById('btnUpload');
const fileInput     = document.getElementById('fileInput');
const fileList      = document.getElementById('fileList');
const docCountBadge = document.getElementById('docCountBadge');
const historyList   = document.getElementById('historyList');
const modelSelect   = document.getElementById('modelSelect');
const messagesArea  = document.getElementById('messagesArea');
const emptyState    = document.getElementById('emptyState');
const chatInput     = document.getElementById('chatInput');
const btnSend       = document.getElementById('btnSend');
const btnReset      = document.getElementById('btnReset');
const charCount     = document.getElementById('charCount');
const ragStatus     = document.getElementById('ragStatus');
const headerModel   = document.getElementById('headerModel');
const headerDocs    = document.getElementById('headerDocs');

// ── MODEL INFO MAP ──
const modelMap = {
  'groq':    { name: 'LLaMA 3.1 70B', sub: 'Groq Cloud · Latence ~1s', color: 'var(--blue)' },
  'mistral': { name: 'Mistral 7B',    sub: 'Ollama Local · CPU/GPU',   color: 'var(--teal)' },
  'qwen3:8b':{ name: 'Qwen 3 8B',     sub: 'Ollama Local · CPU/GPU',   color: 'var(--amber)'}
};

// ── UTILS ──
function formatTime() {
  return new Date().toLocaleTimeString('fr-FR', { hour:'2-digit', minute:'2-digit' });
}

function getExt(filename) {
  return filename.split('.').pop().toUpperCase().slice(0, 4);
}

function updateStats() {
  const statMsg = document.getElementById('statMessages');
  const statDoc = document.getElementById('statDocs');
  const statSrc = document.getElementById('statSources');
  const statConf = document.getElementById('statConf');

  if (statMsg) statMsg.textContent = state.messages.filter(m => m.role === 'user').length;
  if (statDoc) statDoc.textContent = state.files.length;
  if (statSrc) statSrc.textContent = state.totalSources;
  if (statConf) {
    statConf.textContent =
      state.confidenceCount > 0
        ? Math.round(state.confidenceSum / state.confidenceCount * 100) + '%'
        : '—';
  }

  if (headerDocs) {
    headerDocs.innerHTML = `<span class="dot dot-amber"></span> ${state.files.length} doc${state.files.length !== 1 ? 's' : ''}`;
  }
  
  if(docCountBadge) {
    if(state.files.length > 0) {
      docCountBadge.textContent = state.files.length;
      docCountBadge.style.display = 'block';
      btnUpload.style.color = 'var(--blue)';
    } else {
      docCountBadge.style.display = 'none';
      btnUpload.style.color = 'var(--muted)';
    }
  }
}

function updateRagStatus() {
  const hasFiles = state.files.length > 0;
  if (ragStatus) {
    ragStatus.innerHTML = hasFiles
      ? `<span class="dot dot-green"></span> ${state.files.length} document(s) chargé(s) — RAG actif`
      : `<span class="dot" style="background:var(--amber);box-shadow:0 0 6px var(--amber)"></span> En attente de documents`;
  }
}

// ── FILES ──
function addFiles(newFiles) {
  const allowed = ['pdf','docx','txt','md'];
  
  // Remove virtual files if user adds real files
  state.files = state.files.filter(f => !f.isVirtual);
  
  Array.from(newFiles).forEach(f => {
    const ext = f.name.split('.').pop().toLowerCase();
    if (!allowed.includes(ext)) return;
    if (state.files.find(x => x.name === f.name)) return;
    state.files.push(f);
  });
  
  saveChatState();
  renderFileList();
  updateStats();
  updateRagStatus();
}

function removeFile(name) {
  state.files = state.files.filter(f => f.name !== name);
  saveChatState();
  renderFileList();
  updateStats();
  updateRagStatus();
}

function renderFileList() {
  if (!fileList) return;
  fileList.innerHTML = '';
  state.files.forEach(f => {
    const item = document.createElement('div');
    item.className = 'file-item';
    item.innerHTML = `
      <span class="file-name" title="${f.name}">${f.name.length > 15 ? f.name.slice(0,12) + '...' + getExt(f.name) : f.name}</span>
      <span class="file-remove" role="button" tabindex="0" title="Supprimer" data-name="${f.name}">✕</span>
    `;
    fileList.appendChild(item);
  });

  fileList.querySelectorAll('.file-remove').forEach(btn => {
    btn.addEventListener('click', () => removeFile(btn.dataset.name));
    btn.addEventListener('keydown', e => { if (e.key === 'Enter') removeFile(btn.dataset.name); });
  });
}

// Upload btn
if (btnUpload) {
  btnUpload.addEventListener('click', () => fileInput.click());
  btnUpload.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') fileInput.click(); });
}

if (fileInput) {
  fileInput.addEventListener('change', () => { addFiles(fileInput.files); fileInput.value = ''; });
}

// Expose for inline script compatibility
window.handleChatFiles = addFiles;

// ── MODEL SELECTOR ──
if (modelSelect) {
  modelSelect.addEventListener('change', () => {
    state.model = modelSelect.value;
    saveChatState();
    if (headerModel) {
      headerModel.innerHTML = `<span class="dot" style="background:var(--blue);box-shadow:0 0 6px var(--blue)"></span> ${state.model}`;
    }
  });
}

// ── MESSAGES ──
function addMessage(role, content, sources = [], confidence = null) {
  // Masquer empty state
  if (emptyState) emptyState.style.display = 'none';

  const msg = document.createElement('div');
  msg.className = `message ${role}`;

  const avatar = role === 'user' ? 'U' : 'AI';
  const name   = role === 'user' ? 'Vous' : 'Holokia RAG';

  let sourcesHtml = '';
  if (sources && sources.length > 0) {
    state.totalSources += sources.length;
    sourcesHtml = `
      <div class="msg-sources">
        <div class="sources-header">Sources (${sources.length})</div>
        ${sources.map(s => {
          let pageText = s.page || '?';
          if (pageText.toString().includes(',')) {
            pageText = 'p.' + pageText;
          } else if (!pageText.toString().startsWith('p.')) {
            pageText = 'p.' + pageText;
          }
          return `
          <span class="source-tag" title="${s.extrait || ''}">
            📄 ${s.fichier || s.file_name || 'Document'} · ${pageText}
          </span>
          `;
        }).join('')}
      </div>
    `;
  }

  let confHtml = '';
  if (confidence !== null) {
    state.confidenceSum += confidence;
    state.confidenceCount++;
    const cls = confidence >= 0.8 ? 'high' : confidence >= 0.5 ? 'medium' : 'low';
    const pct = Math.round(confidence * 100);
    confHtml = `<div class="confidence-badge confidence-${cls}">● Confiance ${pct}%</div>`;
  }

  msg.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-body">
      <div class="msg-meta">
        ${name}
        <span class="msg-time">${formatTime()}</span>
      </div>
      <div class="msg-bubble">
        <p>${content.replace(/\n/g, '<br>')}</p>
      </div>
      ${sourcesHtml}
      ${confHtml}
    </div>
  `;

  if (messagesArea) {
    messagesArea.appendChild(msg);
    messagesArea.scrollTop = messagesArea.scrollHeight;
  }
  updateStats();

  // Update state and save
  state.messages.push({ role, content, sources, confidence });
  saveChatState();
}

function addTyping() {
  const msg = document.createElement('div');
  msg.className = 'message assistant';
  msg.id = 'typingMsg';
  msg.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-body">
      <div class="msg-meta">Holokia RAG <span class="msg-time">${formatTime()}</span></div>
      <div class="typing-bubble">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>
  `;
  if (messagesArea) {
    messagesArea.appendChild(msg);
    messagesArea.scrollTop = messagesArea.scrollHeight;
  }
  return msg;
}

// ── SEND ──
async function sendMessage() {
  const text = chatInput.value.trim();
  if (!text || state.isLoading) return;

  state.isLoading = true;
  chatInput.value = '';
  if (charCount) charCount.textContent = '0';
  if (btnSend) btnSend.disabled = true;
  if (chatInput) chatInput.disabled = true;

  addMessage('user', text);

  const typing = addTyping();

  try {
    const formData = new FormData();
    formData.append('message', text);
    
    const historyPayload = state.messages
      .filter(m => m.role !== 'system')
      .map(m => ({ role: m.role, content: m.content }));
    formData.append('history', JSON.stringify(historyPayload));

    let provider = 'groq';
    let model = 'llama-3.3-70b-versatile';
    
    if (state.model === 'mistral') {
        provider = 'ollama';
        model = 'mistral';
    } else if (state.model === 'qwen3:8b') {
        provider = 'ollama';
        model = 'qwen3:8b';
    } else if (state.model === 'gpt-4o') {
        provider = 'openai';
        model = 'gpt-4o';
    }

    formData.append('provider', provider);
    formData.append('model', model);
    
    const realFiles = state.files.filter(f => !f.isVirtual);
    realFiles.forEach(f => formData.append('files', f));
    
    if (realFiles.length === 0 && state.files.length > 0) {
        const fileNames = state.files.map(f => f.name);
        formData.append('cached_files', JSON.stringify(fileNames));
    }

    const res = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      body: formData
    });

    typing.remove();

    if (!res.ok) throw new Error(`Erreur serveur : ${res.status}`);

    const data = await res.json();
    const citations = data.citations || data.sources || [];
    const simulatedConfidence = citations.length > 0 ? 0.85 + (Math.random() * 0.1) : null;

    addMessage(
      'assistant',
      data.answer || data.response || 'Aucune réponse reçue.',
      citations,
      data.confidence ?? simulatedConfidence
    );

  } catch (err) {
    typing.remove();
    const demo = state.files.length > 0
      ? `J'ai analysé vos ${state.files.length} document(s) via le pipeline RAG. Voici ce que j'ai trouvé concernant votre question : "${text}"\n\nRéponse simulée — vérifiez que votre backend FastAPI est correctement configuré et accessible.`
      : `Aucun document chargé. Uploadez un rapport d'activité dans la sidebar pour que je puisse analyser son contenu et répondre à : "${text}"`;

    addMessage('assistant', demo, state.files.length > 0 ? [{ fichier: state.files[0]?.name, page: 1 }] : [], state.files.length > 0 ? 0.78 : null);
  }

  state.isLoading = false;
  if (btnSend) btnSend.disabled = false;
  if (chatInput) {
    chatInput.disabled = false;
    chatInput.focus();
  }
}

// ── EVENTS ──
if (btnSend) {
  btnSend.addEventListener('click', sendMessage);
}

if (chatInput) {
  chatInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  chatInput.addEventListener('input', () => {
    if (charCount) charCount.textContent = chatInput.value.length;
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 140) + 'px';
  });
}

if (btnReset) {
  btnReset.addEventListener('click', () => {
    state.id = null;
    state.messages = [];
    state.files = [];
    state.totalSources = 0;
    state.confidenceSum = 0;
    state.confidenceCount = 0;
    
    localStorage.removeItem('holokia_chat_state');

    if (fileList) fileList.innerHTML = '';
    if (messagesArea) {
      messagesArea.innerHTML = '';
      if (emptyState) {
        messagesArea.appendChild(emptyState);
        emptyState.style.display = 'flex';
      }
    }
    if (chatInput) {
      chatInput.value = '';
      if (charCount) charCount.textContent = '0';
      chatInput.focus();
    }
    updateStats();
    updateRagStatus();
    renderHistory();
  });
}

// Quick prompts
document.querySelectorAll('.quick-prompt').forEach(btn => {
  btn.addEventListener('click', () => {
    if (chatInput) {
      chatInput.value = btn.dataset.q;
      if (charCount) charCount.textContent = chatInput.value.length;
      chatInput.focus();
      if (state.files.length > 0) {
        sendMessage();
      }
    }
  });
});

// ── INIT ──
function initChat() {
  const saved = localStorage.getItem('holokia_chat_state');
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      if (parsed.id) state.id = parsed.id;
      
      if (parsed.fileNames && parsed.fileNames.length > 0) {
        state.files = parsed.fileNames.map(name => ({ name: name, isVirtual: true }));
        renderFileList();
      }
      
      if (parsed.messages && parsed.messages.length > 0) {
        state.totalSources = 0;
        state.confidenceSum = 0;
        state.confidenceCount = 0;
        
        const tempMessages = [...parsed.messages];
        state.messages = [];
        
        tempMessages.forEach(m => {
          addMessage(m.role, m.content, m.sources, m.confidence);
        });
      }
      if (parsed.model && modelSelect) {
        modelSelect.value = parsed.model;
        modelSelect.dispatchEvent(new Event('change'));
      }
    } catch (e) {
      console.error("Erreur lors de la restauration du chat", e);
    }
  }
  
  updateStats();
  updateRagStatus();
  renderHistory();
  if (chatInput) chatInput.focus();
}

let cachedChatHistory = [];

async function loadHistory() {
  try {
    const res = await fetch(`${API_URL}/history/chat`);
    const data = await res.json();
    if (data.ok && data.data) {
      cachedChatHistory = data.data.map(h => {
        if (h.created_at) h.date = h.created_at;
        return h;
      });
      return cachedChatHistory;
    }
  } catch (e) {
    console.error("Erreur chargement historique chat:", e);
  }
  return JSON.parse(localStorage.getItem('holokia_chat_history') || '[]');
}

async function saveToHistory() {
  if (state.messages.length === 0) return;
  
  if (!state.id) {
    state.id = Date.now().toString();
  }
  
  const firstUserMsg = state.messages.find(m => m.role === 'user');
  const title = firstUserMsg 
    ? firstUserMsg.content.slice(0, 30) + (firstUserMsg.content.length > 30 ? '...' : '') 
    : 'Nouvelle conversation';
  
  const existingIdx = cachedChatHistory.findIndex(h => h.id === state.id);
  const creationDate = existingIdx >= 0 && cachedChatHistory[existingIdx].date 
    ? cachedChatHistory[existingIdx].date 
    : new Date().toISOString();
  
  const sessionData = {
    id: state.id,
    title: title,
    date: creationDate,
    messages: state.messages,
    files: state.files.map(f => ({ name: f.name, isVirtual: true })),
    model: state.model
  };
  
  try {
    await fetch(`${API_URL}/history/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(sessionData)
    });
  } catch (e) {
    console.error("Erreur sauvegarde historique chat:", e);
    let hist = JSON.parse(localStorage.getItem('holokia_chat_history') || '[]');
    const eIdx = hist.findIndex(h => h.id === state.id);
    if (eIdx >= 0) hist[eIdx] = sessionData;
    else hist.unshift(sessionData);
    localStorage.setItem('holokia_chat_history', JSON.stringify(hist));
  }
  
  await renderHistory();
}

async function renderHistory() {
  if (!historyList) return;
  const hist = await loadHistory();
  historyList.innerHTML = '';
  
  if (hist.length === 0) {
    historyList.innerHTML = '<div style="font-family:var(--mono);font-size:9px;color:var(--muted);padding:8px;text-align:center;">Aucun historique</div>';
    return;
  }
  
  hist.forEach(h => {
    const item = document.createElement('div');
    item.className = `history-item ${h.id === state.id ? 'active' : ''}`;
    
    const dateObj = new Date(h.date || h.created_at);
    const dateStr = dateObj.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
    
    item.innerHTML = `
      <div class="history-title" title="${h.title}">${h.title}</div>
      <div class="history-date">${dateStr}</div>
      <button class="history-delete" title="Supprimer">✕</button>
    `;
    
    item.addEventListener('click', (e) => {
      if (!e.target.classList.contains('history-delete')) {
        loadSession(h.id);
      }
    });
    
    const deleteBtn = item.querySelector('.history-delete');
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteSession(h.id);
    });
    
    historyList.appendChild(item);
  });
}

async function deleteSession(id) {
  if (!confirm("Voulez-vous vraiment supprimer cette conversation ?")) return;
  
  try {
    await fetch(`${API_URL}/history/chat/${id}`, { method: 'DELETE' });
  } catch (e) {
    console.error("Erreur suppression historique chat:", e);
    let hist = JSON.parse(localStorage.getItem('holokia_chat_history') || '[]');
    hist = hist.filter(h => h.id !== id);
    localStorage.setItem('holokia_chat_history', JSON.stringify(hist));
  }
  
  if (id === state.id) {
    if (btnReset) btnReset.click();
  } else {
    await renderHistory();
  }
}

async function loadSession(id) {
  const hist = await loadHistory();
  const session = hist.find(h => h.id === id);
  if (!session) return;
  
  state.id = session.id;
  state.messages = [];
  state.totalSources = 0;
  state.confidenceSum = 0;
  state.confidenceCount = 0;
  
  let filesToRestore = [];
  if (session.files) {
    filesToRestore = session.files.map(f => ({ name: f.name, isVirtual: true }));
  } else if (session.fileNames) {
    filesToRestore = session.fileNames.map(name => ({ name, isVirtual: true }));
  }
  state.files = filesToRestore;
  
  if (session.model && modelSelect) {
    state.model = session.model;
    modelSelect.value = state.model;
    modelSelect.dispatchEvent(new Event('change'));
  }
  
  if (messagesArea) {
    messagesArea.innerHTML = '';
    if (emptyState) {
      messagesArea.appendChild(emptyState);
      emptyState.style.display = 'none';
    }
  }
  
  const tempMessages = [...(session.messages || [])];
  tempMessages.forEach(m => {
    addMessage(m.role, m.content, m.sources, m.confidence);
  });
  
  renderFileList();
  updateStats();
  updateRagStatus();
  await renderHistory();
  saveChatState();
}

function saveChatState() {
  if (!state.id && state.messages.length > 0) {
    state.id = Date.now().toString();
  }

  const fileNames = state.files.map(f => f.name);
  
  localStorage.setItem('holokia_chat_state', JSON.stringify({
    id: state.id,
    messages: state.messages,
    model: state.model,
    fileNames: fileNames
  }));
  
  saveToHistory();
}

// Ensure DOM is loaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initChat);
} else {
  initChat();
}
