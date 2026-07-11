"""Unit-Tests: Gesetzesdatenbank – Abfragen, Volltextsuche, Performance, Diff."""

import time

from app import datenbank


def test_seed_daten_vorhanden():
    alle = datenbank.alle_paragraphen()
    assert len(alle) >= 50
    kuerzel = {e["gesetz_kuerzel"] for e in alle}
    for erwartet in ("BGB", "KSchG", "ArbZG", "BUrlG", "EFZG", "GewO",
                     "BetrKV", "UStG", "HGB", "GmbHG", "DSGVO", "ZPO"):
        assert erwartet in kuerzel


def test_paragraph_mit_fassungsdatum_und_quelle():
    eintrag = datenbank.paragraph_holen("BGB", "§ 623")
    assert eintrag is not None
    assert "Schriftform" in eintrag["titel"]
    assert eintrag["fassung_stand"]
    assert eintrag["quelle_url"].startswith("https://www.gesetze-im-internet.de")


def test_volltextsuche_findet_mietminderung():
    treffer = datenbank.volltextsuche("Mietminderung")
    assert any(t["paragraph"] == "§ 536" for t in treffer)


def test_volltextsuche_sonderzeichen_sicher():
    # FTS5-Syntax darf nicht zu Fehlern führen (Injection-Schutz)
    assert datenbank.volltextsuche('kündigung" OR "1') is not None
    assert datenbank.volltextsuche("(((*)))") == []


def test_abfrage_unter_200ms():
    anfragen = ["Kündigungsfrist", "Mietminderung Schimmel", "Betriebskosten",
                "Kleinunternehmer", "Handelsregister", "Urlaub", "Verzug",
                "Widerspruch Werbung", "Stammkapital", "Zeugnis"]
    for anfrage in anfragen:
        start = time.perf_counter()
        datenbank.volltextsuche(anfrage)
        dauer = time.perf_counter() - start
        assert dauer < 0.2, f"Abfrage „{anfrage}“ dauerte {dauer * 1000:.0f} ms"


def test_lasttest_einzelabfragen():
    # 500 Einzelabfragen (mit Cache) müssen deutlich unter 200 ms/Abfrage bleiben
    start = time.perf_counter()
    for _ in range(500):
        assert datenbank.paragraph_holen("BGB", "§ 622") is not None
    gesamt = time.perf_counter() - start
    assert gesamt / 500 < 0.2


def test_update_mit_diff_protokoll():
    original = datenbank.paragraph_holen("ZPO", "§ 224")
    geaendert = dict(original)
    geaendert["gesetz_kuerzel"] = "ZPO"
    geaendert["paragraph"] = "§ 224"
    geaendert["volltext"] = original["volltext"] + " (Teständerung)"
    geaendert["fassung_stand"] = "Test-Update"
    assert datenbank.aktualisieren([geaendert]) == 1
    protokoll = datenbank.update_protokoll()
    eintrag = next(p for p in protokoll if p["aenderung"] == "geaendert"
                   and p["paragraph"] == "§ 224")
    assert "Teständerung" in eintrag["diff"]
    # Zurücksetzen für andere Tests
    datenbank.aktualisieren([original])


def test_unbekannter_paragraph_liefert_none():
    assert datenbank.paragraph_holen("BGB", "§ 99999") is None
