"""Import/Update aktueller Gesetzesfassungen von gesetze-im-internet.de.

Der Importer lädt die amtliche XML-Fassung eines Gesetzes, extrahiert die in
der Datenbank vorhandenen Paragraphen und aktualisiert sie über
``datenbank.aktualisieren`` – jede Änderung landet damit im Diff-Protokoll.
Netzwerkzugriffe laufen mit Timeout und Retry; ohne Netz bleibt der
Seed-Stand unverändert bestehen.
"""

import io
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import date

import httpx

from . import config, datenbank, fehlerlog

# Kürzel -> Pfadsegment auf gesetze-im-internet.de
_GII_PFADE = {
    "BGB": "bgb", "KSchG": "kschg", "ArbZG": "arbzg", "BUrlG": "burlg",
    "EFZG": "entgfg", "GewO": "gewo", "BetrKV": "betrkv", "UStG": "ustg_1980",
    "HGB": "hgb", "GmbHG": "gmbhg", "ZPO": "zpo", "AO": "ao_1977",
}


def _xml_laden(kuerzel: str) -> ET.Element | None:
    pfad = _GII_PFADE.get(kuerzel)
    if pfad is None:
        return None
    url = f"https://www.gesetze-im-internet.de/{pfad}/xml.zip"
    letzter_fehler: Exception | None = None
    for versuch in range(config.EXTERN_RETRIES + 1):
        try:
            antwort = httpx.get(url, timeout=config.EXTERN_TIMEOUT_SEK, follow_redirects=True)
            antwort.raise_for_status()
            with zipfile.ZipFile(io.BytesIO(antwort.content)) as z:
                xml_namen = [n for n in z.namelist() if n.endswith(".xml")]
                if not xml_namen:
                    return None
                return ET.fromstring(z.read(xml_namen[0]))
        except Exception as exc:  # Netzwerk-/Parsefehler: Retry mit Backoff
            letzter_fehler = exc
            time.sleep(2 ** versuch)
    fehlerlog.protokollieren("importer", f"Download {kuerzel} fehlgeschlagen: {letzter_fehler}")
    return None


def _norm_text(norm: ET.Element) -> str:
    teil = norm.find(".//textdaten/text/Content")
    if teil is None:
        return ""
    return " ".join("".join(teil.itertext()).split())


def gesetz_aktualisieren(kuerzel: str) -> int:
    """Aktualisiert alle DB-Paragraphen eines Gesetzes gegen die Online-Fassung."""
    wurzel = _xml_laden(kuerzel)
    if wurzel is None:
        return 0
    vorhandene = {
        e["paragraph"]: e for e in datenbank.alle_paragraphen()
        if e["gesetz_kuerzel"] == kuerzel
    }
    stand = f"Online-Import {date.today().strftime('%d.%m.%Y')}"
    aktualisiert: list[dict] = []
    for norm in wurzel.iter("norm"):
        enbez = norm.findtext(".//metadaten/enbez") or ""
        if enbez not in vorhandene:
            continue
        volltext = _norm_text(norm)
        titel = norm.findtext(".//metadaten/titel") or vorhandene[enbez]["titel"]
        if not volltext:
            continue
        eintrag = dict(vorhandene[enbez])
        eintrag.update(volltext=volltext, titel=" ".join(titel.split()), fassung_stand=stand)
        aktualisiert.append(eintrag)
    return datenbank.aktualisieren(aktualisiert)


def alle_aktualisieren() -> dict[str, int]:
    """Regelmäßiger Update-Lauf über alle bekannten Gesetze."""
    ergebnis: dict[str, int] = {}
    for kuerzel in _GII_PFADE:
        try:
            ergebnis[kuerzel] = gesetz_aktualisieren(kuerzel)
        except Exception as exc:
            fehlerlog.protokollieren("importer", f"Update {kuerzel}: {exc}", kritisch=True)
            ergebnis[kuerzel] = -1
    return ergebnis
