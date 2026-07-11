"""Unit-Tests: Upload-Validierung (Typ, Größe, Magic Bytes, Virenscan)."""

import pytest

from app import config, krypto, upload
from app.upload import UploadFehler

PDF_MINI = b"%PDF-1.4 test dokument inhalt " + b"x" * 100
TXT = "Kündigung erhalten am 01.07.2026, Frist bis zum 22.07.2026.".encode("utf-8")


def test_unbekannter_dateityp_wird_abgelehnt():
    with pytest.raises(UploadFehler, match="nicht unterstützt"):
        upload.validieren("virus.exe", b"MZ....")


def test_leere_datei_wird_abgelehnt():
    with pytest.raises(UploadFehler, match="leer"):
        upload.validieren("leer.pdf", b"")


def test_zu_grosse_datei_wird_abgelehnt():
    riesig = b"%PDF" + b"0" * (config.MAX_UPLOAD_BYTES + 1)
    with pytest.raises(UploadFehler, match="zu groß"):
        upload.validieren("gross.pdf", riesig)


def test_falsche_magic_bytes_werden_abgelehnt():
    with pytest.raises(UploadFehler, match="Dateikopf"):
        upload.validieren("fake.pdf", b"Das ist gar kein PDF, nur Text.")
    with pytest.raises(UploadFehler, match="Dateikopf"):
        upload.validieren("fake.png", b"%PDF-1.4 ...")


def test_virenscan_eicar_wird_abgelehnt():
    eicar = (b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-"
             b"FILE!$H+H*")
    with pytest.raises(UploadFehler, match="Virenscan"):
        upload.validieren("test.txt", eicar)


def test_gueltige_dateien_passieren():
    assert upload.validieren("brief.pdf", PDF_MINI) == ".pdf"
    assert upload.validieren("notiz.txt", TXT) == ".txt"
    assert upload.validieren("scan.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 50) == ".png"


def test_speichern_verschluesselt_und_metadaten(fall):
    meta = upload.speichern(fall["fall_id"], "kuendigung.txt", TXT)
    assert meta["originalname"] == "kuendigung.txt"
    assert meta["ordner"] == "dokumente"
    assert meta["datei"].endswith(".enc")
    # Auf der Platte liegt NICHT der Klartext
    from app import faelle
    pfad = faelle.fall_ordner_holen(fall["fall_id"]) / "dokumente" / meta["datei"]
    roh = pfad.read_bytes()
    assert TXT not in roh
    assert krypto.entschluesseln(roh) == TXT


def test_eml_landet_in_kommunikation(fall):
    eml = (b"From: a@example.org\r\nTo: b@example.org\r\n"
           b"Subject: Zusage\r\nDate: Mon, 01 Jun 2026 10:00:00 +0200\r\n\r\n"
           b"Wir werden den Mangel bis zum 15.08.2026 beheben, das ist zugesagt.")
    meta = upload.speichern(fall["fall_id"], "mail.eml", eml)
    assert meta["ordner"] == "kommunikation"


def test_dateiname_wird_bereinigt(fall):
    meta = upload.speichern(fall["fall_id"], "../../../etc/passwd.txt", TXT)
    assert "/" not in meta["originalname"]
    assert ".." not in meta["originalname"]
