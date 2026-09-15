// ---------- document body ----------
const body = [];

// === COPERTINA ===
body.push(new Paragraph({ spacing: { after: 60 },
  children: [new TextRun({ text: 'RETE MASTERPLAN', font: F, size: 22, bold: true, color: NAVY, characterSpacing: 60 })] }));
body.push(new Paragraph({ spacing: { after: 320 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: ACCENT, space: 8 } },
  children: [new TextRun({ text: 'Engineering & Infrastructure Network', font: F, size: 19, color: GREY })] }));
body.push(new Paragraph({ spacing: { after: 100 },
  children: [new TextRun({ text: 'Quadro normativo', font: F, size: 40, bold: true, color: NAVY })] }));
body.push(new Paragraph({ spacing: { after: 100 },
  children: [new TextRun({ text: 'Le reti di società di ingegneria negli appalti pubblici: fonti europee, fonti nazionali e criteri di partecipazione alle gare italiane', font: F, size: 26, color: '2A3340' })] }));
body.push(new Paragraph({ spacing: { after: 360 },
  children: [new TextRun({ text: 'Ricognizione delle fonti · Giurisprudenza euro-unitaria e nazionale · Checklist dei criteri di ammissione · Questioni aperte e argomenti difensivi', font: F, size: 20, italics: true, color: GREY })] }));

const cw = [2400, 7238];
body.push(TBL([
  TROW(['Data', '15 settembre 2026'], cw, { boldFirst: true, size: 19 }),
  TROW(['Predisposta da', 'Ing. Giampiero De Michelis — Manager di Rete'], cw, { boldFirst: true, zebra: true, size: 19 }),
  TROW(['Oggetto', 'Ricognizione delle norme europee e nazionali che governano la partecipazione delle reti di imprese, e in particolare delle reti di società di ingegneria, alle procedure di affidamento di servizi di architettura e ingegneria.'], cw, { boldFirst: true, size: 19 }),
  TROW(['Perimetro', 'Gare nazionali. La dimensione internazionale — appalti UE fuori dall’Italia, istituzioni finanziarie internazionali, mercati terzi — è rinviata a una seconda ricognizione.'], cw, { boldFirst: true, zebra: true, size: 19 }),
  TROW(['Documento collegato', '«Relazione per la riunione della Rete — Requisiti di partecipazione delle reti di società di ingegneria alle gare pubbliche italiane», di pari data, che applica questo quadro al caso Masterplan.'], cw, { boldFirst: true, size: 19 })
], cw));

body.push(SPACER(300));
body.push(BOX('Avvertenza sulle fonti', [
  'Le norme, le sentenze e gli atti citati sono stati riscontrati attraverso ricerca su fonti professionali e istituzionali secondarie. Non è stato possibile, in questa sede, accedere direttamente ai testi ufficiali su Normattiva, EUR-Lex, CURIA e sul portale ANAC.',
  'Prima di qualunque uso esterno — memoria difensiva, istanza di chiarimento, parere — estremi e testo letterale vanno riverificati sulla fonte ufficiale. Il documento è una mappa delle fonti e degli argomenti, non un parere legale.'
]));
body.push(new Paragraph({ children: [new PageBreak()] }));

body.push(H1('Indice'));
body.push(new TableOfContents('Sommario', { hyperlink: true, headingStyleRange: '1-3' }));
body.push(new Paragraph({ children: [new PageBreak()] }));

// === PARTE I — EUROPA ===
body.push(H1('Parte I — Il livello europeo'));

body.push(H2('1.1  Le direttive appalti del 2014'));
body.push(P('La disciplina degli appalti pubblici nell’Unione poggia su tre direttive del 26 febbraio 2014, recepite in Italia con il D.Lgs. 50/2016 e oggi con il D.Lgs. 36/2023.'));
const dirW = [2100, 3100, 4438];
body.push(TBL([
  THEAD(['Direttiva', 'Ambito', 'Rilievo per la Rete'], dirW),
  TROW(['2014/24/UE', 'Settori ordinari: amministrazioni aggiudicatrici, enti locali, centrali di committenza', 'È la cornice delle gare di Regione Campania, Agenzia del Demanio, Consip, Invitalia, ANAS. Contiene le norme sui raggruppamenti e sulla nozione di operatore economico'], dirW, { boldFirst: true }),
  TROW(['2014/25/UE', 'Settori speciali: acqua, energia, trasporti, servizi postali', 'È la cornice di RFI, Italferr, Terna, Snam, gestori idrici. Consente i sistemi di qualificazione, che sono la porta d’accesso a quelle committenze'], dirW, { boldFirst: true, zebra: true }),
  TROW(['2014/23/UE', 'Concessioni di lavori e servizi', 'Rilevante per il project financing e per le iniziative in concessione previste dall’art. 5 del contratto di rete'], dirW, { boldFirst: true })
], dirW));

