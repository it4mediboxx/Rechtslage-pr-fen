"""Integrationstests: Upload → Verarbeitung → Analyse → Ergebnis → Schreiben.

Kompletter Durchlauf über die HTTP-API (wie das Frontend ihn nutzt),
inklusive Performance-Vorgabe (Upload-Bestätigung < 2 s) und sichtbarem
Beratungshinweis an allen Ausgabestellen.
"""

import time


def _fall_anlegen(client, bereich="Wohnrecht", beschreibung=""):
    antwort = client.post("/api/faelle", json={
        "vorname": "Anna", "nachname": "Fall", "email": "anna@example.org",
        "rechtsbereich": bereich, "beschreibung": beschreibung,
    })
    assert antwort.status_code == 201, antwort.text
    return antwort.json()["fall_id"]


def _analyse_abwarten(client, fall_id, timeout=60):
    antwort = client.post(f"/api/faelle/{fall_id}/analyse")
    assert antwort.status_code == 202
    ende = time.time() + timeout
    while time.time() < ende:
        stand = client.get(f"/api/faelle/{fall_id}/analyse/fortschritt").json()
        if stand["status"] in ("fertig", "fehler"):
            return stand
        time.sleep(0.2)
    raise AssertionError("Analyse wurde nicht rechtzeitig fertig.")


def test_info_und_hinweise(client):
    info = client.get("/api/info").json()
    assert len(info["rechtsbereiche"]) == 5
    assert info["beratungshinweis"] == "Ersetzt keine anwaltliche Beratung."
    assert "RDG-Prüfung" in info["rdg_hinweis"]


def test_kompletter_durchlauf(client):
    fall_id = _fall_anlegen(
        client, "Wohnrecht",
        "Seit dem 01.06.2026 Schimmel im Schlafzimmer. Vermieter wurde am "
        "05.06.2026 informiert. Frist zur Beseitigung bis zum 31.07.2026 gesetzt.",
    )

    # Upload mit Bestätigung < 2 s
    start = time.perf_counter()
    antwort = client.post(
        f"/api/faelle/{fall_id}/upload",
        files={"datei": ("maengelanzeige.txt",
                         "Mängelanzeige: Schimmel in der Wohnung, Frist bis zum "
                         "31.07.2026 zur Beseitigung.".encode("utf-8"), "text/plain")},
    )
    dauer = time.perf_counter() - start
    assert antwort.status_code == 201, antwort.text
    assert dauer < 2.0, f"Upload-Bestätigung dauerte {dauer:.2f} s"
    assert antwort.json()["beratungshinweis"]

    # E-Mail in die Kommunikation
    eml = ("From: vermieter@example.org\r\nTo: anna@example.org\r\n"
           "Subject: Schimmel\r\nDate: Mon, 08 Jun 2026 09:00:00 +0200\r\n\r\n"
           "Wir werden den Schaden bis zum 15.07.2026 beheben, das ist zugesagt.")
    antwort = client.post(
        f"/api/faelle/{fall_id}/upload",
        files={"datei": ("vermieter.eml", eml.encode("utf-8"), "message/rfc822")},
    )
    assert antwort.json()["ordner"] == "kommunikation"

    # Analyse asynchron mit Fortschritt
    stand = _analyse_abwarten(client, fall_id)
    assert stand["status"] == "fertig"

    ergebnis = client.get(f"/api/faelle/{fall_id}/analyse").json()
    zitiert = {(p["gesetz"], p["paragraph"]) for p in ergebnis["paragraphen"]}
    assert ("BGB", "§ 536") in zitiert
    assert all(p["fassung_stand"] for p in ergebnis["paragraphen"])
    assert ergebnis["beratungshinweis"] == "Ersetzt keine anwaltliche Beratung."
    assert "mietminderung-schimmel" in ergebnis["vorlagen_vorschlaege"]

    # Zeitleiste enthält Frist und Zusage aus Dokument + E-Mail
    zeitleiste = client.get(f"/api/faelle/{fall_id}/zeitleiste").json()
    daten = {e["datum"] for e in zeitleiste}
    assert "2026-07-31" in daten
    assert "2026-07-15" in daten

    # Schreiben generieren -> landet im Ordner vorlagen/
    antwort = client.post(f"/api/faelle/{fall_id}/schreiben", json={
        "vorlage_id": "mietminderung-schimmel",
        "werte": {"WOHNUNG": "Musterstr. 1", "MINDERUNGSQUOTE": "15",
                  "DATUM_MANGEL": "01.06.2026"},
    })
    assert antwort.status_code == 201, antwort.text
    schreiben = antwort.json()
    assert "§ 536" in schreiben["text"]
    assert "Anna Fall" in schreiben["text"]
    assert schreiben["beratungshinweis"]

    liste = client.get(f"/api/faelle/{fall_id}/schreiben").json()
    assert any(s["datei"] == schreiben["datei"] for s in liste)
    text = client.get(f"/api/faelle/{fall_id}/schreiben/{schreiben['datei']}")
    assert "Musterstr. 1" in text.text

    # Status ist jetzt "analysiert"
    fall = client.get(f"/api/faelle/{fall_id}").json()
    assert fall["status"] == "analysiert"


def test_upload_ablehnung_verstaendlich(client):
    fall_id = _fall_anlegen(client, "Privatrecht")
    antwort = client.post(
        f"/api/faelle/{fall_id}/upload",
        files={"datei": ("boese.exe", b"MZ\x90\x00", "application/octet-stream")},
    )
    assert antwort.status_code == 400
    assert "nicht unterstützt" in antwort.json()["fehler"]


def test_typ_plausibilitaet_warnung(client):
    # Nebenkostenabrechnung im Arbeitsrecht -> Warnhinweis
    fall_id = _fall_anlegen(client, "Arbeitsrecht", "Prüfung eines Dokuments.")
    client.post(
        f"/api/faelle/{fall_id}/upload",
        files={"datei": ("abrechnung.txt",
                         "Betriebskostenabrechnung für den Abrechnungszeitraum 2024, "
                         "Nachzahlung 300 Euro.".encode("utf-8"), "text/plain")},
    )
    _analyse_abwarten(client, fall_id)
    ergebnis = client.get(f"/api/faelle/{fall_id}/analyse").json()
    assert any("untypisch" in w for w in ergebnis["warnhinweise"])


def test_gesetzessuche_api(client):
    treffer = client.get("/api/gesetze/suche", params={"q": "Kündigungsfrist"}).json()
    assert any(t["paragraph"] == "§ 622" for t in treffer)
    eintrag = client.get("/api/gesetze/BGB/§ 622").json()
    assert eintrag["fassung_stand"]
    assert client.get("/api/gesetze/BGB/§ 0").status_code == 404


def test_fall_loeschen_api(client):
    fall_id = _fall_anlegen(client, "Privatrecht")
    antwort = client.delete(f"/api/faelle/{fall_id}")
    assert antwort.status_code == 200
    assert client.get(f"/api/faelle/{fall_id}").status_code == 400


def test_frontend_erreichbar_mit_hinweis(client):
    seite = client.get("/")
    assert seite.status_code == 200
    assert "Ersetzt keine anwaltliche Beratung" in seite.text
    assert "RDG-Prüfung" in seite.text
