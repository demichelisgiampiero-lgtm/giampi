const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, AlignmentType, HeadingLevel, BorderStyle, ShadingType,
  VerticalAlign, LevelFormat, convertMillimetersToTwip,
} = require("docx");
const fs = require("fs");

/* ---------- misure ---------- */
const CONTENT = 9638;                       // A4 (11906) - margini 2x1134
const C = [800, 3130, 4508, 1200];          // colonne tabella richieste
const H = [2900, 6738];                     // colonne tabella dati commessa

/* ---------- palette ---------- */
const INK = "1A1A1A";
const GREY = "5C5C5C";
const RULE = "B8B8B8";
const HEADFILL = "1F3864";
const SOFT = "EDF0F6";
const ZEBRA = "F7F8FA";

/* ---------- helper ---------- */
const P = (text, opts = {}) => new Paragraph({
  alignment: opts.align,
  spacing: { before: opts.before ?? 0, after: opts.after ?? 120, line: 276 },
  indent: opts.indent,
  border: opts.border,
  children: [new TextRun({
    text, bold: opts.bold, italics: opts.italics, size: opts.size ?? 20,
    color: opts.color ?? INK, font: "Calibri", allCaps: opts.caps,
  })],
});

const Prich = (runs, opts = {}) => new Paragraph({
  alignment: opts.align,
  spacing: { before: opts.before ?? 0, after: opts.after ?? 120, line: 276 },
  children: runs.map(r => new TextRun({
    text: r.t, bold: r.b, italics: r.i, size: r.s ?? 20,
    color: r.c ?? INK, font: "Calibri",
  })),
});

const H1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 360, after: 160 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: HEADFILL, space: 4 } },
  children: [new TextRun({ text, bold: true, size: 24, color: HEADFILL, font: "Calibri" })],
});

const cell = (children, { w, fill, span, valign } = {}) => new TableCell({
  width: { size: w, type: WidthType.DXA },
  columnSpan: span,
  verticalAlign: valign ?? VerticalAlign.TOP,
  shading: fill ? { type: ShadingType.CLEAR, fill, color: "auto" } : undefined,
  margins: { top: 90, bottom: 90, left: 110, right: 110 },
  children,
});

const txt = (t, o = {}) => [new Paragraph({
  alignment: o.align,
  spacing: { before: 0, after: 0, line: 260 },
  children: [new TextRun({
    text: t, bold: o.bold, italics: o.italics, size: o.size ?? 18,
    color: o.color ?? INK, font: "Calibri",
  })],
})];

const tblBorders = {
  top:    { style: BorderStyle.SINGLE, size: 4, color: RULE },
  bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE },
  left:   { style: BorderStyle.SINGLE, size: 4, color: RULE },
  right:  { style: BorderStyle.SINGLE, size: 4, color: RULE },
  insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: RULE },
  insideVertical:   { style: BorderStyle.SINGLE, size: 2, color: RULE },
};

/* Tabella richieste: [codice, oggetto, finalità, priorità] */
function tabellaRichieste(rows) {
  const head = new TableRow({
    tableHeader: true,
    children: [
      cell(txt("N.", { bold: true, color: "FFFFFF", align: AlignmentType.CENTER }), { w: C[0], fill: HEADFILL }),
      cell(txt("Documento / dato richiesto", { bold: true, color: "FFFFFF" }), { w: C[1], fill: HEADFILL }),
      cell(txt("Finalità e rilievo collegato", { bold: true, color: "FFFFFF" }), { w: C[2], fill: HEADFILL }),
      cell(txt("Prior.", { bold: true, color: "FFFFFF", align: AlignmentType.CENTER }), { w: C[3], fill: HEADFILL }),
    ],
  });
  const body = rows.map((r, i) => new TableRow({
    children: [
      cell(txt(r[0], { bold: true, align: AlignmentType.CENTER }), { w: C[0], fill: i % 2 ? ZEBRA : undefined }),
      cell(txt(r[1], { bold: true }), { w: C[1], fill: i % 2 ? ZEBRA : undefined }),
      cell(txt(r[2], { color: GREY }), { w: C[2], fill: i % 2 ? ZEBRA : undefined }),
      cell(txt(r[3], { bold: true, align: AlignmentType.CENTER }), { w: C[3], fill: i % 2 ? ZEBRA : undefined }),
    ],
  }));
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: C,
    borders: tblBorders,
    rows: [head, ...body],
  });
}

