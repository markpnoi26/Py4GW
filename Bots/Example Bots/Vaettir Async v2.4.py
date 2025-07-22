import math

from Py4GWCoreLib import *
from Py4GWCoreLib.enums import ModelID

module_name = "Vaettir Bot"

#region coords

outpost_coord_list = [(-24380, 15074), (-26375, 16180)]

bjora_coord_list = [
    (15003, -16598), (12699, -14589), (11628, -13867), (10891, -12989), (10517, -11229),
    (10209, -9973), (9296, -8811), (7815, -7967), (6266, -6328), (4940, -4655),
    (3867, -2397), (2279, -1331), (7, -1072), (-1752, -1209), (-3596, -1671),
    (-5386, -1526), (-6904, -283), (-7711, 364), (-9537, 1265), (-11141, 857),
    (-12730, 371), (-13379, 40), (-14925, 1099), (-16183, 2753), (-17803, 4439),
    (-18852, 5290), (-19250, 5431), (-19968, 5564), (-20076, 5580)
]


take_bounty_coord_list = [(13367, -20771)]

farming_route = [
    (11375, -22761), (10925, -23466), (10917, -24311), (10280, -24620),
    (9640, -23175), (7815, -23200), (7765, -22940), (8213, -22829), (8740, -22475),
    (8880, -21384), (8684, -20833), (8982, -20576)
]

farming_route2 = [
    (10196, -20124), (9976, -18338), (11316, -18056), (10392, -17512),
    (10114, -16948), (10729, -16273), (10505, -14750), (10815, -14790), (11090, -15345),
    (11670, -15457), (12604, -15320), (12450, -14800), (12725, -14850), (12476, -16157)
]

path_to_killing_spot = [
    (13070, -16911), (12938, -17081), (12790, -17201), (12747, -17220),
    (12703, -17239), (12684, -17184)
]


path_to_merchant = [
    (-23041, 14939)
]

exit_jaga_moraine = [(12289, -17700) ,(13970, -18920), (15400, -20400), (15800,-20600)]

return_jaga_moraine = [(-20300, 5600 )] ## A Dekoy Accadia: removed unnecessary coordinates to re-enter Jaga.

#endregion

#region types

class WindowStatistics:
    def __init__(self):
        self.global_timer = Timer()
        self.lap_timer = Timer()
        self.lap_history = []
        self.min_time = 0
        self.max_time = 0
        self.avg_time = 0.0
        self.runs_attempted = 0
        self.runs_completed = 0
        self.runs_failed = 0
        self.success_rate = 0.0
        self.deaths = 0
        self.kills = 0
        self.left_alive = 0
        self.whites = 0
        self.blues = 0
        self.purples = 0
        self.golds = 0
        self.tomes = 0
        self.white_dyes = 0
        self.black_dyes = 0
        self.lockpicks = 0
        self.dyes = 0
        self.glacial_stones = 0
        self.event_items = 0
        self.id_kits = 0
        self.salvage_kits = 0
        self.map_pieces = 0
        self.starting_gold = 0
        self.gold_gained = 0
        self.wood_planks = 0
        self.iron_ingots = 0
        self.glittering_dust = 0
        self.cloth = 0
        self.bones = 0

class ConfigVarsClass:
    def __init__(self):
        self.loot_blues = False
        self.loot_purples = False
        self.loot_golds = True
        self.loot_tomes = True
        self.loot_white_dyes = True
        self.loot_black_dyes = True
        self.loot_lockpicks = True
        self.loot_whites = True
        self.loot_dyes = False
        self.loot_glacial_stones = True
        self.loot_event_items = True
        self.loot_map_pieces = False
        self.id_whites = False
        self.id_blues = False
        self.id_purples = True
        self.id_golds = True
        self.salvage_whites = True
        self.salvage_blues = True
        self.salvage_purples = False
        self.salvage_golds = False
        self.salvage_glacial_stones = False
        self.salvage_purple_with_sup_kit = True
        self.salvage_gold_with_sup_kit = False
        self.sell_whites = True
        self.sell_blues = True
        self.sell_purples = True
        self.sell_golds = True
        self.sell_materials = True
        self.sell_wood = True
        self.sell_iron = True
        self.sell_dust = True
        self.sell_bones = True
        self.sell_cloth = True
        self.sell_granite = True
        self.keep_id_kit = 2
        self.keep_salvage_kit = 0
        self.keep_sup_salvage_kit = 0
        self.keep_gold_amount = 5000
        self.leave_empty_inventory_slots = 2

class BotVars:
    def __init__(self, map_id=0):
        self.starting_map = map_id
        self.bot_started = False
        self.window_module = ImGui.WindowModule()
        self.variables = {}
        self.window_statistics = WindowStatistics()
        self.show_config_options = False
        self.config_vars = ConfigVarsClass()
        self.progress = 0
        self.prograss_limit = 100
        self.forced_restart = False
        self.show_visual_path = True
        self.desired_map_id = self.starting_map
        self.sell_to_vendor_action_queue = ActionQueueNode(350)
        self.salvage_action_queue = ActionQueueNode(350)
        self.identify_action_queue = ActionQueueNode(350)
        self.buy_from_vendor_action_queue = ActionQueueNode(350)
        self.deposit_action_queue = ActionQueueNode(350)
        self.skillbar_action_queue = ActionQueueNode(100)
        

class StateMachineVars:
        def __init__(self):
            self.state_machine = FSM("Main")
            self.sell_to_vendor = FSM("SellToVendor")
            self.outpost_pathing = Routines.Movement.PathHandler(outpost_coord_list)
            self.bjora_pathing = Routines.Movement.PathHandler(bjora_coord_list)
            self.bounty_npc = Routines.Movement.PathHandler(take_bounty_coord_list)
            self.farming_route = Routines.Movement.PathHandler(farming_route)
            self.farming_route2 = Routines.Movement.PathHandler(farming_route2)
            self.path_to_killing_spot = Routines.Movement.PathHandler(path_to_killing_spot)
            self.exit_jaga_moraine = Routines.Movement.PathHandler(exit_jaga_moraine)
            self.return_jaga_moraine = Routines.Movement.PathHandler(return_jaga_moraine)
            self.in_waiting_routine = False
            self.in_killing_routine = False
            self.auto_stuck_command_timer = Timer()
            self.auto_stuck_command_timer.Start()
            self.old_player_x = 0.0
            self.old_player_y = 0.0
            self.stuck_count = 0
            self.non_movement_timer = Timer()
            self.non_movement_timer.Start()
            self.looting_item_id = 0
            self.movement_handler = Routines.Movement.FollowXY()
            self.exact_movement_handler = Routines.Movement.FollowXY(tolerance=0) # Added by Markitosline: this movement routine has a 0 tolerance so that the final player location is exactly as per defined in waypoints
            self.path_to_merchant = Routines.Movement.PathHandler(path_to_merchant)

FSM_vars = StateMachineVars()

#endregion

#region globals

follow_delay_timer = Timer()
bot_vars = BotVars(map_id=650) #Longeye's Ledge
bot_vars.window_module = ImGui.WindowModule(module_name, window_name="Vaettir Bot v2.3.3 Enums WIP D", window_size=(300, 300), window_flags=PyImGui.WindowFlags.AlwaysAutoResize)
looting_state_entered = False


#endregion

def progress_bar_value():
    global FSM_vars
    current_value = FSM_vars.state_machine.get_current_state_number()
    max_value = FSM_vars.state_machine.get_state_count()

    first_phase_name = "Outpost Handling"
    first_phase_steps = 3 + FSM_vars.sell_to_vendor.get_state_count() + FSM_vars.outpost_pathing.get_position_count()

    if current_value < 3:
        return current_value /first_phase_steps, "Initializing"
    if current_value == 4:
        sub_fsm_current_value = FSM_vars.sell_to_vendor.get_current_state_number()
        sub_fsm_max_value = FSM_vars.sell_to_vendor.get_state_count()
        return 3 + sub_fsm_current_value/first_phase_steps, FSM_vars.sell_to_vendor.get_current_step_name()
    if current_value == 5:
        sub_fsm_current_value = FSM_vars.outpost_pathing.get_position()
        sub_fsm_max_value = FSM_vars.outpost_pathing.get_position_count()
        offset = 3 + FSM_vars.sell_to_vendor.get_state_count()
        return offset + sub_fsm_current_value/first_phase_steps, FSM_vars.outpost_pathing.get_position_count()


#region Helper Functions
def StartBot():
    global bot_vars
    bot_vars.bot_started = True
    bot_vars.window_statistics.global_timer.Start()
    bot_vars.window_statistics.lap_timer.Start()
    bot_vars.forced_restart = False

def StopBot():
    global bot_vars
    bot_vars.bot_started = False
    bot_vars.window_statistics.global_timer.Stop()
    bot_vars.window_statistics.lap_timer.Stop()

def IsBotStarted():
    global bot_vars
    return bot_vars.bot_started
	
def GetDyeColorIdFromItem(item_id: int) -> int:
    """
    Retrieves the specific color ID from a generic dye item.
    Assumes color ID is stored in the first argument of a modifier.
    Returns 0 if no color ID modifier is found.
    """
    modifiers = Item.Customization.Modifiers.GetModifiers(item_id)

    for mod in modifiers:
        modColor = mod.GetArg1() # Assuming GetArg1() returns the color ID

        if modColor != 0:
            return modColor # Return the found color ID

    return 0 # Return 0 if no non-zero color modifier argument found

def InventoryCheck():
    global bot_vars
    if bot_vars.config_vars.leave_empty_inventory_slots < Inventory.GetFreeSlotCount(): #tnt
        return True
    return False


def set_waiting_routine():
    global FSM_vars
    FSM_vars.in_waiting_routine = True

def end_waiting_routine():
    global FSM_vars
    FSM_vars.in_waiting_routine = False
    return True

def set_killing_routine():
    global FSM_vars
    FSM_vars.in_waiting_routine = True
    FSM_vars.in_killing_routine = True

def end_killing_routine():
    global FSM_vars, bot_vars
    global area_distance
    player_x, player_y = Player.GetXY()
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), Range.Area.value)
    enemy_array = AgentArray.Filter.ByCondition(enemy_array, lambda agent_id: Agent.IsAlive(agent_id))


    if len(enemy_array) <= 3:
        FSM_vars.in_waiting_routine = False
        FSM_vars.in_killing_routine = False

        bot_vars.window_statistics.runs_completed += 1
        bot_vars.window_statistics.success_rate = bot_vars.window_statistics.runs_completed / bot_vars.window_statistics.runs_attempted if bot_vars.window_statistics.runs_attempted > 0 else 1
        lap_timer = bot_vars.window_statistics.lap_timer.GetElapsedTime()
        bot_vars.window_statistics.lap_timer.Stop()

        bot_vars.window_statistics.lap_history.append(lap_timer)
        bot_vars.window_statistics.min_time = min(bot_vars.window_statistics.lap_history)
        bot_vars.window_statistics.max_time = max(bot_vars.window_statistics.lap_history)
        bot_vars.window_statistics.avg_time = sum(bot_vars.window_statistics.lap_history) / len(bot_vars.window_statistics.lap_history) if len(bot_vars.window_statistics.lap_history) > 0 else 1

        bot_vars.window_statistics.left_alive += 60 - len(enemy_array)
        bot_vars.window_statistics.kills += len(enemy_array)
        
        take_bags_snapshot()
        take_item_array_snapshot()

        return True

    return False

def log_run_start():
    global bot_vars
    bot_vars.window_statistics.runs_attempted += 1
    bot_vars.window_statistics.lap_timer.Reset()

pick_up_item_timer = Timer()
pick_up_item_timer.Start()

def IsValidItem(item_id):
    return (Agent.agent_instance(item_id).item_agent.owner_id == Player.GetAgentID()) or (Agent.agent_instance(item_id).item_agent.owner_id == 0)

def get_filtered_loot_array():
    global bot_vars

    # Get all item agents nearby
    item_array = AgentArray.GetItemArray()
    item_array = AgentArray.Filter.ByCondition(item_array, Agent.IsValid)
    item_array = AgentArray.Filter.ByDistance(item_array, Player.GetXY(), Range.Spellcast.value)
    initial_nearby_count = len(item_array) # Count after basic range/validity
    item_array = AgentArray.Filter.ByCondition(item_array, lambda agent_id: IsValidItem(agent_id))
    valid_owner_count = len(item_array) # Count after ownership check

    agent_to_item_map = {
        agent_id: Agent.GetItemAgent(agent_id).item_id
        for agent_id in item_array
    }

    item_ids = list(agent_to_item_map.values())
    pre_filter_count = len(item_ids) # <-- Calculation moved earlier

    # === Rarity filtering ===
    rarity_filters = []
    if not bot_vars.config_vars.loot_whites:
        rarity_filters.append(lambda item_id: not Item.Rarity.IsWhite(item_id))
    if not bot_vars.config_vars.loot_blues:
        rarity_filters.append(lambda item_id: not Item.Rarity.IsBlue(item_id))
    if not bot_vars.config_vars.loot_purples:
        rarity_filters.append(lambda item_id: not Item.Rarity.IsPurple(item_id))
    if not bot_vars.config_vars.loot_golds:
        rarity_filters.append(lambda item_id: not Item.Rarity.IsGold(item_id))
    for rf in rarity_filters:
        item_ids = ItemArray.Filter.ByCondition(item_ids, rf)

    # === Map piece filtering ===
    if not bot_vars.config_vars.loot_map_pieces:
        map_piece_model_ids = {
            ModelID.Map_Piece_Tl, # 24629
            ModelID.Map_Piece_Tr, # 24630
            ModelID.Map_Piece_Bl, # 24631
            ModelID.Map_Piece_Br, # 24632
        }
        item_ids = ItemArray.Filter.ByCondition(item_ids, lambda item_id: Item.GetModelID(item_id) not in map_piece_model_ids)

    # === Tome filtering ===
    if not bot_vars.config_vars.loot_tomes:
        item_ids = ItemArray.Filter.ByCondition(item_ids, lambda item_id: not Item.Type.IsTome(item_id))

    # Convert back to agent IDs
    filtered_agent_ids = [
        agent_id for agent_id, item_id in agent_to_item_map.items()
        if item_id in item_ids # item_ids now holds the fully filtered list
    ]
    final_filtered_count = len(filtered_agent_ids) # <-- Calculation moved earlier

    # --- Logging block is now after calculations ---
    if final_filtered_count == 0 and initial_nearby_count > 0:
         Py4GW.Console.Log(bot_vars.window_module.module_name, f"[Debug] get_filtered_loot_array: Initial Nearby={initial_nearby_count}, Valid Owner={valid_owner_count}, Pre-Filter={pre_filter_count}, Final Filtered={final_filtered_count}", Py4GW.Console.MessageType.Info)
         # Optional: Log model IDs here if needed

    return AgentArray.Sort.ByDistance(filtered_agent_ids, Player.GetXY())


