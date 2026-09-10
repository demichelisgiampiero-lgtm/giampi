// Genera la scheda di registro per Cons. Stato, Sez. V, 11 agosto 2026, n. 6507.
// Fonte: testo integrale in giurisprudenza/testo-integrale/2026-08-11_CdS-V_6507-2026.txt
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  Header, Footer, PageNumber,
} = require("docx");

const W = 9638;                 // larghezza utile (A4, margini 2 cm)
const SERIF = "Cambria";
const INK = "1A1A1A", MUTED = "5A5A5A", RULE = "C8C8C8", BAND = "EFEFEF", ACCENT = "7A2E2E";

const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: none, bottom: none, left: none, right: none };

const p = (text, o = {}) => new Paragraph({
  alignment: o.align,
  spacing: { before: o.before ?? 0, after: o.after ?? 100, line: o.line ?? 260 },
  indent: o.indent,
  border: o.border,
  children: [new TextRun({
    text, font: SERIF, size: o.size ?? 20, bold: o.bold, italics: o.italics,
    color: o.color ?? INK, allCaps: o.caps, characterSpacing: o.track,
  })],
});

// paragrafo con più run (per virgolettati con coda di riferimento)
const pr = (runs, o = {}) => new Paragraph({
  alignment: o.align,
  spacing: { before: o.before ?? 0, after: o.after ?? 100, line: o.line ?? 260 },
  indent: o.indent,
  border: o.border,
  children: runs.map(r => new TextRun({
    text: r.t, font: SERIF, size: r.size ?? o.size ?? 20, bold: r.b, italics: r.i,
    color: r.c ?? o.color ?? INK,
  })),
});

const h1 = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  spacing: { before: 320, after: 140 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 6 } },
  children: [new TextRun({ text: t, font: SERIF, size: 22, bold: true, color: ACCENT, allCaps: true, characterSpacing: 24 })],
});

const h2 = (t) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  spacing: { before: 220, after: 100 },
  children: [new TextRun({ text: t, font: SERIF, size: 21, bold: true, color: INK })],
});

// virgolettato testuale della sentenza: rientro + filetto laterale
const quote = (text, rif) => new Paragraph({
  spacing: { before: 80, after: 120, line: 250 },
  indent: { left: 340 },
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: ACCENT, space: 10 } },
  children: [
    new TextRun({ text: "«" + text + "»", font: SERIF, size: 19, italics: true, color: INK }),
    ...(rif ? [new TextRun({ text: "  " + rif, font: SERIF, size: 17, color: MUTED })] : []),
  ],
});

const bullet = (text, o = {}) => new Paragraph({
  bullet: { level: o.level ?? 0 },
  spacing: { after: 70, line: 255 },
  children: [new TextRun({ text, font: SERIF, size: o.size ?? 20, color: INK, italics: o.italics })],
});

// tabella etichetta/valore
const kv = (rows, wLabel = 2500) => new Table({
  width: { size: W, type: WidthType.DXA },
  columnWidths: [wLabel, W - wLabel],
  rows: rows.map(([k, v], i) => new TableRow({
    children: [
      new TableCell({
        width: { size: wLabel, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: i % 2 ? "FFFFFF" : BAND, color: "auto" },
        margins: { top: 60, bottom: 60, left: 110, right: 110 },
        borders: { top: none, bottom: { style: BorderStyle.SINGLE, size: 2, color: RULE }, left: none, right: none },
        children: [p(k, { size: 18, bold: true, color: MUTED, after: 0, line: 240 })],
      }),
      new TableCell({
        width: { size: W - wLabel, type: WidthType.DXA },
        shading: { type: ShadingType.CLEAR, fill: i % 2 ? "FFFFFF" : BAND, color: "auto" },
        margins: { top: 60, bottom: 60, left: 110, right: 110 },
        borders: { top: none, bottom: { style: BorderStyle.SINGLE, size: 2, color: RULE }, left: none, right: none },
        children: [p(v, { size: 19, after: 0, line: 240 })],
      }),
    ],
  })),
});

