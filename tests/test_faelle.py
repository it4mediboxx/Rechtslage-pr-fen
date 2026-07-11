"""Unit-Tests: Fallanlage, Ordnerstruktur, Metadaten, Bereinigung, Löschung."""

import json

import pytest

from app import config, faelle
from app.faelle import FallFehler


def test_ordnerstruktur_wird_angelegt(fall):
    ordner = faelle.fall_ordner_holen(fall["fall_id"])
    for unter in ("dokumente", "kommunikation", "vorlagen"):
        assert (ordner / unter).is_dir()
    assert (ordner / "metadaten.json").is_file()


def test_metadaten_vollstaendig(fall):
    meta = json.loads(
        (faelle.fall_ordner_holen(fall["fall_id"]) / "metadaten.json").read_text(encoding="utf-8")
    )
    for feld in ("vorname", "nachname", "email", "rechtsbereich",
                 "erstellungsdatum", "status", "fall_id"):
        assert feld in meta
    assert meta["status"] == "offen"
    assert meta["rechtsbereich"] == "Arbeitsrecht"


def test_path_traversal_wird_neutralisiert():
    f = faelle.fall_anlegen("../../boese", "..\\..\\Pfad", "", "Privatrecht")
    ordner = faelle.fall_ordner_holen(f["fall_id"])
    assert config.FAELLE_DIR.resolve() in ordner.parents
    assert ".." not in ordner.name
    assert "/" not in f["vorname"] and "\\" not in f["nachname"]


def test_injection_zeichen_werden_entfernt():
    f = faelle.fall_anlegen("Max'; DROP TABLE--", "<script>Muster</script>", "", "Privatrecht")
    assert "'" not in f["vorname"] and ";" not in f["vorname"]
    assert "<" not in f["nachname"] and ">" not in f["nachname"]


def test_unbekannter_rechtsbereich_abgelehnt():
    with pytest.raises(FallFehler, match="Rechtsbereich"):
        faelle.fall_anlegen("Max", "Muster", "", "Steuerrecht")


def test_ungueltige_email_abgelehnt():
    with pytest.raises(FallFehler, match="E-Mail"):
        faelle.fall_anlegen("Max", "Muster", "keine-mail", "Privatrecht")


def test_leerer_name_abgelehnt():
    with pytest.raises(FallFehler):
        faelle.fall_anlegen("///", "Muster", "", "Privatrecht")


def test_alle_fuenf_rechtsbereiche_anlegbar():
    assert len(config.RECHTSBEREICHE) == 5
    for bereich in config.RECHTSBEREICHE:
        f = faelle.fall_anlegen("Test", "Bereich", "", bereich)
        assert faelle.fall_holen(f["fall_id"])["rechtsbereich"] == bereich


def test_loeschung_vollstaendig_und_protokolliert(fall):
    ordner = faelle.fall_ordner_holen(fall["fall_id"])
    protokoll = faelle.fall_loeschen(fall["fall_id"])
    assert not ordner.exists()
    assert protokoll["fall_id"] == fall["fall_id"]
    zeilen = config.LOESCHPROTOKOLL_PFAD.read_text(encoding="utf-8").strip().splitlines()
    assert any(fall["fall_id"] in z for z in zeilen)
    with pytest.raises(FallFehler, match="nicht gefunden"):
        faelle.fall_holen(fall["fall_id"])


def test_ungueltige_fall_id_abgelehnt():
    with pytest.raises(FallFehler, match="Ungültige Fall-ID"):
        faelle.fall_ordner_holen("../../etc")
