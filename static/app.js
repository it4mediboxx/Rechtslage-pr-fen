/* Rechtslage · Frontend (SPA, ohne Abhängigkeiten) */
"use strict";

const app = document.getElementById("app");
let info = { rechtsbereiche: [], beratungshinweis: "", max_upload_mb: 25, erlaubte_formate: [] };

/* ---------- Hilfen ---------- */

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

async function api(pfad, optionen = {}) {
  const antwort = await fetch(pfad, optionen);
  const daten = await antwort.json().catch(() => ({}));
  if (!antwort.ok) throw new Error(daten.fehler || daten.detail || "Unbekannter Fehler.");
  return daten;
}

let meldungTimer = null;
function meldung(text) {
  let el = document.querySelector(".meldung");
  if (!el) {
    el = document.createElement("div");
    el.className = "meldung";
    document.body.appendChild(el);
  }
  el.textContent = text;
  el.classList.add("sichtbar");
  clearTimeout(meldungTimer);
  meldungTimer = setTimeout(() => el.classList.remove("sichtbar"), 4200);
}

function datumSchoen(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return isNaN(d) ? esc(iso) : d.toLocaleDateString("de-DE", { day: "2-digit", month: "long", year: "numeric" });
}

const STATUS_TEXT = {
  offen: "Offen", in_analyse: "In Analyse",
  analysiert: "Analysiert", unvollstaendig: "Unvollständig",
};

/* ---------- Router ---------- */