const spacer = (h = 120) => new Paragraph({ spacing: { after: h }, children: [] });

// ─────────────────────────── contenuto ───────────────────────────
const doc = new Document({
  creator: "C.E.A. Engineering",
  title: "Cons. Stato, Sez. V, 11 agosto 2026, n. 6507 — scheda di registro",
  description: "Computo metrico estimativo allegato all'offerta economica negli appalti in parte a misura",
  styles: { default: { document: { run: { font: SERIF, size: 20, color: INK } } } },
  numbering: { config: [{ reference: "default-bullet", levels: [
    { level: 0, format: "bullet", text: "–", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 340, hanging: 200 } } } },
    { level: 1, format: "bullet", text: "·", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 640, hanging: 200 } } } },
  ]}]},
  sections: [{
    properties: { page: { margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    headers: { default: new Header({ children: [
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 60 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE, space: 4 } },
        children: [new TextRun({ text: "Registro delle fonti giuridiche · Giurisprudenza", font: SERIF, size: 16, color: MUTED, characterSpacing: 16 })],
      }),
    ]})},
    footers: { default: new Footer({ children: [
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "Cons. Stato, Sez. V, n. 6507/2026 — pag. ", font: SERIF, size: 16, color: MUTED }),
                   new TextRun({ children: [PageNumber.CURRENT], font: SERIF, size: 16, color: MUTED })],
      }),
    ]})},
    children: [
      // ── testata
      p("SCHEDA DI GIURISPRUDENZA", { size: 17, bold: true, color: ACCENT, track: 40, after: 60 }),
      p("Consiglio di Stato, Sezione Quinta", { size: 21, color: MUTED, after: 30 }),
      p("sentenza 11 agosto 2026, n. 6507", { size: 34, bold: true, after: 100, line: 340 }),
      p("Computo metrico estimativo allegato all'offerta economica: valore negoziale nella quota di lavori «a misura» e limiti della rettifica per errore materiale",
        { size: 21, italics: true, color: MUTED, after: 40, line: 280 }),
      new Paragraph({ spacing: { after: 200 }, border: { bottom: { style: BorderStyle.SINGLE, size: 10, color: ACCENT, space: 8 } }, children: [] }),

      // ── 1. estremi
      h1("1. Estremi identificativi"),
      kv([
        ["Autorità", "Consiglio di Stato in sede giurisdizionale — Sezione Quinta"],
        ["Provvedimento", "Sentenza n. 06507/2026 REG.PROV.COLL., pubblicata l'11 agosto 2026"],
        ["N.R.G.", "1630/2026 (ricorso in appello)"],
        ["Udienza pubblica", "2 luglio 2026 — decisione in camera di consiglio del 2 luglio 2026"],
        ["Collegio", "Francesco Caringella (Presidente); Stefano Fantini; Elena Quadri; Massimo Santini (Estensore); Francesca Picardi"],
        ["Grado impugnato", "TAR Campania, sezione staccata di Salerno, Sez. II, sentenza breve n. 337/2026 — riformata"],
        ["Appellante", "Quagliariello Infrastrutture S.r.l. (seconda classificata) — avv. Antonio Melucci"],
        ["Appellato", "Ente Parco Nazionale del Cilento, Vallo di Diano e Alburni — Avvocatura Generale dello Stato"],
        ["Controinteressato", "Consorzio Stabile I.T.M. — Infrastrutture Terrestri e Marittime (aggiudicatario) — avv.ti M. G. Feola, L. Lentini"],
        ["Procedura", "CIG B72793D440 — pista ciclabile lungo il fiume Tanagro"],
        ["Esito", "Appello accolto. Riforma della sentenza di primo grado e annullamento dell'aggiudicazione. Ricorso incidentale riproposto dichiarato inammissibile. Contratto già stipulato lasciato efficace. Spese compensate."],
      ]),
      spacer(180),

      // ── 2. massime
      h1("2. Massime"),
      h2("2.1 — Valore del computo metrico estimativo"),
      p("Negli appalti stipulati anche solo in parte «a misura», il valore — strettamente negoziale ovvero meramente indicativo — del computo metrico estimativo allegato all'offerta economica non si determina in astratto, ma dipende dalla formulazione della lex specialis. Quando il capitolato àncora il corrispettivo della quota «a misura» ai prezzi unitari applicati alle quantità effettivamente eseguite, e il disciplinare impone a pena di esclusione la corrispondenza fra l'importo del CME e quello risultante dal ribasso percentuale, i prezzi unitari del CME costituiscono parametro negoziale e non elemento meramente giustificativo: la loro discordanza dall'importo derivante dal ribasso determina l'indeterminatezza dell'offerta.",
        { after: 140 }),
      h2("2.2 — Limiti dell'errore materiale emendabile"),
      p("La rettifica di una voce del computo metrico estimativo non è riconducibile all'errore materiale emendabile quando il concorrente non spiega in cosa l'errore sia consistito e la commissione non avrebbe potuto percepirlo ictu oculi dalla lettura della sola offerta. In tal caso la sequenza richiesta di chiarimenti — risposta — accettazione si risolve in una modificazione sostanziale dell'offerta economica, inammissibile per violazione del principio di immutabilità dell'offerta e non suscettibile di soccorso istruttorio.",
        { after: 100 }),
      spacer(120),

      // ── 3. vicenda
      h1("3. La vicenda"),
      p("L'Ente Parco Nazionale del Cilento, Vallo di Diano e Alburni indiceva (bando del 5 giugno 2025) una gara per la realizzazione di una pista ciclabile lungo il fiume Tanagro, con importo a base d'asta superiore a € 1.301.000 e aggiudicazione secondo il criterio dell'offerta economicamente più vantaggiosa. L'appalto era strutturato per circa il 70% «a corpo» e per circa il 30% «a misura» (art. 1.3 del capitolato speciale). Si classificava primo il Consorzio Stabile I.T.M., seconda la Quagliariello Infrastrutture S.r.l.", { after: 120 }),
      p("Il disciplinare, all'art. 16, imponeva a pena di esclusione che la busta economica contenesse, oltre al ribasso percentuale, il computo metrico estimativo, e che l'importo del CME fosse corrispondente al prezzo complessivamente offerto.", { after: 120 }),
      h2("Lo scostamento e la «rettifica»"),
      kv([
        ["6 novembre 2025", "La stazione appaltante rileva la discrepanza fra l'importo da ribasso (20,5% — oltre € 1.345.599) e la somma delle voci del CME (oltre € 1.373.600): circa € 28.000 di differenza."],
        ["7 novembre 2025", "I.T.M. risponde che vincolante è solo il ribasso percentuale, imputa lo scarto a un errore materiale sulle quattro voci di abbattimento alberi (nn. 2, 63, 71, 73) e si dichiara disponibile a produrre un computo corretto con prezzo unitario di € 33,59."],
        ["14 novembre 2025", "La commissione accetta i chiarimenti, qualificandoli come correzione di un mero errore materiale non lesiva della par condicio."],
      ], 2100),
      spacer(120),
      p("Le quattro voci ricadevano tutte nella quota di lavori «a misura». Il prezzo unitario aveva questo andamento:", { after: 100 }),
      kv([
        ["CME a base di gara", "€ 100,50"],
        ["CME allegato all'offerta I.T.M.", "€ 79,49"],
        ["CME «corretto» dopo i chiarimenti", "€ 33,59 — valore che consentiva di pareggiare l'importo risultante dal ribasso"],
      ], 3400),
      spacer(180),

      // ── 4. questioni
      h1("4. Le questioni sottoposte al Collegio"),
      p("Il Collegio individua due nodi (§ 9.4):", { after: 100 }),
      bullet("se negli appalti anche solo in parte «a misura» il CME rivesta ruolo puramente indicativo e specificativo ovvero funzione essenziale, cioè impegno negoziale in senso stretto all'interno dell'offerta economica;"),
      bullet("se, nel caso concreto, la voce relativa all'abbattimento degli alberi fosse riconducibile alla nozione di «errore materiale»."),
      spacer(140),

      // ── 5. prima questione
      h1("5. Prima questione — il valore del CME"),
      p("Il Collegio prende atto dell'orientamento invocato dalla stazione appaltante e dall'aggiudicatario, secondo cui prevale il prezzo derivante dal ribasso percentuale e il CME «non ha valore negoziale» (Cons. Stato, Sez. V, n. 1851/2018; n. 6119/2018; n. 1143/2019, sulla scia dell'art. 118 d.P.R. 207/2010, ancorché abrogato). Ne circoscrive però l'ambito:", { after: 100 }),
      quote("Va subito precisato […] come il detto orientamento si sia formato in relazione ai contratti “stipulati a corpo” […]. Quanto invece ai contratti “stipulati a misura” si è formato un ulteriore indirizzo secondo cui occorre verificare, caso per caso, se la lex specialis abbia espressamente inteso attribuire, o meno, “un valore dirimente al computo metrico”", "(§ 9.5.6; richiama CGARS, sez. giurisdiz., 10 maggio 2022, n. 560)"),
      p("Di qui la regola generale:", { after: 100 }),
      quote("per gli appalti “a misura” (o, come nella specie, per le quote di appalto “a misura”) il valore strettamente negoziale o meramente indicativo del CME dipende dalla formulazione della legge di gara", "(§ 9.5.7)"),
      p("Applicata al caso concreto — art. 1.3 del CSA e art. 16 del disciplinare — la regola conduce a qualificare i prezzi unitari come vincolanti:", { after: 100 }),
      quote("per la quota di lavorazioni da eseguirsi a misura il corrispettivo contrattuale è determinato in fase esecutiva mediante l'applicazione dei prezzi unitari offerti alle quantità effettivamente realizzate, con la conseguenza che i prezzi unitari contenuti nel computo metrico estimativo allegato all'offerta economica non assumevano valore meramente interno o giustificativo ma costituivano parametro negoziale per la determinazione del corrispettivo dovuto […]. Il tutto con la ulteriore conseguenza per cui le difformità tra gli importi ivi indicati nel CME e quelli risultanti dalla applicazione del ribasso percentuale non potevano essere degradate a mere discordanze interne o ad errori materiali", "(§ 9.5.8)"),
      p("Ne discende che la discrasia fra somma delle voci del CME e importo da ribasso «non poteva che comportare la indeterminatezza dell'offerta» (§ 9.5.10), e che la giurisprudenza sugli appalti integralmente a corpo non è applicabile alla fattispecie (§ 9.5.9).", { after: 100 }),
      spacer(140),

      // ── 6. seconda questione
      h1("6. Seconda questione — i limiti dell'errore materiale"),
      p("Il Collegio richiama i criteri consolidati (§ 9.6.1), fondati su Ad. plen. 13 novembre 2015, n. 10:", { after: 100 }),
      bullet("la rettifica è ammissibile solo se vi si perviene «con ragionevole certezza e senza attingere a fonti di conoscenza estranee all'offerta medesima»;"),
      bullet("l'errore emendabile è quello «che può essere percepito o rilevato dal contesto stesso dell'atto e che può essere corretto sulla base di una volontà agevolmente individuabile» (Cons. Stato, Sez. VI, n. 978/2017);"),
      bullet("deve trattarsi di «un mero refuso materiale riconoscibile ictu oculi dalla lettura del documento d'offerta», la cui correzione riconduca la volontà erroneamente espressa a quella «inespressa ma chiaramente desumibile dal documento» (Cons. Stato, Sez. V, n. 5344/2022, richiamata da Sez. VII, n. 2101/2024);"),
      bullet("non è esigibile dalla stazione appaltante «uno sforzo di ricostruzione logica dell'offerta esteso a più atti da inquadrare sinotticamente»."),
      spacer(80),
      p("Applicati al caso, i criteri portano a escludere l'errore materiale (§ 9.6.2):", { after: 100 }),
      quote("Non sono state tuttavia spiegate, sia nella sede procedimentale sia nella presente sede processuale, le ragioni per cui vi sarebbe stato un errore materiale tale da correggere, o meglio rettificare, tale voce di costo da euro 79,49 ad euro 33,59. Non è stato illustrato, in altre parole, in cosa potesse consistere l'errore materiale commesso in sede di formulazione dell'offerta originaria", "(§ 9.6.2, lett. b)"),
      quote("Tanto meno un simile “errore materiale” poteva o avrebbe potuto essere immediatamente percepibile dalla commissione di gara. Non si è dunque trattato di un errore o meglio di un refuso ictu oculi percepibile, autoevidente e riconoscibile dalla commissione di gara", "(§ 9.6.2, lett. c)"),
      quote("la complessiva operazione messa in atto tra chiarimenti richiesti (6 novembre 2025), chiarimenti forniti (7 novembre 2025) e chiarimenti accettati (verbale 14 novembre 2025) si è tradotta in una sostanziale manipolazione, integrazione e dunque modificazione dell'offerta, come tale inammissibile (per violazione del principio di immutabilità dell'offerta economica) e neppure suscettibile di soccorso istruttorio", "(§ 9.6.2, lett. d)"),
      spacer(140),

      // ── 7. profili processuali
      h1("7. Profili processuali e dispositivo"),
      h2("Inammissibilità del ricorso incidentale riproposto"),
      p("Il ricorso incidentale, dichiarato improcedibile in primo grado per sopravvenuta carenza di interesse, era stato riproposto in appello ex art. 101, comma 2, c.p.a. Il Collegio lo dichiara inammissibile: la declaratoria di improcedibilità non equivale a omesso esame o assorbimento — presupposti della riproposizione — ma dà luogo a una soccombenza, sia pure virtuale, su questione pregiudiziale, che va impugnata nelle forme dell'appello incidentale per impedire il giudicato interno (§ 8, che richiama Cons. Stato, Sez. III, 10 dicembre 2025, n. 9696). Il Collegio aggiunge comunque, ad abundantiam, le ragioni di infondatezza nel merito (§§ 8.1–8.3).", { after: 120 }),
      h2("Dispositivo"),
      bullet("appello principale accolto sotto i profili di cui ai §§ 3.2, 3.3 e 3.4, con assorbimento di ogni altra censura;"),
      bullet("riforma della sentenza di primo grado e accoglimento del ricorso originario, con annullamento dell'aggiudicazione;"),
      bullet("nessuna declaratoria di inefficacia del contratto già stipulato, per mancanza di rituale domanda di subentro e per l'avanzata fase esecutiva della commessa (§ 11);"),
      bullet("spese integralmente compensate, per la complessità e la «sostanziale novità» della fattispecie (§ 12)."),
      spacer(140),

      // ── 8. riferimenti
      h1("8. Riferimenti"),
      h2("Norme"),
      kv([
        ["D.lgs. 36/2023", "artt. 95, 96, 98 (cause di esclusione e obblighi informativi) — richiamati nel ricorso incidentale; art. 95, comma 1, lett. a), per il triennio di rilevanza dei fatti"],
        ["c.p.a.", "art. 101, comma 2 (riproposizione dei motivi assorbiti); art. 35, comma 1, lett. c) (improcedibilità)"],
        ["Codice civile", "art. 1430 (errore di calcolo: rettifica e non annullamento)"],
        ["d.P.R. 207/2010", "art. 118 — abrogato dal D.lgs. 50/2016, ma base storica dell'orientamento sul CME «privo di valore negoziale» negli appalti a corpo"],
      ], 2100),
      spacer(120),
      h2("Precedenti richiamati"),
      kv([
        ["CME negli appalti a corpo", "Cons. Stato, Sez. V, 23 marzo 2018, n. 1851; Sez. V, 26 ottobre 2018, n. 6119; Sez. V, 19 febbraio 2019, n. 1143"],
        ["CME negli appalti a misura", "CGARS, sez. giurisdiz., 10 maggio 2022, n. 560"],
        ["Errore materiale — principio", "Cons. Stato, Ad. plen., 13 novembre 2015, n. 10"],
        ["Errore materiale — applicazioni", "Cons. Stato, Sez. VI, 2 marzo 2017, n. 978; Sez. V, 26 gennaio 2021, n. 804; Sez. III, 21 marzo 2022, n. 2003; Sez. V, 5 aprile 2022, n. 2529; Sez. V, 28 giugno 2022, n. 5344; Sez. III, 7 luglio 2022, n. 5650; Sez. IV, 31 ottobre 2022, n. 9415; Sez. VII, 4 marzo 2024, n. 2101"],
        ["Riproposizione vs. appello incidentale", "Cons. Stato, Sez. III, 10 dicembre 2025, n. 9696; CGARS, 19 aprile 2021, n. 330; CGARS, 20 febbraio 2023, n. 143"],
      ], 2600),
      spacer(180),

      // ── 9. rilievo operativo
      h1("9. Rilievo operativo"),
      p("Elaborazione redazionale a uso interno: le indicazioni che seguono non sono contenuto della sentenza, ma conseguenze pratiche che se ne traggono per la redazione delle offerte.",
        { size: 18, italics: true, color: MUTED, after: 140 }),
      bullet("Qualificare l'appalto prima di compilare il CME. La distinzione rilevante non è fra gara «a corpo» e gara «a misura», ma fra le singole lavorazioni: in un appalto misto, le voci ricadenti nella quota a misura possono essere vincolanti anche se il resto dell'offerta non lo è."),
      bullet("Leggere la clausola sulla corrispondenza. Se il disciplinare impone, a pena di esclusione, l'uguaglianza fra somma del CME e importo da ribasso, quella clausola trasforma la quadratura aritmetica in requisito di ammissibilità dell'offerta."),
      bullet("Verificare la quadratura prima della trasmissione. Lo scarto qui contestato era di circa € 28.000 su € 1,3 milioni — poco più del 2% — e ha comportato l'annullamento dell'aggiudicazione."),
      bullet("Non contare sui chiarimenti. Un errore è emendabile solo se riconoscibile dalla sola lettura dell'offerta e se la volontà corretta ne è desumibile: uno scostamento di prezzo unitario privo di spiegazione interna non supera il vaglio, e il tentativo di correggerlo qualifica l'operazione come modifica inammissibile."),
      bullet("Conservare la tracciabilità del calcolo. La possibilità di dimostrare in cosa sia consistito l'errore è il presupposto della sanabilità: nel caso deciso è mancata proprio questa dimostrazione, in sede sia procedimentale sia processuale."),
      spacer(200),

      // ── nota di archiviazione
      new Paragraph({ spacing: { before: 200, after: 100 }, border: { top: { style: BorderStyle.SINGLE, size: 6, color: RULE, space: 8 } }, children: [] }),
      p("Nota di archiviazione", { size: 18, bold: true, color: MUTED, caps: true, track: 20, after: 80 }),
      p("Scheda redatta sul testo integrale della sentenza, archiviato in «giurisprudenza/testo-integrale/2026-08-11_CdS-V_6507-2026.txt». I passaggi fra virgolette basse sono citazioni testuali, con indicazione del paragrafo di provenienza; le sintesi e la sezione 9 sono elaborazione redazionale. Filetti, tabelle ed evidenziazioni sono impaginazione di scheda e non appartengono all'originale. Si segnala che la sentenza alterna due grafie della ragione sociale dell'appellante: «Quagliariello» nell'epigrafe, «Quagliarello» nel corpo della motivazione; in scheda si è adottata quella dell'epigrafe.",
        { size: 17, color: MUTED, line: 240, after: 60 }),
      p("Da completare in fase di archiviazione: numero progressivo di registro, data di inserimento, classificazione per tema.",
        { size: 17, italics: true, color: MUTED, line: 240 }),
    ],
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(process.argv[2] || "scheda.docx", b);
  console.log("scritto:", process.argv[2], b.length, "byte");
});
