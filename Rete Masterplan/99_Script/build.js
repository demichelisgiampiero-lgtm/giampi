const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, PageNumber, Footer, Header, TableOfContents, PageBreak,
  LevelFormat, convertMillimetersToTwip, TabStopType, VerticalAlign
} = require('docx');
const fs = require('fs');

const NAVY = '1A3A5C';
const ACCENT = '8A6D3B';
const GREY = '5A6672';
const LIGHT = 'EEF2F6';
const BAND = 'DCE4EC';
const TW = 9638; // usable width DXA (A4 - 2cm margins)

const F = 'Calibri';

// ---------- helpers ----------
const P = (text, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after === undefined ? 120 : o.after, before: o.before || 0, line: o.line || 276 },
  indent: o.indent,
  border: o.border,
  shading: o.shading,
  children: [new TextRun({ text, font: F, size: o.size || 21, color: o.color || '222222', bold: o.bold, italics: o.italics })]
});

// rich paragraph from array of {t, b, i, c}
const RP = (runs, o = {}) => new Paragraph({
  alignment: o.align || AlignmentType.JUSTIFIED,
  spacing: { after: o.after === undefined ? 120 : o.after, before: o.before || 0, line: o.line || 276 },
  indent: o.indent,
  border: o.border,
  shading: o.shading,
  children: runs.map(r => new TextRun({
    text: r.t, font: F, size: r.size || o.size || 21,
    color: r.c || o.color || '222222', bold: r.b, italics: r.i
  }))
});

const H1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 380, after: 180 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: NAVY, space: 6 } },
  children: [new TextRun({ text, font: F, size: 30, bold: true, color: NAVY })]
});

const H2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 300, after: 130 },
  children: [new TextRun({ text, font: F, size: 24, bold: true, color: NAVY })]
});

const H3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  spacing: { before: 220, after: 100 },
  children: [new TextRun({ text, font: F, size: 21, bold: true, color: ACCENT })]
});

const BUL = (text, o = {}) => new Paragraph({
  numbering: { reference: 'bullets', level: 0 },
  spacing: { after: o.after === undefined ? 80 : o.after, line: 276 },
  alignment: AlignmentType.JUSTIFIED,
  children: [new TextRun({ text, font: F, size: 21, color: '222222' })]
});

const BULR = (runs, o = {}) => new Paragraph({
  numbering: { reference: 'bullets', level: 0 },
  spacing: { after: o.after === undefined ? 80 : o.after, line: 276 },
  alignment: AlignmentType.JUSTIFIED,
  children: runs.map(r => new TextRun({ text: r.t, font: F, size: 21, color: r.c || '222222', bold: r.b, italics: r.i }))
});

const NUMP = (runs, o = {}) => new Paragraph({
  numbering: { reference: 'numbers', level: 0 },
  spacing: { after: o.after === undefined ? 110 : o.after, line: 276 },
  alignment: AlignmentType.JUSTIFIED,
  children: runs.map(r => new TextRun({ text: r.t, font: F, size: 21, color: r.c || '222222', bold: r.b, italics: r.i }))
});

// table cell
const TC = (content, w, o = {}) => new TableCell({
  width: { size: w, type: WidthType.DXA },
  shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: 'auto' } : undefined,
  margins: { top: 70, bottom: 70, left: 100, right: 100 },
  verticalAlign: VerticalAlign.CENTER,
  children: Array.isArray(content) ? content : [new Paragraph({
    alignment: o.align || AlignmentType.LEFT,
    spacing: { after: 0, line: 250 },
    children: [new TextRun({
      text: String(content), font: F, size: o.size || 18,
      bold: o.bold, color: o.color || (o.head ? 'FFFFFF' : '222222'), italics: o.italics
    })]
  })]
});

const THEAD = (cells, widths) => new TableRow({
  tableHeader: true,
  children: cells.map((c, i) => TC(c, widths[i], { fill: NAVY, head: true, bold: true, align: AlignmentType.LEFT }))
});

const TROW = (cells, widths, o = {}) => new TableRow({
  children: cells.map((c, i) => TC(c, widths[i], {
    fill: o.fill || (o.zebra ? LIGHT : undefined),
    bold: (o.boldFirst && i === 0) || o.bold,
    color: o.color,
    align: o.aligns ? o.aligns[i] : AlignmentType.LEFT,
    size: o.size
  }))
});

const TBL = (rows, widths) => new Table({
  columnWidths: widths,
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    left: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    right: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 3, color: BAND },
    insideVertical: { style: BorderStyle.SINGLE, size: 3, color: BAND }
  },
  rows
});

const SPACER = (h) => new Paragraph({ spacing: { after: h || 120 }, children: [] });

// callout box
const BOX = (title, body, fill) => new Table({
  columnWidths: [TW],
  width: { size: TW, type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    left: { style: BorderStyle.SINGLE, size: 24, color: ACCENT },
    right: { style: BorderStyle.SINGLE, size: 4, color: BAND },
    insideHorizontal: { style: BorderStyle.NONE },
    insideVertical: { style: BorderStyle.NONE }
  },
  rows: [new TableRow({
    children: [new TableCell({
      width: { size: TW, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: fill || LIGHT, color: 'auto' },
      margins: { top: 130, bottom: 130, left: 180, right: 180 },
      children: [
        new Paragraph({ spacing: { after: 70 }, children: [new TextRun({ text: title, font: F, size: 20, bold: true, color: NAVY })] }),
        ...body.map(b => new Paragraph({
          alignment: AlignmentType.JUSTIFIED, spacing: { after: 60, line: 264 },
          children: [new TextRun({ text: b, font: F, size: 19, color: '2A3340' })]
        }))
      ]
    })]
  })]
});

// ---------- document body ----------
const body = [];

// === COPERTINA ===
body.push(new Paragraph({
  spacing: { after: 60 },
  children: [new TextRun({ text: 'RETE MASTERPLAN', font: F, size: 22, bold: true, color: NAVY, characterSpacing: 60 })]
}));
body.push(new Paragraph({
  spacing: { after: 320 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: ACCENT, space: 8 } },
  children: [new TextRun({ text: 'Engineering & Infrastructure Network', font: F, size: 19, color: GREY })]
}));

body.push(new Paragraph({
  spacing: { after: 100 },
  children: [new TextRun({ text: 'Relazione per la riunione della Rete', font: F, size: 40, bold: true, color: NAVY })]
}));
body.push(new Paragraph({
  spacing: { after: 100 },
  children: [new TextRun({
    text: 'Requisiti di partecipazione delle reti di società di ingegneria alle gare pubbliche italiane',
    font: F, size: 26, color: '2A3340'
  })]
}));
body.push(new Paragraph({
  spacing: { after: 360 },
  children: [new TextRun({
    text: 'Quadro normativo e giurisprudenziale · Evidenze dai bandi delle maggiori stazioni appaltanti · Gap analysis della Rete · Roadmap operativa',
    font: F, size: 20, italics: true, color: GREY
  })]
}));

const covW = [2400, 7238];
body.push(TBL([
  TROW(['Data', '15 settembre 2026'], covW, { boldFirst: true, size: 19 }),
  TROW(['Predisposta da', 'Ing. Giampiero De Michelis — Manager di Rete'], covW, { boldFirst: true, zebra: true, size: 19 }),
  TROW(['Destinatari', 'Imprese Aderenti Fondatrici della Rete Masterplan (9 soggetti) — Organo Comune'], covW, { boldFirst: true, size: 19 }),
  TROW(['Perimetro', 'Servizi di architettura e ingegneria (SIA) ex art. 66 D.Lgs. 36/2023. Esclusa l’esecuzione di lavori e la qualificazione SOA, salvo dove indicato.'], covW, { boldFirst: true, zebra: true, size: 19 }),
  TROW(['Base documentale interna', 'Testo del contratto istitutivo sottoscritto (PDF di 23 pagine, versione R03), letto integralmente e confrontato riga per riga con la bozza agli atti su Drive; «Rapporto verifica requisiti partecipazione — Rete mista — Lotti 4-6» (06/08/2026); nota interna sul contratto R03 (14/09/2026).'], covW, { boldFirst: true, size: 19 }),
  TROW(['Stato della Rete', 'Rete-soggetto costituita, iscritta al Registro delle Imprese e dotata di partita IVA propria (dato riferito dal Manager di Rete; visura non ancora acquisita agli atti).'], covW, { boldFirst: true, zebra: true, size: 19 }),
  TROW(['Natura del documento', 'Documento interno di lavoro. Non è un parere legale e non sostituisce la valutazione del legale e del notaio incaricati.'], covW, { boldFirst: true, zebra: true, size: 19 })
], covW));

body.push(SPACER(300));

body.push(BOX('Avvertenza metodologica', [
  'Le disposizioni del Codice dei contratti pubblici e le pronunce citate sono state riscontrate attraverso ricerca web su fonti professionali e istituzionali secondarie. In questa sessione non è stato possibile accedere direttamente ai testi su Normattiva e sul portale ANAC: prima di qualunque uso esterno, gli estremi e il testo letterale delle norme e delle sentenze citate vanno riverificati sulla fonte ufficiale.',
  'Le informazioni sui bandi provengono da comunicati delle stazioni appaltanti e dalla stampa tecnica di settore. Importi, lotti e scadenze vanno confermati sulla documentazione di gara pubblicata sui rispettivi portali prima di assumere qualsiasi decisione.',
  'I riferimenti al contratto di rete sono invece tratti dalla lettura diretta e integrale del file agli atti.'
]));

body.push(new Paragraph({ children: [new PageBreak()] }));

// === INDICE ===
body.push(H1('Indice'));
body.push(new TableOfContents('Sommario', { hyperlink: true, headingStyleRange: '1-3' }));
body.push(new Paragraph({ children: [new PageBreak()] }));

