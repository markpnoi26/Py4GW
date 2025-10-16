import json
import os
import re
import shutil
import traceback
from collections import OrderedDict
from pathlib import Path

import Py4GW  # type: ignore
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Color
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import ImGui
from Py4GWCoreLib import IniHandler
from Py4GWCoreLib import PyImGui
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ThrottledTimer
from Py4GWCoreLib import Timer
from Py4GWCoreLib import get_texture_for_model
from Py4GWCoreLib.enums import Bags
from Py4GWCoreLib.enums import ModelID


script_directory = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_directory, os.pardir))

first_run = True

BASE_DIR = os.path.join(project_root, "Widgets/Config")
DB_BASE_DIR = os.path.join(project_root, "Widgets/Data")
JSON_INVENTORY_PATH = os.path.join(DB_BASE_DIR, "Inventory")
INI_WIDGET_WINDOW_PATH = os.path.join(BASE_DIR, "TeamInventoryViewer.ini")
os.makedirs(BASE_DIR, exist_ok=True)

# ——— Window Persistence Setup ———
ini_window = IniHandler(INI_WIDGET_WINDOW_PATH)
save_window_timer = Timer()
save_window_timer.Start()

# String consts
MODULE_NAME = "TeamInventoryViewer"  # Change this Module name
COLLAPSED = "collapsed"
X_POS = "x"
Y_POS = "y"

# load last‐saved window state (fallback to 100,100 / un-collapsed)
window_x = ini_window.read_int(MODULE_NAME, X_POS, 100)
window_y = ini_window.read_int(MODULE_NAME, Y_POS, 100)
window_collapsed = ini_window.read_bool(MODULE_NAME, COLLAPSED, False)


inventory_poller_timer = ThrottledTimer(3000)
on_first_load = True
all_accounts_search_query = ''
search_query = ''
current_character_name = ''
last_seen_name = ''
recorded_data = OrderedDict()

INVENTORY_BAGS = {
    "Backpack": Bags.Backpack.value,
    "BeltPouch": Bags.BeltPouch.value,
    "Bag1": Bags.Bag1.value,
    "Bag2": Bags.Bag2.value,
    "EquipmentPack": Bags.EquipmentPack.value,
    "Equipped": Bags.EquippedItems.value,
}

STORAGE_BAGS = {
    "Storage1": Bags.Storage1.value,
    "Storage2": Bags.Storage2.value,
    "Storage3": Bags.Storage3.value,
    "Storage4": Bags.Storage4.value,
    "Storage5": Bags.Storage5.value,
    "Storage6": Bags.Storage6.value,
    "Storage7": Bags.Storage7.value,
    "Storage8": Bags.Storage8.value,
    "Storage9": Bags.Storage9.value,
    "Storage10": Bags.Storage10.value,
    "Storage11": Bags.Storage11.value,
    "Storage12": Bags.Storage12.value,
    "Storage13": Bags.Storage13.value,
    "Storage14": Bags.Storage14.value,
    "MaterialStorage": Bags.MaterialStorage.value,
}


