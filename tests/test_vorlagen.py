"""Unit-Tests: Vorlagen-Bibliothek, Platzhalter-Befüllung, Prüfregeln."""

from datetime import date, timedelta

import pytest

from app import faelle, vorlagen
from app.vorlagen import VorlagenFehler

ERWARTETE_VORLAGEN = {
    "mietminderung-schimmel", "nebenkosten-widerspruch", "lohnzahlungsaufforderung",
    "eigenkuendigung", "nachbarschaftsbeschwerde", "werbewiderspruch-dsgvo",
    "fristverlaengerung-gericht", "steuerunterlagen-anforderung",
}


def test_alle_acht_vorlagen_vorhanden():
    ids = {v["id"] for v in vorlagen.alle_vorlagen()}
    assert ids == ERWARTETE_VORLAGEN


def test_app_hinweise_nicht_im_schreiben():
    for v in vorlagen.alle_vorlagen():
        assert "App-Hinweis" not in v["text"]


def test_einheitlicher_aufbau():
    for v in vorlagen.alle_vorlagen():
        assert "Betreff" in v["text"], v["id"]
        assert "Mit freundlichen Grüßen" in v["text"], v["id"]
        assert "FRIST" in " ".join(v["platzhalter"]), v["id"]


def test_platzhalter_befuellung_aus_metadaten(fall):
    ergebnis = vorlagen.generieren(fall["fall_id"], "lohnzahlungsaufforderung",
                                   {"BETRAG": "2400", "ABRECHNUNGSZEITRAUM": "Juni 2026"})
    assert "Max Muster" in ergebnis["text"]
    assert "2400" in ergebnis["text"]
    assert "[VORNAME]" not in ergebnis["text"]
    # Konkretes Fristdatum (heute + 14 Tage) statt Platzhalter
    frist = (date.today() + timedelta(days=vorlagen.STANDARD_FRIST_TAGE)).strftime("%d.%m.%Y")
    assert frist in ergebnis["text"]
    # Paragraph direkt beim Anspruch
    assert "§ 614 BGB" in ergebnis["text"]


def test_offene_platzhalter_werden_gemeldet(fall):
    ergebnis = vorlagen.generieren(fall["fall_id"], "lohnzahlungsaufforderung")
    assert "BETRAG" in ergebnis["offene_platzhalter"]


def test_schreiben_landet_verschluesselt_in_vorlagen(fall):
    ergebnis = vorlagen.generieren(fall["fall_id"], "eigenkuendigung",
                                   {"BEENDIGUNGSDATUM": "31.08.2026"})
    pfad = faelle.fall_ordner_holen(fall["fall_id"]) / "vorlagen" / ergebnis["datei"]
    assert pfad.is_file()
    assert b"Muster" not in pfad.read_bytes()  # verschlüsselt
    assert vorlagen.schreiben_laden(fall["fall_id"], ergebnis["datei"]) == ergebnis["text"]


def test_pruefregel_schriftform_eigenkuendigung(fall):
    ergebnis = vorlagen.generieren(fall["fall_id"], "eigenkuendigung")
    assert any("§ 623 BGB" in w and "eigenhändiger Unterschrift" in w
               for w in ergebnis["warnungen"])


def test_pruefregel_556_zwoelf_monate(fall):
    alt = (date.today() - timedelta(days=400)).strftime("%d.%m.%Y")
    ergebnis = vorlagen.generieren(fall["fall_id"], "nebenkosten-widerspruch",
                                   {"DATUM_ZUGANG": alt})
    assert any("12-Monats-Frist" in w and "abgelaufen" in w for w in ergebnis["warnungen"])
    frisch = (date.today() - timedelta(days=30)).strftime("%d.%m.%Y")
    ergebnis2 = vorlagen.generieren(fall["fall_id"], "nebenkosten-widerspruch",
                                    {"DATUM_ZUGANG": frisch})
    assert not any("abgelaufen" in w for w in ergebnis2["warnungen"])


def test_pruefregel_minderungsquote(fall):
    ergebnis = vorlagen.generieren(fall["fall_id"], "mietminderung-schimmel",
                                   {"MINDERUNGSQUOTE": "80", "DATUM_MANGEL": "01.06.2026"})
    assert any("50 %" in w for w in ergebnis["warnungen"])


def test_pruefregel_notfrist_hinweis(fall):
    ergebnis = vorlagen.generieren(fall["fall_id"], "fristverlaengerung-gericht")
    assert any("NOTFRISTEN" in w for w in ergebnis["warnungen"])


def test_unbekannte_vorlage(fall):
    with pytest.raises(VorlagenFehler, match="existiert nicht"):
        vorlagen.generieren(fall["fall_id"], "gibt-es-nicht")