looting_item = 0

def loot_items():
    global area_distance, bot_vars
    global pick_up_item_timer
    global looting_item

    
    if Inventory.GetFreeSlotCount() == 0:#<= bot_vars.config_vars.leave_empty_inventory_slots:
        return

    FSM_vars.in_waiting_routine = True
    filtered_agent_ids = get_filtered_loot_array()
    if not filtered_agent_ids:
        return
    
    item = filtered_agent_ids[0]

    if looting_item != item:
        looting_item = item


    
    current_target = Player.GetTargetID()
    
    if current_target != looting_item:
        Player.ChangeTarget(looting_item)
        return

    if pick_up_item_timer.HasElapsed(1600):
        Keystroke.PressAndRelease(Key.Space.value)
        pick_up_item_timer.Reset()
        return
        
    

def finished_looting():
    global area_distance, bot_vars
    global pick_up_item_timer
    global looting_state_entered # Reference the global flag

    inventory_slots_available = Inventory.GetFreeSlotCount()
    inventory_full_condition = inventory_slots_available <= bot_vars.config_vars.leave_empty_inventory_slots

    filtered_agent_ids = get_filtered_loot_array()
    no_items_condition = len(filtered_agent_ids) == 0

    # This is the correct check determining if looting should stop
    if inventory_full_condition or no_items_condition:
        # --- Logging block MOVED inside the correct 'if' ---
        reason = ""
        if inventory_full_condition:
            # Use the actual value checked
            reason += f"Inventory full ({inventory_slots_available} <= {bot_vars.config_vars.leave_empty_inventory_slots}). "
        if no_items_condition:
            reason += "No valid/filtered items found nearby."

        # Log only if we were actually attempting to loot (flag is True)
        if looting_state_entered:
             Py4GW.Console.Log(bot_vars.window_module.module_name, f"[Debug] Exiting 'Loot routine'. Reason: {reason.strip()}", Py4GW.Console.MessageType.Warning) # Use Warning to make it stand out
             looting_state_entered = False # Reset flag for next time ONLY when exiting

        # --- End logging block ---
        return True # Exit the looting state

    # If neither condition is met, continue looting
    return False

item_array_snapshot = []
bag_array_snapshot = []

def take_item_array_snapshot():
    global item_array_snapshot
    item_array_snapshot = get_filtered_loot_array()
    
def take_bags_snapshot():
    global bag_array_snapshot
    bags_to_check = ItemArray.CreateBagList(1,2,3,4)
    bag_array_snapshot = ItemArray.GetItemArray(bags_to_check)

def compare_item_array_snapshot():
    global item_array_snapshot
    current_item_array = get_filtered_loot_array() 
    item_array_difference = AgentArray.Manipulation.Subtract(item_array_snapshot,current_item_array)
    return item_array_difference

def compare_bag_array_snapshot():
    global bag_array_snapshot
    bags_to_check = ItemArray.CreateBagList(1,2,3,4)
    current_bag_array = ItemArray.GetItemArray(bags_to_check)
    bag_array_difference = AgentArray.Manipulation.Subtract(bag_array_snapshot, current_bag_array)
    return bag_array_difference

def check_looted_items():
    global bot_vars
    item_array_difference = compare_item_array_snapshot()
    if len(item_array_difference) > 0:
    # Create a dictionary of conditions to count different item types
        item_counters = {
            # ... (rarity checks) ...
            # --- CORRECTED Enum Names ---
            # Dye Color IDs likely remain numbers
            "black_dyes": lambda item_id: GetDyeColorIdFromItem(item_id) == 10,
            "white_dyes": lambda item_id: GetDyeColorIdFromItem(item_id) == 12,
            "lockpicks": lambda item_id: Item.GetModelID(item_id) == ModelID.Lockpick, # 22751
            "dyes": lambda item_id: Item.GetModelID(item_id) == ModelID.Vial_Of_Dye, # 146
            "glacial_stones": lambda item_id: Item.GetModelID(item_id) == ModelID.Glacial_Stone, # 27047
            "event_items": lambda item_id: Item.GetModelID(item_id) in {
                ModelID.Hard_Apple_Cider,     # 28435
                ModelID.Slice_Of_Pumpkin_Pie  # 28436
            },
            "map_pieces": lambda item_id: Item.GetModelID(item_id) in {
                ModelID.Map_Piece_Tl, # 24629
                ModelID.Map_Piece_Tr, # 24630
                ModelID.Map_Piece_Bl, # 24631
                ModelID.Map_Piece_Br, # 24632
            },
            # --- END CORRECTION ---
        }
        

        # Initialize counters
        item_counts = {key: 0 for key in item_counters}

        # Process items only once
        for item_id in item_array_difference:
            for key, condition in item_counters.items():
                if condition(item_id):
                    item_counts[key] += 1

        # Assign to bot_vars statistics
        bot_vars.window_statistics.whites += item_counts["whites"]
        bot_vars.window_statistics.blues += item_counts["blues"]
        bot_vars.window_statistics.purples += item_counts["purples"]
        bot_vars.window_statistics.golds += item_counts["golds"]
        bot_vars.window_statistics.tomes += item_counts["tomes"]
        bot_vars.window_statistics.white_dyes += item_counts["white_dyes"]
        bot_vars.window_statistics.black_dyes += item_counts["black_dyes"]
        bot_vars.window_statistics.lockpicks += item_counts["lockpicks"]
        bot_vars.window_statistics.dyes += item_counts["dyes"]
        bot_vars.window_statistics.glacial_stones += item_counts["glacial_stones"]
        bot_vars.window_statistics.event_items += item_counts["event_items"]
        bot_vars.window_statistics.map_pieces += item_counts["map_pieces"]

        
def check_salvaged_items(): 
    global bot_vars
    bag_array_difference = compare_bag_array_snapshot()
    if len(bag_array_difference) > 0:
        # --- CORRECTED Enum Names ---
        wood = ItemArray.Filter.ByCondition(bag_array_difference, lambda item_id: Item.GetModelID(item_id) == ModelID.Wood_Plank)         # 946
        iron = ItemArray.Filter.ByCondition(bag_array_difference, lambda item_id: Item.GetModelID(item_id) == ModelID.Iron_Ingot)         # 948
        dust = ItemArray.Filter.ByCondition(bag_array_difference, lambda item_id: Item.GetModelID(item_id) == ModelID.Pile_Of_Glittering_Dust) # 929
        bones = ItemArray.Filter.ByCondition(bag_array_difference, lambda item_id: Item.GetModelID(item_id) == ModelID.Bone)              # 921
        cloth = ItemArray.Filter.ByCondition(bag_array_difference, lambda item_id: Item.GetModelID(item_id) == ModelID.Bolt_Of_Cloth)      # 925

        bot_vars.window_statistics.wood_planks += len(wood)
        bot_vars.window_statistics.iron_ingots += len(iron)
        bot_vars.window_statistics.glittering_dust += len(dust)
        bot_vars.window_statistics.bones += len(bones)
        bot_vars.window_statistics.cloth += len(cloth)



def filter_identify_array():
    global bot_vars
    bags_to_check = ItemArray.CreateBagList(1,2,3,4)
    unidentified_items = ItemArray.GetItemArray(bags_to_check)
    unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Usage.IsIdentified(item_id))

    # Filter by rarity based on config settings
    if not bot_vars.config_vars.id_whites:
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Rarity.IsWhite(item_id))
    if not bot_vars.config_vars.id_blues:
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Rarity.IsBlue(item_id))
    if not bot_vars.config_vars.id_purples:
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Rarity.IsPurple(item_id))
    if not bot_vars.config_vars.id_golds:
        unidentified_items = ItemArray.Filter.ByCondition(unidentified_items, lambda item_id: not Item.Rarity.IsGold(item_id))
        
    return unidentified_items

def filter_salvage_array():
    global bot_vars
    bags_to_check = ItemArray.CreateBagList(1,2,3,4)
    salvageable_items = ItemArray.GetItemArray(bags_to_check)
    salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: Item.Usage.IsIdentified(item_id))
    salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: Item.Usage.IsSalvageable(item_id))

    if not bot_vars.config_vars.salvage_blues:
        salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: not Item.Rarity.IsBlue(item_id))
    if not bot_vars.config_vars.salvage_purples:
        salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: not Item.Rarity.IsPurple(item_id))
    if not bot_vars.config_vars.salvage_golds:
        salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: not Item.Rarity.IsGold(item_id))
    if not bot_vars.config_vars.salvage_glacial_stones:
    # Remove items if they are Glacial Stones (Model ID 27047)
        glacial_stone_model_id = ModelID.Glacial_Stone # 27047
        salvageable_items = ItemArray.Filter.ByCondition(salvageable_items, lambda item_id: Item.GetModelID(item_id) != glacial_stone_model_id)
    return salvageable_items


def DepositGold():
    global bot_vars # Ensure global bot_vars is accessible
    
    gold_on_char = Inventory.GetGoldOnCharacter()
    gold_to_keep = bot_vars.config_vars.keep_gold_amount
    gold_to_deposit = gold_on_char - gold_to_keep # Calculate amount over threshold

    if gold_to_deposit > 0:
        # Ensure we don't try to deposit negative gold if keep_gold_amount is very high
        # Also ensures we don't try to deposit more than we have (though API might handle this)
        if gold_to_deposit > gold_on_char: 
             gold_to_deposit = gold_on_char 

        Inventory.DepositGold(gold_to_deposit) # Perform the deposit action

        # --- ADDED Confirmation Log ---
        # Format the number with commas for readability
        log_message = f"[Deposit] Deposited {gold_to_deposit:,} gold to Xunlai Chest." 
        Py4GW.Console.Log(bot_vars.window_module.module_name, log_message, Py4GW.Console.MessageType.Info)
        # --- END Added Log ---

        return True # Indicate deposit was performed
        
    return False # Indicate no deposit was needed/performed

#endregion

#region debug

def lsit_to_string(list):
    return ', '.join([str(elem) for elem in list])

#endregion

#region targetting
def TargetNearestNPC():
    npc_array = AgentArray.GetNPCMinipetArray()
    npc_array = AgentArray.Filter.ByDistance(npc_array,Player.GetXY(), 200)
    npc_array = AgentArray.Sort.ByDistance(npc_array, Player.GetXY())
    if len(npc_array) > 0:
        Player.ChangeTarget(npc_array[0])

def TargetNearestNPCXY(x,y):
    scan_pos = (x,y)
    npc_array = AgentArray.GetNPCMinipetArray()
    npc_array = AgentArray.Filter.ByDistance(npc_array,scan_pos, 200)
    npc_array = AgentArray.Sort.ByDistance(npc_array, scan_pos)
    if len(npc_array) > 0 and Agent.IsValid(npc_array[0]):
        Player.ChangeTarget(npc_array[0])
        
#endregion

#region Map

def TravelToOutpost(outpost_id):
    if not IsMapValid():
        return
    if Map.GetMapID() == outpost_id:
        return
    Map.Travel(outpost_id)

    
def HasArrivedToOutpost(outpost_id):
    if Map.GetMapID() == outpost_id:
        return True
    return False

#endregion
#region skillbar
def LoadSkillBar():
    primary_profession, secondary_profession = Agent.GetProfessionNames(Player.GetAgentID())

    if primary_profession == "Assassin":
        SkillBar.LoadSkillTemplate("OwVUI2h5lPP8Id2BkAiAvpLBTAA")
    elif primary_profession == "Mesmer":
        SkillBar.LoadSkillTemplate("OQdUAQROqPP8Id2BkAiAvpLBTAA")

