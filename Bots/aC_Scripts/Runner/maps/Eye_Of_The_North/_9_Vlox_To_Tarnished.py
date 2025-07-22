# maps/EOTN/_9_vlox_to_tarnished.py

from Py4GWCoreLib.enums import explorable_name_to_id
from Py4GWCoreLib.enums import outpost_name_to_id

# 1) IDs
_9_vlox_to_tarnished_ids = {
    "outpost_id": outpost_name_to_id["Vlox's Falls"],  # 624
}

# 2) Exit‐outpost path from Vlox’s Falls (map 624)
_9_vlox_to_tarnished_outpost_path = [
    (16021.786132, 14000.079101),  # initial _Run
    (15519.092773, 12572.936523),  # into Arbor Bay
]

# 3) Explorable segments
_9_vlox_to_tarnished_segments = [
    {
        # Arbor Bay (ID 485)
        "map_id": explorable_name_to_id["Arbor Bay"],
        "path": [
            (13331.803710, 10848.732421),
            ( 9207.168945,  7158.782226),
            ( 5715.663574,  3649.900390),  # IAU point
            ( 2385.320800,  1828.722900),
            ( -719.137451, -1148.595825),
            (-3010.732421, -4905.047363),
            (-4796.903320, -6259.326171),
            (-7677.546386, -6762.379394),
            (-10550.049804,-7143.164062),
            (-12772.930664,-9579.868164),
            (-15232.251953,-12602.846679),
            (-17456.839843,-14899.894531),
            (-17390.365234,-18139.921875),
            (-19796.037109,-19468.126953),
        ],
    },
    {
        # Alcazia Tangle (ID 572)
        "map_id": explorable_name_to_id["Alcazia Tangle"],
        "path": [
            (-20455.207031, -19872.332031),  # into Alcazia Tangle
            (23025.226562, 13777.048828),
            (21148.154296, 14763.507812),
            (18471.025390, 13652.770507),  # IAU point
            (13929.705078, 11236.818359),
            (13920.853515,  8353.000976),
            (16721.199218,  8154.790039),
            (19755.736328,  8212.900390),
            (21026.087890,  7582.662109),
            (20336.568359,  3354.434082),
            (19155.373046,  -393.969360),
            (16801.886718, -3632.189941),
            (18186.484375,-7186.589843),
            (18793.058593,-10097.039062),
        ],
    },
    {
        # Tarnished Haven (final outpost, ID 641)
        "map_id": outpost_name_to_id["Tarnished Haven"],
        "path": [],  # arrival, no walking needed
    },
]
