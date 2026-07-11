"""Gesetzesdatenbank: SQLite + FTS5-Volltextindex, Caching, Diff-Protokoll.

Jede Analyse zitiert ausschließlich Paragraphen aus dieser Datenbank
(inkl. Fassungsstand) – nie aus statischem Modellwissen.
"""

import difflib
import re
import sqlite3
import threading
from datetime import datetime, timezone

from . import config
from .gesetze_seed import GESETZE_SEED

_lock = threading.Lock()
_verbindung: sqlite3.Connection | None = None
_cache: dict[tuple[str, str], dict] = {}
_CACHE_MAX = 256


def _verbinden() -> sqlite3.Connection:
    global _verbindung
    if _verbindung is None:
        config.verzeichnisse_anlegen()
        _verbindung = sqlite3.connect(config.DB_PFAD, check_same_thread=False)
        _verbindung.row_factory = sqlite3.Row
        _schema_anlegen(_verbindung)
    return _verbindung


def _schema_anlegen(con: sqlite3.Connection) -> None:
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS gesetze (
            id            INTEGER PRIMARY KEY,
            gesetz_kuerzel TEXT NOT NULL,
            paragraph     TEXT NOT NULL,
            titel         TEXT NOT NULL,
            volltext      TEXT NOT NULL,
            fassung_stand TEXT NOT NULL,
            quelle_url    TEXT NOT NULL,
            UNIQUE (gesetz_kuerzel, paragraph)
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS gesetze_fts USING fts5(
            gesetz_kuerzel, paragraph, titel, volltext,
            content='gesetze', content_rowid='id',
            tokenize='unicode61 remove_diacritics 2'
        );
        CREATE TRIGGER IF NOT EXISTS gesetze_ai AFTER INSERT ON gesetze BEGIN
            INSERT INTO gesetze_fts(rowid, gesetz_kuerzel, paragraph, titel, volltext)
            VALUES (new.id, new.gesetz_kuerzel, new.paragraph, new.titel, new.volltext);
        END;
        CREATE TRIGGER IF NOT EXISTS gesetze_ad AFTER DELETE ON gesetze BEGIN
            INSERT INTO gesetze_fts(gesetze_fts, rowid, gesetz_kuerzel, paragraph, titel, volltext)
            VALUES ('delete', old.id, old.gesetz_kuerzel, old.paragraph, old.titel, old.volltext);
        END;
        CREATE TRIGGER IF NOT EXISTS gesetze_au AFTER UPDATE ON gesetze BEGIN
            INSERT INTO gesetze_fts(gesetze_fts, rowid, gesetz_kuerzel, paragraph, titel, volltext)
            VALUES ('delete', old.id, old.gesetz_kuerzel, old.paragraph, old.titel, old.volltext);
            INSERT INTO gesetze_fts(rowid, gesetz_kuerzel, paragraph, titel, volltext)
            VALUES (new.id, new.gesetz_kuerzel, new.paragraph, new.titel, new.volltext);
        END;
        CREATE TABLE IF NOT EXISTS update_protokoll (
            id INTEGER PRIMARY KEY,
            zeitpunkt TEXT NOT NULL,
            gesetz_kuerzel TEXT NOT NULL,
            paragraph TEXT NOT NULL,
            aenderung TEXT NOT NULL,   -- 'neu' | 'geaendert' | 'entfernt'
            diff TEXT NOT NULL DEFAULT ''
        );
        """
    )
    con.commit()


def initialisieren() -> int:
    """Seed-Daten einspielen (idempotent). Liefert Anzahl neuer/aktualisierter Einträge."""
    with _lock:
        con = _verbinden()
        anzahl = 0
        for eintrag in GESETZE_SEED:
            anzahl += _upsert(con, eintrag)
        con.commit()
    return anzahl


def _upsert(con: sqlite3.Connection, eintrag: dict) -> int:
    """Einfügen oder aktualisieren; Änderungen werden mit Diff protokolliert."""
    alt = con.execute(
        "SELECT * FROM gesetze WHERE gesetz_kuerzel=? AND paragraph=?",
        (eintrag["gesetz_kuerzel"], eintrag["paragraph"]),
    ).fetchone()
    jetzt = datetime.now(timezone.utc).isoformat()
    if alt is None:
        con.execute(
            "INSERT INTO gesetze (gesetz_kuerzel, paragraph, titel, volltext, fassung_stand, quelle_url)"
            " VALUES (?,?,?,?,?,?)",
            (eintrag["gesetz_kuerzel"], eintrag["paragraph"], eintrag["titel"],
             eintrag["volltext"], eintrag["fassung_stand"], eintrag["quelle_url"]),
        )
        con.execute(
            "INSERT INTO update_protokoll (zeitpunkt, gesetz_kuerzel, paragraph, aenderung) VALUES (?,?,?,?)",
            (jetzt, eintrag["gesetz_kuerzel"], eintrag["paragraph"], "neu"),
        )
        return 1
    if alt["volltext"] != eintrag["volltext"] or alt["titel"] != eintrag["titel"]:
        diff = "\n".join(difflib.unified_diff(
            alt["volltext"].splitlines(), eintrag["volltext"].splitlines(),
            fromfile=f"alt ({alt['fassung_stand']})",
            tofile=f"neu ({eintrag['fassung_stand']})", lineterm="",
        ))
        con.execute(
            "UPDATE gesetze SET titel=?, volltext=?, fassung_stand=?, quelle_url=?"
            " WHERE gesetz_kuerzel=? AND paragraph=?",
            (eintrag["titel"], eintrag["volltext"], eintrag["fassung_stand"],
             eintrag["quelle_url"], eintrag["gesetz_kuerzel"], eintrag["paragraph"]),
        )
        con.execute(
            "INSERT INTO update_protokoll (zeitpunkt, gesetz_kuerzel, paragraph, aenderung, diff)"
            " VALUES (?,?,?,?,?)",
            (jetzt, eintrag["gesetz_kuerzel"], eintrag["paragraph"], "geaendert", diff),
        )
        _cache.pop((eintrag["gesetz_kuerzel"], eintrag["paragraph"]), None)
        return 1
    return 0


def aktualisieren(eintraege: list[dict]) -> int:
    """Öffentlicher Update-Pfad (z. B. für den Importer). Mit Diff-Protokoll."""
    with _lock:
        con = _verbinden()
        anzahl = sum(_upsert(con, e) for e in eintraege)
        con.commit()
    return anzahl


def _zeile_zu_dict(zeile: sqlite3.Row) -> dict:
    return {
        "gesetz_kuerzel": zeile["gesetz_kuerzel"],
        "paragraph": zeile["paragraph"],
        "titel": zeile["titel"],
        "volltext": zeile["volltext"],
        "fassung_stand": zeile["fassung_stand"],
        "quelle_url": zeile["quelle_url"],
    }


def paragraph_holen(kuerzel: str, paragraph: str) -> dict | None:
    """Einzelabfrage mit Cache für häufige Paragraphen."""
    schluessel = (kuerzel, paragraph)
    if schluessel in _cache:
        return _cache[schluessel]
    with _lock:
        con = _verbinden()
        zeile = con.execute(
            "SELECT * FROM gesetze WHERE gesetz_kuerzel=? AND paragraph=?", schluessel
        ).fetchone()
    if zeile is None:
        return None
    ergebnis = _zeile_zu_dict(zeile)
    if len(_cache) >= _CACHE_MAX:
        _cache.pop(next(iter(_cache)))
    _cache[schluessel] = ergebnis
    return ergebnis


_FTS_SONDERZEICHEN = re.compile(r'["\'^*():{}\[\]]')


def volltextsuche(anfrage: str, limit: int = 20) -> list[dict]:
    """FTS5-Suche, bm25-sortiert. Sonderzeichen werden neutralisiert."""
    anfrage = _FTS_SONDERZEICHEN.sub(" ", anfrage).strip()
    if not anfrage:
        return []
    fts_anfrage = " ".join(f'"{wort}"' for wort in anfrage.split())
    with _lock:
        con = _verbinden()
        zeilen = con.execute(
            "SELECT g.* FROM gesetze_fts f JOIN gesetze g ON g.id = f.rowid"
            " WHERE gesetze_fts MATCH ? ORDER BY bm25(gesetze_fts) LIMIT ?",
            (fts_anfrage, limit),
        ).fetchall()
    return [_zeile_zu_dict(z) for z in zeilen]


def alle_paragraphen() -> list[dict]:
    with _lock:
        con = _verbinden()
        zeilen = con.execute(
            "SELECT * FROM gesetze ORDER BY gesetz_kuerzel, paragraph"
        ).fetchall()
    return [_zeile_zu_dict(z) for z in zeilen]


def update_protokoll(limit: int = 100) -> list[dict]:
    with _lock:
        con = _verbinden()
        zeilen = con.execute(
            "SELECT zeitpunkt, gesetz_kuerzel, paragraph, aenderung, diff"
            " FROM update_protokoll ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(z) for z in zeilen]


def schliessen() -> None:
    """Verbindung schließen (für Tests mit wechselnden Datenverzeichnissen)."""
    global _verbindung
    with _lock:
        if _verbindung is not None:
            _verbindung.close()
            _verbindung = None
        _cache.clear()
