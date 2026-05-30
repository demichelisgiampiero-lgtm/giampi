// Smoke test dell'API: copre cantieri, voci (manuali + import CSV),
// giornaliere con avanzamenti e calcolo della contabilità/SAL.
import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

// Database temporaneo isolato per i test.
const tmp = mkdtempSync(join(tmpdir(), 'giornale-test-'));
process.env.DB_PATH = join(tmp, 'test.db');

const { default: app } = await import('../src/server.js');
const { chiudiDb } = await import('../src/db.js');
let server, base;

before(async () => {
  await new Promise((r) => { server = app.listen(0, r); });
  base = `http://localhost:${server.address().port}`;
});

after(() => {
  server.close();
  // Chiude il database prima di rimuovere la cartella: su Windows un file
  // con un handle ancora aperto non è eliminabile (EPERM).
  chiudiDb();
  rmSync(tmp, { recursive: true, force: true, maxRetries: 3, retryDelay: 100 });
});

const j = async (metodo, url, corpo) => {
  const opts = { method: metodo, headers: {} };
  if (corpo !== undefined) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(corpo);
  }
  const r = await fetch(base + url, opts);
  const dati = r.status === 204 ? null : await r.json();
  return { status: r.status, dati };
};

test('flusso completo CME → giornale → SAL', async () => {
  // 1) Cantiere
  const c = await j('POST', '/api/cantieri', {
    nome: 'Scuola Primaria', codice_commessa: 'A-01',
    importo_contrattuale: 100000,
  });
  assert.equal(c.status, 201);
  const cid = c.dati.id;

  // 2) Voce manuale
  const v1 = await j('POST', `/api/cantieri/${cid}/voci`, {
    codice: '01', descrizione: 'Scavo', unita_misura: 'm3',
    quantita_progetto: 100, prezzo_unitario: 10,
  });
  assert.equal(v1.status, 201);

  // 3) Import CSV (formato italiano: ; e virgola decimale)
  const csv = 'codice;descrizione;um;quantità;prezzo\n02;Calcestruzzo;m3;50;120,50\n';
  const imp = await j('POST', `/api/cantieri/${cid}/voci/import`, { csv });
  assert.equal(imp.status, 201);
  assert.equal(imp.dati.importate, 1);

  const voci = (await j('GET', `/api/cantieri/${cid}/voci`)).dati;
  assert.equal(voci.length, 2);
  const calcestruzzo = voci.find((v) => v.codice === '02');
  assert.equal(calcestruzzo.prezzo_unitario, 120.5);

  // 4) Giornaliera con avanzamenti
  const g = await j('POST', `/api/cantieri/${cid}/giornaliere`, {
    data: '2026-05-10', meteo: 'sereno', maestranze_numero: 4,
    avanzamenti: [
      { voce_computo_id: v1.dati.id, quantita_eseguita: 40 },
      { voce_computo_id: calcestruzzo.id, quantita_eseguita: 10 },
    ],
  });
  assert.equal(g.status, 201);
  assert.equal(g.dati.avanzamenti.length, 2);

  // 5) Contabilità / SAL: 40*10 + 10*120,50 = 400 + 1205 = 1605
  const cont = (await j('GET', `/api/cantieri/${cid}/contabilita`)).dati;
  assert.equal(cont.sal.importo_eseguito, 1605);
  assert.equal(cont.sal.base_calcolo, 100000);
  assert.ok(Math.abs(cont.sal.percentuale_avanzamento - 1.605) < 1e-9);

  // 6) SAL con filtro data anteriore: nessun avanzamento conteggiato
  const prima = (await j('GET', `/api/cantieri/${cid}/contabilita?alla_data=2026-05-01`)).dati;
  assert.equal(prima.sal.importo_eseguito, 0);
});

test('validazioni di base', async () => {
  assert.equal((await j('POST', '/api/cantieri', {})).status, 400);
  const c = await j('POST', '/api/cantieri', { nome: 'X' });
  assert.equal((await j('POST', `/api/cantieri/${c.dati.id}/voci`, {})).status, 400);
  assert.equal((await j('POST', `/api/cantieri/${c.dati.id}/giornaliere`, {})).status, 400);
  assert.equal((await j('GET', '/api/cantieri/999999')).status, 404);
});