/* Box a piena larghezza */
function box(paragraphs, fill = SOFT) {
  return new Table({
    width: { size: CONTENT, type: WidthType.DXA },
    columnWidths: [CONTENT],
    borders: {
      top:    { style: BorderStyle.SINGLE, size: 4, color: HEADFILL },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: HEADFILL },
      left:   { style: BorderStyle.SINGLE, size: 18, color: HEADFILL },
      right:  { style: BorderStyle.SINGLE, size: 4, color: HEADFILL },
      insideHorizontal: { style: BorderStyle.NONE, size: 0, color: "auto" },
      insideVertical:   { style: BorderStyle.NONE, size: 0, color: "auto" },
    },
    rows: [new TableRow({ children: [cell(paragraphs, { w: CONTENT, fill })] })],
  });
}

/* ---------- dati commessa ---------- */
const datiCommessa = [
  ["Oggetto lavori", "Lavori di miglioramento sismico ed energetico, logistico-funzionale ed architettonico della sede del Comando Provinciale VV.F. di Pisa, Via Matteotti n. 1"],
  ["Contratto", "Rep. n. 7/23 del 16/05/2023"],
  ["Perizia", "n. 1071"],
  ["CUP / CIG", "D56J22000140001  /  9616784535"],
  ["Impresa appaltatrice", "SUPINO GROUP S.R.L. – Via G.B. Marino 7, Napoli – P.I. 06509991219"],
  ["Direzione Lavori", "3ing S.r.l. – Ing. Jacopo Pellegrino"],
  ["RUP", "Arch. Michele Mariani"],
  ["Procedimento di riferimento", "Risoluzione contrattuale per grave inadempimento ex art. 108, co. 3, D.Lgs. 50/2016"],
  ["Data della richiesta", "09 settembre 2026"],
  ["Ns. riferimento", "VER-VVF-PI/2026/RID-001"],
];

const tabellaDati = new Table({
  width: { size: CONTENT, type: WidthType.DXA },
  columnWidths: H,
  borders: tblBorders,
  rows: datiCommessa.map(([k, v], i) => new TableRow({
    children: [
      cell(txt(k, { bold: true }), { w: H[0], fill: i % 2 ? ZEBRA : SOFT }),
      cell(txt(v), { w: H[1], fill: i % 2 ? ZEBRA : undefined }),
    ],
  })),
});

/* ---------- contenuti ---------- */
const sez1 = [
  ["1.1", "Ordine di Servizio n. 19 – copia integrale, con data di emissione e stato di adempimento",
   "L'OdS n. 19 è citato come fonte della contestazione in due righe della Tabella riepilogativa e al § 4.1 della Relazione, ma la riga corrispondente della cronistoria è vuota. Senza il documento la contestazione su strutture metalliche sulla guaina e inghisaggi resta priva di atto presupposto.", "P1"],
  ["1.2", "Copia integrale degli OdS nn. 1-20 con ricevute di trasmissione (PEC) e date di notifica",
   "La cronistoria riporta solo l'oggetto. Per provare l'inadempimento occorre dimostrare che ciascun ordine è stato ricevuto e che il termine assegnato è scaduto.", "P1"],
  ["1.3", "Data esatta di emissione dell'OdS n. 4",
   "In cronistoria è indicato solo «Set. 2025». Il § 6 della Relazione calcola le penali «dalla data di ciascun inadempimento»: senza data non è quantificabile.", "P1"],
  ["1.4", "Chiarimento sulla successione cronologica degli OdS nn. 13, 14 e 15",
   "Le date in cronistoria non sono progressive (n. 12 del 03/02/2026, n. 13 del 04/03/2026, n. 14 del 11/02/2026, n. 15 del 04/02/2026). L'anomalia è utilizzabile dalla controparte per contestare la formazione del registro.", "P1"],
  ["1.5", "Riscontri, controdeduzioni e riserve dell'Impresa a ciascun OdS",
   "Necessari per qualificare correttamente ogni voce come «inadempiuta», «parzialmente adempiuta» o «contestata», e per dare conto del contraddittorio già svolto.", "P1"],
  ["1.6", "Verbali di sopralluogo (Allegato E della Relazione)",
   "Citati fra gli allegati ma non prodotti.", "P1"],
  ["1.7", "Messa in mora del 05/05/2026 e comunicazioni precedenti (Allegato C)",
   "Citata come atto presupposto in tutti e tre i documenti; non disponibile agli atti esaminati.", "P1"],
  ["1.8", "Contestazione della contabilità VMV del 05/07/2026 (Allegato D)",
   "Fonda l'addebito di € 56.752,03 richiamato al § 7 della Relazione.", "P2"],
  ["1.9", "Comunicazione del Comando VV.F. di Pisa del 27/09/2025 e successive (Allegato H)",
   "Documenta il pregiudizio alla funzionalità del presidio, elemento centrale della gravità dell'inadempimento.", "P1"],
  ["1.10", "13 bolle DDT dei materiali con annotazioni della DL (Allegato F)",
   "Sostengono l'addebito di impiego sistematico di materiali non accettati dalla DL.", "P2"],
  ["1.11", "Quadro comparativo contabilità DL / Supino Group / VMV (Allegato G)",
   "Necessario per la stima dei lavori regolarmente eseguiti (v. punto 2.6).", "P1"],
];

