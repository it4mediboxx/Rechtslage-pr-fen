# Vorlagen-Bibliothek

Seed-Daten für das Vorlagen-Modul. Einheitlicher Aufbau je Schreiben:
Briefkopf → Empfänger → Betreff → Sachverhalt → Rechtsgrundlage →
Forderung mit konkreter Frist → Konsequenz → Grußformel.

Die *kursiven App-Hinweise* sind Prüfregeln für die Anwendung – sie werden
als Validierungen implementiert und NICHT in das Schreiben übernommen.

---

## vorlage: mietminderung-schimmel
### titel: Mietminderung wegen Schimmelbefalls

[VORNAME] [NACHNAME]
[ABSENDER_ADRESSE]

[EMPFAENGER_NAME]
[EMPFAENGER_ADRESSE]

[ORT], den [DATUM_HEUTE]

**Betreff: Mängelanzeige und Mietminderung – Schimmelbefall in der Wohnung [WOHNUNG]**

Sehr geehrte Damen und Herren,

hiermit zeige ich Ihnen an, dass in der von mir gemieteten Wohnung [WOHNUNG] seit dem [DATUM_MANGEL] ein erheblicher Schimmelbefall besteht ([MANGEL_BESCHREIBUNG]). Der Mangel ist dokumentiert (Fotos vom [DATUM_FOTOS]).

Nach § 536 Abs. 1 BGB ist die Miete für die Dauer der Gebrauchsbeeinträchtigung kraft Gesetzes gemindert. Ich mindere die Miete daher ab dem [DATUM_MINDERUNG_BEGINN] um [MINDERUNGSQUOTE] %. Zugleich fordere ich Sie auf, den Mangel gemäß Ihrer Erhaltungspflicht aus § 535 Abs. 1 BGB zu beseitigen.

Ich setze Ihnen hierfür eine Frist bis zum **[FRIST_DATUM]**.

Sollte der Mangel bis dahin nicht beseitigt sein, behalte ich mir vor, den Mangel auf Ihre Kosten selbst beseitigen zu lassen (§ 536a Abs. 2 BGB) sowie weitere Rechte geltend zu machen.

Mit freundlichen Grüßen

[VORNAME] [NACHNAME]

*App-Hinweis: Vor Versand prüfen, dass die Mängelanzeige unverzüglich erfolgt (§ 536c BGB) – Datum der ersten Anzeige abfragen. Minderungsquote plausibilisieren (Warnung ab > 50 %).*

---

## vorlage: nebenkosten-widerspruch
### titel: Widerspruch gegen die Nebenkostenabrechnung

[VORNAME] [NACHNAME]
[ABSENDER_ADRESSE]

[EMPFAENGER_NAME]
[EMPFAENGER_ADRESSE]

[ORT], den [DATUM_HEUTE]

**Betreff: Einwendungen gegen die Betriebskostenabrechnung vom [DATUM_ABRECHNUNG] – Abrechnungszeitraum [ABRECHNUNGSZEITRAUM]**

Sehr geehrte Damen und Herren,

gegen Ihre oben genannte Betriebskostenabrechnung, mir zugegangen am [DATUM_ZUGANG], erhebe ich fristgerecht Einwendungen gemäß § 556 Abs. 3 BGB.

Im Einzelnen beanstande ich: [BEANSTANDUNGEN]

Nach §§ 1, 2 BetrKV sind nur die dort aufgeführten laufenden Betriebskosten umlagefähig; Verwaltungs- und Instandhaltungskosten gehören nicht dazu (§ 1 Abs. 2 BetrKV). Ich fordere Sie auf, mir bis zum **[FRIST_DATUM]** Belegeinsicht zu gewähren und eine korrigierte Abrechnung zu erteilen.

Bis zur Klärung leiste ich etwaige Nachzahlungen nur unter Vorbehalt. Nach fruchtlosem Fristablauf werde ich die Nachforderung insgesamt zurückweisen.

Mit freundlichen Grüßen

[VORNAME] [NACHNAME]

*App-Hinweis: 12-Monats-Frist des § 556 Abs. 3 BGB prüfen – Einwendungen müssen innerhalb von 12 Monaten nach Zugang der Abrechnung erhoben werden; bei Überschreitung warnen. Ebenso prüfen, ob die Abrechnung selbst später als 12 Monate nach Ende des Abrechnungszeitraums zuging (dann Nachforderung ausgeschlossen).*

---

## vorlage: lohnzahlungsaufforderung
### titel: Aufforderung zur Lohnzahlung