body.push(H2('1.2  Il principio di neutralità della forma giuridica'));
body.push(RP([
  { t: 'È il principio più importante di tutto questo quadro, perché è l’argomento europeo su cui una rete può fondare la propria legittimazione a concorrere. Si articola in tre disposizioni della direttiva 2014/24/UE.' }
]));
body.push(BULR([
  { t: 'Considerando 14. ', b: true },
  { t: 'La nozione di «operatori economici» ' },
  { t: 'deve essere interpretata in senso ampio', b: true },
  { t: ', così da comprendere qualunque persona o ente che offra sul mercato la realizzazione di lavori, la fornitura di prodotti o la prestazione di servizi, ' },
  { t: 'a prescindere dalla forma giuridica nel quadro della quale ha scelto di operare', i: true },
  { t: '. Il considerando precisa che vi rientrano imprese, succursali, filiali, società di persone, cooperative, società a responsabilità limitata, università pubbliche e private e altre forme di enti diversi dalle persone fisiche, ' },
  { t: 'a prescindere dal fatto che siano o meno «persone giuridiche» in ogni circostanza', b: true },
  { t: '.' }
]));
body.push(BULR([
  { t: 'Art. 2, paragrafo 1, punto 10. ', b: true },
  { t: 'Definisce l’operatore economico come qualsiasi persona fisica o giuridica, ente pubblico, o ' },
  { t: 'raggruppamento di tali persone o enti, compresa qualsiasi associazione temporanea di imprese', b: true },
  { t: ', che offra sul mercato la prestazione di servizi.' }
]));
body.push(BULR([
  { t: 'Art. 19, paragrafo 2. ', b: true },
  { t: 'I raggruppamenti di operatori economici ' },
  { t: 'non possono essere obbligati dalle amministrazioni aggiudicatrici ad avere una forma giuridica specifica', b: true },
  { t: ' ai fini della presentazione di un’offerta o di una domanda di partecipazione. Le amministrazioni possono precisare nei documenti di gara come i raggruppamenti ottemperano ai requisiti di capacità economico-finanziaria e tecnico-professionale, ' },
  { t: 'purché ciò sia proporzionato e giustificato da ragioni oggettive', i: true },
  { t: '. Solo dopo l’aggiudicazione, e nella misura in cui sia necessario per la buona esecuzione del contratto, può essere imposta al raggruppamento una forma giuridica determinata.' }
]));
body.push(SPACER(100));
body.push(BOX('Perché conta per noi', [
  'L’art. 66 del Codice italiano elenca sette categorie di soggetti ammessi ai servizi di architettura e ingegneria e non menziona le reti. Se quell’elenco venisse letto come tassativo, al punto da escludere una rete i cui componenti sono tutti, individualmente, soggetti ex art. 66, la lettura entrerebbe in tensione con il considerando 14 e con l’art. 19, paragrafo 2, della direttiva.',
  'Nella prassi questo si traduce in un argomento concreto da spendere in un’istanza di chiarimento o, se necessario, in una impugnazione: una clausola di gara che escludesse le aggregazioni di retisti dai lotti di servizi tecnici andrebbe disapplicata o interpretata in senso conforme al diritto dell’Unione.',
  'Non è una garanzia. È la ragione per cui la questione, pur aperta, non è disperata — e la ragione per cui conviene sempre chiedere il chiarimento anziché rinunciare.'
]));

body.push(H2('1.3  La giurisprudenza della Corte di giustizia'));
body.push(H3('C-631/21, Taxi Horn Tours — 10 novembre 2022, Ottava Sezione'));
body.push(P('Rinvio pregiudiziale dal Gerechtshof ’s-Hertogenbosch. La Corte ha confermato che la nozione di operatore economico va interpretata in senso ampio, fino a comprendere una società in nome collettivo priva di personalità giuridica, e ha precisato che quando più operatori partecipano in raggruppamento, anche temporaneo, va presentato un documento di gara unico europeo distinto per ciascuno degli operatori partecipanti. È la pronuncia che meglio illustra l’irrilevanza della personalità giuridica ai fini della legittimazione a concorrere.'));