class AccountJSONStore:
    def __init__(self, email):
        self.email = email
        self.path = Path(JSON_INVENTORY_PATH)
        self.path.mkdir(parents=True, exist_ok=True)  # ensure directory exists
        self.file_path = self.path / f"{self.email}.json"
        self.backup_path = self.file_path.with_suffix(".json.bak")

    def _read(self):
        if not self.file_path.exists():
            return {"Characters": OrderedDict(), "Storage": OrderedDict()}
        try:
            with open(self.file_path, "r") as f:
                return json.load(f, object_pairs_hook=OrderedDict)
        except json.JSONDecodeError:
            if self.backup_path.exists():
                try:
                    with open(self.backup_path, "r") as f:
                        return json.load(f, object_pairs_hook=OrderedDict)
                except Exception:
                    pass
            return {"Characters": OrderedDict(), "Storage": OrderedDict()}

    def _write_nonblocking(self, data):
        """Generator that writes JSON safely without blocking the main coroutine."""
        temp_file = self.file_path.with_suffix(".tmp")
        backup_file = self.backup_path

        # 1️⃣ Write temp file fully
        try:
            with open(temp_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            ConsoleLog("AccountJSONStore", f"[ERROR] Could not write temp file: {e}")
            yield  # allow coroutine to continue
            return

        # 2️⃣ Yield control, temp file now exists
        yield

        # 3️⃣ Backup current file if it exists
        if self.file_path.exists():
            try:
                shutil.copy2(self.file_path, backup_file)
            except Exception as e:
                ConsoleLog("AccountJSONStore", f"[WARN] Could not create backup: {e}")
        yield

        # 4️⃣ Atomic replace of original file
        if temp_file.exists():
            try:
                # On Windows, shutil.move works reliably for overwriting existing files
                shutil.move(str(temp_file), str(self.file_path))
            except Exception as e:
                ConsoleLog("AccountJSONStore", f"[WARN] Could not replace file: {e}")
        else:
            ConsoleLog("AccountJSONStore", "[WARN] Temp file missing, skipping replace")
        yield

    # --- Public API ---
    def load(self):
        return self._read()

    def save_bag(self, char_name=None, storage_name=None, bag_name=None, bag_items={}):
        data = self._read()
        changed = False

        if char_name:
            chars = data["Characters"]
            if char_name not in chars:
                chars[char_name] = {"Inventory": OrderedDict()}
            inv = chars[char_name]["Inventory"]
            if inv.get(bag_name) != bag_items:
                inv[bag_name] = bag_items
                changed = True
        elif storage_name:
            storage = data["Storage"]
            if storage.get(storage_name) != bag_items:
                storage[storage_name] = bag_items
                changed = True

        if changed:
            return self._write_nonblocking(data)

        # if nothing changed, return an empty generator
        def dummy_gen():
            yield

        return dummy_gen()

    # --- Other API remains unchanged ---
    def clear_character(self, char_name):
        data = self._read()
        chars = data.get("Characters", {})
        if char_name in chars:
            del chars[char_name]
            return self._write_nonblocking(data)

        def dummy_gen():
            yield

        return dummy_gen()

    def clear_storage(self, storage_name):
        data = self._read()
        storage = data.get("Storage", {})
        if storage_name in storage:
            del storage[storage_name]
            return self._write_nonblocking(data)

        def dummy_gen():
            yield

        return dummy_gen()

    def clear_account(self):
        if self.file_path.exists():
            self.file_path.unlink()
        if self.backup_path.exists():
            self.backup_path.unlink()

        def dummy_gen():
            yield

        return dummy_gen()


class MultiAccountInventoryStore:
    def __init__(self):
        self.inventory_dir = Path(JSON_INVENTORY_PATH)
        self.inventory_dir.mkdir(exist_ok=True)

    def account_store(self, email):
        return AccountJSONStore(email)

    def load_all(self):
        """Load all account JSON files and merge into a dict"""
        merged = OrderedDict()
        for file_path in self.inventory_dir.glob("*.json"):
            if file_path.suffix != ".json":
                continue
            email = file_path.stem
            store = AccountJSONStore(email)
            account_data = store.load()
            merged[email] = account_data
        return merged

    def clear_all_data(self):
        """Remove all account JSON files and their backups"""
        for file_path in self.inventory_dir.glob("*.json"):
            backup_path = file_path.with_suffix(".json.bak")
            try:
                if file_path.exists():
                    file_path.unlink()
                if backup_path.exists():
                    backup_path.unlink()
            except Exception as e:
                ConsoleLog("MultiAccountInventoryStore", f"[WARN] Failed to delete {file_path}: {e}")


multi_store = MultiAccountInventoryStore()


def get_character_name():
    agent_id = GLOBAL_CACHE.Player.GetAgentID()
    GLOBAL_CACHE.Agent.RequestName(agent_id)

    # Wait until all names are ready (with timeout safeguard)
    timeout = 2.0  # seconds
    poll_interval = 0.1
    elapsed = 0.0

    while elapsed < timeout:
        if GLOBAL_CACHE.Agent.IsNameReady(agent_id):
            break

        yield from Routines.Yield.wait(int(poll_interval) * 1000)
        elapsed += poll_interval

    name = ''
    # Populate agent_names dictionary
    if GLOBAL_CACHE.Agent.IsNameReady(agent_id):
        name = GLOBAL_CACHE.Agent.GetName(agent_id)
    return name


def get_character_bag_items_coroutine(bag, email, char_name, bag_name):
    store = AccountJSONStore(email)
    """Updates recorded_data[email]["Characters"][char_name]["Inventory"][bag_name]"""

    if not email or not char_name:
        return

    bag_items = yield from _collect_bag_items(bag)
    yield from store.save_bag(char_name=char_name, bag_name=bag_name, bag_items=bag_items)


def get_storage_bag_items_coroutine(bag, email, storage_name):
    store = AccountJSONStore(email)
    """Updates recorded_data[email]["Storage"][bag_name]"""

    if not email:
        return

    bag_items = yield from _collect_bag_items(bag)
    yield from store.save_bag(storage_name=storage_name, bag_items=bag_items)


def _collect_bag_items(bag):
    """Shared coroutine to fetch all items from a bag."""
    bag_items = OrderedDict()

    for item in bag.GetItems():
        if not item or item.model_id == 0:
            continue

        model_id = item.model_id
        name = None

        # Try to get name from your IntEnum first
        try:
            name = ModelID(model_id).name  # Enum member name
            INSCRIPTIONS = {
                ModelID.Inscriptions_All,
                ModelID.Inscriptions_Focus_Items,
                ModelID.Inscriptions_Focus_Shield,
                ModelID.Inscriptions_General,
                ModelID.Inscriptions_Martial,
                ModelID.Inscriptions_Spellcasting,
            }

            name = name.replace("_", " ")

            if model_id in INSCRIPTIONS:
                name = None
            if model_id == ModelID.Vial_Of_Dye:
                name = None
        except ValueError:
            name = None  # Not in enum

        # Only request in-game name if enum doesn't have it
        if not name:
            if not GLOBAL_CACHE.Item.IsNameReady(item.item_id):
                GLOBAL_CACHE.Item.RequestName(item.item_id)
                timeout = 1.5
                poll_interval = 0.05
                elapsed = 0
                while not GLOBAL_CACHE.Item.IsNameReady(item.item_id) and elapsed < timeout:
                    yield from Routines.Yield.wait(int(poll_interval * 1000))
                    elapsed += poll_interval

            name = GLOBAL_CACHE.Item.GetName(item.item_id)

        if not name:
            continue

        model_id = item.model_id
        quantity = item.quantity

        if name not in bag_items:
            bag_items[name] = {"model_id": model_id, "count": quantity}
        else:
            bag_items[name]["count"] += quantity

    return bag_items


def record_data():
    global current_character_name

    current_email = GLOBAL_CACHE.Player.GetAccountEmail()
    login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(GLOBAL_CACHE.Player.GetAgentID())
    char_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)

    if not current_email or not char_name:
        yield
        return

    current_character_name = char_name
    raw_item_cache = GLOBAL_CACHE.Inventory._raw_item_cache

    for bag_name, bag_id in INVENTORY_BAGS.items():
        bag = raw_item_cache.get_bags([bag_id])[0]
        yield from (
            get_character_bag_items_coroutine(
                bag,
                current_email,
                char_name=char_name,
                bag_name=bag_name,
            )
        )

    for storage_name, bag_id in STORAGE_BAGS.items():
        if bag_id is None:
            continue
        bag = raw_item_cache.get_bags([bag_id])[0]
        yield from (
            get_storage_bag_items_coroutine(
                bag,
                current_email,
                storage_name=storage_name,
            )
        )


