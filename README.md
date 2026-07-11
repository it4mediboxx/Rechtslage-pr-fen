# § Rechtslage – Persönlicher Rechts-Check

Webanwendung zur **persönlichen Rechtslage-Einschätzung nach deutschem Recht**
(private Eigennutzung, ein Nutzer). Die App verwaltet Fälle, analysiert
hochgeladene Dokumente gegen eine lokale Gesetzesdatenbank und generiert
fertige Schreiben.

> **Ersetzt keine anwaltliche Beratung.**
> Nur zur privaten Eigennutzung – Weitergabe von Einschätzungen an Dritte
> erfordert vorher eine RDG-Prüfung. Angaben ohne Gewähr.

---

## Start

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://127.0.0.1:8000
```

Tests:

```bash
python -m pytest tests/ -v
```

## Funktionsumfang

| Bereich | Umsetzung |
|---|---|
| **Rechtsbereiche** | Arbeitsrecht, Privatrecht, Wohnrecht, Firmenrecht (Kleingewerbe/EU), Firmenrecht (GmbH & e.K.) |
| **Upload** | PDF, DOCX, DOC, JPG/PNG, EML/MSG, TXT · Typ-/Magic-Byte-Prüfung, Größenlimit, Virenscan (EICAR-Signatur + optional ClamAV), verständliche Fehlermeldungen |
| **OCR-Pipeline** | Tesseract (falls installiert); bei unleserlicher Qualität expliziter Hinweis statt stiller Fehlanalyse |
| **Dokumenttyp-Erkennung** | Vertrag, Kündigung, Bescheid, Rechnung, Abmahnung, … mit Plausibilitätscheck gegen den Rechtsbereich (Warnhinweis bei Widerspruch) |
| **Fallablage** | `faelle/{rechtsbereich}/{nachname}_{vorname}_{fall-id}/` mit `dokumente/`, `kommunikation/`, `vorlagen/`, `metadaten.json` · Eingaben serverseitig bereinigt (Injection/Path-Traversal) |
| **Gesetzesdatenbank** | SQLite + FTS5-Volltextindex (< 200 ms), Cache häufiger Paragraphen, Seed aus gesetze-im-internet.de, Update-Importer mit **Diff-Protokoll** · Analysen zitieren **ausschließlich** DB-Paragraphen inkl. Fassungsstand |
| **Analyse** | System-Instruktion nach Vorgabe · regelbasierte Engine + optionale KI-Zweitmeinung (`ANTHROPIC_API_KEY`) · bereichsübergreifende Paragraphen, Ausnahmen/Sonderregeln, Chancen/Risiken, fehlende Fakten, Anwalts-Empfehlung |
| **Fristen** | Automatische Extraktion aus Dokumenten & Kommunikation, chronologische Zeitleiste, Warnstufen (überfällig/kritisch/bald/ok), Notfrist-Kennzeichnung (z. B. § 4 KSchG) |
| **Vorlagen** | 8 Schreiben aus `vorlagen-bibliothek.md`, Platzhalter-Befüllung aus Metadaten, App-Hinweise als Prüfregeln implementiert (§ 623 BGB Schriftform, § 556 Abs. 3 BGB 12-Monats-Frist, …) |
| **Robustheit** | Abgebrochene Analysen → Status „unvollständig“, erneut anstoßbar · zentrales Fehlerlog ohne personenbezogene Daten · Timeout + Retry für OCR/DB/KI-API |
| **Datenschutz** | Dokumente, Analysen und Schreiben verschlüsselt (Fernet/AES) · vollständige, protokollierte Löschung je Fall |
| **Performance** | Upload-Bestätigung < 2 s, Analyse asynchron mit Fortschrittsanzeige, Stapelverarbeitung ab 20 Dokumenten |

## Gesetzesdatenbank aktualisieren

```bash
python -c "from app import datenbank, importer; datenbank.initialisieren(); print(importer.alle_aktualisieren())"
```

Der Importer lädt die amtlichen XML-Fassungen von gesetze-im-internet.de und
protokolliert jede Änderung als Diff (`/api/gesetze/protokoll`).

## Architektur

```
app/
├── main.py          FastAPI-Routen + Frontend-Auslieferung
├── config.py        Pfade, Limits, Rechtsbereiche, Hinweise
├── datenbank.py     SQLite + FTS5, Cache, Diff-Protokoll
├── gesetze_seed.py  Seed-Normtexte (Auszüge, Quelle gesetze-im-internet.de)
├── importer.py      Online-Update mit Timeout/Retry
├── faelle.py        Fallanlage, Ordnerstruktur, Löschprotokoll
├── upload.py        Validierung, Virenscan, verschlüsselte Ablage
├── extraktion.py    PDF/DOCX/DOC/OCR/EML/MSG/TXT → Text
├── doktyp.py        Dokumenttyp + Plausibilität
├── fristen.py       Fristen/Zusagen → Zeitleiste mit Warnstufen
├── analyse.py       Analyse-Engine (Regelwerk + optionale KI)
├── vorlagen.py      Vorlagen-Modul mit Prüfregeln
├── krypto.py        Verschlüsselung (Fernet)
└── fehlerlog.py     Zentrales Log ohne PII, kritische Benachrichtigungen
static/              Frontend (Zwei-Farben-Design: Weiß + Tiefblau)
tests/               Unit- & Integrationstests, 2 Testfälle je Rechtsbereich
```
