(define (domain zum-du3-magic-world)
    (:requirements :strips :typing)
    (:types
        ; --- META TYPES ---
        object
        location
        creature - object
        thing - object

        ; --- NORMAL TYPES ---
        human - creature
        bear - creature

        academy - location
        bar - location
        town - location
        sea - location
        harbour - location
        forest - location
        river - location
        island - location
        lighthouse - location

        water - thing
        wood - thing
        flower - thing
        ring - thing
        pearl - thing
        map - thing
        alcohol - thing
        cocaine - thing
        gold - thing
        gold-coin - thing
        gold-angot - thing

        goods - thing
        cocoa - goods
        skin - goods

        ship - thing
        boat - ship
        frigate - ship
        caravel - ship
    )

    (:predicates
        (path-exists ?location-1 - location ?location-2 - location)
        (path-exists-only-by-the-sea ?location-1 - location ?location-2 - location)

        (is-located ?object - objekt ?location - location)
        (owns ?human - human ?thing - thing)

        (has-a-criminal-record ?human - human)
        (has-good-connections ?human - human)
        (has-suspicious-connections ?human - human)
        (knows-contrabandists ?human - human)
        (has-defeated-pirates ?human - human)
        (amazed-young-lady ?human - human)
        (is-hardy ?human - human)
        (had-a-drink ?human - human)
        (is-drunk ?human - human)
        (has-alcohol-addiction ?human - human)
        (is-engaged ?human - human)
        (is-a-captain ?human - human)
        (is-happy1 ?human - human)
        (is-happy2 ?human - human)
        (is-happy3 ?human - human)

        (is-happy ?human - human)
    )

    ; MOVING AND SO ON ----------------------------------------------------------------------

    (:action went
        :parameters (?human - human ?location-1 - location ?location-2 - location)
        :precondition (and
            (is-located ?human ?location-1)
            (path-exists ?location-1 ?location-2)
        )
        :effect (and
            (is-located ?human ?location-2)
            (not (is-located ?human ?location-1))
        )
    )

    (:action sailed
        :parameters (?human - human ?ship - ship ?location-1 - location ?location-2 - location)
        :precondition (and
            (is-located ?human ?location-1)
            (path-exists-only-by-the-sea ?location-1 ?location-2)
            (owns ?human ?ship)
            (is-hardy ?human)
        )
        :effect (and
            (is-located ?human ?location-2)
            (not (is-located ?human ?location-1))
        )
    )

    (:action got
        :parameters (?human - human ?thing - thing ?location - location)
        :precondition (and
            (is-located ?human ?location)
            (is-located ?thing ?location)
        )
        :effect (and
            (owns ?human ?thing)
        )
    )

    ; MONEY ------------------------------------------------------------------------------------------

    (:action worked
        :parameters (?human - human ?gold - gold ?harbour - harbour)
        :precondition (and
            (is-located ?human ?harbour)
        )
        :effect (and
            (owns ?human ?gold)
        )
    )

    (:action panned-gold
        :parameters (?human - human ?gold - gold ?river - river)
        :precondition (and
            (is-located ?human ?river)
        )
        :effect (and
            (owns ?human ?gold)
        )
    )

    (:action sold
        :parameters (?human - human ?goods - goods ?harbour - harbour ?gold-coin - gold-coin)
        :precondition (and
            (is-located ?human ?harbour)
            (owns ?human ?goods)
        )
        :effect (and
            (not (owns ?human ?goods))
            (owns ?human ?gold-coin)
        )
    )

    (:action saved-money
        :parameters (?human - human ?gold - gold ?gold-coin - gold-coin ?town - town)
        :precondition (and
            (owns ?human ?gold)
            (is-located ?human ?town)
        )
        :effect (and
            (owns ?human ?gold-coin)
            (not (owns ?human ?gold))
            (has-good-connections ?human)
        )
    )

    (:action invested
        :parameters (?human - human ?gold-coin - gold-coin ?gold-angot - gold-angot ?town - town)
        :precondition (and
            (owns ?human ?gold-coin)
            (is-located ?human ?town)
        )
        :effect (and
            (owns ?human ?gold-angot)
            (not (owns ?human ?gold-coin))
            (has-good-connections ?human)
        )
    )

    (:action stole
        :parameters (?human - human ?gold-coin - gold-coin ?town - town)
        :precondition (and (is-located ?human ?town))
        :effect (and
            (owns ?human ?gold-coin)
            (has-a-criminal-record ?human)
        )
    )

    ; ALCOHOL -------------------------------------------------------------------------------

    (:action bought-alcohol
        :parameters (?human - human ?alcohol - alcohol ?gold - gold ?bar - bar)
        :precondition (and
            (is-located ?human ?bar)
            (owns ?human ?gold)
        )
        :effect (and
            (not (owns ?human ?gold))
            (owns ?human ?alcohol)
        )
    )

    (:action took-a-drink
        :parameters (?human - human ?alcohol - alcohol)
        :precondition (and (owns ?human ?alcohol))
        :effect (and
            (had-a-drink ?human)
            (not (owns ?human ?alcohol))
        )
    )

    (:action got-drunk
        :parameters (?human - human ?alcohol - alcohol)
        :precondition (and (owns ?human ?alcohol) (had-a-drink ?human))
        :effect (and
            (is-drunk ?human)
            (not (had-a-drink ?human))
            (not (owns ?human ?alcohol))
        )
    )

    (:action got-drunk-got-alcohol-addiction
        :parameters (?human - human ?alcohol - alcohol)
        :precondition (and
            (owns ?human ?alcohol)
            (is-drunk ?human)
        )
        :effect (and
            (has-alcohol-addiction ?human)
            (not (is-drunk ?human))
            (not (owns ?human ?alcohol))
        )
    )

    (:action took-a-bath-in-cold-water
        :parameters (?human - human ?location - location ?water - water)
        :precondition (and
            (is-located ?water ?location)
            (is-located ?human ?location)
        )
        :effect (and
            (not (had-a-drink ?human))
            (not (is-drunk ?human))
        )
    )

    ; BOATS ---------------------------------------------------------------------------------

    (:action stole-a-boat
        :parameters (?human - human ?boat - boat ?river - river)
        :precondition (and
            (is-located ?human ?river)
        )
        :effect (and
            (owns ?human ?boat)
            (has-a-criminal-record ?human)
        )
    )

    (:action built-a-ship
        :parameters (?human - human ?boat - boat ?wood - wood)
        :precondition (and (owns ?human ?wood))
        :effect (and
            (not (owns ?human ?wood))
            (owns ?human ?boat)
        )
    )

    (:action got-a-frigate
        :parameters (?human - human ?frigate - frigate ?boat - boat ?wood - wood ?gold - gold)
        :precondition (and
            (owns ?human ?boat)
            (owns ?human ?wood)
            (owns ?human ?gold)
        )
        :effect (and
            (not (owns ?human ?boat))
            (not (owns ?human ?wood))
            (not (owns ?human ?gold))
            (owns ?human ?frigate)
        )
    )

    (:action got-a-caravel
        :parameters (?human - human ?caravel - caravel ?boat - boat ?wood - wood ?gold-coin - gold-coin)
        :precondition (and
            (owns ?human ?boat)
            (owns ?human ?wood)
            (owns ?human ?gold-coin)
        )
        :effect (and
            (not (owns ?human ?boat))
            (not (owns ?human ?wood))
            (not (owns ?human ?gold-coin))
            (owns ?human ?caravel)
        )
    )

    ; SOME OTHER LOGIC -------------------------------------------------------------------------------

    (:action changed-alcohol-for-a-map
        :parameters (?human - human ?kouzelny-dedecek - human ?alcohol - alcohol ?map - map ?forest - forest)
        :precondition (and
            (is-located ?kouzelny-dedecek ?forest)
            (owns ?kouzelny-dedecek ?map)
            (is-located ?human ?forest)
            (owns ?human ?alcohol)
        )
        :effect (and
            (has-suspicious-connections ?human)
            (owns ?human ?map)
            (not (owns ?human ?alcohol))
        )
    )

    (:action emptied-a-cache
        :parameters (?human - human ?cocaine - cocaine ?map - map ?island - island)
        :precondition (and
            (is-located ?human ?island)
            (owns ?human ?map)
        )
        :effect (and
            (owns ?human ?cocaine)
            (not (owns ?human ?map))
        )
    )

    ; RELATIONS ---------------------------------------------------------------------------

    (:action got-to-know-contrabandists
        :parameters (?human - human ?gold-angot - gold-angot ?harbour - harbour)
        :precondition (and
            (has-suspicious-connections ?human)
            (is-located ?human ?harbour)
            (owns ?human ?gold-angot)
        )
        :effect (and
            (knows-contrabandists ?human)
        )
    )

    (:action was-attached-by-pirates
        :parameters (
            ?human - human
            ?sea - sea
            ?gold - gold
            ?gold-coin - gold-coin
            ?gold-angot - gold-angot
            ?frigate - frigate
            ?caravel - caravel
        )
        :precondition (and
            (is-located ?human ?sea)
            (not (is-hardy ?human))
        )
        :effect (and
            (is-hardy ?human)
            (not (owns ?human ?gold))
            (not (owns ?human ?gold-coin))
            (not (owns ?human ?gold-angot))
            (not (owns ?human ?frigate))
            (not (owns ?human ?caravel))
        )
    )

    (:action joined-pirates
        :parameters (?human - human ?sea - sea)
        :precondition (and
            (is-located ?human ?sea)
            (has-suspicious-connections ?human)
        )
        :effect (and (had-a-drink ?human))
    )

    (:action bought-alcohol-for-everyone-in-the-bar
        :parameters (?human - human ?gold-coin - gold-coin ?bar - bar ?alcohol - alcohol)
        :precondition (and
            (is-located ?human ?bar)
            (owns ?human ?gold-coin)
        )
        :effect (and
            (owns ?human ?alcohol)
            (has-good-connections ?human)
            (not (owns ?human ?gold-coin))
        )
    )

    (:action bought-and-indulgence
        :parameters (?human - human ?town - town ?gold - gold)
        :precondition (and
            (is-located ?human ?town)
            (has-a-criminal-record ?human)
            (owns ?human ?gold)
        )
        :effect (and
            (not (has-a-criminal-record ?human))
            (not (owns ?human ?gold))
        )
    )

    (:action did-public-works
        :parameters (?human - human ?town - town)
        :precondition (and
            (is-located ?human ?town)
            (has-a-criminal-record ?human)
        )
        :effect (and
            (not (has-a-criminal-record ?human))
            (had-a-drink ?human)
        )
    )

    (:action studied-in-the-academy-became-captain
        :parameters (?human - human ?gold-coin - gold-coin ?academy - academy)
        :precondition (and
            (owns ?human ?gold-coin)
            (is-located ?human ?academy)
        )
        :effect (and
            (not (owns ?human ?gold-coin))
            (is-a-captain ?human)
            (amazed-young-lady ?human)
        )
    )

    ; WAYS TO AMAZE ETC -----------------------------------------------------------------------

    (:action had-fight-with-a-bear
        :parameters (?human - human ?bear - bear ?forest - forest ?skin - skin)
        :precondition (and
            (is-located ?human ?forest)
            (is-located ?bear ?forest)
        )
        :effect (and
            (owns ?human ?skin)
            (is-hardy ?human)
            (amazed-young-lady ?human)
        )
    )

    (:action got-hardy-in-the-bar-fight
        :parameters (?human - human ?bar - bar)
        :precondition (and
            (is-located ?human ?bar)
            (had-a-drink ?human)
        )
        :effect (and
            (is-hardy ?human)
        )
    )

    (:action defeated-pirates
        :parameters (
            ?human - human
            ?sea - sea
            ?caravel - caravel
            ?boat - boat
            ?frigate - frigate
            ?gold - gold
            ?gold-coin - gold-coin
            ?gold-angot - gold-angot
        )
        :precondition (and
            (is-hardy ?human)
            (owns ?human ?caravel)
            (is-located ?human ?sea)
        )
        :effect (and
            (has-defeated-pirates ?human)
            (amazed-young-lady ?human)
            (owns ?human ?boat)
            (owns ?human ?frigate)
            (owns ?human ?gold)
            (owns ?human ?gold-coin)
            (owns ?human ?gold-angot)
        )
    )

    (:action found-ring
        :parameters (?human - human ?ring - ring ?gold-angot - gold-angot ?pearl - pearl)
        :precondition (and
            (owns ?human ?gold-angot)
            (owns ?human ?pearl)
        )
        :effect (and
            (owns ?human ?ring)
            (not (owns ?human ?gold-angot))
            (not (owns ?human ?pearl))
        )
    )

    (:action gave-young-lady-ring-flower
        :parameters (?human - human ?young-lady - human ?flower - flower ?ring - ring ?lighthouse - lighthouse)
        :precondition (and
            (amazed-young-lady ?human)
            (owns ?human ?flower)
            (owns ?human ?ring)
            (is-located ?human ?lighthouse)
        )
        :effect (and
            (is-engaged ?human)
        )
    )

    ; -------------------------------------------
    ;               FINAL
    ; -------------------------------------------

    (:action got-married
        :parameters (?human - human ?flower - flower ?ring - ring ?island - island)
        :precondition (and
            (is-engaged ?human)
            (has-good-connections ?human)
            (not (has-a-criminal-record ?human))
            (not (is-drunk ?human))
            (not (has-alcohol-addiction ?human))
            (is-located ?human ?island)
        )
        :effect (and
            (is-happy1 ?human)
            (is-happy ?human)
        )
    )

    (:action became-an-admiral
        :parameters (?human - human ?academy - academy)
        :precondition (and
            (is-a-captain ?human)
            (has-defeated-pirates ?human)
            (is-located ?human ?academy)
            (not (had-a-drink ?human))
            (not (is-drunk ?human))
            (not (has-alcohol-addiction ?human))
        )
        :effect (and
            (is-happy2 ?human)
            (is-happy ?human)
        )
    )

    (:action got-down-to-cocaine
        :parameters (?human - human ?cocaine - cocaine ?gold-angot - gold-angot ?frigate - frigate)
        :precondition (and
            (owns ?human ?cocaine)
            (knows-contrabandists ?human)
            (owns ?human ?gold-angot)
            (owns ?human ?frigate)
            (has-alcohol-addiction ?human)
        )
        :effect (and
            (is-happy3 ?human)
            (is-happy ?human)
        )
    )
)
