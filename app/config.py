"""Zentrale Konfiguration: Pfade, Limits, Konstanten."""

import os
from pathlib import Path

# Datenverzeichnis – per Umgebungsvariable umlenkbar (wichtig für Tests)
DATEN_DIR = Path(os.environ.get("RECHTSLAGE_DATEN", "daten")).resolve()
FAELLE_DIR = DATEN_DIR / "faelle"
DB_PFAD = DATEN_DIR / "gesetze.sqlite3"
SCHLUESSEL_PFAD = DATEN_DIR / "schluessel.key"
FEHLERLOG_PFAD = DATEN_DIR / "fehlerlog.jsonl"
LOESCHPROTOKOLL_PFAD = DATEN_DIR / "loeschprotokoll.jsonl"

# Upload-Limits
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_ANALYSE_DOKUMENTE_PRO_STAPEL = 20

# Erlaubte Formate: Endung -> (Beschreibung, Zielordner)
ERLAUBTE_ENDUNGEN = {
    ".pdf":  ("PDF-Dokument", "dokumente"),
    ".docx": ("Word-Dokument", "dokumente"),
    ".doc":  ("Word-Dokument (alt)", "dokumente"),
    ".jpg":  ("Foto/Scan", "dokumente"),
    ".jpeg": ("Foto/Scan", "dokumente"),
    ".png":  ("Foto/Scan", "dokumente"),
    ".eml":  ("E-Mail", "kommunikation"),
    ".msg":  ("Outlook-Nachricht", "kommunikation"),
    ".txt":  ("Textdatei", "dokumente"),
}

# Magic Bytes je Endung (None = textbasiert, kein fester Header)
MAGIC_BYTES = {
    ".pdf":  [b"%PDF"],
    ".docx": [b"PK\x03\x04"],
    ".doc":  [b"\xd0\xcf\x11\xe0"],
    ".jpg":  [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".png":  [b"\x89PNG"],
    ".msg":  [b"\xd0\xcf\x11\xe0"],
    ".eml":  None,
    ".txt":  None,
}

RECHTSBEREICHE = [
    "Arbeitsrecht",
    "Privatrecht",
    "Wohnrecht",
    "Firmenrecht – Kleingewerbe & Einzelunternehmer",
    "Firmenrecht – GmbH & e.K.",
]

FALL_STATUS = ("offen", "in_analyse", "analysiert", "unvollstaendig")

BERATUNGSHINWEIS = "Ersetzt keine anwaltliche Beratung."
RDG_HINWEIS = (
    "Nur zur privaten Eigennutzung – Weitergabe von Einschätzungen an Dritte "
    "erfordert vorher eine RDG-Prüfung."
)

# Timeouts / Retries für externe Abhängigkeiten (OCR, KI-API, Importer)
EXTERN_TIMEOUT_SEK = 30
EXTERN_RETRIES = 2

# Mindestlänge extrahierten Texts, unterhalb derer ein Dokument als
# "unleserlich" gilt (statt stiller Fehlanalyse)
OCR_MIN_ZEICHEN = 40


def verzeichnisse_anlegen() -> None:
    DATEN_DIR.mkdir(parents=True, exist_ok=True)
    FAELLE_DIR.mkdir(parents=True, exist_ok=True)
