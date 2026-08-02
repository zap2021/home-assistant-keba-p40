# Keba P40 Home Assistant Integration

Benutzerdefinierte Home-Assistant-Integration fuer eine KEBA-Ladestation ueber die lokale REST-API.

## Aktueller Umfang

- Einrichtung ueber Config Flow mit `Host`, `Port`, `Benutzername`, `Passwort` und optionaler SSL-Pruefung
- Authentifizierung ueber `/v2/jwt/login` mit automatischem JWT-Refresh
- Automatische Erkennung der Wallbox ueber `/serialnumber` und `/v2/wallboxes`
- Sensoren fuer Ladeleistung, Gesamtenergie, freigegebenen Strom, Temperatur und aktuelle RFID-Karte
- Binary Sensoren fuer Fahrzeug verbunden, aktive Ladesitzung und Autorisierung aktiv
- Schalter fuer Laden, Verfuegbarkeit und Dauersperre
- Number-Entitaet fuer den maximal verfuegbaren Ladestrom ueber die REST-Load-Management-API
- Lokales Logo/Icon fuer die Integrationskarte in Home Assistant 2026.3 und neuer

## API-Basis

Die Implementierung nutzt die lokale OpenAPI/Swagger-Dokumentation der Wallbox auf Port `8443`, insbesondere:

- `/version`
- `/serialnumber`
- `/v2/jwt/login`
- `/v2/jwt/refresh`
- `/v2/wallboxes`
- `/v2/wallboxes/{serialNumber}`
- `/v2/wallboxes/{serialNumber}/start-charging`
- `/v2/wallboxes/{serialNumber}/stop-charging`
- `/v2/wallboxes/{serialNumber}/change-availability`
- `/v2/wallboxes/{serialNumber}/permanently-lock`
- `/v2/sessions`
- `/v2/rfids/{id}`
- `/v2/configs/lmgmt/{prop}`
- `PUT /v2/configs/lmgmt` mit `max_available_current`

## Installation

1. Das Verzeichnis `custom_components/keba_p40` nach `<config>/custom_components/keba_p40` kopieren.
2. Falls vorhanden, den alten Ordner `<config>/custom_components/keba` entfernen, damit die native Integration nicht ersetzt wird.
3. Home Assistant neu starten.
4. In Home Assistant die Integration `Keba P40` hinzufuegen.
5. Die REST-API-Zugangsdaten der Wallbox eintragen.

Die Brand-Assets liegen unter `custom_components/keba_p40/brand/` und werden von Home Assistant 2026.3+ automatisch als Integrations-Icon und -Logo verwendet.

## Test Client

Unter [test-client/README.md](/Users/sebastian/GitHub/KebaTest/test-client/README.md) liegt eine getrennte lokale TypeScript-Webanwendung, mit der sich die REST-API der Wallbox vorab testen laesst.

## Hinweise

- Standardmaessig ist die SSL-Zertifikatspruefung deaktiviert, da die Wallbox typischerweise ein selbstsigniertes Zertifikat verwendet.
- Die Integration geht aktuell von genau einer primaeren Wallbox pro Geraet aus.

## Verbindungsdiagnose

Wenn Home Assistant meldet, dass keine Verbindung zur Box aufgebaut werden kann, zuerst aus der Home-Assistant-Umgebung testen. Ein erfolgreicher `ping` reicht nicht aus, weil er nur ICMP prueft; die Integration braucht TCP und TLS auf Port `8443`.

```bash
nc -vz -w 5 192.168.147.169 8443
curl -vk --connect-timeout 5 https://192.168.147.169:8443/version
```

Erwartet wird ein erfolgreicher TCP-Verbindungsaufbau und bei `curl` eine Antwort wie `"2.3.0-SNAPSHOT"`. Wenn `ping` funktioniert, diese Befehle im Home-Assistant-Container aber scheitern, blockiert wahrscheinlich Firewall, VLAN-Policy oder Docker-/VM-Netzwerk den TCP-Port `8443`.

Fuer detaillierte Logs:

```yaml
logger:
  logs:
    custom_components.keba_p40: debug
```