// === SINTESI ===
body.push(H1('Sintesi per la riunione'));
body.push(P('Cinque messaggi. Se il tempo in riunione è poco, sono questi i punti su cui serve una decisione collegiale.'));

body.push(H3('1. La Rete esiste come operatore economico, ed è la notizia buona di questa relazione'));
body.push(RP([
  { t: 'Il contratto è stato sottoscritto, la Rete è iscritta al Registro delle Imprese e dispone di partita IVA propria: è a tutti gli effetti una ' },
  { t: 'rete-soggetto', b: true },
  { t: ', dotata di soggettività giuridica ai sensi dell’art. 3, comma 4-quater, del D.L. 5/2009. Può quindi contrattare e fatturare in nome proprio, il che per un accordo quadro pluriennale non è un dettaglio contabile ma la condizione per reggere la commessa. Il blocco più grave che pesava sulla versione precedente di questa relazione è superato.' }
]));

body.push(H3('2. Ma per i servizi di ingegneria la Rete non è ancora qualificata, e le manca un requisito preciso'));
body.push(RP([
  { t: 'L’art. 66 del Codice — la norma ' },
  { t: 'speciale', i: true },
  { t: ' che elenca chi può concorrere ai servizi di architettura e ingegneria — non nomina le reti in nessuna delle sue sette lettere. Avendo soggettività giuridica autonoma, l’ente-rete non è né una società di ingegneria né una società tra professionisti: l’unica casella disponibile è la ' },
  { t: 'lettera e), «altri soggetti abilitati in forza del diritto nazionale»', b: true },
  { t: '. Quella casella richiama l’art. 37 dell’Allegato II.12, che pretende oggetto sociale comprensivo dei SIA, organigramma dei tecnici e ' },
  { t: 'almeno un direttore tecnico', b: true },
  { t: ' laureato, abilitato da almeno dieci anni e iscritto all’albo. Nelle ventitré pagine del contratto sottoscritto la figura del direttore tecnico non compare mai. ' },
  { t: 'È il primo blocco da rimuovere, e ha preso il posto di quello vecchio.', b: true }
]));

body.push(H3('3. Il Consiglio di Stato ha chiuso nel 2025 la porta al cumulo dei requisiti'));
body.push(RP([
  { t: 'Con la sentenza della Sezione V n. 8289 del 27 ottobre 2025 è stato affermato che il ' },
  { t: 'cumulo alla rinfusa', b: true },
  { t: ' è istituto eccezionale, riservato ai soli consorzi stabili, e non si estende alle reti di imprese, le quali — prive di soggettività economica unitaria — ' },
  { t: 'devono possedere i requisiti individualmente', b: true },
  { t: '. La conseguenza pratica è netta: Masterplan somma i requisiti come un raggruppamento temporaneo, non come un consorzio stabile. Chi contava sulla rete per «fare massa critica» sui requisiti deve rivedere l’aspettativa. La soggettività giuridica non cambia questo: il Consiglio di Stato l’ha affermato proprio con riferimento a reti dotate di autonoma personalità.' }
]));

body.push(H3('4. Il testo sottoscritto è la bozza R03 senza correzioni, e tre difetti sono entrati nel contratto'));
body.push(RP([
  { t: 'Il confronto riga per riga fra il testo sottoscritto e la bozza agli atti non mostra alcuna modifica. Restano quindi nel contratto ' },
  { t: 'eseguito', i: true },
  { t: ' tre difetti che incidono sulla partecipazione alle gare: il Presidente e il primo Vice Presidente non figurano fra i nove componenti dell’Organo Comune benché l’art. 17 li voglia nominati «al suo interno»; non è previsto alcun direttore tecnico; il fondo patrimoniale comune è fissato in € 1.000 complessivi con quota individuale indicata anch’essa in € 1.000 a testa. ' },
  { t: 'Non sono più correzioni da fare prima della firma: sono modifiche a un contratto in vigore', b: true },
  { t: ', che richiedono la delibera assembleare con le maggioranze dell’art. 15 e la nuova iscrizione al Registro delle Imprese nella forma prescritta dall’art. 37.' }
]));

body.push(H3('5. Il mercato premia una struttura come la nostra, ma non con i tempi delle finestre aperte'));
body.push(RP([
  { t: 'Nei primi cinque mesi del 2026 il mercato delle gare di ingegneria e architettura è cresciuto del 63,4%, e ad aprile gli accordi quadro erano il 25,2% delle gare bandite ma il ' },
  { t: '66% del valore complessivo', b: true },
  { t: '. È il formato che valorizza la multidisciplinarità e il presidio continuativo, cioè esattamente ciò per cui la Rete è stata costituita. Le tre procedure oggi aperte — Regione Campania–Sarno (25 settembre), Agenzia del Demanio (2 ottobre), Consip verifica della progettazione (6 ottobre) — non sono però compatibili con i tempi di un’assemblea di modifica e della successiva iscrizione. Su quelle, se si vuole esserci, la forma praticabile resta il raggruppamento temporaneo fra i retisti abilitati.' }
]));

body.push(SPACER(160));
body.push(BOX('La direzione scelta: attrezzare la Rete', [
  'L’indirizzo è rendere la Rete un operatore qualificato che concorre in proprio, non limitarla al ruolo di cornice commerciale. Questo significa portare in assemblea un pacchetto unico di modifiche e, subito dopo, costruire il fascicolo di qualificazione dell’ente-rete.',
  'Tre cose vanno deliberate perché la Rete superi il test dell’art. 37 dell’Allegato II.12: la nomina di un direttore tecnico con i requisiti di legge, l’allineamento dell’oggetto e del codice ATECO iscritti ai servizi di architettura e ingegneria, e l’elezione del Presidente fra i componenti dell’Organo Comune. Alle stesse condizioni conviene rideterminare il fondo patrimoniale comune.',
  'La Parte V indica la sequenza, le maggioranze necessarie e i documenti da raccogliere.'
], 'FBF6EC'));

body.push(new Paragraph({ children: [new PageBreak()] }));

// === PARTE I ===
body.push(H1('Parte I — Il quadro normativo'));

body.push(H2('1.1  Le reti come operatori economici: artt. 65 e 68 del Codice'));
body.push(P('Il Codice dei contratti pubblici (D.Lgs. 31 marzo 2023, n. 36) riconosce le reti di imprese come operatori economici legittimati a concorrere. Due sono le disposizioni rilevanti.'));
body.push(BULR([
  { t: 'Art. 65, comma 2, lettera g)', b: true },
  { t: ' — include fra i soggetti ammessi a partecipare alle procedure di affidamento le «aggregazioni tra imprese aderenti al contratto di rete» di cui all’art. 3, comma 4-ter, del D.L. 10 febbraio 2009, n. 5, convertito con L. 9 aprile 2009, n. 33. È la norma su cui si fonda la legittimazione generale.' }
]));
body.push(BULR([
  { t: 'Art. 68, comma 20', b: true },
  { t: ' — dispone che alle aggregazioni di retisti si applicano, ' },
  { t: 'in quanto compatibili', i: true },
  { t: ', le regole previste per i raggruppamenti temporanei e i consorzi ordinari. È la norma che governa il funzionamento concreto: quote, mandato, requisiti della mandataria, divieti di partecipazione plurima.' }
]));
body.push(P('La clausola «in quanto compatibili» non è una formula di stile: significa che ogni istituto del raggruppamento va verificato caso per caso nella sua trasferibilità alla rete, e che dove la disciplina della rete presenta una specificità — la soggettività giuridica, l’organo comune, il fondo patrimoniale — prevale quest’ultima.'));

body.push(H2('1.2  Le tre configurazioni di rete e cosa cambia in gara'));
body.push(P('La disciplina di gara distingue tre configurazioni, con regimi documentali e di sottoscrizione differenti. La collocazione di Masterplan è nella prima.'));

const cfgW = [2500, 3600, 3538];
body.push(TBL([
  THEAD(['Configurazione', 'Struttura', 'Come partecipa'], cfgW),
  new TableRow({
    children: [
      TC([
        new Paragraph({ spacing: { after: 40, line: 250 }, children: [new TextRun({ text: 'Rete-soggetto', font: F, size: 18, bold: true, color: '222222' })] }),
        new Paragraph({ spacing: { after: 0, line: 250 }, children: [new TextRun({ text: '(configurazione Masterplan)', font: F, size: 18, bold: true, italics: true, color: ACCENT })] })
      ], cfgW[0]),
      TC('Organo comune con potere di rappresentanza + soggettività giuridica acquisita con l’iscrizione nella Sezione Ordinaria del Registro delle Imprese', cfgW[1]),
      TC('Partecipa a mezzo dell’organo comune, che assume il ruolo di mandatario purché in possesso dei relativi requisiti. La domanda è sottoscritta dal solo operatore che riveste la funzione di organo comune. L’organo comune deve obbligatoriamente far parte dei retisti indicati per la gara.', cfgW[2])
    ]
  }),
  TROW([
    'Rete-contratto con organo comune rappresentativo',
    'Organo comune con potere di rappresentanza, senza soggettività giuridica',
    'Partecipa tramite l’organo comune in forza del mandato risultante dal contratto di rete, con carico documentale intermedio.'
  ], cfgW, { boldFirst: true, zebra: true }),
  TROW([
    'Rete priva di organo comune, o con organo comune privo di rappresentanza',
    'Nessun mandato collettivo opponibile ai terzi',
    'Deve costituirsi, o impegnarsi a costituirsi, in raggruppamento temporaneo secondo le regole ordinarie: mandato collettivo speciale con rappresentanza, sottoscrizione da parte di tutti i componenti.'
  ], cfgW, { boldFirst: true })
], cfgW));

