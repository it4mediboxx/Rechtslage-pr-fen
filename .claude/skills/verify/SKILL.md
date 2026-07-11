---
name: verify
description: Rechtslage-App bauen, starten und end-to-end im Browser prüfen.
---

# Rechtslage-App verifizieren

## Starten

```bash
pip install -r requirements.txt   # falls nötig: pip3 install --upgrade cffi cryptography
RECHTSLAGE_DATEN=/tmp/rechtslage-daten python3 -m uvicorn app.main:app --port 8321 &
curl -s http://127.0.0.1:8321/api/info   # muss die 5 Rechtsbereiche liefern
```

`RECHTSLAGE_DATEN` immer auf ein Wegwerf-Verzeichnis setzen, sonst landen
Testfälle im echten `daten/`-Ordner.

## Browser-Durchlauf (Playwright, global installiert)

Chromium liegt unter `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`;
Playwright per `createRequire(import.meta.url)('/opt/node22/lib/node_modules/playwright')`
laden (ESM ignoriert NODE_PATH).

Kernstrecke: `#/neu` (Formular) → Upload über `#datei-eingabe`
(`setInputFiles` mit Buffer) → Tab „Analyse“ → auf `.thema` warten (Analyse
läuft asynchron, < 30 s) → Tab „Schreiben“ → Vorlage ausfüllen → `.brief`
prüfen. Gesetzessuche unter `#/gesetze`. Kino-Intro unter `/intro`
(Play-Button nötig, da WebAudio eine Nutzer-Geste verlangt).

## Fallstricke

- Einblendanimationen (~0,7 s): vor Screenshots kurz warten, sonst leere Seiten.
- Erwartete Konsolenfehler: 400 beim abgelehnten Upload, 404 solange keine
  Analyse existiert – keine Bugs.
- OCR (tesseract) ist im Container nicht installiert: Bild-Uploads erzeugen
  bewusst den Hinweis „OCR nicht verfügbar“ statt einer Analyse.
- Tests: `python3 -m pytest tests/ -q` (isoliertes Datenverzeichnis via conftest).
