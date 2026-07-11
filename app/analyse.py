"""Analyse-Komponente.

Prüft einen Fall anhand der hochgeladenen Dokumente, Nachweise und
Kommunikation sowie der Gesetzestexte aus der Datenbank. Zitiert
AUSSCHLIESSLICH Paragraphen aus der Datenbank inkl. Fassungsdatum –
nie aus statischem Modellwissen.

Läuft asynchron mit Fortschrittsanzeige; abgebrochene Analysen markieren
den Fall als "unvollständig" und sind erneut anstoßbar (kein Datenverlust).
Optional wird eine KI-Einschätzung über die Anthropic-API eingeholt
(Umgebungsvariable ANTHROPIC_API_KEY); fällt sie aus, trägt die
regelbasierte Auswertung das Ergebnis allein.
"""

import json
import os
import re
import threading
import time
from datetime import datetime, timezone

from . import config, datenbank, doktyp, extraktion, faelle, fehlerlog, fristen, krypto, upload

SYSTEM_INSTRUKTION = """Du prüfst einen Fall im Bereich {rechtsbereich} anhand der hochgeladenen Dokumente, Nachweise und Kommunikation sowie der Gesetzestexte aus der Datenbank. Vorgehen:
1. Sachverhalt vollständig erfassen; fehlende Fakten explizit benennen
2. ALLE potenziell einschlägigen Paragraphen identifizieren, auch bereichsübergreifend (z. B. Kündigung arbeits- UND vertragsrechtlich)
3. Ausnahmen und Sonderregeln prüfen (Kleinunternehmerregelung, Kündigungsfristen nach Betriebszugehörigkeit, Kaufmannseigenschaft § 1 vs. § 2 HGB, Ausschlussfristen in Arbeits-/Tarifverträgen, Formvorschriften wie § 623 BGB)
4. Chancen und Risiken realistisch gewichten; Beweislücken benennen statt übergehen
5. Fristen konkret nennen, nach Dringlichkeit ordnen; gesetzliche Notfristen von richterlichen Fristen unterscheiden
6. Unklarheiten explizit machen statt zu raten
7. Bei komplexen oder folgenreichen Fällen anwaltliche Prüfung empfehlen
Zitiere ausschließlich die dir übergebenen Paragraphen aus der Datenbank (mit Fassungsdatum), niemals eigenes Modellwissen."""

# ---------------------------------------------------------------------------
# Regelwerk: Trigger -> einschlägige Paragraphen (nur DB-Referenzen), Chancen,
# Risiken, Ausnahmen/Sonderregeln, fehlende Fakten, Vorlagen-Vorschlag
# ---------------------------------------------------------------------------

def _r(thema, trigger, paragraphen, chancen="", risiken="", ausnahmen=(),
       fakten=(), vorlage=None, bereiche=()):
    return {
        "thema": thema,
        "trigger": [re.compile(t, re.IGNORECASE) for t in trigger],
        "paragraphen": paragraphen,
        "chancen": chancen,
        "risiken": risiken,
        "ausnahmen": list(ausnahmen),
        "fakten": list(fakten),
        "vorlage": vorlage,
        "bereiche": list(bereiche) or list(config.RECHTSBEREICHE),
    }


