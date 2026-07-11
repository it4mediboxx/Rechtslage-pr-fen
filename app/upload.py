"""Upload-Validierung und verschlüsselte Ablage.

Je Upload: Dateityp (Endung + Magic Bytes), Maximalgröße, Virenscan.
Bei Ablehnung gibt es eine verständliche Fehlermeldung. Dateien werden
verschlüsselt (Endung ``.enc``) abgelegt; daneben liegt eine kleine
``.meta.json`` mit Originalname, Typ und Upload-Zeitpunkt.
"""

import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from . import config, faelle, fehlerlog, krypto

# EICAR-Testsignatur – Standard zum Testen von Virenscannern
_EICAR = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"


class UploadFehler(ValueError):
    """Abgelehnter Upload mit verständlicher Begründung."""


def _endung(dateiname: str) -> str:
    return Path(dateiname).suffix.lower()


def _dateiname_bereinigen(dateiname: str) -> str:
    name = Path(dateiname or "datei").name
    name = name.replace("\x00", "")
    name = re.sub(r"[^\w.\- ÄÖÜäöüß]", "_", name)
    return name[:120] or "datei"


def _virenscan(inhalt: bytes, dateiname: str) -> None:
    if _EICAR in inhalt:
        raise UploadFehler(
            f"„{dateiname}“ wurde vom Virenscan abgelehnt (Testsignatur erkannt)."
        )
    clamscan = shutil.which("clamscan")
    if clamscan:
        try:
            ergebnis = subprocess.run(
                [clamscan, "--no-summary", "-"], input=inhalt,
                capture_output=True, timeout=config.EXTERN_TIMEOUT_SEK,
            )
            if ergebnis.returncode == 1:
                raise UploadFehler(f"„{dateiname}“ wurde vom Virenscan abgelehnt.")
        except (subprocess.TimeoutExpired, OSError) as exc:
            # Scanner nicht verfügbar/hängt: Signaturprüfung oben bleibt aktiv
            fehlerlog.protokollieren("upload", f"clamscan nicht nutzbar: {exc}")


def validieren(dateiname: str, inhalt: bytes) -> str:
    """Prüft Typ, Größe und Virenfreiheit. Liefert die normalisierte Endung."""
    endung = _endung(dateiname)
    if endung not in config.ERLAUBTE_ENDUNGEN:
        erlaubt = ", ".join(sorted(config.ERLAUBTE_ENDUNGEN))
        raise UploadFehler(
            f"Der Dateityp „{endung or 'ohne Endung'}“ wird nicht unterstützt. "
            f"Erlaubt sind: {erlaubt}."
        )
    if len(inhalt) == 0:
        raise UploadFehler(f"„{dateiname}“ ist leer.")
    if len(inhalt) > config.MAX_UPLOAD_BYTES:
        mb = config.MAX_UPLOAD_BYTES // (1024 * 1024)
        raise UploadFehler(
            f"„{dateiname}“ ist zu groß ({len(inhalt) / 1024 / 1024:.1f} MB). "
            f"Maximal erlaubt sind {mb} MB."
        )
    magic = config.MAGIC_BYTES.get(endung)
    if magic is not None and not any(inhalt.startswith(m) for m in magic):
        raise UploadFehler(
            f"„{dateiname}“ sieht nicht wie eine gültige {endung}-Datei aus "
            f"(Dateikopf passt nicht zum Typ). Bitte die Originaldatei hochladen."
        )
    _virenscan(inhalt, dateiname)
    return endung


def speichern(fall_id: str, dateiname: str, inhalt: bytes) -> dict:
    """Validiert und legt die Datei verschlüsselt im richtigen Unterordner ab."""
    endung = validieren(dateiname, inhalt)
    _, zielordner = config.ERLAUBTE_ENDUNGEN[endung]
    ordner = faelle.fall_ordner_holen(fall_id) / zielordner
    ordner.mkdir(parents=True, exist_ok=True)

    sauber = _dateiname_bereinigen(dateiname)
    zeitstempel = datetime.now(timezone.utc)
    basis = f"{zeitstempel.strftime('%Y%m%d-%H%M%S')}_{sauber}"
    ziel = ordner / f"{basis}.enc"
    zaehler = 1
    while ziel.exists():
        ziel = ordner / f"{basis}.{zaehler}.enc"
        zaehler += 1

    ziel.write_bytes(krypto.verschluesseln(inhalt))
    meta = {
        "originalname": sauber,
        "endung": endung,
        "typ": config.ERLAUBTE_ENDUNGEN[endung][0],
        "groesse_bytes": len(inhalt),
        "hochgeladen": zeitstempel.isoformat(),
        "ordner": zielordner,
        "datei": ziel.name,
    }
    ziel.with_suffix(".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta


def dokumente_auflisten(fall_id: str) -> list[dict]:
    ordner = faelle.fall_ordner_holen(fall_id)
    eintraege = []
    for unter in ("dokumente", "kommunikation"):
        pfad = ordner / unter
        if not pfad.is_dir():
            continue
        for meta_datei in sorted(pfad.glob("*.meta.json")):
            try:
                eintraege.append(json.loads(meta_datei.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError) as exc:
                fehlerlog.protokollieren("upload", f"Meta-Datei unlesbar: {exc}")
    eintraege.sort(key=lambda e: e.get("hochgeladen", ""))
    return eintraege


def inhalt_laden(fall_id: str, datei: str) -> tuple[dict, bytes]:
    """Lädt und entschlüsselt eine abgelegte Datei anhand des .enc-Namens."""
    if "/" in datei or "\\" in datei or ".." in datei or not datei.endswith(".enc"):
        raise UploadFehler("Ungültiger Dateiname.")
    ordner = faelle.fall_ordner_holen(fall_id)
    for unter in ("dokumente", "kommunikation"):
        pfad = ordner / unter / datei
        if pfad.is_file():
            meta_pfad = pfad.with_suffix(".meta.json")
            meta = json.loads(meta_pfad.read_text(encoding="utf-8")) if meta_pfad.exists() else {}
            return meta, krypto.entschluesseln(pfad.read_bytes())
    raise UploadFehler("Datei nicht gefunden.")
