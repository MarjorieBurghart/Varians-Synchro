# Dokumentace pro vývojáře — V0.8.5.5

Podrobnosti o architektuře, rozhraních a testech obsahují `en.md` a `fr.md`. Při převzetí vývoje dodržujte následující zásady.

- `.vsynch`: verzovaný JSON, atomické ukládání a záloha `.vsynch.bak`; při otevírání nikdy nepřepisovat existující projekty.
- ALTO/PAGE: zachovat polygony, ID řádků, pořadí čtení i vyloučený rozsah.
- `reading_stream.py`, `textual_progress.py`: zachovat schválený model porovnávání z V0.7.4.
- TEI: `<lb edRef="#ID"/>` specifické pro svědka; nejednoznačný kritický aparát musí zabránit automatickému přiřazení.
- `varians_export.py`: respektovat `validated/`, `working/` a `base_keys`; neměnit bez upozornění význam exportu.
- `hd_registry.py`: před exportem místních kopií vyžadovat ověřené vazby Canvas–soubor a úplné pokrytí.
- `i18n/<lang>.xml`: stejné klíče a formátovací parametry ve všech katalozích; ediční prameny se nepřekládají.
- Testy: `PYTHONPATH=. pytest -q`; je ještě nutné ověřit GUI ve Windows a import do Varians.

Viz [úplnou technickou dokumentaci v angličtině](en.md) a [francouzskou dokumentaci](fr.md).

**V0.8.5.5:** 653/653 klíčů v katalogu; odbornou jazykovou revizi rodilým mluvčím je ještě nutné provést.