body.push(H3('C-642/20, Caruter — 28 aprile 2022, Quarta Sezione'));
body.push(RP([
  { t: 'Rinvio pregiudiziale dal Consiglio di giustizia amministrativa per la Regione siciliana. La Corte ha giudicato ' },
  { t: 'contraria alla direttiva 2014/24/UE', b: true },
  { t: ' la norma nazionale — allora l’art. 83, comma 8, del D.Lgs. 50/2016 — che imponeva al soggetto mandatario di un raggruppamento di possedere i requisiti ed eseguire le prestazioni ' },
  { t: 'in misura maggioritaria', i: true },
  { t: '. La pronuncia riguardava un consorzio stabile, ma il principio investe la regola in sé: un vincolo generale e astratto sulla quota della mandataria non trova base nella direttiva.' }
]));
body.push(RP([
  { t: 'Il rilievo pratico è notevole. Molti disciplinari continuano a richiedere che la mandataria possieda i requisiti «in misura percentuale superiore rispetto a ciascuna delle mandanti». ' },
  { t: 'Una clausola di questo tenore è contestabile alla luce di Caruter', b: true },
  { t: ', e va quindi letta con attenzione: se condiziona in modo decisivo l’architettura dell’aggregazione, merita un’istanza di chiarimento prima di rassegnarsi a subirla. ' },
  { t: '⚠ Va però verificato caso per caso se la clausola sia espressione di una prescrizione normativa vigente o di una scelta della stazione appaltante, e quale sia lo stato del recepimento della pronuncia nel D.Lgs. 36/2023.', i: true }
]));

body.push(H2('1.4  Il riconoscimento delle qualifiche professionali'));
body.push(RP([
  { t: 'Rileva per ogni retista stabilito in un altro Stato membro — nel nostro caso Perla Engineering, società di diritto polacco — e per i professionisti che firmano gli elaborati. La fonte è la ' },
  { t: 'direttiva 2005/36/CE', b: true },
  { t: ', modificata dalla direttiva 2013/55/UE, recepita in Italia con il ' },
  { t: 'D.Lgs. 9 novembre 2007, n. 206', b: true },
  { t: ' e, quanto alle modifiche del 2013, con il recepimento entrato in vigore nel gennaio 2016.' }
]));
body.push(BUL('Per gli architetti la direttiva istituisce un sistema di riconoscimento automatico dei titoli, con elenco delle qualifiche nell’allegato V, periodicamente aggiornato da decisioni delegate della Commissione.'));
body.push(BUL('Per gli ingegneri il riconoscimento segue il regime generale, con possibile richiesta di misure compensative, e passa dall’autorità competente italiana.'));
body.push(BUL('La direttiva distingue fra stabilimento e libera prestazione di servizi transfrontaliera: chi presta servizi in modo temporaneo e occasionale segue un regime dichiarativo più leggero rispetto a chi si stabilisce.'));
body.push(P('Nel Codice dei contratti la corrispondenza è nell’art. 66, comma 1, lettera d), che ammette ai servizi di architettura e ingegneria i prestatori stabiliti in altri Stati membri. È la lettera sotto cui va ricondotta Perla Engineering, con l’onere di documentare l’abilitazione secondo la legge dello Stato di stabilimento, corredata di traduzione asseverata.'));

body.push(H2('1.5  Obblighi trasversali di più recente introduzione'));
body.push(H3('Regolamento (UE) 2022/2560 sulle sovvenzioni estere distorsive'));
body.push(RP([
  { t: 'In vigore dal 12 gennaio 2023, applicabile dal 12 luglio 2023, con gli obblighi di notifica operativi dal 12 ottobre 2023. Negli appalti pubblici impone una ' },
  { t: 'notifica alla stazione appaltante', b: true },
  { t: ' quando ricorrono congiuntamente due condizioni: il valore del contratto è pari o superiore a ' },
  { t: '250 milioni di euro', b: true },
  { t: ', e l’offerente ha ricevuto, direttamente o indirettamente, contributi finanziari esteri — cioè provenienti da Paesi terzi, non da Stati membri — pari o superiori a ' },
  { t: '4 milioni di euro', b: true },
  { t: ' nei tre anni precedenti.' }
]));
body.push(BUL('In caso di appalto suddiviso in lotti, l’obbligo scatta quando il valore aggregato dei lotti per i quali l’impresa presenta offerta eccede 125 milioni di euro.'));
body.push(BUL('L’obbligo riguarda l’offerente, le società del gruppo cui appartiene e i principali subappaltatori e fornitori coinvolti nella procedura.'));
body.push(BULR([
  { t: 'Anche quando non sussiste l’obbligo di notifica, l’operatore deve comunque produrre in gara una dichiarazione che elenchi i contributi finanziari esteri ricevuti.', b: true },
  { t: ' È l’adempimento che viene dimenticato più spesso.' }
]));
body.push(P('Per la Rete l’ipotesi non è teorica: l’accordo quadro della Regione Campania sul bacino del Sarno vale oltre 406 milioni di euro, e l’adempimento va verificato per ciascun retista partecipante, la Rete compresa.'));

body.push(H3('Il documento di gara unico europeo'));
body.push(P('Il DGUE è disciplinato dal regolamento di esecuzione (UE) 2016/7 e, in Italia, si compila oggi in forma elettronica sui portali delle stazioni appaltanti. Nelle aggregazioni di retisti va prodotto dall’organo comune e da ciascuna impresa retista indicata per la gara — o da tutte, se l’intera rete partecipa. La regola trova conferma diretta in Taxi Horn Tours.'));