body.push(SPACER(140));
body.push(RP([
  { t: 'La giurisprudenza amministrativa ha precisato che, nella rete-soggetto, la partecipazione avviene ' },
  { t: 'a condizione che l’organo comune possieda i requisiti di qualificazione previsti per la mandataria', b: true },
  { t: ', e che la mandataria deve in ogni caso possedere i requisiti ed eseguire le prestazioni in misura maggioritaria rispetto a ciascuna delle mandanti. È il vincolo che condiziona più di ogni altro l’architettura interna della nostra aggregazione.' }
]));

body.push(H2('1.3  Il nodo dell’art. 66: le reti non sono nell’elenco dei soggetti ammessi ai SIA'));
body.push(P('L’art. 66 del Codice è la norma speciale che individua gli operatori economici ammessi all’affidamento dei servizi di architettura e ingegneria. Il comma 1 si apre con una clausola di apertura — «nel rispetto del principio di non discriminazione fra i diversi soggetti sulla base della forma giuridica assunta» — e prosegue con un elenco di sette lettere.'));

const art66W = [800, 8838];
body.push(TBL([
  THEAD(['Lett.', 'Soggetto ammesso ai servizi di architettura e ingegneria'], art66W),
  TROW(['a)', 'Prestatori di servizi di ingegneria e architettura: professionisti singoli, associati, società tra professionisti, società di ingegneria, consorzi, GEIE, raggruppamenti temporanei fra i predetti soggetti che rendono a committenti pubblici e privati, operando sul mercato, servizi di ingegneria e architettura; inclusi i restauratori di beni culturali e gli archeologi professionisti'], art66W, { boldFirst: true }),
  TROW(['b)', 'Società tra professionisti'], art66W, { boldFirst: true, zebra: true }),
  TROW(['c)', 'Società di ingegneria'], art66W, { boldFirst: true }),
  TROW(['d)', 'Prestatori di servizi di ingegneria e architettura stabiliti in altri Stati membri'], art66W, { boldFirst: true, zebra: true }),
  TROW(['e)', 'Altri soggetti abilitati in forza del diritto nazionale a offrire sul mercato servizi di ingegneria e architettura'], art66W, { boldFirst: true }),
  TROW(['f)', 'Raggruppamenti temporanei costituiti dai soggetti di cui alle lettere da a) a e)'], art66W, { boldFirst: true, zebra: true }),
  TROW(['g)', 'Consorzi stabili di società di professionisti e di società di ingegneria, anche in forma mista'], art66W, { boldFirst: true })
], art66W));

body.push(SPACER(140));
body.push(RP([
  { t: 'Le aggregazioni di retisti non compaiono in nessuna delle sette lettere.', b: true },
  { t: ' Questa è la criticità strutturale con cui dobbiamo fare i conti, e non è un problema teorico: si è già presentata in concreto sul bando della Regione Campania per il Fiume Sarno, dove il disciplinare disciplina le reti in almeno quattro punti diversi (soggetti ammessi, requisiti nelle forme associate, garanzia provvisoria, documentazione amministrativa) ma la clausola speciale che elenca i soggetti ammessi ai lotti di servizi non le menziona.' }
]));

body.push(SPACER(100));
body.push(BOX('Le due letture possibili, e perché la questione resta aperta', [
  'A favore dell’ammissibilità: ciascun retista è già di per sé un soggetto ex art. 66, l’aggregazione opera con la logica del raggruppamento temporaneo della lettera f), e l’art. 68 comma 20 estende alle reti la disciplina dei raggruppamenti. Il principio di non discriminazione in ragione della forma giuridica, posto in apertura dell’art. 66, milita nella stessa direzione.',
  'Contro: l’art. 66 è norma speciale rispetto all’art. 65, e l’elenco potrebbe essere letto come tassativo da una commissione rigorosa. Inoltre la rete-soggetto, avendo soggettività giuridica autonoma, non è né una società di ingegneria né una società tra professionisti: andrebbe ricondotta alla lettera e), con l’onere di possedere in proprio i requisiti previsti per gli «altri soggetti abilitati» (oggetto sociale comprensivo dei SIA, organigramma, direttore tecnico con abilitazione da almeno dieci anni).',
  'Regola operativa: su ogni gara in cui si valuti la partecipazione come rete, presentare istanza di chiarimento alla stazione appaltante nei termini del disciplinare e non presentare offerta senza risposta scritta favorevole, tenendo pronto il ripiego sul raggruppamento temporaneo.'
]));

body.push(H2('1.4  Che cosa serve alla Rete-soggetto per qualificarsi: il test dell’art. 37'));
body.push(RP([
  { t: 'Questo paragrafo è il cuore della relazione, perché descrive ciò che separa Masterplan dalla possibilità di concorrere in proprio. Avendo acquistato soggettività giuridica, ' },
  { t: 'l’ente-rete è un soggetto di diritto distinto dalle nove imprese che lo compongono', b: true },
  { t: ': non è una società di ingegneria, non è una società tra professionisti, non è un consorzio stabile. Per concorrere ai servizi di architettura e ingegneria deve quindi trovare posto nell’elenco dell’art. 66, e l’unica collocazione praticabile è la lettera e), «altri soggetti abilitati in forza del diritto nazionale a offrire sul mercato servizi di ingegneria e architettura».' }
]));
body.push(RP([
  { t: 'Quella collocazione ha un prezzo: la lettera e) richiama l’' },
  { t: 'art. 37 dell’Allegato II.12, Parte V', b: true },
  { t: ', che pone tre requisiti in capo al soggetto, non all’aggregazione. Sono requisiti verificabili documentalmente, e una commissione li verifica.' }
]));

const t37W = [2300, 4100, 3238];
body.push(TBL([
  THEAD(['Requisito', 'Che cosa chiede la norma', 'Stato della Rete Masterplan'], t37W),
  TROW([
    'Oggetto sociale',
    'L’oggetto deve comprendere i servizi di architettura e ingegneria. I disciplinari aggiungono l’iscrizione al Registro delle Imprese «per attività coerenti con quelle oggetto della procedura», riferita anche all’ente-rete in quanto dotato di soggettività giuridica',
    'Da verificare sulla visura. L’art. 5 del contratto descrive un oggetto molto ampio, che affianca ai SIA lavori edili, General Contractor, gestione rifiuti, commercio, logistica e formazione: un oggetto disomogeneo è argomento per chi voglia contestare la coerenza'
  ], t37W, { boldFirst: true }),
  TROW([
    'Organigramma',
    'Organigramma dei soggetti direttamente impiegati nello svolgimento di funzioni professionali e tecniche e di controllo della qualità: soci, amministratori, dipendenti e consulenti su base annua muniti di partita IVA',
    'Non previsto dal contratto. Va costruito e deliberato: è il documento che dimostra che la Rete dispone di una struttura tecnica e non è un contenitore vuoto'
  ], t37W, { boldFirst: true, zebra: true }),
  TROW([
    'Direttore tecnico',
    'Almeno un direttore tecnico laureato in ingegneria, architettura o disciplina tecnica attinente all’attività prevalente, abilitato all’esercizio della professione da almeno dieci anni e iscritto al relativo albo, in regola con contribuzione, assicurazione e aggiornamento professionale',
    'ASSENTE. Nelle ventitré pagine del contratto sottoscritto la figura non compare mai. È il requisito mancante che oggi impedisce alla Rete di concorrere in proprio ai SIA'
  ], t37W, { boldFirst: true })
], t37W));

body.push(SPACER(140));
body.push(P('A questi si aggiungono tre adempimenti che discendono dalla soggettività giuridica e che vanno curati fin dalla prima gara.'));
body.push(BULR([
  { t: 'Requisiti generali. ', b: true },
  { t: 'Gli artt. 94, 95 e 100 del Codice vanno posseduti da ciascun retista che partecipa ' },
  { t: 'e', i: true },
  { t: ' dall’ente-rete: significa DGUE proprio della Rete, verifica del casellario, regolarità contributiva e consenso al trattamento dei dati tramite FVOE ex art. 35, comma 5-bis.' }
]));
body.push(BULR([
  { t: 'Sottoscrizione dell’offerta. ', b: true },
  { t: 'Nella rete-soggetto la domanda di partecipazione è sottoscritta dal solo operatore economico che riveste la funzione di organo comune, il quale assume il ruolo di mandatario e deve obbligatoriamente essere fra i retisti indicati per la gara. La legittimazione di chi firma va quindi documentata in modo inattaccabile.' }
]));
body.push(BULR([
  { t: 'Fatturazione in nome proprio. ', b: true },
  { t: 'La partita IVA autonoma consente alla Rete di fatturare direttamente le prestazioni, con i rapporti interni regolati da accordi collegati al contratto di rete. È il profilo che rende sostenibile un accordo quadro pluriennale, ma va impostato prima, non a commessa avviata.' }
]));