def IsSkillBarLoaded():
    global bot_vars
    global skillbar

    primary_profession, secondary_profession = Agent.GetProfessionNames(Player.GetAgentID())
    if primary_profession != "Assassin" and primary_profession != "Mesmer":
        frame = inspect.currentframe()
        current_function = frame.f_code.co_name if frame else "Unknown"
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"{current_function} - This bot requires either A/Me or Me/A to work, halting.", Py4GW.Console.MessageType.Error)
        ResetEnvironment()
        StopBot()
        return False

    skillbar.deadly_paradox = SkillBar.GetSkillIDBySlot(1)
    skillbar.shadow_form = SkillBar.GetSkillIDBySlot(2)
    skillbar.shroud_of_distress = SkillBar.GetSkillIDBySlot(3)
    skillbar.way_of_perfection = SkillBar.GetSkillIDBySlot(4)
    skillbar.heart_of_shadow = SkillBar.GetSkillIDBySlot(5)
    skillbar.wastrels_worry = SkillBar.GetSkillIDBySlot(6)
    skillbar.arcane_echo = SkillBar.GetSkillIDBySlot(7)
    skillbar.channeling = SkillBar.GetSkillIDBySlot(8)
    
    Py4GW.Console.Log(bot_vars.window_module.module_name, f"SkillBar Loaded.", Py4GW.Console.MessageType.Info)       
    return True
    
#region inventory
def HasThingsToSell(log = False):
    global bot_vars

    # Create a list of bags to check
    bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    items_to_sell = ItemArray.GetItemArray(bags_to_check)

    # Log initial items
    frame = inspect.currentframe()
    current_function = frame.f_code.co_name if frame else "Unknown"
    if log:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"{current_function} - Initial items: {items_to_sell}", Py4GW.Console.MessageType.Info)

    # General material filtering
    if not bot_vars.config_vars.sell_materials:
        items_to_sell = ItemArray.Filter.ByCondition(items_to_sell, lambda item_id: not Item.Type.IsMaterial(item_id))
        if log:
            Py4GW.Console.Log(bot_vars.window_module.module_name, f"{current_function} - After filtering out all materials: {items_to_sell}", Py4GW.Console.MessageType.Info)
    else:
        # Filter specific materials if 'sell_materials' is enabled
        filtered_items = []

        if bot_vars.config_vars.sell_wood:
            filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsWood))
        if bot_vars.config_vars.sell_iron:
            filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsIron))
        if bot_vars.config_vars.sell_dust:
            filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsDust))
        if bot_vars.config_vars.sell_bones:
            filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsBones))
        if bot_vars.config_vars.sell_cloth:
            filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsCloth))
        if bot_vars.config_vars.sell_granite:
            filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsGranite))

        # Replace 'items_to_sell' with filtered items
        items_to_sell = filtered_items
        if log:
            Py4GW.Console.Log(bot_vars.window_module.module_name, f"{current_function} - After filtering specific materials: {items_to_sell}", Py4GW.Console.MessageType.Info)

    # Filter based on rarity
    if not bot_vars.config_vars.sell_whites:
        items_to_sell = ItemArray.Filter.ByCondition(items_to_sell, lambda item_id: not Item.Rarity.IsWhite(item_id))
        if log:
            Py4GW.Console.Log(bot_vars.window_module.module_name, f"{current_function} - After filtering whites: {items_to_sell}", Py4GW.Console.MessageType.Info)

    if not bot_vars.config_vars.sell_blues:
        items_to_sell = ItemArray.Filter.ByCondition(items_to_sell, lambda item_id: not Item.Rarity.IsBlue(item_id))
        if log:
            Py4GW.Console.Log(bot_vars.window_module.module_name, f"{current_function} - After filtering blues: {items_to_sell}", Py4GW.Console.MessageType.Info)

    if not bot_vars.config_vars.sell_purples:
        items_to_sell = ItemArray.Filter.ByCondition(items_to_sell, lambda item_id: not Item.Rarity.IsPurple(item_id))
        if log:
            Py4GW.Console.Log(bot_vars.window_module.module_name, f"{current_function} - After filtering purples: {items_to_sell}", Py4GW.Console.MessageType.Info)

    if not bot_vars.config_vars.sell_golds:
        items_to_sell = ItemArray.Filter.ByCondition(items_to_sell, lambda item_id: not Item.Rarity.IsGold(item_id))
        if log:
            Py4GW.Console.Log(bot_vars.window_module.module_name, f"{current_function} - After filtering golds: {items_to_sell}", Py4GW.Console.MessageType.Info)

    # Check if there are any remaining items to sell
    if len(items_to_sell) > 0:
        if log:
            Py4GW.Console.Log(bot_vars.window_module.module_name, f"{current_function} - We have Items to sell: {items_to_sell}", Py4GW.Console.MessageType.Info)
        return True

    return False

def DoesNeedInventoryHandling():
    global bot_vars 
    if Inventory.GetFreeSlotCount() < bot_vars.config_vars.leave_empty_inventory_slots:
        return True
    if Inventory.GetModelCount(ModelID.Superior_Identification_Kit) < bot_vars.config_vars.keep_id_kit: # Check 5899 vs keep_id_kit
        return True
    if Inventory.GetModelCount(ModelID.Salvage_Kit) < bot_vars.config_vars.keep_salvage_kit: # Check 2992 vs keep_salvage_kit
        return True
    return HasThingsToSell()


def identify_item(item_id):
    first_id_kit = Inventory.GetFirstIDKit()
    if first_id_kit == 0:
        return
    Inventory.IdentifyItem(item_id, first_id_kit)
    
    
def identify_items():
    global bot_vars
    unidentified_items = filter_identify_array()
    if len(unidentified_items) == 0:
        return
    
    for item_id in unidentified_items:
        bot_vars.identify_action_queue.add_action(identify_item, item_id)

def finished_identifying():
    global bot_vars
    return bot_vars.identify_action_queue.is_empty()


def salvage_item(item_id):
    salvage_kit = Inventory.GetFirstSalvageKit()
    if salvage_kit == 0:
        return
    Inventory.SalvageItem(item_id, salvage_kit)
    
def salvage_items():
    global bot_vars
    salvageable_items = filter_salvage_array()
    if len(salvageable_items) == 0:
        return
    
    for item_id in salvageable_items:
        bot_vars.salvage_action_queue.add_action(salvage_item, item_id)
        
def finished_salvaging():
    global bot_vars
    return bot_vars.salvage_action_queue.is_empty()

#endregion

#region material
def IsMaterial(item_id):
    material_model_ids = {
        ModelID.Wood_Plank,             # 946
        ModelID.Iron_Ingot,             # 948
        ModelID.Pile_Of_Glittering_Dust,# 929
        ModelID.Bone,                   # 921
        ModelID.Bolt_Of_Cloth,          # 925
        ModelID.Granite_Slab            # 955
    }
    return Item.GetModelID(item_id) in material_model_ids
	
def IsGranite(item_id):
    """Check if the item is granite."""
    granite_model_ids = {ModelID.Granite_Slab} # 955
    return Item.GetModelID(item_id) in granite_model_ids
	
def IsWood(item_id):
    """Check if the item is wood."""
    wood_model_ids = {ModelID.Wood_Plank} # 946
    return Item.GetModelID(item_id) in wood_model_ids

def IsIron(item_id):
    """Check if the item is iron."""
    iron_model_ids = {ModelID.Iron_Ingot} # 948
    return Item.GetModelID(item_id) in iron_model_ids

def IsDust(item_id):
    """Check if the item is glittering dust."""
    dust_model_ids = {ModelID.Pile_Of_Glittering_Dust} # 929
    return Item.GetModelID(item_id) in dust_model_ids

def IsBones(item_id):
    """Check if the item is bones."""
    bone_model_ids = {ModelID.Bone} # 921
    return Item.GetModelID(item_id) in bone_model_ids

def IsCloth(item_id):
    """Check if the item is cloth."""
    cloth_model_ids = {ModelID.Bolt_Of_Cloth} # 925
    return Item.GetModelID(item_id) in cloth_model_ids



#endregion



#region Merchant

def get_filtered_materials_to_sell():
    # Get items from the specified bags
    bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    items_to_sell = ItemArray.GetItemArray(bags_to_check)

    # Filter materials first using the centralized definition
    items_to_sell = ItemArray.Filter.ByCondition(items_to_sell, lambda item_id: IsMaterial(item_id))

    # Apply individual material filters
    filtered_items = []
    if bot_vars.config_vars.sell_wood:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsWood))
    if bot_vars.config_vars.sell_iron:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsIron))
    if bot_vars.config_vars.sell_dust:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsDust))
    if bot_vars.config_vars.sell_bones:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsBones))
    if bot_vars.config_vars.sell_cloth:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsCloth))
    if bot_vars.config_vars.sell_granite:
        filtered_items.extend(ItemArray.Filter.ByCondition(items_to_sell, IsGranite))

    return filtered_items
    
def SellMaterials(log=False):
    global bot_vars

    # --- NEW: Define Dye constants ---
    DYE_MODEL_ID = ModelID.Vial_Of_Dye # 146
    BLACK_DYE_COLOR_ID = 10
    WHITE_DYE_COLOR_ID = 12
    # --- END NEW ---

    bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    items = ItemArray.GetItemArray(bags_to_check)

    # STEP 1: Filter out excluded items by model ID
    # --- CORRECTED Enum Names (Except Kits - see note) ---
    EXCLUDED_MODEL_IDS = {
        ModelID.Salvage_Kit,                 # Was 2992
        ModelID.Superior_Identification_Kit, # Was 5899
        ModelID.Lockpick,              # 22751
        ModelID.Glacial_Stone,         # 27047
        ModelID.Hard_Apple_Cider,      # 28435
        ModelID.Slice_Of_Pumpkin_Pie,  # 28436
        ModelID.Hunters_Ale,           # 910
    }
    # Keep items whose ModelID is NOT in the exclusion set
    items = ItemArray.Filter.ByCondition(items, lambda item_id: Item.GetModelID(item_id) not in EXCLUDED_MODEL_IDS)

    # --- NEW: STEP 1.5: Filter out specific Black/White Dyes by Color ID ---
    # Keep items that are NOT (a Dye AND (Black or White))
    # Requires GetDyeColorIdFromItem function to be defined in the script
    items = ItemArray.Filter.ByCondition(items, lambda item_id: not (
            Item.GetModelID(item_id) == DYE_MODEL_ID and
            GetDyeColorIdFromItem(item_id) in {BLACK_DYE_COLOR_ID, WHITE_DYE_COLOR_ID}
    ))
    # --- END NEW ---

    # STEP 2: Remove materials unless user wants to sell them
    if not bot_vars.config_vars.sell_materials:
        items = ItemArray.Filter.ByCondition(items, lambda item_id: not Item.Type.IsMaterial(item_id))
    else:
        # Optionally filter specific material types NOT to sell
        # This logic keeps items that are NOT the specified material type if the corresponding sell flag is False
        material_filters = []
        if not bot_vars.config_vars.sell_wood:
            material_filters.append(IsWood)
        if not bot_vars.config_vars.sell_iron:
            material_filters.append(IsIron)
        if not bot_vars.config_vars.sell_dust:
            material_filters.append(IsDust)
        if not bot_vars.config_vars.sell_bones:
            material_filters.append(IsBones)
        if not bot_vars.config_vars.sell_cloth:
            material_filters.append(IsCloth)
        if not bot_vars.config_vars.sell_granite:
            material_filters.append(IsGranite)

        # Apply the filters: remove items if they match a material type the user wants to keep
        if material_filters: # Only filter if there are materials to keep
            items = ItemArray.Filter.ByCondition(items, lambda item_id: not (
                IsMaterial(item_id) and # Check if it's a material first
                any(filter_fn(item_id) for filter_fn in material_filters) # Check if it matches any 'keep' filter
            ))

    # STEP 3: Filter by rarity settings (remove items of rarities the user doesn't want to sell)
    if not bot_vars.config_vars.sell_whites:
        items = ItemArray.Filter.ByCondition(items, lambda item_id: not Item.Rarity.IsWhite(item_id))
    if not bot_vars.config_vars.sell_blues:
        items = ItemArray.Filter.ByCondition(items, lambda item_id: not Item.Rarity.IsBlue(item_id))
    if not bot_vars.config_vars.sell_purples:
        items = ItemArray.Filter.ByCondition(items, lambda item_id: not Item.Rarity.IsPurple(item_id))

    gold_items_to_store = []
    if not bot_vars.config_vars.sell_golds:
        gold_items_to_store = ItemArray.Filter.ByCondition(items, lambda item_id: Item.Rarity.IsGold(item_id)) # Find golds
        items = ItemArray.Filter.ByCondition(items, lambda item_id: not Item.Rarity.IsGold(item_id)) # Remove golds from sell list

    # STEP 4: Queue remaining items to sell
    # --- MODIFIED: Clear queue before adding new items to prevent duplicates if called multiple times ---
    bot_vars.sell_to_vendor_action_queue.clear()
    # --- END MODIFIED ---
    for item_id in items:
        quantity = Item.Properties.GetQuantity(item_id)
        value = Item.Properties.GetValue(item_id)

        if value == 0:
            if log:
                Py4GW.Console.Log(
                    bot_vars.window_module.module_name,
                    f"[Sell] Skipped item {item_id} (qty: {quantity}) because value is 0",
                    Py4GW.Console.MessageType.Warning
                )
            continue

        # --- NOTE: Verify the correct arguments for SellItem. Using item_id and quantity is typical. ---
        # Original used 'cost = quantity * value'. Adjust if 'quantity' is correct.
        # bot_vars.sell_to_vendor_action_queue.add_action(Trading.Merchant.SellItem, item_id, quantity) # Example using quantity
        bot_vars.sell_to_vendor_action_queue.add_action(Trading.Merchant.SellItem, item_id, quantity * value) # Keeping original 'cost' logic for now

        if log:
            Py4GW.Console.Log(
                bot_vars.window_module.module_name,
                f"[Sell] Queued item {item_id} for sale (qty: {quantity}, value: {value})",
                Py4GW.Console.MessageType.Info
            )

    if log and len(items) == 0: # --- MODIFIED: Check length of 'items' (filtered list), not queue ---
        Py4GW.Console.Log(
            bot_vars.window_module.module_name,
            "[Sell] No items matched filters for sale.",
            Py4GW.Console.MessageType.Info
        )

      