_REGELN: list[dict] = [
    # --- Arbeitsrecht ---------------------------------------------------
    _r("Kündigung des Arbeitsverhältnisses (erhalten)",
       [r"kündig(ung|en)?.{0,400}(arbeitsverhältnis|arbeitgeber|arbeitsvertrag)",
        r"(arbeitsverhältnis|arbeitgeber).{0,400}kündig"],
       [("BGB", "§ 622"), ("BGB", "§ 623"), ("BGB", "§ 626"),
        ("KSchG", "§ 1"), ("KSchG", "§ 4"), ("KSchG", "§ 7"), ("KSchG", "§ 23"),
        ("BGB", "§ 133"), ("BGB", "§ 157")],
       chancen="Kündigungen scheitern häufig an der Schriftform (§ 623 BGB), an falsch "
               "berechneten Fristen (§ 622 BGB) oder an fehlender sozialer Rechtfertigung "
               "(§ 1 KSchG). Bereichsübergreifend ist die Kündigungserklärung auch "
               "vertragsrechtlich auszulegen (§§ 133, 157 BGB).",
       risiken="Wird die 3-Wochen-Frist des § 4 KSchG versäumt, gilt die Kündigung als "
               "von Anfang an wirksam (§ 7 KSchG) – gesetzliche Notfrist!",
       ausnahmen=["Kleinbetriebsklausel: § 1 KSchG gilt nicht bei i. d. R. 10 oder "
                  "weniger Arbeitnehmern (§ 23 KSchG).",
                  "Wartezeit: Kündigungsschutz erst nach 6 Monaten Betriebszugehörigkeit "
                  "(§ 1 Abs. 1 KSchG).",
                  "Kündigungsfrist verlängert sich mit der Betriebszugehörigkeit "
                  "(§ 622 Abs. 2 BGB).",
                  "Ausschlussfristen im Arbeits- oder Tarifvertrag prüfen."],
       fakten=["Zugangsdatum der Kündigung", "Dauer der Betriebszugehörigkeit",
               "Anzahl der Beschäftigten im Betrieb (Kleinbetriebsklausel § 23 KSchG)"],
       bereiche=["Arbeitsrecht"]),
    _r("Ausstehender Lohn / Gehalt",
       [r"(lohn|gehalt|vergütung|entgelt).{0,300}(nicht (gezahlt|bezahlt|überwiesen)|aussteh|offen|rückstand|verspätet)",
        r"(zahlt|zahlung).{0,120}(lohn|gehalt).{0,120}nicht"],
       [("BGB", "§ 611a"), ("BGB", "§ 614"), ("BGB", "§ 286"), ("BGB", "§ 288")],
       chancen="Der Vergütungsanspruch folgt aus § 611a Abs. 2 BGB und ist nach § 614 BGB "
               "fällig; ab Verzug fallen Zinsen an (§§ 286, 288 BGB).",
       risiken="Beweislage zur Arbeitsleistung und zur Höhe des Anspruchs sichern "
               "(Arbeitsvertrag, Stundennachweise, Abrechnungen).",
       ausnahmen=["Ausschlussfristen in Arbeits- oder Tarifverträgen können Ansprüche "
                  "bereits nach wenigen Monaten erlöschen lassen – dringend prüfen."],
       fakten=["Höhe des ausstehenden Betrags", "Abrechnungszeitraum"],
       vorlage="lohnzahlungsaufforderung",
       bereiche=["Arbeitsrecht"]),
    _r("Eigenkündigung durch Arbeitnehmer",
       [r"(selbst|eigen|möchte|will).{0,120}kündig", r"eigenkündigung"],
       [("BGB", "§ 622"), ("BGB", "§ 623")],
       chancen="Die ordentliche Eigenkündigung ist mit der Grundfrist von vier Wochen zum "
               "15. oder Monatsende möglich (§ 622 Abs. 1 BGB).",
       risiken="Ohne eigenhändig unterschriebenes Schriftstück ist die Kündigung nichtig – "
               "E-Mail, Fax oder Scan genügen NICHT (§ 623 BGB).",
       ausnahmen=["Längere vertragliche Kündigungsfristen können vereinbart sein."],
       fakten=["Gewünschter Beendigungstermin"],
       vorlage="eigenkuendigung",
       bereiche=["Arbeitsrecht"]),
    _r("Urlaubsanspruch / Urlaubsabgeltung",
       [r"\burlaub", r"urlaubsabgeltung"],
       [("BUrlG", "§ 1"), ("BUrlG", "§ 3"), ("BUrlG", "§ 7")],
       chancen="Mindesturlaub von 24 Werktagen (§§ 1, 3 BUrlG); bei Beendigung ist nicht "
               "genommener Urlaub abzugelten (§ 7 Abs. 4 BUrlG).",
       bereiche=["Arbeitsrecht"]),
    _r("Entgeltfortzahlung im Krankheitsfall",
       [r"(krank|arbeitsunfähig)", r"entgeltfortzahlung"],
       [("EFZG", "§ 3")],
       chancen="Bis zu sechs Wochen Entgeltfortzahlung bei unverschuldeter "
               "Arbeitsunfähigkeit (§ 3 EFZG).",
       fakten=["Beginn und Nachweis der Arbeitsunfähigkeit"],
       bereiche=["Arbeitsrecht"]),
    _r("Arbeitszeugnis",
       [r"zeugnis"],
       [("GewO", "§ 109")],
       chancen="Anspruch auf ein schriftliches, klar formuliertes Zeugnis; auf Verlangen "
               "qualifiziert mit Leistungs- und Verhaltensbeurteilung (§ 109 GewO).",
       bereiche=["Arbeitsrecht"]),
    _r("Arbeitszeit / Überstunden",
       [r"überstunden", r"arbeitszeit.{0,80}(überschritten|zu lang|10 stunden|zehn stunden)"],
       [("ArbZG", "§ 3"), ("BGB", "§ 611a"), ("BGB", "§ 614")],
       chancen="Die werktägliche Arbeitszeit ist auf 8 (max. 10) Stunden begrenzt "
               "(§ 3 ArbZG); geleistete Überstunden sind zu dokumentieren.",
       fakten=["Aufzeichnungen der tatsächlichen Arbeitszeiten"],
       bereiche=["Arbeitsrecht"]),

    # --- Privatrecht ------------------------------------------------------
    _r("Kaufvertrag / Mängelrechte",
       [r"(gekauft|kaufvertrag|gekaufte|bestellt).{0,400}(mangel|defekt|kaputt|funktioniert nicht|beschädigt)",
        r"(mangel|defekt).{0,300}(kauf|händler|verkäufer)"],
       [("BGB", "§ 433"), ("BGB", "§ 434"), ("BGB", "§ 437"), ("BGB", "§ 439"),
        ("BGB", "§ 323"), ("BGB", "§ 280")],
       chancen="Bei Mängeln bestehen Rechte auf Nacherfüllung, Rücktritt, Minderung oder "
               "Schadensersatz (§§ 434, 437, 439, 323, 280 BGB).",
       risiken="Für den Rücktritt ist regelmäßig eine erfolglose, angemessene Fristsetzung "
               "erforderlich (§ 323 BGB); Mangel bei Gefahrübergang dokumentieren.",
       fakten=["Kaufdatum und Zeitpunkt der Mangelentdeckung"],
       bereiche=["Privatrecht", "Firmenrecht – Kleingewerbe & Einzelunternehmer",
                 "Firmenrecht – GmbH & e.K."]),
    _r("Offene Forderung / Zahlungsverzug",
       [r"(rechnung|forderung).{0,300}(nicht (gezahlt|bezahlt|beglichen)|offen|überfällig|aussteh)",
        r"(mahnung|zahlungserinnerung)"],
       [("BGB", "§ 286"), ("BGB", "§ 288")],
       chancen="Verzug tritt durch Mahnung, kalendermäßige Bestimmung oder spätestens "
               "30 Tage nach Fälligkeit und Rechnungszugang ein (§ 286 BGB); dann "
               "Verzugszinsen nach § 288 BGB.",
       fakten=["Rechnungsdatum und Zugang beim Schuldner"],
       bereiche=["Privatrecht", "Firmenrecht – Kleingewerbe & Einzelunternehmer",
                 "Firmenrecht – GmbH & e.K."]),
    _r("Unerwünschte Werbung / Datenverarbeitung (DSGVO)",
       [r"(werbung|newsletter|werbemail|werbebrief|direktwerbung)",
        r"datenschutz.{0,120}widerspruch"],
       [("DSGVO", "Art. 21")],
       chancen="Gegen Direktwerbung besteht ein jederzeitiges, bedingungsloses "
               "Widerspruchsrecht; danach dürfen die Daten dafür nicht mehr verwendet "
               "werden (Art. 21 Abs. 2, 3 DSGVO).",
       vorlage="werbewiderspruch-dsgvo",
       bereiche=["Privatrecht"]),
    _r("Anfechtung wegen Irrtums / Täuschung",
       [r"(getäuscht|täuschung|irrtum|angefochten|anfechtung|gedroht|drohung)"],
       [("BGB", "§ 119"), ("BGB", "§ 123")],
       chancen="Willenserklärungen sind bei Irrtum (§ 119 BGB) oder arglistiger Täuschung/"
               "Drohung (§ 123 BGB) anfechtbar.",
       risiken="Anfechtungsfristen beachten: bei § 119 BGB unverzüglich nach Kenntnis.",
       bereiche=["Privatrecht"]),
    _r("Eigentumsstörung / Nachbarschaft",
       [r"(nachbar|lärm|ruhestörung|grundstück.{0,120}(störung|beeinträchtigung))",
        r"(herausgabe|weggenommen|nicht zurückgegeben)"],
       [("BGB", "§ 985"), ("BGB", "§ 1004"), ("BGB", "§ 906"), ("BGB", "§ 823")],
       chancen="Beseitigungs- und Unterlassungsansprüche gegen Störer (§ 1004 BGB), "
               "Herausgabeanspruch des Eigentümers (§ 985 BGB), ggf. Schadensersatz "
               "(§ 823 BGB); Wesentlichkeitsgrenze des § 906 BGB beachten.",
       fakten=["Störungsprotokoll mit Datum und Uhrzeit"],
       vorlage="nachbarschaftsbeschwerde",
       bereiche=["Privatrecht", "Wohnrecht"]),

    # --- Wohnrecht --------------------------------------------------------
    _r("Mietmangel (z. B. Schimmel) / Mietminderung",
       [r"(schimmel|feuchtigkeit|wasserschaden|heizungsausfall|heizung.{0,80}(defekt|ausgefallen|kalt))",
        r"(mangel|mängel).{0,300}(wohnung|mietsache|miete)"],
       [("BGB", "§ 535"), ("BGB", "§ 536"), ("BGB", "§ 536a"), ("BGB", "§ 536c"),
        ("BGB", "§ 569")],
       chancen="Bei erheblichen Mängeln ist die Miete kraft Gesetzes gemindert (§ 536 BGB); "
               "daneben kommen Schadens-/Aufwendungsersatz (§ 536a BGB) und bei "
               "Gesundheitsgefahr die fristlose Kündigung (§ 569 BGB) in Betracht.",
       risiken="Der Mangel muss dem Vermieter unverzüglich angezeigt werden – sonst "
               "drohen Rechtsverlust und Schadensersatzpflicht (§ 536c BGB). "
               "Minderungsquote nicht überziehen: Zahlungsrückstand kann eine fristlose "
               "Kündigung nach § 543 BGB begründen.",
       ausnahmen=["Unerhebliche Tauglichkeitsminderungen berechtigen nicht zur Minderung "
                  "(§ 536 Abs. 1 S. 3 BGB)."],
       fakten=["Datum der Mängelanzeige an den Vermieter", "Fotodokumentation des Mangels"],
       vorlage="mietminderung-schimmel",
       bereiche=["Wohnrecht"]),
    _r("Nebenkosten-/Betriebskostenabrechnung",
       [r"(nebenkosten|betriebskosten)", r"abrechnungszeitraum"],
       [("BGB", "§ 556"), ("BetrKV", "§ 1"), ("BetrKV", "§ 2")],
       chancen="Nur umlagefähige Betriebskosten nach §§ 1, 2 BetrKV dürfen abgerechnet "
               "werden; verspätete Abrechnungen (> 12 Monate nach Ende des "
               "Abrechnungszeitraums) schließen Nachforderungen aus (§ 556 Abs. 3 BGB).",
       risiken="Eigene Einwendungen müssen innerhalb von 12 Monaten nach Zugang der "
               "Abrechnung erhoben werden (§ 556 Abs. 3 S. 5 BGB) – Frist notieren!",
       fakten=["Zugangsdatum der Abrechnung", "Ende des Abrechnungszeitraums"],
       vorlage="nebenkosten-widerspruch",
       bereiche=["Wohnrecht"]),
    _r("Kündigung des Mietverhältnisses durch den Vermieter",
       [r"(vermieter|mietverhältnis|wohnung).{0,300}kündig",
        r"kündig.{0,300}(mietverhältnis|wohnung|eigenbedarf)", r"eigenbedarf"],
       [("BGB", "§ 573"), ("BGB", "§ 573c"), ("BGB", "§ 574"), ("BGB", "§ 543"),
        ("BGB", "§ 133"), ("BGB", "§ 157")],
       chancen="Die Vermieterkündigung braucht ein berechtigtes Interesse (§ 573 BGB) und "
               "die richtige Frist (§ 573c BGB); bei unzumutbarer Härte ist Widerspruch "
               "möglich (§ 574 BGB). Auch hier gilt die allgemeine vertragsrechtliche "
               "Auslegung der Erklärung (§§ 133, 157 BGB).",
       risiken="Der Härtewiderspruch nach § 574 BGB muss rechtzeitig vor Ende des "
               "Mietverhältnisses erklärt werden; bei Zahlungsverzug droht die fristlose "
               "Kündigung (§ 543 BGB).",
       fakten=["Zugangsdatum der Kündigung", "Wohndauer (Fristverlängerung § 573c BGB)"],
       bereiche=["Wohnrecht"]),
    _r("Mietkaution",
       [r"kaution"],
       [("BGB", "§ 551")],
       chancen="Die Kaution ist auf drei Nettokaltmieten begrenzt (§ 551 BGB).",
       bereiche=["Wohnrecht"]),

    # --- Firmenrecht – Kleingewerbe & Einzelunternehmer --------------------
    _r("Kleinunternehmerregelung (Umsatzsteuer)",
       [r"kleinunternehmer", r"§ ?19 ?ustg", r"umsatzsteuer.{0,160}(befreit|ausweisen|erheben)"],
       [("UStG", "§ 19"), ("BGB", "§ 14")],
       chancen="Als Kleinunternehmer wird keine Umsatzsteuer erhoben (§ 19 UStG).",
       ausnahmen=["Grenzen prüfen: Vorjahresumsatz max. 25 000 €, laufendes Jahr max. "
                  "100 000 € (§ 19 UStG). Bei Überschreiten entfällt die Regelung."],
       fakten=["Gesamtumsatz Vorjahr und laufendes Jahr"],
       bereiche=["Firmenrecht – Kleingewerbe & Einzelunternehmer"]),
    _r("Gewerbeanzeige (An-/Um-/Abmeldung)",
       [r"gewerbe.{0,80}(anmeld|ummeld|abmeld|anzeige)", r"gewerbeamt"],
       [("GewO", "§ 14")],
       chancen="Beginn, Verlegung, Änderung und Aufgabe des Gewerbes sind anzeigepflichtig "
               "(§ 14 GewO) – die Anzeige ist keine Genehmigung, sondern eine Meldung.",
       bereiche=["Firmenrecht – Kleingewerbe & Einzelunternehmer"]),
    _r("Aufbewahrung von Steuerunterlagen",
       [r"(steuerunterlagen|aufbewahrung|belege).{0,200}(frist|jahre|anfordern|steuerberater)",
        r"steuerberater.{0,200}(unterlagen|herausgabe)"],
       [("AO", "§ 147"), ("HGB", "§ 257")],
       chancen="Herausgabe- bzw. Aufbewahrungspflichten für Buchführungsunterlagen folgen "
               "aus § 147 AO (für Kaufleute auch § 257 HGB).",
       vorlage="steuerunterlagen-anforderung",
       bereiche=["Firmenrecht – Kleingewerbe & Einzelunternehmer",
                 "Firmenrecht – GmbH & e.K."]),

    # --- Firmenrecht – GmbH & e.K. -----------------------------------------
    _r("Kaufmannseigenschaft / Handelsregister",
       [r"(kaufmann|handelsregister|eingetragener? kaufmann|\be\.? ?k\.?\b|firma.{0,120}eintrag)"],
       [("HGB", "§ 1"), ("HGB", "§ 2"), ("HGB", "§ 5"), ("HGB", "§ 8"),
        ("HGB", "§ 15"), ("HGB", "§ 29")],
       chancen="Ob Istkaufmann (§ 1 HGB) oder Kannkaufmann kraft Eintragung (§ 2 HGB), "
               "entscheidet über HGB-Pflichten; die Registerpublizität des § 15 HGB "
               "schützt den Rechtsverkehr.",
       ausnahmen=["§ 1 vs. § 2 HGB: Ohne in kaufmännischer Weise eingerichteten "
                  "Geschäftsbetrieb entsteht die Kaufmannseigenschaft erst mit "
                  "freiwilliger Eintragung."],
       bereiche=["Firmenrecht – GmbH & e.K."]),
    _r("GmbH: Organisation und Haftung",
       [r"\bgmbh\b", r"geschäftsführer", r"stammkapital", r"gesellschafter"],
       [("GmbHG", "§ 5"), ("GmbHG", "§ 6"), ("GmbHG", "§ 13"), ("GmbHG", "§ 35"),
        ("GmbHG", "§ 43"), ("HGB", "§ 6")],
       chancen="Für Verbindlichkeiten haftet grundsätzlich nur das Gesellschaftsvermögen "
               "(§ 13 Abs. 2 GmbHG); die Gesellschaft wird durch die Geschäftsführer "
               "vertreten (§ 35 GmbHG).",
       risiken="Geschäftsführer haften der Gesellschaft bei Pflichtverletzungen persönlich "
               "(§ 43 GmbHG).",
       bereiche=["Firmenrecht – GmbH & e.K."]),
    _r("Handelsvertreter: außerordentliche Kündigung",
       [r"handelsvertreter", r"vertriebspartner.{0,160}kündig"],
       [("HGB", "§ 89a")],
       chancen="Der Handelsvertretervertrag ist aus wichtigem Grund fristlos kündbar; das "
               "Recht ist unabdingbar (§ 89a HGB).",
       bereiche=["Firmenrecht – GmbH & e.K."]),

    # --- Verfahren (übergreifend) -------------------------------------------
    _r("Gerichtliche Frist / Fristverlängerung",
       [r"(gericht|klage|schriftsatz).{0,240}frist", r"fristverlängerung"],
       [("ZPO", "§ 224")],
       chancen="Richterliche Fristen können auf Antrag mit erheblichen Gründen verlängert "
               "werden (§ 224 Abs. 2 ZPO).",
       risiken="NOTFRISTEN sind NICHT verlängerbar (§ 224 Abs. 1 ZPO) – vor jedem Antrag "
               "die Fristart prüfen.",
       vorlage="fristverlaengerung-gericht"),
]