body.push(H2('1.5  Il Bando tipo ANAC n. 2/2026: la nuova cornice vincolante'));
body.push(RP([
  { t: 'Con delibera n. 153 del 15 aprile 2026 l’ANAC ha approvato il ' },
  { t: 'Bando tipo n. 2/2026', b: true },
  { t: ' per l’affidamento dei servizi di architettura e ingegneria di importo pari o superiore alle soglie di rilevanza europea, con aggiudicazione secondo il criterio dell’offerta economicamente più vantaggiosa. È in vigore dal 30 maggio 2026. ' },
  { t: 'Non è un modello facoltativo', b: true },
  { t: ': ai sensi dell’art. 103 del Codice i bandi tipo ANAC sono vincolanti per le stazioni appaltanti, che possono discostarsene solo con motivazione espressa.' }
]));
body.push(P('Per noi conta per tre ragioni.'));
body.push(NUMP([
  { t: 'Standardizza la struttura dei disciplinari. ', b: true },
  { t: 'Le clausole sulle aggregazioni di retisti — chi sottoscrive, chi produce il DGUE, quali requisiti devono possedere l’organo comune e i singoli retisti — tenderanno a ripetersi identiche da una gara all’altra. Una volta costruita la nostra checklist documentale, è riutilizzabile.' }
]));
body.push(NUMP([
  { t: 'Istituzionalizza il BIM. ', b: true },
  { t: 'Il Building Information Modeling non è più un elemento accessorio valutato in modo discrezionale, ma un processo codificato che permea l’intera struttura del capitolato. Serve una capacità BIM certificata e documentabile, non dichiarata.' }
]));
body.push(NUMP([
  { t: 'Consolida la regola dell’equo compenso. ', b: true },
  { t: 'Il 65% dell’importo determinato per i corrispettivi professionali è prezzo fisso; solo il restante 35% è soggetto a confronto concorrenziale. Il margine di manovra sul prezzo è quindi limitato: la competizione si sposta sui contenuti tecnici, che è precisamente il terreno su cui una struttura multidisciplinare può giocare.' }
]));

body.push(H2('1.6  I requisiti per tipologia soggettiva: Allegato II.12, Parte V'));
body.push(P('Qualunque sia la forma di partecipazione, ciascun componente dell’aggregazione deve possedere i requisiti previsti per la propria natura giuridica dagli artt. 34-40 dell’Allegato II.12, Parte V, al Codice — disposizioni che hanno assorbito il contenuto del previgente D.M. 2 dicembre 2016, n. 263.'));

const allW = [1100, 3100, 5438];
body.push(TBL([
  THEAD(['Art.', 'Soggetto', 'Requisito essenziale'], allW),
  TROW(['34', 'Professionisti singoli e associati', 'Iscrizione all’albo professionale; per gli studi associati, requisiti in capo a ciascun associato che svolge le prestazioni'], allW, { boldFirst: true }),
  TROW(['35', 'Società tra professionisti', 'Soci professionisti iscritti agli albi; prestazioni eseguite da soci o con la collaborazione di dipendenti e consulenti; disciplina dei rapporti con i consulenti su base annua muniti di partita IVA'], allW, { boldFirst: true, zebra: true }),
  TROW(['36', 'Società di ingegneria', 'Almeno un direttore tecnico laureato in ingegneria, architettura o disciplina tecnica attinente all’attività prevalente, abilitato all’esercizio della professione da almeno dieci anni e iscritto all’albo al momento dell’assunzione dell’incarico; organigramma dei soggetti impegnati nelle attività tecnico-professionali (soci, amministratori, dipendenti, consulenti su base annua con partita IVA)'], allW, { boldFirst: true }),
  TROW(['37', 'Altri soggetti abilitati', 'Oggetto sociale comprensivo dei SIA; organigramma; almeno un direttore tecnico con laurea, abilitazione da almeno dieci anni, iscrizione all’albo, regolarità contributiva, assicurativa e di aggiornamento professionale'], allW, { boldFirst: true, zebra: true }),
  TROW(['38', 'Consorzi stabili', 'Struttura stabile di società di professionisti e/o di ingegneria; è l’unica figura cui la giurisprudenza riconosce il cumulo alla rinfusa'], allW, { boldFirst: true }),
  TROW(['39', 'Raggruppamenti temporanei', 'Requisiti in capo a ciascun componente secondo la propria natura; obbligo di prevedere almeno un giovane professionista, laureato abilitato da meno di cinque anni, quale progettista; i requisiti del giovane non concorrono alla formazione dei requisiti di partecipazione'], allW, { boldFirst: true, zebra: true })
], allW));

body.push(SPACER(140));
body.push(RP([
  { t: 'Due implicazioni dirette per noi. Primo: ' },
  { t: 'ciascuna società di ingegneria retista deve disporre di un proprio direttore tecnico', b: true },
  { t: ' con abilitazione da almeno dieci anni. È requisito del singolo soggetto, non dell’aggregazione, e va verificato società per società — non si copre con il direttore tecnico di un altro retista. Secondo: poiché alle aggregazioni di retisti si applica la disciplina dei raggruppamenti, ' },
  { t: 'l’obbligo del giovane professionista va considerato applicabile in via prudenziale', b: true },
  { t: '. Il costo di inserirlo è nullo; il rischio di ometterlo è l’esclusione.' }
]));

body.push(new Paragraph({ children: [new PageBreak()] }));

// === PARTE II ===
body.push(H1('Parte II — La svolta del 2025: niente cumulo alla rinfusa per le reti'));

body.push(H2('2.1  Che cosa ha deciso il Consiglio di Stato'));
body.push(P('Il «cumulo alla rinfusa» è il meccanismo che consente a un soggetto plurisoggettivo di sommare e far valere come propri i requisiti di qualificazione delle imprese che lo compongono, senza che ciascuna debba possedere una quota corrispondente alla prestazione che eseguirà. È il vantaggio competitivo classico del consorzio stabile.'));
body.push(RP([
  { t: 'Nel corso del 2025 la questione della sua estensibilità alle reti di imprese è stata oggetto di un contrasto, ora risolto. Il ' },
  { t: 'TAR Emilia-Romagna, con la sentenza n. 472/2025', b: true },
  { t: ', aveva ammesso il cumulo per una rete, valorizzando l’art. 68, comma 20 e l’assimilazione sostanziale al consorzio stabile. Il ' },
  { t: 'Consiglio di Stato, Sezione V, con sentenza n. 8289 del 27 ottobre 2025', b: true },
  { t: ', ha affermato il principio opposto e destinato a prevalere.' }
]));

body.push(SPACER(100));
body.push(BOX('Il principio affermato', [
  'Il cumulo alla rinfusa è istituto di carattere eccezionale, valevole per i soli consorzi stabili, e in assenza di una norma espressa che lo consenta non può essere esteso alle reti di imprese.',
  'La ratio: il cumulo si fonda sull’avvalimento reciproco fra consorzio e consorziate, reso possibile dal rapporto organico stabile e dalla natura del consorzio stabile quale struttura imprenditoriale autonoma e permanente, dotata di personalità giuridica distinta e costituita con scopo mutualistico.',
  'Le reti di imprese, prive di una struttura autonoma in questo senso e di soggettività economica unitaria, devono possedere i requisiti individualmente.'
], 'FAEDED'));

body.push(H2('2.2  Che cosa significa concretamente per Masterplan'));
body.push(P('Questo è il punto che cambia le aspettative di chi ha costruito la rete pensando a un moltiplicatore di capacità. Vale la pena essere espliciti.'));
body.push(BULR([
  { t: 'La rete somma i requisiti come un raggruppamento temporaneo, non come un consorzio stabile.', b: true },
  { t: ' Il fatturato SIA dei nove retisti si cumula, ma con le regole del raggruppamento: ciascuno porta quello che ha, e la mandataria deve possedere i requisiti in misura percentuale superiore a ciascuna delle mandanti.' }
]));
body.push(BULR([
  { t: 'Il vantaggio competitivo rispetto a un RTP costituito fra gli stessi nove soggetti è, sul piano dei requisiti, nullo.', b: true },
  { t: ' Il vantaggio della rete sta altrove: continuità del rapporto, marchio comune, struttura commerciale stabile, riduzione dei costi transattivi nel costituire di volta in volta un raggruppamento, possibilità di codatorialità e distacco del personale, accesso a strumenti di finanza agevolata riservati alle reti.' }
]));
body.push(BULR([
  { t: 'Il costo aggiuntivo della forma «rete» in gara è invece reale:', b: true },
  { t: ' l’incertezza sull’ammissibilità ex art. 66, l’onere di iscrizione e aggiornamento al Registro delle Imprese, il requisito di iscrizione camerale in capo anche all’ente-rete, il carico documentale specifico.' }
]));
body.push(P('La conclusione non è che la rete sia inutile: è che la rete è un asset organizzativo e commerciale, e solo in seconda battuta un veicolo di gara. Trattarla come veicolo di gara senza le correzioni descritte nella Parte IV espone a un rischio di esclusione che non è compensato da alcun vantaggio sui requisiti.'));

body.push(H2('2.3  Il confronto fra le tre forme aggregative'));
const cmpW = [2300, 2446, 2446, 2446];
body.push(TBL([
  THEAD(['Profilo', 'Rete-soggetto', 'RTP costituendo', 'Consorzio stabile'], cmpW),
  TROW(['Ammissibilità ai SIA ex art. 66', 'Controversa: non elencata', 'Pacifica: lett. f)', 'Pacifica: lett. g)'], cmpW, { boldFirst: true }),
  TROW(['Cumulo alla rinfusa', 'Escluso (Cons. Stato 8289/2025)', 'Escluso', 'Ammesso'], cmpW, { boldFirst: true, zebra: true }),
  TROW(['Chi sottoscrive l’offerta', 'Solo l’organo comune', 'Tutti i componenti', 'Il consorzio'], cmpW, { boldFirst: true }),
  TROW(['Tempi di costituzione', 'Atto notarile + iscrizione RI', 'Immediati (impegno in offerta)', 'Atto costitutivo + struttura stabile'], cmpW, { boldFirst: true, zebra: true }),
  TROW(['Stabilità del rapporto', 'Alta, pluriennale', 'Limitata alla singola gara', 'Alta, strutturale'], cmpW, { boldFirst: true }),
  TROW(['Costi di mantenimento', 'Contenuti (fondo comune, organi)', 'Nulli fra una gara e l’altra', 'Elevati (struttura autonoma)'], cmpW, { boldFirst: true, zebra: true }),
  TROW(['Adatto per', 'Presidio commerciale continuativo e accordi quadro pluriennali', 'Singola gara, tempi stretti', 'Operatività continuativa con massa critica di requisiti'], cmpW, { boldFirst: true })
], cmpW));

