"""Vorlagen-Modul: lädt die Bibliothek, befüllt Platzhalter, validiert.

Die kursiven App-Hinweise der Bibliothek sind Prüfregeln (z. B.
Schriftformerfordernis § 623 BGB, 12-Monats-Frist § 556 Abs. 3 BGB) –
sie werden hier als Validierungen umgesetzt und NICHT in das Schreiben
übernommen.

Wirkprinzipien bei jeder Generierung: konkretes Fristdatum, Paragraph
direkt beim Anspruch (steht in den Vorlagen selbst), dokumentierte Fakten,
sachlich-bestimmter Ton, Eskalationsstufe einmal am Ende.
"""

import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import faelle, fristen, krypto

BIBLIOTHEK_PFAD = Path(__file__).resolve().parent.parent / "vorlagen-bibliothek.md"

_VORLAGE_KOPF = re.compile(r"^## vorlage: ([a-z0-9\-]+)\s*$", re.MULTILINE)
_TITEL = re.compile(r"^### titel: (.+)$", re.MULTILINE)
_APP_HINWEIS = re.compile(r"^\*App-Hinweis:.*?\*\s*$", re.MULTILINE | re.DOTALL)
_PLATZHALTER = re.compile(r"\[([A-ZÄÖÜ_]+)\]")

STANDARD_FRIST_TAGE = 14


class VorlagenFehler(ValueError):
    pass


def _bibliothek_lesen() -> str:
    if not BIBLIOTHEK_PFAD.exists():
        raise VorlagenFehler("vorlagen-bibliothek.md wurde nicht gefunden.")
    return BIBLIOTHEK_PFAD.read_text(encoding="utf-8")


def alle_vorlagen() -> list[dict]:
    """Parst die Bibliothek in Einzelvorlagen (App-Hinweise entfernt)."""
    text = _bibliothek_lesen()
    treffer = list(_VORLAGE_KOPF.finditer(text))
    vorlagen = []
    for i, kopf in enumerate(treffer):
        ende = treffer[i + 1].start() if i + 1 < len(treffer) else len(text)
        block = text[kopf.end():ende]
        titel_treffer = _TITEL.search(block)
        titel = titel_treffer.group(1).strip() if titel_treffer else kopf.group(1)
        koerper = block[titel_treffer.end():] if titel_treffer else block
        koerper = _APP_HINWEIS.sub("", koerper)
        # Markdown-Auszeichnung entfernen – die Schreiben sind reiner Brieftext
        koerper = koerper.replace("**", "")
        koerper = koerper.replace("\n---", "").strip()
        vorlagen.append({
            "id": kopf.group(1),
            "titel": titel,
            "text": koerper,
            "platzhalter": sorted(set(_PLATZHALTER.findall(koerper))),
        })
    return vorlagen


def vorlage_holen(vorlage_id: str) -> dict:
    for v in alle_vorlagen():
        if v["id"] == vorlage_id:
            return v
    raise VorlagenFehler(f"Vorlage „{vorlage_id}“ existiert nicht.")


# ---------------------------------------------------------------------------
# Prüfregeln aus den App-Hinweisen der Bibliothek
# ---------------------------------------------------------------------------