const sez2 = [
  ["2.1", "Contratto Rep. n. 7/23 del 16/05/2023 e Capitolato Speciale d'Appalto integrali",
   "Nessuno dei documenti esaminati riporta il contenuto contrattuale. Serve per verificare quali obblighi si assumono violati.", "P1"],
  ["2.2", "Importo contrattuale netto, oneri della sicurezza non soggetti a ribasso, importo della perizia n. 1071",
   "Dati assenti dall'intero corpus. Servono a dimensionare la gravità dell'inadempimento e il tetto delle penali.", "P1"],
  ["2.3", "Clausola del CSA in materia di penali: misura giornaliera, tetto massimo, presupposti di applicazione",
   "Il § 6 della Relazione applica le penali ex art. 113-bis D.Lgs. 50/2016 «dalla data di ciascun inadempimento» agli OdS. L'art. 113-bis riguarda il ritardo nell'esecuzione: senza una clausola che preveda penali per singolo ordine di servizio, l'impostazione è contestabile.", "P1"],
  ["2.4", "Verbale di consegna dei lavori, termine di ultimazione, proroghe concesse, verbali di sospensione e ripresa",
   "L'intero corpus non contiene alcun dato temporale contrattuale. In una risoluzione per grave inadempimento il ritardo maturato è normalmente l'elemento portante e oggi manca del tutto.", "P1"],
  ["2.5", "Cronoprogramma contrattuale e ultimo aggiornamento approvato",
   "Serve a dimostrare lo scostamento fra avanzamento previsto ed effettivo.", "P1"],
  ["2.6", "SAL emessi, certificati di pagamento, importo contabilizzato e liquidato ad oggi",
   "L'art. 108, co. 3, D.Lgs. 50/2016 impone che la relazione indichi la stima dei lavori eseguiti regolarmente. Il § 6 rinvia a un documento separato «in corso»: finché non è prodotta, la relazione è incompleta rispetto alla norma che invoca.", "P1"],
  ["2.7", "Estratti del Progetto Esecutivo (tavole, computo metrico, elenco prezzi) limitatamente a: linea vita copertura Ed. 6; punti luce e apparecchi illuminanti con grado IP richiesto; colore delle facciate e fondo fissativo; porte interne; impianto gas e caldaia preesistente",
   "Sono esattamente gli addebiti che oggi non trovano riscontro né in un OdS né in una fotografia. Senza l'estratto di progetto non sono dimostrabili.", "P1"],
  ["2.8", "Elaborato che identifica la numerazione degli edifici (Ed. 1 … Ed. 6) con destinazione dei locali",
   "I tre documenti si contraddicono fra Ed. 1 ed Ed. 6 (v. § 6.2 della presente richiesta). Serve la chiave di lettura ufficiale.", "P1"],
  ["2.9", "Polizza della cauzione definitiva: massimale, scadenza, garante",
   "Il § 8.4 della Relazione ne propone l'escussione integrale.", "P2"],
  ["2.10", "Autorizzazione al subappalto a favore di VMV Costruzioni e relativo contratto",
   "La Relazione qualifica VMV come subappaltatrice; l'OdS n. 20 la tratta come impresa autonoma. Va chiarito il rapporto giuridico.", "P2"],
  ["2.11", "Registro di contabilità: riserve iscritte dall'Impresa ai sensi dell'art. 205 D.Lgs. 50/2016",
   "Eventuali riserve già iscritte cambiano la strategia difensiva e vanno conosciute prima di trasmettere la relazione al RUP.", "P1"],
];

