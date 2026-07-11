"""Mindestens 2 Testfälle pro Rechtsbereich mit erwarteten Paragraphen als Soll.

Jeder Fall wird angelegt, ein Textdokument hochgeladen und synchron
analysiert. Geprüft wird, dass die erwarteten Paragraphen zitiert werden –
ausschließlich aus der Datenbank, stets mit Fassungsdatum.
"""

import pytest

from app import analyse, datenbank, faelle, upload

TESTFAELLE = [
    # (Rechtsbereich, Sachverhalt, erwartete Paragraphen)
    ("Arbeitsrecht",
     "Ich habe am 03.07.2026 die schriftliche Kündigung von meinem Arbeitgeber "
     "erhalten. Ich bin seit sechs Jahren im Betrieb, wir sind etwa 25 Mitarbeiter.",
     [("BGB", "§ 622"), ("BGB", "§ 623"), ("KSchG", "§ 1"), ("KSchG", "§ 4"),
      ("KSchG", "§ 23")]),
    ("Arbeitsrecht",
     "Mein Arbeitgeber hat mein Gehalt für Juni 2026 nicht gezahlt. "
     "Es stehen 2.400 Euro aus, die Arbeit wurde vollständig geleistet.",
     [("BGB", "§ 614"), ("BGB", "§ 286"), ("BGB", "§ 288")]),
    ("Privatrecht",
     "Ich habe im Mai eine Waschmaschine gekauft. Sie ist defekt, der Verkäufer "
     "reagiert nicht auf meine Beschwerden.",
     [("BGB", "§ 433"), ("BGB", "§ 437"), ("BGB", "§ 439"), ("BGB", "§ 323")]),
    ("Privatrecht",
     "Ich erhalte ständig unerwünschte Werbung per Post und E-Mail von einem "
     "Versandhändler und möchte der Nutzung meiner Daten widersprechen.",
     [("DSGVO", "Art. 21")]),
    ("Wohnrecht",
     "In meiner Mietwohnung ist seit dem 01.06.2026 starker Schimmel im "
     "Schlafzimmer. Der Vermieter wurde informiert, reagiert aber nicht.",
     [("BGB", "§ 535"), ("BGB", "§ 536"), ("BGB", "§ 536a"), ("BGB", "§ 536c")]),
    ("Wohnrecht",
     "Die Nebenkostenabrechnung für 2024 enthält Verwaltungskosten und kam "
     "sehr spät. Ich halte mehrere Positionen für nicht umlagefähig.",
     [("BGB", "§ 556"), ("BetrKV", "§ 1"), ("BetrKV", "§ 2")]),
    ("Firmenrecht – Kleingewerbe & Einzelunternehmer",
     "Ich bin Kleinunternehmer und unsicher, ob ich auf meinen Rechnungen "
     "Umsatzsteuer ausweisen muss. Mein Umsatz lag letztes Jahr bei 18.000 Euro.",
     [("UStG", "§ 19")]),
    ("Firmenrecht – Kleingewerbe & Einzelunternehmer",
     "Mein früherer Steuerberater gibt meine Belege und Steuerunterlagen der "
     "letzten Jahre nicht heraus, obwohl ich sie mehrfach angefordert habe.",
     [("AO", "§ 147")]),
    ("Firmenrecht – GmbH & e.K.",
     "Unsere GmbH hat einen neuen Geschäftsführer bestellt. Wir möchten wissen, "
     "wann er persönlich haftet und wer die Gesellschaft vertritt.",
     [("GmbHG", "§ 13"), ("GmbHG", "§ 35"), ("GmbHG", "§ 43")]),
    ("Firmenrecht – GmbH & e.K.",
     "Ich bin eingetragener Kaufmann (e. K.) und möchte wissen, welche Pflichten "
     "die Eintragung im Handelsregister mit sich bringt.",
     [("HGB", "§ 1"), ("HGB", "§ 2"), ("HGB", "§ 15"), ("HGB", "§ 29")]),
]


@pytest.mark.parametrize("bereich,sachverhalt,erwartet", TESTFAELLE,
                         ids=[f"{b[:12]}-{i}" for i, (b, _, _) in enumerate(TESTFAELLE)])