def _pruefen(vorlage_id: str, werte: dict, heute: date) -> list[str]:
    warnungen: list[str] = []
    if vorlage_id == "eigenkuendigung":
        warnungen.append(
            "Schriftform (§ 623 BGB): Die Kündigung ist NUR mit eigenhändiger "
            "Unterschrift auf Papier wirksam. Nicht per E-Mail, Fax oder Scan "
            "versenden!"
        )
    if vorlage_id == "nebenkosten-widerspruch":
        zugang = fristen.datum_aus_text(werte.get("DATUM_ZUGANG", ""))
        if zugang is None:
            warnungen.append(
                "12-Monats-Frist (§ 556 Abs. 3 BGB): Zugangsdatum der Abrechnung "
                "angeben, damit die Einwendungsfrist geprüft werden kann."
            )
        elif heute > zugang + timedelta(days=365):
            warnungen.append(
                "ACHTUNG: Die 12-Monats-Frist für Einwendungen (§ 556 Abs. 3 BGB) "
                "ist rechnerisch abgelaufen – Erfolgsaussichten anwaltlich prüfen "
                "lassen."
            )
    if vorlage_id == "mietminderung-schimmel":
        quote = werte.get("MINDERUNGSQUOTE", "")
        try:
            if float(quote.replace(",", ".")) > 50:
                warnungen.append(
                    "Minderungsquote über 50 % ist nur in Extremfällen haltbar – "
                    "zu hohe Minderung riskiert Zahlungsverzug und Kündigung "
                    "(§ 543 BGB)."
                )
        except ValueError:
            pass
        if not werte.get("DATUM_MANGEL"):
            warnungen.append(
                "Mängelanzeige muss unverzüglich erfolgen (§ 536c BGB) – Datum "
                "der ersten Anzeige ergänzen."
            )
    if vorlage_id == "fristverlaengerung-gericht":
        warnungen.append(
            "NOTFRISTEN sind nicht verlängerbar (§ 224 Abs. 1 ZPO) – z. B. die "
            "Klagefrist des § 4 KSchG. Vor dem Versand die Fristart prüfen; der "
            "Antrag muss VOR Fristablauf bei Gericht eingehen."
        )
    if vorlage_id == "steuerunterlagen-anforderung":
        warnungen.append(
            "Hinweis: Bei offenen Honoraren kann dem Steuerberater ein "
            "Zurückbehaltungsrecht zustehen. Aufbewahrungsfristen nach § 147 AO: "
            "6, 8 bzw. 10 Jahre."
        )
    if vorlage_id == "werbewiderspruch-dsgvo":
        warnungen.append(
            "Der Widerspruch ist frist- und begründungsfrei (Art. 21 Abs. 2 DSGVO); "
            "Versand per Einschreiben für den Zugangsnachweis empfohlen."
        )
    return warnungen


def generieren(fall_id: str, vorlage_id: str, werte: dict | None = None) -> dict:
    """Befüllt eine Vorlage aus metadaten.json + übergebenen Werten und legt
    das Schreiben verschlüsselt unter vorlagen/ im Fallordner ab."""
    werte = {k.upper(): str(v) for k, v in (werte or {}).items()}
    meta = faelle.fall_holen(fall_id)
    vorlage = vorlage_holen(vorlage_id)
    heute = date.today()

    standard = {
        "VORNAME": meta["vorname"],
        "NACHNAME": meta["nachname"],
        "DATUM_HEUTE": heute.strftime("%d.%m.%Y"),
        "FRIST_DATUM": (heute + timedelta(days=STANDARD_FRIST_TAGE)).strftime("%d.%m.%Y"),
    }
    befuellung = {**standard, **{k: v for k, v in werte.items() if v.strip()}}

    offen: list[str] = []

    def _ersetzen(treffer: re.Match) -> str:
        name = treffer.group(1)
        if name in befuellung:
            return befuellung[name]
        offen.append(name)
        return f"[{name}]"

    text = _PLATZHALTER.sub(_ersetzen, vorlage["text"])
    warnungen = _pruefen(vorlage_id, befuellung, heute)

    zeit = datetime.now(timezone.utc)
    dateiname = f"{zeit.strftime('%Y%m%d-%H%M%S')}_{vorlage_id}.txt.enc"
    ordner = faelle.fall_ordner_holen(fall_id) / "vorlagen"
    ordner.mkdir(parents=True, exist_ok=True)
    (ordner / dateiname).write_bytes(krypto.verschluesseln(text.encode("utf-8")))

    return {
        "vorlage_id": vorlage_id,
        "titel": vorlage["titel"],
        "datei": dateiname,
        "text": text,
        "offene_platzhalter": sorted(set(offen)),
        "warnungen": warnungen,
        "frist_datum": befuellung["FRIST_DATUM"],
        "beratungshinweis": "Ersetzt keine anwaltliche Beratung.",
    }


def schreiben_auflisten(fall_id: str) -> list[dict]:
    ordner = faelle.fall_ordner_holen(fall_id) / "vorlagen"
    if not ordner.is_dir():
        return []
    eintraege = []
    for pfad in sorted(ordner.glob("*.enc")):
        eintraege.append({"datei": pfad.name})
    return eintraege


def schreiben_laden(fall_id: str, datei: str) -> str:
    if "/" in datei or "\\" in datei or ".." in datei or not datei.endswith(".enc"):
        raise VorlagenFehler("Ungültiger Dateiname.")
    pfad = faelle.fall_ordner_holen(fall_id) / "vorlagen" / datei
    if not pfad.is_file():
        raise VorlagenFehler("Schreiben nicht gefunden.")
    return krypto.entschluesseln(pfad.read_bytes()).decode("utf-8")