# ---------------------------------------------------------------------------
# Fortschritt (in-memory, je Fall)
# ---------------------------------------------------------------------------
_fortschritt: dict[str, dict] = {}
_fortschritt_lock = threading.Lock()


def fortschritt_holen(fall_id: str) -> dict:
    with _fortschritt_lock:
        return dict(_fortschritt.get(fall_id, {"status": "keine", "prozent": 0, "schritt": ""}))


def _fortschritt_setzen(fall_id: str, prozent: int, schritt: str, status: str = "läuft") -> None:
    with _fortschritt_lock:
        _fortschritt[fall_id] = {"status": status, "prozent": prozent, "schritt": schritt}


# ---------------------------------------------------------------------------
# Kernanalyse
# ---------------------------------------------------------------------------

def _paragraph_zitieren(kuerzel: str, paragraph: str) -> dict | None:
    """Zitat ausschließlich aus der DB – existiert der Eintrag nicht, wird er
    NICHT zitiert (kein Rückgriff auf Modellwissen)."""
    eintrag = datenbank.paragraph_holen(kuerzel, paragraph)
    if eintrag is None:
        return None
    return {
        "gesetz": kuerzel,
        "paragraph": paragraph,
        "titel": eintrag["titel"],
        "volltext": eintrag["volltext"],
        "fassung_stand": eintrag["fassung_stand"],
        "quelle_url": eintrag["quelle_url"],
    }


