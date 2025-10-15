import os
import re
import sqlite3
import traceback
import time
from collections import OrderedDict
from contextlib import closing

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


DB_BASE_DIR = os.path.join(project_root, "Widgets/Data")
DB_PATH = os.path.join(DB_BASE_DIR, "inventory.db")
STABILIZATION_TIME = 3.0
inventory_poller_timer = ThrottledTimer(3000)
db_initialized = False
on_first_load = True
all_accounts_search_query = ''
search_query = ''
current_character_name = ''
last_seen_name = ''
name_stable_since = 0.0
recorded_data = OrderedDict()

INVENTORY_BAGS = {
    "Backpack": Bags.Backpack.value,
    "BeltPouch": Bags.BeltPouch.value,
    "Bag1": Bags.Bag1.value,
    "Bag2": Bags.Bag2.value,
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
}


def init_db():
    with closing(sqlite3.connect(DB_PATH, timeout=1.0)) as conn:
        c = conn.cursor()

        # === Accounts ===
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE
        )
        """
        )

        # === Characters ===
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            name TEXT,
            UNIQUE(account_id, name),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
        """
        )

        # === Items (for both inventory + storage) ===
        c.execute(
            """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            character_id INTEGER,
            storage_name TEXT,
            bag_name TEXT,
            item_name TEXT,
            model_id INTEGER,
            count INTEGER,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (character_id) REFERENCES characters(id)
        )
        """
        )

        conn.commit()


def get_account_id(conn, email):
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO accounts (email) VALUES (?)", (email,))
    conn.commit()
    c.execute("SELECT id FROM accounts WHERE email = ?", (email,))
    return c.fetchone()[0]


def get_character_id(conn, account_id, name):
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO characters (account_id, name) VALUES (?, ?)", (account_id, name))
    conn.commit()
    c.execute("SELECT id FROM characters WHERE account_id = ? AND name = ?", (account_id, name))
    result = c.fetchone()
    if result:
        return result[0]
    return None


