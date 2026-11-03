# User guide — Varians-Synchro V0.8.5.5

Varians-Synchro aligns physical manuscript lines from local/IIIF images and ALTO/PAGE segmentation. It prepares alignments for Varians without modifying source documents.

> ALTO / PAGE-XML / IIIF / TEI / HTR / `.vsynch` / `base_keys`: technical identifiers and original manuscript text are never translated.

## Install and launch

Install Python and PySide6. On Windows run start_windows.bat or run.py. With Spyder prefer the isolated process described in GUIDE_DEPANNAGE_SPYDER.md.

## Create a project and witnesses

Choose New project and save the .vsynch file immediately. Add witnesses with their identifiers, local images or IIIF Manifest, ALTO/PAGE files and optional TEI XML edition. Choose a pivot witness.

## Associate resources

In step 2 check natural image order and image ↔ XML pairings. Exact filename matches take priority; natural-order matches are suggestions requiring review. Canvas without segmentation may remain unlinked.

## Set the physical scope

Ignore lines outside the edited passage, including leading and trailing material. A passage can span multiple pages and columns.

## Link TEI

The TEI must contain witness-specific <lb edRef="#ID"/> elements. Compare counts of TEI and active physical lines. Review the manuscript crop and edited text (first line by default; select any line to inspect it). Ambiguous apparatus readings block automatic binding.

## Align witnesses

In step 3 choose two witnesses, place homologous anchors, generate cumulative-text-progress suggestions and review them. Single-click replaces the witness selection across all pages; Ctrl-click toggles an item; Shift-click selects a range. Counterpart highlighting is not a selection.

## Validate and manage exceptions

Validate correct groups, revise uncertain groups and confirm genuine omissions pair by pair. Globally ignored lines are outside the witness scope. Manual and validated groups are protected against automatic recalculation.

## IIIF HD and external HTR

Download selected HD Canvas only and save the project to retain Canvas-to-file mapping. Copies enter Varians export only if every required segmented Canvas has a verified local copy. Export for HTR / Reimport HTR concern optional external recognition.

## Finalize and export

Use step 4 to run the read-only integrity audit. Export validated or working JSON sets, or a prefilled Varians project folder. Review warnings before import.

## Saving and troubleshooting

Projects use atomic .vsynch saving and a previous-version .vsynch.bak. Back up your project before editing scope and resources. An unavailable IIIF server does not necessarily mean lost metadata; check paths, connectivity and audit output.

---

## Technical references

- `GUIDE_COPIES_HD_V0853.md`
- `GUIDE_LIAISON_TEI_V083.md`
- `GUIDE_REVISION_RAPIDE.md`
- `GUIDE_SAUVEGARDE_V085.md`