body.push(SPACER(140));
body.push(RP([
  { t: 'Una terza via merita di essere messa sul tavolo: ' },
  { t: 'il consorzio stabile di società di ingegneria, anche in forma mista', b: true },
  { t: ', espressamente ammesso dall’art. 66, comma 1, lettera g) e unico soggetto che gode del cumulo alla rinfusa. È la forma che darebbe a Masterplan ciò che oggi la rete non può dare. Richiede però una struttura imprenditoriale autonoma e permanente, con costi e impegni di ben altro ordine. È una decisione strategica, non una scelta tecnica, e come tale va portata in assemblea.' }
]));

body.push(new Paragraph({ children: [new PageBreak()] }));

// === PARTE III ===
body.push(H1('Parte III — Il mercato e i bandi delle maggiori stazioni appaltanti'));

body.push(H2('3.1  I numeri del 2026'));
body.push(P('I dati dell’Osservatorio OICE/Informatel sulle gare pubbliche di ingegneria e architettura descrivono un mercato in forte espansione e in rapida concentrazione.'));

const mktW = [2200, 2600, 4838];
body.push(TBL([
  THEAD(['Periodo', 'Valore bandito', 'Nota'], mktW),
  TROW(['Gennaio 2026', '64,7 mln €', 'di cui 53 mln di SIA e 11,7 mln di progettazione esecutiva da appalti integrati'], mktW, { boldFirst: true }),
  TROW(['Febbraio 2026', '132,5 mln €', 'di cui 106,3 mln di SIA e 26,2 mln di progettazione esecutiva'], mktW, { boldFirst: true, zebra: true }),
  TROW(['Marzo 2026', '474,5 mln €', '+258% sul mese precedente, trainato da due maxi-bandi'], mktW, { boldFirst: true }),
  TROW(['Aprile 2026', '~415 mln €', '254 gare, di cui 64 accordi quadro: il 25,2% delle gare ma il 66% del valore (273,7 mln €)'], mktW, { boldFirst: true, zebra: true }),
  TROW(['Maggio 2026', '311,6 mln €', 'cumulato gennaio-maggio +63,4% sul 2025'], mktW, { boldFirst: true }),
  TROW(['Giugno 2026', '1.662,8 mln €', '+67,1% sull’anno precedente'], mktW, { boldFirst: true, zebra: true })
], mktW));

body.push(SPACER(140));
body.push(RP([
  { t: 'Il dato che conta strategicamente è quello di aprile: ' },
  { t: 'un quarto delle gare assorbe due terzi del valore', b: true },
  { t: ', e sono accordi quadro. Il mercato si sta spostando da un modello a incarico singolo a un modello a contenitore pluriennale, in cui la stazione appaltante seleziona pochi operatori e poi affida per contratti attuativi. Per una struttura aggregata questo è il formato ideale — la multidisciplinarità e la capacità di presidio continuativo sono premiate — ma è anche quello con le soglie di accesso più alte.' }
]));

body.push(H2('3.2  Censimento dei bandi delle maggiori stazioni appaltanti'));
body.push(RP([
  { t: 'Quadro delle procedure rilevanti per il perimetro SIA. ' },
  { t: 'Importi, lotti e scadenze vanno confermati sulla documentazione ufficiale prima di qualunque decisione', b: true },
  { t: ': i dati che seguono provengono da comunicati istituzionali e stampa tecnica di settore.' }
]));

body.push(H3('Finestre aperte con scadenza imminente'));
const b1W = [1900, 3400, 1700, 2638];
body.push(TBL([
  THEAD(['Stazione appaltante', 'Oggetto', 'Importo', 'Scadenza offerte'], b1W),
  TROW([
    'Regione Campania — Centrale di Committenza Regionale',
    'Proc. 4396/AQ/2026 — Accordo Quadro quadriennale, Programma strategico di riqualificazione ambientale e contrasto al rischio idraulico del bacino del Fiume Sarno. 7 lotti funzionali e territoriali, un unico operatore per lotto. I lotti 4-6 comprendono SIA prevalenti più una componente di indagini e rilievi qualificata come lavori (OS20-B, OS20-A, OS25, OG12)',
    '406.990.761,29 €',
    '25 settembre 2026'
  ], b1W, { boldFirst: true }),
  TROW([
    'Agenzia del Demanio — Struttura per la Progettazione',
    'Accordi Quadro triennali di servizi di architettura e ingegneria su tutto il territorio nazionale: progettazione in BIM, rilievi e indagini, direzione lavori e coordinamento della sicurezza, per efficientamento energetico, miglioramento sismico, ristrutturazione, restauro, rifunzionalizzazione e nuova edificazione. 4 lotti (3 territoriali per interventi fino a 5 mln €, 1 nazionale oltre). Fino a 36 operatori selezionati, con apertura esplicita a liberi professionisti, microimprese e PMI',
    '219.000.000 €',
    '2 ottobre 2026 h 12:00 (prorogata dal 21 settembre)'
  ], b1W, { boldFirst: true, zebra: true }),
  TROW([
    'Consip',
    'Primo Accordo Quadro per i servizi di verifica della progettazione (PFTE e progetti esecutivi), per nuove opere e interventi su immobili esistenti, inclusi beni tutelati. 6 lotti per valore e destinazione funzionale, durata 24 mesi, più aggiudicatari per lotto. Vincolo di partecipazione a 2 lotti fra 1 e 5; massimo 3 lotti complessivi considerando il lotto 6',
    '51.000.000 € (fino a 73,44 mln €)',
    '6 ottobre 2026 h 16:00'
  ], b1W, { boldFirst: true })
], b1W));

body.push(SPACER(160));
body.push(H3('Programmi e procedure di riferimento delle altre committenze'));
const b2W = [1900, 5100, 2638];
body.push(TBL([
  THEAD(['Stazione appaltante', 'Oggetto / regime', 'Rilievo per la Rete'], b2W),
  TROW([
    'ANAS',
    'Gara DG 11/25 — Accordo Quadro triennale per servizi di ingegneria su ponti e viadotti: fattibilità, progettazione tecnico-economica ed esecutiva, indagini diagnostiche e rilievi strutturali. 8 lotti territoriali, procedura aperta, 80 punti qualità / 20 prezzo, 28,8 mln €, offerte scadute il 15 gennaio 2026. In precedenza, Accordo Quadro SIA triennale su 2 lotti (Centro Nord; Centro, Sud e Isole) da 6 mln € per progettazione definitiva ed esecutiva di opere fino a 30 mln €, con requisito di fatturato pari a 1,5 volte l’importo a base d’asta nei tre migliori esercizi dell’ultimo quinquennio',
    'Modello ricorrente: accordi quadro a lotti territoriali, requisiti di fatturato severi, forte peso della componente qualitativa. Monitorare la riapertura del programma: è il committente più coerente con l’esperienza infrastrutturale della Rete'
  ], b2W, { boldFirst: true }),
  TROW([
    'RFI / Italferr (Gruppo FS)',
    'Regime dei settori speciali. L’accesso non passa in via ordinaria per gare aperte ma per i Sistemi di Qualificazione: qualificazione di ingegneri e società di ingegneria per la progettazione di opere civili di infrastruttura ferroviaria e fabbricati, progettazione di tracciati e piani di stazione, rilievi della geometria del binario; e Sistema di Qualificazione dei fornitori di servizi di supporto ai gruppi di progettazione di Italferr',
    'Priorità operativa distinta: prima ci si qualifica, poi si viene invitati. Ogni retista interessato va qualificato singolarmente; la qualificazione non è un requisito che la Rete può cumulare'
  ], b2W, { boldFirst: true, zebra: true }),
  TROW([
    'Consip — altre iniziative 2026',
    'Accordo Quadro per l’adeguamento antincendio degli edifici scolastici (98 mln €); collaudi statici per l’ammodernamento autostradale (43,5 mln €); servizi professionali BIM per la Pubblica Amministrazione (58 mln €)',
    'Consip si sta strutturando come committente stabile di servizi tecnici. Presidiare il portale acquistinretepa.it e il Piano industriale 2026-2029'
  ], b2W, { boldFirst: true }),
  TROW([
    'Invitalia (per conto del Ministero della Cultura)',
    'Accordi Quadro per lavori e servizi di ingegneria e architettura a servizio di 105 interventi del Piano di investimenti strategici su siti del patrimonio culturale, edifici e aree naturali (PNRR Missione 1, Componente 3, Fondo Complementare). Ciascuna procedura articolata in massimo 3 lotti geografici (nord, centro, sud)',
    'Terreno naturale per le competenze su beni culturali e restauro presenti in Rete. Richiede archeologi iscritti all’Elenco Nazionale dei Professionisti dei Beni Culturali'
  ], b2W, { boldFirst: true, zebra: true }),
  TROW([
    'Utility idriche e reti energetiche (AQP, Terna, Snam, gestori idrici)',
    'Regime dei settori speciali, con sistemi di qualificazione e albi fornitori propri. Acquedotto Pugliese pubblica bandi di qualificazione e gare attive su sezioni dedicate del proprio portale',
    'Accesso mediato dalla qualificazione preventiva. Da valutare come secondo fronte, dopo la messa in sicurezza della forma di partecipazione'
  ], b2W, { boldFirst: true })
], b2W));