def _regeln_anwenden(gesamttext: str, rechtsbereich: str) -> list[dict]:
    treffer = []
    for regel in _REGELN:
        relevant_im_bereich = rechtsbereich in regel["bereiche"]
        if not any(t.search(gesamttext) for t in regel["trigger"]):
            continue
        # Bereichsübergreifende Themen werden mit Hinweis aufgenommen
        treffer.append({"regel": regel, "im_bereich": relevant_im_bereich})
    return treffer


def _anwalt_empfehlen(gesamttext: str, fristen_liste: list[dict]) -> bool:
    klein = gesamttext.lower()
    signale = ("kündig", "fristlos", "klage", "abmahnung", "räumung", "insolvenz",
               "strafanzeige", "gericht")
    if any(s in klein for s in signale):
        return True
    if any(f.get("notfrist") or f.get("warnstufe") in ("überfällig", "kritisch")
           for f in fristen_liste):
        return True
    for betrag in re.findall(r"(\d{1,3}(?:\.\d{3})+|\d{4,})(?:,\d{2})?\s*(?:€|euro)", klein):
        if int(betrag.replace(".", "")) >= 5000:
            return True
    return False


def _ki_einschaetzung(rechtsbereich: str, sachverhalt: str, zitate: list[dict]) -> str | None:
    """Optionale KI-Zweitmeinung über die Anthropic-API (mit Timeout & Retry).
    Der Prompt erzwingt Zitate ausschließlich aus den übergebenen DB-Paragraphen."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not zitate:
        return None
    import httpx
    paragraphen_text = "\n\n".join(
        f"{z['gesetz']} {z['paragraph']} – {z['titel']} (Fassung: {z['fassung_stand']}):\n{z['volltext']}"
        for z in zitate
    )
    for versuch in range(config.EXTERN_RETRIES + 1):
        try:
            antwort = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                json={
                    "model": "claude-sonnet-5",
                    "max_tokens": 1500,
                    "system": SYSTEM_INSTRUKTION.format(rechtsbereich=rechtsbereich),
                    "messages": [{
                        "role": "user",
                        "content": f"Sachverhalt/Dokumentauszüge:\n{sachverhalt[:6000]}\n\n"
                                   f"Verfügbare Gesetzestexte aus der Datenbank:\n{paragraphen_text}",
                    }],
                },
                timeout=config.EXTERN_TIMEOUT_SEK,
            )
            antwort.raise_for_status()
            bloecke = antwort.json().get("content", [])
            return "".join(b.get("text", "") for b in bloecke) or None
        except Exception as exc:
            fehlerlog.protokollieren("analyse", f"KI-API Versuch {versuch + 1}: {exc}")
            time.sleep(2 ** versuch)
    return None


def analyse_durchfuehren(fall_id: str) -> dict:
    """Vollständige Fallanalyse. Bei Abbruch: Status 'unvollständig', erneut anstoßbar."""
    meta = faelle.fall_holen(fall_id)
    rechtsbereich = meta["rechtsbereich"]
    faelle.status_setzen(fall_id, "in_analyse")
    _fortschritt_setzen(fall_id, 5, "Dokumente werden geladen …")
    try:
        ergebnis = _analyse_kern(fall_id, meta, rechtsbereich)
    except Exception as exc:
        faelle.status_setzen(fall_id, "unvollstaendig")
        _fortschritt_setzen(fall_id, 0, "Analyse abgebrochen – erneut anstoßbar.", "fehler")
        fehlerlog.protokollieren("analyse", f"Analyse abgebrochen: {exc}", kritisch=True)
        raise
    _fortschritt_setzen(fall_id, 100, "Fertig.", "fertig")
    faelle.status_setzen(fall_id, "analysiert")
    return ergebnis


def _analyse_kern(fall_id: str, meta: dict, rechtsbereich: str) -> dict:
    dokumente = upload.dokumente_auflisten(fall_id)
    texte: list[dict] = []
    unleserlich: list[str] = []
    warnhinweise: list[str] = []

    # 1) Sachverhalt erfassen: Texte extrahieren (in Stapeln, mit Fortschritt)
    stapel = dokumente[: config.MAX_ANALYSE_DOKUMENTE_PRO_STAPEL]
    for i, dok in enumerate(stapel):
        _fortschritt_setzen(
            fall_id, 5 + int(45 * (i + 1) / max(len(stapel), 1)),
            f"Lese „{dok['originalname']}“ ({i + 1}/{len(stapel)}) …",
        )
        try:
            _, inhalt = upload.inhalt_laden(fall_id, dok["datei"])
        except Exception as exc:
            fehlerlog.protokollieren("analyse", f"Dokument nicht ladbar: {exc}")
            unleserlich.append(dok["originalname"])
            continue
        extrakt = extraktion.text_extrahieren(dok["endung"], inhalt)
        if not extrakt["lesbar"]:
            unleserlich.append(dok["originalname"])
        warnhinweise.extend(f"{dok['originalname']}: {h}" for h in extrakt["hinweise"])
        typ = doktyp.typ_erkennen(extrakt["text"])
        plausi = doktyp.plausibilitaet_pruefen(typ, rechtsbereich)
        if plausi:
            warnhinweise.append(f"{dok['originalname']}: {plausi}")
        texte.append({
            "datei": dok["originalname"], "ordner": dok["ordner"],
            "typ": typ, "text": extrakt["text"],
        })
    if len(dokumente) > len(stapel):
        warnhinweise.append(
            f"{len(dokumente) - len(stapel)} weitere Dokumente werden im nächsten "
            f"Analyse-Stapel verarbeitet (Stapelgröße: "
            f"{config.MAX_ANALYSE_DOKUMENTE_PRO_STAPEL})."
        )

    beschreibung = meta.get("beschreibung", "")
    gesamttext = "\n\n".join([beschreibung] + [t["text"] for t in texte])

    # 2) Fristen & Zusagen als Zeitleiste
    _fortschritt_setzen(fall_id, 55, "Fristen und Zusagen werden extrahiert …")
    fristen_liste: list[dict] = fristen.fristen_extrahieren(beschreibung, "Fallbeschreibung")
    for t in texte:
        fristen_liste.extend(fristen.fristen_extrahieren(t["text"], t["datei"]))
    zeitleiste = fristen.zeitleiste(fristen_liste)

    # 3) Einschlägige Paragraphen über das Regelwerk (nur DB-Zitate)
    _fortschritt_setzen(fall_id, 70, "Gesetzesdatenbank wird abgeglichen …")
    regel_treffer = _regeln_anwenden(gesamttext, rechtsbereich)
    themen: list[dict] = []
    zitate: list[dict] = []
    zitiert: set[tuple[str, str]] = set()
    fehlende_fakten: list[str] = []
    vorlagen_vorschlaege: list[str] = []
    for treffer in regel_treffer:
        regel = treffer["regel"]
        thema_zitate = []
        for kuerzel, para in regel["paragraphen"]:
            zitat = _paragraph_zitieren(kuerzel, para)
            if zitat is None:
                continue
            thema_zitate.append({"gesetz": kuerzel, "paragraph": para,
                                 "titel": zitat["titel"],
                                 "fassung_stand": zitat["fassung_stand"]})
            if (kuerzel, para) not in zitiert:
                zitiert.add((kuerzel, para))
                zitate.append(zitat)
        themen.append({
            "thema": regel["thema"],
            "im_gewaehlten_bereich": treffer["im_bereich"],
            "paragraphen": thema_zitate,
            "chancen": regel["chancen"],
            "risiken": regel["risiken"],
            "ausnahmen": regel["ausnahmen"],
        })
        fehlende_fakten.extend(f for f in regel["fakten"] if f not in fehlende_fakten)
        if regel["vorlage"] and regel["vorlage"] not in vorlagen_vorschlaege:
            vorlagen_vorschlaege.append(regel["vorlage"])

    # 4) Fehlende Fakten: nur behalten, was der Sachverhalt nicht schon liefert
    offene_fragen = [f for f in fehlende_fakten if not _fakt_vorhanden(f, gesamttext)]
    if unleserlich:
        offene_fragen.append(
            "Unleserliche Dokumente erneut hochladen: " + ", ".join(unleserlich)
        )
    if not texte and not beschreibung:
        offene_fragen.append("Es liegen weder Dokumente noch eine Fallbeschreibung vor.")

    # 5) Optionale KI-Einschätzung (nur mit DB-Paragraphen als Quelle)
    _fortschritt_setzen(fall_id, 85, "Einschätzung wird erstellt …")
    ki_text = _ki_einschaetzung(rechtsbereich, gesamttext, zitate)

    ergebnis = {
        "fall_id": fall_id,
        "rechtsbereich": rechtsbereich,
        "erstellt": datetime.now(timezone.utc).isoformat(),
        "sachverhalt": {
            "beschreibung": beschreibung,
            "dokumente": [{"datei": t["datei"], "typ": t["typ"],
                           "auszug": t["text"][:400]} for t in texte],
            "unleserliche_dokumente": unleserlich,
        },
        "themen": themen,
        "paragraphen": [{k: z[k] for k in
                         ("gesetz", "paragraph", "titel", "volltext", "fassung_stand",
                          "quelle_url")} for z in zitate],
        "offene_fragen": offene_fragen,
        "warnhinweise": warnhinweise,
        "zeitleiste": zeitleiste,
        "anwalt_empfohlen": _anwalt_empfehlen(gesamttext, fristen_liste),
        "ki_einschaetzung": ki_text,
        "vorlagen_vorschlaege": vorlagen_vorschlaege,
        "beratungshinweis": config.BERATUNGSHINWEIS,
        "rdg_hinweis": config.RDG_HINWEIS,
    }

    # 6) Ergebnis verschlüsselt im Fallordner ablegen
    _fortschritt_setzen(fall_id, 95, "Ergebnis wird gespeichert …")
    ordner = faelle.fall_ordner_holen(fall_id)
    (ordner / "analyse.json.enc").write_bytes(
        krypto.verschluesseln(json.dumps(ergebnis, ensure_ascii=False).encode("utf-8"))
    )
    return ergebnis


_FAKT_INDIKATOREN = {
    "Zugangsdatum der Kündigung": [r"(zugegangen|erhalten|zugestellt).{0,60}\d{1,2}\.\d{1,2}\.\d{2,4}",
                                   r"\d{1,2}\.\d{1,2}\.\d{2,4}.{0,60}(zugegangen|erhalten|zugestellt)"],
    "Dauer der Betriebszugehörigkeit": [r"(seit|betriebszugehörigkeit|beschäftigt.{0,40}(seit|jahre))"],
    "Anzahl der Beschäftigten im Betrieb (Kleinbetriebsklausel § 23 KSchG)":
        [r"\d+\s*(mitarbeiter|beschäftigte|arbeitnehmer)"],
}


def _fakt_vorhanden(fakt: str, text: str) -> bool:
    for muster in _FAKT_INDIKATOREN.get(fakt, []):
        if re.search(muster, text, re.IGNORECASE):
            return True
    return False


def analyse_laden(fall_id: str) -> dict | None:
    ordner = faelle.fall_ordner_holen(fall_id)
    pfad = ordner / "analyse.json.enc"
    if not pfad.exists():
        return None
    return json.loads(krypto.entschluesseln(pfad.read_bytes()).decode("utf-8"))