body.push(new Paragraph({ children: [new PageBreak()] }));

// === PARTE II — NAZIONALE, L'ISTITUTO ===
body.push(H1('Parte II — Il livello nazionale: il contratto di rete come istituto'));

body.push(H2('2.1  Le fonti'));
const fontiW = [2600, 7038];
body.push(TBL([
  THEAD(['Fonte', 'Contenuto'], fontiW),
  TROW(['D.L. 10 febbraio 2009, n. 5, art. 3, commi 4-ter e seguenti, convertito con L. 9 aprile 2009, n. 33', 'Norma istitutiva. Con il contratto di rete più imprenditori perseguono lo scopo di accrescere, individualmente e collettivamente, la propria capacità innovativa e la propria competitività sul mercato, obbligandosi sulla base di un programma comune a collaborare in forme e ambiti predeterminati, a scambiarsi informazioni o prestazioni, o a esercitare in comune una o più attività rientranti nell’oggetto delle rispettive imprese'], fontiW, { boldFirst: true }),
  TROW(['D.L. 31 maggio 2010, n. 78, art. 42', 'Interviene sulla disciplina del contratto di rete e sul regime di pubblicità'], fontiW, { boldFirst: true, zebra: true }),
  TROW(['D.L. 18 ottobre 2012, n. 179, art. 36', 'Introduce la possibilità per la rete di acquistare soggettività giuridica mediante iscrizione nella sezione ordinaria del Registro delle Imprese: è la norma che fonda la distinzione fra rete-contratto e rete-soggetto'], fontiW, { boldFirst: true }),
  TROW(['D.M. 10 aprile 2014, n. 122', 'Approva il modello standard tipizzato per la trasmissione del contratto di rete al Registro delle Imprese. Il modello è utilizzabile sia per le reti prive di soggettività sia, con i necessari adattamenti, per le reti-soggetto'], fontiW, { boldFirst: true, zebra: true }),
  TROW(['Codice civile, artt. 2614 e 2615', 'Regime del fondo patrimoniale comune, richiamato in quanto compatibile: indivisibilità del fondo per la durata della rete e limitazione della responsabilità per le obbligazioni assunte dall’organo comune in relazione al programma'], fontiW, { boldFirst: true }),
  TROW(['D.Lgs. 10 settembre 2003, n. 276, art. 30, comma 4-ter', 'Distacco di personale fra imprese retiste e assunzione in regime di codatorialità: strumenti di flessibilità organizzativa propri della rete'], fontiW, { boldFirst: true, zebra: true }),
  TROW(['Circolare Agenzia delle Entrate n. 20/E del 2013', 'Regime fiscale. La rete-soggetto è autonomo soggetto passivo d’imposta, con propria partita IVA: può quindi contrattare e fatturare in nome proprio'], fontiW, { boldFirst: true })
], fontiW));

body.push(H2('2.2  Rete-contratto e rete-soggetto'));
body.push(P('La distinzione governa tutto il resto ed è la prima cosa da accertare quando si legge un contratto di rete.'));
const rsW = [2300, 3700, 3638];
body.push(TBL([
  THEAD(['Profilo', 'Rete-contratto', 'Rete-soggetto'], rsW),
  TROW(['Soggettività giuridica', 'Assente. La rete è un contratto plurilaterale con comunione di scopo', 'Acquistata con l’iscrizione nella sezione ordinaria del Registro delle Imprese della circoscrizione in cui ha sede'], rsW, { boldFirst: true }),
  TROW(['Forma richiesta', 'Atto pubblico, scrittura privata autenticata, o atto firmato digitalmente ai sensi dell’art. 25 del CAD', 'Le stesse forme, ma con l’iscrizione nella sezione ordinaria quale condizione costitutiva della soggettività'], rsW, { boldFirst: true, zebra: true }),
  TROW(['Fondo comune', 'Eventuale', 'Necessario, insieme all’organo comune'], rsW, { boldFirst: true }),
  TROW(['Posizione fiscale', 'Nessuna autonoma: gli effetti ricadono sulle imprese aderenti', 'Autonomo soggetto passivo d’imposta con partita IVA propria'], rsW, { boldFirst: true, zebra: true }),
  TROW(['In gara', 'Partecipa tramite l’organo comune in forza del mandato, o si costituisce in raggruppamento', 'Partecipa a mezzo dell’organo comune che assume il ruolo di mandatario; la domanda è sottoscritta dal solo operatore che riveste quella funzione'], rsW, { boldFirst: true })
], rsW));

body.push(new Paragraph({ children: [new PageBreak()] }));

// === PARTE III — LA RETE NEGLI APPALTI ===
body.push(H1('Parte III — Il livello nazionale: la rete negli appalti pubblici'));

