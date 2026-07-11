"""Verschlüsselte Speicherung (AES-128-CBC + HMAC via Fernet).

Dokumente enthalten Namen, Finanz- und Vertragsdaten und werden deshalb
ausschließlich verschlüsselt auf der Platte abgelegt (Endung ``.enc``).
Der Schlüssel liegt lokal in einer Datei mit restriktiven Rechten.
"""

import os
import stat

from cryptography.fernet import Fernet, InvalidToken

from . import config


def _schluessel_laden() -> bytes:
    pfad = config.SCHLUESSEL_PFAD
    if pfad.exists():
        return pfad.read_bytes().strip()
    config.verzeichnisse_anlegen()
    schluessel = Fernet.generate_key()
    pfad.write_bytes(schluessel)
    os.chmod(pfad, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    return schluessel


def _fernet() -> Fernet:
    return Fernet(_schluessel_laden())


def verschluesseln(daten: bytes) -> bytes:
    return _fernet().encrypt(daten)


def entschluesseln(daten: bytes) -> bytes:
    try:
        return _fernet().decrypt(daten)
    except InvalidToken as exc:
        raise ValueError(
            "Entschlüsselung fehlgeschlagen – Schlüssel oder Datei beschädigt."
        ) from exc
