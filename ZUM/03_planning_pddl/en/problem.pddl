(define (problem happinness-searching)
    (:domain zum-du3-magic-world)
    (:requirements :strips :typing)

    (:objects
        ; --- LOCATIONS ---
        some-academy - academy
        some-forest - forest
        some-town - town
        some-island - island
        some-harbour - harbour
        some-sea - sea
        some-bar - bar
        some-river - river
        some-lighthouse - lighthouse

        ; --- CREATURES ---
        sailor - human
        yound-lady - human
        magic-little-old-man - human
        some-bear - bear

        ; --- THINGS ---
        some-water - water
        some-wood - wood
        some-flower - flower
        some-ring - ring
        some-pearl - pearl
        some-cocoas - cocoa
        bears-skin - skin
        some-boat - boat
        some-frigate - frigate
        some-caravel - caravel
        some-gold - gold
        some-gold-coin - gold-coin
        some-gold-angot - gold-angot
        some-map - map
        some-cocaine - cocaine
        some-alcohol - alcohol
    )

    (:init
        (is-located sailor some-harbour)

        ; --- PATHS ---
        (path-exists some-forest some-river) (path-exists some-river some-forest)
        (path-exists some-harbour some-river) (path-exists some-river some-harbour)
        (path-exists some-harbour some-bar) (path-exists some-bar some-harbour)
        (path-exists some-harbour some-town) (path-exists some-town some-harbour)
        (path-exists some-town some-academy) (path-exists some-academy some-town)

        ; --- PATHS BY THE SEA ---
        (path-exists-only-by-the-sea some-harbour some-sea) (path-exists-only-by-the-sea some-sea some-harbour)
        (path-exists-only-by-the-sea some-sea some-island) (path-exists-only-by-the-sea some-island some-sea)
        (path-exists-only-by-the-sea some-sea some-lighthouse) (path-exists-only-by-the-sea some-lighthouse some-sea)
        (path-exists-only-by-the-sea some-harbour some-lighthouse) (path-exists-only-by-the-sea some-lighthouse some-harbour)

        ; --- FOREST ---
        (is-located some-flower some-forest)
        (is-located some-wood some-forest)
        (is-located some-bear some-forest)
        (is-located magic-little-old-man some-forest)
        (owns magic-little-old-man some-map)

        ; --- RIVER ---
        (is-located some-water some-river)
        (is-located some-gold some-river)

        ; --- HARBOUR ---
        (is-located some-gold some-harbour)

        ; --- BAR ---

        ; --- TOWN ---

        ; --- ACADEMY ---

        ; --- SEA ---
        (is-located some-water some-sea)
        (is-located some-pearl some-sea)

        ; --- LIGHTHOUSE ---
        (is-located yound-lady some-lighthouse)

        ; --- ISLAND ---
        (is-located some-wood some-island)
        (is-located some-cocoas some-island)
    )

    (:goal (and
            (is-happy1 sailor)
            (is-happy2 sailor)
            (is-happy3 sailor)

            ; is-happy1 OR is-happy2 OR is-happy3
            ;(is-happy sailor)
        )
    )
)