def search(query: str, items: list[str]) -> list[str]:
    """Return items matching partially or with fuzzy similarity."""
    if not query:
        return items

    query = query.lower()

    # --- Partial match first (fast) ---
    partial_matches = [item for item in items if query in item.lower()]

    return sorted(partial_matches)


def aggregate_items_by_model(items_dict):
    """
    Given a dict of items (item_name -> {"model_id", "count"}), return
    a dict of model_id -> {"name": first_item_name, "count": total_count}.
    """
    agg = OrderedDict()
    for name, info in items_dict.items():
        model_id = info["model_id"]
        count = info["count"]

        if model_id not in agg:
            agg[model_id] = {"name": name, "count": count}
        else:
            agg[model_id]["count"] += count
    return agg


# Pass in whatever your widget needs as argument
def draw_widget():
    global window_x
    global window_y
    global window_collapsed
    global first_run
    global all_accounts_search_query
    global search_query
    global on_first_load
    global recorded_data
    global current_character_name
    global multi_store

    if first_run:
        PyImGui.set_next_window_pos(window_x, window_y)
        PyImGui.set_next_window_collapsed(window_collapsed, 0)
        first_run = False

    new_collapsed = PyImGui.is_window_collapsed()
    end_pos = PyImGui.get_window_pos()

    if on_first_load:
        on_first_load = False

        # Load all accounts for search
        recorded_data = multi_store.load_all()

    # === AUTO-POLL (Refresh inventory snapshot) ===
    if inventory_poller_timer.IsExpired():
        GLOBAL_CACHE.Coroutines.append(record_data())
        # Reload memory view
        recorded_data = multi_store.load_all()
        inventory_poller_timer.Reset()

    PyImGui.set_next_window_size(1000, 1000)
    if PyImGui.begin("Team Inventory Viewer"):
        PyImGui.text("Inventory + Storage Viewer")
        PyImGui.separator()

        # === SCROLLABLE AREA START ===
        # Compute space for footer
        available_height = PyImGui.get_window_height() - 190  # leave room for buttons + footer
        PyImGui.begin_child("ScrollableContent", (0.0, float(available_height)), True, 1)

        # === TABS BY ACCOUNT ===
        if recorded_data:
            if PyImGui.begin_tab_bar("AccountTabs"):
                # === GLOBAL SEARCH TAB ===
                if PyImGui.begin_tab_item("Search View"):
                    PyImGui.text("Search for items across all accounts")
                    PyImGui.separator()

                    all_accounts_search_query = PyImGui.input_text("##GlobalSearchBar", all_accounts_search_query, 128)
                    PyImGui.separator()

                    if all_accounts_search_query:
                        # === Gather all matching results across accounts ===
                        search_results = []
                        for email, account_data in recorded_data.items():
                            # Build a neat identifier like: email — [Char1, Char2]
                            character_names = list(account_data.get("Characters", {}).keys())
                            if character_names:
                                character_block = "\n".join(f"   - {name}" for name in character_names)
                                account_label = f"{character_block}"
                            else:
                                account_label = "[No Characters]"

                            # --- Characters ---
                            if "Characters" in account_data:
                                for char_name, char_info in account_data["Characters"].items():
                                    inv_data = char_info.get("Inventory", {})
                                    for bag_name, items in inv_data.items():
                                        for item_name, info in items.items():
                                            if all_accounts_search_query.lower() in item_name.lower():
                                                search_results.append(
                                                    {
                                                        "account_label": account_label,
                                                        "email": email,
                                                        "character": char_name,
                                                        "bag": bag_name,
                                                        "item_name": item_name,
                                                        "model_id": info["model_id"],
                                                        "count": info["count"],
                                                        "location_type": "Character",
                                                    }
                                                )

                            # --- Storage ---
                            if "Storage" in account_data:
                                for storage_name, items in account_data["Storage"].items():
                                    for item_name, info in items.items():
                                        if all_accounts_search_query.lower() in item_name.lower():
                                            search_results.append(
                                                {
                                                    "account_label": account_label,
                                                    "email": email,
                                                    "character": None,
                                                    "bag": storage_name,
                                                    "item_name": item_name,
                                                    "model_id": info["model_id"],
                                                    "count": info["count"],
                                                    "location_type": "Storage",
                                                }
                                            )

                        # === Display results ===
                        if search_results:
                            # Sort alphabetically ignoring leading numbers
                            search_results.sort(key=lambda entry: re.sub(r'^\d+\s*', '', entry["item_name"]).lower())
                            if PyImGui.begin_table(
                                "SearchResultsTable",
                                5,
                                PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg | PyImGui.TableFlags.ScrollY,
                            ):
                                PyImGui.table_setup_column("Icon", 0, 30.0)
                                PyImGui.table_setup_column("Item Name", 0, 300.0)
                                PyImGui.table_setup_column("Count", 0, 50.0)
                                PyImGui.table_setup_column("Location", 0, 150.0)
                                PyImGui.table_setup_column("Account", 0, 150.0)
                                PyImGui.table_headers_row()

                                for index, entry in enumerate(search_results):
                                    texture = get_texture_for_model(entry["model_id"])
                                    PyImGui.table_next_row()

                                    # === ICON ===
                                    PyImGui.table_next_column()
                                    if texture:
                                        ImGui.DrawTexture(texture, 20, 20)
                                    else:
                                        PyImGui.text("N/A")

                                    # === ITEM NAME ===
                                    PyImGui.table_next_column()
                                    PyImGui.text(re.sub(r'^\d+\s*', '', entry["item_name"]))

                                    # === COUNT ===
                                    PyImGui.table_next_column()
                                    PyImGui.text(str(entry["count"]))

                                    # === LOCATION ===
                                    PyImGui.table_next_column()
                                    if entry["location_type"] == "Character":
                                        PyImGui.text(f"{entry['character']}\n  - {entry['bag']}")
                                    else:
                                        PyImGui.text(f"Storage\n  - {entry['bag']}")

                                    # === ACCOUNT IDENTIFIER ===
                                    PyImGui.table_next_column()
                                    if PyImGui.collapsing_header(f'{entry["email"]}##{index}'):
                                        PyImGui.text(entry["account_label"])

                                PyImGui.end_table()
                        else:
                            PyImGui.text("No matching items found.")
                    else:
                        PyImGui.text("Type above to search across all accounts.")
                    PyImGui.end_tab_item()
                for email, account_data in recorded_data.items():
                    if PyImGui.begin_tab_item(email):
                        PyImGui.text(f"Account: {email}")
                        PyImGui.separator()

                        # === SEARCH BAR ===
                        PyImGui.text("Search Items:")
                        search_query = PyImGui.input_text("##SearchBar", search_query, 128)
                        PyImGui.separator()

                        PyImGui.begin_child(f"Child_{email}")

                        # === CHARACTER INVENTORIES ===
                        if "Characters" in account_data:
                            for char_name, char_info in account_data["Characters"].items():
                                if char_name == "Invalid ID":
                                    continue

                                if PyImGui.collapsing_header(char_name, True):
                                    inv_data = char_info.get("Inventory", {})
                                    ordered_inv_data = {
                                        bag_name: inv_data.get(bag_name, [])
                                        for bag_name in INVENTORY_BAGS.keys()
                                        if bag_name in inv_data
                                    }
                                    for bag_name, items in ordered_inv_data.items():
                                        if not items:
                                            continue

                                        # Filter visible items
                                        item_names = list(items.keys())
                                        filtered_items = item_names
                                        if search_query:
                                            filtered_items = search(search_query, item_names)
                                        if not filtered_items:
                                            continue

                                        PyImGui.text(bag_name)
                                        if PyImGui.begin_table(
                                            f"InvTable_{email}_{char_name}_{bag_name}",
                                            3,
                                            PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg,
                                        ):
                                            PyImGui.table_setup_column("Icon", 0, 30.0)
                                            PyImGui.table_setup_column("Item Name", 0, 300.0)
                                            PyImGui.table_setup_column("Count", 0, 25.0)
                                            PyImGui.table_headers_row()

                                            for item_name in filtered_items:
                                                info = items[item_name]
                                                texture = get_texture_for_model(info["model_id"])

                                                PyImGui.table_next_row()

                                                # === ICON COLUMN ===
                                                PyImGui.table_next_column()
                                                if texture:
                                                    ImGui.DrawTexture(texture, 20, 20)
                                                else:
                                                    PyImGui.text("N/A")

                                                # === ITEM NAME COLUMN ===
                                                PyImGui.table_next_column()
                                                PyImGui.text(re.sub(r'^\d+\s*', '', item_name))

                                                # === COUNT COLUMN ===
                                                PyImGui.table_next_column()
                                                PyImGui.text(str(info["count"]))
                                            PyImGui.end_table()
                                        PyImGui.separator()

                        # === STORAGE SECTION ===
                        if "Storage" in account_data:
                            if PyImGui.collapsing_header("Shared Storage", True):
                                account_storage = account_data.get("Storage", {})
                                ordered_storage_data = {
                                    storage_name: account_storage.get(storage_name, [])
                                    for storage_name in STORAGE_BAGS.keys()
                                    if storage_name in account_storage
                                }
                                for storage_name, items in ordered_storage_data.items():
                                    if not items:
                                        continue

                                    item_names = list(items.keys())
                                    filtered_items = item_names
                                    if search_query:
                                        filtered_items = search(search_query, item_names)
                                    if not filtered_items:
                                        continue

                                    PyImGui.text(storage_name)
                                    if PyImGui.begin_table(
                                        f"StorageTable_{email}_{storage_name}",
                                        3,
                                        PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg,
                                    ):
                                        PyImGui.table_setup_column("Icon", 0, 30.0)
                                        PyImGui.table_setup_column("Item Name", 0, 300.0)
                                        PyImGui.table_setup_column("Count", 0, 25.0)
                                        PyImGui.table_headers_row()

                                        for item_name in filtered_items:
                                            info = items[item_name]
                                            texture = get_texture_for_model(info["model_id"])

                                            PyImGui.table_next_row()

                                            # === ICON COLUMN ===
                                            PyImGui.table_next_column()
                                            if texture:
                                                ImGui.DrawTexture(texture, 20, 20)
                                            else:
                                                PyImGui.text("N/A")

                                            # === ITEM NAME COLUMN ===
                                            PyImGui.table_next_column()
                                            PyImGui.text(re.sub(r'^\d+\s*', '', item_name))

                                            # === COUNT COLUMN ===
                                            PyImGui.table_next_column()
                                            PyImGui.text(str(info["count"]))
                                        PyImGui.end_table()
                                    PyImGui.separator()

                        PyImGui.end_child()
                        PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
        else:
            PyImGui.text("No recorded accounts found yet.")
        PyImGui.end_child()  # End scrollable section

        PyImGui.separator()
        current_character = f'Current Character: {current_character_name}'
        PyImGui.text(f"{"Waiting for ..." if not current_character_name else current_character}")
        if PyImGui.collapsing_header("Advanced Clearing", True):
            PyImGui.text(f'Polling in: {int(inventory_poller_timer.GetTimeRemaining() // 1000)}(s)')
            if PyImGui.begin_table("clear_buttons_table", 3, PyImGui.TableFlags.BordersInnerV):
                # Define colors
                orange_color = Color(255, 165, 0, 255).to_tuple_normalized()  # orange
                orange_hover = Color(255, 200, 50, 255).to_tuple_normalized()
                orange_active = Color(255, 140, 0, 255).to_tuple_normalized()

                red_color = Color(220, 20, 60, 255).to_tuple_normalized()  # crimson red
                red_hover = Color(255, 50, 80, 255).to_tuple_normalized()
                red_active = Color(180, 0, 40, 255).to_tuple_normalized()

                green_color = Color(50, 205, 50, 255).to_tuple_normalized()  # lime green
                green_hover = Color(80, 230, 80, 255).to_tuple_normalized()
                green_active = Color(0, 180, 0, 255).to_tuple_normalized()

                PyImGui.table_next_row()
                # === CLEAR CHARACTER ===
                PyImGui.table_set_column_index(0)
                col_width = PyImGui.get_content_region_avail()[0]
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, green_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, green_hover)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, green_active)
                if PyImGui.button("Clear Character", width=col_width):
                    current_email = GLOBAL_CACHE.Player.GetAccountEmail()
                    login_number = GLOBAL_CACHE.Party.Players.GetLoginNumberByAgentID(GLOBAL_CACHE.Player.GetAgentID())
                    char_name = GLOBAL_CACHE.Party.Players.GetPlayerNameByLoginNumber(login_number)
                    if current_email and char_name:
                        store = AccountJSONStore(current_email)
                        store.clear_character(char_name)
                        ConsoleLog("Inventory Recorder", f"Cleared character {char_name} for {current_email}.")
                        recorded_data = multi_store.load_all()
                    else:
                        ConsoleLog("Inventory Recorder", "No data found for this character.")
                PyImGui.pop_style_color(3)

                # === CLEAR CURRENT ACCOUNT ===
                PyImGui.table_set_column_index(1)
                col_width = PyImGui.get_content_region_avail()[0]
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, orange_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, orange_hover)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, orange_active)
                if PyImGui.button("Clear Current account", width=col_width):
                    current_email = GLOBAL_CACHE.Player.GetAccountEmail()
                    if current_email:
                        store = AccountJSONStore(current_email)
                        store.clear_account()
                        ConsoleLog("Inventory Recorder", f"Cleared recorded data for {current_email}.")
                        recorded_data = multi_store.load_all()
                    else:
                        ConsoleLog("Inventory Recorder", "No data found for this account.")
                PyImGui.pop_style_color(3)

                # === CLEAR ALL ACCOUNTS ===
                PyImGui.table_set_column_index(2)
                col_width = PyImGui.get_content_region_avail()[0]
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, red_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, red_hover)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, red_active)
                if PyImGui.button("Clear all accounts", width=col_width):
                    multi_store.clear_all_data()
                    recorded_data = multi_store.load_all()
                PyImGui.pop_style_color(3)
                PyImGui.end_table()

    if save_window_timer.HasElapsed(1000):
        # Position changed?
        if (end_pos[0], end_pos[1]) != (window_x, window_y):
            window_x, window_y = int(end_pos[0]), int(end_pos[1])
            ini_window.write_key(MODULE_NAME, X_POS, str(window_x))
            ini_window.write_key(MODULE_NAME, Y_POS, str(window_y))
        # Collapsed state changed?
        if new_collapsed != window_collapsed:
            window_collapsed = new_collapsed
            ini_window.write_key(MODULE_NAME, COLLAPSED, str(window_collapsed))
        save_window_timer.Reset()


def configure():
    pass


def main():
    try:
        if not Routines.Checks.Map.MapValid() or GLOBAL_CACHE.Player.InCharacterSelectScreen():
            # When swapping characters, reset everything
            return

        if Routines.Checks.Map.IsMapReady():
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
