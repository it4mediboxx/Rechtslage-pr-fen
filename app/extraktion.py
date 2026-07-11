"""Textextraktion je Dateityp inkl. OCR-Pipeline.

Jedes Ergebnis meldet Qualität zurück: Ist der extrahierte Text zu kurz
oder OCR nicht verfügbar, gibt es einen expliziten Hinweis statt einer
stillen Fehlanalyse.
"""

import io
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
import zipfile
from email import policy
from email.parser import BytesParser

from . import config, fehlerlog

_HINWEIS_UNLESERLICH = (
    "Das Dokument konnte nicht zuverlässig gelesen werden. Bitte einen besser "
    "lesbaren Scan oder das Original hochladen – es wurde bewusst KEINE "
    "Analyse auf Basis unleserlicher Inhalte durchgeführt."
)
_HINWEIS_OCR_FEHLT = (
    "Für Scans/Fotos ist eine OCR-Texterkennung nötig (Tesseract), die auf "
    "diesem System nicht installiert ist. Das Dokument wurde gespeichert, "
    "aber nicht analysiert."
)


def _ergebnis(text: str, hinweise: list[str] | None = None, datum: str = "") -> dict:
    text = (text or "").strip()
    hinweise = list(hinweise or [])
    lesbar = len(text) >= config.OCR_MIN_ZEICHEN
    if not lesbar and not hinweise:
        hinweise.append(_HINWEIS_UNLESERLICH)
    return {"text": text, "lesbar": lesbar, "hinweise": hinweise, "datum": datum}


def _pdf(inhalt: bytes) -> dict:
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(inhalt))
        text = "\n".join((seite.extract_text() or "") for seite in reader.pages)
    except Exception as exc:
        fehlerlog.protokollieren("extraktion", f"PDF unlesbar: {exc}")
        return _ergebnis("", [_HINWEIS_UNLESERLICH])
    if len(text.strip()) < config.OCR_MIN_ZEICHEN:
        # Vermutlich gescanntes PDF ohne Textebene -> OCR-Hinweis
        return _ergebnis(text, [_HINWEIS_OCR_FEHLT if not _tesseract_verfuegbar()
                                else _HINWEIS_UNLESERLICH])
    return _ergebnis(text)


def _docx(inhalt: bytes) -> dict:
    try:
        with zipfile.ZipFile(io.BytesIO(inhalt)) as z:
            xml = z.read("word/document.xml")
        wurzel = ET.fromstring(xml)
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        absaetze = []
        for absatz in wurzel.iter(f"{ns}p"):
            teile = [knoten.text or "" for knoten in absatz.iter(f"{ns}t")]
            if teile:
                absaetze.append("".join(teile))
        return _ergebnis("\n".join(absaetze))
    except (zipfile.BadZipFile, KeyError, ET.ParseError) as exc:
        fehlerlog.protokollieren("extraktion", f"DOCX unlesbar: {exc}")
        return _ergebnis("", [_HINWEIS_UNLESERLICH])


def _doc(inhalt: bytes) -> dict:
    antiword = shutil.which("antiword")
    if antiword:
        try:
            ergebnis = subprocess.run(
                [antiword, "-"], input=inhalt, capture_output=True,
                timeout=config.EXTERN_TIMEOUT_SEK,
            )
            if ergebnis.returncode == 0:
                return _ergebnis(ergebnis.stdout.decode("utf-8", "replace"))
        except (subprocess.TimeoutExpired, OSError) as exc:
            fehlerlog.protokollieren("extraktion", f"antiword fehlgeschlagen: {exc}")
    # Fallback: lesbare Zeichenketten aus dem Binärformat ziehen
    texte = re.findall(rb"[\x20-\x7e\xc0-\xff]{6,}", inhalt)
    roh = " ".join(t.decode("latin-1", "replace") for t in texte)
    roh = re.sub(r"\s+", " ", roh)
    hinweise = []
    if len(roh) < config.OCR_MIN_ZEICHEN:
        hinweise.append(_HINWEIS_UNLESERLICH)
    else:
        hinweise.append(
            "Altes .doc-Format ohne Konverter gelesen – bitte Ergebnis prüfen "
            "oder als .docx/.pdf hochladen."
        )
    return _ergebnis(roh, hinweise)


