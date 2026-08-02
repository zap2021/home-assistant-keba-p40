# KEBA Test Client

Lokale Webanwendung zum Verifizieren der KEBA-REST-API unabhaengig von Home Assistant.

## Zweck

- Verbindung zur Wallbox pruefen
- Login gegen `/v2/jwt/login` testen
- JWT-Refresh pruefen
- Seriennummer, Version und Wallbox-Status lesen
- Schreibende Funktionen wie `startCharging`, `stopCharging`, `changeAvailability` und `permanentlyLock` gezielt ausloesen

## Start

```bash
cd test-client
npm install
npm run dev
```

Danach die von Vite ausgegebene URL im Browser oeffnen.

## Technische Notizen

- Die App ist bewusst als eigenstaendige Vanilla-TypeScript-Anwendung ohne UI-Framework gebaut.
- Im Dev-Betrieb leitet ein lokaler Vite-Middleware-Forwarder Requests von `/keba-api/*` an die konfigurierte Wallbox weiter.
- Fuer selbstsignierte Zertifikate kann die SSL-Pruefung im UI deaktiviert werden.
- Die Zugangsdaten werden nur im Browser-`localStorage` dieser Test-App abgelegt.