const sez3 = [
  ["3.1", "Nominativo del Coordinatore per la Sicurezza in fase di Esecuzione e copia integrale dei suoi atti: verbali di visita, contestazioni, sospensioni, comunicazioni ex art. 92 D.Lgs. 81/2008",
   "Ponteggio non conforme, bombole di gas abbandonate, cavi elettrici scoperti e mancata installazione della linea vita sono materia del CSE. Nel corpus non compare alcun atto del Coordinatore: è la lacuna più evidente sul fronte sicurezza.", "P1"],
  ["3.2", "PSC e POS di Supino Group e VMV, con tutti gli aggiornamenti",
   "L'OdS n. 10 contesta il POS: serve la versione contestata e quella eventualmente trasmessa in riscontro.", "P2"],
  ["3.3", "Libretto del ponteggio, PiMUS e progetto del ponteggio ove fuori schema tipo",
   "L'OdS n. 20 afferma la non conformità «al libretto» e nega il corrispettivo economico: entrambe le affermazioni vanno documentate.", "P1"],
  ["3.4", "Eventuali segnalazioni o verbali di ASL, Ispettorato Territoriale del Lavoro o Vigili del Fuoco",
   "Un accertamento di un organo di vigilanza è la prova più solida delle violazioni ex D.Lgs. 81/2008 contestate.", "P2"],
  ["3.5", "Notifica preliminare e successivi aggiornamenti",
   "Serve a identificare le imprese formalmente presenti in cantiere nei periodi contestati.", "P3"],
];

const sez4 = [
  ["4.1", "Atto formale con cui gli ambienti sono stati dichiarati non agibili: autorità emanante, data, protocollo, estensione dell'inagibilità",
   "I documenti usano la forma passiva («ambienti dichiarati temporaneamente non agibili») senza indicare da chi. L'inagibilità è dichiarata dall'autorità competente, non dalla Direzione Lavori: senza l'atto, l'affermazione più grave dell'intero fascicolo resta non provata.", "P1"],
  ["4.2", "Comunicazioni del Comando VV.F. sulla sospensione delle attività",
   "L'OdS n. 20 parla di «sospensione di tutte le attività del Comando», la Relazione di «inagibilità di un'aula». Le due affermazioni non sono compatibili e va stabilito quale è documentata.", "P1"],
  ["4.3", "Eventuali analisi, campionamenti o relazioni tecniche sulle muffe e sull'umidità",
   "Trasformano un rilievo visivo in un accertamento tecnico, e sostengono la voce di danno per la bonifica.", "P2"],
];

const sez5 = [
  ["5.1", "File originali delle fotografie con metadati EXIF integri (data e ora di scatto)",
   "Le fotografie prodotte non recano data di scatto né identificazione del locale. È la principale debolezza del corredo probatorio in vista di un contenzioso.", "P1"],
  ["5.2", "Chiarimento sulla Foto 3 della Relazione Fotografica",
   "Le didascalie passano da «Foto 1-2» a «Foto 4-5-6»: la Foto 3 non esiste. Di conseguenza le fotografie effettivamente presenti sono 69, mentre la Relazione ne dichiara 70 in cinque punti diversi.", "P1"],
  ["5.3", "Didascalie delle due immagini prive di numerazione a pag. 19 della Relazione Fotografica",
   "Due fotografie sono prive di didascalia e di numero: allo stato sono inutilizzabili come prova.", "P1"],
  ["5.4", "Le due immagini mancanti del gruppo «Foto 62-63-64-65»",
   "La didascalia annuncia quattro fotografie ma le immagini presenti sono due. Il § 4.5 e la tabella riepilogativa citano «Foto 62-65» a sostegno dell'addebito sull'intonaco armato GFRP ex art. 1669 c.c.", "P1"],
  ["5.5", "Fotografie del sopralluogo dell'08/09/2026 in alta risoluzione",
   "Le immagini allegate all'OdS n. 20 e alla lettera misurano 212×379 e 259×345 pixel: a stampa sono al limite dell'inutilizzabile per documentare muffe e dettagli esecutivi.", "P1"],
  ["5.6", "Autore e data della Relazione Fotografica, da riportare in frontespizio, e planimetria con i punti di ripresa",
   "Il documento non reca data né firma; nei metadati del file risultano l'autore «Fabrizio Mariani» e la data di creazione 05/05/2026, mentre la Relazione la attribuisce a 3ing S.r.l.", "P1"],
];