body.push(H2('3.1  Le norme del Codice'));
const codW = [2000, 7638];
body.push(TBL([
  THEAD(['Disposizione', 'Contenuto e rilievo'], codW),
  TROW(['Art. 65, comma 2, lett. g), D.Lgs. 36/2023', 'Include fra gli operatori economici ammessi alle procedure di affidamento le «aggregazioni tra imprese aderenti al contratto di rete» di cui all’art. 3, comma 4-ter, del D.L. 5/2009. È la norma che fonda la legittimazione generale'], codW, { boldFirst: true }),
  TROW(['Art. 68, comma 20', 'Alle aggregazioni di retisti si applicano, in quanto compatibili, le regole previste per i raggruppamenti temporanei e i consorzi ordinari. Governa quote, mandato, requisiti della mandataria e divieti di partecipazione plurima. La clausola «in quanto compatibili» impone di verificare ogni istituto caso per caso'], codW, { boldFirst: true, zebra: true }),
  TROW(['Art. 66, comma 1', 'Elenca in sette lettere i soggetti ammessi ai servizi di architettura e ingegneria, aprendo con il principio di non discriminazione in ragione della forma giuridica. Le aggregazioni di retisti non vi compaiono: è il nodo interpretativo centrale'], codW, { boldFirst: true }),
  TROW(['Allegato II.12, Parte V, artt. 34-40', 'Requisiti per tipologia soggettiva: professionisti singoli e associati (34), società tra professionisti (35), società di ingegneria (36), altri soggetti abilitati (37), consorzi stabili (38), raggruppamenti temporanei e giovane professionista (39). Ha assorbito il contenuto del D.M. 2 dicembre 2016, n. 263'], codW, { boldFirst: true, zebra: true }),
  TROW(['Artt. 94, 95 e 100', 'Requisiti di ordine generale, cause di esclusione automatiche e non automatiche, requisiti di ordine speciale. Nella rete-soggetto vanno posseduti da ciascun retista partecipante e dall’ente-rete'], codW, { boldFirst: true }),
  TROW(['Art. 104', 'Avvalimento. Consentito per i requisiti di ordine speciale, con contratto nativo digitale sottoscritto dalle parti e indicazione a pena di nullità delle risorse messe a disposizione'], codW, { boldFirst: true, zebra: true }),
  TROW(['Art. 103', 'Bandi tipo ANAC: le stazioni appaltanti vi si conformano, potendosene discostare solo con motivazione espressa. È ciò che rende vincolante il Bando tipo n. 2/2026'], codW, { boldFirst: true })
], codW));
body.push(SPACER(120));
body.push(P('⚠ Il D.Lgs. 31 dicembre 2024, n. 209 (correttivo) ha inciso su numerose disposizioni del Codice e dei suoi allegati, intervenendo fra l’altro sulla disciplina dei consorzi. L’elenco puntuale degli articoli incisi in materia di reti e di servizi di ingegneria non è stato verificato su fonte primaria in questa sede e va riscontrato prima dell’uso.'));

body.push(H2('3.2  Le tre configurazioni in gara'));
body.push(P('La prassi dei disciplinari, che discende dalla Determinazione ANAC n. 3 del 23 aprile 2013 e si è consolidata nei bandi tipo, distingue tre situazioni con regimi documentali diversi.'));
const cfg2W = [2600, 3400, 3638];
body.push(TBL([
  THEAD(['Configurazione', 'Struttura', 'Modalità di partecipazione'], cfg2W),
  TROW(['Rete dotata di organo comune con potere di rappresentanza e di soggettività giuridica (rete-soggetto)', 'Ente autonomo iscritto nella sezione ordinaria del Registro delle Imprese', 'Partecipa a mezzo dell’organo comune, che assume il ruolo di mandatario se in possesso dei relativi requisiti. La domanda è sottoscritta dal solo operatore che riveste quella funzione, il quale deve obbligatoriamente essere fra i retisti indicati per la gara'], cfg2W, { boldFirst: true }),
  TROW(['Rete dotata di organo comune con potere di rappresentanza ma priva di soggettività giuridica', 'Mandato collettivo risultante dal contratto di rete', 'Partecipa tramite l’organo comune in forza del mandato, con carico documentale intermedio'], cfg2W, { boldFirst: true, zebra: true }),
  TROW(['Rete priva di organo comune, o con organo comune privo di potere di rappresentanza', 'Nessun mandato opponibile ai terzi', 'Deve costituirsi, o impegnarsi a costituirsi, in raggruppamento temporaneo secondo le regole ordinarie, con sottoscrizione di tutti i componenti'], cfg2W, { boldFirst: true })
], cfg2W));
body.push(SPACER(120));
body.push(P('Due prescrizioni ricorrono in tutti i disciplinari, per ogni configurazione: la partecipazione congiunta alle gare deve risultare individuata nel contratto di rete come uno degli scopi strategici inclusi nel programma comune, e la durata della rete deve essere commisurata ai tempi di realizzazione dell’appalto. Nei contratti pluriennali il parametro non sono i mesi dell’accordo quadro, ma il completamento dei contratti attuativi.'));

