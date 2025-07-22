# maps/EOTN/_5_sifhalla_to_olafstead.py

from Py4GWCoreLib.enums import outpost_name_to_id, explorable_name_to_id

# 1) IDs
_5_sifhalla_to_olafstead_ids = {
    "outpost_id": outpost_name_to_id["Sifhalla"],  # 643
}

# 2) Exit path from Sifhalla (map 643)
_5_sifhalla_to_olafstead_outpost_path = [
    (13510.718750, 19647.238281),
    (13596.396484, 19212.427734),  # into Drakkar Lake
]

# 3) Explorable segments
_5_sifhalla_to_olafstead_segments = [
    {
        # Drakkar Lake (ID 513)
        "map_id": explorable_name_to_id["Drakkar Lake"],
        "path": [
            (13946.335937, 14286.607421),
            (13599.999023,  6967.771484),
            (13396.375000,  4099.683105),
            (10782.618164,  3919.063720),
            ( 5936.016113,  3485.744873),
            ( 3749.377929,  3285.844482),
            (  -12.388924,  -244.892211),
            ( -2623.909912, -3307.028076),
            ( -5624.512207, -4308.001953),
            ( -7885.518554, -9186.645507),
            ( -9944.139648,-13188.315429),
            (-10946.782226,-16388.703125),
            (-11847.703125,-19820.244140),
            (-11442.958984,-22719.455078),
            (-11040.512695,-25654.402343),
            (-11019.546875,-26164.341796),  # portal to Varajar Fells
        ],
    },
    {
        # Varajar Fells (ID 553)
        "map_id": explorable_name_to_id["Varajar Fells"],
        "path": [
            ( -1605.245239, 12837.257812),
            ( -2047.884399,  8718.327148),
            ( -2288.647216,  4162.530273),
            ( -3639.192138,  1637.482666),
            ( -4178.047851, -2814.842773),
            ( -3368.485107, -4232.247070),
            ( -3315.862060, -1716.598754),
            ( -1648.331054,  1095.387329),
            ( -1196.614624,  1241.174560),  # portal to Olafstead
        ],
    },
    {
        # Olafstead (final outpost, ID 645)
        "map_id": outpost_name_to_id["Olafstead"],
        "path": [],  # end of run
    },
]