const routen = [
  [/^#?\/?$/, ansichtStart],
  [/^#\/neu$/, ansichtNeuerFall],
  [/^#\/fall\/([0-9a-f\-]+)(?:\/([a-z]+))?$/, (m) => ansichtFall(m[1], m[2] || "dokumente")],
  [/^#\/gesetze$/, ansichtGesetze],
];

async function navigieren() {
  const hash = location.hash || "#/";
  document.querySelectorAll(".nav-links a").forEach(a => {
    const ziel = a.getAttribute("data-nav");
    a.classList.toggle("aktiv",
      (ziel === "faelle" && (hash === "#/" || hash.startsWith("#/fall"))) ||
      (ziel === "neu" && hash === "#/neu") ||
      (ziel === "gesetze" && hash === "#/gesetze"));
  });
  for (const [muster, handler] of routen) {
    const m = hash.match(muster);
    if (m) { try { await handler(m); } catch (e) { fehlerAnsicht(e); } return; }
  }
  fehlerAnsicht(new Error("Seite nicht gefunden."));
}

function fehlerAnsicht(e) {
  app.innerHTML = `<section class="abschnitt"><div class="leer">
    <h2 style="margin-bottom:10px">Das hat nicht geklappt</h2>
    <p>${esc(e.message)}</p>
    <p style="margin-top:22px"><a class="knopf" href="#/">Zur Übersicht</a></p>
  </div></section>`;
}

/* ---------- Start: Hero + Fälle ---------- */

async function ansichtStart() {
  const faelle = await api("/api/faelle");
  const karten = faelle.map(f => `
    <a class="karte" href="#/fall/${esc(f.fall_id)}">
      <span class="etikett">${esc(f.rechtsbereich)}</span>
      <h3>${esc(f.nachname)}, ${esc(f.vorname)}</h3>
      <p class="meta">Angelegt am ${datumSchoen(f.erstellungsdatum)} ·
        ${f.dokumente_anzahl} Dokument${f.dokumente_anzahl === 1 ? "" : "e"}</p>
      <p class="meta" style="margin-top:12px">
        <span class="abzeichen ${f.status === "analysiert" ? "invers" : ""}">${esc(STATUS_TEXT[f.status] || f.status)}</span>
      </p>
    </a>`).join("");

  app.innerHTML = `
    <section class="held">
      <h1>Rechtslage.<br>Klar&nbsp;geprüft.</h1>
      <p class="unterzeile">Dokumente hochladen, Fristen im Blick behalten und die eigene
        Rechtslage anhand aktueller Gesetzestexte einschätzen – ruhig, präzise, privat.</p>
      <div class="aktionen">
        <a class="knopf" href="#/neu">Neuen Fall anlegen</a>
        <a class="knopf sekundaer" href="#/gesetze">Gesetze durchsuchen</a>
        <a class="knopf sekundaer" href="/intro">▶&thinsp;Film-Vorschau</a>
      </div>
    </section>
    <section class="abschnitt">
      <h2>Meine Fälle</h2>
      <p class="beschreibung">Jeder Fall bündelt Dokumente, Kommunikation, Fristen, Analyse
        und fertige Schreiben in einer verschlüsselten Ablage.</p>
      ${faelle.length ? `<div class="kartenraster">${karten}</div>`
        : `<div class="leer">Noch keine Fälle. <br><br><a class="knopf" href="#/neu">Ersten Fall anlegen</a></div>`}
    </section>`;
}

/* ---------- Neuer Fall ---------- */

function ansichtNeuerFall() {
  const optionen = info.rechtsbereiche.map(b => `<option>${esc(b)}</option>`).join("");
  app.innerHTML = `
    <section class="abschnitt" style="padding-top:72px">
      <h2>Neuer Fall</h2>
      <p class="beschreibung">Rechtsbereich wählen und den Fall kurz beschreiben.
        Die Ordnerstruktur wird automatisch angelegt.</p>
      <form class="formular" id="fall-formular">
        <div class="feld"><label for="vorname">Vorname</label>
          <input id="vorname" required maxlength="80" autocomplete="given-name"></div>
        <div class="feld"><label for="nachname">Nachname</label>
          <input id="nachname" required maxlength="80" autocomplete="family-name"></div>
        <div class="feld"><label for="email">E-Mail (optional)</label>
          <input id="email" type="email" maxlength="120" autocomplete="email"></div>
        <div class="feld"><label for="bereich">Rechtsbereich</label>
          <select id="bereich">${optionen}</select></div>
        <div class="feld"><label for="beschreibung">Worum geht es? (optional, fließt in die Analyse ein)</label>
          <textarea id="beschreibung" maxlength="4000"
            placeholder="z. B.: Kündigung am 03.07.2026 erhalten, seit 6 Jahren im Betrieb, 25 Mitarbeiter …"></textarea></div>
        <button class="knopf" type="submit">Fall anlegen</button>
      </form>
    </section>`;
  document.getElementById("fall-formular").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    try {
      const fall = await api("/api/faelle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          vorname: document.getElementById("vorname").value,
          nachname: document.getElementById("nachname").value,
          email: document.getElementById("email").value,
          rechtsbereich: document.getElementById("bereich").value,
          beschreibung: document.getElementById("beschreibung").value,
        }),
      });
      meldung("Fall angelegt.");
      location.hash = `#/fall/${fall.fall_id}`;
    } catch (e) { meldung(e.message); }
  });
}

/* ---------- Falldetail mit Tabs ---------- */

async function ansichtFall(fallId, tab) {
  const fall = await api(`/api/faelle/${fallId}`);
  const tabs = [
    ["dokumente", "Dokumente"], ["zeitleiste", "Fristen & Zeitleiste"],
    ["analyse", "Analyse"], ["schreiben", "Schreiben"],
  ];
  app.innerHTML = `
    <section class="abschnitt" style="padding-top:64px">
      <span class="etikett" style="font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:var(--tinte-3)">${esc(fall.rechtsbereich)}</span>
      <h2>${esc(fall.nachname)}, ${esc(fall.vorname)}</h2>
      <p class="beschreibung" style="margin-bottom:8px">
        Fall ${esc(fall.fall_id)} · angelegt am ${datumSchoen(fall.erstellungsdatum)} ·
        <span class="abzeichen">${esc(STATUS_TEXT[fall.status] || fall.status)}</span></p>
      ${fall.beschreibung ? `<p class="beschreibung">„${esc(fall.beschreibung)}“</p>` : ""}
      <div class="tabs">${tabs.map(([id, name]) =>
        `<button data-tab="${id}" class="${id === tab ? "aktiv" : ""}">${name}</button>`).join("")}
        <button data-aktion="loeschen" style="color:var(--tinte-3)">Fall löschen</button>
      </div>
      <div id="tab-inhalt"></div>
    </section>`;
  document.querySelectorAll("[data-tab]").forEach(k =>
    k.addEventListener("click", () => { location.hash = `#/fall/${fallId}/${k.dataset.tab}`; }));
  document.querySelector("[data-aktion=loeschen]").addEventListener("click", async () => {
    if (!confirm("Diesen Fall vollständig und unwiderruflich löschen? Die Löschung wird protokolliert.")) return;
    await api(`/api/faelle/${fallId}`, { method: "DELETE" });
    meldung("Fall vollständig gelöscht (protokolliert).");
    location.hash = "#/";
  });
  const inhalt = document.getElementById("tab-inhalt");
  if (tab === "dokumente") await tabDokumente(inhalt, fallId);
  else if (tab === "zeitleiste") await tabZeitleiste(inhalt, fallId);
  else if (tab === "analyse") await tabAnalyse(inhalt, fallId, fall);
  else if (tab === "schreiben") await tabSchreiben(inhalt, fallId);
}

