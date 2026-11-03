# Entwicklerdokumentation — V0.8.5.5

Die Architektur, Schnittstellen und Tests sind in `en.md` und `fr.md` ausführlich beschrieben. Für die Übernahme sind insbesondere die folgenden unveränderlichen Regeln wichtig.

- `.vsynch`: versioniertes JSON, atomare Speicherung und Sicherungskopie `.vsynch.bak`; bestehende Projekte beim Öffnen niemals überschreiben.
- ALTO/PAGE: Polygone, Zeilenkennungen, Lesereihenfolge und ausgeschlossene Bereiche erhalten.
- `reading_stream.py`, `textual_progress.py`: das bestätigte Abgleichmodell der V0.7.4 unverändert beibehalten.
- TEI: textzeugenspezifisches `<lb edRef="#ID"/>`; mehrdeutige Variantenapparate müssen eine automatische Zuordnung verhindern.
- `varians_export.py`: `validated/`, `working/` und `base_keys` beachten; Exportsemantik niemals stillschweigend ändern.
- `hd_registry.py`: geprüfte Zuordnungen von Canvas zu Datei und vollständige Abdeckung vor dem Export lokaler Kopien sicherstellen.
- `i18n/<lang>.xml`: Schlüssel und Platzhalter müssen in allen Sprachkatalogen übereinstimmen; editorische Quellen werden nicht übersetzt.
- Tests: `PYTHONPATH=. pytest -q`; GUI-Test unter Windows und Import in Varians bleiben erforderlich.

Siehe die [vollständige technische Dokumentation auf Englisch](en.md) und die [französische Dokumentation](fr.md).

**V0.8.5.5:** 653/653 Einträge im Sprachkatalog; die endgültige fachsprachliche Prüfung durch Muttersprachler steht noch aus.
