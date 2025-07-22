import math
import traceback

import Py4GW  # type: ignore
from HeroAI.cache_data import CacheData
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Player

cached_data = CacheData()

# String consts
MODULE_NAME = "NFDialogSender"  # Change this Module name

# Full structured dialog GUI for Guild Wars: Nightfall quests
DIALOG_GROUPS = {
    "And a Hero Shall Lead Them": {
        "dialogs": [
            (0x822601, "Start (Lonai)"),
            (0x84, "Talk to Commander Suha"),
            (0x822607, "Accept Reward"),
        ],
        "note": "Only one of the Sunspear Evacuees must make it to the end (near Margrid the Sly) for the mission to finish.",
    },
    "The Council is Called": {
        "dialogs": [
            (0x81EA01, "Start (Dockmaster Ahlaro)"),
            (0x84, "Talk to first 2 NPCs"),
            (0x81EA04, "Update (Elder Suhl)"),
            (0x81EA07, "Accept Reward (Suhl)"),
        ],
        "note": "0x84 works for the first two NPCs. Use 0x81EA04 to update the quest, and 0x81EA07 for reward.",
    },
    "To Vabbi!": {
        "dialogs": [
            (0x822701, "Start (Elder Suhl)"),
            (0x822704, "Update (Dunkoro)"),
            (0x822704, "Update (Nerashi)"),
            (0x822707, "Accept Reward (Lonai)"),
        ],
        "note": "Kournans do not spawn until after speaking with Dunkoro.",
    },
    "Centaur Blackmail": {
        "dialogs": [
            (0x822801, "Start (Lonai)"),
            (0x85, "Update (Haroj Firemane)"),
            (0x822807, "Accept Reward (Estate Guard Rikesh)"),
        ],
        "note": "The Veldrunner Centaurs do not need to survive. They do not count for the bonus.",
    },
    "Mysterious Message": {"dialogs": [(0x822901, "Start (Lonai)"), (0x822907, "Accept Reward (Adept of Whispers)")]},
    "Secrets in the Shadow": {
        "dialogs": [
            (0x822A01, "Start (Master of Whispers)"),
            (0x822A04, "Update (Dehjah)"),
            (0x822A07, "Accept Reward (MoW)"),
        ]
    },
    "To Kill a Demon": {
        "dialogs": [
            (0x822B01, "Start (MoW)"),
            (0x85, "Skip Droughtlings (Dehjah)"),
            (0x822B07, "Accept Reward (Dehjah)"),
        ],
        "note": "Use 0x85 on Dehjah to skip killing droughtlings. This is the last quest before Moddok Crevice becomes a mission.",
    },
    "Moddok Crevice (Mission)": {
        "dialogs": [],
        "note": "Flag heroes at start. Use HoS/Vipers/EE to jump past allied Corsairs. Run to the end to trigger the cutscene. Knockdown/spell prevention helps at the Mangradors. Flag heroes under the bridge and kill both bosses.",
    },
    "Rally the Princes": {
        "dialogs": [
            (0x81F601, "Start (Kuwame)"),
            (0x85, "Skip Entire Quest (Priestess Haila)"),
            (0x81F607, "Accept Reward (Kazsha)"),
        ],
        "note": "Starting from Kodash, you can skip most of the quest with 0x85 to Haila.",
    },
    "Tihark Orchard": {
        "dialogs": [(0x84, "Talk to Each Prince (x3)")],
        "note": "Talk to each prince with 0x84, then finish with Prince Ahmtur.",
    },
    "All's Well That Ends Well": {
        "dialogs": [(0x81F701, "Start (Rendu)"), (0x81F707, "Accept Reward (Oluda)")],
        "note": "No need to talk to Kehanni.",
    },
    "Warning Kehanni": {"dialogs": [(0x81F801, "Start (Oluda)"), (0x81F807, "Accept Reward (Vahmani)")]},
    "Calling the Order": {
        "dialogs": [
            (0x81F901, "Start (Vahmani)"),
            (0x81F904, "Talk to Whispers Acolyte"),
            (0x85, "Talk to Prince Ahmtur the Mighty"),
            (0x81F907, "Accept Reward (Lieutenant Murunda)"),
        ],
        "note": "Spawns Prince Ahmtur outside Dzagonur Bastion.",
    },
    "Dzagonur Bastion (Mission)": {"dialogs": [], "note": "Send two NPC groups east and one west."},
    "Pledge of the Merchant Princes": {
        "dialogs": [
            (0x81FB01, "Start (Zerai the Learner)"),
            (0x81FB04, "Talk to Morgahn"),
            (0x85, "Enter Cutscene"),
            (0x81FB07, "Accept Reward (Vahmani)"),
        ]
    },
    "Attack at the Kodash": {
        "dialogs": [
            (0x82A801, "Start (Zerai)"),
            (0x82A804, "Talk to Butoh the Bold"),
            (0x82A804, "After killing Margonites"),
            (0x82A807, "Accept Reward (Zerai)"),
        ]
    },
    "Heart or Mind: Garden in Danger": {
        "dialogs": [],
        "note": "Map to Tihark Orchard and talk to the NPC in the Nightfallen Garden.",
    },
    "Jennur’s Horde (Mission)": {
        "dialogs": [],
        "note": "Grab the light, run past enemies. Use it to kill 3 Harbingers. Prevent snares.",
    },
    "Crossing the Desolation": {
        "dialogs": [
            (0x82AC01, "Start (Lonai)"),
            (0x82AC04, "Talk to Kormir"),
            (0x82AC04, "Talk to Mirza Veldrunner"),
            (0x82AC04, "Talk to Kormir again"),
            (0x85, "Talk to Dirah Traptail in Turai's"),
            (0x82AC07, "Accept Reward (Laph Longmane)"),
        ],
        "note": "Watch the dialog in Jahai Bluffs and interact with the monument.",
    },
    "Gate of Desolation (Mission)": {
        "dialogs": [],
        "note": "You can pay a runner to finish the mission in ~3 minutes if competent.",
    },
    "A Deal's a Deal": {
        "dialogs": [(0x824701, "Start (Sahlahjar the Dead)"), (0x824701, "Accept Reward (Ritual Priest Kehmut)")],
        "note": "Kill the Margonite group in Joko’s Domain.",
    },
    "Horde of Darkness": {
        "dialogs": [
            (0x824801, "Start (Priest Kehmut)"),
            (0x85, "Captain Mehhan"),
            (0x824807, "Accept Reward (Captain Mehhan)"),
        ],
        "note": "Use wurm, hug tendrils, wipe at gate to skip. Vampiric/lifesteal bow kills the pillar.",
    },
    "Ruins of Morah (Mission)": {"dialogs": [], "note": "Standard mission progression."},
    "Uncharted Territory": {
        "dialogs": [(0x82BD01, "Start (Pehai)"), (0x85, "Tortured Sunspear"), (0x82BD07, "Accept Reward (Jarindok)")],
        "note": "Dunkoro must be in the party.",
    },
    "Gate of Pain (Mission)": {"dialogs": [], "note": "Advance through standard Gate of Pain mission."},
    "Kormir's Crusade": {
        "dialogs": [
            (0x82BE01, "Start (Rahmor)"),
            (0x82BE01, "Talk to Kormir"),
            (0x82BE07, "Accept Reward (Keeper Halyssi)"),
        ],
        "note": "Run to the gate of secrets. Wait for Kormir.",
    },
    "All Alone in the Darkness": {
        "dialogs": [
            (0x82BF01, "Start (Keeper Halyssi)"),
            (0x82BF04, "Talk to Kormir"),
            (0x85, "Scout Ahtok"),
            (0x82BF07, "Accept Reward (Runic Oracle)"),
        ],
        "note": "Scout Ahtok is in danger; be quick.",
    },
}