[VORNAME] [NACHNAME]
[ABSENDER_ADRESSE]

[EMPFAENGER_NAME]
[EMPFAENGER_ADRESSE]

[ORT], den [DATUM_HEUTE]

**Betreff: Ausstehende Vergütung für [ABRECHNUNGSZEITRAUM] – Zahlungsaufforderung**

Sehr geehrte Damen und Herren,

für den Zeitraum [ABRECHNUNGSZEITRAUM] steht meine Vergütung in Höhe von **[BETRAG] €** aus. Die Arbeitsleistung wurde vollständig erbracht; die Vergütung ist gemäß § 614 BGB fällig.

Ich fordere Sie auf, den ausstehenden Betrag bis spätestens **[FRIST_DATUM]** auf mein Ihnen bekanntes Konto zu zahlen. Sie befinden sich mit Ablauf der Frist in Verzug (§ 286 BGB); Verzugszinsen nach § 288 BGB behalte ich mir vor.

Sollte die Zahlung nicht fristgerecht eingehen, werde ich meine Ansprüche ohne weitere Ankündigung gerichtlich geltend machen.

Mit freundlichen Grüßen

[VORNAME] [NACHNAME]

*App-Hinweis: Auf arbeits- oder tarifvertragliche Ausschlussfristen hinweisen – Anspruch kann bereits nach wenigen Monaten verfallen; Vertragsdatum und einschlägigen Tarifvertrag abfragen.*

---

## vorlage: eigenkuendigung
### titel: Eigenkündigung des Arbeitsverhältnisses

[VORNAME] [NACHNAME]
[ABSENDER_ADRESSE]

[EMPFAENGER_NAME]
[EMPFAENGER_ADRESSE]

[ORT], den [DATUM_HEUTE]

**Betreff: Kündigung meines Arbeitsverhältnisses**

Sehr geehrte Damen und Herren,

hiermit kündige ich das zwischen uns bestehende Arbeitsverhältnis ordentlich und fristgerecht zum **[BEENDIGUNGSDATUM]**, hilfsweise zum nächstmöglichen Zeitpunkt (§ 622 Abs. 1 BGB).

Bitte bestätigen Sie mir den Erhalt dieser Kündigung sowie das Beendigungsdatum schriftlich. Zugleich bitte ich um Erteilung eines qualifizierten Arbeitszeugnisses (§ 109 GewO) und um Abrechnung sowie Abgeltung etwaiger offener Urlaubstage (§ 7 Abs. 4 BUrlG) bis zum **[FRIST_DATUM]**.

Mit freundlichen Grüßen

[VORNAME] [NACHNAME]
(eigenhändige Unterschrift)

*App-Hinweis: Schriftformerfordernis § 623 BGB – die Kündigung ist nur mit eigenhändiger Unterschrift auf Papier wirksam; Versand per E-Mail/Scan blockieren bzw. deutlich warnen.*

---

## vorlage: nachbarschaftsbeschwerde
### titel: Beschwerde wegen Ruhestörung / Beeinträchtigung

[VORNAME] [NACHNAME]
[ABSENDER_ADRESSE]

[EMPFAENGER_NAME]
[EMPFAENGER_ADRESSE]

[ORT], den [DATUM_HEUTE]

**Betreff: Aufforderung zur Unterlassung – [STOERUNG_ART]**

Sehr geehrte(r) [EMPFAENGER_NAME],

seit dem [DATUM_BEGINN] kommt es wiederholt zu erheblichen Beeinträchtigungen durch [STOERUNG_BESCHREIBUNG]. Die Vorfälle sind protokolliert ([STOERUNGSPROTOKOLL]).

Als betroffener Eigentümer/Besitzer steht mir ein Unterlassungsanspruch aus § 1004 Abs. 1 BGB zu; die Einwirkungen überschreiten das nach § 906 BGB hinzunehmende Maß.

Ich fordere Sie auf, die Störungen ab sofort zu unterlassen und mir dies bis zum **[FRIST_DATUM]** schriftlich zuzusichern.

Andernfalls werde ich ohne weitere Ankündigung rechtliche Schritte einleiten.

Mit freundlichen Grüßen

[VORNAME] [NACHNAME]

*App-Hinweis: Störungsprotokoll (Datum, Uhrzeit, Art, Zeugen) als Anlage empfehlen; ohne Protokoll auf Beweislücke hinweisen.*

---