/* ---------- Tab: Dokumente ---------- */

async function tabDokumente(inhalt, fallId) {
  const dokumente = await api(`/api/faelle/${fallId}/dokumente`);
  inhalt.innerHTML = `
    <div class="ablage" id="ablage" role="button" tabindex="0" aria-label="Dateien hochladen">
      <strong>Dateien hierher ziehen</strong> oder klicken zum Auswählen
      <span class="formate">${info.erlaubte_formate.join(" · ")} · max. ${info.max_upload_mb} MB ·
      Virenscan &amp; Typprüfung bei jedem Upload · verschlüsselte Ablage</span>
      <input type="file" id="datei-eingabe" multiple hidden>
    </div>
    <div id="upload-status" style="margin:14px 0"></div>
    ${dokumente.length ? `<ul class="zeilenliste" style="margin-top:22px">${dokumente.map(d => `
      <li><span>${esc(d.originalname)} <span class="abzeichen hohl" style="margin-left:8px">${esc(d.typ)}</span></span>
      <span class="neben">${datumSchoen(d.hochgeladen)} · ${Math.max(1, Math.round(d.groesse_bytes / 1024))} KB · ${d.ordner === "kommunikation" ? "Kommunikation" : "Dokumente"}</span></li>`).join("")}
    </ul>` : `<p class="beschreibung" style="margin-top:20px">Noch keine Dokumente hochgeladen.</p>`}`;

  const ablage = document.getElementById("ablage");
  const eingabe = document.getElementById("datei-eingabe");
  ablage.addEventListener("click", () => eingabe.click());
  ablage.addEventListener("keydown", ev => { if (ev.key === "Enter" || ev.key === " ") eingabe.click(); });
  ["dragover", "dragleave", "drop"].forEach(art => ablage.addEventListener(art, ev => {
    ev.preventDefault();
    ablage.classList.toggle("aktiv", art === "dragover");
    if (art === "drop") hochladen(ev.dataTransfer.files);
  }));
  eingabe.addEventListener("change", () => hochladen(eingabe.files));

  async function hochladen(dateien) {
    const status = document.getElementById("upload-status");
    for (const datei of dateien) {
      status.innerHTML = `<div class="hinweiskasten">Lade „${esc(datei.name)}“ hoch …</div>`;
      const formular = new FormData();
      formular.append("datei", datei);
      try {
        await api(`/api/faelle/${fallId}/upload`, { method: "POST", body: formular });
        meldung(`„${datei.name}“ gespeichert.`);
      } catch (e) {
        status.innerHTML = `<div class="hinweiskasten">${esc(e.message)}</div>`;
        meldung(e.message);
        return;
      }
    }
    await tabDokumente(inhalt, fallId);
  }
}

/* ---------- Tab: Zeitleiste ---------- */