def draw_widget():
    is_window_opened = PyImGui.begin("Nightfall Quest Dialogs", PyImGui.WindowFlags.AlwaysAutoResize)
    if is_window_opened:
        group_items = list(DIALOG_GROUPS.items())
        num_columns = 4
        num_rows = math.ceil(len(group_items) / num_columns)

        if PyImGui.begin_table("dialog_groups_table", num_columns):
            for row in range(num_rows):
                PyImGui.table_next_row()
                for col in range(num_columns):
                    index = row * num_columns + col
                    PyImGui.table_next_column()
                    if index >= len(group_items):
                        continue

                    group_name, group_data = group_items[index]
                    dialogs = group_data.get("dialogs", [])
                    note = group_data.get("note", "")

                    PyImGui.text(group_name)
                    PyImGui.separator()

                    for dialog_id, label in dialogs:
                        button_label = f"{label} [0x{dialog_id:X}]"
                        if PyImGui.button(button_label):
                            print(f'Sending dialog [0x{dialog_id:X}]')
                            Player.SendDialog(dialog_id)

                    if note:
                        PyImGui.spacing()
                        PyImGui.text_wrapped(f"Note: {note}")
                        PyImGui.spacing()
        PyImGui.end_table()
    PyImGui.end()


def configure():
    pass


def main():
    global cached_data
    try:
        if not Routines.Checks.Map.MapValid():
            return

        cached_data.Update()
        if cached_data.data.is_map_ready and cached_data.data.is_party_loaded:
            draw_widget()

    except ImportError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(MODULE_NAME, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(MODULE_NAME, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        # Catch-all for any other unexpected exceptions
        Py4GW.Console.Log(MODULE_NAME, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(MODULE_NAME, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass


if __name__ == "__main__":
    main()

# These functions need to be available at module level
__all__ = ['main', 'configure']
