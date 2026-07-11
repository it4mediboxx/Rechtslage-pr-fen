"""Fall- und Ordnerverwaltung.

Struktur:
    /faelle/{rechtsbereich}/{nachname}_{vorname}_{fall-id}/
      ├── dokumente/
      ├── kommunikation/
      ├── vorlagen/
      └── metadaten.json

Eingaben werden serverseitig bereinigt (Schutz vor Injection und
Path-Traversal über Ordnernamen).
"""

import json
import re
import secrets
import shutil
import threading
from datetime import datetime, timezone
from pathlib import Path

from . import config, fehlerlog

_lock = threading.Lock()

_NAME_ERLAUBT = re.compile(r"[^A-Za-zÀ-ÿ0-9 \-]")
_EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$")

UNTERORDNER = ("dokumente", "kommunikation", "vorlagen")


class FallFehler(ValueError):
    """Validierungs-/Zustandsfehler mit verständlicher Meldung."""


def name_bereinigen(wert: str, feld: str) -> str:
    """Entfernt Pfad- und Steuerzeichen; verhindert Traversal über Ordnernamen."""
    wert = (wert or "").strip()
    wert = wert.replace("/", "").replace("\\", "").replace("..", "").replace("\x00", "")
    wert = _NAME_ERLAUBT.sub("", wert)
    wert = re.sub(r"\s+", " ", wert).strip()
    if not wert:
        raise FallFehler(f"Bitte einen gültigen Wert für „{feld}“ angeben.")
    if len(wert) > 60:
        wert = wert[:60].strip()
    return wert


def _bereich_slug(rechtsbereich: str) -> str:
    if rechtsbereich not in config.RECHTSBEREICHE:
        raise FallFehler("Unbekannter Rechtsbereich. Bitte aus der Liste wählen.")
    slug = rechtsbereich.lower()
    for alt, neu in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("–", "-")):
        slug = slug.replace(alt, neu)
    slug = re.sub(r"[^a-z0-9]+", "-", slug).strip("-")
    return slug


def _fall_ordner(rechtsbereich: str, nachname: str, vorname: str, fall_id: str) -> Path:
    ordner_name = f"{nachname}_{vorname}_{fall_id}".replace(" ", "-")
    pfad = (config.FAELLE_DIR / _bereich_slug(rechtsbereich) / ordner_name).resolve()
    if config.FAELLE_DIR.resolve() not in pfad.parents:
        raise FallFehler("Ungültiger Fallpfad.")
    return pfad


def fall_anlegen(vorname: str, nachname: str, email: str, rechtsbereich: str,
                 beschreibung: str = "") -> dict:
    vorname = name_bereinigen(vorname, "Vorname")
    nachname = name_bereinigen(nachname, "Nachname")
    email = (email or "").strip()
    if email and not _EMAIL_RE.match(email):
        raise FallFehler("Die E-Mail-Adresse ist ungültig.")
    fall_id = datetime.now().strftime("%Y%m%d") + "-" + secrets.token_hex(3)
    ordner = _fall_ordner(rechtsbereich, nachname, vorname, fall_id)
    with _lock:
        for unter in UNTERORDNER:
            (ordner / unter).mkdir(parents=True, exist_ok=True)
        metadaten = {
            "fall_id": fall_id,
            "vorname": vorname,
            "nachname": nachname,
            "email": email,
            "rechtsbereich": rechtsbereich,
            "beschreibung": (beschreibung or "").strip()[:2000],
            "erstellungsdatum": datetime.now(timezone.utc).isoformat(),
            "status": "offen",
        }
        _metadaten_schreiben(ordner, metadaten)
    return metadaten


def _metadaten_schreiben(ordner: Path, metadaten: dict) -> None:
    (ordner / "metadaten.json").write_text(
        json.dumps(metadaten, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _metadaten_lesen(ordner: Path) -> dict | None:
    pfad = ordner / "metadaten.json"
    if not pfad.exists():
        return None
    try:
        return json.loads(pfad.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        fehlerlog.protokollieren("faelle", f"metadaten.json unlesbar: {exc}")
        return None


def alle_faelle() -> list[dict]:
    faelle = []
    if not config.FAELLE_DIR.exists():
        return faelle
    for bereich in sorted(config.FAELLE_DIR.iterdir()):
        if not bereich.is_dir():
            continue
        for ordner in sorted(bereich.iterdir()):
            meta = _metadaten_lesen(ordner)
            if meta:
                meta["dokumente_anzahl"] = _anzahl_dateien(ordner)
                faelle.append(meta)
    faelle.sort(key=lambda m: m.get("erstellungsdatum", ""), reverse=True)
    return faelle


def _anzahl_dateien(ordner: Path) -> int:
    anzahl = 0
    for unter in ("dokumente", "kommunikation"):
        pfad = ordner / unter
        if pfad.is_dir():
            anzahl += sum(1 for p in pfad.iterdir() if p.is_file() and not p.name.endswith(".meta.json"))
    return anzahl


def fall_ordner_holen(fall_id: str) -> Path:
    if not re.fullmatch(r"[0-9]{8}-[0-9a-f]{6}", fall_id or ""):
        raise FallFehler("Ungültige Fall-ID.")
    if config.FAELLE_DIR.exists():
        for bereich in config.FAELLE_DIR.iterdir():
            if not bereich.is_dir():
                continue
            for ordner in bereich.iterdir():
                if ordner.name.endswith(f"_{fall_id}") and ordner.is_dir():
                    return ordner
    raise FallFehler("Fall nicht gefunden.")


def fall_holen(fall_id: str) -> dict:
    ordner = fall_ordner_holen(fall_id)
    meta = _metadaten_lesen(ordner)
    if meta is None:
        raise FallFehler("Metadaten des Falls sind beschädigt.")
    meta["dokumente_anzahl"] = _anzahl_dateien(ordner)
    return meta


def status_setzen(fall_id: str, status: str) -> dict:
    if status not in config.FALL_STATUS:
        raise FallFehler("Ungültiger Status.")
    ordner = fall_ordner_holen(fall_id)
    with _lock:
        meta = _metadaten_lesen(ordner)
        if meta is None:
            raise FallFehler("Metadaten des Falls sind beschädigt.")
        meta["status"] = status
        _metadaten_schreiben(ordner, meta)
    return meta


def fall_loeschen(fall_id: str) -> dict:
    """Vollständige, protokollierte Löschung eines Falls."""
    ordner = fall_ordner_holen(fall_id)
    anzahl = sum(1 for p in ordner.rglob("*") if p.is_file())
    with _lock:
        shutil.rmtree(ordner)
        eintrag = {
            "zeitpunkt": datetime.now(timezone.utc).isoformat(),
            "fall_id": fall_id,
            "geloeschte_dateien": anzahl,
        }
        config.verzeichnisse_anlegen()
        with open(config.LOESCHPROTOKOLL_PFAD, "a", encoding="utf-8") as f:
            f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")
    return eintrag
