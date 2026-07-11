"""Automatische Dokumenttyp-Erkennung mit Plausibilitätscheck.

Erkennt aus dem extrahierten Text den Dokumenttyp (Vertrag, Kündigung,
Bescheid, …) und prüft, ob der Typ zum gewählten Rechtsbereich passt.
Bei Widerspruch wird ein Warnhinweis erzeugt – die Datei bleibt gespeichert.
"""

import re

# Reihenfolge = Priorität (spezifisch vor allgemein)
_TYP_MUSTER: list[tuple[str, list[str]]] = [
    ("Kündigung", [r"\bkündig", r"\bkuendig", r"beendigung des (arbeits|miet)verhältnisses"]),
    ("Abmahnung", [r"\babmahnung\b", r"\babgemahnt\b", r"unterlassungserklärung"]),
    ("Mängelanzeige", [r"mängelanzeige", r"maengelanzeige", r"mangel.{0,60}anzeigen?\b"]),
    ("Mahnung", [r"\bmahnung\b", r"zahlungserinnerung", r"letzte aufforderung"]),
    ("Bescheid", [r"\bbescheid\b", r"widerspruchsbelehrung", r"rechtsbehelfsbelehrung"]),
    ("Nebenkostenabrechnung", [r"nebenkostenabrechnung", r"betriebskostenabrechnung",
                               r"abrechnungszeitraum"]),
    ("Rechnung", [r"\brechnung\b", r"rechnungsnummer", r"\bnetto\b.*\bbrutto\b",
                  r"umsatzsteuer", r"zahlbar (bis|innerhalb)"]),
    ("Arbeitsvertrag", [r"arbeitsvertrag", r"\banstellungsvertrag\b"]),
    ("Mietvertrag", [r"mietvertrag", r"\bmietsache\b", r"\bkaltmiete\b"]),
    ("Vertrag", [r"\bvertrag\b", r"vertragspartner", r"\bvereinbarung\b"]),
    ("Zeugnis", [r"arbeitszeugnis", r"\bzeugnis\b"]),
    ("Lohnabrechnung", [r"lohnabrechnung", r"gehaltsabrechnung", r"entgeltabrechnung"]),
]

# Welche Typen sind je Rechtsbereich plausibel?
_PLAUSIBEL: dict[str, set[str]] = {
    "Arbeitsrecht": {"Kündigung", "Abmahnung", "Arbeitsvertrag", "Vertrag", "Zeugnis",
                     "Lohnabrechnung", "Mahnung", "Sonstiges"},
    "Privatrecht": {"Vertrag", "Rechnung", "Mahnung", "Bescheid", "Abmahnung",
                    "Kündigung", "Mängelanzeige", "Sonstiges"},
    "Wohnrecht": {"Mietvertrag", "Nebenkostenabrechnung", "Mängelanzeige", "Kündigung",
                  "Mahnung", "Abmahnung", "Vertrag", "Sonstiges"},
    "Firmenrecht – Kleingewerbe & Einzelunternehmer":
        {"Rechnung", "Vertrag", "Bescheid", "Mahnung", "Kündigung", "Abmahnung", "Sonstiges"},
    "Firmenrecht – GmbH & e.K.":
        {"Rechnung", "Vertrag", "Bescheid", "Mahnung", "Kündigung", "Abmahnung", "Sonstiges"},
}


def typ_erkennen(text: str) -> str:
    klein = (text or "").lower()
    for typ, muster in _TYP_MUSTER:
        if any(re.search(m, klein) for m in muster):
            return typ
    return "Sonstiges"


def plausibilitaet_pruefen(typ: str, rechtsbereich: str) -> str | None:
    """Liefert einen Warnhinweis, wenn Typ und Rechtsbereich nicht zusammenpassen."""
    plausibel = _PLAUSIBEL.get(rechtsbereich, set())
    if typ in plausibel or typ == "Sonstiges":
        return None
    return (
        f"Achtung: Das Dokument wurde als „{typ}“ erkannt, was untypisch für den "
        f"Rechtsbereich „{rechtsbereich}“ ist. Bitte prüfen, ob der Fall im "
        f"richtigen Bereich angelegt wurde."
    )