def save_bag_to_db(email, char_name=None, storage_name=None, bag_name=None, bag_items={}):
    """Insert or update items directly in the DB for this bag."""
    try:
        with closing(sqlite3.connect(DB_PATH, timeout=1.0)) as conn:
            account_id = get_account_id(conn, email)
            character_id = get_character_id(conn, account_id, char_name) if char_name else None
            c = conn.cursor()

            # Delete old items for this bag first
            if char_name:
                c.execute(
                    """
                    DELETE FROM items
                    WHERE account_id=? AND character_id=? AND bag_name=?
                """,
                    (account_id, character_id, bag_name),
                )
            else:
                c.execute(
                    """
                    DELETE FROM items
                    WHERE account_id=? AND storage_name=?
                """,
                    (account_id, storage_name),
                )

            # Insert new items
            for item_name, info in bag_items.items():
                c.execute(
                    """
                    INSERT INTO items
                    (account_id, character_id, bag_name, storage_name, item_name, model_id, count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        account_id,
                        character_id,
                        bag_name if char_name else None,
                        storage_name if not char_name else None,
                        item_name,
                        info.get("model_id", 0),
                        info.get("count", 1),
                    ),
                )
            conn.commit()
    except sqlite3.OperationalError as e:
        error = 'Database timeout'
        if "database is locked" in str(e):
            error = 'Database write lock timeout'
        ConsoleLog(f"Inventory Recorder [{error}]", "Write lock timeout reached. Will try again later.")


def load_from_db():
    """Load all accounts, characters, and items into the in-memory format used by the UI."""
    with closing(sqlite3.connect(DB_PATH)) as conn:
        c = conn.cursor()

        recorded_data = OrderedDict()

        # === Get all accounts ===
        c.execute("SELECT id, email FROM accounts")
        accounts = c.fetchall()

        for account_id, email in accounts:
            recorded_data[email] = {"Characters": OrderedDict(), "Storage": OrderedDict()}

            # === Characters ===
            c.execute("SELECT id, name FROM characters WHERE account_id = ?", (account_id,))
            characters = c.fetchall()

            for char_id, char_name in characters:
                recorded_data[email]["Characters"][char_name] = {"Inventory": OrderedDict()}

                # === Inventory items ===
                c.execute(
                    """
                    SELECT bag_name, item_name, model_id, count
                    FROM items
                    WHERE account_id = ? AND character_id = ? AND bag_name IS NOT NULL
                """,
                    (account_id, char_id),
                )
                for bag_name, item_name, model_id, count in c.fetchall():
                    inv = recorded_data[email]["Characters"][char_name]["Inventory"]
                    if bag_name not in inv:
                        inv[bag_name] = OrderedDict()
                    inv[bag_name][item_name] = {"model_id": model_id, "count": count}

            # === Storage items ===
            c.execute(
                """
                SELECT storage_name, item_name, model_id, count
                FROM items
                WHERE account_id = ? AND storage_name IS NOT NULL
            """,
                (account_id,),
            )
            for storage_name, item_name, model_id, count in c.fetchall():
                storage = recorded_data[email]["Storage"]
                if storage_name not in storage:
                    storage[storage_name] = OrderedDict()
                storage[storage_name][item_name] = {"model_id": model_id, "count": count}

        return recorded_data


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
    """Updates recorded_data[email]["Characters"][char_name]["Inventory"][bag_name]"""

    if not email or not char_name:
        return

    bag_items = yield from _collect_bag_items(bag)
    save_bag_to_db(email, char_name=char_name, bag_name=bag_name, bag_items=bag_items)


def get_storage_bag_items_coroutine(bag, email, storage_name):
    """Updates recorded_data[email]["Storage"][bag_name]"""

    if not email:
        return

    bag_items = yield from _collect_bag_items(bag)
    save_bag_to_db(email, storage_name=storage_name, bag_items=bag_items)


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


def record_data_coroutine():
    global current_character_name
    global last_seen_name
    global name_stable_since

    current_email = GLOBAL_CACHE.Player.GetAccountEmail()
    if not current_email or GLOBAL_CACHE.Player.InCharacterSelectScreen():
        yield
        return

    if not Routines.Checks.Map.MapValid():
        yield
        return

    # --- get current name asynchronously ---
    char_name = yield from get_character_name()
    if not char_name:
        yield
        return

    now = time.time()

    # --- Stabilization tracking ---
    if char_name != last_seen_name:
        # Name changed — restart the timer
        last_seen_name = char_name
        name_stable_since = now
        yield
        return

    # Check if stable long enough
    stable_duration = now - name_stable_since
    if stable_duration < STABILIZATION_TIME:
        # Wait until the name has stabilized
        yield
        return

    # --- Once stable: update and record ---
    if current_character_name != char_name:
        current_character_name = char_name
        ConsoleLog("Inventory Recorder", f"Character stabilized: {char_name}")
        yield from save_character_inventory_to_db(current_email, char_name)
    yield


def save_character_inventory_to_db(current_email, char_name):
    """Save both inventory and storage bags to DB."""
    raw_item_cache = GLOBAL_CACHE.Inventory._raw_item_cache

    # Character Bags
    for bag_name, bag_id in INVENTORY_BAGS.items():
        bag = raw_item_cache.get_bags([bag_id])[0]
        yield from get_character_bag_items_coroutine(
            bag,
            current_email,
            char_name=char_name,
            bag_name=bag_name,
        )

    # Storage Bags
    for storage_name, bag_id in STORAGE_BAGS.items():
        if bag_id is None:
            continue
        bag = raw_item_cache.get_bags([bag_id])[0]
        yield from get_storage_bag_items_coroutine(
            bag,
            current_email,
            storage_name=storage_name,
        )

    ConsoleLog("Inventory Recorder", f"Saved bags for {char_name}")
    yield


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
    global db_initialized
    global on_first_load
    global recorded_data
    global current_character_name
    global name_stable_since

    if first_run:
        PyImGui.set_next_window_pos(window_x, window_y)
        PyImGui.set_next_window_collapsed(window_collapsed, 0)
        first_run = False

    new_collapsed = PyImGui.is_window_collapsed()
    end_pos = PyImGui.get_window_pos()

    if on_first_load:
        on_first_load = False
        recorded_data = load_from_db()

    if not db_initialized:
        init_db()
        ConsoleLog("DB", "DB initialized")
        db_initialized = True

    # === AUTO-POLL (Refresh inventory snapshot) ===
    if inventory_poller_timer.IsExpired():
        GLOBAL_CACHE.Coroutines.append(record_data_coroutine())
        # Reload memory view
        recorded_data = load_from_db()
        inventory_poller_timer.Reset()

    PyImGui.set_next_window_size(1000, 800)
    if PyImGui.begin(MODULE_NAME):
        PyImGui.text("Inventory + Storage Recorder by Email / Character (SQLite Edition)")
        PyImGui.separator()

        # === SCROLLABLE AREA START ===
        # Compute space for footer
        available_height = PyImGui.get_window_height() - 175  # leave room for buttons + footer
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
                                # Limit to 3 characters for readability
                                display_chars = character_names[:3]
                                # Join each character name on its own new line, indented
                                character_block = "\n".join(f"   - {name}" for name in display_chars)
                                account_label = f"{email}\n{character_block}"
                            else:
                                account_label = f"[{email}]\n   [No Characters]"

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
                                PyImGui.table_setup_column("Item Name", 0, 200.0)
                                PyImGui.table_setup_column("Count", 0, 50.0)
                                PyImGui.table_setup_column("Location", 0, 150.0)
                                PyImGui.table_setup_column("Account (Characters)", 0, 300.0)
                                PyImGui.table_headers_row()

                                for entry in search_results:
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
                                        PyImGui.text(f"{entry['character']} - {entry['bag']}")
                                    else:
                                        PyImGui.text(f"Storage - {entry['bag']}")

                                    # === ACCOUNT IDENTIFIER ===
                                    PyImGui.table_next_column()
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

                                if PyImGui.collapsing_header(f"{char_name} Inventory", True):
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
        is_name_stable = time.time() - name_stable_since > STABILIZATION_TIME
        PyImGui.text(
            f"Reload interval: {int(inventory_poller_timer.GetTimeRemaining() // 1000)}(s) for {"..." if not is_name_stable else current_character_name}"
        )
        if PyImGui.collapsing_header("Advanced Clearing", True):
            if PyImGui.begin_table("clear_buttons_table", 2, PyImGui.TableFlags.BordersInnerV):
                # Define colors
                orange_color = Color(255, 165, 0, 255).to_tuple_normalized()  # orange
                orange_hover = Color(255, 200, 50, 255).to_tuple_normalized()
                orange_active = Color(255, 140, 0, 255).to_tuple_normalized()

                red_color = Color(220, 20, 60, 255).to_tuple_normalized()  # crimson red
                red_hover = Color(255, 50, 80, 255).to_tuple_normalized()
                red_active = Color(180, 0, 40, 255).to_tuple_normalized()

                PyImGui.table_next_row()

                # === Column 1: CLEAR CURRENT ACCOUNT ===
                PyImGui.table_set_column_index(0)
                col_width = PyImGui.get_content_region_avail()[0]
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, orange_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, orange_hover)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, orange_active)
                if PyImGui.button("Clear Current account", width=col_width):
                    current_email = GLOBAL_CACHE.Player.GetAccountEmail()
                    if current_email:
                        with closing(sqlite3.connect(DB_PATH)) as conn:
                            c = conn.cursor()
                            c.execute(
                                "DELETE FROM items WHERE account_id = (SELECT id FROM accounts WHERE email = ?)",
                                (current_email,),
                            )
                            conn.commit()
                        ConsoleLog("Inventory Recorder", f"Cleared recorded data for {current_email}.")
                        recorded_data = load_from_db()
                    else:
                        ConsoleLog("Inventory Recorder", "No data found for this account.")
                PyImGui.pop_style_color(3)

                # === Column 2: CLEAR ALL ACCOUNTS ===
                PyImGui.table_set_column_index(1)
                col_width = PyImGui.get_content_region_avail()[0]
                PyImGui.push_style_color(PyImGui.ImGuiCol.Button, red_color)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonHovered, red_hover)
                PyImGui.push_style_color(PyImGui.ImGuiCol.ButtonActive, red_active)
                if PyImGui.button("Clear all accounts", width=col_width):
                    with closing(sqlite3.connect(DB_PATH)) as conn:
                        c = conn.cursor()
                        c.execute("DELETE FROM items")
                        c.execute("DELETE FROM characters")
                        c.execute("DELETE FROM accounts")
                        conn.commit()
                    ConsoleLog("Inventory Recorder", "Cleared ALL recorded data.")
                    recorded_data = load_from_db()
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