body.push(SPACER(160));
body.push(BOX('Che cosa ci dicono i bandi, letti insieme', [
  'Primo: la forma prevalente è l’accordo quadro pluriennale a lotti, spesso con più aggiudicatari e vincoli di partecipazione incrociata fra lotti. Presentarsi su più lotti impone di farlo sempre nella medesima forma e con la medesima compagine.',
  'Secondo: il BIM è ormai un requisito di ammissione sostanziale, non un elemento premiale. Serve un BIM Manager certificato, un ambiente di condivisione dati e un piano di gestione informativa documentabili.',
  'Terzo: le grandi committenze infrastrutturali di settore speciale (RFI, Italferr, utility) non si aggrediscono con la gara aperta ma con la qualificazione preventiva, che è un lavoro a sé e va avviato in parallelo.',
  'Quarto: diversi bandi affiancano ai SIA componenti qualificate come lavori, con categorie SOA. Una rete di sole società di ingegneria e professionisti non le possiede e deve ricorrere all’avvalimento o includere un retista qualificato.'
]));

body.push(new Paragraph({ children: [new PageBreak()] }));

// === PARTE IV ===
body.push(H1('Parte IV — Gap analysis della Rete Masterplan'));

body.push(H2('4.1  Stato dell’atto e riscontri'));
body.push(RP([
  { t: 'La Rete è costituita, iscritta al Registro delle Imprese e dotata di partita IVA propria. È quindi una ' },
  { t: 'rete-soggetto', b: true },
  { t: ' nel senso pieno dell’art. 3, comma 4-quater, del D.L. 5/2009: un soggetto di diritto autonomo, che può contrattare e fatturare in nome proprio. Il contratto configura un organo comune di nove membri (art. 16), un fondo patrimoniale comune (art. 10), sede in Benevento (art. 4) e durata fino al 31 dicembre 2050 (art. 29).' }
]));
body.push(RP([
  { t: 'Il confronto riga per riga fra il testo sottoscritto e la bozza precedentemente agli atti ' },
  { t: 'non mostra alcuna modifica', b: true },
  { t: ': il testo firmato coincide integralmente con la versione R03. Questo ha una conseguenza che va compresa bene in riunione. I rilievi che seguono non sono più correzioni da apportare prima della firma — sono ' },
  { t: 'modifiche a un contratto in vigore', b: true },
  { t: ', che richiedono la delibera dell’assemblea con le maggioranze dell’art. 15 e la successiva iscrizione nella forma prescritta dall’art. 37. Il costo di intervenire è quindi più alto di quanto sarebbe stato tre mesi fa, ma resta ampiamente sostenibile.' }
]));
body.push(RP([
  { t: 'Due elementi sono ' },
  { t: 'già conformi', b: true },
  { t: ' alle prescrizioni ricorrenti nei disciplinari, e non è scontato: la partecipazione congiunta alle gare risulta individuata come scopo strategico (art. 5) e come «obiettivo principale della rete» nel programma comune (art. 7, lett. g); la durata al 2050 è ampiamente commisurata ai tempi di qualunque accordo quadro, contratti attuativi compresi. Sono le due carenze più frequenti nelle reti che si presentano in gara, e la Rete non le ha.' }
]));

body.push(SPACER(120));
body.push(BOX('Nota documentale — che cosa si produce alla stazione appaltante', [
  'Il file esaminato per questa relazione è un documento di videoscrittura esportato in PDF: non contiene blocco firme, estremi notarili, numeri di repertorio e raccolta né riferimenti di iscrizione, e l’art. 42 è ancora formulato al futuro («sarà iscritto… acquisterà soggettività giuridica»). È con ogni evidenza il testo portato alla sottoscrizione, non la copia autenticata.',
  'In gara i disciplinari chiedono copia del contratto di rete con indicazione dell’organo comune che agisce in rappresentanza, e l’iscrizione camerale dell’ente-rete. Vanno quindi recuperati e tenuti nel fascicolo permanente: la copia con evidenza della sottoscrizione (scansione dell’originale o file firmato digitalmente) e la visura camerale aggiornata della Rete.',
  'La visura serve anche a chiudere due verifiche di questa relazione che allo stato restano aperte: la coerenza dell’oggetto e del codice ATECO con i servizi di architettura e ingegneria, e l’identità del soggetto che risulta iscritto come organo comune.'
]));

body.push(H2('4.2  Come si modifica il contratto adesso'));
body.push(P('Trattandosi di contratto in vigore, ogni intervento segue due regole. L’art. 37 impone che le modifiche siano fatte «nella forma necessaria ai fini dell’iscrizione presso il Registro delle Imprese». L’art. 15 gradua le maggioranze: regola generale la maggioranza delle imprese aderenti; due terzi per le materie riservate all’assemblea dall’art. 14, lettere da a) a g); due terzi più la maggioranza delle Imprese Fondatrici per le lettere h) e i) e per la modifica degli obiettivi strategici e del programma di rete.'));

const delW = [1900, 3500, 2500, 1738];
body.push(TBL([
  THEAD(['Articolo', 'Modifica necessaria', 'Perché', 'Maggioranza'], delW),
  TROW([
    'Nuovo articolo (o integrazione dell’art. 16)',
    'Istituzione e nomina del Direttore Tecnico della Rete, con i requisiti dell’art. 37 dell’Allegato II.12: laurea, abilitazione da almeno dieci anni, iscrizione all’albo, regolarità contributiva, assicurativa e di aggiornamento',
    'È il requisito che oggi impedisce alla Rete di concorrere in proprio ai SIA',
    'Due terzi (materia riconducibile all’art. 14, lett. a-b)'
  ], delW, { boldFirst: true }),
  TROW([
    'Art. 16 e art. 17',
    'Elezione del Presidente e dei Vice Presidenti fra i componenti dell’Organo Comune, come l’art. 17 già prescrive, con verbale che documenti la legittimazione del sottoscrittore delle offerte',
    'Sana il difetto di legittimazione di chi firma digitalmente l’offerta',
    'Due terzi (art. 14, lett. a-b)'
  ], delW, { boldFirst: true, zebra: true }),
  TROW([
    'Art. 16 e art. 19',
    'Individuazione dell’impresa retista che riveste la funzione di organo comune ai fini della partecipazione alle gare, e che assume il ruolo di mandataria',
    'I disciplinari richiedono un operatore economico, non un collegio di persone fisiche',
    'Due terzi (art. 14, lett. a-b)'
  ], delW, { boldFirst: true }),
  TROW([
    'Art. 5 e visura',
    'Allineamento dell’oggetto e del codice ATECO iscritti ai servizi di architettura e ingegneria, con approvazione dell’organigramma dei tecnici',
    'Richiesto dall’art. 37 dell’Allegato II.12 e dalla clausola sull’iscrizione «per attività coerenti»',
    'Due terzi più maggioranza delle Fondatrici, se incide sugli obiettivi strategici'
  ], delW, { boldFirst: true, zebra: true }),
  TROW([
    'Art. 10',
    'Rideterminazione del fondo patrimoniale comune e correzione della quota individuale di adesione',
    'Il fondo è l’unica garanzia dei terzi ex artt. 2614-2615 c.c. e viene guardato da committenti e garanti',
    'Due terzi (art. 10, ultimo comma, e art. 14, lett. g)'
  ], delW, { boldFirst: true }),
  TROW([
    'Artt. 19, 37 e denominazioni',
    'Correzioni redazionali: citazione impropria dell’art. 65, co. 2, lett. g) per la firma delle offerte; rinvio dell’art. 37 all’art. 22 anziché all’art. 23; «Europrogettazione srl» e «Europrogettazione Italia srl» usate alternativamente',
    'Incoerenze che un controinteressato può usare per contestare il testo',
    'Maggioranza (materia redazionale)'
  ], delW, { boldFirst: true, zebra: true })
], delW));

body.push(SPACER(140));
body.push(BOX('Avvertenza sulle maggioranze e sul diritto di recesso', [
  'La qualificazione di ciascuna modifica sotto le lettere dell’art. 14, e quindi la maggioranza applicabile, va confermata dal notaio che redige l’atto: l’art. 14 non contempla espressamente la modifica del contratto fra le materie elencate, e la lettura qui proposta è prudenziale.',
  'Attenzione a un effetto non ovvio: l’art. 5, ultimo periodo, stabilisce che la modifica degli obiettivi strategici costituisce giusta causa di recesso per l’impresa dissenziente. Se l’allineamento dell’oggetto viene costruito come modifica degli obiettivi strategici, un retista contrario può uscire dalla Rete. Conviene quindi impostare l’intervento come precisazione e integrazione, non come riscrittura dell’oggetto, e verificare prima dell’assemblea che il consenso sia pieno.'
], 'FBF6EC'));

body.push(SPACER(100));
body.push(H2('4.3  Registro delle criticità'));
body.push(P('I rilievi sono ordinati per gravità. «Bloccante» significa che il profilo va risolto prima di impegnare risorse su un’offerta presentata in forma di rete; «alta» che va risolto prima della prima gara; «media» che incide sull’architettura dell’aggregazione o sul punteggio.'));