def _tesseract_verfuegbar() -> bool:
    return shutil.which("tesseract") is not None


def _bild(inhalt: bytes) -> dict:
    """OCR-Pipeline für Scans/Fotos."""
    if not _tesseract_verfuegbar():
        return _ergebnis("", [_HINWEIS_OCR_FEHLT])
    try:
        ergebnis = subprocess.run(
            ["tesseract", "stdin", "stdout", "-l", "deu+eng"],
            input=inhalt, capture_output=True, timeout=config.EXTERN_TIMEOUT_SEK,
        )
        text = ergebnis.stdout.decode("utf-8", "replace")
        if len(text.strip()) < config.OCR_MIN_ZEICHEN:
            return _ergebnis(text, [_HINWEIS_UNLESERLICH])
        return _ergebnis(text)
    except (subprocess.TimeoutExpired, OSError) as exc:
        fehlerlog.protokollieren("extraktion", f"OCR fehlgeschlagen: {exc}")
        return _ergebnis("", [_HINWEIS_UNLESERLICH])


def _eml(inhalt: bytes) -> dict:
    try:
        nachricht = BytesParser(policy=policy.default).parsebytes(inhalt)
        koerper = nachricht.get_body(preferencelist=("plain", "html"))
        text = koerper.get_content() if koerper else ""
        if koerper is not None and koerper.get_content_type() == "text/html":
            text = re.sub(r"<[^>]+>", " ", text)
        kopf = (
            f"Von: {nachricht.get('From', '')}\n"
            f"An: {nachricht.get('To', '')}\n"
            f"Datum: {nachricht.get('Date', '')}\n"
            f"Betreff: {nachricht.get('Subject', '')}\n\n"
        )
        return _ergebnis(kopf + text, datum=str(nachricht.get("Date", "")))
    except Exception as exc:
        fehlerlog.protokollieren("extraktion", f"EML unlesbar: {exc}")
        return _ergebnis("", [_HINWEIS_UNLESERLICH])


def _msg(inhalt: bytes) -> dict:
    # Outlook-.msg (OLE-Compound): Text liegt als UTF-16 in den Streams.
    treffer = re.findall(rb"(?:[\x20-\x7e\xc4\xd6\xdc\xe4\xf6\xfc\xdf]\x00){8,}", inhalt)
    texte = [t.decode("utf-16-le", "ignore") for t in treffer]
    text = "\n".join(t for t in texte if t.strip())
    hinweise = ["Outlook-.msg wurde heuristisch gelesen – bitte Inhalt prüfen "
                "oder die Mail als .eml exportieren."]
    if len(text.strip()) < config.OCR_MIN_ZEICHEN:
        return _ergebnis(text, [_HINWEIS_UNLESERLICH])
    return _ergebnis(text, hinweise)


def _txt(inhalt: bytes) -> dict:
    for kodierung in ("utf-8", "latin-1"):
        try:
            return _ergebnis(inhalt.decode(kodierung))
        except UnicodeDecodeError:
            continue
    return _ergebnis(inhalt.decode("utf-8", "replace"))


_EXTRAKTOREN = {
    ".pdf": _pdf, ".docx": _docx, ".doc": _doc,
    ".jpg": _bild, ".jpeg": _bild, ".png": _bild,
    ".eml": _eml, ".msg": _msg, ".txt": _txt,
}


def text_extrahieren(endung: str, inhalt: bytes) -> dict:
    """Zentraler Einstieg: liefert {text, lesbar, hinweise, datum}."""
    extraktor = _EXTRAKTOREN.get(endung.lower())
    if extraktor is None:
        return _ergebnis("", [f"Kein Extraktor für {endung} vorhanden."])
    return extraktor(inhalt)
