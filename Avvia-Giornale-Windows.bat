@echo off
REM ============================================================
REM  Giornale dei Lavori - Avvio per Windows (doppio click)
REM  Avvia il server e apre l'app nel browser.
REM ============================================================
title Giornale dei Lavori
cd /d "%~dp0"

echo.
echo   ========================================
echo     GIORNALE DEI LAVORI
echo   ========================================
echo.

REM Controlla che Node.js sia installato
where node >nul 2>nul
if errorlevel 1 (
  echo   [ERRORE] Node.js non risulta installato.
  echo.
  echo   Scaricalo gratis da:  https://nodejs.org
  echo   Scegli la versione "LTS", installa, poi riprova
  echo   facendo di nuovo doppio click su questo file.
  echo.
  pause
  exit /b 1
)

REM Installa le dipendenze solo la prima volta
if not exist "node_modules" (
  echo   Prima installazione in corso, attendere...
  echo   ^(serve la connessione a internet, solo questa volta^)
  echo.
  call npm install
  if errorlevel 1 (
    echo.
    echo   [ERRORE] Installazione non riuscita. Verifica la connessione e riprova.
    pause
    exit /b 1
  )
)

echo   Avvio dell'applicazione...
echo.
echo   L'app si aprira' nel browser tra pochi secondi.
echo   Indirizzo:  http://localhost:3000
echo.
echo   >>> Per CHIUDERE l'app: chiudi questa finestra nera. <<<
echo.

REM Apre il browser dopo 3 secondi (in parallelo all'avvio del server)
start "" /b cmd /c "timeout /t 3 >nul & start http://localhost:3000"

REM Avvia il server (resta in esecuzione finche' la finestra resta aperta)
call npm start

pause
