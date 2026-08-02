# Inoffizielle Home-Assistant-Integration für KEBA P40

[![HACS validation](https://github.com/zap2021/home-assistant-keba-p40/actions/workflows/hacs.yaml/badge.svg)](https://github.com/zap2021/home-assistant-keba-p40/actions/workflows/hacs.yaml)
[![Hassfest](https://github.com/zap2021/home-assistant-keba-p40/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/zap2021/home-assistant-keba-p40/actions/workflows/hassfest.yaml)

> **Status:** Frühphase. Diese benutzerdefinierte Integration ist nicht Teil von Home Assistant Core und wird unabhängig davon entwickelt.

> **Hinweis zu KEBA und Haftung:** Dies ist keine offizielle KEBA-Integration. Der Autor steht in keiner geschäftlichen oder sonstigen Verbindung zu KEBA AG oder ihren verbundenen Unternehmen. Die Nutzung erfolgt auf eigene Verantwortung; es wird keine Haftung für Schäden, Datenverluste, Ausfälle oder Folgeschäden übernommen, soweit dies gesetzlich zulässig ist.

Diese unabhängige Integration dient ausschließlich dazu, KEBA-P40-Ladestationen über ihre lokale REST-API mit Home Assistant zu verwenden. Sie wird weder von KEBA entwickelt, unterstützt noch freigegeben.

## Funktionen

- Einrichtung über den Home-Assistant-Config-Flow
- Lokale JWT-Anmeldung mit automatischer Token-Erneuerung
- Sensoren für Ladeleistung, Energie, Strom, Temperatur und RFID-Informationen
- Binary Sensoren für Fahrzeugverbindung, Ladesitzung und Autorisierung
- Schalter für Laden, Verfügbarkeit und Dauersperre
- Number-Entität für den maximal verfügbaren Ladestrom

## Installation über HACS

1. Öffne in Home Assistant **HACS**.
2. Wähle oben rechts **⋮** → **Benutzerdefinierte Repositories**.
3. Füge `https://github.com/zap2021/home-assistant-keba-p40` hinzu und wähle als Kategorie **Integration**.
4. Suche nach **KEBA P40 (inoffiziell)** und installiere die Integration.
5. Starte Home Assistant neu.
6. Öffne **Einstellungen** → **Geräte & Dienste** → **Integration hinzufügen** und füge **KEBA P40** hinzu.
7. Trage Host, Port, Benutzername und Passwort deiner Wallbox ein.

HACS installiert die Dateien nach `custom_components/keba_p40`. Zugangsdaten und Laufzeit-Tokens werden nicht im Repository gespeichert.

## Manuelle Installation

Kopiere `custom_components/keba_p40` nach `<config>/custom_components/keba_p40` und starte Home Assistant neu. Anschließend wird die Integration unter **Einstellungen** → **Geräte & Dienste** hinzugefügt.

## Voraussetzungen

- Home Assistant 2026.3.0 oder neuer
- Zugriff von Home Assistant auf die lokale REST-API der Wallbox (standardmäßig HTTPS auf Port `8443`)
- REST-API-Zugangsdaten der Wallbox

## Verbindungsdiagnose

Teste die Verbindung aus der Home-Assistant-Umgebung. Ein erfolgreicher `ping` genügt nicht, da die Integration TCP und TLS benötigt:

```bash
nc -vz -w 5 192.0.2.10 8443
curl -vk --connect-timeout 5 https://192.0.2.10:8443/version
```

`192.0.2.10` ist ausschließlich ein Dokumentationsbeispiel. Ersetze die Adresse durch den Hostnamen oder die IP-Adresse deiner eigenen Wallbox.

Für detaillierte Logs:

```yaml
logger:
  logs:
    custom_components.keba_p40: debug
```

## Hinweise

- Die Zertifikatsprüfung ist standardmäßig deaktiviert, weil Wallboxen häufig ein selbstsigniertes TLS-Zertifikat verwenden.
- Die Integration geht derzeit von einer primären Wallbox pro Gerät aus.
- Ein separater Browser-basierter API-Testclient befindet sich unter `test-client/`; er gehört nicht zur HACS-Installation.

## Markenhinweis

„KEBA“ und „P40“ werden ausschließlich zur Beschreibung der Kompatibilität mit den jeweiligen Produkten verwendet. Alle Rechte an Namen, Marken und Produktkennzeichen liegen bei den jeweiligen Rechteinhabern. Dieses Projekt verwendet keine Herstellerlogos.

## Sicherheits- und Nutzungshinweis

Die Integration kann Lade- und Verfügbarkeitsfunktionen der Wallbox steuern. Sie ist nicht für sicherheitskritische, lebenswichtige oder anderweitig schadenskritische Anwendungen vorgesehen. Prüfe die Konfiguration und jede Steuerfunktion vor dem produktiven Einsatz und verwende ausschließlich berechtigte REST-API-Zugangsdaten. Stelle außerdem sicher, dass die Nutzung der lokalen API mit deinen Verträgen, den Geräteeinstellungen und den geltenden Sicherheitsvorgaben vereinbar ist.

## Support

Bitte melde Fehler oder Funktionswünsche über die [GitHub Issues](https://github.com/zap2021/home-assistant-keba-p40/issues).
