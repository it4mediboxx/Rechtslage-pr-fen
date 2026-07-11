"""Seed-Daten der Gesetzesdatenbank.

Quelle der Normtexte: gesetze-im-internet.de (amtliche Lesefassungen).
Lange Vorschriften sind als gekennzeichnete Auszüge hinterlegt ("(Auszug)").
`fassung_stand` bezeichnet den Stand des Seed-Imports; der Importer
(app.importer) aktualisiert Einträge gegen die Online-Fassung und
protokolliert jede Änderung als Diff.
"""

SEED_STAND = "Seed-Import 11.07.2026"

_GII = "https://www.gesetze-im-internet.de"


def _e(kuerzel: str, paragraph: str, titel: str, volltext: str, url: str) -> dict:
    return {
        "gesetz_kuerzel": kuerzel,
        "paragraph": paragraph,
        "titel": titel,
        "volltext": volltext.strip(),
        "fassung_stand": SEED_STAND,
        "quelle_url": url,
    }


GESETZE_SEED: list[dict] = [
    # ------------------------------------------------------------------
    # Arbeitsrecht
    # ------------------------------------------------------------------
    _e("BGB", "§ 611", "Vertragstypische Pflichten beim Dienstvertrag",
       "(1) Durch den Dienstvertrag wird derjenige, welcher Dienste zusagt, zur Leistung der "
       "versprochenen Dienste, der andere Teil zur Gewährung der vereinbarten Vergütung verpflichtet. "
       "(2) Gegenstand des Dienstvertrags können Dienste jeder Art sein.",
       f"{_GII}/bgb/__611.html"),
    _e("BGB", "§ 611a", "Arbeitsvertrag",
       "(1) Durch den Arbeitsvertrag wird der Arbeitnehmer im Dienste eines anderen zur Leistung "
       "weisungsgebundener, fremdbestimmter Arbeit in persönlicher Abhängigkeit verpflichtet. Das "
       "Weisungsrecht kann Inhalt, Durchführung, Zeit und Ort der Tätigkeit betreffen. (…) "
       "(2) Der Arbeitgeber ist zur Zahlung der vereinbarten Vergütung verpflichtet. (Auszug)",
       f"{_GII}/bgb/__611a.html"),
    _e("BGB", "§ 614", "Fälligkeit der Vergütung",
       "Die Vergütung ist nach der Leistung der Dienste zu entrichten. Ist die Vergütung nach "
       "Zeitabschnitten bemessen, so ist sie nach dem Ablaufe der einzelnen Zeitabschnitte zu entrichten.",
       f"{_GII}/bgb/__614.html"),
    _e("BGB", "§ 622", "Kündigungsfristen bei Arbeitsverhältnissen",
       "(1) Das Arbeitsverhältnis eines Arbeiters oder eines Angestellten (Arbeitnehmers) kann mit "
       "einer Frist von vier Wochen zum Fünfzehnten oder zum Ende eines Kalendermonats gekündigt werden. "
       "(2) Für eine Kündigung durch den Arbeitgeber beträgt die Kündigungsfrist, wenn das "
       "Arbeitsverhältnis in dem Betrieb oder Unternehmen 1. zwei Jahre bestanden hat, einen Monat zum "
       "Ende eines Kalendermonats; 2. fünf Jahre bestanden hat, zwei Monate zum Ende eines "
       "Kalendermonats; 3. acht Jahre bestanden hat, drei Monate zum Ende eines Kalendermonats; "
       "4. zehn Jahre bestanden hat, vier Monate zum Ende eines Kalendermonats; 5. zwölf Jahre bestanden "
       "hat, fünf Monate zum Ende eines Kalendermonats; 6. 15 Jahre bestanden hat, sechs Monate zum Ende "
       "eines Kalendermonats; 7. 20 Jahre bestanden hat, sieben Monate zum Ende eines Kalendermonats. "
       "(3) Während einer vereinbarten Probezeit, längstens für die Dauer von sechs Monaten, kann das "
       "Arbeitsverhältnis mit einer Frist von zwei Wochen gekündigt werden. (Auszug)",
       f"{_GII}/bgb/__622.html"),
    _e("BGB", "§ 623", "Schriftform der Kündigung",
       "Die Beendigung von Arbeitsverhältnissen durch Kündigung oder Auflösungsvertrag bedürfen zu "
       "ihrer Wirksamkeit der Schriftform; die elektronische Form ist ausgeschlossen.",
       f"{_GII}/bgb/__623.html"),
    _e("BGB", "§ 626", "Fristlose Kündigung aus wichtigem Grund",
       "(1) Das Dienstverhältnis kann von jedem Vertragsteil aus wichtigem Grund ohne Einhaltung einer "
       "Kündigungsfrist gekündigt werden, wenn Tatsachen vorliegen, auf Grund derer dem Kündigenden "
       "unter Berücksichtigung aller Umstände des Einzelfalles und unter Abwägung der Interessen beider "
       "Vertragsteile die Fortsetzung des Dienstverhältnisses bis zum Ablauf der Kündigungsfrist oder "
       "bis zu der vereinbarten Beendigung des Dienstverhältnisses nicht zugemutet werden kann. "
       "(2) Die Kündigung kann nur innerhalb von zwei Wochen erfolgen. Die Frist beginnt mit dem "
       "Zeitpunkt, in dem der Kündigungsberechtigte von den für die Kündigung maßgebenden Tatsachen "
       "Kenntnis erlangt. (Auszug)",
       f"{_GII}/bgb/__626.html"),
    _e("KSchG", "§ 1", "Sozial ungerechtfertigte Kündigungen",
       "(1) Die Kündigung des Arbeitsverhältnisses gegenüber einem Arbeitnehmer, dessen "
       "Arbeitsverhältnis in demselben Betrieb oder Unternehmen ohne Unterbrechung länger als sechs "
       "Monate bestanden hat, ist rechtsunwirksam, wenn sie sozial ungerechtfertigt ist. (2) Sozial "
       "ungerechtfertigt ist die Kündigung, wenn sie nicht durch Gründe, die in der Person oder in dem "
       "Verhalten des Arbeitnehmers liegen, oder durch dringende betriebliche Erfordernisse, die einer "
       "Weiterbeschäftigung des Arbeitnehmers in diesem Betrieb entgegenstehen, bedingt ist. (Auszug)",
       f"{_GII}/kschg/__1.html"),
    _e("KSchG", "§ 4", "Anrufung des Arbeitsgerichts",
       "Will ein Arbeitnehmer geltend machen, dass eine Kündigung sozial ungerechtfertigt oder aus "
       "anderen Gründen rechtsunwirksam ist, so muss er innerhalb von drei Wochen nach Zugang der "
       "schriftlichen Kündigung Klage beim Arbeitsgericht auf Feststellung erheben, dass das "
       "Arbeitsverhältnis durch die Kündigung nicht aufgelöst ist. (Auszug)",
       f"{_GII}/kschg/__4.html"),
    _e("KSchG", "§ 7", "Wirksamwerden der Kündigung",
       "Wird die Rechtsunwirksamkeit einer Kündigung nicht rechtzeitig geltend gemacht (§ 4 Satz 1, "
       "§§ 5 und 6), so gilt die Kündigung als von Anfang an rechtswirksam. (Auszug)",
       f"{_GII}/kschg/__7.html"),
    _e("KSchG", "§ 13", "Außerordentliche, sittenwidrige und sonstige Kündigungen",
       "(1) Die Vorschriften über das Recht zur außerordentlichen Kündigung eines Arbeitsverhältnisses "
       "werden durch das vorliegende Gesetz nicht berührt. Die Rechtsunwirksamkeit einer "
       "außerordentlichen Kündigung kann jedoch nur nach Maßgabe des § 4 Satz 1 und der §§ 5 bis 7 "
       "geltend gemacht werden. (Auszug)",
       f"{_GII}/kschg/__13.html"),
    _e("KSchG", "§ 23", "Geltungsbereich",
       "(1) Die Vorschriften des Ersten und Zweiten Abschnitts gelten für Betriebe und Verwaltungen "
       "des privaten und des öffentlichen Rechts (…). Die Vorschriften des Ersten Abschnitts gelten "
       "(…) nicht für Betriebe und Verwaltungen, in denen in der Regel zehn oder weniger Arbeitnehmer "
       "ausschließlich der zu ihrer Berufsbildung Beschäftigten beschäftigt werden. (Auszug – "
       "Kleinbetriebsklausel)",
       f"{_GII}/kschg/__23.html"),
    _e("ArbZG", "§ 3", "Arbeitszeit der Arbeitnehmer",
       "Die werktägliche Arbeitszeit der Arbeitnehmer darf acht Stunden nicht überschreiten. Sie kann "
       "auf bis zu zehn Stunden nur verlängert werden, wenn innerhalb von sechs Kalendermonaten oder "
       "innerhalb von 24 Wochen im Durchschnitt acht Stunden werktäglich nicht überschritten werden.",
       f"{_GII}/arbzg/__3.html"),
    _e("BUrlG", "§ 1", "Urlaubsanspruch",
       "Jeder Arbeitnehmer hat in jedem Kalenderjahr Anspruch auf bezahlten Erholungsurlaub.",
       f"{_GII}/burlg/__1.html"),
    _e("BUrlG", "§ 3", "Dauer des Urlaubs",
       "(1) Der Urlaub beträgt jährlich mindestens 24 Werktage. (2) Als Werktage gelten alle "
       "Kalendertage, die nicht Sonn- oder gesetzliche Feiertage sind.",
       f"{_GII}/burlg/__3.html"),
    _e("BUrlG", "§ 7", "Zeitpunkt, Übertragbarkeit und Abgeltung des Urlaubs",
       "(4) Kann der Urlaub wegen Beendigung des Arbeitsverhältnisses ganz oder teilweise nicht mehr "
       "gewährt werden, so ist er abzugelten. (Auszug)",
       f"{_GII}/burlg/__7.html"),
    _e("EFZG", "§ 3", "Anspruch auf Entgeltfortzahlung im Krankheitsfall",
       "(1) Wird ein Arbeitnehmer durch Arbeitsunfähigkeit infolge Krankheit an seiner Arbeitsleistung "
       "verhindert, ohne dass ihn ein Verschulden trifft, so hat er Anspruch auf Entgeltfortzahlung im "
       "Krankheitsfall durch den Arbeitgeber für die Zeit der Arbeitsunfähigkeit bis zur Dauer von "
       "sechs Wochen. (Auszug)",
       f"{_GII}/entgfg/__3.html"),
    _e("GewO", "§ 109", "Zeugnis",
       "(1) Der Arbeitnehmer hat bei Beendigung eines Arbeitsverhältnisses Anspruch auf ein "
       "schriftliches Zeugnis. Das Zeugnis muss mindestens Angaben zu Art und Dauer der Tätigkeit "
       "(einfaches Zeugnis) enthalten. Der Arbeitnehmer kann verlangen, dass sich die Angaben darüber "
       "hinaus auf Leistung und Verhalten im Arbeitsverhältnis (qualifiziertes Zeugnis) erstrecken. "
       "(2) Das Zeugnis muss klar und verständlich formuliert sein. (Auszug)",
       f"{_GII}/gewo/__109.html"),

    # ------------------------------------------------------------------
    # Privatrecht (BGB AT, Schuldrecht, Sachenrecht, DSGVO)
    # ------------------------------------------------------------------
    _e("BGB", "§ 119", "Anfechtbarkeit wegen Irrtums",
       "(1) Wer bei der Abgabe einer Willenserklärung über deren Inhalt im Irrtum war oder eine "
       "Erklärung dieses Inhalts überhaupt nicht abgeben wollte, kann die Erklärung anfechten, wenn "
       "anzunehmen ist, dass er sie bei Kenntnis der Sachlage und bei verständiger Würdigung des "
       "Falles nicht abgegeben haben würde. (Auszug)",
       f"{_GII}/bgb/__119.html"),
    _e("BGB", "§ 123", "Anfechtbarkeit wegen Täuschung oder Drohung",
       "(1) Wer zur Abgabe einer Willenserklärung durch arglistige Täuschung oder widerrechtlich durch "
       "Drohung bestimmt worden ist, kann die Erklärung anfechten. (Auszug)",
       f"{_GII}/bgb/__123.html"),
    _e("BGB", "§ 133", "Auslegung einer Willenserklärung",
       "Bei der Auslegung einer Willenserklärung ist der wirkliche Wille zu erforschen und nicht an "
       "dem buchstäblichen Sinne des Ausdrucks zu haften.",
       f"{_GII}/bgb/__133.html"),
    _e("BGB", "§ 145", "Bindung an den Antrag",
       "Wer einem anderen die Schließung eines Vertrags anträgt, ist an den Antrag gebunden, es sei "
       "denn, dass er die Gebundenheit ausgeschlossen hat.",
       f"{_GII}/bgb/__145.html"),
    _e("BGB", "§ 157", "Auslegung von Verträgen",
       "Verträge sind so auszulegen, wie Treu und Glauben mit Rücksicht auf die Verkehrssitte es "
       "erfordern.",
       f"{_GII}/bgb/__157.html"),
    _e("BGB", "§ 242", "Leistung nach Treu und Glauben",
       "Der Schuldner ist verpflichtet, die Leistung so zu bewirken, wie Treu und Glauben mit "
       "Rücksicht auf die Verkehrssitte es erfordern.",
       f"{_GII}/bgb/__242.html"),
    _e("BGB", "§ 280", "Schadensersatz wegen Pflichtverletzung",
       "(1) Verletzt der Schuldner eine Pflicht aus dem Schuldverhältnis, so kann der Gläubiger Ersatz "
       "des hierdurch entstehenden Schadens verlangen. Dies gilt nicht, wenn der Schuldner die "
       "Pflichtverletzung nicht zu vertreten hat. (Auszug)",
       f"{_GII}/bgb/__280.html"),
    _e("BGB", "§ 286", "Verzug des Schuldners",
       "(1) Leistet der Schuldner auf eine Mahnung des Gläubigers nicht, die nach dem Eintritt der "
       "Fälligkeit erfolgt, so kommt er durch die Mahnung in Verzug. (…) (2) Der Mahnung bedarf es "
       "nicht, wenn 1. für die Leistung eine Zeit nach dem Kalender bestimmt ist (…). (3) Der Schuldner "
       "einer Entgeltforderung kommt spätestens in Verzug, wenn er nicht innerhalb von 30 Tagen nach "
       "Fälligkeit und Zugang einer Rechnung oder gleichwertigen Zahlungsaufstellung leistet. (Auszug)",
       f"{_GII}/bgb/__286.html"),
    _e("BGB", "§ 288", "Verzugszinsen und sonstiger Verzugsschaden",
       "(1) Eine Geldschuld ist während des Verzugs zu verzinsen. Der Verzugszinssatz beträgt für das "
       "Jahr fünf Prozentpunkte über dem Basiszinssatz. (Auszug)",
       f"{_GII}/bgb/__288.html"),
    _e("BGB", "§ 323", "Rücktritt wegen nicht oder nicht vertragsgemäß erbrachter Leistung",
       "(1) Erbringt der Schuldner bei einem gegenseitigen Vertrag eine fällige Leistung nicht oder "
       "nicht vertragsgemäß, so kann der Gläubiger, wenn er dem Schuldner erfolglos eine angemessene "
       "Frist zur Leistung oder Nacherfüllung bestimmt hat, vom Vertrag zurücktreten. (Auszug)",
       f"{_GII}/bgb/__323.html"),
    _e("BGB", "§ 433", "Vertragstypische Pflichten beim Kaufvertrag",
       "(1) Durch den Kaufvertrag wird der Verkäufer einer Sache verpflichtet, dem Käufer die Sache zu "
       "übergeben und das Eigentum an der Sache zu verschaffen. Der Verkäufer hat dem Käufer die Sache "
       "frei von Sach- und Rechtsmängeln zu verschaffen. (2) Der Käufer ist verpflichtet, dem Verkäufer "
       "den vereinbarten Kaufpreis zu zahlen und die gekaufte Sache abzunehmen.",
       f"{_GII}/bgb/__433.html"),
    _e("BGB", "§ 434", "Sachmangel",
       "(1) Die Sache ist frei von Sachmängeln, wenn sie bei Gefahrübergang den subjektiven "
       "Anforderungen, den objektiven Anforderungen und den Montageanforderungen dieser Vorschrift "
       "entspricht. (Auszug)",
       f"{_GII}/bgb/__434.html"),
    _e("BGB", "§ 437", "Rechte des Käufers bei Mängeln",
       "Ist die Sache mangelhaft, kann der Käufer, wenn die Voraussetzungen der folgenden Vorschriften "
       "vorliegen und soweit nicht ein anderes bestimmt ist, 1. nach § 439 Nacherfüllung verlangen, "
       "2. nach den §§ 440, 323 und 326 Abs. 5 von dem Vertrag zurücktreten oder nach § 441 den "
       "Kaufpreis mindern und 3. nach den §§ 440, 280, 281, 283 und 311a Schadensersatz oder nach "
       "§ 284 Ersatz vergeblicher Aufwendungen verlangen.",
       f"{_GII}/bgb/__437.html"),
    _e("BGB", "§ 439", "Nacherfüllung",
       "(1) Der Käufer kann als Nacherfüllung nach seiner Wahl die Beseitigung des Mangels oder die "
       "Lieferung einer mangelfreien Sache verlangen. (Auszug)",
       f"{_GII}/bgb/__439.html"),
    _e("BGB", "§ 823", "Schadensersatzpflicht",
       "(1) Wer vorsätzlich oder fahrlässig das Leben, den Körper, die Gesundheit, die Freiheit, das "
       "Eigentum oder ein sonstiges Recht eines anderen widerrechtlich verletzt, ist dem anderen zum "
       "Ersatz des daraus entstehenden Schadens verpflichtet. (Auszug)",
       f"{_GII}/bgb/__823.html"),
    _e("BGB", "§ 985", "Herausgabeanspruch",
       "Der Eigentümer kann von dem Besitzer die Herausgabe der Sache verlangen.",
       f"{_GII}/bgb/__985.html"),
    _e("BGB", "§ 1004", "Beseitigungs- und Unterlassungsanspruch",
       "(1) Wird das Eigentum in anderer Weise als durch Entziehung oder Vorenthaltung des Besitzes "
       "beeinträchtigt, so kann der Eigentümer von dem Störer die Beseitigung der Beeinträchtigung "
       "verlangen. Sind weitere Beeinträchtigungen zu besorgen, so kann der Eigentümer auf Unterlassung "
       "klagen. (Auszug)",
       f"{_GII}/bgb/__1004.html"),
    _e("BGB", "§ 906", "Zuführung unwägbarer Stoffe",
       "(1) Der Eigentümer eines Grundstücks kann die Zuführung von Gasen, Dämpfen, Gerüchen, Rauch, "
       "Ruß, Wärme, Geräusch, Erschütterungen und ähnliche von einem anderen Grundstück ausgehende "
       "Einwirkungen insoweit nicht verbieten, als die Einwirkung die Benutzung seines Grundstücks "
       "nicht oder nur unwesentlich beeinträchtigt. (Auszug)",
       f"{_GII}/bgb/__906.html"),
    _e("DSGVO", "Art. 21", "Widerspruchsrecht",
       "(1) Die betroffene Person hat das Recht, aus Gründen, die sich aus ihrer besonderen Situation "
       "ergeben, jederzeit gegen die Verarbeitung sie betreffender personenbezogener Daten (…) "
       "Widerspruch einzulegen. (2) Werden personenbezogene Daten verarbeitet, um Direktwerbung zu "
       "betreiben, so hat die betroffene Person das Recht, jederzeit Widerspruch gegen die Verarbeitung "
       "sie betreffender personenbezogener Daten zum Zwecke derartiger Werbung einzulegen. (3) "
       "Widerspricht die betroffene Person der Verarbeitung für Zwecke der Direktwerbung, so werden die "
       "personenbezogenen Daten nicht mehr für diese Zwecke verarbeitet. (Auszug)",
       "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679"),

    # ------------------------------------------------------------------
    # Wohnrecht
    # ------------------------------------------------------------------
    _e("BGB", "§ 535", "Inhalt und Hauptpflichten des Mietvertrags",
       "(1) Durch den Mietvertrag wird der Vermieter verpflichtet, dem Mieter den Gebrauch der "
       "Mietsache während der Mietzeit zu gewähren. Der Vermieter hat die Mietsache dem Mieter in einem "
       "zum vertragsgemäßen Gebrauch geeigneten Zustand zu überlassen und sie während der Mietzeit in "
       "diesem Zustand zu erhalten. (2) Der Mieter ist verpflichtet, dem Vermieter die vereinbarte "
       "Miete zu entrichten.",
       f"{_GII}/bgb/__535.html"),
    _e("BGB", "§ 536", "Mietminderung bei Sach- und Rechtsmängeln",
       "(1) Hat die Mietsache zur Zeit der Überlassung an den Mieter einen Mangel, der ihre Tauglichkeit "
       "zum vertragsgemäßen Gebrauch aufhebt, oder entsteht während der Mietzeit ein solcher Mangel, so "
       "ist der Mieter für die Zeit, in der die Tauglichkeit aufgehoben ist, von der Entrichtung der "
       "Miete befreit. Für die Zeit, während der die Tauglichkeit gemindert ist, hat er nur eine "
       "angemessen herabgesetzte Miete zu entrichten. Eine unerhebliche Minderung der Tauglichkeit "
       "bleibt außer Betracht. (Auszug)",
       f"{_GII}/bgb/__536.html"),
    _e("BGB", "§ 536a", "Schadens- und Aufwendungsersatzanspruch des Mieters wegen eines Mangels",
       "(1) Ist ein Mangel im Sinne des § 536 bei Vertragsschluss vorhanden oder entsteht ein solcher "
       "Mangel später wegen eines Umstands, den der Vermieter zu vertreten hat, oder kommt der "
       "Vermieter mit der Beseitigung eines Mangels in Verzug, so kann der Mieter unbeschadet der "
       "Rechte aus § 536 Schadensersatz verlangen. (2) Der Mieter kann den Mangel selbst beseitigen und "
       "Ersatz der erforderlichen Aufwendungen verlangen, wenn 1. der Vermieter mit der Beseitigung des "
       "Mangels in Verzug ist (…). (Auszug)",
       f"{_GII}/bgb/__536a.html"),
    _e("BGB", "§ 536c", "Während der Mietzeit auftretende Mängel; Mängelanzeige durch den Mieter",
       "(1) Zeigt sich im Laufe der Mietzeit ein Mangel der Mietsache (…), so hat der Mieter dies dem "
       "Vermieter unverzüglich anzuzeigen. (2) Unterlässt der Mieter die Anzeige, so ist er dem "
       "Vermieter zum Ersatz des daraus entstehenden Schadens verpflichtet; soweit der Vermieter "
       "infolge der Unterlassung der Anzeige Abhilfe nicht schaffen konnte, ist der Mieter nicht "
       "berechtigt, die in § 536 bestimmten Rechte geltend zu machen. (Auszug)",
       f"{_GII}/bgb/__536c.html"),
    _e("BGB", "§ 543", "Außerordentliche fristlose Kündigung aus wichtigem Grund",
       "(1) Jede Vertragspartei kann das Mietverhältnis aus wichtigem Grund außerordentlich fristlos "
       "kündigen. (2) Ein wichtiger Grund liegt insbesondere vor, wenn (…) 3. der Mieter a) für zwei "
       "aufeinander folgende Termine mit der Entrichtung der Miete oder eines nicht unerheblichen Teils "
       "der Miete in Verzug ist (…). (Auszug)",
       f"{_GII}/bgb/__543.html"),
    _e("BGB", "§ 551", "Begrenzung und Anlage von Mietsicherheiten",
       "(1) Hat der Mieter dem Vermieter für die Erfüllung seiner Pflichten Sicherheit zu leisten, so "
       "darf diese (…) höchstens das Dreifache der auf einen Monat entfallenden Miete ohne die als "
       "Pauschale oder als Vorauszahlung ausgewiesenen Betriebskosten betragen. (Auszug)",
       f"{_GII}/bgb/__551.html"),
    _e("BGB", "§ 556", "Vereinbarungen über Betriebskosten",
       "(1) Die Vertragsparteien können vereinbaren, dass der Mieter Betriebskosten trägt. (…) "
       "(3) Über die Vorauszahlungen für Betriebskosten ist jährlich abzurechnen (…). Die Abrechnung "
       "ist dem Mieter spätestens bis zum Ablauf des zwölften Monats nach Ende des "
       "Abrechnungszeitraums mitzuteilen. Nach Ablauf dieser Frist ist die Geltendmachung einer "
       "Nachforderung durch den Vermieter ausgeschlossen, es sei denn, der Vermieter hat die verspätete "
       "Geltendmachung nicht zu vertreten. Einwendungen gegen die Abrechnung hat der Mieter dem "
       "Vermieter spätestens bis zum Ablauf des zwölften Monats nach Zugang der Abrechnung mitzuteilen. "
       "(Auszug)",
       f"{_GII}/bgb/__556.html"),
    _e("BGB", "§ 569", "Außerordentliche fristlose Kündigung aus wichtigem Grund (Wohnraum)",
       "(1) Ein wichtiger Grund im Sinne des § 543 Abs. 1 liegt für den Mieter auch vor, wenn der "
       "gemietete Wohnraum so beschaffen ist, dass seine Benutzung mit einer erheblichen Gefährdung "
       "der Gesundheit verbunden ist. (Auszug)",
       f"{_GII}/bgb/__569.html"),
    _e("BGB", "§ 573", "Ordentliche Kündigung des Vermieters",
       "(1) Der Vermieter kann nur kündigen, wenn er ein berechtigtes Interesse an der Beendigung des "
       "Mietverhältnisses hat. (…) (2) Ein berechtigtes Interesse des Vermieters (…) liegt insbesondere "
       "vor, wenn 1. der Mieter seine vertraglichen Pflichten schuldhaft nicht unerheblich verletzt "
       "hat, 2. der Vermieter die Räume als Wohnung für sich, seine Familienangehörigen oder Angehörige "
       "seines Haushalts benötigt (Eigenbedarf) (…). (Auszug)",
       f"{_GII}/bgb/__573.html"),
    _e("BGB", "§ 573c", "Fristen der ordentlichen Kündigung",
       "(1) Die Kündigung ist spätestens am dritten Werktag eines Kalendermonats zum Ablauf des "
       "übernächsten Monats zulässig. Die Kündigungsfrist für den Vermieter verlängert sich nach fünf "
       "und acht Jahren seit der Überlassung des Wohnraums um jeweils drei Monate. (Auszug)",
       f"{_GII}/bgb/__573c.html"),
    _e("BGB", "§ 574", "Widerspruch des Mieters gegen die Kündigung",
       "(1) Der Mieter kann der Kündigung des Vermieters widersprechen und von ihm die Fortsetzung des "
       "Mietverhältnisses verlangen, wenn die Beendigung des Mietverhältnisses für den Mieter, seine "
       "Familie oder einen anderen Angehörigen seines Haushalts eine Härte bedeuten würde, die auch "
       "unter Würdigung der berechtigten Interessen des Vermieters nicht zu rechtfertigen ist. (Auszug)",
       f"{_GII}/bgb/__574.html"),
    _e("BetrKV", "§ 1", "Betriebskosten",
       "(1) Betriebskosten sind die Kosten, die dem Eigentümer (…) durch das Eigentum (…) am Grundstück "
       "oder durch den bestimmungsmäßigen Gebrauch des Gebäudes (…) laufend entstehen. (2) Zu den "
       "Betriebskosten gehören nicht: 1. die Kosten der (…) Verwaltung (…), 2. die Kosten (…) der "
       "Instandsetzung und Instandhaltung. (Auszug)",
       f"{_GII}/betrkv/__1.html"),
    _e("BetrKV", "§ 2", "Aufstellung der Betriebskosten",
       "Betriebskosten im Sinne von § 1 sind: 1. die laufenden öffentlichen Lasten des Grundstücks, "
       "2. die Kosten der Wasserversorgung, 3. die Kosten der Entwässerung, 4. die Kosten des Betriebs "
       "der zentralen Heizungsanlage (…), 8. die Kosten der Straßenreinigung und Müllbeseitigung (…), "
       "17. sonstige Betriebskosten (…). (Auszug)",
       f"{_GII}/betrkv/__2.html"),

    # ------------------------------------------------------------------
    # Firmenrecht – Kleingewerbe & Einzelunternehmer
    # ------------------------------------------------------------------
    _e("GewO", "§ 14", "Anzeigepflicht",
       "(1) Wer den selbständigen Betrieb eines stehenden Gewerbes (…) anfängt, muss dies der "
       "zuständigen Behörde gleichzeitig anzeigen. Das Gleiche gilt, wenn der Betrieb verlegt wird, "
       "der Gegenstand des Gewerbes gewechselt oder auf Waren oder Leistungen ausgedehnt wird (…) oder "
       "der Betrieb aufgegeben wird. (Auszug)",
       f"{_GII}/gewo/__14.html"),
    _e("UStG", "§ 19", "Besteuerung der Kleinunternehmer",
       "(1) Für Umsätze im Sinne des § 1 Absatz 1 Nummer 1, die von inländischen Kleinunternehmern "
       "bewirkt werden, wird die Umsatzsteuer nicht erhoben. Kleinunternehmer ist ein Unternehmer, "
       "dessen Gesamtumsatz im vorangegangenen Kalenderjahr 25 000 Euro nicht überschritten hat und im "
       "laufenden Kalenderjahr 100 000 Euro nicht überschreitet. (Auszug)",
       f"{_GII}/ustg_1980/__19.html"),
    _e("BGB", "§ 14", "Unternehmer",
       "(1) Unternehmer ist eine natürliche oder juristische Person oder eine rechtsfähige "
       "Personengesellschaft, die bei Abschluss eines Rechtsgeschäfts in Ausübung ihrer gewerblichen "
       "oder selbständigen beruflichen Tätigkeit handelt.",
       f"{_GII}/bgb/__14.html"),
    _e("AO", "§ 147", "Ordnungsvorschriften für die Aufbewahrung von Unterlagen",
       "(1) Die folgenden Unterlagen sind geordnet aufzubewahren: 1. Bücher und Aufzeichnungen, "
       "Inventare, Jahresabschlüsse (…) 4. Buchungsbelege (…). (3) Die in Absatz 1 Nr. 1 (…) "
       "aufgeführten Unterlagen sind zehn Jahre, die sonstigen in Absatz 1 aufgeführten Unterlagen "
       "sechs Jahre aufzubewahren; Buchungsbelege sind acht Jahre aufzubewahren. (Auszug)",
       f"{_GII}/ao_1977/__147.html"),

    # ------------------------------------------------------------------
    # Firmenrecht – GmbH & e.K.
    # ------------------------------------------------------------------
    _e("HGB", "§ 1", "Istkaufmann",
       "(1) Kaufmann im Sinne dieses Gesetzbuchs ist, wer ein Handelsgewerbe betreibt. (2) "
       "Handelsgewerbe ist jeder Gewerbebetrieb, es sei denn, dass das Unternehmen nach Art oder "
       "Umfang einen in kaufmännischer Weise eingerichteten Geschäftsbetrieb nicht erfordert.",
       f"{_GII}/hgb/__1.html"),
    _e("HGB", "§ 2", "Kannkaufmann",
       "Ein gewerbliches Unternehmen, dessen Gewerbebetrieb nicht schon nach § 1 Abs. 2 Handelsgewerbe "
       "ist, gilt als Handelsgewerbe im Sinne dieses Gesetzbuchs, wenn die Firma des Unternehmens in "
       "das Handelsregister eingetragen ist. (Auszug)",
       f"{_GII}/hgb/__2.html"),
    _e("HGB", "§ 5", "Kaufmann kraft Eintragung",
       "Ist eine Firma im Handelsregister eingetragen, so kann gegenüber demjenigen, welcher sich auf "
       "die Eintragung beruft, nicht geltend gemacht werden, dass das unter der Firma betriebene "
       "Gewerbe kein Handelsgewerbe sei.",
       f"{_GII}/hgb/__5.html"),
    _e("HGB", "§ 6", "Handelsgesellschaften; Formkaufmann",
       "(1) Die in Betreff der Kaufleute gegebenen Vorschriften finden auch auf die "
       "Handelsgesellschaften Anwendung. (2) Die Rechte und Pflichten eines Vereins, dem das Gesetz "
       "ohne Rücksicht auf den Gegenstand des Unternehmens die Eigenschaft eines Kaufmanns beilegt, "
       "werden durch die Vorschrift des § 1 Abs. 2 nicht berührt.",
       f"{_GII}/hgb/__6.html"),
    _e("HGB", "§ 7", "Kaufmannseigenschaft und öffentliches Recht",
       "Durch die Vorschriften des öffentlichen Rechtes, nach welchen die Befugnis zum Gewerbebetriebe "
       "ausgeschlossen oder von gewissen Voraussetzungen abhängig gemacht ist, wird die Anwendung der "
       "die Kaufleute betreffenden Vorschriften dieses Gesetzbuchs nicht berührt.",
       f"{_GII}/hgb/__7.html"),
    _e("HGB", "§ 8", "Handelsregister",
       "(1) Das Handelsregister wird von den Gerichten elektronisch geführt. (Auszug)",
       f"{_GII}/hgb/__8.html"),
    _e("HGB", "§ 15", "Publizität des Handelsregisters",
       "(1) Solange eine in das Handelsregister einzutragende Tatsache nicht eingetragen und bekannt "
       "gemacht ist, kann sie von demjenigen, in dessen Angelegenheiten sie einzutragen war, einem "
       "Dritten nicht entgegengesetzt werden, es sei denn, dass sie diesem bekannt war. (Auszug)",
       f"{_GII}/hgb/__15.html"),
    _e("HGB", "§ 29", "Anmeldepflicht des Einzelkaufmanns",
       "Jeder Kaufmann ist verpflichtet, seine Firma, den Ort und die inländische Geschäftsanschrift "
       "seiner Handelsniederlassung bei dem Gericht, in dessen Bezirke sich die Niederlassung "
       "befindet, zur Eintragung in das Handelsregister anzumelden.",
       f"{_GII}/hgb/__29.html"),
    _e("HGB", "§ 89a", "Außerordentliche Kündigung des Handelsvertretervertrags",
       "(1) Das Vertragsverhältnis kann von jedem Teil aus wichtigem Grund ohne Einhaltung einer "
       "Kündigungsfrist gekündigt werden. Dieses Recht kann nicht ausgeschlossen oder beschränkt "
       "werden. (2) Wird die Kündigung durch ein Verhalten veranlasst, das der andere Teil zu vertreten "
       "hat, so ist dieser zum Ersatz des durch die Aufhebung des Vertragsverhältnisses entstehenden "
       "Schadens verpflichtet.",
       f"{_GII}/hgb/__89a.html"),
    _e("HGB", "§ 257", "Aufbewahrung von Unterlagen; Aufbewahrungsfristen",
       "(1) Jeder Kaufmann ist verpflichtet, die folgenden Unterlagen geordnet aufzubewahren: "
       "1. Handelsbücher, Inventare, Eröffnungsbilanzen, Jahresabschlüsse (…), 4. Buchungsbelege. (…) "
       "(4) Die in Absatz 1 Nr. 1 (…) aufgeführten Unterlagen sind zehn Jahre, die sonstigen (…) sechs "
       "Jahre aufzubewahren; Buchungsbelege sind acht Jahre aufzubewahren. (Auszug)",
       f"{_GII}/hgb/__257.html"),
    _e("GmbHG", "§ 5", "Stammkapital; Geschäftsanteil",
       "(1) Das Stammkapital der Gesellschaft muss mindestens fünfundzwanzigtausend Euro betragen. "
       "(Auszug)",
       f"{_GII}/gmbhg/__5.html"),
    _e("GmbHG", "§ 6", "Geschäftsführer",
       "(1) Die Gesellschaft muss einen oder mehrere Geschäftsführer haben. (…) (3) Zu Geschäftsführern "
       "können nur natürliche, unbeschränkt geschäftsfähige Personen bestellt werden. (Auszug)",
       f"{_GII}/gmbhg/__6.html"),
    _e("GmbHG", "§ 13", "Juristische Person; Handelsgesellschaft",
       "(1) Die Gesellschaft mit beschränkter Haftung als solche hat selbständig ihre Rechte und "
       "Pflichten; sie kann Eigentum und andere dingliche Rechte an Grundstücken erwerben, vor Gericht "
       "klagen und verklagt werden. (2) Für die Verbindlichkeiten der Gesellschaft haftet den "
       "Gläubigern derselben nur das Gesellschaftsvermögen. (3) Die Gesellschaft gilt als "
       "Handelsgesellschaft im Sinne des Handelsgesetzbuchs.",
       f"{_GII}/gmbhg/__13.html"),
    _e("GmbHG", "§ 35", "Vertretung der Gesellschaft",
       "(1) Die Gesellschaft wird durch die Geschäftsführer gerichtlich und außergerichtlich vertreten. "
       "(Auszug)",
       f"{_GII}/gmbhg/__35.html"),
    _e("GmbHG", "§ 43", "Haftung der Geschäftsführer",
       "(1) Die Geschäftsführer haben in den Angelegenheiten der Gesellschaft die Sorgfalt eines "
       "ordentlichen Geschäftsmannes anzuwenden. (2) Geschäftsführer, welche ihre Obliegenheiten "
       "verletzen, haften der Gesellschaft solidarisch für den entstandenen Schaden. (Auszug)",
       f"{_GII}/gmbhg/__43.html"),

    # ------------------------------------------------------------------
    # Verfahren / übergreifend
    # ------------------------------------------------------------------
    _e("ZPO", "§ 224", "Fristkürzung; Fristverlängerung",
       "(1) Durch Vereinbarung der Parteien können Fristen, mit Ausnahme der Notfristen, abgekürzt "
       "werden. Notfristen sind nur diejenigen Fristen, die in diesem Gesetz als solche bezeichnet "
       "sind. (2) Auf Antrag können richterliche und gesetzliche Fristen abgekürzt oder verlängert "
       "werden, wenn erhebliche Gründe glaubhaft gemacht werden, gesetzliche Fristen jedoch nur in den "
       "besonders bestimmten Fällen.",
       f"{_GII}/zpo/__224.html"),
]