def process_sell_queue():
    global bot_vars

    if bot_vars.sell_to_vendor_action_queue.is_empty():
        # Queue is empty, check if anything needs selling now based on current inventory/settings
        # This populates the queue if needed. Log only if queue was initially empty.
        SellMaterials(log=True)

    # If the queue is not empty (either had items before, or SellMaterials just added some), run the next action.
    # This prevents SellMaterials being called repeatedly if the queue isn't clearing in one go.
    if not bot_vars.sell_to_vendor_action_queue.is_empty():
        bot_vars.sell_to_vendor_action_queue.execute_next()

def SellingMaterialsComplete():
    global bot_vars
    # Selling is considered complete only if the queue is empty.
    # The check to populate the queue now happens reliably inside process_sell_queue.
    return bot_vars.sell_to_vendor_action_queue.is_empty()
    
def DepositItems():
    global bot_vars

    bags_to_check = ItemArray.CreateBagList(1, 2, 3, 4)
    items_to_deposit = ItemArray.GetItemArray(bags_to_check) # Use items_to_deposit from the start

    # 1. Filter out essential kits
    # Using Enums based on last confirmation - verify these match your intent
    banned_kits = {
        ModelID.Superior_Identification_Kit, # 5899 
        ModelID.Salvage_Kit                  # 2992 
    }
    items_to_deposit = ItemArray.Filter.ByCondition(
        items_to_deposit, lambda item_id: Item.GetModelID(item_id) not in banned_kits
    )

    # 2. Filter out specific Event Items / Other items to KEEP in inventory
    banned_event_items = {
         ModelID.Hard_Apple_Cider, ModelID.Slice_Of_Pumpkin_Pie, ModelID.Glacial_Stone,
         ModelID.Bottle_Rocket, ModelID.Honeycomb, ModelID.Sparkler, ModelID.Champagne_Popper,
         ModelID.Victory_Token, ModelID.Birthday_Cupcake, ModelID.Hunters_Ale,
         ModelID.Mesmer_Tome, ModelID.Krytan_Brandy, ModelID.Sugary_Blue_Drink,
         # Add/remove other ModelID constants if needed
    }
    items_to_deposit = ItemArray.Filter.ByCondition(
        items_to_deposit, lambda item_id: Item.GetModelID(item_id) not in banned_event_items
    )

    # --- NEW (From previous recommendation): Filter out Gold items ---
    # Add this filter if you decided you DON'T want to attempt depositing golds
    # because the API call fails. Remove/comment it out if your solution fixed gold deposits.
    # items_to_deposit = ItemArray.Filter.ByCondition(
    #     items_to_deposit, lambda item_id: not Item.Rarity.IsGold(item_id)
    # )
    # --- END NEW ---

    # 3. Clear queue before adding
    bot_vars.deposit_action_queue.clear()

    # 4. Queue remaining items for deposit
    queued_count = 0
    for item_id in items_to_deposit:
        # Using the direct API call as per your last script version
        bot_vars.deposit_action_queue.add_action(Inventory.DepositItemToStorage, item_id) 
        queued_count += 1

    # Keep this final summary log if you find it useful
    Py4GW.Console.Log(bot_vars.window_module.module_name, f"[Deposit] Finished queuing {queued_count} items for deposit.", Py4GW.Console.MessageType.Info)


def DepositItemsComplete():
    return bot_vars.deposit_action_queue.is_empty()
    

def buy_id_kits():
    global bot_vars
    id_kits = bot_vars.config_vars.keep_id_kit
    kits_in_inv = Inventory.GetModelCount(ModelID.Superior_Identification_Kit) # Check 5899 vs keep_id_kit
    kits_to_buy = id_kits - kits_in_inv
    if kits_to_buy <= 0:
        bot_vars.buy_from_vendor_action_queue.clear()
        return
    merchant_item_list = Trading.Merchant.GetOfferedItems()
    merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: Item.GetModelID(item_id) == ModelID.Superior_Identification_Kit) # Buy 5899
    
    

    if len(merchant_item_list) == 0:
        bot_vars.buy_from_vendor_action_queue.clear()
        return

    for i in range(kits_to_buy):
        item_id = merchant_item_list[0]
        value = Item.Properties.GetValue(item_id) * 2 # value reported is sell value not buy value
        bot_vars.buy_from_vendor_action_queue.add_action(Trading.Merchant.BuyItem, item_id, value)

def buy_from_merchant_complete():
    global bot_vars
    return bot_vars.buy_from_vendor_action_queue.is_empty()

def buy_salvage_kits():
    global bot_vars
    salv_kits = bot_vars.config_vars.keep_salvage_kit
    kits_in_inv = Inventory.GetModelCount(ModelID.Salvage_Kit) # Check 2992 vs keep_salvage_kit
    kits_to_buy = salv_kits - kits_in_inv
    if kits_to_buy <= 0:
        bot_vars.buy_from_vendor_action_queue.clear()
        return

    merchant_item_list = Trading.Merchant.GetOfferedItems()
    merchant_item_list = ItemArray.Filter.ByCondition(merchant_item_list, lambda item_id: Item.GetModelID(item_id) == ModelID.Salvage_Kit) # Buy 2992

    if len(merchant_item_list) == 0:
        bot_vars.buy_from_vendor_action_queue.clear()
        return
    
    for i in range(kits_to_buy):
        item_id = merchant_item_list[0]
        value = Item.Properties.GetValue(item_id) * 2 # value reported is sell value not buy value
        bot_vars.buy_from_vendor_action_queue.add_action(Trading.Merchant.BuyItem, item_id, value)

#endregion

#region transition
def config_transition(map_id):
    global bot_vars
    global FSM_vars
    #482 = Bjora Marches
    #546 = Jaga Moraine
    bot_vars.desired_map_id = map_id
    FSM_vars.movement_handler.reset()
    
def transition_to_map(map_id):
    global bot_vars
    if Map.GetMapID() == map_id:
        return True
    return False

#endregion

#region FSM

def reset_farming_loop():
    global FSM_vars
    FSM_vars.outpost_pathing.reset()
    FSM_vars.bjora_pathing.reset()
    FSM_vars.bounty_npc.reset()
    FSM_vars.farming_route.reset()
    FSM_vars.farming_route2.reset()
    FSM_vars.path_to_killing_spot.reset()
    FSM_vars.exit_jaga_moraine.reset()
    FSM_vars.return_jaga_moraine.reset()
    FSM_vars.movement_handler.reset()
    FSM_vars.sell_to_vendor.reset()
    FSM_vars.state_machine.jump_to_state_by_name("Waiting for Jaga Explorable Map Load")
    bot_vars.forced_restart = False
    FSM_vars.in_waiting_routine = False


def handle_end_state_machine():
    global bot_vars
    #bot_vars.window_statistics.lap_timer.Reset()
    inventory_check_result = InventoryCheck() # Store result
    if not inventory_check_result: # If InventoryCheck is FALSE (means inventory IS full / needs handling)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"[Debug] Inventory full or needs handling. Jumping to 'End State Machine Loop' (triggers Outpost return).", Py4GW.Console.MessageType.Info)
        FSM_vars.state_machine.jump_to_state_by_name("End State Machine Loop")
    else: # InventoryCheck is TRUE (means inventory is NOT full / okay to continue)
         Py4GW.Console.Log(bot_vars.window_module.module_name, f"[Debug] Inventory OK. Proceeding to 'Exit Jaga Moraine' state.", Py4GW.Console.MessageType.Info)


def FollowPathwithDelayTimer(path_handler,follow_handler, log_actions=False, delay=50):
            """
            Purpose: Follow a path using the path handler and follow handler objects.
            Args:
                path_handler (PathHandler): The PathHandler object containing the path coordinates.
                follow_handler (FollowXY): The FollowXY object for moving to waypoints.
            Returns: None
            """
            global follow_delay_timer
            
            follow_handler.update()

            if follow_handler.is_following():
                return

            if follow_delay_timer.IsStopped():
                follow_delay_timer.Start()
                return

            if follow_delay_timer.HasElapsed(delay):
                follow_delay_timer.Stop()

                point = path_handler.advance()
                if point is not None:
                    follow_handler.move_to_waypoint(point[0], point[1])
                    if log_actions:
                        Py4GW.Console.Log("FollowPath", f"Moving to {point}", Py4GW.Console.MessageType.Info)


class build:
    deadly_paradox:int = 0
    shadow_form:int = 0
    shroud_of_distress:int = 0
    way_of_perfection:int = 0
    heart_of_shadow:int = 0
    wastrels_worry:int = 0
    arcane_echo:int = 0
    channeling:int = 0

skillbar = build()


#FSM Routine for Locating and following the merchant
FSM_vars.sell_to_vendor.AddState(name="Go to Merchant",
                        execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.path_to_merchant, FSM_vars.movement_handler),
                        exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.path_to_merchant, FSM_vars.movement_handler),
                        run_once=False)
FSM_vars.sell_to_vendor.AddState(name="Target Merchant",
                        execute_fn=lambda: TargetNearestNPCXY(x=-23100,y=14900),
                        transition_delay_ms=1000)
FSM_vars.sell_to_vendor.AddState(name="InteractMerchant",
                        execute_fn=lambda: Routines.Targeting.InteractTarget(),
                        exit_condition=lambda: Routines.Targeting.HasArrivedToTarget())
FSM_vars.sell_to_vendor.AddState(name="Sell Materials to make Space",
                        execute_fn=lambda: SellMaterials(),
                        run_once=True,
                        exit_condition=lambda: SellingMaterialsComplete())
FSM_vars.sell_to_vendor.AddState(name="Buy ID Kits",
                        execute_fn=lambda: buy_id_kits(),
                        run_once=True,
                        exit_condition=lambda: buy_from_merchant_complete())
FSM_vars.sell_to_vendor.AddState(name="Buy Salvage Kits",
                        execute_fn=lambda: buy_salvage_kits(),
                        run_once=True,
                        exit_condition=lambda: buy_from_merchant_complete())
FSM_vars.sell_to_vendor.AddState(name="Identify routine",
                        execute_fn=lambda: identify_items(),
                        run_once=True,
                        exit_condition=lambda: finished_identifying())
FSM_vars.sell_to_vendor.AddState(name="Salvage routine",
                        execute_fn=lambda: salvage_items(),
                        run_once=True,
                        exit_condition=lambda: finished_salvaging())
FSM_vars.sell_to_vendor.AddState(name="Sell Materials",
                        execute_fn=lambda: process_sell_queue(),
                        run_once=False,
                        exit_condition=lambda: SellingMaterialsComplete())

FSM_vars.sell_to_vendor.AddState(name="Deposit Gold",
                                 execute_fn=lambda: DepositGold(),
                                 run_once=True, # Only needs to run once per visit
                                 exit_condition=lambda: True, # Assume DepositGold is quick
                                 transition_delay_ms=500) # Small delay after depositing

FSM_vars.sell_to_vendor.AddState(name="Deposit Items",
                        execute_fn=lambda: DepositItems(),
                        run_once=True,
                        exit_condition=lambda: DepositItemsComplete())




                        


#MAIN STATE MACHINE CONFIGURATION
FSM_vars.state_machine.AddState(name="Longeyes Ledge Map Check", 
                       execute_fn=lambda: TravelToOutpost(bot_vars.starting_map), #the Code to run
                       exit_condition=lambda: HasArrivedToOutpost(bot_vars.starting_map), #the condition that needs to be true to continue
                       run_once=True, #we only want to run this once
                       transition_delay_ms=1000) #interval or delay to check the condition
FSM_vars.state_machine.AddState(name="Load SkillBar",
                       execute_fn=lambda: LoadSkillBar(),
                       transition_delay_ms=1000,
                       exit_condition=lambda: IsSkillBarLoaded())
FSM_vars.state_machine.AddState(name="Set Hard Mode",
                       execute_fn=lambda: Party.SetHardMode(),
                       transition_delay_ms=1000)
FSM_vars.state_machine.AddSubroutine(name="Sell at Outpost",
                        sub_fsm=FSM_vars.sell_to_vendor,
                        condition_fn=lambda: Map.GetMapID() == bot_vars.starting_map)
FSM_vars.state_machine.AddState(name="Leaving Outpost",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.outpost_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.outpost_pathing, FSM_vars.movement_handler) or transition_to_map(482),
                       run_once=False) #run once is false because we want to keep updating the pathing objects
FSM_vars.state_machine.AddState(name="Waiting for Bjora Explorable Map Load",
                       execute_fn=lambda: config_transition(482),
                       exit_condition=lambda: transition_to_map(482),
                       transition_delay_ms=1000)
FSM_vars.state_machine.AddState(name="Traverse Bjora Marches",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.bjora_pathing, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.bjora_pathing, FSM_vars.movement_handler) or transition_to_map(546),
                       run_once=False)
FSM_vars.state_machine.AddState(name="Waiting for Jaga Explorable Map Load",
                       execute_fn=lambda: config_transition(546),
                       run_once=True,
                       exit_condition=lambda: transition_to_map(546),
                       transition_delay_ms=1000)
FSM_vars.state_machine.AddState(name="Log run start",
                       execute_fn=lambda: log_run_start(),
                       run_once=True)
FSM_vars.state_machine.AddState(name="Check Norn Title",
                       execute_fn=lambda: check_norn_title(),
                       run_once=True)