const sez6 = [
  ["6.1", "Di quale elemento costruttivo si tratta con il termine «brindosbarra»",
   "Il termine compare nell'OdS n. 20 (§ 2.4) e nella lettera (§ e) ma non è riconducibile ad alcun elemento tecnico identificabile. Una prescrizione formulata su un elemento non identificabile è ineseguibile e quindi inopponibile all'Impresa.", "P1"],
  ["6.2", "Come si documenta il nesso causale fra la copertura dell'Ed. 6 e le muffe rilevate al piano terra dell'Ed. 1",
   "Le fotografie sono didascalizzate «Ed 1 Piano Terra», mentre la Relazione (§§ 4.1 e 6) attribuisce la causa alla copertura dell'Ed. 6. Inoltre la Foto 6 descrive umidità «in posizione bassa di parete» attribuendola a infiltrazione dalla copertura: la collocazione bassa indica piuttosto risalita capillare o perdita impiantistica. È il primo punto che verrà attaccato.", "P1"],
  ["6.3", "Prescrizione corretta da associare alla non conformità 2.2 dell'OdS n. 20 (tubazione gas che attraversa muratura portante)",
   "La prescrizione attualmente riportata impone di «completare la chiusura delle partizioni con lastre di cartongesso, previa verifica di tenuta idraulica»: non ha alcuna attinenza con la non conformità contestata e appare riportata da un altro ordine di servizio.", "P1"],
  ["6.4", "Conteggio definitivo e concordato degli OdS emessi e di quelli inadempiuti",
   "Il corpus fornisce quattro dati diversi: Relazione § 3 (17 inadempiuti + 1 in ritardo + 2 adempiuti = 20 su 19 dichiarati); cronistoria (16 inadempiuti, 1 riga vuota); box riepilogativo (17 su 19); lettera al Comando (15 su 19).", "P1"],
  ["6.5", "Documentazione a supporto degli addebiti su linea vita, punti luce/grado IP e imbiancatura esterna",
   "Sono tre addebiti gravi — il primo classificato «CRITICA – SICUREZZA» — per i quali non risulta emesso alcun OdS né esiste documentazione fotografica. Il § 4.4 li dice «già contestati», ma la cronistoria non lo conferma.", "P1"],
  ["6.6", "Conferma sulle fotografie raccolte e non utilizzate",
   "Non sono richiamate in alcun documento le Foto 25-26 (macchia d'acqua e umidità da infiltrazione), 48 (guaina non protetta), 52, 58-61 (assenza di tassellatura, pertinente al capo «inghisaggi»), 30, 38, 39, 40, 57 e 66-67. Va deciso se valorizzarle.", "P2"],
];