async function tabZeitleiste(inhalt, fallId) {
  const eintraege = await api(`/api/faelle/${fallId}/zeitleiste`);
  if (!eintraege.length) {
    inhalt.innerHTML = `<div class="leer">Noch keine Fristen oder Zusagen erkannt.<br>
      Fristen werden bei der Analyse automatisch aus Dokumenten und Kommunikation extrahiert.</div>`;
    return;
  }
  const stufenText = { "überfällig": "Überfällig", "kritisch": "Kritisch (≤ 7 Tage)", "bald": "Bald (≤ 30 Tage)", "ok": "Ausreichend Zeit" };
  inhalt.innerHTML = `<ul class="zeitleiste">${eintraege.map(e => `
    <li class="stufe-${esc(e.warnstufe || "ok")}">
      <div class="z-datum">${datumSchoen(e.datum)}
        <span class="abzeichen ${["überfällig", "kritisch"].includes(e.warnstufe) ? "invers" : "hohl"}" style="margin-left:8px">
          ${e.art === "Zusage" ? "Zusage" : (e.notfrist ? "NOTFRIST" : "Frist")}${e.warnstufe ? " · " + stufenText[e.warnstufe] : ""}</span></div>
      <div class="z-kontext">${esc(e.kontext)} <em style="color:var(--tinte-3)">(${esc(e.quelle)})</em></div>
    </li>`).join("")}</ul>
    <div class="hinweiskasten">Gesetzliche <strong>Notfristen</strong> (z. B. drei Wochen für die
      Kündigungsschutzklage, § 4 KSchG) sind nicht verlängerbar – richterliche Fristen können auf
      Antrag verlängert werden (§ 224 ZPO).</div>`;
}

/* ---------- Tab: Analyse ---------- */

async function tabAnalyse(inhalt, fallId, fall) {
  let analyse = null;
  try { analyse = await api(`/api/faelle/${fallId}/analyse`); } catch { /* noch keine */ }

  const startKnopf = `<button class="knopf" id="analyse-start">
      ${analyse ? "Analyse erneut durchführen" : "Analyse starten"}</button>
    <p class="beschreibung" style="margin-top:14px;font-size:13px">
      Zitiert ausschließlich Paragraphen aus der lokalen Gesetzesdatenbank inkl. Fassungsstand.
      ${esc(info.beratungshinweis)}</p>
    <div id="analyse-fortschritt"></div>`;

  inhalt.innerHTML = (analyse ? analyseDarstellen(analyse) : "") + `<div style="margin-top:26px">${startKnopf}</div>`;
  bindeParagraphPillen(inhalt);

  document.getElementById("analyse-start").addEventListener("click", async () => {
    const knopf = document.getElementById("analyse-start");
    knopf.disabled = true;
    const anzeige = document.getElementById("analyse-fortschritt");
    try {
      await api(`/api/faelle/${fallId}/analyse`, { method: "POST" });
    } catch (e) { meldung(e.message); knopf.disabled = false; return; }
    const puls = setInterval(async () => {
      try {
        const stand = await api(`/api/faelle/${fallId}/analyse/fortschritt`);
        anzeige.innerHTML = `<div class="fortschritt"><div style="width:${stand.prozent}%"></div></div>
          <p style="font-size:13px;color:var(--tinte-2)">${esc(stand.schritt)}</p>`;
        if (stand.status === "fertig") {
          clearInterval(puls);
          meldung("Analyse abgeschlossen.");
          await ansichtFall(fallId, "analyse"); // kompletter Neuaufbau inkl. Status-Badge
        } else if (stand.status === "fehler") {
          clearInterval(puls);
          anzeige.innerHTML = `<div class="hinweiskasten">${esc(stand.schritt)} Der Fall ist als
            „unvollständig“ markiert und kann erneut analysiert werden.</div>`;
          knopf.disabled = false;
        }
      } catch { /* weiter pollen */ }
    }, 800);
  });
}

