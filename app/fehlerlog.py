"""Zentrales Fehlerlog ohne personenbezogene Inhalte.

Vor dem Schreiben werden E-Mail-Adressen, Pfadbestandteile mit Namen und
lange Zahlenfolgen (IBAN/Telefon) maskiert. Kritische Fehler erzeugen
zusätzlich eine Benachrichtigung (abrufbar über die API).
"""

import json
import re
import threading
from datetime import datetime, timezone

from . import config

_lock = threading.Lock()
_benachrichtigungen: list[dict] = []

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_ZAHLEN_RE = re.compile(r"\b[\dA-Z]{2}[\d\s]{8,}\b")
_FALLPFAD_RE = re.compile(r"(faelle/[^/]+/)[^/\s]+")


def _bereinigen(text: str) -> str:
    text = _EMAIL_RE.sub("[email]", text)
    text = _ZAHLEN_RE.sub("[nummer]", text)
    text = _FALLPFAD_RE.sub(r"\1[fall]", text)
    return text


def protokollieren(quelle: str, meldung: str, kritisch: bool = False) -> dict:
    eintrag = {
        "zeitpunkt": datetime.now(timezone.utc).isoformat(),
        "quelle": quelle,
        "meldung": _bereinigen(str(meldung)),
        "kritisch": kritisch,
    }
    config.verzeichnisse_anlegen()
    with _lock:
        with open(config.FEHLERLOG_PFAD, "a", encoding="utf-8") as f:
            f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
        if kritisch:
            _benachrichtigungen.append(eintrag)
    return eintrag


def benachrichtigungen() -> list[dict]:
    with _lock:
        return list(_benachrichtigungen)


def benachrichtigungen_leeren() -> None:
    with _lock:
        _benachrichtigungen.clear()
