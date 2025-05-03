(define (problem hledani-stesti)
    (:domain zum-du3-kouzelny-svet)
    (:requirements :strips :typing)

    (:objects
        ; --- LOKACE ---
        nejaka-akademie - akademie
        nejaky-les - les
        nejake-mesto - mesto
        nejaky-ostrov - ostrov
        nejaky-pristav - pristav
        nejake-more - more
        nejaka-hospoda - hospoda
        nejaka-reka - reka
        nejaky-majak - majak

        ; --- STVORENI ---
        namornik - clovek
        divka - clovek
        kouzelny-dedecek - clovek
        nejaky-medved - medved

        ; --- VECI ---
        nejaka-voda - voda
        nejake-drevo - drevo
        nejaka-kvetina - kvetina
        nejaky-prstynek - prstynek
        nejaka-perla - perla
        nejake-kokosy - kokos
        medvedi-kuze - kuze
        nejaky-clun - clun
        nejaka-fregata - fregata
        nejaka-karavela - karavela
        nejake-zlate-zrnko - zlate-zrnko
        nejaka-zlata-mince - zlata-mince
        nejaka-zlata-cihla - zlata-cihla
        nejaka-mapa - mapa
        nejaky-kokain - kokain
        nejaky-alkohol - alkohol
    )

    (:init
        (nachazi-se namornik nejaky-pristav)

        ; --- CESTY ---
        (existuje-cesta nejaky-les nejaka-reka) (existuje-cesta nejaka-reka nejaky-les)
        (existuje-cesta nejaky-pristav nejaka-reka) (existuje-cesta nejaka-reka nejaky-pristav)
        (existuje-cesta nejaky-pristav nejaka-hospoda) (existuje-cesta nejaka-hospoda nejaky-pristav)
        (existuje-cesta nejaky-pristav nejake-mesto) (existuje-cesta nejake-mesto nejaky-pristav)
        (existuje-cesta nejake-mesto nejaka-akademie) (existuje-cesta nejaka-akademie nejake-mesto)

        ; --- CESTY MOREM ---
        (existuje-cesta-morem nejaky-pristav nejake-more) (existuje-cesta-morem nejake-more nejaky-pristav)
        (existuje-cesta-morem nejake-more nejaky-ostrov) (existuje-cesta-morem nejaky-ostrov nejake-more)
        (existuje-cesta-morem nejake-more nejaky-majak) (existuje-cesta-morem nejaky-majak nejake-more)
        (existuje-cesta-morem nejaky-pristav nejaky-majak) (existuje-cesta-morem nejaky-majak nejaky-pristav)

        ; --- LES ---
        (nachazi-se nejaka-kvetina nejaky-les)
        (nachazi-se nejake-drevo nejaky-les)
        (nachazi-se nejaky-medved nejaky-les)
        (nachazi-se kouzelny-dedecek nejaky-les)
        (vlastni kouzelny-dedecek nejaka-mapa)

        ; --- REKA ---
        (nachazi-se nejaka-voda nejaka-reka)
        (nachazi-se nejake-zlate-zrnko nejaka-reka)

        ; --- PRISTAV ---
        (nachazi-se nejake-zlate-zrnko nejaky-pristav)

        ; --- HOSPODA ---

        ; --- MESTO ---

        ; --- AKADEMIE ---

        ; --- MORE ---
        (nachazi-se nejaka-voda nejake-more)
        (nachazi-se nejaka-perla nejake-more)

        ; --- MAJAK ---
        (nachazi-se divka nejaky-majak)

        ; --- OSTROV ---
        (nachazi-se nejake-drevo nejaky-ostrov)
        (nachazi-se nejake-kokosy nejaky-ostrov)
    )

    (:goal (and
            (je-stastny1 namornik)
            (je-stastny2 namornik)
            (je-stastny3 namornik)

            ; je-stastny1 NEBO je-stastny2 NEBO je-stastny3 (nejrychlejsi reseni)
            ; (je-stastny namornik)
        )
    )
)
