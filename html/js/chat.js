// CHAT LOGIC
const chatFileInput = document.getElementById('chatFileInput');
const chatDropZone = document.getElementById('chatDropZone');
const chatFileList = document.getElementById('chatFileList');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');
const chatMessages = document.getElementById('chatMessages');
const btnSendChat = document.getElementById('btnSendChat');
const btnNewChat = document.getElementById('btnNewChat');
const chatModelSelect = document.getElementById('chatModelSelect');

let chatFiles = [];
let chatHistory = [];

chatDropZone.addEventListener('click', () => chatFileInput.click());
chatDropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  chatDropZone.style.background = 'rgba(0,71,255,0.05)';
});
chatDropZone.addEventListener('dragleave', (e) => {
  e.preventDefault();
  chatDropZone.style.background = '#fff';
});
chatDropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  chatDropZone.style.background = '#fff';
  handleChatFiles(e.dataTransfer.files);
});
chatFileInput.addEventListener('change', (e) => {
  handleChatFiles(e.target.files);
});

function handleChatFiles(files) {
  for (let i = 0; i < files.length; i++) {
    chatFiles.push(files[i]);
    const li = document.createElement('li');
    li.textContent = `📄 ${files[i].name}`;
    li.style.marginBottom = '5px';
    chatFileList.appendChild(li);
  }
  if (chatFiles.length > 0 && chatHistory.length === 0) {
    chatMessages.innerHTML = ''; // Clear "Upload documents to start"
    appendChatMessage('system', 'Documents chargés. Posez votre question !');
  }
}

function appendChatMessage(role, text, citations = []) {
  const msgDiv = document.createElement('div');
  msgDiv.style.display = 'flex';
  msgDiv.style.flexDirection = 'column';
  msgDiv.style.maxWidth = '80%';
  
  if (role === 'user') {
    msgDiv.style.alignSelf = 'flex-end';
    msgDiv.innerHTML = `<div style="background: var(--blue); color: #fff; padding: 15px 20px; border-radius: 20px 20px 0 20px; font-size: 14px; line-height: 1.5;">${text}</div>`;
  } else if (role === 'system') {
    msgDiv.style.alignSelf = 'center';
    msgDiv.style.maxWidth = '100%';
    msgDiv.innerHTML = `<div style="font-family: var(--mono); font-size: 11px; color: var(--muted); text-transform: uppercase;">${text}</div>`;
  } else {
    // assistant
    msgDiv.style.alignSelf = 'flex-start';
    let html = `<div style="background: #f5f5f5; border: 1px solid var(--line); color: var(--ink); padding: 15px 20px; border-radius: 20px 20px 20px 0; font-size: 14px; line-height: 1.6; white-space: pre-wrap;">${text}</div>`;
    
    if (citations && citations.length > 0) {
      html += `<div style="margin-top: 10px; display: flex; flex-direction: column; gap: 5px;">`;
      citations.forEach(c => {
        html += `<div style="font-family: var(--mono); font-size: 10px; color: var(--muted); background: rgba(0,71,255,0.05); padding: 8px 12px; border-left: 2px solid var(--blue);">
          <strong>Page ${c.page} (${c.file_name})</strong> : "${c.extrait.replace(/\n/g, ' ')}"
        </div>`;
      });
      html += `</div>`;
    }
    msgDiv.innerHTML = html;
  }
  
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();
  const msg = chatInput.value.trim();
  if (!msg) return;
  
  if (chatFiles.length === 0) {
    alert("Veuillez uploader au moins un document avant de poser une question.");
    return;
  }
  
  appendChatMessage('user', msg);
  chatInput.value = '';
  btnSendChat.disabled = true;
  btnSendChat.style.opacity = '0.5';
  
  // Create loading indicator
  const loadingId = 'loading-' + Date.now();
  const loadingDiv = document.createElement('div');
  loadingDiv.id = loadingId;
  loadingDiv.style.alignSelf = 'flex-start';
  loadingDiv.innerHTML = `<div style="font-family: var(--mono); font-size: 11px; color: var(--blue);">L'IA réfléchit...</div>`;
  chatMessages.appendChild(loadingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  
  const formData = new FormData();
  // Only send files if it's the first message or if new files were added (simplified: always send to ensure backend has them, or rely on backend caching)
  // Since our backend uses FAISS cache based on file content/name, sending them is fine.
  chatFiles.forEach(f => formData.append('files', f));
  formData.append('message', msg);
  formData.append('history', JSON.stringify(chatHistory));
  
  let provider = 'groq';
  let model = '';
  const selModel = chatModelSelect.value;
  if (selModel === 'gpt-4o') {
    provider = 'openai';
  } else if (selModel === 'mistral') {
    provider = 'ollama';
    model = 'mistral';
  } else if (selModel === 'qwen3:8b') {
    provider = 'ollama';
    model = 'qwen3:8b';
  } else {
    model = 'llama-3.3-70b-versatile';
  }
  
  formData.append('provider', provider);
  if (model) formData.append('model', model);
  
  try {
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    document.getElementById(loadingId).remove();
    
    if (data.ok) {
      appendChatMessage('assistant', data.answer, data.citations);
      chatHistory.push({ role: 'user', content: msg });
      chatHistory.push({ role: 'assistant', content: data.answer });
    } else {
      appendChatMessage('system', `Erreur: ${data.error}`);
    }
  } catch (err) {
    document.getElementById(loadingId).remove();
    appendChatMessage('system', 'Erreur de connexion au serveur.');
  } finally {
    btnSendChat.disabled = false;
    btnSendChat.style.opacity = '1';
    chatInput.focus();
  }
});

btnNewChat.addEventListener('click', () => {
  if (confirm("Voulez-vous vraiment effacer la conversation et les documents actuels ?")) {
    chatFiles = [];
    chatHistory = [];
    chatFileList.innerHTML = '';
    chatMessages.innerHTML = `<div style="text-align: center; color: var(--muted); font-family: var(--mono); font-size: 12px; margin-top: auto; margin-bottom: auto;">
      Uploadez des documents pour commencer à discuter.
    </div>`;
  }
});