const gapW = [620, 1080, 4300, 3638];
const gapRows = [
  ['G1', 'BLOCCANTE', 'La Rete non dispone di un direttore tecnico. Il contratto non lo prevede né lo nomina. Senza questa figura l’ente-rete non soddisfa l’art. 37 dell’Allegato II.12 e non può qualificarsi come soggetto ex art. 66, comma 1, lett. e).', 'Deliberare in assemblea l’istituzione e la nomina del Direttore Tecnico, scegliendolo fra i professionisti dei retisti che abbiano abilitazione da almeno dieci anni, e raccogliere certificato di iscrizione all’albo, attestazione dell’anzianità, regolarità contributiva e assicurativa.'],
  ['G2', 'BLOCCANTE', 'L’art. 66 del Codice non menziona le aggregazioni di retisti fra i soggetti ammessi ai SIA. Il rischio è l’esclusione per difetto di legittimazione soggettiva, non sanabile con soccorso istruttorio.', 'Su ogni gara: istanza di chiarimento preventiva alla stazione appaltante nei termini del disciplinare; nessuna offerta in forma di rete senza risposta scritta favorevole; raggruppamento temporaneo pronto come alternativa. Il superamento di G1 e G6 rafforza in modo decisivo la posizione della Rete su questo punto.'],
  ['G3', 'BLOCCANTE', 'Il cumulo alla rinfusa è escluso per le reti (Cons. Stato, Sez. V, n. 8289/2025) e la soggettività giuridica non cambia il principio. Ogni retista deve possedere i requisiti individualmente; l’organo comune-mandatario deve possederli in misura superiore a ciascun mandante ed eseguire in misura maggioritaria.', 'Ricognizione del fatturato SIA dei migliori tre esercizi dell’ultimo quinquennio per ciascun retista e verifica di chi può reggere il ruolo di mandataria. Da questo dipende l’architettura dell’aggregazione e la scelta dei lotti aggredibili.'],
  ['G4', 'ALTA', 'Presidente e primo Vice Presidente non figurano fra i nove componenti dell’Organo Comune, mentre l’art. 17 li vuole nominati «al suo interno» e l’art. 19 attribuisce proprio a loro il potere di rappresentanza. Chi firma digitalmente l’offerta lo fa in forza di una nomina che contraddice il contratto.', 'Rielezione del Presidente e dei Vice Presidenti fra i componenti dell’Organo Comune, con verbale idoneo a essere prodotto in gara a dimostrazione dei poteri del sottoscrittore.'],
  ['G5', 'ALTA', 'L’Organo Comune è un collegio di nove persone fisiche, ma i disciplinari richiedono che a rivestirne la funzione sia un «operatore economico» che assume il ruolo di mandatario e sottoscrive da solo la domanda. Un collegio di persone fisiche non è un operatore economico.', 'Individuare nel contratto quale impresa retista eserciti la funzione di organo comune ai fini delle gare, coerentemente con l’esito della ricognizione di G3.'],
  ['G6', 'ALTA', 'Oggetto e codice ATECO iscritti: i disciplinari richiedono l’iscrizione camerale «per attività coerenti» anche in capo all’ente-rete. L’art. 5 descrive un oggetto molto ampio che affianca ai SIA lavori, General Contractor, rifiuti, commercio, logistica e formazione.', 'Acquisire la visura e verificare oggetto e ATECO. Se non coerenti, deliberare l’allineamento con le cautele indicate al § 4.2 sul diritto di recesso.'],
  ['G7', 'ALTA', 'Organigramma dei soggetti impegnati nelle attività tecnico-professionali: richiesto dall’art. 37 dell’Allegato II.12, non previsto dal contratto.', 'Costruire e approvare l’organigramma della Rete, con soci, amministratori, dipendenti e consulenti su base annua muniti di partita IVA, coerente con il gruppo di lavoro tipo.'],
  ['G8', 'ALTA', 'Non tutti i retisti sono soggetti ex art. 66. Bear Service (ditta individuale: energia, qualità, sicurezza, compliance 231) ed Europrogettazione Italia (europrogettazione e finanza agevolata) non rientrano, allo stato, fra i prestatori di SIA.', 'Distinguere nel programma di rete i retisti «abilitati SIA» dagli altri. Nelle gare SIA l’aggregazione va composta con i soli soggetti ex art. 66; gli altri contribuiscono come struttura di supporto, non come componenti dell’aggregazione.'],
  ['G9', 'ALTA', 'Perla Engineering è società di diritto polacco: va ricondotta alla lett. d) dell’art. 66, prestatori stabiliti in altri Stati membri. Ammissibile, ma con onere documentale specifico e senza iscrizione camerale italiana.', 'Predisporre in anticipo la documentazione di abilitazione secondo la legge polacca con traduzione asseverata. Valutare con attenzione l’ipotesi che sia questo soggetto a rivestire il ruolo di mandataria: il carico probatorio sarebbe massimo.'],
  ['G10', 'MEDIA', 'Fondo patrimoniale comune fissato in «€ 1000,00» con quota individuale indicata anch’essa in «€ 1,000,00»: con nove fondatrici i due numeri non tornano e il separatore è errato. Il fondo è la sola garanzia dei terzi per le obbligazioni dell’organo comune (artt. 2614-2615 c.c.).', 'Correggere e dimensionare il fondo in modo credibile per committenti e istituti di credito, con delibera assembleare e iscrizione della modifica.'],
  ['G11', 'MEDIA', 'La stessa persona fisica rappresenta tre dei nove retisti — C.E.A., Europrogettazione Italia e I&B Studio — e il contratto non disciplina come voti chi occupa più seggi. In gara questo espone al rischio di «unico centro decisionale» e al divieto di partecipazione plurima.', 'Disciplinare il voto nell’Organo Comune. Mappare le partecipazioni incrociate prima di decidere su quanti lotti presentare offerta: il divieto colpisce il professionista singolo che sia anche socio, amministratore o dipendente di una società che ha presentato offerta su un lotto diverso.'],
  ['G12', 'MEDIA', 'Ciascuna società di ingegneria retista deve disporre di almeno un proprio direttore tecnico con laurea e abilitazione da almeno dieci anni (art. 36, All. II.12). È requisito del singolo soggetto, distinto dal direttore tecnico della Rete di cui a G1.', 'Verifica società per società, con raccolta di certificati di iscrizione all’albo e attestazione dell’anzianità. Da fare una volta e mantenere aggiornata nel fascicolo permanente.'],
  ['G13', 'MEDIA', 'Il Bando tipo ANAC 2/2026 istituzionalizza il BIM come processo codificato che permea l’intero capitolato. La Rete dichiara competenze BIM ma non risulta agli atti una certificazione formale di BIM Manager.', 'Certificare almeno un BIM Manager e dotarsi di ambiente di condivisione dati e capitolato informativo tipo. Senza questo i lotti sopra soglia sono preclusi in fatto, non in diritto.'],
  ['G14', 'MEDIA', 'La riduzione del 30% della garanzia provvisoria per certificazione ISO 9001 spetta solo se tutte le imprese retiste partecipanti la possiedono. In una compagine che include ditte individuali è improbabile.', 'Censire le certificazioni. Valutare se comporre l’aggregazione di gara con i soli retisti certificati quando la riduzione è economicamente rilevante.'],
  ['G15', 'MEDIA', 'Obbligo del giovane professionista (art. 39, All. II.12): previsto per i raggruppamenti temporanei, applicabile alle reti «in quanto compatibile».', 'Individuare stabilmente almeno un giovane professionista abilitato da meno di cinque anni. I suoi requisiti non concorrono ai requisiti di partecipazione: il costo è nullo, il rischio di ometterlo è l’esclusione.'],
  ['G16', 'BASSA', 'Difetti redazionali sopravvissuti alla sottoscrizione: l’art. 19 cita l’art. 65, co. 2, lett. g) per la firma delle offerte, che è norma sui soggetti e non sulla firma; l’art. 37 rinvia all’art. 22, che riguarda il marchio, anziché all’art. 23 sull’adesione di nuove imprese; «Europrogettazione srl» ed «Europrogettazione Italia srl» si alternano fra firmatari, art. 9 e art. 16.', 'Correzioni da inserire nello stesso pacchetto di modifiche, per non aprire due volte l’atto.'],
  ['G17', 'INFO', 'Il testo esaminato è un file di videoscrittura privo di blocco firme, estremi notarili e riferimenti di iscrizione. Non è la copia producibile in gara.', 'Recuperare e archiviare nel fascicolo permanente la copia con evidenza della sottoscrizione e la visura camerale aggiornata della Rete.']
];
body.push(TBL([
  THEAD(['ID', 'Gravità', 'Rilievo', 'Azione'], gapW),
  ...gapRows.map((r, i) => new TableRow({
    children: [
      TC(r[0], gapW[0], { bold: true, fill: i % 2 ? LIGHT : undefined }),
      TC(r[1], gapW[1], {
        bold: true,
        color: r[1] === 'BLOCCANTE' ? 'B03030' : (r[1] === 'ALTA' ? 'A86A1F' : '3A5570'),
        fill: i % 2 ? LIGHT : undefined
      }),
      TC(r[2], gapW[2], { fill: i % 2 ? LIGHT : undefined }),
      TC(r[3], gapW[3], { fill: i % 2 ? LIGHT : undefined })
    ]
  }))
], gapW));

body.push(new Paragraph({ children: [new PageBreak()] }));

// === PARTE V ===
body.push(H1('Parte V — Roadmap: attrezzare la Rete'));
body.push(RP([
  { t: 'L’indirizzo assunto è rendere la Rete un operatore economico qualificato che concorre in proprio ai servizi di architettura e ingegneria, e non limitarla al ruolo di cornice commerciale entro cui si costituiscono raggruppamenti temporanei. È la strada che risolve il problema alla radice: una volta che l’ente-rete supera il test dell’art. 37, la posizione sull’art. 66 diventa difendibile e la Rete può presentarsi con un unico interlocutore su accordi quadro pluriennali. Richiede però un’assemblea, una nuova iscrizione e la costruzione di un fascicolo di qualificazione. La sequenza che segue è ordinata per dipendenze, non per importanza.' }
]));

