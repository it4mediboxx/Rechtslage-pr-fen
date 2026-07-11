"""Test-Setup: isoliertes Datenverzeichnis, initialisierte DB, API-Client.

WICHTIG: Die Umgebungsvariable muss VOR dem ersten Import von app.config
gesetzt sein – deshalb passiert das hier auf Modulebene.
"""

import os
import sys
import tempfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="rechtslage-tests-")
os.environ["RECHTSLAGE_DATEN"] = _TMP
os.environ.pop("ANTHROPIC_API_KEY", None)  # Tests laufen ohne externe KI

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

from app import config, datenbank  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _db():
    config.verzeichnisse_anlegen()
    datenbank.initialisieren()
    yield
    datenbank.schliessen()


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def fall():
    """Frischer Fall im Arbeitsrecht für Tests."""
    from app import faelle
    return faelle.fall_anlegen("Max", "Muster", "max@example.org", "Arbeitsrecht")