body.push(H2('3.3  La giurisprudenza nazionale'));
const giuW = [2700, 6938];
body.push(TBL([
  THEAD(['Pronuncia', 'Principio'], giuW),
  TROW(['Cons. Stato, Sez. V, 27 ottobre 2025, n. 8289', 'Il cumulo alla rinfusa è istituto di carattere eccezionale, valevole per i soli consorzi stabili, e in assenza di norma espressa non si estende alle reti di imprese. Il cumulo si fonda sull’avvalimento reciproco fra consorzio e consorziate, reso possibile dal rapporto organico stabile e dalla natura del consorzio stabile quale struttura imprenditoriale autonoma e permanente. Le reti, prive di soggettività economica unitaria, devono possedere i requisiti individualmente'], giuW, { boldFirst: true }),
  TROW(['TAR Emilia-Romagna, n. 472/2025', 'Aveva ammesso il cumulo per una rete, valorizzando l’art. 68, comma 20, e l’assimilazione sostanziale al consorzio stabile. Orientamento superato dalla pronuncia del Consiglio di Stato'], giuW, { boldFirst: true, zebra: true }),
  TROW(['Cons. Stato, Sez. V, 15 marzo 2023, n. 2734', 'Neutralità delle forme giuridiche: la nozione di operatore economico comprende enti di ogni forma, a prescindere dal fatto che siano o meno persone giuridiche. Il legislatore non impone particolari formalità costitutive ai fini della legittimazione a operare sul mercato, e il bando non può prescriverle per la partecipazione alla gara'], giuW, { boldFirst: true }),
  TROW(['Cons. Stato — rete-soggetto e organo comune', 'Nella rete dotata di organo comune e soggettività giuridica la partecipazione avviene a mezzo dell’organo comune, a condizione che questo possieda i requisiti di qualificazione previsti per la mandataria'], giuW, { boldFirst: true, zebra: true })
], giuW));

body.push(new Paragraph({ children: [new PageBreak()] }));

// === PARTE IV — CRITERI ===
body.push(H1('Parte IV — I criteri per partecipare a una gara nazionale di servizi di ingegneria'));
body.push(P('Questa parte raccoglie in forma di checklist i criteri che una rete di società di ingegneria deve soddisfare per concorrere a una procedura italiana sopra soglia. La colonna «chi lo possiede» è riferita alla configurazione rete-soggetto.'));

body.push(H2('4.1  Requisiti di ordine generale'));
const rgW = [3100, 3300, 3238];
body.push(TBL([
  THEAD(['Requisito', 'Fonte', 'Chi lo possiede'], rgW),
  TROW(['Assenza delle cause di esclusione automatiche e non automatiche', 'Artt. 94 e 95 del Codice', 'Ciascun retista partecipante e l’ente-rete, in quanto dotato di soggettività giuridica'], rgW, { boldFirst: true }),
  TROW(['Regolarità contributiva e fiscale', 'Art. 94 e normativa DURC', 'Ciascun retista e l’ente-rete'], rgW, { boldFirst: true, zebra: true }),
  TROW(['Consenso al trattamento dei dati tramite FVOE', 'Art. 35, comma 5-bis', 'Ciascun operatore economico partecipante'], rgW, { boldFirst: true }),
  TROW(['Dichiarazione sui contributi finanziari esteri', 'Reg. (UE) 2022/2560', 'Ciascun partecipante, sopra le soglie indicate al § 1.5'], rgW, { boldFirst: true, zebra: true })
], rgW));

body.push(H2('4.2  Idoneità professionale'));
body.push(TBL([
  THEAD(['Requisito', 'Fonte', 'Chi lo possiede'], rgW),
  TROW(['Iscrizione al Registro delle Imprese per attività coerenti con l’oggetto della procedura', 'Art. 100 del Codice e clausole di disciplinare', 'Ciascun componente dell’aggregazione e l’organo comune, in quanto dotato di soggettività giuridica'], rgW, { boldFirst: true }),
  TROW(['Requisiti per tipologia soggettiva', 'Allegato II.12, Parte V, artt. 34-38', 'Ciascun retista secondo la propria natura giuridica; l’ente-rete secondo l’art. 37, se ricondotto alla lett. e) dell’art. 66'], rgW, { boldFirst: true, zebra: true }),
  TROW(['Direttore tecnico', 'Art. 36 per le società di ingegneria; art. 37 per gli altri soggetti abilitati', 'Ciascuna società di ingegneria retista, e l’ente-rete se si qualifica ex art. 37. Requisito del singolo soggetto, non dell’aggregazione'], rgW, { boldFirst: true }),
  TROW(['Iscrizione agli albi professionali', 'Art. 66 e Allegato II.12', 'I professionisti che firmano gli elaborati. Per i prestatori stabiliti in altri Stati membri, abilitazione secondo la legge dello Stato di stabilimento'], rgW, { boldFirst: true, zebra: true })
], rgW));

