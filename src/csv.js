// Parser CSV minimale pensato per i file di computo esportati da Excel italiano.
// Gestisce: delimitatore ';' o ',', campi tra virgolette, numeri con la virgola
// decimale (es. "1.234,56"). Nessuna dipendenza esterna.

/** Converte un numero in formato italiano/inglese in Number. */
export function parseNumero(value) {
  if (value === null || value === undefined) return 0;
  let s = String(value).trim();
  if (s === '') return 0;
  // Rimuove eventuale simbolo di valuta e spazi.
  s = s.replace(/[€\s]/g, '');
  const hasComma = s.includes(',');
  const hasDot = s.includes('.');
  if (hasComma && hasDot) {
    // Formato italiano "1.234,56": il punto è separatore migliaia.
    s = s.replace(/\./g, '').replace(',', '.');
  } else if (hasComma) {
    // Solo virgola → decimale italiano.
    s = s.replace(',', '.');
  }
  const n = Number(s);
  return Number.isFinite(n) ? n : 0;
}

/** Individua il delimitatore più probabile guardando la prima riga. */
function rilevaDelimitatore(testo) {
  const primaRiga = testo.split(/\r?\n/, 1)[0] || '';
  const puntiVirgola = (primaRiga.match(/;/g) || []).length;
  const virgole = (primaRiga.match(/,/g) || []).length;
  return puntiVirgola >= virgole ? ';' : ',';
}

/** Suddivide il CSV in righe di celle, rispettando le virgolette. */
export function parseCSV(testo) {
  const delimitatore = rilevaDelimitatore(testo);
  const righe = [];
  let cella = '';
  let riga = [];
  let dentroVirgolette = false;

  for (let i = 0; i < testo.length; i++) {
    const c = testo[i];
    if (dentroVirgolette) {
      if (c === '"') {
        if (testo[i + 1] === '"') { cella += '"'; i++; } // virgoletta escapata
        else dentroVirgolette = false;
      } else {
        cella += c;
      }
    } else if (c === '"') {
      dentroVirgolette = true;
    } else if (c === delimitatore) {
      riga.push(cella); cella = '';
    } else if (c === '\n') {
      riga.push(cella); righe.push(riga); cella = ''; riga = [];
    } else if (c === '\r') {
      // ignorato: gestito insieme a \n
    } else {
      cella += c;
    }
  }
  // Ultima cella/riga se il file non termina con newline.
  if (cella !== '' || riga.length > 0) { riga.push(cella); righe.push(riga); }

  return righe.filter((r) => r.some((cell) => String(cell).trim() !== ''));
}

// Sinonimi di intestazione accettati per ciascun campo della voce di computo.
const COLONNE = {
  codice: ['codice', 'cod', 'art', 'articolo', 'n.', 'num', 'numero'],
  descrizione: ['descrizione', 'descr', 'lavorazione', 'designazione', 'oggetto'],
  categoria: ['categoria', 'cat', 'capitolo', 'gruppo'],
  unita_misura: ['unita_misura', 'unita', 'unità', 'um', 'u.m.', 'udm', 'misura'],
  quantita_progetto: ['quantita_progetto', 'quantita', 'quantità', 'qta', 'q.tà', 'qty'],
  prezzo_unitario: ['prezzo_unitario', 'prezzo', 'prezzo unit.', 'pu', 'p.u.', 'importo unitario'],
};

function normalizza(s) {
  return String(s).trim().toLowerCase().replace(/\s+/g, ' ');
}

/**
 * Trasforma un CSV di computo in un array di voci pronte per il DB.
 * La prima riga è considerata intestazione. Restituisce { voci, errori }.
 */
export function parseVociComputo(testo) {
  const righe = parseCSV(testo);
  if (righe.length === 0) return { voci: [], errori: ['File vuoto.'] };

  const intestazione = righe[0].map(normalizza);
  const mappa = {};
  for (const [campo, sinonimi] of Object.entries(COLONNE)) {
    mappa[campo] = intestazione.findIndex((h) => sinonimi.includes(h));
  }

  const errori = [];
  if (mappa.descrizione === -1) {
    errori.push("Colonna 'descrizione' non trovata nell'intestazione.");
    return { voci: [], errori };
  }

  const voci = [];
  for (let i = 1; i < righe.length; i++) {
    const r = righe[i];
    const get = (campo) => (mappa[campo] >= 0 ? (r[mappa[campo]] ?? '').trim() : '');
    const descrizione = get('descrizione');
    if (descrizione === '') {
      errori.push(`Riga ${i + 1}: descrizione mancante, saltata.`);
      continue;
    }
    voci.push({
      codice: get('codice') || null,
      descrizione,
      categoria: get('categoria') || null,
      unita_misura: get('unita_misura') || null,
      quantita_progetto: parseNumero(get('quantita_progetto')),
      prezzo_unitario: parseNumero(get('prezzo_unitario')),
    });
  }
  return { voci, errori };
}
