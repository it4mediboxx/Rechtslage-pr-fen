"""FastAPI-Anwendung: REST-API + Auslieferung des Frontends.

Start:  uvicorn app.main:app --reload
"""

import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import (analyse, config, datenbank, faelle, fehlerlog, upload, vorlagen)
from .faelle import FallFehler
from .upload import UploadFehler
from .vorlagen import VorlagenFehler

@asynccontextmanager
async def _lebenszyklus(_: FastAPI):
    config.verzeichnisse_anlegen()
    datenbank.initialisieren()
    yield


app = FastAPI(
    title="Rechtslage-Check",
    description="Persönliche Rechtslage-Einschätzung nach deutschem Recht. "
                + config.BERATUNGSHINWEIS + " " + config.RDG_HINWEIS,
    version="1.0.0",
    lifespan=_lebenszyklus,
)

_STATIC = Path(__file__).resolve().parent.parent / "static"


@app.exception_handler(FallFehler)
@app.exception_handler(UploadFehler)
@app.exception_handler(VorlagenFehler)
async def _validierungsfehler(_, exc):
    return JSONResponse(status_code=400, content={"fehler": str(exc)})


@app.exception_handler(Exception)
async def _serverfehler(_, exc):
    fehlerlog.protokollieren("api", f"Unerwarteter Fehler: {exc}", kritisch=True)
    return JSONResponse(
        status_code=500,
        content={"fehler": "Interner Fehler. Details stehen im Fehlerlog."},
    )


# ---------------------------------------------------------------------------
# Stammdaten & Hinweise
# ---------------------------------------------------------------------------

@app.get("/api/info")
def info():
    return {
        "rechtsbereiche": config.RECHTSBEREICHE,
        "beratungshinweis": config.BERATUNGSHINWEIS,
        "rdg_hinweis": config.RDG_HINWEIS,
        "max_upload_mb": config.MAX_UPLOAD_BYTES // (1024 * 1024),
        "erlaubte_formate": sorted(config.ERLAUBTE_ENDUNGEN),
    }


@app.get("/api/benachrichtigungen")
def benachrichtigungen():
    return fehlerlog.benachrichtigungen()


# ---------------------------------------------------------------------------
# Fälle
# ---------------------------------------------------------------------------

class FallAnlage(BaseModel):
    vorname: str = Field(min_length=1, max_length=80)
    nachname: str = Field(min_length=1, max_length=80)
    email: str = Field(default="", max_length=120)
    rechtsbereich: str
    beschreibung: str = Field(default="", max_length=4000)


@app.get("/api/faelle")
def faelle_liste():
    return faelle.alle_faelle()


@app.post("/api/faelle", status_code=201)
def fall_anlegen(daten: FallAnlage):
    return faelle.fall_anlegen(
        daten.vorname, daten.nachname, daten.email,
        daten.rechtsbereich, daten.beschreibung,
    )


@app.get("/api/faelle/{fall_id}")
def fall_detail(fall_id: str):
    return faelle.fall_holen(fall_id)


@app.delete("/api/faelle/{fall_id}")
def fall_loeschen(fall_id: str):
    return faelle.fall_loeschen(fall_id)


# ---------------------------------------------------------------------------
# Upload & Dokumente
# ---------------------------------------------------------------------------

@app.post("/api/faelle/{fall_id}/upload", status_code=201)
async def hochladen(fall_id: str, datei: UploadFile = File(...)):
    inhalt = await datei.read()
    meta = upload.speichern(fall_id, datei.filename or "datei", inhalt)
    meta["beratungshinweis"] = config.BERATUNGSHINWEIS
    return meta


@app.get("/api/faelle/{fall_id}/dokumente")
def dokumente(fall_id: str):
    return upload.dokumente_auflisten(fall_id)


# ---------------------------------------------------------------------------
# Analyse (asynchron mit Fortschritt)
# ---------------------------------------------------------------------------

@app.post("/api/faelle/{fall_id}/analyse", status_code=202)
def analyse_starten(fall_id: str):
    faelle.fall_holen(fall_id)  # validiert die Fall-ID
    stand = analyse.fortschritt_holen(fall_id)
    if stand["status"] == "läuft":
        return {"gestartet": False, "hinweis": "Analyse läuft bereits.", **stand}

    def _lauf():
        try:
            analyse.analyse_durchfuehren(fall_id)
        except Exception:
            pass  # Status/Fehlerlog sind in analyse_durchfuehren versorgt

    threading.Thread(target=_lauf, daemon=True).start()
    return {"gestartet": True, "hinweis": "Analyse läuft asynchron.",
            "beratungshinweis": config.BERATUNGSHINWEIS}


@app.get("/api/faelle/{fall_id}/analyse/fortschritt")
def analyse_fortschritt(fall_id: str):
    return analyse.fortschritt_holen(fall_id)


@app.get("/api/faelle/{fall_id}/analyse")
def analyse_ergebnis(fall_id: str):
    ergebnis = analyse.analyse_laden(fall_id)
    if ergebnis is None:
        raise HTTPException(404, "Für diesen Fall liegt noch keine Analyse vor.")
    return ergebnis


@app.get("/api/faelle/{fall_id}/zeitleiste")
def zeitleiste(fall_id: str):
    ergebnis = analyse.analyse_laden(fall_id)
    return ergebnis["zeitleiste"] if ergebnis else []


# ---------------------------------------------------------------------------
# Vorlagen & Schreiben
# ---------------------------------------------------------------------------

class SchreibenAuftrag(BaseModel):
    vorlage_id: str
    werte: dict[str, str] = Field(default_factory=dict)


@app.get("/api/vorlagen")
def vorlagen_liste():
    return [{"id": v["id"], "titel": v["titel"], "platzhalter": v["platzhalter"]}
            for v in vorlagen.alle_vorlagen()]


@app.post("/api/faelle/{fall_id}/schreiben", status_code=201)
def schreiben_erzeugen(fall_id: str, auftrag: SchreibenAuftrag):
    return vorlagen.generieren(fall_id, auftrag.vorlage_id, auftrag.werte)


@app.get("/api/faelle/{fall_id}/schreiben")
def schreiben_liste(fall_id: str):
    return vorlagen.schreiben_auflisten(fall_id)


@app.get("/api/faelle/{fall_id}/schreiben/{datei}")
def schreiben_text(fall_id: str, datei: str):
    return PlainTextResponse(vorlagen.schreiben_laden(fall_id, datei))


# ---------------------------------------------------------------------------
# Gesetzesdatenbank
# ---------------------------------------------------------------------------

@app.get("/api/gesetze/suche")
def gesetze_suche(q: str = ""):
    return datenbank.volltextsuche(q)


@app.get("/api/gesetze/protokoll")
def gesetze_protokoll():
    return datenbank.update_protokoll()


@app.get("/api/gesetze/{kuerzel}/{paragraph}")
def gesetz_detail(kuerzel: str, paragraph: str):
    eintrag = datenbank.paragraph_holen(kuerzel, paragraph)
    if eintrag is None:
        raise HTTPException(404, "Paragraph nicht in der Datenbank.")
    return eintrag


# ---------------------------------------------------------------------------
# Frontend
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
def index():
    return FileResponse(_STATIC / "index.html")


@app.get("/intro", include_in_schema=False)
def intro():
    return FileResponse(_STATIC / "intro.html")


app.mount("/static", StaticFiles(directory=_STATIC), name="static")
