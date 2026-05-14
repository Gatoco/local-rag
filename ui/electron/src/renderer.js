let currentProvider = null;
let currentModel = null;

async function loadProviders() {
  try {
    const data = await window.api.getProviders();
    const providerSelect = document.getElementById('provider-select');

    data.providers.forEach(p => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = `${p.id.toUpperCase()} (${p.models.length} models)`;
      providerSelect.appendChild(opt);
    });

    if (data.local && data.local.model) {
      const opt = document.createElement('option');
      opt.value = 'local';
      opt.textContent = `LOCAL (${data.local.model})`;
      providerSelect.appendChild(opt);
    }
  } catch (e) {
    console.error('Failed to load providers:', e);
  }
}

async function loadModels(provider) {
  const modelSelect = document.getElementById('model-select');
  modelSelect.innerHTML = '';

  if (provider === 'local') {
    const opt = document.createElement('option');
    opt.value = 'local';
    opt.textContent = 'Local Model';
    modelSelect.appendChild(opt);
    return;
  }

  try {
    const data = await window.api.getModels(provider);
    data.models.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = m;
      if (m === data.default) opt.selected = true;
      modelSelect.appendChild(opt);
    });
  } catch (e) {
    console.error('Failed to load models:', e);
  }
}

async function sendQuery() {
  const question = document.getElementById('question').value;
  const provider = document.getElementById('provider-select').value;
  const model = document.getElementById('model-select').value;
  const apiKey = document.getElementById('api-key').value;

  const resultDiv = document.getElementById('result');

  try {
    resultDiv.innerHTML = '<p>Procesando...</p>';

    const params = { question };
    if (provider !== 'local') {
      params.provider = provider;
      params.model = model;
      if (apiKey) params.api_key = apiKey;
    }

    const result = await window.api.query(params);

    resultDiv.innerHTML = `
      <div class="answer">
        <h3>Respuesta:</h3>
        <p>${result.answer}</p>
        <p class="meta">Latencia: ${result.latency_ms}ms | Modelo: ${result.model}</p>
      </div>
      <div class="sources">
        <h4>Fuentes (${result.sources.length})</h4>
        ${result.sources.map((s, i) => `
          <div class="source">
            <span class="source-id">#${i + 1}</span>
            <span class="source-content">${s.content.substring(0, 200)}...</span>
          </div>
        `).join('')}
      </div>
    `;
  } catch (e) {
    resultDiv.innerHTML = `<p class="error">Error: ${e.message}</p>`;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('provider-select').addEventListener('change', (e) => {
    loadModels(e.target.value);
  });

  loadProviders();
});