# Uživatelská příručka — Varians-Synchro V0.8.5.5

Varians-Synchro zarovnává fyzické řádky rukopisných svědků podle lokálních či IIIF obrazů a segmentace ALTO/PAGE. Původní soubory nemění.

> ALTO / PAGE-XML / IIIF / TEI / HTR / `.vsynch` / `base_keys` jsou technické identifikátory. Identifikátory a původní texty rukopisů se nikdy nepřekládají.

## Instalace a spuštění

Nainstalujte Python a PySide6. Ve Windows spusťte start_windows.bat nebo run.py; ve Spyderu použijte oddělený proces.

## Projekt a svědkové

Založte projekt a ihned uložte soubor .vsynch. Přidejte svědky se siglou, obrazy nebo IIIF manifestem, soubory ALTO/PAGE a případně edicí TEI XML. Určete pivotního svědka.

## Přiřazení zdrojů

Ve druhém kroku zkontrolujte pořadí obrazů a přiřazení XML. Shoda názvů má přednost; přiřazení podle přirozeného pořadí je pouze návrhem ke kontrole.

## Vymezení rozsahu

Označte řádky mimo editovaný úsek jako ignorované. Úsek může procházet více sloupci a folii.

## Propojení TEI

TEI musí obsahovat řádky <lb edRef="#SIGLA"/> přiřazené svědkovi. Porovnejte počty řádků TEI a aktivních fyzických řádků. Prohlédněte text a výřez obrazu; nejprve se zobrazí první řádek. Nejednoznačné varianty brání automatickému propojení.

## Zarovnání svědků

Ve třetím kroku vyberte dvojici svědků, určete odpovídající kotvy a zkontrolujte návrhy. Běžné kliknutí nahradí výběr, Ctrl+klik přidá či odebere řádek, Shift+klik vybere rozsah.

Již zarovnané dvojice jsou se svým postupem uvedeny pod tlačítkem „Zarovnat svědky“: dvojklikem na dvojici nebo klávesou Enter znovu otevřete její zarovnání, jedním kliknutím ji vyberete v obou nabídkách.

## Ověření a výjimky

Potvrďte správné vazby a opravte nejisté. Potvrzená absence se vztahuje jen k dané dvojici. Ručně vytvořené a potvrzené vazby zůstávají chráněné.

## Nová segmentace stránky

Přiřazení jiného souboru ALTO/PAGE ke stránce (opravená segmentace) může změnit její řádky: řádek je určen svým pořadím na stránce. Před nahrazením Varians-Synchro uvede, kolik skupin na tyto řádky odkazuje. Po potvrzení jsou skupiny, jejichž řádky se změnily, označeny „[zastaralé]“: už se nepoužívají jako kotvy, ve výpočtech ani v exportu, ale nikdy nejsou smazány. Filtr „Zastaralé“ v okně zarovnání je vypíše; po kontrole na obrázcích je „Znovu potvrdit…“ obnoví, jinak zrušte jejich propojení. Opravené pořadí čtení stránky se vynuluje.

## IIIF HD a externí HTR

Stahujte jen požadované Canvas ve vysokém rozlišení a poté projekt uložte. Lokální kopie se exportují do Varians jen při úplném a ověřeném pokrytí všech obrazů s ALTO/PAGE. Nástroje HTR slouží k volitelnému externímu zpracování.

## Dokončení a export

Ve čtvrtém kroku spusťte kontrolu integrity pouze pro čtení. Exportujte validated či working JSON nebo předvyplněný projekt Varians.

## Zálohování a řešení potíží

Projekt .vsynch se ukládá atomicky a předchozí kopie se nachází v .vsynch.bak. Před změnami zdrojů si vytvořte zálohu; při potížích s IIIF ověřte síť a cesty.

---

## Technické reference

- `GUIDE_COPIES_HD_V0853.md`
- `GUIDE_LIAISON_TEI_V083.md`
- `GUIDE_REVISION_RAPIDE.md`
- `GUIDE_SAUVEGARDE_V085.md`