def test_bereich_analyse(bereich, sachverhalt, erwartet):
    fall = faelle.fall_anlegen("Erika", "Beispiel", "", bereich, sachverhalt)
    upload.speichern(fall["fall_id"], "sachverhalt.txt", sachverhalt.encode("utf-8"))
    ergebnis = analyse.analyse_durchfuehren(fall["fall_id"])

    zitiert = {(p["gesetz"], p["paragraph"]) for p in ergebnis["paragraphen"]}
    for soll in erwartet:
        assert soll in zitiert, f"{soll} fehlt in der Analyse ({bereich})"

    # Zitate NUR aus der Datenbank, immer mit Fassungsdatum
    for p in ergebnis["paragraphen"]:
        db_eintrag = datenbank.paragraph_holen(p["gesetz"], p["paragraph"])
        assert db_eintrag is not None, f"{p['gesetz']} {p['paragraph']} nicht in DB"
        assert p["volltext"] == db_eintrag["volltext"]
        assert p["fassung_stand"] == db_eintrag["fassung_stand"]

    # Beratungshinweis an der Ausgabestelle
    assert ergebnis["beratungshinweis"] == "Ersetzt keine anwaltliche Beratung."
    assert "RDG" in ergebnis["rdg_hinweis"]
    assert faelle.fall_holen(fall["fall_id"])["status"] == "analysiert"


def test_kuendigungsfall_empfiehlt_anwalt():
    fall = faelle.fall_anlegen("Erika", "Beispiel", "", "Arbeitsrecht",
                               "Kündigung vom Arbeitgeber erhalten, fristlos.")
    ergebnis = analyse.analyse_durchfuehren(fall["fall_id"])
    assert ergebnis["anwalt_empfohlen"] is True


def test_fehlende_fakten_werden_benannt():
    fall = faelle.fall_anlegen("Erika", "Beispiel", "", "Arbeitsrecht",
                               "Ich habe eine Kündigung vom Arbeitgeber bekommen.")
    ergebnis = analyse.analyse_durchfuehren(fall["fall_id"])
    assert any("Betriebszugehörigkeit" in f for f in ergebnis["offene_fragen"])
    assert any("Kleinbetriebsklausel" in f for f in ergebnis["offene_fragen"])


def test_bereichsuebergreifende_pruefung():
    # Kündigungsfall zitiert auch die vertragsrechtliche Auslegung (§§ 133, 157 BGB)
    fall = faelle.fall_anlegen("Erika", "Beispiel", "", "Arbeitsrecht",
                               "Kündigung vom Arbeitgeber erhalten am 01.07.2026.")
    ergebnis = analyse.analyse_durchfuehren(fall["fall_id"])
    zitiert = {(p["gesetz"], p["paragraph"]) for p in ergebnis["paragraphen"]}
    assert ("BGB", "§ 133") in zitiert
    assert ("BGB", "§ 157") in zitiert


def test_unleserliches_dokument_gibt_hinweis_statt_fehlanalyse():
    fall = faelle.fall_anlegen("Erika", "Beispiel", "", "Wohnrecht",
                               "Schimmel in der Wohnung seit Juni.")
    # PNG ohne lesbaren Inhalt -> OCR-Hinweis statt stiller Fehlanalyse
    upload.speichern(fall["fall_id"], "foto.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 200)
    ergebnis = analyse.analyse_durchfuehren(fall["fall_id"])
    assert "foto.png" in ergebnis["sachverhalt"]["unleserliche_dokumente"]
    assert any("foto.png" in w for w in ergebnis["warnhinweise"])
    assert any("erneut hochladen" in f for f in ergebnis["offene_fragen"])


def test_fristen_landen_in_zeitleiste():
    fall = faelle.fall_anlegen("Erika", "Beispiel", "", "Wohnrecht",
                               "Schimmel gemeldet. Dem Vermieter wurde eine Frist "
                               "bis zum 25.07.2026 zur Beseitigung gesetzt.")
    ergebnis = analyse.analyse_durchfuehren(fall["fall_id"])
    assert any(e["datum"] == "2026-07-25" and e["art"] == "Frist"
               for e in ergebnis["zeitleiste"])
