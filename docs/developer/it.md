# Documentazione per sviluppatori — V0.8.5.5

Architettura, formati e test sono documentati dettagliatamente in `en.md` e `fr.md`. Per la manutenzione sono fondamentali le regole seguenti.

- `.vsynch`: JSON versionato, salvataggio atomico e copia di sicurezza `.vsynch.bak`; non sovrascrivere mai un progetto esistente durante l’apertura.
- ALTO/PAGE: conservare poligoni, ID delle righe, ordine di lettura e intervalli esclusi.
- `reading_stream.py`, `textual_progress.py`: mantenere il modello di corrispondenza approvato nella V0.7.4.
- TEI: `<lb edRef="#ID"/>` specifico del testimone; un apparato critico ambiguo deve bloccare l’associazione automatica.
- `varians_export.py`: rispettare `validated/`, `working/` e `base_keys`; non cambiare tacitamente la semantica dell’esportazione.
- `hd_registry.py`: verificare le associazioni Canvas–file e la copertura completa prima di esportare copie locali.
- `i18n/<lang>.xml`: chiavi e parametri di sostituzione devono coincidere in tutti i cataloghi; le fonti editoriali non vengono tradotte.
- Test: `PYTHONPATH=. pytest -q`; restano necessari il collaudo GUI su Windows e l’importazione in Varians.

Consultare la [documentazione tecnica completa in inglese](en.md) e la [versione francese](fr.md).

**V0.8.5.5:** 653/653 voci nel catalogo; resta necessaria una revisione terminologica da parte di madrelingua.
