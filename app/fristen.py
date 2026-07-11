"""Fristen- und Zusagen-Extraktion aus Dokumenten und Kommunikation.

Erkennt deutsche Datumsangaben im Umfeld von Frist-/Zusage-Formulierungen,
ordnet sie chronologisch als Zeitleiste und versieht Fristen mit Warnstufen.
Gesetzliche Notfristen (z. B. 3-Wochen-Frist des § 4 KSchG) werden von
sonstigen (z. B. richterlichen) Fristen unterschieden.
"""

import re
from datetime import date, datetime, timedelta

_MONATE = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5,
    "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10,
    "november": 11, "dezember": 12,
}

_DATUM_NUM = re.compile(r"\b(\d{1,2})\.(\d{1,2})\.(\d{2,4})\b")
_DATUM_WORT = re.compile(
    r"\b(\d{1,2})\.?\s+(januar|februar|märz|maerz|april|mai|juni|juli|august|"
    r"september|oktober|november|dezember)\s+(\d{4})\b", re.IGNORECASE)

_FRIST_SIGNALE = ("frist", "bis zum", "bis spätestens", "spätestens", "zahlbar bis",
                  "einzureichen bis", "zu zahlen bis", "letztmalig", "innerhalb von",
                  "kündigungsfrist", "zum ablauf", "widerspruch bis")
_ZUSAGE_SIGNALE = ("zusage", "zugesagt", "wir werden", "ich werde", "versprochen",
                   "verpflichten uns", "sagen zu", "wird erledigt", "kümmern uns")
_NOTFRIST_SIGNALE = ("kündigungsschutzklage", "drei wochen", "3 wochen", "notfrist",
                     "§ 4 kschg", "klagefrist")


def _datum_parsen(treffer: re.Match, wortform: bool) -> date | None:
    try:
        if wortform:
            tag = int(treffer.group(1))
            monat = _MONATE[treffer.group(2).lower()]
            jahr = int(treffer.group(3))
        else:
            tag, monat, jahr = (int(treffer.group(i)) for i in (1, 2, 3))
            if jahr < 100:
                jahr += 2000
        return date(jahr, monat, tag)
    except (ValueError, KeyError):
        return None


def warnstufe(frist_datum: date, heute: date | None = None) -> str:
    heute = heute or date.today()
    tage = (frist_datum - heute).days
    if tage < 0:
        return "überfällig"
    if tage <= 7:
        return "kritisch"
    if tage <= 30:
        return "bald"
    return "ok"


def _kontext(text: str, start: int, ende: int, radius: int = 90) -> str:
    ausschnitt = text[max(0, start - radius): ende + radius]
    return " ".join(ausschnitt.split())


def fristen_extrahieren(text: str, quelle: str = "", heute: date | None = None) -> list[dict]:
    """Findet Fristen und Zusagen mit Datumsbezug im Text.

    Frist-Signale zählen nur VOR dem Datum („Frist bis zum 31.07.“) – sonst
    würden erzählende Datumsangaben („Seit dem 01.06. … später eine Frist …“)
    fälschlich als überfällige Fristen erscheinen. Zusagen dürfen auch nach
    dem Datum stehen („… bis zum 15.07. beheben, das ist zugesagt“).
    """
    eintraege: list[dict] = []
    gesehen: set[tuple[str, str]] = set()
    for muster, wortform in ((_DATUM_NUM, False), (_DATUM_WORT, True)):
        for treffer in muster.finditer(text or ""):
            datum = _datum_parsen(treffer, wortform)
            if datum is None:
                continue
            kontext = _kontext(text, treffer.start(), treffer.end())
            klein = kontext.lower()
            davor = " ".join(text[max(0, treffer.start() - 70):treffer.start()].split()).lower()
            ist_frist = any(s in davor for s in _FRIST_SIGNALE)
            ist_zusage = any(s in klein for s in _ZUSAGE_SIGNALE)
            if not (ist_frist or ist_zusage):
                continue
            art = "Frist" if ist_frist else "Zusage"
            schluessel = (datum.isoformat(), art)
            if schluessel in gesehen:
                continue
            gesehen.add(schluessel)
            eintrag = {
                "datum": datum.isoformat(),
                "art": art,
                "kontext": kontext,
                "quelle": quelle,
            }
            if art == "Frist":
                eintrag["warnstufe"] = warnstufe(datum, heute)
                eintrag["notfrist"] = any(s in klein for s in _NOTFRIST_SIGNALE)
            eintraege.append(eintrag)
    return eintraege


def zeitleiste(alle_eintraege: list[dict]) -> list[dict]:
    """Chronologische Zeitleiste; Fristen nach Dringlichkeit markiert."""
    return sorted(alle_eintraege, key=lambda e: e["datum"])


def kschg_klagefrist(zugang_kuendigung: date) -> dict:
    """Berechnet die 3-Wochen-Notfrist des § 4 KSchG ab Zugang der Kündigung."""
    frist = zugang_kuendigung + timedelta(weeks=3)
    return {
        "datum": frist.isoformat(),
        "art": "Frist",
        "kontext": "Kündigungsschutzklage: 3 Wochen ab Zugang der schriftlichen "
                   "Kündigung (§ 4 KSchG) – gesetzliche Notfrist, nicht verlängerbar.",
        "quelle": "berechnet",
        "warnstufe": warnstufe(frist),
        "notfrist": True,
    }


def datum_aus_text(text: str) -> date | None:
    """Erstes plausibles Datum im Text (z. B. Datum eines Schreibens)."""
    for muster, wortform in ((_DATUM_NUM, False), (_DATUM_WORT, True)):
        treffer = muster.search(text or "")
        if treffer:
            datum = _datum_parsen(treffer, wortform)
            if datum and 2000 <= datum.year <= datetime.now().year + 5:
                return datum
    return None