function analyseDarstellen(a) {
  const dokZeilen = (a.sachverhalt.dokumente || []).map(d =>
    `<li><span>${esc(d.datei)} <span class="abzeichen hohl" style="margin-left:8px">${esc(d.typ)}</span></span>
     <span class="neben">${esc((d.auszug || "").slice(0, 80))}…</span></li>`).join("");
  const themen = (a.themen || []).map(t => `
    <article class="thema">
      <h3>${esc(t.thema)}${t.im_gewaehlten_bereich ? "" :
        ' <span class="abzeichen hohl">bereichsübergreifend</span>'}</h3>
      <div class="paragraph-pillen">${t.paragraphen.map(p =>
        `<button class="paragraph-pille" data-gesetz="${esc(p.gesetz)}" data-paragraph="${esc(p.paragraph)}"
          title="Fassung: ${esc(p.fassung_stand)}">${esc(p.gesetz)} ${esc(p.paragraph)}</button>`).join("")}</div>
      ${t.chancen ? `<p class="absatz"><strong>Chancen</strong>${esc(t.chancen)}</p>` : ""}
      ${t.risiken ? `<p class="absatz"><strong>Risiken</strong>${esc(t.risiken)}</p>` : ""}
      ${t.ausnahmen?.length ? `<p class="absatz"><strong>Ausnahmen &amp; Sonderregeln</strong>${t.ausnahmen.map(esc).join("<br>")}</p>` : ""}
      <div class="gesetzestext-ziel"></div>
    </article>`).join("");

  return `
    <h3 style="font-size:22px;margin-bottom:14px">Sachverhalt</h3>
    ${a.sachverhalt.beschreibung ? `<p class="beschreibung">„${esc(a.sachverhalt.beschreibung)}“</p>` : ""}
    ${dokZeilen ? `<ul class="zeilenliste" style="margin-bottom:26px">${dokZeilen}</ul>` : ""}
    ${(a.warnhinweise || []).map(w => `<div class="hinweiskasten">${esc(w)}</div>`).join("")}
    ${a.themen?.length ? `<h3 style="font-size:22px;margin:30px 0 14px">Rechtliche Einordnung</h3>${themen}`
      : `<div class="leer" style="margin:20px 0">Keine einschlägigen Regelungen erkannt – bitte
         Fallbeschreibung ergänzen oder Dokumente hochladen.</div>`}
    ${(a.offene_fragen || []).length ? `
      <h3 style="font-size:22px;margin:30px 0 14px">Offene Fragen &amp; fehlende Fakten</h3>
      <ul class="zeilenliste">${a.offene_fragen.map(f => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}
    ${a.ki_einschaetzung ? `
      <h3 style="font-size:22px;margin:30px 0 14px">KI-Einschätzung</h3>
      <div class="thema" style="white-space:pre-wrap">${esc(a.ki_einschaetzung)}</div>` : ""}
    ${a.anwalt_empfohlen ? `<div class="hinweiskasten stark"><strong>Empfehlung:</strong> Dieser Fall ist
      komplex oder folgenreich (Kündigung, Klage, hohe Beträge oder kritische Fristen) –
      eine anwaltliche Prüfung wird ausdrücklich empfohlen.</div>` : ""}
    <div class="hinweiskasten">${esc(a.beratungshinweis)} ${esc(a.rdg_hinweis)}
      <br>Analyse vom ${datumSchoen(a.erstellt)} · Zitate ausschließlich aus der Gesetzesdatenbank.</div>`;
}

function bindeParagraphPillen(wurzel) {
  wurzel.querySelectorAll(".paragraph-pille").forEach(pille => {
    pille.addEventListener("click", async () => {
      const ziel = pille.closest(".thema")?.querySelector(".gesetzestext-ziel");
      if (!ziel) return;
      try {
        const g = await api(`/api/gesetze/${encodeURIComponent(pille.dataset.gesetz)}/${encodeURIComponent(pille.dataset.paragraph)}`);
        ziel.innerHTML = `<div class="gesetzestext">
          <h4>${esc(g.gesetz_kuerzel)} ${esc(g.paragraph)} – ${esc(g.titel)}</h4>
          <p class="fassung">Fassung: ${esc(g.fassung_stand)} ·
            <a href="${esc(g.quelle_url)}" target="_blank" rel="noopener">Quelle: gesetze-im-internet.de</a></p>
          <p>${esc(g.volltext)}</p></div>`;
      } catch (e) { meldung(e.message); }
    });
  });
}

/* ---------- Tab: Schreiben ---------- */

async function tabSchreiben(inhalt, fallId) {
  const [vorlagen, vorhandene] = await Promise.all([
    api("/api/vorlagen"), api(`/api/faelle/${fallId}/schreiben`),
  ]);
  let analyse = null;
  try { analyse = await api(`/api/faelle/${fallId}/analyse`); } catch { /* keine */ }
  const empfohlen = new Set(analyse?.vorlagen_vorschlaege || []);

  inhalt.innerHTML = `
    <p class="beschreibung">Vorlage wählen – Platzhalter werden aus den Falldaten befüllt,
      Prüfregeln (z. B. Schriftform § 623 BGB, 12-Monats-Frist § 556 BGB) laufen automatisch.
      Fertige Schreiben landen verschlüsselt im Ordner <code>vorlagen/</code> des Falls.</p>
    <div class="kartenraster">${vorlagen.map(v => `
      <div class="karte">
        ${empfohlen.has(v.id) ? '<span class="etikett">Für diesen Fall empfohlen</span>' : '<span class="etikett">Vorlage</span>'}
        <h3 style="font-size:18px">${esc(v.titel)}</h3>
        <p class="meta" style="margin:14px 0 0"><button class="knopf klein" data-vorlage="${esc(v.id)}">Ausfüllen</button></p>
      </div>`).join("")}</div>
    <div id="vorlage-formular" style="margin-top:30px"></div>
    ${vorhandene.length ? `<h3 style="font-size:22px;margin:36px 0 14px">Erstellte Schreiben</h3>
      <ul class="zeilenliste">${vorhandene.map(s => `
        <li><span>${esc(s.datei.replace(".txt.enc", ""))}</span>
        <span><button class="knopf klein sekundaer" data-schreiben="${esc(s.datei)}">Anzeigen</button></span></li>`).join("")}
      </ul><div id="schreiben-anzeige"></div>` : ""}`;

  inhalt.querySelectorAll("[data-vorlage]").forEach(k =>
    k.addEventListener("click", () => vorlageFormular(fallId, k.dataset.vorlage, vorlagen, inhalt)));
  inhalt.querySelectorAll("[data-schreiben]").forEach(k =>
    k.addEventListener("click", async () => {
      const antwort = await fetch(`/api/faelle/${fallId}/schreiben/${encodeURIComponent(k.dataset.schreiben)}`);
      const text = await antwort.text();
      document.getElementById("schreiben-anzeige").innerHTML =
        `<div class="brief">${esc(text)}</div>
         <div class="hinweiskasten">${esc(info.beratungshinweis)}</div>`;
    }));
}

const PLATZHALTER_LABELS = {
  ABSENDER_ADRESSE: "Eigene Anschrift", EMPFAENGER_NAME: "Empfänger (Name)",
  EMPFAENGER_ADRESSE: "Empfänger (Anschrift)", ORT: "Ort",
  FRIST_DATUM: "Fristdatum (leer = heute + 14 Tage)", BETRAG: "Betrag in Euro",
  ABRECHNUNGSZEITRAUM: "Abrechnungszeitraum", DATUM_ABRECHNUNG: "Datum der Abrechnung",
  DATUM_ZUGANG: "Zugangsdatum (TT.MM.JJJJ)", BEANSTANDUNGEN: "Beanstandete Positionen",
  WOHNUNG: "Wohnung (Anschrift/Lage)", DATUM_MANGEL: "Mangel besteht seit (Datum)",
  MANGEL_BESCHREIBUNG: "Beschreibung des Mangels", DATUM_FOTOS: "Datum der Fotos",
  DATUM_MINDERUNG_BEGINN: "Minderung ab (Datum)", MINDERUNGSQUOTE: "Minderungsquote in %",
  BEENDIGUNGSDATUM: "Beendigung zum (Datum)", STOERUNG_ART: "Art der Störung",
  STOERUNG_BESCHREIBUNG: "Beschreibung der Störung", DATUM_BEGINN: "Störung seit (Datum)",
  STOERUNGSPROTOKOLL: "Verweis auf Protokoll", AKTENZEICHEN: "Aktenzeichen",
  FRIST_ZWECK: "Zweck der Frist (z. B. Klageerwiderung)", FRIST_ALT: "Bisheriges Fristende",
  FRIST_NEU: "Beantragtes Fristende", VERLAENGERUNGSGRUND: "Begründung",
  UNTERLAGEN_LISTE: "Liste der Unterlagen", UNTERLAGEN_ZEITRAUM: "Zeitraum der Unterlagen",
};

function vorlageFormular(fallId, vorlageId, vorlagen, inhalt) {
  const vorlage = vorlagen.find(v => v.id === vorlageId);
  const felder = vorlage.platzhalter
    .filter(p => !["VORNAME", "NACHNAME", "DATUM_HEUTE"].includes(p))
    .map(p => `<div class="feld"><label for="ph-${p}">${esc(PLATZHALTER_LABELS[p] || p)}</label>
      <input id="ph-${p}" data-platzhalter="${p}"></div>`).join("");
  const ziel = document.getElementById("vorlage-formular");
  ziel.innerHTML = `
    <div class="thema"><h3>${esc(vorlage.titel)}</h3>
      <form id="schreiben-formular" class="formular">${felder}
        <button class="knopf" type="submit">Schreiben erzeugen</button></form>
      <div id="schreiben-ergebnis"></div></div>`;
  ziel.scrollIntoView({ behavior: "smooth", block: "start" });
  document.getElementById("schreiben-formular").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const werte = {};
    ziel.querySelectorAll("[data-platzhalter]").forEach(f => { werte[f.dataset.platzhalter] = f.value; });
    try {
      const s = await api(`/api/faelle/${fallId}/schreiben`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vorlage_id: vorlageId, werte }),
      });
      document.getElementById("schreiben-ergebnis").innerHTML = `
        ${s.warnungen.map(w => `<div class="hinweiskasten">${esc(w)}</div>`).join("")}
        ${s.offene_platzhalter.length ? `<div class="hinweiskasten">Noch offen:
          ${s.offene_platzhalter.map(esc).join(", ")} – im Schreiben als [PLATZHALTER] markiert.</div>` : ""}
        <div class="brief">${esc(s.text)}</div>
        <div class="hinweiskasten">Gespeichert als <code>vorlagen/${esc(s.datei)}</code> (verschlüsselt).
          ${esc(s.beratungshinweis)}</div>`;
      meldung("Schreiben erzeugt und im Fallordner abgelegt.");
    } catch (e) { meldung(e.message); }
  });
}

/* ---------- Gesetzessuche ---------- */

async function ansichtGesetze() {
  app.innerHTML = `
    <section class="abschnitt" style="padding-top:72px">
      <h2>Gesetzesdatenbank</h2>
      <p class="beschreibung">Volltextsuche über alle importierten Paragraphen
        (Quelle: gesetze-im-internet.de, mit Fassungsstand und Update-Diff-Protokoll).</p>
      <div class="feld" style="max-width:560px">
        <input id="suche" placeholder="z. B. Kündigungsfrist, Mietminderung, § 623 …" autofocus>
      </div>
      <div id="treffer"></div>
    </section>`;
  const eingabe = document.getElementById("suche");
  let timer = null;
  eingabe.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(suchen, 250);
  });
  async function suchen() {
    const q = eingabe.value.trim();
    const ziel = document.getElementById("treffer");
    if (!q) { ziel.innerHTML = ""; return; }
    const treffer = await api(`/api/gesetze/suche?q=${encodeURIComponent(q)}`);
    ziel.innerHTML = treffer.length ? treffer.map(g => `
      <div class="gesetzestext">
        <h4>${esc(g.gesetz_kuerzel)} ${esc(g.paragraph)} – ${esc(g.titel)}</h4>
        <p class="fassung">Fassung: ${esc(g.fassung_stand)} ·
          <a href="${esc(g.quelle_url)}" target="_blank" rel="noopener">Quelle</a></p>
        <p>${esc(g.volltext)}</p>
      </div>`).join("")
      : `<div class="leer">Keine Treffer für „${esc(q)}“.</div>`;
  }
}

/* ---------- Start ---------- */

(async function start() {
  try { info = await api("/api/info"); } catch { /* Grundfunktionen bleiben nutzbar */ }
  window.addEventListener("hashchange", navigieren);
  await navigieren();
})();