FSM_vars.state_machine.AddState(name="Go to NPC",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.bounty_npc, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.bounty_npc, FSM_vars.movement_handler),
                       run_once=False)
FSM_vars.state_machine.AddState(name="Target NPC",
                       execute_fn=lambda: TargetNearestNPC(),
                       transition_delay_ms=1000)
FSM_vars.state_machine.AddState(name="Interact NPC",
                       execute_fn=lambda: Routines.Targeting.InteractTarget(),
                       transition_delay_ms=500)
FSM_vars.state_machine.AddState(name="Take Bounty",
                       execute_fn=lambda: Player.SendDialog(int("0x84", 16)),
                       transition_delay_ms=500)
FSM_vars.state_machine.AddState(name="Route Aggro Left",
                       execute_fn=lambda: FollowPathwithDelayTimer(FSM_vars.farming_route, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.farming_route, FSM_vars.movement_handler),
                       run_once=False)
FSM_vars.state_machine.AddState(name="Waiting for Left Aggro Ball",
                       execute_fn=lambda: set_waiting_routine(),
                       transition_delay_ms=15000,
                       exit_condition=lambda: end_waiting_routine())
FSM_vars.state_machine.AddState(name="Route Aggro Right",
                       execute_fn=lambda: FollowPathwithDelayTimer(FSM_vars.farming_route2, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.farming_route2, FSM_vars.movement_handler),
                       run_once=False)
FSM_vars.state_machine.AddState(name="Waiting for Right Aggro Ball",
                       execute_fn=lambda: set_waiting_routine(),
                       transition_delay_ms=15000,
                       exit_condition=lambda: end_waiting_routine())
FSM_vars.state_machine.AddState(name="Moving to kill spot",
                       execute_fn=lambda: FollowPathwithDelayTimer(FSM_vars.path_to_killing_spot, FSM_vars.exact_movement_handler,delay=500),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.path_to_killing_spot, FSM_vars.exact_movement_handler),
                       run_once=False)
FSM_vars.state_machine.AddState(name="Killing Routine",
                       execute_fn=lambda: set_killing_routine(),
                       transition_delay_ms=1000,
                       exit_condition=lambda: end_killing_routine())
FSM_vars.state_machine.AddState(name="Loot routine",
                       execute_fn=lambda: loot_items(),
                       run_once=False,
                       exit_condition=lambda: finished_looting())
FSM_vars.state_machine.AddState(name="Identify routine",
                       execute_fn=lambda: identify_items(),
                       run_once=True,
                       exit_condition=lambda: finished_identifying())
FSM_vars.state_machine.AddState(name="Salvage routine",
                        execute_fn=lambda: salvage_items(),
                        run_once=True,
                        exit_condition=lambda: finished_salvaging())
FSM_vars.state_machine.AddState(name="Need to return to Outpost?",
                       execute_fn=lambda: handle_end_state_machine(),
                       exit_condition=lambda: InventoryCheck())
FSM_vars.state_machine.AddState(name="Exit Jaga Moraine",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.exit_jaga_moraine, FSM_vars.movement_handler),
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.exit_jaga_moraine, FSM_vars.movement_handler) or transition_to_map(482),
                       run_once=False)
FSM_vars.state_machine.AddState(name="Waiting for Bjora Explorable Map Load 2",
                       execute_fn=lambda: config_transition(482),
                       exit_condition=lambda: transition_to_map(482),
                       transition_delay_ms=1000)
FSM_vars.state_machine.AddState(name="Return To Jaga Moraine",
                       execute_fn=lambda: Routines.Movement.FollowPath(FSM_vars.return_jaga_moraine, FSM_vars.movement_handler),  
                       exit_condition=lambda: Routines.Movement.IsFollowPathFinished(FSM_vars.return_jaga_moraine, FSM_vars.movement_handler) or transition_to_map(546),
                       run_once=False)
FSM_vars.state_machine.AddState(name="Waiting for Jaga Moraine Explorable Map Load 2",
                       execute_fn=lambda: config_transition(546),
                       exit_condition=lambda: transition_to_map(546),
                       transition_delay_ms=1000)
FSM_vars.state_machine.AddState(name="reset Farming Loop",
                       execute_fn=lambda: reset_farming_loop(),
                       transition_delay_ms=2000)
FSM_vars.state_machine.AddState(name="End State Machine Loop",
                       execute_fn=lambda: ResetEnvironment(),
                       transition_delay_ms=1000)
FSM_vars.state_machine.AddState(name="Extra Bonus Step",
                       execute_fn=lambda: StopBot(),
                       transition_delay_ms=1000)
#enregion

#region SkillCasting

################## SKILL HANDLING ROUTINES ##################
class GameAreas:
    def __init__(self):
        self.Touch = 144
        self.Adjacent = 166
        self.Nearby = 252
        self.Area = 322
        self.Earshot = 1012  #aggro bubble
        self.Spellcast = 1248
        self.Spirit = 2500
        self.Compass = 5000

area_distance = GameAreas()



def CanCast():
    player_agent_id = Player.GetAgentID()

    if (
        Agent.IsCasting(player_agent_id) 
        or Agent.GetCastingSkill(player_agent_id) != 0
        or Agent.IsKnockedDown(player_agent_id)
        or Agent.IsDead(player_agent_id)
        or SkillBar.GetCasting() != 0
    ):
        return False
    return True

def GetEnergyAgentCost(skill_id, agent_id):
    """Retrieve the actual energy cost of a skill by its ID and effects.

    Args:
        skill_id (int): ID of the skill.
        agent_id (int): ID of the agent (player or hero).

    Returns:
        float: Final energy cost after applying all effects.
              Values are rounded to integers.
              Minimum cost is 0 unless otherwise specified by an effect.
    """
    # Get base energy cost for the skill
    cost = Skill.skill_instance(skill_id).energy_cost

    # Adjust base cost for special cases (API inconsistencies)
    if cost == 11:
        cost = 15    # True cost is 15
    elif cost == 12:
        cost = 25    # True cost is 25

    # Get all active effects on the agent
    player_effects = Effects.GetEffects(agent_id)

    # Process each effect in order of application
    # Effects are processed in this specific order to match game mechanics
    for effect in player_effects:
        effect_id = effect.skill_id
        attr = Effects.EffectAttributeLevel(agent_id, effect_id)

        match effect_id:
            case 469:  # Primal Echoes - Forces Signets to cost 10 energy
                if Skill.Flags.IsSignet(skill_id):
                    cost = 10  # Fixed cost regardless of other effects
                    continue  # Allow other effects to modify this cost

            case 475:  # Quickening Zephyr - Increases energy cost by 30%
                cost *= 1.30   # Using multiplication instead of addition for better precision
                continue

            case 1725:  # Roaring Winds - Increases Shout/Chant cost based on attribute level
                if Skill.Flags.IsChant(skill_id) or Skill.Flags.IsShout(skill_id):
                    match attr:
                        case a if 0 < a <= 1:
                            cost += 1
                        case a if 2 <= a <= 5:
                            cost += 2
                        case a if 6 <= a <= 9:
                            cost += 3
                        case a if 10 <= a <= 13:
                            cost += 4
                        case a if 14 <= a <= 16:
                            cost += 5
                        case a if 17 <= a <= 20:
                            cost += 6
                    continue

            case 1677:  # Veiled Nightmare - Increases all costs by 40%
                cost *= 1.40
                continue

            case 856:  # "Kilroy Stonekin" - Reduces all costs by 50%
                cost *= 0.50
                continue

            case 1115:  # Air of Enchantment
                if Skill.Flags.IsEnchantment(skill_id):
                    cost -= 5
                continue

            case 1223:  # Anguished Was Lingwah
                if Skill.Flags.IsHex(skill_id) and Skill.GetProfession(skill_id)[0] == 8:
                    match attr:
                        case a if 0 < a <= 1:
                            cost -= 1
                        case a if 2 <= a <= 5:
                            cost -= 2
                        case a if 6 <= a <= 9:
                            cost -= 3
                        case a if 10 <= a <= 13:
                            cost -= 4
                        case a if 14 <= a <= 16:
                            cost -= 5
                        case a if 17 <= a <= 20:
                            cost -= 6
                        case a if a > 20:
                            cost -= 7
                    continue

            case 1220:  # Attuned Was Songkai
                if Skill.Flags.IsSpell(skill_id) or Skill.Flags.IsRitual(skill_id):
                    percentage = 5 + (attr * 3) if attr <= 20 else 68
                    cost -= cost * (percentage / 100)
                continue

            case 596:  # Chimera of Intensity
                cost -= cost * 0.50
                continue

            case 806:  # Cultist's Fervor
                if Skill.Flags.IsSpell(skill_id) and Skill.GetProfession(skill_id)[0] == 4:
                    match attr:
                        case a if 0 < a <= 1:
                            cost -= 1
                        case a if 2 <= a <= 4:
                            cost -= 2
                        case a if 5 <= a <= 7:
                            cost -= 3
                        case a if 8 <= a <= 10:
                            cost -= 4
                        case a if 11 <= a <= 13:
                            cost -= 5
                        case a if 14 <= a <= 16:
                            cost -= 6
                        case a if 17 <= a <= 19:
                            cost -= 7
                        case a if a > 19:
                            cost -= 8
                    continue

            case 310:  # Divine Spirit
                if Skill.Flags.IsSpell(skill_id) and Skill.GetProfession(skill_id)[0] == 3:
                    cost -= 5
                continue

            case 1569:  # Energizing Chorus
                if Skill.Flags.IsChant(skill_id) or Skill.Flags.IsShout(skill_id):
                    match attr:
                        case a if 0 < a <= 1:
                            cost -= 3
                        case a if 2 <= a <= 5:
                            cost -= 4
                        case a if 6 <= a <= 9:
                            cost -= 5
                        case a if 10 <= a <= 13:
                            cost -= 6
                        case a if 14 <= a <= 16:
                            cost -= 7
                        case a if 17 <= a <= 20:
                            cost -= 8
                        case a if a > 20:
                            cost -= 9
                    continue

            case 474:  # Energizing Wind
                if cost >= 15:
                    cost -= 15
                else:
                    cost = 0
                continue

            case 2145:  # Expert Focus
                if Skill.Flags.IsAttack(skill_id) and Skill.Data.GetWeaponReq(skill_id) == 2:
                    match attr:
                        case a if 0 < a <= 7:
                            cost -= 1
                        case a if a > 8:
                            cost -= 2
                        

            case 199:  # Glyph of Energy
                if Skill.Flags.IsSpell(skill_id):
                    if attr == 0:
                        cost -= 10
                    else:
                        cost -= (10 + attr)

            case 200:  # Glyph of Lesser Energy
                if Skill.Flags.IsSpell(skill_id):
                    match attr:
                        case 0:
                            cost -= 10
                        case a if 1 <= a <= 2:
                            cost -= 11
                        case a if 3 <= a <= 4:
                            cost -= 12
                        case a if 5 <= a <= 6:
                            cost -= 13
                        case a if 7 <= a <= 8:
                            cost -= 14
                        case a if 9 <= a <= 10:
                            cost -= 15
                        case a if 11 <= a <= 12:
                            cost -= 16
                        case a if 13 <= a <= 14:
                            cost -= 17
                        case 15:
                            cost -= 18
                        case a if 16 <= a <= 16:
                            cost -= 19
                        case a if 17 <= a <= 18:
                            cost -= 20
                        case a if a >= 20:
                            cost -= 21

            case 1394:  # Healer's Covenant
                if Skill.Flags.IsSpell(skill_id) and Skill.Attribute.GetAttribute(skill_id) == 15:
                    match attr:
                        case a if 0 < a <= 3:
                            cost -= 1
                        case a if 4 <= a <= 11:
                            cost -= 2
                        case a if 12 <= a <= 18:
                            cost -= 3
                        case a if a >= 19:
                            cost -= 4

            case 763:  # Jaundiced Gaze
                if Skill.Flags.IsEnchantment(skill_id):
                    match attr:
                        case 0:
                            cost -= 1
                        case a if 1 <= a <= 2:
                            cost -= 2
                        case a if 3 <= a <= 4:
                            cost -= 3
                        case 5:
                            cost -= 4
                        case a if 6 <= a <= 7:
                            cost -= 5
                        case a if 8 <= a <= 9:
                            cost -= 6
                        case 10:
                            cost -= 7
                        case a if 11 <= a <= 12:
                            cost -= 8
                        case a if 13 <= a <= 14:
                            cost -= 9
                        case 15:
                            cost -= 10
                        case a if 16 <= a <= 17:
                            cost -= 11
                        case a if 18 <= a <= 19:
                            cost -= 12
                        case 20:
                            cost -= 13
                        case a if a > 20:
                            cost -= 14

            case 1739:  # Renewing Memories
                if Skill.Flags.IsItemSpell(skill_id) or Skill.Flags.IsWeaponSpell(skill_id):
                    percentage = 5 + (attr * 2) if attr <= 20 else 47
                    cost -= cost * (percentage / 100)

            case 1240:  # Soul Twisting
                if Skill.Flags.IsRitual(skill_id):
                    cost = 10  # Fixe le coût à 10

            case 987:  # Way of the Empty Palm
                if Skill.Data.GetCombo(skill_id) == 2 or Skill.Data.GetCombo(skill_id) == 3:  # Attaque double ou secondaire
                    cost = 0

    cost = max(0, cost)
    return cost


def HasEnoughEnergy(skill_id):
    player_agent_id = Player.GetAgentID()
    energy = Agent.GetEnergy(player_agent_id)
    max_energy = Agent.GetMaxEnergy(player_agent_id)
    energy_points = int(energy * max_energy)

    return GetEnergyAgentCost(skill_id, player_agent_id) <= energy_points


