let allExtractions = [];
let currentExtractionId = null;
const COMPLETENESS_MIN_CONFIDENCE = 0.6;

async function loadHistorique() {
  const tbody = document.getElementById('historiqueTableBody');
  try {
    const res = await Auth.apiFetch(`${API_URL}/extractions`);
    const data = await res.json();
    if (data.ok) {
      allExtractions = data.data || [];
      renderHistorique(allExtractions);
      populateCompareSelect(allExtractions);
    } else {
      tbody.innerHTML = `<tr><td colspan="7" style="padding: 20px; color: var(--red);">${data.error || 'Erreur de chargement'}</td></tr>`;
    }
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="7" style="padding: 20px; color: var(--red);">Erreur réseau</td></tr>`;
  }
}

function populateCompareSelect(extractions) {
  const select = document.getElementById('compareSelect');
  if (!select) return;
  select.innerHTML = '<option value="">-- Choisir --</option>';
  
  extractions.forEach(ext => {
    const date = new Date(ext.created_at).toLocaleString('fr-FR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
    const option = document.createElement('option');
    option.value = ext.id;
    option.textContent = `${ext.company || 'Inconnu'} - ${date} (${ext.model || ext.provider || '?'})`;
    select.appendChild(option);
  });
}

function calculateAverageConfidence(ext) {
  if (!ext) return 0;
  
  // Utiliser le résultat déjà normalisé par le serveur si disponible (T8.27)
  if (ext.ui_result) {
    let total = 0;
    let count = 0;
    const sections = ['diagnostic_strategique', 'diagnostic_financier', 'diagnostic_rh', 'diagnostic_data', 'diagnostic_cyber_gouvernance'];
    
    sections.forEach(sec => {
      if (ext.ui_result[sec]) {
        Object.values(ext.ui_result[sec]).forEach(field => {
          if (field && typeof field === 'object' && typeof field.confiance === 'number') {
            total += field.confiance;
            count++;
          }
        });
      }
    });
    return count > 0 ? (total / count) : 0;
  }

  // Fallback sur l'ancienne méthode si pas de ui_result
  const result = ext.result;
  if (!result) return 0;
  const dataToAnalyze = result.result ? result.result : result;
  
  let total = 0;
  let count = 0;
  const sections = Object.keys(dataToAnalyze).filter(k => k.startsWith('diagnostic_'));
  
  sections.forEach(sec => {
    if (dataToAnalyze[sec]) {
      Object.values(dataToAnalyze[sec]).forEach(field => {
        if (field && typeof field === 'object' && typeof field.confiance === 'number') {
          total += field.confiance;
          count++;
        }
      });
    }
  });
  
  return count > 0 ? (total / count) : 0;
}

function isFieldFilled(field) {
  if (!field || typeof field !== 'object') return false;
  const val = field.valeur;
  const hasValue = Array.isArray(val)
    ? val.length > 0
    : (val !== null && val !== undefined && String(val).trim() !== '');
  if (!hasValue) return false;
  const conf = field.confiance;
  if (typeof conf === 'number' && Number.isFinite(conf)) {
    return conf >= COMPLETENESS_MIN_CONFIDENCE;
  }
  return true;
}

function calculateCompleteness(ext) {
  if (!ext) return 0;
  const result = ext.ui_result || ext.result;
  if (!result || typeof result !== 'object') return 0;
  const dataToAnalyze = result.result && typeof result.result === 'object' ? result.result : result;
  const sections = ['diagnostic_strategique', 'diagnostic_financier', 'diagnostic_rh', 'diagnostic_data', 'diagnostic_cyber_gouvernance'];
  let total = 0;
  let filled = 0;
  sections.forEach(sec => {
    const secObj = dataToAnalyze[sec];
    if (!secObj || typeof secObj !== 'object') return;
    Object.values(secObj).forEach(field => {
      if (field && typeof field === 'object') {
        total += 1;
        if (isFieldFilled(field)) filled += 1;
      }
    });
  });
  return total > 0 ? (filled / total) : 0;
}

function renderHistorique(extractions) {
  const tbody = document.getElementById('historiqueTableBody');
  tbody.innerHTML = '';
  
  if (extractions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="padding: 20px; text-align: center; color: var(--muted);">Aucune extraction trouvée.</td></tr>`;
    return;
  }
  
  extractions.forEach(ext => {
    const date = new Date(ext.created_at).toLocaleString('fr-FR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
    
    const conf = calculateAverageConfidence(ext);
    const confColor = conf > 0.8 ? 'var(--teal)' : (conf > 0.5 ? '#f39c12' : 'var(--red)');
    const comp = calculateCompleteness(ext);
    const compColor = comp > 0.8 ? 'var(--teal)' : (comp > 0.5 ? '#f39c12' : 'var(--red)');
    
    const tr = document.createElement('tr');
    tr.style.borderBottom = '1px solid var(--line)';
    tr.innerHTML = `
      <td style="padding: 15px; font-family: var(--mono); font-size: 12px;">${date}</td>
      <td style="padding: 15px; font-family: var(--body); font-weight: 500;">${ext.company || '-'}</td>
      <td style="padding: 15px; font-family: var(--mono); font-size: 11px; color: var(--muted);">${ext.document_file || '-'}</td>
      <td style="padding: 15px; font-family: var(--mono); font-size: 12px;">
        <span style="background: rgba(0,71,255,0.1); color: var(--blue); padding: 4px 8px; border-radius: 4px;">
          ${ext.model || ext.provider || '-'}
        </span>
      </td>
      <td style="padding: 15px; font-family: var(--mono); font-size: 12px; color: ${confColor}; font-weight: 500;">
        ${(conf * 100).toFixed(1)}%
      </td>
      <td style="padding: 15px; font-family: var(--mono); font-size: 12px; color: ${compColor}; font-weight: 500;">
        ${(comp * 100).toFixed(1)}%
      </td>
      <td style="padding: 15px; display: flex; gap: 8px;">
        <button class="btn-load" data-id="${ext.id}" style="background: var(--blue); color: #fff; border: none; padding: 6px 12px; font-family: var(--mono); font-size: 10px; cursor: pointer; border-radius: 4px;">OUVRIR LE DIAGNOSTIC</button>
        <button class="btn-view" data-id="${ext.id}" style="background: var(--ink); color: #fff; border: none; padding: 6px 12px; font-family: var(--mono); font-size: 10px; cursor: pointer; border-radius: 4px;">VOIR JSON</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  
  document.querySelectorAll('.btn-view').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = e.target.getAttribute('data-id');
      openModal(id);
    });
  });

  document.querySelectorAll('.btn-load').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const id = e.target.getAttribute('data-id');
      const ext = allExtractions.find(item => item.id == id);
      if (ext) {
        try {
          // Utiliser en priorité le résultat normalisé par le serveur (T8.27)
          let dataToStore = ext.ui_result || ext.result;
          
          // Si on utilise ext.result (ancien format), on tente de désimbriquer
          if (!ext.ui_result && ext.result && ext.result.result && (ext.result.result.diagnostic_strategique || ext.result.result.meta)) {
            dataToStore = ext.result.result;
          }
          
          localStorage.setItem('holokia_last_result', JSON.stringify(dataToStore));
          window.location.href = 'diagnostic.html';
        } catch (err) {
          console.error("Erreur lors du chargement de l'extraction", err);
          alert("Impossible de charger cette extraction.");
        }
      }
    });
  });
}

function filterHistorique() {
  const entrepriseStr = document.getElementById('filterEntreprise').value.toLowerCase();
  const dateStr = document.getElementById('filterDate').value;
  const modelStr = document.getElementById('filterModel').value.toLowerCase();
  
  const filtered = allExtractions.filter(ext => {
    const matchEnt = !entrepriseStr || (ext.company && ext.company.toLowerCase().includes(entrepriseStr));
    const extDate = ext.created_at ? ext.created_at.split('T')[0] : '';
    const matchDate = !dateStr || extDate === dateStr;
    const matchModel = !modelStr || (
      (ext.model && ext.model.toLowerCase().includes(modelStr)) || 
      (ext.provider && ext.provider.toLowerCase().includes(modelStr))
    );
    
    return matchEnt && matchDate && matchModel;
  });
  
  renderHistorique(filtered);
}

document.getElementById('filterEntreprise').addEventListener('input', filterHistorique);
document.getElementById('filterDate').addEventListener('change', filterHistorique);
document.getElementById('filterModel').addEventListener('change', filterHistorique);

// Initialize fetch
document.addEventListener('DOMContentLoaded', () => {
  loadHistorique();
});

// Modal logic
const modal = document.getElementById('historiqueModal');
const modalJsonContainer = document.getElementById('modalJsonContainer');
const modalCompareContainer = document.getElementById('modalCompareContainer');

async function openModal(id) {
  currentExtractionId = id;
  const ext = allExtractions.find(e => e.id == id);
  if (!ext) return;
  
  document.getElementById('modalTitle').textContent = `Détails : ${ext.company || 'Inconnu'}`;
  document.getElementById('modalJson').textContent = JSON.stringify(ext.result, null, 2);
  
  modalJsonContainer.style.display = 'block';
  modalCompareContainer.style.display = 'none';
  document.getElementById('btnCompare').style.display = 'block';
  document.getElementById('btnCompare').textContent = 'Comparer';
  
  // Set current selected in compare select
  const compareSelect = document.getElementById('compareSelect');
  compareSelect.value = '';
  
  modal.style.display = 'block';
}

document.getElementById('btnCloseModal').addEventListener('click', () => {
  modal.style.display = 'none';
});
