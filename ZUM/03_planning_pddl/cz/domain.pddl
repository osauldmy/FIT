(define (domain zum-du3-kouzelny-svet)
    (:requirements :strips :typing)
    (:types
        ; --- META TYPES ---
        objekt
        lokace
        stvoreni - objekt
        vec - objekt

        ; --- NORMAL TYPES ---
        clovek - stvoreni
        medved - stvoreni

        akademie - lokace
        hospoda - lokace
        mesto - lokace
        more - lokace
        pristav - lokace
        les - lokace
        reka - lokace
        ostrov - lokace
        majak - lokace

        voda - vec
        drevo - vec
        kvetina - vec
        prstynek - vec
        perla - vec
        mapa - vec
        alkohol - vec
        kokain - vec
        zlate-zrnko - vec
        zlata-mince - vec
        zlata-cihla - vec

        zbozi - vec
        kokos - zbozi
        kuze - zbozi

        lod - vec
        clun - lod
        fregata - lod
        karavela - lod
    )

    (:predicates
        (existuje-cesta ?lokace-1 - lokace ?lokace-2 - lokace)
        (existuje-cesta-morem ?lokace-1 - lokace ?lokace-2 - lokace)

        (nachazi-se ?objekt - objekt ?lokace - lokace)
        (vlastni ?clovek - clovek ?vec - vec)

        (ma-zaznam-v-rejstriku-trestu ?clovek - clovek)
        (ma-dobre-znamosti ?clovek - clovek)
        (ma-pochybne-znamosti ?clovek - clovek)
        (ma-znamosti-s-paseraky ?clovek - clovek)
        (ma-porazene-piraty ?clovek - clovek)
        (ma-oslnenou-divku ?clovek - clovek)
        (je-zocelen ?clovek - clovek)
        (je-nameteny ?clovek - clovek)
        (je-opily ?clovek - clovek)
        (je-zavisly-na-alkoholu ?clovek - clovek)
        (je-zasnoubeny-s-divkou ?clovek - clovek)
        (je-kapitanem ?clovek - clovek)
        (je-stastny1 ?clovek - clovek)
        (je-stastny2 ?clovek - clovek)
        (je-stastny3 ?clovek - clovek)

        (je-stastny ?clovek - clovek)
    )

    ; POHYB ATD --------------------------------------------------------------------------

    (:action sel
        :parameters (?clovek - clovek ?lokace-1 - lokace ?lokace-2 - lokace)
        :precondition (and
            (nachazi-se ?clovek ?lokace-1)
            (existuje-cesta ?lokace-1 ?lokace-2)
        )
        :effect (and
            (nachazi-se ?clovek ?lokace-2)
            (not (nachazi-se ?clovek ?lokace-1))
        )
    )

    (:action plul
        :parameters (?clovek - clovek ?lod - lod ?lokace-1 - lokace ?lokace-2 - lokace)
        :precondition (and
            (nachazi-se ?clovek ?lokace-1)
            (existuje-cesta-morem ?lokace-1 ?lokace-2)
            (vlastni ?clovek ?lod)
            (je-zocelen ?clovek)
        )
        :effect (and
            (nachazi-se ?clovek ?lokace-2)
            (not (nachazi-se ?clovek ?lokace-1))
        )
    )

    (:action ziskal
        :parameters (?clovek - clovek ?vec - vec ?lokace - lokace)
        :precondition (and
            (nachazi-se ?clovek ?lokace)
            (nachazi-se ?vec ?lokace)
        )
        :effect (and
            (vlastni ?clovek ?vec)
        )
    )


    ; PENIZE ------------------------------------------------------------------------------------------

    (:action pracoval
        :parameters (?clovek - clovek ?zlate-zrnko - zlate-zrnko ?pristav - pristav)
        :precondition (and
            (nachazi-se ?clovek ?pristav)
        )
        :effect (and
            (vlastni ?clovek ?zlate-zrnko)
        )
    )

    (:action ryzoval-zlato
        :parameters (?clovek - clovek ?zlate-zrnko - zlate-zrnko ?reka - reka)
        :precondition (and
            (nachazi-se ?clovek ?reka)
        )
        :effect (and
            (vlastni ?clovek ?zlate-zrnko)
        )
    )

    (:action prodal
        :parameters (?clovek - clovek ?zbozi - zbozi ?pristav - pristav ?zlata-mince - zlata-mince)
        :precondition (and
            (nachazi-se ?clovek ?pristav)
            (vlastni ?clovek ?zbozi)
        )
        :effect (and
            (not (vlastni ?clovek ?zbozi))
            (vlastni ?clovek ?zlata-mince)
        )
    )

    (:action stradal
        :parameters (?clovek - clovek ?zlate-zrnko - zlate-zrnko ?zlata-mince - zlata-mince ?mesto - mesto)
        :precondition (and
            (vlastni ?clovek ?zlate-zrnko)
            (nachazi-se ?clovek ?mesto)
        )
        :effect (and
            (vlastni ?clovek ?zlata-mince)
            (not (vlastni ?clovek ?zlate-zrnko))
            (ma-dobre-znamosti ?clovek)
        )
    )

    (:action investoval
        :parameters (?clovek - clovek ?zlata-mince - zlata-mince ?zlata-cihla - zlata-cihla ?mesto - mesto)
        :precondition (and
            (vlastni ?clovek ?zlata-mince)
            (nachazi-se ?clovek ?mesto)
        )
        :effect (and
            (vlastni ?clovek ?zlata-cihla)
            (not (vlastni ?clovek ?zlata-mince))
            (ma-dobre-znamosti ?clovek)
        )
    )

    (:action pustil-se-do-zlodejiny
        :parameters (?clovek - clovek ?zlata-mince - zlata-mince ?mesto - mesto)
        :precondition (and (nachazi-se ?clovek ?mesto))
        :effect (and
            (vlastni ?clovek ?zlata-mince)
            (ma-zaznam-v-rejstriku-trestu ?clovek)
        )
    )

    ; ALKOHOL -------------------------------------------------------------------------------

    (:action koupil-alkohol
        :parameters (?clovek - clovek ?alkohol - alkohol ?zlate-zrnko - zlate-zrnko ?hospoda - hospoda)
        :precondition (and
            (nachazi-se ?clovek ?hospoda)
            (vlastni ?clovek ?zlate-zrnko)
        )
        :effect (and
            (not (vlastni ?clovek ?zlate-zrnko))
            (vlastni ?clovek ?alkohol)
        )
    )

    (:action dal-si-panaka
        :parameters (?clovek - clovek ?alkohol - alkohol)
        :precondition (and (vlastni ?clovek ?alkohol))
        :effect (and
            (je-nameteny ?clovek)
            (not (vlastni ?clovek ?alkohol))
        )
    )

    (:action opil-se
        :parameters (?clovek - clovek ?alkohol - alkohol)
        :precondition (and (vlastni ?clovek ?alkohol) (je-nameteny ?clovek))
        :effect (and
            (je-opily ?clovek)
            (not (je-nameteny ?clovek))
            (not (vlastni ?clovek ?alkohol))
        )
    )

    (:action opil-se-a-ziskal-alkozavislost
        :parameters (?clovek - clovek ?alkohol - alkohol)
        :precondition (and
            (vlastni ?clovek ?alkohol)
            (je-opily ?clovek)
        )
        :effect (and
            (je-zavisly-na-alkoholu ?clovek)
            (not (je-opily ?clovek))
            (not (vlastni ?clovek ?alkohol))
        )
    )

    (:action dopral-si-ledovou-koupel-a-vystrizlivel
        :parameters (?clovek - clovek ?lokace - lokace ?voda - voda)
        :precondition (and
            (nachazi-se ?voda ?lokace)
            (nachazi-se ?clovek ?lokace)
        )
        :effect (and
            (not (je-nameteny ?clovek))
            (not (je-opily ?clovek))
        )
    )

    ; LODE ---------------------------------------------------------------------------------

    (:action ukradl-clun
        :parameters (?clovek - clovek ?clun - clun ?reka - reka)
        :precondition (and
            (nachazi-se ?clovek ?reka)
        )
        :effect (and
            (vlastni ?clovek ?clun)
            (ma-zaznam-v-rejstriku-trestu ?clovek)
        )
    )

    (:action vytvoril-clun
        :parameters (?clovek - clovek ?clun - clun ?drevo - drevo)
        :precondition (and (vlastni ?clovek ?drevo))
        :effect (and
            (not (vlastni ?clovek ?drevo))
            (vlastni ?clovek ?clun)
        )
    )

    (:action sehnal-fregatu
        :parameters (?clovek - clovek ?fregata - fregata ?clun - clun ?drevo - drevo ?zlate-zrnko - zlate-zrnko)
        :precondition (and
            (vlastni ?clovek ?clun)
            (vlastni ?clovek ?drevo)
            (vlastni ?clovek ?zlate-zrnko)
        )
        :effect (and
            (not (vlastni ?clovek ?clun))
            (not (vlastni ?clovek ?drevo))
            (not (vlastni ?clovek ?zlate-zrnko))
            (vlastni ?clovek ?fregata)
        )
    )

    (:action sehnal-karavelu
        :parameters (?clovek - clovek ?karavela - karavela ?clun - clun ?drevo - drevo ?zlata-mince - zlata-mince)
        :precondition (and
            (vlastni ?clovek ?clun)
            (vlastni ?clovek ?drevo)
            (vlastni ?clovek ?zlata-mince)
        )
        :effect (and
            (not (vlastni ?clovek ?clun))
            (not (vlastni ?clovek ?drevo))
            (not (vlastni ?clovek ?zlata-mince))
            (vlastni ?clovek ?karavela)
        )
    )

    ; NEJAKA DALSI LOGIKA -------------------------------------------------------------------------------

    (:action vymenil-alkohol-za-mapu
        :parameters (?clovek - clovek ?kouzelny-dedecek - clovek ?alkohol - alkohol ?mapa - mapa ?les - les)
        :precondition (and
            (nachazi-se ?kouzelny-dedecek ?les)
            (vlastni ?kouzelny-dedecek ?mapa)
            (nachazi-se ?clovek ?les)
            (vlastni ?clovek ?alkohol)
        )
        :effect (and
            (ma-pochybne-znamosti ?clovek)
            (vlastni ?clovek ?mapa)
            (not (vlastni ?clovek ?alkohol))
        )
    )

    (:action vybral-skrys
        :parameters (?clovek - clovek ?kokain - kokain ?mapa - mapa ?ostrov - ostrov)
        :precondition (and
            (nachazi-se ?clovek ?ostrov)
            (vlastni ?clovek ?mapa)
        )
        :effect (and
            (vlastni ?clovek ?kokain)
            (not (vlastni ?clovek ?mapa))
        )
    )

    ; VZTAHY ---------------------------------------------------------------------------

    (:action seznamil-se-s-paseraky
        :parameters (?clovek - clovek ?zlata-cihla - zlata-cihla ?pristav - pristav)
        :precondition (and
            (ma-pochybne-znamosti ?clovek)
            (nachazi-se ?clovek ?pristav)
            (vlastni ?clovek ?zlata-cihla)
        )
        :effect (and
            (ma-znamosti-s-paseraky ?clovek)
        )
    )

    (:action napadli-pirati
        :parameters (
            ?clovek - clovek
            ?more - more
            ?zlate-zrnko - zlate-zrnko
            ?zlata-mince - zlata-mince
            ?zlata-cihla - zlata-cihla
            ?fregata - fregata
            ?karavela - karavela
        )
        :precondition (and
            (nachazi-se ?clovek ?more)
            (not (je-zocelen ?clovek))
        )
        :effect (and
            (je-zocelen ?clovek)
            (not (vlastni ?clovek ?zlate-zrnko))
            (not (vlastni ?clovek ?zlata-mince))
            (not (vlastni ?clovek ?zlata-cihla))
            (not (vlastni ?clovek ?fregata))
            (not (vlastni ?clovek ?karavela))
        )
    )

    (:action pridal-se-k-piratum
        :parameters (?clovek - clovek ?more - more)
        :precondition (and
            (nachazi-se ?clovek ?more)
            (ma-pochybne-znamosti ?clovek)
        )
        :effect (and (je-nameteny ?clovek))
    )

    (:action zaplatil-rundu
        :parameters (?clovek - clovek ?zlata-mince - zlata-mince ?hospoda - hospoda ?alkohol - alkohol)
        :precondition (and
            (nachazi-se ?clovek ?hospoda)
            (vlastni ?clovek ?zlata-mince)
        )
        :effect (and
            (vlastni ?clovek ?alkohol)
            (ma-dobre-znamosti ?clovek)
            (not (vlastni ?clovek ?zlata-mince))
        )
    )

    (:action koupil-si-odpustek
        :parameters (?clovek - clovek ?mesto - mesto ?zlate-zrnko - zlate-zrnko)
        :precondition (and
            (nachazi-se ?clovek ?mesto)
            (ma-zaznam-v-rejstriku-trestu ?clovek)
            (vlastni ?clovek ?zlate-zrnko)
        )
        :effect (and
            (not (ma-zaznam-v-rejstriku-trestu ?clovek))
            (not (vlastni ?clovek ?zlate-zrnko))
        )
    )

    (:action venoval-se-verejnym-pracim
        :parameters (?clovek - clovek ?mesto - mesto)
        :precondition (and
            (nachazi-se ?clovek ?mesto)
            (ma-zaznam-v-rejstriku-trestu ?clovek)
        )
        :effect (and
            (not (ma-zaznam-v-rejstriku-trestu ?clovek))
            (je-nameteny ?clovek)
        )
    )

    (:action vystudoval-akademii-a-stal-se-kapitanem
        :parameters (?clovek - clovek ?zlata-mince - zlata-mince ?akademie - akademie)
        :precondition (and
            (vlastni ?clovek ?zlata-mince)
            (nachazi-se ?clovek ?akademie)
        )
        :effect (and
            (not (vlastni ?clovek ?zlata-mince))
            (je-kapitanem ?clovek)
            (ma-oslnenou-divku ?clovek)
        )
    )

    ; OSLNENI ATD ------------------------------------------------------------------------------

    (:action porval-se-s-medvedem
        :parameters (?clovek - clovek ?medved - medved ?les - les ?kuze - kuze)
        :precondition (and
            (nachazi-se ?clovek ?les)
            (nachazi-se ?medved ?les)
        )
        :effect (and
            (vlastni ?clovek ?kuze)
            (je-zocelen ?clovek)
            (ma-oslnenou-divku ?clovek)
        )
    )

    (:action zocelil-se-v-bitce-v-hospode
        :parameters (?clovek - clovek ?hospoda - hospoda)
        :precondition (and
            (nachazi-se ?clovek ?hospoda)
            (je-nameteny ?clovek)
        )
        :effect (and
            (je-zocelen ?clovek)
        )
    )

    (:action porazil-piraty
        :parameters (
            ?clovek - clovek
            ?more - more
            ?karavela - karavela
            ?clun - clun
            ?fregata - fregata
            ?zlate-zrnko - zlate-zrnko
            ?zlata-mince - zlata-mince
            ?zlata-cihla - zlata-cihla
        )
        :precondition (and
            (je-zocelen ?clovek)
            (vlastni ?clovek ?karavela)
            (nachazi-se ?clovek ?more)
        )
        :effect (and
            (ma-porazene-piraty ?clovek)
            (ma-oslnenou-divku ?clovek)
            (vlastni ?clovek ?clun)
            (vlastni ?clovek ?fregata)
            (vlastni ?clovek ?zlate-zrnko)
            (vlastni ?clovek ?zlata-mince)
            (vlastni ?clovek ?zlata-cihla)
        )
    )

    (:action sehnal-prstynek
        :parameters (?clovek - clovek ?prstynek - prstynek ?zlata-cihla - zlata-cihla ?perla - perla)
        :precondition (and
            (vlastni ?clovek ?zlata-cihla)
            (vlastni ?clovek ?perla)
        )
        :effect (and
            (vlastni ?clovek ?prstynek)
            (not (vlastni ?clovek ?zlata-cihla))
            (not (vlastni ?clovek ?perla))
        )
    )

    (:action donesl-divce-prstynek-a-kvetinu
        :parameters (?clovek - clovek ?divka - clovek ?kvetina - kvetina ?prstynek - prstynek ?majak - majak)
        :precondition (and
            (ma-oslnenou-divku ?clovek)
            (vlastni ?clovek ?kvetina)
            (vlastni ?clovek ?prstynek)
            (nachazi-se ?clovek ?majak)
        )
        :effect (and
            (je-zasnoubeny-s-divkou ?clovek)
        )
    )

    ; -------------------------------------------
    ;               FINAL
    ; -------------------------------------------

    (:action ozenil-se
        :parameters (?clovek - clovek ?kvetina - kvetina ?prstynek - prstynek ?ostrov - ostrov)
        :precondition (and
            (je-zasnoubeny-s-divkou ?clovek)
            (ma-dobre-znamosti ?clovek)
            (not (ma-zaznam-v-rejstriku-trestu ?clovek))
            (not (je-opily ?clovek))
            (not (je-zavisly-na-alkoholu ?clovek))
            (nachazi-se ?clovek ?ostrov)
        )
        :effect (and
            (je-stastny1 ?clovek)
            (je-stastny ?clovek)
        )
    )

    (:action stal-se-admiralem
        :parameters (?clovek - clovek ?akademie - akademie)
        :precondition (and
            (je-kapitanem ?clovek)
            (ma-porazene-piraty ?clovek)
            (nachazi-se ?clovek ?akademie)
            (not (je-nameteny ?clovek))
            (not (je-opily ?clovek))
            (not (je-zavisly-na-alkoholu ?clovek))
        )
        :effect (and
            (je-stastny2 ?clovek)
            (je-stastny ?clovek)
        )
    )

    (:action dal-se-na-kokain
        :parameters (?clovek - clovek ?kokain - kokain ?zlata-cihla - zlata-cihla ?fregata - fregata)
        :precondition (and
            (vlastni ?clovek ?kokain)
            (ma-znamosti-s-paseraky ?clovek)
            (vlastni ?clovek ?zlata-cihla)
            (vlastni ?clovek ?fregata)
            (je-zavisly-na-alkoholu ?clovek)
        )
        :effect (and
            (je-stastny3 ?clovek)
            (je-stastny ?clovek)
        )
    )
)