def HasBuff(agent_id, skill_id):
    if Effects.BuffExists(agent_id, skill_id) or Effects.EffectExists(agent_id, skill_id):
        return True
    return False

def IsSkillReady(skill_id):
    skill = SkillBar.GetSkillData(SkillBar.GetSlotBySkillID(skill_id))
    recharge = skill.recharge
    return recharge == 0

def IsSkillReady2(skill_slot):
    skill = SkillBar.GetSkillData(skill_slot)
    return skill.recharge == 0

target = None
def IsEnemyBehind (agent_id):
    global target
    player_agent_id = Player.GetAgentID()
    player_x, player_y = Agent.GetXY(player_agent_id)
    player_angle = Agent.GetRotationAngle(player_agent_id)  # Player's facing direction
    nearest_enemy = agent_id
    if target is None and Agent.IsValid(nearest_enemy):
        Player.ChangeTarget(nearest_enemy)
        target = nearest_enemy
    nearest_enemy_x, nearest_enemy_y = Agent.GetXY(nearest_enemy)
                

    # Calculate the angle between the player and the enemy
    dx = nearest_enemy_x - player_x
    dy = nearest_enemy_y - player_y
    angle_to_enemy = math.atan2(dy, dx)  # Angle in radians
    angle_to_enemy = math.degrees(angle_to_enemy)  # Convert to degrees
    angle_to_enemy = (angle_to_enemy + 360) % 360  # Normalize to [0, 360]

    # Calculate the relative angle to the enemy
    angle_diff = (angle_to_enemy - player_angle + 360) % 360

    if angle_diff < 90 or angle_diff > 270:
        return True
    return False

def CastSkill (skill_id):
    global bot_vars
    SkillBar.UseSkill(SkillBar.GetSlotBySkillID(skill_id))
    #Py4GW.Console.Log(bot_vars.window_module.module_name, f"Cast {Skill.GetName(skill_id)}, slot: {SkillBar.GetSlotBySkillID(skill_id)}", Py4GW.Console.MessageType.Info)
 
def CastSkill2(skill_slot):
    global bot_vars
    SkillBar.UseSkill(skill_slot)
    #Py4GW.Console.Log(bot_vars.window_module.module_name, f"Cast {Skill.GetName(SkillBar.GetSkillIDBySlot(skill_slot))}, slot: {skill_slot}", Py4GW.Console.MessageType.Info)

def assign_skill_ids():
    global skillbar
    skillbar.deadly_paradox = SkillBar.GetSkillIDBySlot(1)
    skillbar.shadow_form = SkillBar.GetSkillIDBySlot(2)
    skillbar.shroud_of_distress = SkillBar.GetSkillIDBySlot(3)
    skillbar.way_of_perfection = SkillBar.GetSkillIDBySlot(4)
    skillbar.heart_of_shadow = SkillBar.GetSkillIDBySlot(5)
    skillbar.wastrels_worry = SkillBar.GetSkillIDBySlot(6)
    skillbar.arcane_echo = SkillBar.GetSkillIDBySlot(7)
    skillbar.channeling = SkillBar.GetSkillIDBySlot(8)

def check_norn_title():
    norntitle = Player.GetTitle(41)
    if norntitle.current_points > 160000:
        FSM_vars.state_machine.jump_to_state_by_name("Route Aggro Left")

def BjoraRunningSkillbar():
    global area_distance, skillbar, aftercast, target

    assign_skill_ids()

    # Are we in danger?
    player_agent_id = Player.GetAgentID()
    player_x, player_y = Agent.GetXY(player_agent_id)
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), area_distance.Earshot)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

    sf_buff_remaining_time = 0

    player_buffs = Effects.GetEffects(player_agent_id)
                
    for buff in player_buffs:
        if buff.skill_id == skillbar.shadow_form:
            sf_buff_remaining_time = buff.time_remaining

    if len(enemy_array) == 0:
        target = None
                
    if len(enemy_array) > 0:
        # If we are in danger, use Deadly Paradox / Shadow Form
            
        if sf_buff_remaining_time < 3500:
            if HasEnoughEnergy(skillbar.deadly_paradox) and not HasBuff(player_agent_id,skillbar.deadly_paradox) and IsSkillReady(skillbar.deadly_paradox):
                CastSkill(skillbar.deadly_paradox)
                return
            
        if HasEnoughEnergy(skillbar.deadly_paradox) and not HasBuff(player_agent_id,skillbar.deadly_paradox) and IsSkillReady(skillbar.deadly_paradox):
            CastSkill(skillbar.deadly_paradox)
            return

        if HasEnoughEnergy(skillbar.shadow_form) and not HasBuff(player_agent_id,skillbar.shadow_form) and IsSkillReady(skillbar.shadow_form):
            CastSkill(skillbar.shadow_form)
            return

        #check if nearest is behind us for escaping with Heart of Shadow
                
        if ((HasEnoughEnergy(skillbar.heart_of_shadow) and IsEnemyBehind(enemy_array[0]) and IsSkillReady(skillbar.heart_of_shadow)) and FSM_vars.non_movement_timer.HasElapsed(4500)):
            CastSkill(skillbar.heart_of_shadow)
            return   
                           
    # Keep Shroud of Distress up if Injured
    if (
        not HasBuff(player_agent_id, skillbar.shroud_of_distress) 
        and IsSkillReady(skillbar.shroud_of_distress)
        and Agent.GetHealth(player_agent_id) < 0.33
        and HasEnoughEnergy(skillbar.shroud_of_distress) 
    ):
        CastSkill(skillbar.shroud_of_distress)
        return
def cast_hos():
        player_agent_id = Player.GetAgentID()
        player_x, player_y = Agent.GetXY(player_agent_id)
        enemy_array = AgentArray.GetEnemyArray()
        enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), area_distance.Earshot)
        enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

        if enemy_array:
            target = enemy_array[0]
        else:
            target = player_agent_id

        has_energy = HasEnoughEnergy(skillbar.heart_of_shadow)
        low_health = Agent.GetHealth(player_agent_id) < 0.25
        skill_ready = IsSkillReady(skillbar.heart_of_shadow)
        stuck_too_long = FSM_vars.stuck_count > 3
        not_moving = FSM_vars.non_movement_timer.HasElapsed(10000)

        if not FSM_vars.in_killing_routine and has_energy and skill_ready:
            if low_health:
                Player.ChangeTarget(player_agent_id)
                CastSkill(skillbar.heart_of_shadow)
                return
            if stuck_too_long:
                Player.ChangeTarget(enemy_array[0])
                CastSkill(skillbar.heart_of_shadow)
                return
            if not_moving and not FSM_vars.in_waiting_routine:
                Player.ChangeTarget(enemy_array[0])
                CastSkill(skillbar.heart_of_shadow) 
                return
            return
            

def FarmingSkillbar():
    global area_distance, skillbar, aftercast, target
    global FSM_vars

    assign_skill_ids()


    player_agent_id = Player.GetAgentID()
    player_x, player_y = Agent.GetXY(player_agent_id)

    sf_buff_remaining_time = 0

    player_buffs = Effects.GetEffects(player_agent_id)
                
    for buff in player_buffs:
        if buff.skill_id == skillbar.shadow_form:
            sf_buff_remaining_time = buff.time_remaining

    cast_hos()

    if HasBuff(player_agent_id, skillbar.arcane_echo):
        CastSkill(skillbar.wastrels_worry)
        return

    if (
        IsSkillReady(skillbar.shroud_of_distress)
        and HasEnoughEnergy(skillbar.shroud_of_distress)
    ):
        CastSkill(skillbar.shroud_of_distress)
        return

    #keep Channeling up
    if (
        not HasBuff(player_agent_id, skillbar.channeling)
        and IsSkillReady(skillbar.channeling)
        and HasEnoughEnergy(skillbar.channeling)
    ):
        CastSkill(skillbar.channeling)
        return

    #keep Way of Perfection up
    if (
        IsSkillReady(skillbar.way_of_perfection)
        and HasEnoughEnergy(skillbar.way_of_perfection)
    ): 
        CastSkill(skillbar.way_of_perfection)
        return

    #combat routine
    if FSM_vars.in_killing_routine:
        not_hexed_array = AgentArray.GetEnemyArray()
        not_hexed_array = AgentArray.Filter.ByDistance(not_hexed_array, (player_x, player_y), area_distance.Area)
        not_hexed_array = AgentArray.Filter.ByAttribute(not_hexed_array, 'IsAlive')
        not_hexed_array = AgentArray.Filter.ByAttribute(not_hexed_array, 'IsHexed',negate=True)

        if len(not_hexed_array) > 0 and sf_buff_remaining_time > 5000:
            if SkillBar.GetSkillIDBySlot(7) == skillbar.arcane_echo and IsSkillReady2(7) and IsSkillReady2(6) and HasEnoughEnergy(skillbar.arcane_echo):
                CastSkill2(7)
                return
                                              
            if IsSkillReady2(6) and HasEnoughEnergy(skillbar.wastrels_worry):
                Player.ChangeTarget(not_hexed_array[0])
                CastSkill2(6)
                return
            
            if SkillBar.GetSkillIDBySlot(7) == skillbar.wastrels_worry and IsSkillReady2(7) and HasEnoughEnergy(skillbar.wastrels_worry):
                Player.ChangeTarget(not_hexed_array[0])
                CastSkill2(7)
                return
    
    #making sure Wastrels gets echoed properly



    # Are we in or about to be in danger?
            
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), area_distance.Spellcast)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')


            


    if len(enemy_array) == 0:
        target = None
                
    if len(enemy_array) > 0:
        # If we are in danger, use Deadly Paradox / Shadow Form
                

        if sf_buff_remaining_time < 3500:
            if HasEnoughEnergy(skillbar.deadly_paradox) and not HasBuff(player_agent_id,skillbar.deadly_paradox) and IsSkillReady(skillbar.deadly_paradox):
                CastSkill(skillbar.deadly_paradox)
                return

            if IsSkillReady(skillbar.shadow_form) and HasEnoughEnergy(skillbar.shadow_form):
                CastSkill(skillbar.shadow_form)
                return

        # has_energy = HasEnoughEnergy(skillbar.heart_of_shadow)
        # low_health = Agent.GetHealth(player_agent_id) < 0.25
        # skill_ready = IsSkillReady(skillbar.heart_of_shadow)
        # stuck_too_long = FSM_vars.stuck_count > 3
        # not_moving = FSM_vars.non_movement_timer.HasElapsed(10000)


        # if not FSM_vars.in_killing_routine and has_energy and skill_ready:
        #     if low_health:
        #         print("Low health, using Hos")
        #         Player.ChangeTarget(player_agent_id)
        #         CastSkill(skillbar.heart_of_shadow)
        #         return
        #     elif stuck_too_long:
        #         print("Stuck counter, using hos")
        #         Player.ChangeTarget(enemy_array[0])
        #         CastSkill(skillbar.heart_of_shadow)
        #         return
        #     elif not_moving and not FSM_vars.in_waiting_routine:
        #         print("Not moving, using hos")
        #         Player.ChangeTarget(enemy_array[0])
        #         CastSkill(skillbar.heart_of_shadow) 
        #         return
        # if (
        #     not FSM_vars.in_killing_routine and has_energy and (
        #         (low_health and skill_ready) or
        #         stuck_too_long or
        #         (not_moving and not FSM_vars.in_waiting_routine)
        #     )
        # ):
        #     print("In hos block")
        #     if FSM_vars.in_waiting_routine and low_health:
        #         Player.ChangeTarget(Player.GetAgentID())  # hos self
        #         CastSkill(skillbar.heart_of_shadow)
        #         return
        #     else:
        #         Player.ChangeTarget(enemy_array[0])  # hos enemy
        #         CastSkill(skillbar.heart_of_shadow)
        #         return


    
def stay_alive():
    sf_time_remaining = 0
    player = Player.GetAgentID()
    player_buffs = Effects.GetEffects(player)
    for buff in player_buffs:
        if buff.skill_id == skillbar.shadow_form:
            sf_time_remaining = buff.time_remaining
    x,y = Player.GetXY()
    enemyarray = AgentArray.GetEnemyArray()
    enemyarray = AgentArray.Filter.ByDistance(enemyarray, (x, y), area_distance.Spellcast)
    enemyarray = AgentArray.Filter.ByAttribute(enemyarray, 'IsAlive')

    if enemyarray:
        if sf_time_remaining < 3500:
                if HasEnoughEnergy(skillbar.deadly_paradox) and not HasBuff(player,skillbar.deadly_paradox) and IsSkillReady(skillbar.deadly_paradox):
                    CastSkill(skillbar.deadly_paradox)
                    return

                if IsSkillReady(skillbar.shadow_form) and HasEnoughEnergy(skillbar.shadow_form):
                    CastSkill(skillbar.shadow_form)
                    return

            
def HandleSkillbar():
    if (Map.IsMapReady() and not Map.IsMapLoading()):
        if (
            Map.IsExplorable() 
            and Party.IsPartyLoaded()
            and CanCast()
        ):
            if FSM_vars.state_machine.get_current_step_name() == "Loot routine":
                stay_alive()
            if Map.GetMapID() == 482: #Bjora Marches
                BjoraRunningSkillbar()
            if Map.GetMapID() == 546 and FSM_vars.state_machine.get_current_step_name() != "Loot routine": #Jaga Moraine 
                FarmingSkillbar()


