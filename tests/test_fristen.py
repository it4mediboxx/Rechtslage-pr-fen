"""Unit-Tests: Fristen-/Zusagen-Extraktion und Warnstufen."""

from datetime import date, timedelta

from app import fristen


def test_frist_mit_numerischem_datum():
    text = "Bitte zahlen Sie den Betrag bis zum 05.08.2026 auf unser Konto."
    treffer = fristen.fristen_extrahieren(text, "brief.txt", heute=date(2026, 7, 11))
    assert len(treffer) == 1
    assert treffer[0]["datum"] == "2026-08-05"
    assert treffer[0]["art"] == "Frist"
    assert treffer[0]["warnstufe"] == "bald"


def test_frist_mit_monatsnamen():
    text = "Die Frist läuft bis spätestens 3. September 2026."
    treffer = fristen.fristen_extrahieren(text, heute=date(2026, 7, 11))
    assert treffer and treffer[0]["datum"] == "2026-09-03"


def test_zusage_wird_erkannt():
    text = "Wir werden den Mangel bis 20.07.2026 beheben, das haben wir zugesagt."
    treffer = fristen.fristen_extrahieren(text, heute=date(2026, 7, 11))
    assert any(t["art"] == "Zusage" or t["art"] == "Frist" for t in treffer)


def test_datum_ohne_fristkontext_wird_ignoriert():
    text = "Am 01.01.2020 haben wir uns kennengelernt."
    assert fristen.fristen_extrahieren(text) == []


def test_ungueltiges_datum_wird_ignoriert():
    text = "Frist bis zum 31.02.2026."  # existiert nicht
    assert fristen.fristen_extrahieren(text) == []


def test_warnstufen():
    heute = date(2026, 7, 11)
    assert fristen.warnstufe(heute - timedelta(days=1), heute) == "überfällig"
    assert fristen.warnstufe(heute + timedelta(days=3), heute) == "kritisch"
    assert fristen.warnstufe(heute + timedelta(days=20), heute) == "bald"
    assert fristen.warnstufe(heute + timedelta(days=90), heute) == "ok"


def test_kschg_klagefrist_notfrist():
    eintrag = fristen.kschg_klagefrist(date(2026, 7, 1))
    assert eintrag["datum"] == "2026-07-22"
    assert eintrag["notfrist"] is True
    assert "§ 4 KSchG" in eintrag["kontext"]


def test_zeitleiste_chronologisch():
    eintraege = [{"datum": "2026-09-01"}, {"datum": "2026-07-01"}, {"datum": "2026-08-01"}]
    sortiert = fristen.zeitleiste(eintraege)
    assert [e["datum"] for e in sortiert] == ["2026-07-01", "2026-08-01", "2026-09-01"]