body.push(H2('5.1  Fase 1 — L’assemblea di modifica (entro 30 giorni)'));
body.push(NUMP([
  { t: 'Ricognizione preliminare del fatturato SIA. ', b: true },
  { t: 'Ciascun retista comunica il fatturato per servizi di ingegneria e architettura dei migliori tre esercizi dell’ultimo quinquennio, con il documento di comprova: bilancio con nota integrativa per le società di capitali, Modello Unico o dichiarazione IVA per imprese individuali e società di persone. È il dato da cui dipende chi può rivestire la funzione di organo comune, e va acquisito prima di convocare, non durante.' }
]));
body.push(NUMP([
  { t: 'Individuazione del candidato Direttore Tecnico. ', b: true },
  { t: 'Va scelto fra i professionisti che abbiano abilitazione da almeno dieci anni e iscrizione all’albo, verificando fin d’ora la disponibilità dei certificati e la regolarità contributiva, assicurativa e di aggiornamento. Attenzione: l’art. 34 esclude che il Manager di Rete sia titolare, amministratore, socio o dipendente di un’impresa aderente, ma quella incompatibilità riguarda il Manager, non il Direttore Tecnico. Le due figure vanno tenute distinte anche nel verbale.' }
]));
body.push(NUMP([
  { t: 'Acquisizione della visura e della copia sottoscritta. ', b: true },
  { t: 'Servono per verificare oggetto, codice ATECO e soggetto iscritto come organo comune, e per completare l’ordine del giorno con cognizione di causa.' }
]));
body.push(NUMP([
  { t: 'Convocazione e delibera. ', b: true },
  { t: 'Un unico pacchetto di modifiche, secondo la tabella del § 4.2, portato al notaio nella forma necessaria per l’iscrizione. Aprire l’atto una volta sola: ogni ritorno costa tempo e consenso.' }
]));

body.push(H2('5.2  Fase 2 — Il fascicolo di qualificazione della Rete (entro 60 giorni)'));
body.push(BUL('Organigramma dei soggetti impegnati nelle attività tecnico-professionali e di controllo della qualità, con soci, amministratori, dipendenti e consulenti su base annua muniti di partita IVA.'));
body.push(BUL('Documentazione del Direttore Tecnico: laurea, certificato di iscrizione all’albo, attestazione dell’anzianità di abilitazione, regolarità contributiva e assicurativa, aggiornamento professionale.'));
body.push(BUL('Iscrizione della modifica al Registro delle Imprese e nuova visura con oggetto e ATECO allineati ai servizi di architettura e ingegneria.'));
body.push(BUL('Requisiti generali dell’ente-rete: DGUE proprio, verifica del casellario, DURC, consenso al trattamento dei dati tramite FVOE ex art. 35, comma 5-bis del Codice.'));
body.push(BUL('Per ciascun retista: visura, iscrizioni agli albi, direttore tecnico con attestazione dell’anzianità decennale, certificazioni ISO in corso di validità, polizze professionali, regolarità contributiva. Per Perla Engineering, documentazione di abilitazione secondo la legge polacca con traduzione asseverata.'));
body.push(BUL('Verbale di elezione del Presidente e dei Vice Presidenti fra i componenti dell’Organo Comune, in forma producibile in gara a dimostrazione dei poteri del sottoscrittore.'));

body.push(H2('5.3  Fase 3 — La dotazione di gara (entro 90 giorni)'));
body.push(BUL('Certificazione di almeno un BIM Manager, ambiente di condivisione dati e capitolato informativo tipo, riutilizzabili da gara a gara. Con il Bando tipo ANAC 2/2026 il BIM è condizione di accesso sostanziale, non elemento premiale.'));
body.push(BUL('Individuazione stabile del giovane professionista e mappatura delle partecipazioni incrociate fra professionisti e società retiste, per prevenire i divieti di partecipazione plurima e il rischio di «unico centro decisionale».'));
body.push(BUL('Mappatura delle coperture che la Rete non possiede: qualificazioni SOA per le componenti di indagini e rilievi, titoli di laboratorio (autorizzazione ministeriale ex art. 59 D.P.R. 380/2001, accreditamento ACCREDIA ISO/IEC 17025, qualificazione amianto), archeologi iscritti all’Elenco Nazionale dei Professionisti dei Beni Culturali. Per ciascuna: copertura interna, avvalimento ex art. 104 o subappalto necessario.'));
body.push(BUL('Avvio delle procedure di qualificazione presso i sistemi dei settori speciali, a partire da RFI e Italferr, per i retisti interessati. È un percorso lungo e indipendente: va iniziato subito e in parallelo, perché la qualificazione è del singolo soggetto e non si cumula in capo alla Rete.'));
body.push(BUL('Costruzione della checklist documentale di Busta A per l’aggregazione di retisti, sulla falsariga del Bando tipo ANAC 2/2026, così da non ricostruirla a ogni gara.'));

body.push(H2('5.4  Le finestre aperte e i tempi'));
body.push(RP([
  { t: 'Va detto con chiarezza perché non generi aspettative sbagliate: le tre procedure oggi aperte — Regione Campania–Sarno il 25 settembre, Agenzia del Demanio il 2 ottobre, Consip verifica della progettazione il 6 ottobre — ' },
  { t: 'non sono compatibili con i tempi della Fase 1', b: true },
  { t: '. Un’assemblea di modifica, l’atto notarile e l’iscrizione al Registro delle Imprese non si completano in dieci o venti giorni, e presentarsi come rete prima che il fascicolo di qualificazione sia chiuso significherebbe esporsi proprio sui punti G1, G6 e G7.' }
]));
body.push(P('Se la Rete vuole essere presente su una di queste procedure, la forma praticabile resta il raggruppamento temporaneo fra i retisti abilitati ai SIA, con la Rete che continua a svolgere la funzione di regia commerciale e organizzativa. La scelta di attrezzare la Rete guarda al ciclo successivo: gli accordi quadro che si apriranno nei prossimi mesi, dove la qualificazione dell’ente-rete diventa il vantaggio competitivo.'));

body.push(H2('5.5  Le decisioni da assumere in questa riunione'));
const decW = [560, 9078];
body.push(TBL([
  THEAD(['#', 'Decisione'], decW),
  TROW(['1', 'Approvare l’indirizzo: la Rete si attrezza per concorrere in proprio ai servizi di architettura e ingegneria, con il pacchetto di modifiche del § 4.2 da portare in assemblea straordinaria.'], decW, { boldFirst: true }),
  TROW(['2', 'Designare il candidato Direttore Tecnico della Rete e dare mandato di verificarne i requisiti documentali prima della convocazione.'], decW, { boldFirst: true, zebra: true }),
  TROW(['3', 'Stabilire quale impresa retista riveste la funzione di organo comune ai fini delle gare, subordinatamente all’esito della ricognizione sul fatturato SIA.'], decW, { boldFirst: true }),
  TROW(['4', 'Fissare la nuova misura del fondo patrimoniale comune e la quota individuale di adesione.'], decW, { boldFirst: true, zebra: true }),
  TROW(['5', 'Decidere se concorrere su una delle tre finestre aperte in forma di raggruppamento temporaneo e, in caso affermativo, su quale e con quale compagine.'], decW, { boldFirst: true }),
  TROW(['6', 'Dare mandato al Manager di Rete di acquisire la copia sottoscritta del contratto e la visura camerale, e di costituire il fascicolo permanente di qualificazione.'], decW, { boldFirst: true, zebra: true })
], decW));

body.push(SPACER(220));
body.push(BOX('Una considerazione finale', [
  'Il quadro è migliore di quello che si presentava prima di conoscere lo stato della Rete. Il soggetto esiste, ha personalità giuridica e partita IVA, e i due requisiti che le reti più spesso non hanno — la partecipazione congiunta alle gare fra gli scopi strategici e una durata capiente — ci sono già. Quello che manca è un fascicolo di qualificazione, non un assetto da rifondare.',
  'Il punto da non perdere di vista è che la rete non moltiplica i requisiti: su questo il Consiglio di Stato è stato netto nel 2025. Il valore di Masterplan sta altrove, e sta esattamente dove il mercato si sta spostando: accordi quadro pluriennali e multidisciplinari, dove conta presidiare in modo continuativo e coprire competenze che nessuno ha per intero — progettazione, ambiente, laboratorio, strutture, BIM, beni culturali, sicurezza. È la nostra composizione. La decisione presa è di attrezzarci perché quel valore sia anche formalmente spendibile.'
]));

// ---------- document ----------
const doc = new Document({
  creator: 'Rete Masterplan — Engineering & Infrastructure Network',
  title: 'Requisiti di partecipazione delle reti di società di ingegneria alle gare pubbliche italiane',
  description: 'Relazione per la riunione della Rete Masterplan — 15 settembre 2026',
  styles: {
    default: {
      document: { run: { font: F, size: 21, color: '222222' }, paragraph: { spacing: { line: 276 } } }
    },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: F, size: 30, bold: true, color: NAVY } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: F, size: 24, bold: true, color: NAVY } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { font: F, size: 21, bold: true, color: ACCENT } }
    ]
  },
  numbering: {
    config: [
      { reference: 'bullets', levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 340, hanging: 200 } } } }] },
      { reference: 'numbers', levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 400, hanging: 260 } } } }] }
    ]
  },
  features: { updateFields: true },
  sections: [{
    properties: {
      page: {
        size: { width: convertMillimetersToTwip(210), height: convertMillimetersToTwip(297) },
        margin: { top: convertMillimetersToTwip(22), bottom: convertMillimetersToTwip(20),
                  left: convertMillimetersToTwip(20), right: convertMillimetersToTwip(20) }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          spacing: { after: 60 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: BAND, space: 4 } },
          children: [new TextRun({ text: 'Rete Masterplan · Requisiti di partecipazione alle gare SIA · 15 settembre 2026', font: F, size: 16, color: GREY })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: 'Documento interno di lavoro — non è un parere legale          ', font: F, size: 15, color: GREY }),
            new TextRun({ children: [PageNumber.CURRENT], font: F, size: 15, color: GREY, bold: true }),
            new TextRun({ text: ' / ', font: F, size: 15, color: GREY }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], font: F, size: 15, color: GREY })
          ]
        })]
      })
    },
    children: body
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(process.argv[2] || 'relazione.docx', buf);
  console.log('OK', (buf.length / 1024).toFixed(1), 'KB');
});
