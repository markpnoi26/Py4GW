from typing import List
from typing import Tuple

import PyImGui

import Py4GW
from Hello_World import GUARDMAN_ZUI_DLG4
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import *

MODULE_NAME = "Factions Profession Leveler"

class FSM_Config:
    def __init__(self):
        self.FSM:FSM = FSM(MODULE_NAME)
        self.script_running = False
        self.combat_handler:SkillManager.Autocombat = SkillManager.Autocombat()
        self.combat_active = True
        self.run_timer = Timer()
        
        self.use_cupcakes = True
        self.use_honeycombs = True
        
        
        self.initialize()
        
    def initialize(self):
        self.FSM.AddYieldRoutineStep(name="Exit Monastery Overlook", coroutine_fn=self.ExitMonasteryOverlook)
        self.FSM.AddYieldRoutineStep(name = "Wait shing jea Monastery to Load 001",coroutine_fn = lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery")))
        self.FSM.AddYieldRoutineStep(name = "Exit to Courtyard 001", coroutine_fn=self.ExitToCourtyard)
        self.FSM.AddYieldRoutineStep(name = "Wait for Linnok Courtyard Map Load 002", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Linnok Courtyard")))
        self.FSM.AddYieldRoutineStep(name = "Unlock Secondary and Exit", coroutine_fn=self.UnlockSecondaryAndExit)
        self.FSM.AddYieldRoutineStep(name = "Wait shing jea Monastery to Load 002",coroutine_fn = lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery")))
        self.FSM.AddYieldRoutineStep(name = "Unlock Xunlai Storage", coroutine_fn=self.UnlockXunlaiStorage)
        self.FSM.AddYieldRoutineStep(name = "Craft Weapons", coroutine_fn=self.CraftWeapons)
        self.FSM.AddYieldRoutineStep(name = "Exit Shing Jea Monastery", coroutine_fn=self.ExitShingJeaMonastery)
        self.FSM.AddYieldRoutineStep(name = "Wait for Sunqua Vale Map Load 001", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Sunqua Vale")))
        self.FSM.AddYieldRoutineStep(name = "Travel to Minister Cho", coroutine_fn=self.TravelToMinisterCho)
        minister_cho_map_id = 214
        self.FSM.AddYieldRoutineStep(name = "Wait for Minister Cho Map Load", coroutine_fn=lambda: self.WaitforMapLoad(minister_cho_map_id))
        self.FSM.AddYieldRoutineStep(name = "Prepare for Mission", coroutine_fn=self.PrepareForMission)
        self.FSM.AddYieldRoutineStep(name = "Wait for Minister Cho Mission Load", coroutine_fn=lambda: self.WaitforMapLoad(minister_cho_map_id))
        self.FSM.AddYieldRoutineStep(name = "Minister Cho Mission", coroutine_fn=self.MinisterChoMission)
        self.FSM.AddYieldRoutineStep(name = "Take Warning the Tengu and Exit", coroutine_fn=self.TakeWarningTheTenguandExit)
        self.FSM.AddYieldRoutineStep(name = "Wait for Kinya Province Map Load", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Kinya Province"))) #236
        self.FSM.AddYieldRoutineStep(name = "Warning the Tengu", coroutine_fn=self.WarningTheTengu)
        self.FSM.AddYieldRoutineStep(name = "Wait shing jea Monastery to Load 003",coroutine_fn = lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery")))
        self.FSM.AddYieldRoutineStep(name = "Exit Monastery Overlook 002", coroutine_fn=self.ExitMonasteryOverlook002)
        self.FSM.AddYieldRoutineStep(name = "Wait for Sunqua Vale Map Load 002", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Sunqua Vale")))
        self.FSM.AddYieldRoutineStep(name = "Travel to Tsumei Village", coroutine_fn=self.TravelTsumeiVillage)
        self.FSM.AddYieldRoutineStep(name = "Wait for Tsumei Village Map Load", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Tsumei Village")))
        self.FSM.AddYieldRoutineStep(name = "Exit Tsumei Village", coroutine_fn=self.ExitTsumeiVillage)
        self.FSM.AddYieldRoutineStep(name = "Wait for Panjiang Peninsula Map Load", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Panjiang Peninsula")))
        self.FSM.AddYieldRoutineStep(name = "The Threat Grows", coroutine_fn=self.TheThreatGrows)
        self.FSM.AddYieldRoutineStep(name = "Wait shing jea Monastery to Load 004",coroutine_fn = lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery")))
        self.FSM.AddYieldRoutineStep(name = "Exit to Courtyard 002", coroutine_fn=self.ExitToCourtyard002)
        self.FSM.AddYieldRoutineStep(name = "Wait for Linnok Courtyard Map Load 002", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Linnok Courtyard")))
        self.FSM.AddYieldRoutineStep(name = "Finish quest and advance to Saoshang Trail", coroutine_fn=self.FinishQuestsAndAdvanceToSaoshangTrail)
        saoshang_trail_map_id = 313
        self.FSM.AddYieldRoutineStep(name = "Wait for Saoshang Trail Map Load", coroutine_fn=lambda: self.WaitforMapLoad(saoshang_trail_map_id))
        self.FSM.AddYieldRoutineStep(name = "Traverse Saoshang Trail", coroutine_fn=self.TraverseSaoshangTrail)
        self.FSM.AddYieldRoutineStep(name = "Wait for Seitung Harbor Map Load", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Seitung Harbor")))


        self.FSM.AddYieldRoutineStep(name = "Go to Zen Daijun 001", coroutine_fn=self.GoToZenDaijunPart001)
        self.FSM.AddYieldRoutineStep(name = "Wait for Haiju Lagoon Map Load", coroutine_fn=lambda: self.WaitforMapLoad(GLOBAL_CACHE.Map.GetMapIDByName("Haiju Lagoon")))
        self.FSM.AddYieldRoutineStep(name = "Go to Zen Daijun 002", coroutine_fn=self.GoToZenDaijunPart002)
        self.FSM.AddYieldRoutineStep(name = "End Routines", coroutine_fn=self.Endroutine)
        
    #region HELPERS
    
    def _stop_execution(self):
        self.script_running = False
        self.FSM.stop()
        Py4GW.Console.Log(MODULE_NAME, "Script stopped.", Py4GW.Console.MessageType.Info)
        yield from Routines.Yield.wait(100)
        
    def _prepare_for_battle(self):
        
        profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        if profession == "Warrior":
            yield from Routines.Yield.Skills.LoadSkillbar("OQcSEluJPMDjwAAAAAAAAA",log=False)
        elif profession == "Ranger":
            yield from Routines.Yield.Skills.LoadSkillbar("OgcScleJPMDjwAAAAAAAAA",log=False)
        elif profession == "Monk":
            yield from Routines.Yield.Skills.LoadSkillbar("OwcB0lkRuMAAAAAAAAAA",log=False)
        elif profession == "Necromancer":
            yield from Routines.Yield.Skills.LoadSkillbar("OAdSUqvIucaAAAAAAAAAAA",log=False)
        elif profession == "Mesmer":
            yield from Routines.Yield.Skills.LoadSkillbar("OQdSIsvIagLDAAAAAAAAAA",log=False)
        elif profession == "Elementalist":
            yield from Routines.Yield.Skills.LoadSkillbar("OgdSosvICjLDAAAAAAAAAA",log=False)
        elif profession == "Ritualist":
            yield from Routines.Yield.Skills.LoadSkillbar("OAei8Jg24y+mAAAAAAAAAAAA",log=False)
        elif profession == "Assassin":
            yield from Routines.Yield.Skills.LoadSkillbar("OwBR0J5hBAAAAAAAAAAA",log=False)
            
        GLOBAL_CACHE.Party.LeaveParty()
        
        HEALER_ID = 1
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(HEALER_ID)
        SPIRITS_ID = 5
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(SPIRITS_ID)
        GUARDIAN_ID = 2
        GLOBAL_CACHE.Party.Henchmen.AddHenchman(GUARDIAN_ID)
        
        summoning_stone_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(ModelID.Igneous_Summoning_Stone.value)
        if summoning_stone_in_bags < 1:
            GLOBAL_CACHE.Player.SendChatCommand("bonus")
            
        target_cupcake_count = 10     
        if self.use_cupcakes:
            model_id = ModelID.Birthday_Cupcake.value
            cupcake_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
            cupcake_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
            
            if cupcake_in_bags < target_cupcake_count and cupcake_in_storage > 0:
                cupcakes_needed = min(target_cupcake_count - cupcake_in_bags, cupcake_in_storage)
                items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, cupcakes_needed)
                yield from Routines.Yield.wait(250)
                if not items_withdrawn:
                    Py4GW.Console.Log(MODULE_NAME, "Failed to withdraw cupcakes from storage.", Py4GW.Console.MessageType.Error)
            else:
                if cupcake_in_storage < target_cupcake_count - cupcake_in_bags:
                    Py4GW.Console.Log(MODULE_NAME, "Not enough cupcakes in storage.", Py4GW.Console.MessageType.Error)
                    yield from self._stop_execution()
                    return

        yield from Routines.Yield.wait(250)
        
        target_honeycomb_count = 20
        if self.use_honeycombs:
            model_id = ModelID.Honeycomb.value
            honey_in_bags = GLOBAL_CACHE.Inventory.GetModelCount(model_id)
            honey_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(model_id)
            
            if honey_in_bags < target_honeycomb_count and honey_in_storage > 0:
                honey_needed = min(target_honeycomb_count - honey_in_bags, honey_in_storage)
                items_withdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(model_id, honey_needed)
                yield from Routines.Yield.wait(250)
                if not items_withdrawn:
                    Py4GW.Console.Log(MODULE_NAME, "Failed to withdraw honeycombs from storage.", Py4GW.Console.MessageType.Error)
            else:
                if honey_in_storage < target_honeycomb_count - honey_in_bags:
                    Py4GW.Console.Log(MODULE_NAME, "Not enough honeycombs in storage.", Py4GW.Console.MessageType.Error)
                    yield from self._stop_execution()
                    return

        yield from Routines.Yield.wait(1000)
        
    def _pop_imp(self):
        summoning_stone = ModelID.Igneous_Summoning_Stone.value
        stone_id = GLOBAL_CACHE.Inventory.GetFirstModelID(summoning_stone)
        if stone_id:
            GLOBAL_CACHE.Inventory.UseItem(stone_id)
            yield from Routines.Yield.wait(500)
        
        
    def UseCupcake(self):
        if not self.use_cupcakes:
            return

        if ((not Routines.Checks.Map.MapValid()) and (not Map.IsExplorable())):
            return
        
        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            return

        cupcake__id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Birthday_Cupcake.value)
        cupcake_effect = GLOBAL_CACHE.Skill.GetID("Birthday_Cupcake_skill")
        
        if not Effects.HasEffect(GLOBAL_CACHE.Player.GetAgentID(), cupcake_effect) and cupcake__id:
            GLOBAL_CACHE.Inventory.UseItem(cupcake__id)
            yield from Routines.Yield.wait(500)
            
    def UseHoneycomb(self):
        if not self.use_honeycombs:
            return
        
        if ((not Routines.Checks.Map.MapValid()) and (not Map.IsExplorable())):
            return
        
        if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
            return
        
        target_morale = 110
        
        while True:
            morale = GLOBAL_CACHE.Player.GetMorale()
            if morale >= target_morale:
                break

            honeycomb_id = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Honeycomb.value)
            if not honeycomb_id:
                break

            GLOBAL_CACHE.Inventory.UseItem(honeycomb_id)
            yield from Routines.Yield.wait(500)
        
        
    def AutoCombat(self):
        while True:
            if not (Routines.Checks.Map.MapValid() and 
                    Routines.Checks.Player.CanAct() and
                    Map.IsExplorable() and
                    not self.combat_handler.InCastingRoutine()):
                ActionQueueManager().ResetQueue("ACTION")
                yield from Routines.Yield.wait(100)
            else:
                yield from self.UseCupcake()
                yield from self.UseHoneycomb()
                
                if self.combat_active:
                    self.combat_handler.HandleCombat()  

            yield
        
    def _movement_eval_exit_on_map_loading(self):
        if GLOBAL_CACHE.Map.IsMapLoading():
            return True
        
        if not self.script_running:
            return True
        
        return False
    
    def Endroutine(self):
        self.script_running = False
        self.FSM.stop()
        Py4GW.Console.Log(MODULE_NAME, "Script ended.", Py4GW.Console.MessageType.Info)
        yield from Routines.Yield.wait(100)
    
    def WaitforMapLoad(self, target_map_id):
        wait_of_map_load = yield from Routines.Yield.Map.WaitforMapLoad(target_map_id)
        if not wait_of_map_load:
            Py4GW.Console.Log(MODULE_NAME, "Map load failed.", Py4GW.Console.MessageType.Error)
            yield from self._stop_execution()
        yield from Routines.Yield.wait(1000)
        
    from typing import Any
    from typing import Generator
    from typing import List
    from typing import Tuple

    def follow_path(self, path: List[Tuple[float, float]], pause_on_danger: bool = False) -> Generator[Any, Any, bool]:
        success_movement = yield from Routines.Yield.Movement.FollowPath(
            path_points=path,
            custom_exit_condition=lambda: self._movement_eval_exit_on_map_loading(),
            log=False,
            custom_pause_fn=(lambda: Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot)) if pause_on_danger else None
        )

        if not success_movement:
            if GLOBAL_CACHE.Map.IsMapLoading():
                return True
            yield from self._stop_execution()
            return False

        if not self.script_running:
            yield from Routines.Yield.wait(100)
            return False

        return True


    def interact_with_agent(self,coords: Tuple[float, float],dialog_id: Optional[int] = None) -> Generator[Any, Any, bool]:
        result = yield from Routines.Yield.Agents.InteractWithAgentXY(*coords)
        if not result:
            yield from self._stop_execution()
            return False

        if not self.script_running:
            yield from Routines.Yield.wait(100)
            return False

        if dialog_id is not None:
            GLOBAL_CACHE.Player.SendDialog(dialog_id)
            yield from Routines.Yield.wait(500)

        return True
    

    #region LOGIC
        
    def ExitMonasteryOverlook(self):
        path_to_ludo: List[Tuple[float, float]] = [
                        (-2132, 1054),(-2746, 1300),(-3565, 1395),(-4365, 1689),(-5095, 2151),
                        (-5645, 2819),(-6014, 3596),(-6356, 4393),(-6720, 5178),(-7011, 5750),]

        if not (yield from self.follow_path(path_to_ludo)):
            return

        I_AM_SURE = 0x85
        if not (yield from self.interact_with_agent((-7048, 5817), dialog_id=I_AM_SURE)):
            return

        
    def ExitToCourtyard(self):
        path_to_courtyard: List[Tuple[float, float]] = [(-7407, 7048),(-7568, 7678),(-7815,8522),(-7386,9265),
                                                        (-6589,9508),(-5718,9480),(-4856,9478),(-3988,9473),(-3480,9460)]
             
        if not (yield from self.follow_path(path_to_courtyard)):
            return
        
                
    def UnlockSecondaryAndExit(self):
        path_to_togo: List[Tuple[float, float]] = [(-3281, 9442),(-2673, 9447),(-1790, 9441),(-904, 9434),(-159, 9174),]

        if not (yield from self.follow_path(path_to_togo)):
            return
        
        profession, _ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        UNLOCK_SECONDARY = 0x813D08 if profession != "Assassin" else 0x813D0E

        if not (yield from self.interact_with_agent((-92, 9217), dialog_id=UNLOCK_SECONDARY)):
            return
        
        cancel_button_frame_id = UIManager.GetFrameIDByHash(784833442)  # Cancel button frame ID
        if not cancel_button_frame_id:
            Py4GW.Console.Log(MODULE_NAME, "Cancel button frame ID not found.", Py4GW.Console.MessageType.Error)
            yield from self._stop_execution()
            return
        
        while not UIManager.FrameExists(cancel_button_frame_id):
            yield from Routines.Yield.wait(500)
            return
        
        UIManager.FrameClick(cancel_button_frame_id)
        yield from Routines.Yield.wait(500)
        
        cancel_button_frame_id = UIManager.GetFrameIDByHash(784833442)
        if not cancel_button_frame_id:
            Py4GW.Console.Log(MODULE_NAME, "Cancel button frame ID not found.", Py4GW.Console.MessageType.Error)
            yield from self._stop_execution()
            return
        
        while not UIManager.FrameExists(cancel_button_frame_id):
            yield from Routines.Yield.wait(500)
            return
        
        UIManager.FrameClick(cancel_button_frame_id)
        yield from Routines.Yield.wait(500)
          
        x,y = GLOBAL_CACHE.Agent.GetXY(GLOBAL_CACHE.Player.GetAgentID())
        TAKE_REWARD = 0x813D07
        if not (yield from self.interact_with_agent((x, y), dialog_id=TAKE_REWARD)):
            return
        TAKE_QUEST = 0x813E01
        if not (yield from self.interact_with_agent((x, y), dialog_id=TAKE_QUEST)):
            return
        
        exit_path = path_to_togo.reverse() or []
        exit_path.append((-3762, 9471))  # Return to the starting point
        
        if not (yield from self.follow_path(exit_path)):
            return
        
                
    def UnlockXunlaiStorage(self):
        path_to_xunlai: List[Tuple[float, float]] = [(-4958, 9472),(-5465, 9727),(-4791, 10140),(-3945, 10328),(-3869, 10346),]

        if not (yield from self.follow_path(path_to_xunlai)):
            return

        UNLOCK_STORAGE = 0x84
        if not (yield from self.interact_with_agent((-3749, 10367), dialog_id=UNLOCK_STORAGE)):
            return  

        
    def CraftWeapons(self):
        path_to_crafter: List[Tuple[float, float]] = [(-3869, 10346),(-3943, 11015),(-4062, 11863),(-4722, 12376),(-5561, 12170),(-6423, 12183),]

        if not (yield from self.follow_path(path_to_crafter)):
            return
    
        MELEE_CLASSES = ["Warrior", "Ranger", "Assassin"]
        profession,_ = GLOBAL_CACHE.Agent.GetProfessionNames(GLOBAL_CACHE.Player.GetAgentID())
        
        if profession in MELEE_CLASSES:
            if not (yield from self.interact_with_agent((-6519, 12335))):
                return
        
            iron_in_storage = GLOBAL_CACHE.Inventory.GetModelCountInStorage(ModelID.Iron_Ingot.value)
            
            if iron_in_storage < 5:
                Py4GW.Console.Log(MODULE_NAME, "Not enough Iron Ingots to craft weapons.", Py4GW.Console.MessageType.Error)
                yield from self._stop_execution()
                return
            
            items_witdrawn = GLOBAL_CACHE.Inventory.WithdrawItemFromStorageByModelID(ModelID.Iron_Ingot.value, 5)
            if not items_witdrawn:
                Py4GW.Console.Log(MODULE_NAME, "Failed to withdraw Iron Ingots from storage.", Py4GW.Console.MessageType.Error)
                yield from self._stop_execution()
                return
            
            yield from Routines.Yield.wait(500)
            
            SAI_MODEL_ID = 11643
            merchant_item_list = GLOBAL_CACHE.Trading.Merchant.GetOfferedItems()
            for item_id in merchant_item_list:
                
                if GLOBAL_CACHE.Item.GetModelID(item_id) == SAI_MODEL_ID:
                    iron_ingots = GLOBAL_CACHE.Inventory.GetFirstModelID(ModelID.Iron_Ingot.value)
                    if iron_ingots:
                        trade_item_list = [iron_ingots]
                        quantity_list = [5]
                    
                        GLOBAL_CACHE.Trading.Crafter.CraftItem(item_id, 100, trade_item_list, quantity_list)
                        yield from Routines.Yield.wait(500)
                        break
        
            #equip crafted weapon
            crafted_weapon = GLOBAL_CACHE.Inventory.GetFirstModelID(SAI_MODEL_ID)
            if crafted_weapon:
                GLOBAL_CACHE.Inventory.EquipItem(crafted_weapon, GLOBAL_CACHE.Player.GetAgentID())
                yield from Routines.Yield.wait(500)
            else:
                Py4GW.Console.Log(MODULE_NAME, "Crafted weapon not found in inventory.", Py4GW.Console.MessageType.Error)
                yield from self._stop_execution()
                return
        else:
            yield from self._prepare_for_battle()
            wand = GLOBAL_CACHE.Inventory.GetFirstModelID(6508) #wand
            GLOBAL_CACHE.Inventory.EquipItem(wand, GLOBAL_CACHE.Player.GetAgentID())
            shield = GLOBAL_CACHE.Inventory.GetFirstModelID(6514) #shield
            GLOBAL_CACHE.Inventory.EquipItem(shield, GLOBAL_CACHE.Player.GetAgentID())
        
    def ExitShingJeaMonastery(self):
        path_to_exit: List[Tuple[float, float]] = [(-6544,12262),(-7204,12363),(-8055,12528),(-8907,12697),(-9757,12864),
                                                   (-10458,12403),(-11166,11974),(-12022, 11834),(-12848,11576),(-13228,10872),
                                                   (-13956,10470),(-14476,10989),(-14961,11453),]

        if not (yield from self.follow_path(path_to_exit)):
            return
        
    def TravelToMinisterCho(self):
        path_to_minister: List[Tuple[float, float]] = [
                (20323, -8150), (20627, -7571), (21028, -6807), (21508, -6090), (21813, -5296),
                (21744, -4443), (21620, -3579), (21309, -2800), (20648, -2244), (19915, -1782),
                (19153, -1380), (18432, -902),  (17981, -171),  (17612, 611),   (17204, 1378),
                (16636, 2026),  (16129, 2657),  (15381, 3102),  (14614, 3502),  (13827, 3875),
                (13061, 4284),  (12447, 4889),  (11951, 5598),  (11446, 6305),  (10947, 7005),
                (10402, 7682),  (9802, 8308),   (9187, 8916),   (8463, 9372),   (7637, 9616),
                (7319, 10348),  (7299, 11215),  (7280, 12086),  (7261, 12952),  (7223, 13820),
                (6944, 14640),  (6745, 15483),  (6698, 16095),
            ]
        
        if not (yield from self.follow_path(path_to_minister)):
            return

        GUARDMAN_ZUI_DLG4 = 0x80000B
        if not (yield from self.interact_with_agent((6637, 16147), dialog_id=GUARDMAN_ZUI_DLG4)):
            return
        
        yield from Routines.Yield.wait(5000)
        
    def PrepareForMission(self):
        ACCEPT_QUEST = 0x813E07
        if not (yield from self.interact_with_agent((7884, -10029), dialog_id=ACCEPT_QUEST)):
            return
        
        yield from self._prepare_for_battle()

        GLOBAL_CACHE.Map.EnterChallenge()

        yield from Routines.Yield.wait(6500)  # Wait for the map to load and the challenge to start
        
    def MinisterChoMission(self):
        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)

        try:
            yield from Routines.Yield.wait(1000)
            yield from self._pop_imp()
                
            path_to_mission: List[Tuple[float, float]] = [(6358,-7348),(5444, -7748),(5254, -7879),(4170, -8836),(3059, -9734),(1634, -9598),
                                                        (92, -8496),(-64, -8182),(840, -7188),(1274, -6695),(1602, -6502),
                                                        (2447, -5387),(3595, -4592),(4950, -5042),(4269, -4182),(4225, -3439),
                                                        (4769, -2557),(5270, -2191),(5709, -1887),(6020, -1089),(4906, -250),
                                                        (3701, 262),(2950, 569),(1923, 1569),(1599, 1776),(770, 1550),
                                                        (157, 1000),(1098, 1869),(282, 1097),(-418, 346),(-670, -172),
                                                        (-888, -672),(-1712, -1835),(-1493, -3211),(-2390, -4329),(-2928, -4416),
                                                        (-3390, -4829),(-3636, -5125),(-4101, -5656),(-4636, -6313),(-5733, -7239),
                                                        (-7305, -7633),(-7733, -7507),(-7937, -6764),(-8403, -5726),(-9291, -4938),
                                                        (-9254, -3764),(-8975, -2453),(-8241, -1974),(-8775, -1570),(-8995, -2198),
                                                        (-8281, -1795),(-7445, -698),(-6990, 663),(-7239, 2019),(-8049, 2389),
                                                        (-7824, 2133),(-8595, 1960),(-9102, 1900),(-9723, 1561),(-10135, 1537),
                                                        (-10819, 1943),(-11040, 2313),(-11910, 1552),(-13163, 1223),(-13637, 1226),
                                                        (-14432, 1263),(-14602, 2536),(-14611, 3224),(-14576, 2748),(-15830, 2409),
                                                        (-16953, 2447),
                                                    ]

            if not (yield from self.follow_path(path_to_mission, pause_on_danger=True)):
                return
                    
            if not (yield from self.interact_with_agent((-17031, 2448))):
                return

            while True:
                mapid = GLOBAL_CACHE.Map.GetMapID() #251
                if (Routines.Checks.Map.MapValid() and (mapid == GLOBAL_CACHE.Map.GetMapIDByName("Ran Musu Gardens"))):
                    break
                yield from Routines.Yield.wait(1000)
        finally:  
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
                yield from Routines.Yield.wait(3000)
            
    def TakeWarningTheTenguandExit(self):
        TAKE_WARNING = 0x815301
        if not (yield from self.interact_with_agent((15846, 19013), dialog_id=TAKE_WARNING)):
            yield from self._stop_execution()
            return
        
        yield from self._prepare_for_battle()

        exit_path: List[Tuple[float, float]] = [(15911, 19050),(15495, 18564),(14813, 18021),(14629, 17285),
                     (15122, 16584),(14936, 15747),(14928, 15720),(14730,15176)]
        
        if not (yield from self.follow_path(exit_path)):
            yield from self._stop_execution()
            return
        
    def WarningTheTengu(self):
        first_half_path: List[Tuple[float, float]] = [(14621, 14767),(14018, 15121),(13218, 15462),(12393, 15581),(11960, 14900),
                                                    (11651, 14089),(11196, 13354),(10671, 12664),(10049, 12060),(9392, 11492),
                                                    (8582, 11284),(7736, 11456),(6909, 11701),(6132, 12084),(5413, 12572),
                                                    (4701, 13061),(3895, 13378),(3041, 13377),(2215, 13137),(1429, 12768),]
        
        if not (yield from self.follow_path(first_half_path)):
            yield from self._stop_execution()
            return
                
        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)
        
        yield from self._pop_imp()
        
        try:
        
            second_half_path: List[Tuple[float, float]] = [(687, 12331),(-115, 11996),(-920, 11681),(-1782, 11613),(-2636, 11539),
                                                            (-3250, 10969),(-3391, 10127),(-3580, 9285),(-3748, 8702),(-3906, 8316),
                                                            (-4093, 7476),(-3456, 6918),(-2696, 6496),(-1889, 6187),(-1097, 5864),
                                                            (-957, 5057),(-983, 4931),]
            
            if not (yield from self.follow_path(second_half_path, pause_on_danger=True)):
                yield from self._stop_execution()
                return
            
            CONTINUE_QUEST = 0x815304
            if not (yield from self.interact_with_agent((-1023, 4844), dialog_id=CONTINUE_QUEST)):
                yield from self._stop_execution()
                return

            path_to_kill_spot: List[Tuple[float, float]] = [(-988, 4912),(-950, 4435),(-1031, 3568),(-1525, 2870),(-2308, 2525),
                                                            (-3055, 2099),(-3749, 1590),(-4484, 1136),(-5011, 732),(-5011, 732),]
            
            if not (yield from self.follow_path(path_to_kill_spot, pause_on_danger=True)):
                yield from self._stop_execution()
                return

            yield from Routines.Yield.wait(1000)
            
            while Routines.Checks.Agents.InDanger(aggro_area=Range.Earshot):
                yield from Routines.Yield.wait(1000)
            
            path_to_kill_spot.reverse()
            
            if not (yield from self.follow_path(path_to_kill_spot, pause_on_danger=True)):
                yield from self._stop_execution()
                return
        
            TAKE_REWARD = 0x815307
            if not (yield from self.interact_with_agent((-1023, 4844), dialog_id=TAKE_REWARD)):
                yield from self._stop_execution()
                return

            TAKE_THE_THREAT_GROWS = 0x815401
            GLOBAL_CACHE.Player.SendDialog(TAKE_THE_THREAT_GROWS)
            yield from Routines.Yield.wait(500)
        finally:
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
        
        GLOBAL_CACHE.Map.Travel(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery"))
        yield from Routines.Yield.wait(1000)
        
    def ExitMonasteryOverlook002(self):
        exit_path: List[Tuple[float, float]] = [(-8418, 9301),(-8951, 9581),(-9709, 10009),(-10484, 10372),(-11332, 10190),
                                                (-12179, 10020),(-13030, 10122),(-13824, 10473),(-15000,11500)]
        
        if not (yield from self.follow_path(exit_path)):
            yield from self._stop_execution()
            return
        
    def TravelTsumeiVillage(self):
        path_to_tsumei: List[Tuple[float, float]] = [(20323, -8150),(19816, -8562),(19191, -9163),(18379, -9169),(17586, -8827),
                                                    (16846, -8378),(16031, -8414),(15318, -8902),(14598, -9388),(13879, -9872),
                                                    (13166, -10318),(12450, -10801),(11676, -11158),(10872, -11493),(10068, -11818),
                                                    (9217, -11718),(8381, -11475),(7548, -11234),(6706, -11073),(5933, -11466),
                                                    (5174, -11887),(4396, -12252),(3543, -12353),(2676, -12348),(1812, -12398),
                                                    (978, -12172),(144, -11957),(-716, -11988),(-1570, -12149),(-2420, -12325),
                                                    (-3268, -12482),(-4093, -12744),(-4669, -13016),(-4900, -13900)]
        
        if not (yield from self.follow_path(path_to_tsumei)):
            yield from self._stop_execution()
            return
        
    def ExitTsumeiVillage(self):
        exit_path: List[Tuple[float, float]] = [(-5289, -13950),(-5691, -14470),(-6344, -15031),(-7165, -15295),(-8011, -15455),
                                                (-8829, -15745),(-9676, -15940),(-10532, -16069),(-11170, -16560),(-11600,-17400)]
        
        if not (yield from self.follow_path(exit_path)):
            yield from self._stop_execution()
            return

    def TheThreatGrows(self):
        path_to_quest: List[Tuple[float, float]] = [(9687, 16174),(9884, 15533),(10191, 14723),(10528, 13927),(10791, 13105),
                                                    (10803, 12239),(10680, 11382),(10549, 10523),(10419, 9670),(10287, 8812),
                                                    (9922, 8028),(9700, 7250)]

        if not (yield from self.follow_path(path_to_quest)):
            yield from self._stop_execution()
            return
        
        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)
        
        yield from self._pop_imp()
        
        try:
            SISTER_TAI_MODEL_ID = 3316
            while True:
                sister_tai_agent_id = Routines.Agents.GetAgentIDByModelID(SISTER_TAI_MODEL_ID)
                
                if (not Routines.Checks.Agents.InDanger(aggro_area=Range.Spellcast)) and GLOBAL_CACHE.Agent.HasQuest(sister_tai_agent_id):
                    break
                yield from Routines.Yield.wait(1000)
                
        finally:  
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
                yield from Routines.Yield.wait(3000)
            
        sister_tai_agent_id = Routines.Agents.GetAgentIDByModelID(SISTER_TAI_MODEL_ID)
        x,y = GLOBAL_CACHE.Agent.GetXY(sister_tai_agent_id)
        ACCEPT_REWARD = 0x815407
        if not (yield from self.interact_with_agent((x, y), dialog_id=ACCEPT_REWARD)):
            yield from self._stop_execution()
            return
        
        TAKE_QUEST = 0x815501
        GLOBAL_CACHE.Player.SendDialog(TAKE_QUEST)
        yield from Routines.Yield.wait(500)
        
        GLOBAL_CACHE.Map.Travel(GLOBAL_CACHE.Map.GetMapIDByName("Shing Jea Monastery"))
        yield from Routines.Yield.wait(1000)
        
    def ExitToCourtyard002(self):
        yield from self._prepare_for_battle()
        
        path_to_courtyard: List[Tuple[float, float]] = [(-8861, 8508),(-8350, 8960),(-7558, 9307),(-6718, 9488),(-5849, 9469),
                                                        (-5036, 9469),(-4168, 9461),(-3980, 9460),(-3480,9460)]
             
        if not (yield from self.follow_path(path_to_courtyard)):
            return
        
    def FinishQuestsAndAdvanceToSaoshangTrail(self):
        path_to_togo: List[Tuple[float, float]] = [(-3281, 9442),(-2673, 9447),(-1790, 9441),(-904, 9434),(-159, 9174),]

        if not (yield from self.follow_path(path_to_togo)):
            return
        
        ACCEPT_QUEST = 0x815507
        if not (yield from self.interact_with_agent((-92, 9217), dialog_id=ACCEPT_QUEST)):
            return
        
        TAKE_QUEST = 0x815601
        if not (yield from self.interact_with_agent((-92, 9217), dialog_id=TAKE_QUEST)):
            return
        
        CONTINUE = 0x80000B
        if not (yield from self.interact_with_agent((538, 10125), dialog_id=CONTINUE)):
            return

    def TraverseSaoshangTrail(self):
        CONTINUE = 0x815604
        if not (yield from self.interact_with_agent((1254, 10875), dialog_id=CONTINUE)):
            return
        
        path_to_saoshang: List[Tuple[float, float]] = [(1185, 10837),(1574, 10532),(2364, 10186),(2918, 9910),(3647, 10072),
                                                        (4136, 10793),(4491, 11404),(4821, 12209),(5187, 12987),(5552, 13518),
                                                        (5821, 13790),(6608, 14098),(7653, 13843),(8063, 13118),(8290, 12662),
                                                        (8630, 11880),(8367, 11063),(8152, 10532),(8447, 10019),(9281, 10453),
                                                        (10074, 11029),(10471, 11219),(11275, 11554),(12030, 11856),(12628, 12208),
                                                        (12906, 12459),(13653, 12899),(14468, 13194),(15310, 13406),(16600, 13150)]

        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)
        
        yield from self._pop_imp()
        
        try:
            if not (yield from self.follow_path(path_to_saoshang, pause_on_danger=True)):
                return
        finally:  
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
                yield from Routines.Yield.wait(3000)
                
    def TakeRewardAndExitSaoshangTrail(self):
        pass
    
    def GoToZenDaijunPart001(self):
        path_to_zendaijun: List[Tuple[float, float]] = [(10062, -12912),(9347, -12883),(8607, -12472),(8352, -11650),
                                                        (8219, -10799),(8430, -9975),(8944, -9277),(9687, -8848),(10551, -8773),
                                                        (11417, -8733),(12241, -8676),(12984, -8557),(13850, -8478),(14707, -8558),
                                                        (15090, -8652),(16063, -8316),(16619, -8324),(17361, -7878),(18011, -7306),
                                                        (18660, -6735),(19014, -6520),(19606, -6088),(19882, -5267),(20179, -4464),
                                                        (19923, -3871),(19720, -2907),(20225, -2204),(20901, -1664),(21436, -994),
                                                        (21699, -167 ),(22085, 836  ),(22598, 1205 ),(22951, 1457 ),(23616, 1587)]
        
        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)
        
        yield from self._pop_imp()
        
        try:
            if not (yield from self.follow_path(path_to_zendaijun, pause_on_danger=True)):
                return
        finally:  
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
                yield from Routines.Yield.wait(3000)
                
    def GoToZenDaijunPart002(self):
        path_to_zendaijun: List[Tuple[float, float]] = [
                                                    (-12066, -6836), (-11556, -6363), (-11383, -5516), (-11082, -4717), (-10654, -3960),
                                                    (-10146, -3268), (-9151, -2746), (-8527, -2650), (-7670, -2543), (-6808, -2449),
                                                    (-5933, -2379), (-5315, -2086), (-5045, -1296), (-5100, -468), (-4435, 82),
                                                    (-3819, 675), (-2648, 1246), (-1843, 1566), (-1013, 1696), (-226, 1328),
                                                    (604, 1100), (1436, 873), (2153, 480), (2808, -45), (3410, -663),
                                                    (3986, -1311), (4534, -1985), (5185, -2546), (5810, -2619), (5861, -3431),
                                                    (5671, -4255), (5397, -4727), (5473, -5397), (5848, -6176), (6495, -6723),
                                                    (7349, -6730), (8210, -6637), (8984, -6914), (9520, -7567), (9563, -8418),
                                                    (9285, -9239), (9211, -9753), (9372, -10605), (9537, -11454), (9941, -12223),
                                                    (10519, -12867), (11183, -13431), (11781, -14043), (11694, -14886), (11033, -15467),
                                                    (10997, -16286), (11289, -17079), (11918, -17681), (12605, -18199), (13350, -18643),
                                                    (14139, -19014), (14916, -19388), (15667, -19822), (16368, -20323), (16812, -21046),
                                                    (16784, -21887), (16571, -22196),
                                                ]

        
        autocombat = self.AutoCombat()
        GLOBAL_CACHE.Coroutines.append(autocombat)
        
        yield from self._pop_imp()
        
        try:
            if not (yield from self.follow_path(path_to_zendaijun, pause_on_danger=True)):
                return
            
            CONTINUE = 0x80000B
            if not (yield from self.interact_with_agent((16489, -22213), dialog_id=CONTINUE)):
                return
            
        finally:  
            if autocombat in GLOBAL_CACHE.Coroutines:
                GLOBAL_CACHE.Coroutines.remove(autocombat)
                yield from Routines.Yield.wait(3000)

main_FSM = FSM_Config()
selected_step = 0

#region GUI
def ShowMainWindow():
    global selected_step
    if PyImGui.begin(MODULE_NAME, PyImGui.WindowFlags.AlwaysAutoResize): 
        
        PyImGui.text("Current State: " + main_FSM.FSM.get_current_step_name())
        PyImGui.text("Script Running: " + str(main_FSM.script_running))
        PyImGui.text("Time Elapsed: " + str(main_FSM.run_timer.FormatElapsedTime("hh:mm:ss")))
        
        main_FSM.use_cupcakes = PyImGui.checkbox("Use Cupcakes", main_FSM.use_cupcakes)
        main_FSM.use_honeycombs = PyImGui.checkbox("Use Honeycombs", main_FSM.use_honeycombs)
        
        PyImGui.text("Morale: " + str(GLOBAL_CACHE.Player.GetMorale()))

        if PyImGui.button("Start"):
            main_FSM.script_running = True
            main_FSM.run_timer.Reset()
            main_FSM.FSM.restart()
            
        PyImGui.same_line(0,-1)
            
        if PyImGui.button("Stop"):
            main_FSM.script_running = False
            main_FSM.run_timer.Stop()
            main_FSM.FSM.stop()
            
        fsm_steps = main_FSM.FSM.get_state_names()
        selected_step = PyImGui.combo("FSM Steps",selected_step,  fsm_steps)
        if PyImGui.button("start at Step"):
            if selected_step < len(fsm_steps):
                main_FSM.script_running = True
                main_FSM.FSM.reset()
                main_FSM.run_timer.Reset()
                main_FSM.FSM.jump_to_state_by_name(fsm_steps[selected_step])
                

    PyImGui.end()
    
def main():
    global main_FSM
    try:
        ShowMainWindow()
        
        if main_FSM.FSM.finished:
            if main_FSM.script_running:
                main_FSM.script_running = False
                main_FSM.FSM.stop()

        if main_FSM.script_running:
            main_FSM.FSM.update()
    

    except Exception as e:
        Py4GW.Console.Log(MODULE_NAME, f"Error: {str(e)}", Py4GW.Console.MessageType.Error)
        raise

    
if __name__ == "__main__":
    main()