## vorlage: werbewiderspruch-dsgvo
### titel: Widerspruch gegen Werbung (Art. 21 DSGVO)

[VORNAME] [NACHNAME]
[ABSENDER_ADRESSE]

[EMPFAENGER_NAME]
[EMPFAENGER_ADRESSE]

[ORT], den [DATUM_HEUTE]

**Betreff: Widerspruch gegen die Verarbeitung meiner Daten zu Werbezwecken (Art. 21 Abs. 2 DSGVO)**

Sehr geehrte Damen und Herren,

hiermit widerspreche ich der Verarbeitung meiner personenbezogenen Daten zum Zwecke der Direktwerbung gemäß Art. 21 Abs. 2 DSGVO. Der Widerspruch gilt für alle Werbekanäle (Post, E-Mail, Telefon).

Nach Art. 21 Abs. 3 DSGVO dürfen meine Daten ab Zugang dieses Widerspruchs nicht mehr für Werbezwecke verarbeitet werden. Ich fordere Sie auf, mir die Umsetzung bis zum **[FRIST_DATUM]** schriftlich zu bestätigen.

Sollte ich weiterhin Werbung erhalten, werde ich mich an die zuständige Datenschutzaufsichtsbehörde wenden und Schadensersatzansprüche prüfen lassen.

Mit freundlichen Grüßen

[VORNAME] [NACHNAME]

*App-Hinweis: Widerspruch nach Art. 21 Abs. 2 DSGVO ist an keine Begründung und keine Frist gebunden – keine Fristprüfung nötig, aber Zugangsnachweis (Einschreiben) empfehlen.*

---

## vorlage: fristverlaengerung-gericht
### titel: Antrag auf Fristverlängerung bei Gericht

[VORNAME] [NACHNAME]
[ABSENDER_ADRESSE]

An das
[EMPFAENGER_NAME]
[EMPFAENGER_ADRESSE]

[ORT], den [DATUM_HEUTE]

**Betreff: Az. [AKTENZEICHEN] – Antrag auf Verlängerung der Frist zur [FRIST_ZWECK]**

Sehr geehrte Damen und Herren,

in dem oben bezeichneten Verfahren wurde mir eine Frist zur [FRIST_ZWECK] bis zum [FRIST_ALT] gesetzt.

Ich beantrage, diese Frist gemäß § 224 Abs. 2 ZPO bis zum **[FRIST_NEU]** zu verlängern.

Zur Begründung: [VERLAENGERUNGSGRUND]. Die erheblichen Gründe werde ich auf Verlangen glaubhaft machen.

Mit freundlichen Grüßen

[VORNAME] [NACHNAME]

*App-Hinweis: Vor Erstellung prüfen und deutlich warnen: Notfristen (§ 224 Abs. 1 ZPO) sind NICHT verlängerbar (z. B. Klagefrist § 4 KSchG). Der Antrag muss vor Fristablauf bei Gericht eingehen.*

---

## vorlage: steuerunterlagen-anforderung
### titel: Anforderung von Steuerunterlagen

[VORNAME] [NACHNAME]
[ABSENDER_ADRESSE]

[EMPFAENGER_NAME]
[EMPFAENGER_ADRESSE]

[ORT], den [DATUM_HEUTE]

**Betreff: Herausgabe meiner Unterlagen – [UNTERLAGEN_ZEITRAUM]**

Sehr geehrte Damen und Herren,

ich fordere Sie auf, mir die folgenden mir gehörenden Unterlagen vollständig herauszugeben: [UNTERLAGEN_LISTE] (Zeitraum: [UNTERLAGEN_ZEITRAUM]).

Als Eigentümer der Unterlagen habe ich einen Herausgabeanspruch (§ 985 BGB); zudem benötige ich die Unterlagen zur Erfüllung meiner gesetzlichen Aufbewahrungspflichten (§ 147 AO).

Bitte stellen Sie mir die Unterlagen bis zum **[FRIST_DATUM]** zur Abholung bereit oder übersenden Sie sie an die oben genannte Anschrift.

Nach fruchtlosem Fristablauf werde ich den Herausgabeanspruch gerichtlich durchsetzen und Sie mit den Kosten belasten.

Mit freundlichen Grüßen

[VORNAME] [NACHNAME]

*App-Hinweis: Bei Steuerberater-Konstellation auf mögliches Zurückbehaltungsrecht bei offenen Honoraren hinweisen; Aufbewahrungsfristen (§ 147 AO: 6/8/10 Jahre) im Ergebnis anzeigen.*
