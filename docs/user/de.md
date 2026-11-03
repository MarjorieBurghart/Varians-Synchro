# Benutzerhandbuch — Varians-Synchro V0.8.5.5

Varians-Synchro gleicht die physischen Zeilen verschiedener Handschriften anhand lokaler oder IIIF-Bilder und ALTO/PAGE-Segmentierungen ab. Die Quelldateien bleiben unverändert.

> ALTO / PAGE-XML / IIIF / TEI / HTR / `.vsynch` / `base_keys` sind technische Bezeichner. Kennungen und Originaltexte der Handschriften werden niemals übersetzt.

## Installation und Start

Python und PySide6 installieren. Unter Windows start_windows.bat oder run.py ausführen; in Spyder das isolierte Startverfahren verwenden.

## Projekt und Textzeugen

Ein neues Projekt anlegen und die .vsynch-Datei sofort speichern. Jeden Textzeugen mit Sigle, Bildern beziehungsweise IIIF-Manifest, ALTO/PAGE-Dateien und optionaler TEI-Edition hinzufügen. Einen Pivotzeugen festlegen.

## Ressourcen zuordnen

Im zweiten Schritt die Bildreihenfolge und die Zuordnungen zu ALTO/PAGE prüfen. Übereinstimmende Dateinamen haben Vorrang; natürliche Reihenfolge liefert nur prüfbare Vorschläge.

## Textbereich abgrenzen

Zeilen außerhalb des edierten Abschnitts als ignoriert markieren. Ein Abschnitt darf mehrere Spalten oder Blätter umfassen.

## TEI mit Zeilen verbinden

TEI benötigt zeugenspezifische <lb edRef="#SIGLE"/>-Elemente. Anzahl der TEI-Zeilen und aktiven physischen Zeilen vergleichen. Den angezeigten Bildausschnitt und Editionstext kontrollieren; zunächst wird die erste Zeile gezeigt. Unklare Lesarten des Apparats verhindern die automatische Zuordnung.

## Zeugen abgleichen

Im dritten Schritt ein Zeugenpaar auswählen, gemeinsame Anker setzen und Vorschläge des Textfortschritts prüfen. Einfacher Klick ersetzt die Auswahl; Strg-Klick fügt hinzu oder entfernt; Umschalt-Klick wählt einen Bereich.

## Prüfen und bestätigen

Richtige Gruppen bestätigen und unsichere korrigieren. Bestätigte Auslassungen gelten nur für das jeweilige Zeugenpaar. Manuelle und bestätigte Zuordnungen bleiben vor automatischer Neuberechnung geschützt.

## Neue Segmentierung einer Seite

Wenn eine Seite eine andere ALTO/PAGE-Datei erhält (korrigierte Segmentierung), können sich ihre Zeilen ändern: Eine Zeile wird über ihren Rang auf der Seite bestimmt. Vor dem Ersetzen zeigt Varians-Synchro an, wie viele Gruppen diese Zeilen betreffen. Nach der Bestätigung werden Gruppen, deren Zeilen sich geändert haben, als „[veraltet]“ markiert: Sie dienen nicht mehr als Anker, gehen weder in Berechnungen noch in den Export ein, werden aber nie gelöscht. Der Filter „Veraltet“ im Ausrichtungsfenster listet sie auf; nach Prüfung an den Bildern stellt „Erneut bestätigen…“ sie wieder her, andernfalls lösen Sie die Verknüpfung. Die korrigierte Lesereihenfolge der Seite wird zurückgesetzt.

## IIIF-HD und externe HTR

Nur benötigte Canvas in HD herunterladen und danach das Projekt speichern. Beim Varians-Export werden lokale Kopien nur dann übernommen, wenn sämtliche benötigten ALTO/PAGE-Seiten vollständig abgedeckt und geprüft sind. Die HTR-Schaltflächen dienen einer optionalen externen Texterkennung.

## Abschluss und Export

Im vierten Schritt die schreibgeschützte Integritätsprüfung durchführen. Die JSON-Sätze validated beziehungsweise working oder einen vorbereiteten Varians-Projektordner exportieren.

## Sicherung und Fehlerbehebung

Die .vsynch-Datei wird atomar gespeichert; die vorherige Version liegt als .vsynch.bak vor. Vor größeren Änderungen Sicherungskopien erstellen. Bei IIIF-Problemen Netzwerk und Dateipfade prüfen.

---

## Technische Referenzen

- `GUIDE_COPIES_HD_V0853.md`
- `GUIDE_LIAISON_TEI_V083.md`
- `GUIDE_REVISION_RAPIDE.md`
- `GUIDE_SAUVEGARDE_V085.md`