def get_escape_location(scaling_factor=50):
    """
    Moves the player to a calculated escape location based on enemy repulsion.
    
    Args:
        scaling_factor (float): Factor to scale the escape vector magnitude. Default is 5.
    
    Returns:
        tuple: The escape destination (x, y).
    """
    # Get the player's current position
    player_x, player_y = Player.GetXY()
    
    # Initialize VectorFields with the player's position
    vector_fields = Utils.VectorFields(probe_position=(player_x, player_y))

    # Get and filter the enemy array
    enemy_array = AgentArray.GetEnemyArray()
    enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), area_distance.Area)
    enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')
    
    # Configure the enemy array and add it to the vector fields
    agent_arrays = [
        {
            'name': 'enemies',
            'array': enemy_array,
            'radius': area_distance.Area,  # Use the appropriate range
            'is_dangerous': True  # Enemies are repulsive (dangerous)
        }
    ]
    
    # Generate the escape vector
    escape_vector = vector_fields.generate_escape_vector(agent_arrays)
    
    # Scale the escape vector
    scaled_escape_vector = (
        escape_vector[0] * scaling_factor,
        escape_vector[1] * scaling_factor
    )
    
    # Calculate the destination coordinates
    destination = (
        player_x - scaled_escape_vector[0],
        player_y - scaled_escape_vector[1]
    )
 
    # Return the destination for reference
    return destination
#endregion
    

overlay = Overlay()

#region window
def DrawWindow():
    global bot_vars, FSM_vars, overlay

    try:
        if bot_vars.window_module.first_run:
            PyImGui.set_next_window_size(bot_vars.window_module.window_size[0], bot_vars.window_module.window_size[1])     
            PyImGui.set_next_window_pos(bot_vars.window_module.window_pos[0], bot_vars.window_module.window_pos[1])
            bot_vars.window_module.first_run = False

        if PyImGui.begin(bot_vars.window_module.window_name, bot_vars.window_module.window_flags):
            # Start a nested table for controls
            if PyImGui.begin_table("ControlTable", 2):
                # Row 1: Control
                PyImGui.table_next_row()
                PyImGui.table_next_column()
                PyImGui.text("Control")
                PyImGui.table_next_column()

                if IsBotStarted():
                    if PyImGui.button("Stop Routine"):
                        ResetEnvironment()
                        StopBot()
                else:
                    if PyImGui.button("Start Routine"):
                        ResetEnvironment()
                        StartBot()

                # Row 4: Progress
                PyImGui.table_next_row()
                PyImGui.table_next_column() 
                # End the nested ControlTable
                PyImGui.end_table()

                outpost_handling_target = FSM_vars.state_machine.get_state_number_by_name("Waiting for Bjora Explorable Map Load")
                current_state = FSM_vars.state_machine.get_current_state_number()
                current_step_progress = 0
                macro_step_name = "Outpost Handling"
                bar_name = "Outpost Handling Progress Bar"

                if current_state < outpost_handling_target:
                    outpost_handling_target += FSM_vars.sell_to_vendor.get_state_count()
                    bar_name = FSM_vars.state_machine.get_current_step_name()
                    if FSM_vars.sell_to_vendor.is_started():
                        current_step_progress = FSM_vars.state_machine.get_current_state_number() + FSM_vars.sell_to_vendor.get_current_state_number() 
                        bar_name = FSM_vars.sell_to_vendor.get_current_step_name()
                    if FSM_vars.sell_to_vendor.is_finished():
                        current_step_progress = outpost_handling_target + FSM_vars.sell_to_vendor.get_state_count()
                else:
                    outpost_handling_target = FSM_vars.state_machine.get_state_number_by_name("Traverse Bjora Marches")
                    macro_step_name = "Traverse Bjora Marches"
                    if current_state == outpost_handling_target:
                        current_step_progress = FSM_vars.bjora_pathing.get_position()
                        outpost_handling_target = FSM_vars.bjora_pathing.get_position_count()
                        bar_name = "Running"
                    else:
                        outpost_handling_target = FSM_vars.state_machine.get_state_number_by_name("Log Run Start")
                        if current_state >= outpost_handling_target:
                            macro_step_name = "Farming"
                            current_step_progress = FSM_vars.state_machine.get_current_state_number() - outpost_handling_target
                            outpost_handling_target = FSM_vars.state_machine.get_state_count() - outpost_handling_target -12 
                            bar_name = FSM_vars.state_machine.get_current_step_name()


                PyImGui.text(f"Current Step: {macro_step_name}")
                PyImGui.progress_bar(current_step_progress/outpost_handling_target, -1, bar_name)

                #bot_vars.show_visual_path = PyImGui.checkbox("Show Visual Path", bot_vars.show_visual_path)
                bot_vars.show_visual_path = False
                if bot_vars.show_visual_path:
                    start = FSM_vars.bjora_pathing.get_position()
                    end = FSM_vars.bjora_pathing.get_position_count()
                    drawing_path = bjora_coord_list[start:end]
                    for i in range(len(drawing_path) - 1):
                        x1,y1 = drawing_path[i]
                        z1 = overlay.FindZ(x1, y1)
                        x2,y2 = drawing_path[i + 1]
                        z2 = overlay.FindZ(x2, y2)
                        pos1 = PyOverlay.Point3D(x1, y1, z1)
                        pos2 = PyOverlay.Point3D(x2, y2, z2)
                        #overlay.DrawLine3D(pos1, pos2,0xFFFFFFFF, 2.0)

            if PyImGui.collapsing_header("Config"):
                # Identification Section
                if PyImGui.tree_node("Identification"):
                    if PyImGui.tree_node("Rarities"):
                        bot_vars.config_vars.id_whites = PyImGui.checkbox("White Items", bot_vars.config_vars.id_whites)
                        bot_vars.config_vars.id_blues = PyImGui.checkbox("Blue Items", bot_vars.config_vars.id_blues)
                        bot_vars.config_vars.id_purples = PyImGui.checkbox("Purple Items", bot_vars.config_vars.id_purples)
                        bot_vars.config_vars.id_golds = PyImGui.checkbox("Gold Items", bot_vars.config_vars.id_golds)
                        PyImGui.tree_pop()
                    PyImGui.tree_pop()

                # Loot Section
                if PyImGui.tree_node("Loot"):
                    if PyImGui.tree_node("Lockpicks"):
                        bot_vars.config_vars.loot_lockpicks = PyImGui.checkbox("Lockpicks", bot_vars.config_vars.loot_lockpicks)
                        if bot_vars.config_vars.loot_lockpicks:  
                            PyImGui.tree_pop()
                            
                        if PyImGui.tree_node("White Dyes"):
                            bot_vars.config_vars.loot_white_dyes = PyImGui.checkbox("White Dyes", bot_vars.config_vars.loot_white_dyes)
                            if bot_vars.config_vars.loot_white_dyes: 
                                PyImGui.tree_pop()
                            
                        if PyImGui.tree_node("Black Dyes"):
                            bot_vars.config_vars.loot_black_dyes = PyImGui.checkbox("Black Dyes", bot_vars.config_vars.loot_black_dyes)
                            if bot_vars.config_vars.loot_black_dyes: 
                                PyImGui.tree_pop()
                                
                        if PyImGui.tree_node("Map Pieces"):
                            bot_vars.config_vars.loot_map_pieces = PyImGui.checkbox("Map Pieces", bot_vars.config_vars.loot_map_pieces)
                            if bot_vars.config_vars.loot_map_pieces: 
                                PyImGui.tree_pop()
                                
                                
                    
                if PyImGui.tree_node("Whites"):
                            bot_vars.config_vars.loot_whites = PyImGui.checkbox("Items", bot_vars.config_vars.loot_whites)
                            bot_vars.config_vars.loot_glacial_stones = PyImGui.checkbox("Glacial Stones", bot_vars.config_vars.loot_glacial_stones)
                            bot_vars.config_vars.loot_tomes = PyImGui.checkbox("Tomes", bot_vars.config_vars.loot_tomes)
                            bot_vars.config_vars.loot_dyes = PyImGui.checkbox("Dyes", bot_vars.config_vars.loot_dyes)
                            bot_vars.config_vars.loot_event_items = PyImGui.checkbox("Event Items", bot_vars.config_vars.loot_event_items)
                            PyImGui.tree_pop()
                            bot_vars.config_vars.loot_blues = PyImGui.checkbox("Loot Blues", bot_vars.config_vars.loot_blues)
                            bot_vars.config_vars.loot_purples = PyImGui.checkbox("Loot Purples", bot_vars.config_vars.loot_purples)
                            bot_vars.config_vars.loot_golds = PyImGui.checkbox("Loot Golds", bot_vars.config_vars.loot_golds)
                            PyImGui.tree_pop()

                # Salvage Section
                if PyImGui.tree_node("Salvage"):
                    if bot_vars.config_vars.salvage_whites:  # Nested options for Salvage Whites
                        if PyImGui.tree_node("Whites"):
                            bot_vars.config_vars.salvage_whites = PyImGui.checkbox("Items", bot_vars.config_vars.salvage_whites)
                            bot_vars.config_vars.salvage_glacial_stones = PyImGui.checkbox("Glacial Stones", bot_vars.config_vars.salvage_glacial_stones)
                            PyImGui.tree_pop()

                    bot_vars.config_vars.salvage_blues = PyImGui.checkbox("Salvage Blues", bot_vars.config_vars.salvage_blues)
                    bot_vars.config_vars.salvage_purples = PyImGui.checkbox("Salvage Purples", bot_vars.config_vars.salvage_purples)
                    bot_vars.config_vars.salvage_golds = PyImGui.checkbox("Salvage Golds", bot_vars.config_vars.salvage_golds)
                    PyImGui.tree_pop()

                # Sell Section
                if PyImGui.tree_node("Sell"):
                    bot_vars.config_vars.sell_materials = PyImGui.checkbox("Materials", bot_vars.config_vars.sell_materials)
                    bot_vars.config_vars.sell_granite = PyImGui.checkbox("Granite", bot_vars.config_vars.sell_granite)
                    bot_vars.config_vars.sell_wood = PyImGui.checkbox("Wood", bot_vars.config_vars.sell_wood)
                    bot_vars.config_vars.sell_iron = PyImGui.checkbox("Iron", bot_vars.config_vars.sell_iron)
                    bot_vars.config_vars.sell_dust = PyImGui.checkbox("Dust", bot_vars.config_vars.sell_dust)
                    bot_vars.config_vars.sell_cloth = PyImGui.checkbox("Cloth", bot_vars.config_vars.sell_cloth)
                    bot_vars.config_vars.sell_bones = PyImGui.checkbox("Bones", bot_vars.config_vars.sell_bones)
                    PyImGui.tree_pop()

                # Misc Config Section
                if PyImGui.tree_node("Misc"):
                    bot_vars.config_vars.keep_id_kit = PyImGui.input_int("Keep ID Kits", bot_vars.config_vars.keep_id_kit)
                    bot_vars.config_vars.keep_salvage_kit = PyImGui.input_int("Keep Salvage Kits", bot_vars.config_vars.keep_salvage_kit)
                    bot_vars.config_vars.keep_gold_amount = PyImGui.input_int("Keep Gold", bot_vars.config_vars.keep_gold_amount)
                    bot_vars.config_vars.leave_empty_inventory_slots = PyImGui.input_int("Leave Empty Inventory Slots", bot_vars.config_vars.leave_empty_inventory_slots)
                    PyImGui.tree_pop()

            if PyImGui.collapsing_header("Statistics"):
                if PyImGui.begin_tab_bar("MyTabBar"):
                    if PyImGui.begin_tab_item("Statistics"):
                        # Headers and data for statistics table
                        headers = ["Info", "Data"]
                        data = [
                            ("Total Run Time", bot_vars.window_statistics.global_timer.FormatElapsedTime("hh:mm:ss:ms")),
                            ("Current Run Time", bot_vars.window_statistics.lap_timer.FormatElapsedTime("mm:ss:ms")),
                            ("Minimum Run Time", FormatTime(bot_vars.window_statistics.min_time,"mm:ss:ms")),
                            ("Maximum Run Time", FormatTime(bot_vars.window_statistics.max_time,"mm:ss:ms")),
                            ("Average Run Time", FormatTime(bot_vars.window_statistics.avg_time,"mm:ss:ms")),
                            ("Current Step", FSM_vars.state_machine.get_current_step_name()),
                            ("Runs Attempted", bot_vars.window_statistics.runs_attempted),
                            ("Runs Completed", bot_vars.window_statistics.runs_completed),
                            ("Runs Failed", bot_vars.window_statistics.runs_failed),
                            ("Success Rate", bot_vars.window_statistics.success_rate * 100),
                            ("Deaths", bot_vars.window_statistics.deaths),
                            ("Kills", bot_vars.window_statistics.kills),
                            ("Left Alive", bot_vars.window_statistics.left_alive),
                        ]

                        # Render the statistics table
                        ImGui.table("run stats table", headers, data)

                        PyImGui.end_tab_item()

                    if PyImGui.begin_tab_item("Advanced Statistics"):
                        if PyImGui.begin_tab_bar("Advanced StatsTabBar"):
                            if PyImGui.begin_tab_item("Items"):
                                headers = ["Info","Data"]
                                data = [
                                    ("Whites", f"{bot_vars.window_statistics.whites}"),
                                    ("Purples", f"{bot_vars.window_statistics.purples}"),
                                    ("Golds", f"{bot_vars.window_statistics.golds}"),
                                    ("Tomes", f"{bot_vars.window_statistics.tomes}"),
                                    ("Dyes", f"{bot_vars.window_statistics.dyes}"),
                                    ("Glacial Stones", f"{bot_vars.window_statistics.glacial_stones}"),
                                    ("Event Items", f"{bot_vars.window_statistics.event_items}"),
                                    ("Id Kits", f"{bot_vars.window_statistics.id_kits}"),
                                    ("Salvage Kits", f"{bot_vars.window_statistics.salvage_kits}"),
                                ]

                                ImGui.table("run stats table", headers, data)
                                PyImGui.end_tab_item()

                            if PyImGui.begin_tab_item("Materials"):

                                run_time = "00:00:00"
                                fsm_current_step = FSM_vars.state_machine.get_current_step_name()

                                headers = ["Info","Data"]
                                data = [
                                    ("Starting Gold", f"{bot_vars.window_statistics.starting_gold}"),
                                    ("Gold Gained", f"{bot_vars.window_statistics.gold_gained}"),
                                    ("Wood Planks", f"{bot_vars.window_statistics.wood_planks}"),
                                    ("Iron Ingots", f"{bot_vars.window_statistics.iron_ingots}"),
                                    ("Glittering Dust", f"{bot_vars.window_statistics.glittering_dust}"),
                                    ("Cloth", f"{bot_vars.window_statistics.cloth}"),
                                ]

                                ImGui.table("material stats table", headers, data)
                                PyImGui.end_tab_item()
                            PyImGui.end_tab_bar()
                        PyImGui.end_tab_item()

                

                    if PyImGui.begin_tab_item("Debug"):
                        if PyImGui.begin_tab_bar("DebugInfoTB"):
                            if PyImGui.begin_tab_item("DebugInfo"):

                                if PyImGui.button("Start from jaga moraine"):
                                    StartBot()
                                    FSM_vars.state_machine.jump_to_state_by_name("reset Farming Loop")

                                if PyImGui.button("Start from Moving to kill spot"):
                                    FSM_vars.path_to_killing_spot.reset()
                                    FSM_vars.state_machine.jump_to_state_by_name("Moving to kill spot")
                                    StartBot()

                                player_x, player_y = Player.GetXY()

                                player_agent_id = Player.GetAgentID()
                                energy = Agent.GetEnergy(player_agent_id)
                                max_energy = Agent.GetMaxEnergy(player_agent_id)
                                energy_points = energy * max_energy

                                player_x, player_y = Player.GetXY()
                                enemy_array = AgentArray.GetEnemyArray()
                                enemy_array = AgentArray.Filter.ByDistance(enemy_array, (player_x, player_y), area_distance.Area)
                                enemy_array = AgentArray.Filter.ByAttribute(enemy_array, 'IsAlive')

                                enemies_on_range = len(enemy_array)

                                item_array = AgentArray.GetItemArray()

                                filtered_agent_ids = get_filtered_loot_array()

                                id_kits = bot_vars.config_vars.keep_id_kit
                                kits_in_inv = Inventory.GetModelCount(5899)

                                items_to_sell = get_filtered_materials_to_sell()
                                
                                headers = ["Info","Data"]
                                data = [
                                    ("PlayerXY", f"({int(player_x)},{int(player_y)})"),
                                    ("Stuck Timer", f"{FSM_vars.non_movement_timer.FormatElapsedTime('ss:ms')}"),
                                    ("Energy", f"{energy:.2f} : {max_energy} ({int(energy_points)})"),
                                    ("Enemies in Area", f"{enemies_on_range}"),
                                    ("Items in Area", f"{len(filtered_agent_ids)}"),
                                    ("finished_looting?", f"{ finished_looting()}"),
                                    ("ID Kits in Inventory", f"{kits_in_inv}"),
                                    ("ID Kits to keep", f"{id_kits}"),
                                    ("leave_empty_inventory_slots", f"{bot_vars.config_vars.leave_empty_inventory_slots}"),
                                    ("GetFreeSlotCount()", f"{Inventory.GetFreeSlotCount()}"),
                                    ("DoesNeedInventoryHandling", f"{DoesNeedInventoryHandling()}"),
                                    ("SellingMaterialsComplete", f"{SellingMaterialsComplete()}"),
                                    ("Items to sell", f"{lsit_to_string(items_to_sell)}"),

                                ]

                                ImGui.table("debuginfo table", headers, data)

                                PyImGui.end_tab_item()

                            if PyImGui.begin_tab_item("State Machine"):
                                fsm_previous_step = FSM_vars.state_machine.get_previous_step_name()
                                fsm_current_step = FSM_vars.state_machine.get_current_step_name()
                                fsm_next_step = FSM_vars.state_machine.get_next_step_name()

                                headers = ["Value","Data"]
                                data = [
                                    ("Previous Step:", f"{fsm_previous_step}"),
                                    ("Current Step:", f"{fsm_current_step}"),
                                    ("Next Step:", f"{fsm_next_step}"),
                                    ("State Machine is started:", f"{FSM_vars.state_machine.is_started()}"),
                                    ("State Machine is finished:", f"{FSM_vars.state_machine.is_finished()}"),
                                ]

                                ImGui.table("state machine info", headers, data)

                                PyImGui.text("FollowXY Pathing")
                                headers = ["Value","Data"]
                                data = [
                                    ("Waypoint:", f"{FSM_vars.movement_handler.waypoint}"), # Added by Markitosline: This needs fixing, as it only accounts for movement_handler but not for exact_movement_handler
                                    ("Following:", f"{FSM_vars.movement_handler.is_following()}"), # Added by Markitosline: This needs fixing, as it only accounts for movement_handler but not for exact_movement_handler
                                    ("Has Arrived:", f"{FSM_vars.movement_handler.has_arrived()}"), # Added by Markitosline: This needs fixing, as it only accounts for movement_handler but not for exact_movement_handler
                                    ("Distance to Waypoint:", f"{FSM_vars.movement_handler.get_distance_to_waypoint()}"), # Added by Markitosline: This needs fixing, as it only accounts for movement_handler but not for exact_movement_handler
                                    ("Time Elapsed:", f"{FSM_vars.movement_handler.get_time_elapsed()}"), # Added by Markitosline: This needs fixing, as it only accounts for movement_handler but not for exact_movement_handler
                                    ("wait Timer:", f"{FSM_vars.movement_handler.wait_timer.GetElapsedTime()}"), # Added by Markitosline: This needs fixing, as it only accounts for movement_handler but not for exact_movement_handler
                                    ("wait timer run once", f"{FSM_vars.movement_handler.wait_timer_run_once}"), # Added by Markitosline: This needs fixing, as it only accounts for movement_handler but not for exact_movement_handler
                                    ("is casting", f"{Agent.IsCasting(Player.GetAgentID())}"),
                                    ("is moving", f"{Agent.IsMoving(Player.GetAgentID())}"),
                                ]

                                ImGui.table("follow info", headers, data)
                                PyImGui.end_tab_item()
                            PyImGui.end_tab_bar()
                        PyImGui.end_tab_item()
                    PyImGui.end_tab_bar()

        PyImGui.end()

    except Exception as e:
        frame = inspect.currentframe()
        current_function = frame.f_code.co_name if frame else "Unknown"
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Error in {current_function}: {str(e)}", Py4GW.Console.MessageType.Error)
        raise
    
