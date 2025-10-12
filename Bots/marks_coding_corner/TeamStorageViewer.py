import json
from collections import OrderedDict
from Py4GWCoreLib import *
from Py4GWCoreLib.enums import Bags

INVENTORY_FILE = "inventory.json"
recorded_data = OrderedDict()
search_query = ''


def save_data():
    """Save all recorded inventory data to file."""
    with open(INVENTORY_FILE, "w") as f:
        json.dump(recorded_data, f, indent=4)


def load_data():
    """Load data from disk if available."""
    try:
        with open(INVENTORY_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return OrderedDict()


def get_user_name():
    agent_id = GLOBAL_CACHE.Player.GetAgentID()
    GLOBAL_CACHE.Agent.RequestName(agent_id)

    # Wait until all names are ready (with timeout safeguard)
    timeout = 2.0  # seconds
    poll_interval = 0.1
    elapsed = 0.0

    while elapsed < timeout:
        all_ready = True
        if not GLOBAL_CACHE.Agent.IsNameReady(agent_id):
            all_ready = False
            break  # no need to check further

        if all_ready:
            break  # exit early, all names ready

        yield from Routines.Yield.wait(int(poll_interval) * 1000)
        elapsed += poll_interval

    name = ''
    # Populate agent_names dictionary
    if GLOBAL_CACHE.Agent.IsNameReady(agent_id):
        name = GLOBAL_CACHE.Agent.GetName(agent_id)

    return name


def get_items_from_bag(bag):
    """Return dict of {item_name: {model_id, count}} for a single bag."""
    items = OrderedDict()
    for item in bag.GetItems():
        if not item or item.model_id == 0:
            continue

        if not item.IsItemNameReady():
            item.RequestName()
            continue

        name = item.GetName()
        if not name:
            continue

        model_id = item.model_id
        quantity = item.quantity

        if name not in items:
            items[name] = {"model_id": model_id, "count": quantity}
        else:
            items[name]["count"] += quantity

    return items


def record_data(Anniversary_panel=True):
    """Record current account’s inventory (by character) + shared storage."""
    global recorded_data

    current_email = GLOBAL_CACHE.Player.GetAccountEmail()
    character_name = ''

    try:
        while True:
            next(get_user_name())  # advance the generator
    except StopIteration as e:
        character_name = e.value  # this is the return value

    if not current_email or not character_name:
        ConsoleLog("Inventory Recorder", "!! Could not retrieve account email/name.")
        return

    if not recorded_data:
        recorded_data.update(load_data())

    # Ensure structure: { email: { "Characters": {char: {...}}, "Storage": {...} } }
    if current_email not in recorded_data:
        recorded_data[current_email] = {"Characters": OrderedDict(), "Storage": OrderedDict()}

    account_section = recorded_data[current_email]
    raw_item_cache = GLOBAL_CACHE.Inventory._raw_item_cache

    # === INVENTORY ===
    inventory_bags = {
        "Backpack": Bags.Backpack.value,
        "BeltPouch": Bags.BeltPouch.value,
        "Bag1": Bags.Bag1.value,
        "Bag2": Bags.Bag2.value
    }

    # Create or overwrite this character’s inventory
    char_inventory = OrderedDict()
    for bag_name, bag_id in inventory_bags.items():
        bag = raw_item_cache.get_bags([bag_id])[0]
        char_inventory[bag_name] = get_items_from_bag(bag)

    account_section["Characters"][character_name] = {"Inventory": char_inventory}

    # === STORAGE ===
    storage_bags = {
        "Storage1": Bags.Storage1.value,
        "Storage2": Bags.Storage2.value,
        "Storage3": Bags.Storage3.value,
        "Storage4": Bags.Storage4.value,
        "Storage5": Bags.Storage5.value if Anniversary_panel else None,
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

    storage_section = OrderedDict()
    for bag_name, bag_id in storage_bags.items():
        if bag_id is None:
            continue
        bag = raw_item_cache.get_bags([bag_id])[0]
        storage_section[bag_name] = get_items_from_bag(bag)

    account_section["Storage"] = storage_section

    save_data()

    inv_count = sum(len(items) for bag in char_inventory.values() for items in [bag])
    stg_count = sum(len(items) for items in storage_section.values())

    ConsoleLog(
        "Inventory Recorder",
        f"Recorded {inv_count} inventory items and {stg_count} storage items for {character_name} ({current_email})."
    )


# Fuzzy Search
def levenshtein_ratio(s1: str, s2: str) -> float:
    """Return a similarity ratio between 0.0 and 1.0 for two strings."""
    s1, s2 = s1.lower(), s2.lower()
    if s1 == s2:
        return 1.0
    len1, len2 = len(s1), len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0

    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost  # substitution
            )

    distance = dp[len1][len2]
    max_len = max(len1, len2)
    return 1 - (distance / max_len)


def fuzzy_search(query: str, items: list[str], threshold: float = 0.6):
    """Return list of (item, score) for matches above threshold."""
    results = []
    for item in items:
        score = levenshtein_ratio(query, item)
        if score >= threshold:
            results.append((item, score))
    results.sort(key=lambda x: x[1], reverse=True)
    return results


def combined_search(query: str, items: list[str], fuzzy_threshold: float = 0.55) -> list[str]:
    """Return items matching partially or with fuzzy similarity."""
    if not query:
        return items

    query = query.lower()

    # --- Partial match first (fast) ---
    partial_matches = [item for item in items if query in item.lower()]

    # --- Fuzzy match fallback ---
    fuzzy_matches = [
        item for item in items
        if item not in partial_matches and levenshtein_ratio(query, item) >= fuzzy_threshold
    ]

    # Combine and sort alphabetically
    combined = sorted(partial_matches) + sorted(fuzzy_matches)
    return combined


def main():
    global recorded_data, search_query

    if not recorded_data:
        recorded_data.update(load_data())

    if PyImGui.begin("Inventory Recorder (by Account)"):
        PyImGui.text("Inventory + Storage Recorder by Email / Character")
        PyImGui.separator()

        if PyImGui.button("SCAN & RECORD"):
            record_data()

        if PyImGui.button("CLEAR CURRENT ACCOUNT"):
            current_email = GLOBAL_CACHE.Player.GetAccountEmail()
            if current_email in recorded_data:
                recorded_data.pop(current_email)
                save_data()
                ConsoleLog("Inventory Recorder", f"Cleared recorded data for {current_email}.")
            else:
                ConsoleLog("Inventory Recorder", "No data found for this account.")

        if PyImGui.button("CLEAR ALL ACCOUNTS"):
            recorded_data.clear()
            save_data()
            ConsoleLog("Inventory Recorder", "Cleared ALL recorded data.")

        PyImGui.separator()

        # === TABS BY ACCOUNT ===
        if recorded_data:
            if PyImGui.begin_tab_bar("AccountTabs"):
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
                                if PyImGui.collapsing_header(f"{char_name} Inventory", True):
                                    inv_data = char_info.get("Inventory", {})
                                    for bag_name, items in inv_data.items():
                                        if not items:
                                            continue
                                        # Filter visible items
                                        item_names = list(items.keys())
                                        filtered_items = item_names
                                        if search_query:
                                            filtered_items = combined_search(search_query, item_names)
                                        if not filtered_items:
                                            continue

                                        PyImGui.text(bag_name)
                                        if PyImGui.begin_table(f"InvTable_{email}_{char_name}_{bag_name}", 3, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg):
                                            PyImGui.table_setup_column("Model ID")
                                            PyImGui.table_setup_column("Item Name")
                                            PyImGui.table_setup_column("Count")
                                            PyImGui.table_headers_row()
                                            for item_name in filtered_items:
                                                info = items[item_name]
                                                PyImGui.table_next_row()
                                                PyImGui.table_next_column()
                                                PyImGui.text(str(info["model_id"]))
                                                PyImGui.table_next_column()
                                                PyImGui.text(item_name)
                                                PyImGui.table_next_column()
                                                PyImGui.text(str(info["count"]))
                                            PyImGui.end_table()
                                        PyImGui.separator()

                        # === STORAGE SECTION ===
                        if "Storage" in account_data:
                            if PyImGui.collapsing_header("Shared Storage", True):
                                for storage_name, items in account_data["Storage"].items():
                                    if not items:
                                        continue
                                    item_names = list(items.keys())
                                    filtered_items = item_names
                                    if search_query:
                                        filtered_items = combined_search(search_query, item_names)
                                    if not filtered_items:
                                        continue

                                    PyImGui.text(storage_name)
                                    if PyImGui.begin_table(f"StorageTable_{email}_{storage_name}", 3, PyImGui.TableFlags.Borders | PyImGui.TableFlags.RowBg):
                                        PyImGui.table_setup_column("Model ID")
                                        PyImGui.table_setup_column("Item Name")
                                        PyImGui.table_setup_column("Count")
                                        PyImGui.table_headers_row()
                                        for item_name in filtered_items:
                                            info = items[item_name]
                                            PyImGui.table_next_row()
                                            PyImGui.table_next_column()
                                            PyImGui.text(str(info["model_id"]))
                                            PyImGui.table_next_column()
                                            PyImGui.text(item_name)
                                            PyImGui.table_next_column()
                                            PyImGui.text(str(info["count"]))
                                        PyImGui.end_table()
                                    PyImGui.separator()

                        PyImGui.end_child()
                        PyImGui.end_tab_item()
                PyImGui.end_tab_bar()
        else:
            PyImGui.text("No recorded accounts found yet.")

        PyImGui.end()


if __name__ == "__main__":
    main()
