// Processo principale dell'app desktop "Giornale dei Lavori".
// Avvia il server Express interno e mostra l'interfaccia in una finestra nativa.
const { app, BrowserWindow, Menu, shell, dialog } = require('electron');
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');

// I dati vengono salvati nella cartella utente del sistema (userData), così
// persistono tra un aggiornamento e l'altro dell'app. Esempio su Windows:
//   C:\Users\<utente>\AppData\Roaming\Giornale dei Lavori\giornale.db
const dataDir = app.getPath('userData');
fs.mkdirSync(dataDir, { recursive: true });
process.env.DB_PATH = path.join(dataDir, 'giornale.db');

let finestra;
let serverRef;

async function avvia() {
  // Il server è un modulo ESM: lo carico con import() dinamico.
  const serverUrl = pathToFileURL(path.join(__dirname, '..', 'src', 'server.js')).href;
  const { avviaServer } = await import(serverUrl);
  const { server, url } = await avviaServer(0); // porta libera scelta dal sistema
  serverRef = server;
  return url;
}

function creaFinestra(url) {
  finestra = new BrowserWindow({
    width: 1280,
    height: 860,
    minWidth: 900,
    minHeight: 600,
    title: 'Giornale dei Lavori',
    backgroundColor: '#f4f6f9',
    icon: path.join(__dirname, 'icon.ico'),
    webPreferences: { contextIsolation: true, nodeIntegration: false },
  });

  finestra.loadURL(url);

  // I link esterni si aprono nel browser di sistema, non dentro l'app.
  finestra.webContents.setWindowOpenHandler(({ url: u }) => {
    shell.openExternal(u);
    return { action: 'deny' };
  });

  finestra.on('closed', () => { finestra = null; });
}

function creaMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Apri cartella dati',
          click: () => shell.openPath(dataDir),
        },
        { type: 'separator' },
        { role: 'quit', label: 'Esci' },
      ],
    },
    {
      label: 'Modifica',
      submenu: [
        { role: 'undo', label: 'Annulla' },
        { role: 'redo', label: 'Ripeti' },
        { type: 'separator' },
        { role: 'cut', label: 'Taglia' },
        { role: 'copy', label: 'Copia' },
        { role: 'paste', label: 'Incolla' },
        { role: 'selectAll', label: 'Seleziona tutto' },
      ],
    },
    {
      label: 'Visualizza',
      submenu: [
        { role: 'reload', label: 'Ricarica' },
        { role: 'resetZoom', label: 'Zoom normale' },
        { role: 'zoomIn', label: 'Aumenta zoom' },
        { role: 'zoomOut', label: 'Riduci zoom' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: 'Schermo intero' },
      ],
    },
    {
      label: '?',
      submenu: [
        {
          label: 'Informazioni',
          click: () => dialog.showMessageBox(finestra, {
            type: 'info',
            title: 'Giornale dei Lavori',
            message: 'Giornale dei Lavori',
            detail: 'App per la contabilità di cantiere: schede CME, '
              + 'giornaliere con avanzamenti, contabilità e SAL.\n\n'
              + `I dati sono salvati in:\n${process.env.DB_PATH}`,
          }),
        },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

// Garantisce una sola istanza dell'app.
if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (finestra) { if (finestra.isMinimized()) finestra.restore(); finestra.focus(); }
  });

  app.whenReady().then(async () => {
    try {
      const url = await avvia();
      creaMenu();
      creaFinestra(url);
    } catch (err) {
      dialog.showErrorBox('Errore di avvio',
        'Impossibile avviare il Giornale dei Lavori.\n\n' + (err && err.stack || err));
      app.quit();
    }

    app.on('activate', () => {
      if (BrowserWindow.getAllWindows().length === 0 && finestra === null) {
        avvia().then(creaFinestra);
      }
    });
  });

  app.on('window-all-closed', () => {
    if (serverRef) try { serverRef.close(); } catch { /* ignore */ }
    if (process.platform !== 'darwin') app.quit();
  });
}