body.push(H2('4.3  Capacità economica e finanziaria'));
body.push(BUL('Fatturato globale per servizi di architettura e ingegneria maturato nei migliori tre esercizi dell’ultimo quinquennio antecedente la pubblicazione del bando, in misura definita dal disciplinare e commisurata al valore della componente servizi.'));
body.push(BUL('Il requisito si cumula in capo all’aggregazione, ma senza cumulo alla rinfusa: ciascun retista porta ciò che ha, e la somma deve raggiungere la soglia.'));
body.push(BULR([
  { t: 'Frequente la clausola che impone alla mandataria di possedere i requisiti «in misura percentuale superiore rispetto a ciascuna delle mandanti». ', b: true },
  { t: 'Condiziona l’architettura dell’aggregazione ed è la prima verifica da fare, ma alla luce di Caruter è anche la clausola più contestabile (§ 1.3).' }
]));
body.push(BUL('Comprova: bilanci con nota integrativa per le società di capitali; Modello Unico o dichiarazione IVA per imprese individuali e società di persone; dichiarazione dell’organo di controllo contabile ex art. 47 D.P.R. 445/2000. Per operatori con meno di tre anni di attività il requisito è rapportato al periodo effettivo.'));

body.push(H2('4.4  Capacità tecnica e professionale'));
body.push(BUL('Servizi di punta e servizi analoghi nelle classi e categorie richieste, riferiti alle opere oggetto dell’affidamento.'));
body.push(BUL('Gruppo di lavoro minimo, con ruoli tipizzati, titoli, abilitazioni, iscrizioni e anzianità professionale. I nominativi vanno di norma indicati già in sede di offerta.'));
body.push(BUL('Ruoli che il disciplinare riserva a soggetto interno all’impresa capofila: tipicamente il responsabile dell’integrazione delle prestazioni specialistiche e i responsabili dell’accordo quadro e dei contratti attuativi.'));
body.push(BUL('Giovane professionista, laureato abilitato da meno di cinque anni, quale progettista: obbligatorio nei raggruppamenti temporanei ex art. 39 dell’Allegato II.12, applicabile alle reti in quanto compatibile. I suoi requisiti non concorrono alla formazione dei requisiti di partecipazione.'));
body.push(BUL('Capacità BIM: con il Bando tipo ANAC n. 2/2026 il Building Information Modeling è processo codificato che permea l’intero capitolato, non elemento premiale. Servono BIM Manager certificato, ambiente di condivisione dati e piano di gestione informativa.'));
body.push(BUL('Rapporti ammessi fra professionisti e operatore economico: componente del raggruppamento; componente dello studio associato partecipante; professionista in organico con status di dipendente, socio attivo, consulente su base annua o a progetto. Il consulente su base annua deve avere partita IVA, firmare gli elaborati o far parte dell’ufficio di direzione lavori, e aver fatturato verso la società oltre il 50% del proprio fatturato annuo.'));

body.push(H2('4.5  Il Bando tipo ANAC n. 2/2026'));
body.push(RP([
  { t: 'Approvato con delibera n. 153 del 15 aprile 2026, in vigore dal 30 maggio 2026, disciplina la procedura aperta per l’affidamento di servizi di architettura e ingegneria di importo pari o superiore alle soglie di rilevanza europea, con aggiudicazione secondo l’offerta economicamente più vantaggiosa. Ai sensi dell’art. 103 del Codice ' },
  { t: 'è vincolante per le stazioni appaltanti', b: true },
  { t: ', che possono discostarsene solo con motivazione espressa. Standardizza le clausole sulle aggregazioni di retisti — chi sottoscrive, chi produce il DGUE, chi possiede quali requisiti — e consolida la regola dell’equo compenso: il 65% dell’importo determinato per i corrispettivi professionali è prezzo fisso, solo il 35% è soggetto a confronto concorrenziale.' }
]));

body.push(H2('4.6  Documentazione tipica della Busta A per una rete-soggetto'));
body.push(BUL('Domanda di partecipazione e dichiarazioni integrative, sottoscritte dal solo operatore che riveste la funzione di organo comune.'));
body.push(BUL('Copia del contratto di rete, con indicazione dell’organo comune che agisce in rappresentanza.'));
body.push(BUL('Dichiarazione che indichi per quali imprese la rete concorre, e dichiarazione delle parti del servizio ovvero della percentuale in caso di prestazioni indivisibili, eseguite dai singoli operatori aggregati.'));
body.push(BUL('DGUE elettronico dell’organo comune e di ciascuna impresa retista indicata, firmato digitalmente.'));
body.push(BUL('Garanzia provvisoria intestata a tutte le imprese retiste partecipanti. La riduzione del 30% per certificazione ISO 9001 spetta solo se tutte le retiste partecipanti la possiedono.'));
body.push(BUL('Eventuale contratto di avvalimento nativo digitale e DGUE dell’ausiliario; ricevuta del contributo ANAC; imposta di bollo; consensi FVOE; informativa privacy.'));

