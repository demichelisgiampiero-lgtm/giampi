// Giornale dei Lavori — logica frontend (vanilla JS).
'use strict';

const stato = {
  cantieri: [],
  cantiereId: null,
  voci: [],
};

// --- Utility ----------------------------------------------------------------

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));

/** Esegue una chiamata API JSON, lanciando un errore leggibile in caso di fallimento. */
async function api(metodo, url, corpo) {
  const opts = { method: metodo, headers: {} };
  if (corpo !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(corpo);
  }
  const resp = await fetch(url, opts);
  if (resp.status === 204) return null;
  const dati = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(dati.errore || `Errore ${resp.status}`);
  return dati;
}

const escapeHtml = (s) =>
  String(s ?? '').replace(/[&<>"']/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

const euro = (n) =>
  (Number(n) || 0).toLocaleString('it-IT', { style: 'currency', currency: 'EUR' });

const numIt = (n, dec = 2) =>
  n === null || n === undefined || n === ''
    ? '—'
    : Number(n).toLocaleString('it-IT', { minimumFractionDigits: dec, maximumFractionDigits: dec });

const perc = (n) => (n === null || n === undefined ? '—' : `${numIt(n, 1)}%`);

function toast(msg, tipo = '') {
  const el = $('#toast');
  el.textContent = msg;
  el.className = `toast ${tipo}`;
  setTimeout(() => el.classList.add('hidden'), 3200);
}

// --- Modale -----------------------------------------------------------------

function apriModale(titolo, corpoHtml, azioni) {
  $('#modale-titolo').textContent = titolo;
  $('#modale-corpo').innerHTML = corpoHtml;
  const cont = $('#modale-azioni');
  cont.innerHTML = '';
  for (const a of azioni) {
    const b = document.createElement('button');
    b.textContent = a.testo;
    b.className = `btn ${a.classe || ''}`;
    b.onclick = a.onClick;
    cont.appendChild(b);
  }
  $('#modale').classList.remove('hidden');
}
function chiudiModale() { $('#modale').classList.add('hidden'); }

// --- Cantieri ---------------------------------------------------------------

async function caricaCantieri() {
  stato.cantieri = await api('GET', '/api/cantieri');
  const sel = $('#cantiere-select');
  sel.innerHTML = '';
  if (stato.cantieri.length === 0) {
    sel.innerHTML = '<option value="">— nessun cantiere —</option>';
    stato.cantiereId = null;
  } else {
    for (const c of stato.cantieri) {
      const o = document.createElement('option');
      o.value = c.id;
      o.textContent = c.codice_commessa ? `${c.codice_commessa} — ${c.nome}` : c.nome;
      sel.appendChild(o);
    }
    if (!stato.cantieri.some((c) => c.id === stato.cantiereId)) {
      stato.cantiereId = stato.cantieri[0].id;
    }
    sel.value = stato.cantiereId;
  }
  aggiornaVisibilita();
}

function cantiereCorrente() {
  return stato.cantieri.find((c) => c.id === stato.cantiereId) || null;
}

const CAMPI_CANTIERE_FORM = [
  ['nome', 'Nome cantiere *', 'text'],
  ['codice_commessa', 'Codice commessa', 'text'],
  ['committente', 'Committente / Stazione appaltante', 'text'],
  ['importo_contrattuale', 'Importo contrattuale (€)', 'number'],
  ['rif_contratto', 'Riferimento contratto', 'text'],
  ['rif_csa', 'Riferimento Capitolato (CSA)', 'text'],
  ['data_consegna', 'Data consegna lavori', 'date'],
  ['data_inizio', 'Data inizio', 'date'],
  ['data_fine_prevista', 'Data fine prevista', 'date'],
];

function formCantiere(c = {}) {
  const campi = CAMPI_CANTIERE_FORM.map(([k, label, tipo]) => `
    <div class="campo ${tipo === 'text' && k === 'committente' ? 'full' : ''}">
      <label>${label}</label>
      <input name="${k}" type="${tipo}" ${tipo === 'number' ? 'step="0.01"' : ''}
             value="${escapeHtml(c[k] ?? '')}" />
    </div>`).join('');
  return `<form id="form-cantiere"><div class="form-grid">${campi}
    <div class="campo full"><label>Note</label>
      <textarea name="note">${escapeHtml(c.note ?? '')}</textarea></div>
    </div></form>`;
}

function leggiForm(idForm) {
  const dati = {};
  for (const el of $(idForm).elements) {
    if (el.name) dati[el.name] = el.value === '' ? null : el.value;
  }
  return dati;
}

function modaleCantiere(esistente) {
  const c = esistente || {};
  const azioni = [
    { testo: 'Annulla', classe: 'btn-secondary', onClick: chiudiModale },
    {
      testo: 'Salva', onClick: async () => {
        const dati = leggiForm('#form-cantiere');
        try {
          if (c.id) await api('PUT', `/api/cantieri/${c.id}`, dati);
          else {
            const nuovo = await api('POST', '/api/cantieri', dati);
            stato.cantiereId = nuovo.id;
          }
          chiudiModale();
          await caricaCantieri();
          await ricaricaTabCorrente();
          toast('Cantiere salvato.', 'ok');
        } catch (e) { toast(e.message, 'errore'); }
      },
    },
  ];
  if (c.id) {
    azioni.unshift({
      testo: 'Elimina', classe: 'btn-danger', onClick: async () => {
        if (!confirm('Eliminare il cantiere e tutti i suoi dati?')) return;
        try {
          await api('DELETE', `/api/cantieri/${c.id}`);
          stato.cantiereId = null;
          chiudiModale();
          await caricaCantieri();
          await ricaricaTabCorrente();
          toast('Cantiere eliminato.', 'ok');
        } catch (e) { toast(e.message, 'errore'); }
      },
    });
  }
  apriModale(c.id ? 'Modifica cantiere' : 'Nuovo cantiere', formCantiere(c), azioni);
}

// --- Schede di cantiere (voci CME) ------------------------------------------

async function caricaVoci() {
  if (!stato.cantiereId) { stato.voci = []; return; }
  stato.voci = await api('GET', `/api/cantieri/${stato.cantiereId}/voci`);
}

async function renderSchede() {
  await caricaVoci();
  const tb = $('#tabella-voci tbody');
  if (stato.voci.length === 0) {
    tb.innerHTML = '<tr><td colspan="8" class="vuoto">Nessuna voce. Aggiungi una voce o importa il CME da CSV.</td></tr>';
    return;
  }
  tb.innerHTML = stato.voci.map((v) => `
    <tr>
      <td>${escapeHtml(v.codice ?? '')}</td>
      <td>${escapeHtml(v.descrizione)}</td>
      <td>${escapeHtml(v.categoria ?? '')}</td>
      <td>${escapeHtml(v.unita_misura ?? '')}</td>
      <td class="num">${numIt(v.quantita_progetto, 3)}</td>
      <td class="num">${euro(v.prezzo_unitario)}</td>
      <td class="num">${euro(v.quantita_progetto * v.prezzo_unitario)}</td>
      <td class="riga-azioni">
        <button class="btn btn-ghost btn-mini" data-edit-voce="${v.id}">✎</button>
        <button class="btn btn-ghost btn-mini" data-del-voce="${v.id}">🗑</button>
      </td>
    </tr>`).join('');

  tb.querySelectorAll('[data-edit-voce]').forEach((b) =>
    b.onclick = () => modaleVoce(stato.voci.find((v) => v.id == b.dataset.editVoce)));
  tb.querySelectorAll('[data-del-voce]').forEach((b) =>
    b.onclick = () => eliminaVoce(b.dataset.delVoce));
}

function formVoce(v = {}) {
  return `<form id="form-voce"><div class="form-grid">
    <div class="campo"><label>Codice</label><input name="codice" value="${escapeHtml(v.codice ?? '')}" /></div>
    <div class="campo"><label>Categoria / Capitolo</label><input name="categoria" value="${escapeHtml(v.categoria ?? '')}" /></div>
    <div class="campo full"><label>Descrizione *</label><textarea name="descrizione">${escapeHtml(v.descrizione ?? '')}</textarea></div>
    <div class="campo"><label>Unità di misura</label><input name="unita_misura" value="${escapeHtml(v.unita_misura ?? '')}" /></div>
    <div class="campo"><label>Quantità di progetto</label><input name="quantita_progetto" type="number" step="0.001" value="${v.quantita_progetto ?? ''}" /></div>
    <div class="campo"><label>Prezzo unitario (€)</label><input name="prezzo_unitario" type="number" step="0.01" value="${v.prezzo_unitario ?? ''}" /></div>
  </div></form>`;
}

function modaleVoce(esistente) {
  const v = esistente || {};
  apriModale(v.id ? 'Modifica voce' : 'Nuova voce di computo', formVoce(v), [
    { testo: 'Annulla', classe: 'btn-secondary', onClick: chiudiModale },
    {
      testo: 'Salva', onClick: async () => {
        const dati = leggiForm('#form-voce');
        try {
          if (v.id) await api('PUT', `/api/voci/${v.id}`, dati);
          else await api('POST', `/api/cantieri/${stato.cantiereId}/voci`, dati);
          chiudiModale();
          await renderSchede();
          toast('Voce salvata.', 'ok');
        } catch (e) { toast(e.message, 'errore'); }
      },
    },
  ]);
}

async function eliminaVoce(id) {
  if (!confirm('Eliminare questa voce? Verranno rimossi anche i relativi avanzamenti.')) return;
  try {
    await api('DELETE', `/api/voci/${id}`);
    await renderSchede();
    toast('Voce eliminata.', 'ok');
  } catch (e) { toast(e.message, 'errore'); }
}

function modaleImport() {
  const corpo = `
    <p>Incolla il contenuto CSV del computo oppure scegli un file.
    Intestazioni riconosciute: <code>codice, descrizione, categoria, um, quantità, prezzo</code>.</p>
    <div class="campo"><input type="file" id="file-csv" accept=".csv,text/csv" /></div>
    <div class="campo"><label>Oppure incolla qui</label>
      <textarea id="csv-testo" rows="8" placeholder="codice;descrizione;um;quantità;prezzo"></textarea></div>`;
  apriModale('Importa CME da CSV', corpo, [
    { testo: 'Annulla', classe: 'btn-secondary', onClick: chiudiModale },
    {
      testo: 'Importa', onClick: async () => {
        const file = $('#file-csv').files[0];
        const testo = file ? await file.text() : $('#csv-testo').value;
        if (!testo || !testo.trim()) { toast('Nessun contenuto CSV.', 'errore'); return; }
        try {
          const r = await api('POST', `/api/cantieri/${stato.cantiereId}/voci/import`, { csv: testo });
          chiudiModale();
          await renderSchede();
          toast(`Importate ${r.importate} voci.` + (r.avvisi?.length ? ` (${r.avvisi.length} avvisi)` : ''), 'ok');
        } catch (e) { toast(e.message, 'errore'); }
      },
    },
  ]);
  setTimeout(() => {
    $('#file-csv').onchange = async (ev) => {
      const f = ev.target.files[0];
      if (f) $('#csv-testo').value = await f.text();
    };
  }, 0);
}

// --- Giornale ---------------------------------------------------------------

async function renderGiornale() {
  if (!stato.cantiereId) return;
  const da = $('#filtro-da').value, a = $('#filtro-a').value;
  const q = new URLSearchParams();
  if (da) q.set('from', da);
  if (a) q.set('to', a);
  const righe = await api('GET', `/api/cantieri/${stato.cantiereId}/giornaliere?${q}`);
  const tb = $('#tabella-giorn tbody');
  if (righe.length === 0) {
    tb.innerHTML = '<tr><td colspan="7" class="vuoto">Nessuna giornaliera registrata.</td></tr>';
    return;
  }
  tb.innerHTML = righe.map((g) => `
    <tr>
      <td>${escapeHtml(g.data)}</td>
      <td>${escapeHtml(g.meteo ?? '')}</td>
      <td>${escapeHtml(g.temperatura ?? '')}</td>
      <td class="num">${g.maestranze_numero ?? '—'}</td>
      <td>${escapeHtml(g.mezzi ?? '')}</td>
      <td class="num">${g.n_avanzamenti}</td>
      <td class="riga-azioni">
        <button class="btn btn-ghost btn-mini" data-edit-g="${g.id}">✎</button>
        <button class="btn btn-ghost btn-mini" data-del-g="${g.id}">🗑</button>
      </td>
    </tr>`).join('');

  tb.querySelectorAll('[data-edit-g]').forEach((b) =>
    b.onclick = () => modaleGiornaliera(b.dataset.editG));
  tb.querySelectorAll('[data-del-g]').forEach((b) =>
    b.onclick = () => eliminaGiornaliera(b.dataset.delG));
}

function rigaAvanzamento(a = {}) {
  const opts = stato.voci.map((v) =>
    `<option value="${v.id}" ${a.voce_computo_id == v.id ? 'selected' : ''}>
      ${escapeHtml((v.codice ? v.codice + ' — ' : '') + v.descrizione.slice(0, 60))}
    </option>`).join('');
  return `<tr class="riga-avanz">
    <td><select class="av-voce"><option value="">— scegli voce —</option>${opts}</select></td>
    <td><input class="av-qta" type="number" step="0.001" value="${a.quantita_eseguita ?? ''}" placeholder="q.tà" /></td>
    <td><input class="av-note" value="${escapeHtml(a.note ?? '')}" placeholder="note" /></td>
    <td><button type="button" class="btn btn-ghost btn-mini av-del">✕</button></td>
  </tr>`;
}

async function modaleGiornaliera(id) {
  await caricaVoci();
  let g = { avanzamenti: [] };
  if (id) g = await api('GET', `/api/giornaliere/${id}`);

  const corpo = `<form id="form-giorn"><div class="form-grid">
    <div class="campo"><label>Data *</label><input name="data" type="date" value="${escapeHtml(g.data ?? new Date().toISOString().slice(0, 10))}" /></div>
    <div class="campo"><label>Meteo</label><input name="meteo" value="${escapeHtml(g.meteo ?? '')}" placeholder="sereno, pioggia…" /></div>
    <div class="campo"><label>Temperatura</label><input name="temperatura" value="${escapeHtml(g.temperatura ?? '')}" placeholder="es. 18°C" /></div>
    <div class="campo"><label>N. maestranze</label><input name="maestranze_numero" type="number" value="${g.maestranze_numero ?? ''}" /></div>
    <div class="campo full"><label>Maestranze (descrizione)</label><textarea name="maestranze_descrizione">${escapeHtml(g.maestranze_descrizione ?? '')}</textarea></div>
    <div class="campo full"><label>Mezzi e attrezzature</label><textarea name="mezzi">${escapeHtml(g.mezzi ?? '')}</textarea></div>
    <div class="campo full"><label>Materiali</label><textarea name="materiali">${escapeHtml(g.materiali ?? '')}</textarea></div>
    <div class="campo full"><label>Note / annotazioni</label><textarea name="note">${escapeHtml(g.note ?? '')}</textarea></div>
    </div>
    <h4>Avanzamenti (quantità eseguite per voce)</h4>
    ${stato.voci.length === 0 ? '<p class="vuoto">Nessuna voce CME: aggiungi prima le schede di cantiere.</p>' : ''}
    <table class="avanz-table"><thead><tr><th>Voce di computo</th><th>Q.tà eseguita</th><th>Note</th><th></th></tr></thead>
      <tbody id="avanz-body">${(g.avanzamenti || []).map(rigaAvanzamento).join('')}</tbody></table>
    <button type="button" class="btn btn-secondary btn-mini" id="btn-add-avanz" ${stato.voci.length === 0 ? 'disabled' : ''}>+ Aggiungi riga</button>
  </form>`;

  apriModale(id ? 'Modifica giornaliera' : 'Nuova giornaliera', corpo, [
    { testo: 'Annulla', classe: 'btn-secondary', onClick: chiudiModale },
    {
      testo: 'Salva', onClick: async () => {
        const dati = leggiForm('#form-giorn');
        dati.avanzamenti = $$('#avanz-body .riga-avanz')
          .map((tr) => ({
            voce_computo_id: tr.querySelector('.av-voce').value,
            quantita_eseguita: tr.querySelector('.av-qta').value || 0,
            note: tr.querySelector('.av-note').value || null,
          }))
          .filter((a) => a.voce_computo_id);
        try {
          if (id) await api('PUT', `/api/giornaliere/${id}`, dati);
          else await api('POST', `/api/cantieri/${stato.cantiereId}/giornaliere`, dati);
          chiudiModale();
          await renderGiornale();
          toast('Giornaliera salvata.', 'ok');
        } catch (e) { toast(e.message, 'errore'); }
      },
    },
  ]);

  // Gestione righe avanzamento (aggiunta/rimozione) dopo il render.
  setTimeout(() => {
    const body = $('#avanz-body');
    $('#btn-add-avanz')?.addEventListener('click', () => {
      body.insertAdjacentHTML('beforeend', rigaAvanzamento());
    });
    body.addEventListener('click', (ev) => {
      if (ev.target.classList.contains('av-del')) ev.target.closest('tr').remove();
    });
  }, 0);
}

async function eliminaGiornaliera(id) {
  if (!confirm('Eliminare questa giornaliera?')) return;
  try {
    await api('DELETE', `/api/giornaliere/${id}`);
    await renderGiornale();
    toast('Giornaliera eliminata.', 'ok');
  } catch (e) { toast(e.message, 'errore'); }
}

// --- Contabilità / SAL ------------------------------------------------------

async function renderContabilita() {
  if (!stato.cantiereId) return;
  const data = $('#sal-data').value;
  const q = data ? `?alla_data=${data}` : '';
  const { voci, sal } = await api('GET', `/api/cantieri/${stato.cantiereId}/contabilita${q}`);

  const pAvanz = sal.percentuale_avanzamento;
  $('#sal-riepilogo').innerHTML = `
    <div class="sal-card"><div class="label">Importo eseguito${data ? ' alla data' : ''}</div><div class="valore">${euro(sal.importo_eseguito)}</div></div>
    <div class="sal-card"><div class="label">${sal.importo_contrattuale ? 'Importo contrattuale' : 'Importo di progetto'}</div><div class="valore">${euro(sal.base_calcolo)}</div></div>
    <div class="sal-card"><div class="label">Residuo</div><div class="valore">${euro(sal.residuo)}</div></div>
    <div class="sal-card evidenza"><div class="label">Avanzamento (SAL)</div><div class="valore">${perc(pAvanz)}</div>
      <div class="barra"><span style="width:${Math.min(100, Math.max(0, pAvanz || 0))}%"></span></div></div>`;

  const tb = $('#tabella-contabilita tbody');
  if (voci.length === 0) {
    tb.innerHTML = '<tr><td colspan="8" class="vuoto">Nessuna voce di computo.</td></tr>';
    $('#tabella-contabilita tfoot').innerHTML = '';
    return;
  }
  tb.innerHTML = voci.map((v) => `
    <tr>
      <td>${escapeHtml(v.codice ?? '')}</td>
      <td>${escapeHtml(v.descrizione)}</td>
      <td>${escapeHtml(v.unita_misura ?? '')}</td>
      <td class="num">${numIt(v.quantita_progetto, 3)}</td>
      <td class="num">${numIt(v.quantita_eseguita, 3)}</td>
      <td class="num">${perc(v.percentuale)}</td>
      <td class="num">${euro(v.importo_eseguito)}</td>
      <td class="num">${euro(v.residuo)}</td>
    </tr>`).join('');
  $('#tabella-contabilita tfoot').innerHTML = `
    <tr><td colspan="6">TOTALE</td>
      <td class="num">${euro(sal.importo_eseguito)}</td>
      <td class="num">${euro(sal.importo_progetto - sal.importo_eseguito)}</td></tr>`;
}

// --- Navigazione tab --------------------------------------------------------

let tabCorrente = 'schede';

function aggiornaVisibilita() {
  const haCantiere = !!stato.cantiereId;
  $('#no-cantiere').classList.toggle('hidden', haCantiere);
  $$('.tab-panel').forEach((p) => p.classList.add('hidden'));
  if (haCantiere) $(`#tab-${tabCorrente}`).classList.remove('hidden');
  $('#tabs').classList.toggle('hidden', !haCantiere);
}

async function ricaricaTabCorrente() {
  if (!stato.cantiereId) return;
  if (tabCorrente === 'schede') await renderSchede();
  else if (tabCorrente === 'giornale') await renderGiornale();
  else if (tabCorrente === 'contabilita') await renderContabilita();
}

function attivaTab(nome) {
  tabCorrente = nome;
  $$('.tab').forEach((t) => t.classList.toggle('active', t.dataset.tab === nome));
  aggiornaVisibilita();
  ricaricaTabCorrente();
}

// --- Inizializzazione -------------------------------------------------------

function init() {
  $('#cantiere-select').onchange = (e) => {
    stato.cantiereId = Number(e.target.value) || null;
    ricaricaTabCorrente();
  };
  $('#btn-nuovo-cantiere').onclick = () => modaleCantiere(null);
  $('#btn-modifica-cantiere').onclick = () => {
    const c = cantiereCorrente();
    if (c) modaleCantiere(c); else toast('Nessun cantiere selezionato.', 'errore');
  };
  $$('.tab').forEach((t) => t.onclick = () => attivaTab(t.dataset.tab));

  $('#btn-nuova-voce').onclick = () => modaleVoce(null);
  $('#btn-import-csv').onclick = modaleImport;
  $('#btn-nuova-giorn').onclick = () => modaleGiornaliera(null);
  $('#btn-filtra').onclick = renderGiornale;
  $('#btn-calcola-sal').onclick = renderContabilita;

  $('#modale-chiudi').onclick = chiudiModale;
  $('#modale').onclick = (e) => { if (e.target.id === 'modale') chiudiModale(); };

  caricaCantieri().then(ricaricaTabCorrente).catch((e) => toast(e.message, 'errore'));
}

document.addEventListener('DOMContentLoaded', init);