/* ---------- documento ---------- */
const doc = new Document({
  creator: "Verifica documentale",
  title: "Richiesta di integrazione documentale – Comando VV.F. Pisa",
  description: "Elenco dei documenti e dei chiarimenti necessari al consolidamento del fascicolo di risoluzione contrattuale",
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 20, color: INK } },
      heading1: { run: { font: "Calibri", size: 24, bold: true, color: HEADFILL } },
    },
  },
  numbering: {
    config: [{
      reference: "bul",
      levels: [{
        level: 0, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 400, hanging: 220 } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: {
        margin: {
          top: convertMillimetersToTwip(22), bottom: convertMillimetersToTwip(20),
          left: convertMillimetersToTwip(20), right: convertMillimetersToTwip(20),
        },
      },
    },
    children: [
      /* frontespizio */
      P("RICHIESTA DI INTEGRAZIONE DOCUMENTALE", { bold: true, size: 30, align: AlignmentType.CENTER, after: 60, color: HEADFILL }),
      P("Documenti e chiarimenti necessari al consolidamento del fascicolo", { align: AlignmentType.CENTER, size: 21, color: GREY, after: 40 }),
      P("Procedimento di risoluzione contrattuale ex art. 108, co. 3, D.Lgs. 50/2016", { align: AlignmentType.CENTER, size: 21, color: GREY, italics: true, after: 320 }),

      box([
        ...txt("DESTINATARIO", { bold: true, size: 18, color: HEADFILL }),
        new Paragraph({ spacing: { before: 60, after: 0 }, children: [new TextRun({ text: "[ da completare — Direzione Lavori 3ing S.r.l., Ing. Jacopo Pellegrino ]", size: 20, bold: true, font: "Calibri" })] }),
        new Paragraph({ spacing: { before: 120, after: 0 }, children: [new TextRun({ text: "Per conoscenza: [ da completare ]", size: 18, color: GREY, font: "Calibri" })] }),
      ], "FFF4E5"),

      P("", { after: 240 }),
      tabellaDati,
      P("", { after: 300 }),

      /* premessa */
      H1("1.  PREMESSA E OGGETTO DELLA RICHIESTA"),
      Prich([
        { t: "È stata condotta la verifica di coerenza formale, documentale e procedurale sui seguenti atti: " },
        { t: "Relazione di grave inadempimento contrattuale e proposta di risoluzione", b: true },
        { t: " (09/09/2026), " },
        { t: "Ordine di Servizio n. 20", b: true },
        { t: " (09/09/2026), " },
        { t: "lettera di contestazione formale dello stato dei lavori", b: true },
        { t: " (09/09/2026) e " },
        { t: "Relazione Fotografica", b: true },
        { t: " (69 fotografie)." },
      ], { after: 160 }),
      P("La verifica ha accertato che il fascicolo, nella sua composizione attuale, non è ancora completo rispetto ai requisiti di contenuto posti dall'art. 108, co. 3, D.Lgs. 50/2016 e presenta incongruenze interne che sarebbero utilizzabili dall'Impresa in sede di controdeduzioni, davanti al giudice e in sede ANAC.", { after: 160 }),
      P("Con la presente si richiedono pertanto i documenti e i chiarimenti elencati nelle sezioni che seguono. Ciascuna voce riporta la finalità e il rilievo cui si collega, così da rendere immediatamente valutabile che cosa comporti la mancata acquisizione.", { after: 200 }),

      box([
        ...txt("LEGENDA DELLE PRIORITÀ", { bold: true, size: 18, color: HEADFILL }),
        new Paragraph({ spacing: { before: 100, after: 40 }, children: [
          new TextRun({ text: "P1  ", bold: true, size: 19, font: "Calibri" }),
          new TextRun({ text: "Bloccante. Da acquisire prima della trasmissione della relazione al RUP: in assenza, l'atto è impugnabile o l'addebito è indimostrabile.", size: 19, font: "Calibri" }),
        ]}),
        new Paragraph({ spacing: { before: 0, after: 40 }, children: [
          new TextRun({ text: "P2  ", bold: true, size: 19, font: "Calibri" }),
          new TextRun({ text: "Necessario per la quantificazione economica del danno e delle detrazioni.", size: 19, font: "Calibri" }),
        ]}),
        new Paragraph({ spacing: { before: 0, after: 0 }, children: [
          new TextRun({ text: "P3  ", bold: true, size: 19, font: "Calibri" }),
          new TextRun({ text: "Utile a rafforzare l'impianto probatorio, non indispensabile.", size: 19, font: "Calibri" }),
        ]}),
      ]),
      P("", { after: 200 }),

      /* sezioni */
      H1("2.  ATTI DELLA DIREZIONE LAVORI E CORRISPONDENZA"),
      P("Gli allegati da A a L elencati in calce alla Relazione non sono stati resi disponibili per la verifica. Si richiedono in copia integrale, con particolare urgenza per le voci seguenti.", { after: 160, color: GREY, italics: true }),
      tabellaRichieste(sez1),
      P("", { after: 240 }),

      H1("3.  DOCUMENTI CONTRATTUALI, CONTABILI E DI PROGETTO"),
      P("Nessuno dei documenti esaminati riporta i dati economici e temporali del contratto. È la lacuna che più incide sulla tenuta della proposta di risoluzione.", { after: 160, color: GREY, italics: true }),
      tabellaRichieste(sez2),
      P("", { after: 240 }),

      H1("4.  SICUREZZA E COORDINAMENTO"),
      P("Il fascicolo contesta ripetutamente violazioni del D.Lgs. 81/2008 senza che risulti agli atti alcun intervento del Coordinatore per la Sicurezza in fase di Esecuzione.", { after: 160, color: GREY, italics: true }),
      tabellaRichieste(sez3),
      P("", { after: 240 }),

      H1("5.  INAGIBILITÀ DEI LOCALI E STATO DEI LUOGHI"),
      tabellaRichieste(sez4),
      P("", { after: 240 }),

      H1("6.  CORREDO FOTOGRAFICO"),
      tabellaRichieste(sez5),
      P("", { after: 240 }),

      H1("7.  CHIARIMENTI RICHIESTI ALLA DIREZIONE LAVORI"),
      P("Le voci che seguono non richiedono la produzione di un documento ma una presa di posizione della DL, necessaria per correggere i testi prima dell'invio.", { after: 160, color: GREY, italics: true }),
      tabellaRichieste(sez6),
      P("", { after: 260 }),

      /* avvertenza */
      H1("8.  AVVERTENZA SUI TEMPI"),
      box([
        ...txt("Il fascicolo contiene una contraddizione che va sciolta prima di ogni altra cosa.", { bold: true, size: 20 }),
        new Paragraph({ spacing: { before: 140, after: 100 }, children: [new TextRun({
          text: "L'Ordine di Servizio n. 20, emesso il 09/09/2026, convoca il sopralluogo in contraddittorio per venerdì 18 settembre 2026; la lettera di pari data assegna 48 ore per il riscontro. La Relazione, anch'essa datata 09/09/2026, classifica però lo stesso OdS n. 20 come «Inadempiente – nessun riscontro» e propone la risoluzione del contratto.",
          size: 19, font: "Calibri" })] }),
        new Paragraph({ spacing: { before: 0, after: 0 }, children: [new TextRun({
          text: "Se i tre atti vengono trasmessi insieme, l'Impresa eccepirà che la risoluzione è stata proposta prima della scadenza del termine assegnato dalla Direzione Lavori stessa. La sequenza degli atti va quindi definita contestualmente alla raccolta della documentazione qui richiesta.",
          size: 19, bold: true, font: "Calibri" })] }),
      ], "FDECEC"),
      P("", { after: 260 }),

      H1("9.  MODALITÀ E TERMINE DI RISCONTRO"),
      new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 90, line: 276 }, children: [new TextRun({ text: "Si richiede la trasmissione in formato digitale, mantenendo per ogni file la denominazione e la numerazione utilizzate nella presente richiesta (es. «1.1 – OdS 19.pdf»).", size: 20, font: "Calibri" })] }),
      new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 90, line: 276 }, children: [new TextRun({ text: "Per le fotografie si richiedono i file originali non ricompressi, con metadati EXIF integri.", size: 20, font: "Calibri" })] }),
      new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 90, line: 276 }, children: [new TextRun({ text: "Le voci contrassegnate P1 sono richieste con precedenza: senza di esse la revisione dei documenti non può essere completata.", size: 20, font: "Calibri" })] }),
      new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 90, line: 276 }, children: [new TextRun({ text: "Ove un documento non esista, si richiede di darne atto espressamente: l'assenza è essa stessa un dato rilevante per la strategia da adottare.", size: 20, font: "Calibri" })] }),
      new Paragraph({ numbering: { reference: "bul", level: 0 }, spacing: { after: 240, line: 276 }, children: [new TextRun({ text: "Termine richiesto per il riscontro: [ da completare ].", size: 20, bold: true, font: "Calibri" })] }),

      /* firma */
      P("", { after: 400 }),
      P("Luogo e data  ____________________________", { after: 400, color: GREY }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 0 },
        children: [new TextRun({ text: "_________________________________", size: 20, font: "Calibri" })],
      }),
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 0 },
        children: [new TextRun({ text: "[ qualifica e nominativo del richiedente ]", size: 19, color: GREY, font: "Calibri" })],
      }),
    ],
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(process.argv[2] || "Richiesta_integrazione_documentale.docx", b);
  console.log("OK");
});
