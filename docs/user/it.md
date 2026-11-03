# Manuale utente — Varians-Synchro V0.8.5.5

Varians-Synchro allinea le righe fisiche dei testimoni manoscritti usando immagini locali o IIIF e segmentazioni ALTO/PAGE, senza modificare i documenti originali.

> ALTO / PAGE-XML / IIIF / TEI / HTR / `.vsynch` / `base_keys` sono identificativi tecnici. Gli identificativi e i testi originali dei manoscritti non vengono mai tradotti.

## Installazione e avvio

Installare Python e PySide6. Su Windows eseguire start_windows.bat oppure run.py; in Spyder preferire il processo isolato.

## Creare progetto e testimoni

Creare un progetto e salvare subito il file .vsynch. Aggiungere ciascun testimone con sigla, immagini o Manifest IIIF, ALTO/PAGE ed eventuale edizione TEI XML. Designare il testimone pivot.

## Associare le risorse

Nella seconda fase verificare ordine naturale delle immagini e corrispondenze con ALTO/PAGE. I nomi identici hanno precedenza; l’ordine naturale offre proposte da verificare.

## Definire il perimetro

Contrassegnare come ignorate le righe estranee al passo edito. Il passo può attraversare più colonne e carte.

## Collegare TEI e righe

La TEI deve contenere <lb edRef="#SIGLA"/> attribuiti al testimone. Confrontare il numero di righe TEI e fisiche attive. Controllare testo e ritaglio dell’immagine; inizialmente compare la prima riga. Varianti di apparato ambigue impediscono il collegamento automatico.

## Allineare i testimoni

Nella terza fase scegliere una coppia, porre ancore corrispondenti e verificare le proposte. Il clic semplice sostituisce la selezione, Ctrl+clic aggiunge/rimuove, Maiusc+clic seleziona un intervallo.

## Convalidare e correggere

Convalidare i gruppi corretti e rivedere quelli incerti. Le assenze confermate riguardano solo la coppia. I legami manuali e convalidati restano protetti.

## Nuova segmentazione di una pagina

Assegnare a una pagina un altro file ALTO/PAGE (segmentazione corretta) può cambiarne le righe: una riga è individuata dalla sua posizione nella pagina. Prima della sostituzione, Varians-Synchro indica quanti gruppi citano queste righe. Dopo la conferma, i gruppi le cui righe sono cambiate sono segnati «[obsoleto]»: non sono più usati come ancore, nei calcoli né nell’esportazione, ma non vengono mai eliminati. Il filtro «Obsoleti» della finestra di allineamento li elenca; dopo la verifica sulle immagini, «Riconvalida…» li ripristina, altrimenti scollegali. L’ordine di lettura corretto della pagina viene azzerato.

## IIIF HD e HTR esterna

Scaricare soltanto i Canvas HD utili e salvare il progetto. Le copie locali entrano nell’esportazione Varians solo se tutti i Canvas segmentati necessari sono coperti e verificati. I comandi HTR riguardano un’elaborazione esterna facoltativa.

## Finalizzazione ed esportazione

Nella quarta fase eseguire il controllo di integrità in sola lettura. Esportare i JSON validated e working o un progetto Varians precompilato.

## Salvataggi e problemi

Il salvataggio .vsynch è atomico e mantiene la copia precedente .vsynch.bak. Eseguire copie prima di modifiche importanti; controllare rete e percorsi in caso di problemi IIIF.

---

## Riferimenti tecnici

- `GUIDE_COPIES_HD_V0853.md`
- `GUIDE_LIAISON_TEI_V083.md`
- `GUIDE_REVISION_RAPIDE.md`
- `GUIDE_SAUVEGARDE_V085.md`
