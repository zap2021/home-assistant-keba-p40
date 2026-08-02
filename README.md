# KEBA Home Assistant Integration

Benutzerdefinierte Home-Assistant-Integration fuer eine KEBA-Ladestation ueber die lokale REST-API.

## Aktueller Umfang

- Einrichtung ueber Config Flow mit `Host`, `Port`, `Benutzername`, `Passwort` und optionaler SSL-Pruefung
- Authentifizierung ueber `/v2/jwt/login` mit automatischem JWT-Refresh
- Automatische Erkennung der Wallbox ueber `/serialnumber` und `/v2/wallboxes`
- Sensoren fuer Ladeleistung, Gesamtenergie, freigegebenen Strom und Temperatur
- Binary Sensoren fuer Fahrzeug verbunden, aktive Ladesitzung und Autorisierung aktiv
- Schalter fuer Laden, Verfuegbarkeit und Dauersperre

## API-Basis

Die Implementierung nutzt die lokale OpenAPI/Swagger-Dokumentation der Wallbox auf Port `8443`, insbesondere:

- `/version`
- `/serialnumber`
- `/v2/jwt/login`
- `/v2/jwt/refresh`
- `/v2/wallboxes`
- `/v2/wallboxes/{serialNumber}`
- `/v2/wallboxes/{serialNumber}/startCharging`
- `/v2/wallboxes/{serialNumber}/stopCharging`
- `/v2/wallboxes/{serialNumber}/changeAvailability`
- `/v2/wallboxes/{serialNumber}/permanentlyLock`

## Installation

1. Das Verzeichnis `custom_components/keba` nach `<config>/custom_components/keba` kopieren.
2. Home Assistant neu starten.
3. In Home Assistant die Integration `KEBA Wallbox` hinzufuegen.
4. Die REST-API-Zugangsdaten der Wallbox eintragen.

## Test Client

Unter [test-client/README.md](/Users/sebastian/GitHub/KebaTest/test-client/README.md) liegt eine getrennte lokale TypeScript-Webanwendung, mit der sich die REST-API der Wallbox vorab testen laesst.

## Hinweise

- Standardmaessig ist die SSL-Zertifikatspruefung deaktiviert, da die Wallbox typischerweise ein selbstsigniertes Zertifikat verwendet.
- Die Integration geht aktuell von genau einer primaeren Wallbox pro Geraet aus.
