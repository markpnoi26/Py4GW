# maps/EOTN/_8_vlox_to_gadds.py

from Py4GWCoreLib.enums import explorable_name_to_id
from Py4GWCoreLib.enums import outpost_name_to_id

# 1) Teleport ID
_8_vlox_to_gadds_ids = {
    "outpost_id": outpost_name_to_id["Vlox's Falls"],  # 624
}

# 2) Exit‐outpost path in Vlox’s Falls (map 624)
_8_vlox_to_gadds_outpost_path = [
    (15733.728515, 13162.657226),  # first _Run
    (15525.494140, 12616.365234),  # Move into Arbor Bay
]

# 3) Explorable segments
_8_vlox_to_gadds_segments = [
    {
        # Arbor Bay (map 485)
        "map_id": explorable_name_to_id["Arbor Bay"],
        "path": [
            (13957.639648, 10939.767578),
            (11597.432617,  6914.898925),
            (10650.434570,  1715.632202),
            (10843.333984, -1363.161132),
            ( 9930.636718, -4877.984375),
            ( 8712.629882, -8043.770019),
            ( 9576.622070, -13174.955078),
            (10057.143554, -17047.470703),
            ( 9605.093750, -19846.150390),
        ],
    },
    {
        # Shards of Orr (map 581)
        "map_id": explorable_name_to_id["Shards of Oor (level 1)"],
        "path": [
            (-12004.113281, 10065.341796),
            ( -7597.928710, 10046.100585),
            ( -4170.037597, 11332.016601),
            ( -1382.473144, 12572.248046),
            (  1604.056274, 15276.850585),  # IAU point
            (  1604.056274, 15276.850585),
            (  6105.577148, 14172.998046),
            ( 10786.185546, 13449.357421),
            ( 12490.760742, 15101.247070),
            ( 16182.513671, 15978.458007),
            ( 16282.338867, 11838.375000),
        ],
    },
    {
        # Gadds Encampment (map 638) — final arrival, no walking needed
        "map_id": outpost_name_to_id["Gadd's Encampment"],
        "path": [],
    },
]
