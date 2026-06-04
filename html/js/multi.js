// MULTI-DOCS LOGIC
const multiFileInput = document.getElementById('multiFileInput');
const multiDropZone = document.getElementById('multiDropZone');
const multiFileList = document.getElementById('multiFileList');
let multiFiles = [];

multiDropZone.addEventListener('click', () => multiFileInput.click());
multiDropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  multiDropZone.style.background = 'rgba(0,71,255,0.05)';
});
multiDropZone.addEventListener('dragleave', (e) => {
  e.preventDefault();
  multiDropZone.style.background = 'transparent';
});
multiDropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  multiDropZone.style.background = 'transparent';
  handleMultiFiles(e.dataTransfer.files);
});
multiFileInput.addEventListener('change', (e) => {
  handleMultiFiles(e.target.files);
});

function handleMultiFiles(files) {
  for (let i = 0; i < files.length; i++) {
    multiFiles.push(files[i]);
    const li = document.createElement('li');
    li.textContent = `📄 ${files[i].name}`;
    li.style.marginBottom = '5px';
    multiFileList.appendChild(li);
  }
}

const multiQuestionList = document.getElementById('multiQuestionList');
let multiQuestions = [];

function addMultiQuestion(q) {
  if (!q || multiQuestions.includes(q)) return;
  multiQuestions.push(q);
  
  const li = document.createElement('li');
  li.style.background = '#fff';
  li.style.border = '1px solid var(--line)';
  li.style.padding = '10px 15px';
  li.style.display = 'flex';
  li.style.justifyContent = 'space-between';
  li.style.alignItems = 'center';
  
  const text = document.createElement('span');
  text.textContent = q;
  text.style.fontFamily = 'var(--body)';
  text.style.fontSize = '14px';
  
  const btnRemove = document.createElement('button');
  btnRemove.textContent = '×';
  btnRemove.style.background = 'none';
  btnRemove.style.border = 'none';
  btnRemove.style.color = 'var(--red)';
  btnRemove.style.cursor = 'pointer';
  btnRemove.style.fontSize = '16px';
  btnRemove.onclick = () => {
    multiQuestions = multiQuestions.filter(x => x !== q);
    li.remove();
  };
  
  li.appendChild(text);
  li.appendChild(btnRemove);
  multiQuestionList.appendChild(li);
}

document.getElementById('btnAddPredef').addEventListener('click', () => {
  const sel = document.getElementById('multiPredefSelect');
  addMultiQuestion(sel.value);
  sel.value = '';
});

document.getElementById('btnAddCustom').addEventListener('click', () => {
  const inp = document.getElementById('multiCustomQuestion');
  addMultiQuestion(inp.value.trim());
  inp.value = '';
});

document.getElementById('btnMultiExtract').addEventListener('click', async () => {
  if (multiFiles.length === 0) {
    alert("Veuillez ajouter au moins un document.");
    return;
  }
  if (multiQuestions.length === 0) {
    alert("Veuillez ajouter au moins une question.");
    return;
  }
  
  const status = document.getElementById('multiStatus');
  const btn = document.getElementById('btnMultiExtract');
  const resContainer = document.getElementById('multiResultsContainer');
  
  status.style.display = 'block';
  btn.disabled = true;
  btn.style.opacity = '0.5';
  resContainer.innerHTML = '<div style="text-align:center; margin-top:50px;"><div class="spinner" style="margin:0 auto 20px;"></div><p style="font-family:var(--mono); font-size:12px; color:var(--blue);">Analyse en cours... Cela peut prendre plusieurs minutes.</p></div>';
  
  const formData = new FormData();
  multiFiles.forEach(f => formData.append('files', f));
  formData.append('questions', JSON.stringify(multiQuestions));
  
  // Si vous avez un selecteur de modèle dans le HTML pour ce script (optionnel)
  const modelSelect = document.getElementById('modelSelect');
  const modelVal = modelSelect ? modelSelect.value : 'groq';
  
  const provider = modelVal === 'groq' ? 'groq' : 'ollama';
  const modelName = modelVal === 'groq' ? 'llama-3.3-70b-versatile' : modelVal;
  
  formData.append('provider', provider);
  formData.append('model', modelName);
  
  try {
    const response = await fetch('http://localhost:8000/extract-multi', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    if (data.ok) {
      renderMultiResults(data.results);
    } else {
      resContainer.innerHTML = `<div style="color:var(--red); padding:20px;">Erreur: ${data.error}</div>`;
    }
  } catch (err) {
    resContainer.innerHTML = `<div style="color:var(--red); padding:20px;">Erreur de connexion au serveur.</div>`;
  } finally {
    status.style.display = 'none';
    btn.disabled = false;
    btn.style.opacity = '1';
  }
});

function renderMultiResults(results) {
  const container = document.getElementById('multiResultsContainer');
  container.innerHTML = '';
  
  // 1. Synthèse
  if (results.synthese_comparative) {
    const synthDiv = document.createElement('div');
    synthDiv.style.background = 'rgba(0,71,255,0.05)';
    synthDiv.style.border = '1px solid var(--blue)';
    synthDiv.style.padding = '20px';
    synthDiv.style.marginBottom = '30px';
    
    synthDiv.innerHTML = `
      <h3 style="font-family: var(--display); font-size: 24px; margin-bottom: 15px; color: var(--blue);">Synthèse Comparative</h3>
      <div style="font-family: var(--body); font-size: 14px; line-height: 1.6; white-space: pre-wrap;">${results.synthese_comparative}</div>
    `;
    container.appendChild(synthDiv);
  }
  
  // 2. Par document
  const docs = results.results_by_document || {};
  for (const [fname, qRes] of Object.entries(docs)) {
    const docDiv = document.createElement('div');
    docDiv.style.background = '#fff';
    docDiv.style.border = '1px solid var(--line)';
    docDiv.style.padding = '20px';
    docDiv.style.marginBottom = '20px';
    
    let html = `<h4 style="font-family: var(--mono); font-size: 14px; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid var(--line);">📄 ${fname}</h4>`;
    
    for (const [q, ans] of Object.entries(qRes)) {
      const val = ans.valeur || '<span style="color:var(--muted)">Non trouvé</span>';
      let sourceHtml = '';
      if (ans.source && ans.source.page !== null) {
        sourceHtml = `<span style="font-family:var(--mono); font-size:10px; color:var(--teal); margin-left:10px; background:rgba(0,255,170,0.1); padding:2px 6px; border-radius:4px;">Page ${ans.source.page}</span>`;
      }
      
      html += `
        <div style="margin-bottom: 15px;">
          <div style="font-family: var(--body); font-weight: 500; font-size: 14px; margin-bottom: 5px;">${q}</div>
          <div style="font-family: var(--body); font-size: 14px; color: var(--ink); display:flex; align-items:center;">
            ${val} ${sourceHtml}
          </div>
        </div>
      `;
    }
    
    docDiv.innerHTML = html;
    container.appendChild(docDiv);
  }
}