body.push(new Paragraph({ children: [new PageBreak()] }));

// === PARTE V — QUESTIONI APERTE ===
body.push(H1('Parte V — Questioni aperte e argomenti difensivi'));
const qW = [2500, 3600, 3538];
body.push(TBL([
  THEAD(['Questione', 'Il problema', 'L’argomento da spendere'], qW),
  TROW([
    'Le reti non figurano nell’elenco dell’art. 66',
    'La norma speciale sui servizi di architettura e ingegneria elenca sette categorie e non menziona le aggregazioni di retisti. Letta come tassativa, escluderebbe la rete',
    'Considerando 14 e art. 19, par. 2, della direttiva 2014/24/UE; l’apertura dello stesso art. 66 al principio di non discriminazione in ragione della forma giuridica; l’art. 68, comma 20, che estende alle reti la disciplina dei raggruppamenti; Cons. Stato n. 2734/2023 e CGUE C-631/21'
  ], qW, { boldFirst: true }),
  TROW([
    'Quale casella dell’art. 66 per l’ente-rete',
    'Avendo soggettività giuridica, l’ente-rete non è né società di ingegneria né società tra professionisti',
    'Riconduzione alla lett. e), «altri soggetti abilitati in forza del diritto nazionale», con conseguente possesso dei requisiti dell’art. 37 dell’Allegato II.12: oggetto comprensivo dei SIA, organigramma, direttore tecnico. È la strada che rende la posizione difendibile'
  ], qW, { boldFirst: true, zebra: true }),
  TROW([
    'Cumulo alla rinfusa',
    'Escluso per le reti da Cons. Stato n. 8289/2025. La rete somma i requisiti come un raggruppamento, non come un consorzio stabile',
    'Nessun argomento contrario praticabile allo stato. Se la massa critica sui requisiti è l’obiettivo, la forma che la consente è il consorzio stabile di società di ingegneria, anche in forma mista, ammesso dall’art. 66, comma 1, lett. g)'
  ], qW, { boldFirst: true }),
  TROW([
    'Mandataria «in misura maggioritaria»',
    'Clausola ricorrente nei disciplinari, che condiziona chi può fare da capofila',
    'CGUE C-642/20 Caruter ha giudicato contraria alla direttiva la norma nazionale che imponeva alla mandataria di possedere i requisiti ed eseguire in misura maggioritaria. Argomento da istanza di chiarimento, previa verifica dello stato del recepimento'
  ], qW, { boldFirst: true, zebra: true }),
  TROW([
    'Retisti non qualificabili come prestatori di SIA',
    'Una rete mista può includere soggetti che non rientrano nell’art. 66',
    'Comporre l’aggregazione di gara con i soli retisti abilitati, valorizzando gli altri come struttura di supporto. L’organo comune può indicare anche solo alcuni fra i retisti, purché ne faccia parte'
  ], qW, { boldFirst: true })
], qW));

body.push(SPACER(200));
body.push(BOX('Regola operativa', [
  'Su ogni gara in cui si valuti la partecipazione in forma di rete: leggere per prima cosa la clausola sui soggetti ammessi e confrontarla con quella sulle forme aggregative; se la prima non menziona le reti mentre la seconda le disciplina, presentare istanza di chiarimento nei termini del disciplinare, citando le fonti della Parte I; non presentare offerta in forma di rete senza risposta scritta favorevole; tenere pronto il raggruppamento temporaneo come alternativa.',
  'Un’esclusione per difetto di legittimazione soggettiva non è sanabile con soccorso istruttorio: è il rischio che va evitato per primo.'
]));

body.push(SPACER(200));
body.push(H2('Prossimo passo: la dimensione internazionale'));
body.push(P('Questa ricognizione si ferma alle gare nazionali. La seconda parte, da produrre separatamente, dovrà coprire: la partecipazione a gare bandite in altri Stati membri e il regime di stabilimento e libera prestazione di servizi; gli appalti delle istituzioni europee e delle agenzie; le procedure delle istituzioni finanziarie internazionali, che seguono regole proprie di procurement; i mercati terzi e lo strumento per gli appalti internazionali di cui al regolamento (UE) 2022/1031; e il regime delle garanzie, delle assicurazioni professionali e del riconoscimento dei titoli fuori dall’Unione.'));