#endregion

#region stuck

def Handle_Stuck():
    """
    Detect and recover the player when stuck. Uses timers and movement logic.
    """
    global FSM_vars, bot_vars

    if Map.GetMapID() == bot_vars.starting_map:
        FSM_vars.auto_stuck_command_timer.Reset()
        return
    
    # Check for periodic "stuck" chat command
    if FSM_vars.auto_stuck_command_timer.HasElapsed(5000):
        trigger_stuck_command()
        return

    if FSM_vars.stuck_count > 3:
        cast_hos()

    # Handle severe stuck situations
    if FSM_vars.stuck_count > 12:
        restart_due_to_stuck()

    # Detect and handle non-movement
    if not Agent.IsMoving(Player.GetAgentID()) and not FSM_vars.in_waiting_routine:
        handle_non_movement()
    else:
        handle_player_movement()

def trigger_stuck_command():
    """Sends a 'stuck' chat command."""
    global FSM_vars
    Player.SendChatCommand("stuck")
    FSM_vars.auto_stuck_command_timer.Reset()

def restart_due_to_stuck():
    """Logs and restarts the bot when recovery fails repeatedly."""
    global FSM_vars, bot_vars
    if Map.GetMapID() == bot_vars.starting_map:
        return
    Py4GW.Console.Log(bot_vars.window_module.module_name, 
                      "Player is stuck, cannot recover, restarting.", 
                      Py4GW.Console.MessageType.Error)
    FSM_vars.stuck_count = 0
    bot_vars.forced_restart = True
    ResetEnvironment()

def handle_non_movement():
    """Attempts to recover from non-movement situations."""
    global FSM_vars, bot_vars

    if not FSM_vars.non_movement_timer.IsRunning():
        FSM_vars.non_movement_timer.Reset()

    if FSM_vars.non_movement_timer.HasElapsed(3000):
        FSM_vars.non_movement_timer.Reset()
        Player.SendChatCommand("stuck")
        escape_location = get_escape_location()

        Player.Move(escape_location[0], escape_location[1])
        FSM_vars.stuck_count += 1


# def handle_player_movement():
#     """Tracks player movement and resets relevant timers if moving."""
#     global FSM_vars
#     new_player_x, new_player_y = Player.GetXY()
#     if FSM_vars.old_player_x != new_player_x or FSM_vars.old_player_y != new_player_y:
#         FSM_vars.non_movement_timer.Reset()
#         FSM_vars.old_player_x = new_player_x
#         FSM_vars.old_player_y = new_player_y
#         FSM_vars.stuck_count = 0

def handle_player_movement():
    """Tracks player movement and resets relevant timers if moving beyond a certain tolerance."""
    global FSM_vars
    new_player_x, new_player_y = Player.GetXY()

    dx = new_player_x - FSM_vars.old_player_x
    dy = new_player_y - FSM_vars.old_player_y
    distance_squared = dx * dx + dy * dy

    tolerance = 100  # movement tolerance in game units
    if distance_squared > tolerance * tolerance:
        FSM_vars.non_movement_timer.Reset()
        FSM_vars.old_player_x = new_player_x
        FSM_vars.old_player_y = new_player_y
        FSM_vars.stuck_count = 0



          
#endregion

#region Reset        
def ResetEnvironment():
    global FSM_vars
    FSM_vars.sell_to_vendor.reset()
    FSM_vars.path_to_merchant.reset()
    FSM_vars.outpost_pathing.reset()
    FSM_vars.bjora_pathing.reset()
    FSM_vars.bounty_npc.reset()
    FSM_vars.farming_route.reset()
    FSM_vars.farming_route2.reset()
    FSM_vars.path_to_killing_spot.reset()
    FSM_vars.exit_jaga_moraine.reset()
    FSM_vars.return_jaga_moraine.reset()
    FSM_vars.exact_movement_handler.reset() # Added by Markitosline: when the farm loop was done, this movement declaration was missing and therefore when entering for the second time the move to killing spot estate, it would not update waypoints and follow wrong path
    FSM_vars.movement_handler.reset() 
    FSM_vars.stuck_count = 0
    FSM_vars.state_machine.reset()
    FSM_vars.state_machine.jump_to_state_by_name("Longeyes Ledge Map Check")
    FSM_vars.in_killing_routine = False
    FSM_vars.in_waiting_routine = False
    bot_vars.forced_restart = False
    bot_vars.desired_map_id = bot_vars.starting_map
    bot_vars.salvage_action_queue.clear()
    bot_vars.sell_to_vendor_action_queue.clear()
    bot_vars.buy_from_vendor_action_queue.clear()
    bot_vars.identify_action_queue.clear()
    bot_vars.deposit_action_queue.clear()

    

resigned = False
#endregion
#region IsMapValid
def IsMapValid():
    if Map.IsMapLoading():
        return False
    if not Party.IsPartyLoaded():
        return False
    return True
#endregion

#region Main
def main():
    global bot_vars,FSM_vars
    global resigned
    try:
        if not IsMapValid():
            FSM_vars.non_movement_timer.Stop()
            resigned = False
            return
        
   
        DrawWindow()

        if IsBotStarted():
            if Agent.IsDead(Player.GetAgentID()):
                bot_vars.forced_restart = True
            """
            if FSM_vars.state_machine.is_finished():
                bot_vars.forced_restart = True  
            if bot_vars.desired_map_id != Map.GetMapID():
                bot_vars.forced_restart = True
            """
            
            if bot_vars.forced_restart:
                ResetEnvironment()
                return

            
        
            FSM_vars.state_machine.update()
            
            if bot_vars.skillbar_action_queue.action_queue_timer.HasElapsed(bot_vars.skillbar_action_queue.action_queue_time):
                bot_vars.skillbar_action_queue.action_queue_timer.Reset()
                HandleSkillbar()
                Handle_Stuck()

            #Handle Action Queues
            bot_vars.sell_to_vendor_action_queue.execute_next()
            bot_vars.buy_from_vendor_action_queue.execute_next()
            bot_vars.identify_action_queue.execute_next()
            bot_vars.salvage_action_queue.execute_next()
            bot_vars.deposit_action_queue.execute_next() 
            
    except ImportError as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"ImportError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except ValueError as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"ValueError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except TypeError as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"TypeError encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    except Exception as e:
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Unexpected error encountered: {str(e)}", Py4GW.Console.MessageType.Error)
        Py4GW.Console.Log(bot_vars.window_module.module_name, f"Stack trace: {traceback.format_exc()}", Py4GW.Console.MessageType.Error)
    finally:
        pass

if __name__ == "__main__":
    main()

#endregion
