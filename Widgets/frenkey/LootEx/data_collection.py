
from enum import IntEnum
import re
from typing import Optional, Sequence

from Py4GW import Console
from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.GlobalCache.ItemCache import Bag_enum
from Py4GWCoreLib.UIManager import UIManager
from Py4GWCoreLib.enums_src.GameData_enums import Attribute, Profession
from Py4GWCoreLib.enums_src.Item_enums import ItemType, Rarity
from Py4GWCoreLib.enums_src.Model_enums import ModelID
from Py4GWCoreLib.enums_src.Region_enums import ServerLanguage
from Py4GWCoreLib.enums_src.UI_enums import NumberPreference
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Py4GWCoreLib.py4gwcorelib_src.Timer import ThrottledTimer
from Widgets.frenkey.LootEx import enum, messaging, ui_manager_extensions, utility
from Widgets.frenkey.LootEx.models import Item, ItemModifiersInformation, ItemsByType, WeaponMod


ALL_BAGS = GLOBAL_CACHE.ItemArray.CreateBagList(*range(Bag_enum.Backpack.value, Bag_enum.Max.value))
XUNLAI_STORAGE = GLOBAL_CACHE.ItemArray.CreateBagList(*range(Bag_enum.Storage_1.value, Bag_enum.Storage_14.value))
CHARACTER_INVENTORY = GLOBAL_CACHE.ItemArray.CreateBagList(*range(Bag_enum.Backpack.value, Bag_enum.Equipment_Pack.value), Bag_enum.Equipped_Items.value)

class CollectionStatus(IntEnum):
    Unknown = 0
    NameRequested = 1
    NameCollected = 2
    RequiresSave = 3
    
    BetterDataFound = 9
    DataCollected = 10

class CollectionEntry(Item):
    def __init__(self, item_id: int):                                       
        item_type_value, _ = GLOBAL_CACHE.Item.GetItemType(item_id)
        item_type : ItemType = ItemType(item_type_value) if item_type_value in ItemType._value2member_map_ else ItemType.Unknown        
        
        model_id = GLOBAL_CACHE.Item.GetModelID(item_id)
        
        super().__init__(model_id, item_type)        
        self.from_data(model_id, item_type)
        
        self.item_id = item_id
        self.status = CollectionStatus.Unknown
        self.changed : bool = False
        
        rarity, _ = GLOBAL_CACHE.Item.Rarity.GetRarity(item_id)
        self.rarity = Rarity(rarity) if rarity in Rarity._value2member_map_ else Rarity.White
        self.quantity = GLOBAL_CACHE.Item.Properties.GetQuantity(item_id)
        
        self.raw_name = ""
        self.unformatted_name = ""    
        self.mods_info = ItemModifiersInformation.GetModsFromModifiers(GLOBAL_CACHE.Item.Customization.Modifiers.GetModifiers(self.item_id), self.item_type, self.model_id, GLOBAL_CACHE.Item.Customization.IsInscribable(self.item_id))

        self.get_profession()
        self.get_attributes()
        self.get_model_file_id()
    
    def get_model_file_id(self):
        model_file_id = GLOBAL_CACHE.Item.GetModelFileID(self.item_id)
        if model_file_id != self.model_file_id:
            self.model_file_id = model_file_id
            self.changed = True
    
    def get_attributes(self):    
        if not utility.Util.IsWeaponType(self.item_type):
            return
        
        if self.mods_info.attribute != Attribute.None_ and self.mods_info.attribute not in self.attributes:
            self.attributes = self.attributes + [self.mods_info.attribute]
            self.changed = True
    
    def get_profession(self):  
        pv = GLOBAL_CACHE.Item.Properties.GetProfession(self.item_id)
        profession = Profession(pv) if pv in Profession._value2member_map_ else None
        if profession and profession != Profession._None:
            if profession != self.profession:
                self.profession = profession
                self.changed = True
                    
    def has_name(self, language : ServerLanguage) -> bool:
        return self.names.get(language, "") != ""

    def from_data(self, model_id: int, item_type: ItemType):
        from Widgets.frenkey.LootEx.data import Data
        data = Data()
        
        item_data = data.Items.get_item(item_type, model_id)
        
        if item_data is not None:                    
            self.model_id = item_data.model_id
            self.model_file_id = item_data.model_file_id
            self.item_type = item_data.item_type
            self.name = item_data.name
            self.names = item_data.names.copy()
            self.drop_info = item_data.drop_info
            self.attributes = item_data.attributes.copy()
            self.wiki_url = item_data.wiki_url
            self.common_salvage = item_data.common_salvage
            self.rare_salvage = item_data.rare_salvage
            self.nick_index = item_data.nick_index
            self.profession = item_data.profession
            self.contains_amount = item_data.contains_amount
            self.inventory_icon = item_data.inventory_icon
            self.inventory_icon_url = item_data.inventory_icon_url
            self.category = item_data.category
            self.sub_category = item_data.sub_category
            self.wiki_scraped = item_data.wiki_scraped
            self.is_account_data = item_data.is_account_data            
            
    def request_name(self):
        GLOBAL_CACHE.Item.GetName(self.item_id)
        self.status = CollectionStatus.NameRequested
        
    def set_name(self, name: str, language: ServerLanguage = ServerLanguage.English):
        self.raw_name = name
        self.unformatted_name = self.get_name_unformatted(name)
        self.get_mods_names(self.unformatted_name, language)
        
        self.names[language] = self.get_cleaned_item_name(self.unformatted_name, language)
        self.status = CollectionStatus.NameCollected
        self.changed = True
            
    def reformat_string(self, item_name: str) -> str:
        # split on uppercase letters
        item_name = re.sub(r"([a-z])([A-Z])", r"\1 \2", item_name)

        # replace underscores with spaces
        item_name = item_name.replace("_", " ")

        # replace multiple spaces with a single space
        item_name = re.sub(r"\s+", " ", item_name)

        # strip leading and trailing spaces
        item_name = item_name.strip()

        return item_name
    
    def get_name_unformatted(self, item_name) -> str:
        #Remove markups <c=..>...</c> etc.
        while True:
            new_item_name = re.sub(r"<c=[^>]+>(.*?)</c>", r"\1", item_name)
            if new_item_name == item_name:
                break
            
            item_name = new_item_name
            
        return item_name.strip()
    
    def get_cleaned_item_name(self, item_name : str, server_language: ServerLanguage) -> str:  
        from Widgets.frenkey.LootEx.data import Data
        data = Data()
        
        from Widgets.frenkey.LootEx.models import RuneModInfo, WeaponModInfo
                
        if item_name == "STRING DO NOT LOCALIZE":
            item = data.Items.get_item(self.item_type, self.model_id)
            if item is not None:
                item_name = item.names.get(ServerLanguage.English, "")

        if item_name is None or item_name == "":
            return ""

        if self.rarity == Rarity.Green:
            # If the item is a green item, we don't need to cleanup the item name
            return item_name
                
        if utility.Util.IsWeaponType(self.item_type) or utility.Util.IsArmorType(self.item_type) or self.item_type == ItemType.Rune_Mod:
            mods, runes = self.mods_info.weapon_mods, self.mods_info.runes
            is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(self.item_id)

            if not is_identified and not GLOBAL_CACHE.Item.Properties.IsCustomized(self.item_id) and (utility.Util.IsWeaponType(self.item_type) or self.item_type == ItemType.Salvage):
                return item_name.strip()

            if len(mods) > 0:
                for mod in mods:                    
                    suffix = ("Minor" if mod.Rune.rarity == Rarity.Blue else "Major" if mod.Rune.rarity == Rarity.Purple else "Superior" if mod.Rune.rarity == Rarity.Gold else "") if mod in runes and isinstance(mod, RuneModInfo) else ""
                    
                    if mod.Mod.mod_type == enum.ModType.Inherent:
                        # If the mod is inherent, we don't need to cleanup the item name as its not affected by the mod
                        continue
                    
                    if mod.Mod.mod_type == enum.ModType.Prefix:
                        if self.item_type == ItemType.Rune_Mod or not GLOBAL_CACHE.Item.Customization.IsPrefixUpgradable(self.item_id):
                            continue
                        
                    if mod.Mod.mod_type == enum.ModType.Suffix:
                        if not GLOBAL_CACHE.Item.Customization.IsSuffixUpgradable(self.item_id):
                            continue

                    if server_language == ServerLanguage.Italian:
                        ## Get all gender versions of the mod name and replace them
                        for c in ("o", "a", "i", "e"):
                            ## replace the last chacter with the current character
                            mod_name = mod.Mod.applied_name[:-1] + c
                            item_name = item_name.replace(mod_name, "").strip()
                    
                    item_name = item_name.replace(mod.Mod.applied_name, "").strip()
                    
                    if item_name.startswith("-"):
                        item_name = item_name[1:].strip()
                    
                    if self.item_type == ItemType.Rune_Mod:
                        item_name += f" ({suffix})"
                        
            if self.item_type == ItemType.Rune_Mod:
                if utility.Util.is_inscription_model_item(self.model_id):
                    inscription = {
                        ServerLanguage.English: r"Inscription",
                        ServerLanguage.German: r"Inschrift",
                        ServerLanguage.French: r"Inscription",
                        ServerLanguage.Spanish: r"Inscripción",
                        ServerLanguage.Italian: r"Iscrizione",
                        ServerLanguage.TraditionalChinese: r"鑄印",
                        ServerLanguage.Korean: r"마력석",
                        ServerLanguage.Japanese: r"刻印",
                        ServerLanguage.Polish: r"Inskrypcja",
                        ServerLanguage.Russian: r"Надпись",
                        ServerLanguage.BorkBorkBork: r"Inscreepshun"
                    }

                    target_item_type = utility.Util.get_target_item_type_from_mod(self.item_id)
                    
                    # If the item is an inscription model item, we don't need to cleanup the item name
                    return f"{inscription.get(server_language, 'Inscription')}: {self.reformat_string(target_item_type.name) if target_item_type else ''}".strip()       

        if self.quantity > 1:
            item_name = item_name.replace(str(self.quantity), "250").strip()

        return item_name
    
    def get_mods_names(self, item_name, server_language: ServerLanguage):  
        from Widgets.frenkey.LootEx.data import Data
        data = Data()
        
        global save_weapon_mods

        def extract_mod_name(item_name : str, mod_type: enum.ModType = enum.ModType.None_) -> Optional[str]:
            patterns = {}

            match mod_type:
                case enum.ModType.Prefix:
                    patterns = {}

                case enum.ModType.Inherent:
                    patterns = {
                        ServerLanguage.English: r"Inscription: ",
                        ServerLanguage.German: r"Inschrift: ",
                        ServerLanguage.French: r"Inscription : ",
                        ServerLanguage.Spanish: r"Inscripción: ",
                        ServerLanguage.Italian: r"Iscrizione: ",
                        ServerLanguage.TraditionalChinese: r"鑄印：",
                        ServerLanguage.Korean: r"마력석:",
                        ServerLanguage.Japanese: r"刻印：",
                        ServerLanguage.Polish: r"Inskrypcja: ",
                        ServerLanguage.Russian: r"Надпись: ",
                        ServerLanguage.BorkBorkBork: r"Inscreepshun: "
                    }

                case enum.ModType.Suffix:
                    patterns = {
                        ServerLanguage.English: r"^.*?(?= of)",
                        ServerLanguage.German: r"^.*(?= d\.)",
                        ServerLanguage.French: r"^.*?(?=\()",
                        ServerLanguage.Spanish: r"^.*?(?=\()",
                        ServerLanguage.Italian: r"^.*(?= del)",
                        ServerLanguage.TraditionalChinese: r" .*$",
                        ServerLanguage.Japanese: r"^.*?(?=\()",
                        ServerLanguage.Korean: r"^.*?(?=\()",
                        ServerLanguage.Polish: r"^.*?(?=\()",
                        ServerLanguage.Russian: r"^.*?(?= of)",
                        ServerLanguage.BorkBorkBork: r"^.*?(?= ooff)",
                    }

            pattern = patterns.get(server_language, None)

            if item_name is None or item_name == "" or pattern is None:
                return None

            if pattern:
                item_name = re.sub(pattern, '', item_name)
            return item_name.strip()

        is_identified = GLOBAL_CACHE.Item.Usage.IsIdentified(self.item_id)
        if not is_identified and self.item_type != ItemType.Rune_Mod:
            return
    
        if self.item_type == ItemType.Rune_Mod:
            mods = self.mods_info.weapon_mods

            if len(mods) > 0:
                for mod in mods:
                    if not mod.WeaponMod.identifier in data.Weapon_Mods:
                        continue

                    if not data.Weapon_Mods[mod.WeaponMod.identifier].names:
                        data.Weapon_Mods[mod.WeaponMod.identifier].names = {}
                    mod_name = extract_mod_name(item_name, mod.WeaponMod.mod_type)
                    if mod_name == "" or mod_name is None:
                        continue

                    if utility.Util.is_inscription_model_item(self.model_id) != (mod.Mod.mod_type == enum.ModType.Inherent):
                        continue

                    item_type = utility.Util.get_target_item_type_from_mod(
                        self.item_id) if self.item_type == ItemType.Rune_Mod else self.item_type

                    if item_type == None:
                        continue

                    item_type_match = any(utility.Util.IsMatchingItemType(
                        item_type, target_type) for target_type in mod.WeaponMod.target_types) if mod.WeaponMod.target_types else True

                    if item_type_match is False:
                        continue

                    if server_language in data.Weapon_Mods[mod.WeaponMod.identifier].names and data.Weapon_Mods[mod.WeaponMod.identifier].names[server_language] is not None:
                        # ConsoleLog(
                        #     "LootEx", f"Mod name already exists for {self.server_language.name}: {data.Weapon_Mods[index].names[self.server_language]} ({item_id})", Console.MessageType.Debug)
                        continue

                    if mod.WeaponMod.mod_type == enum.ModType.Prefix:
                        # There is no way to gurantee to get the correct prefix name without knowing the item name
                        continue

                    if mod.WeaponMod.mod_type == enum.ModType.Inherent:
                        ConsoleLog(
                            "LootEx", f"Setting Inherent mod name for: {data.Weapon_Mods[mod.WeaponMod.identifier].applied_name} to {mod_name}", Console.MessageType.Debug)
                        data.Weapon_Mods[mod.WeaponMod.identifier].set_name(
                            mod_name, server_language)
                        DataCollector().modified_weapon_mods[mod.WeaponMod.identifier] = data.Weapon_Mods[mod.WeaponMod.identifier]
                        continue

                    if mod.WeaponMod.mod_type == enum.ModType.Suffix:
                        ConsoleLog(
                            "LootEx", f"Setting Suffix mod name for: {data.Weapon_Mods[mod.WeaponMod.identifier].applied_name} to {mod_name}", Console.MessageType.Debug)
                        data.Weapon_Mods[mod.WeaponMod.identifier].set_name(
                            mod_name, server_language)
                        save_weapon_mods = True
                        DataCollector().modified_weapon_mods[mod.WeaponMod.identifier] = data.Weapon_Mods[mod.WeaponMod.identifier]
                        continue

class DataCollector:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(DataCollector, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
    
        from Widgets.frenkey.LootEx.settings import Settings
        
        self.settings = Settings()
        self.modified_items: ItemsByType = ItemsByType()
        self.modified_weapon_mods: dict[str, WeaponMod] = {}
        
        self._initialized = True
        self.server_language = ServerLanguage.Unknown
        self.collected_items : dict[int, CollectionEntry] = {}
                
        self.throttle = ThrottledTimer(1250)
        self.throttle.Start()
        
        self.fetched_cycles = 0
    
    def hasItem(self, item_id: int) -> bool:
        return item_id in self.collected_items and self.collected_items[item_id].status not in [CollectionStatus.NameRequested, CollectionStatus.NameCollected]
    
    def reset(self):
        if self.collected_items:
            ConsoleLog("LootEx DataCollector", f"Resetting data collector. Cleared {len(self.collected_items)} collected items.", Console.MessageType.Info)
        
        # self.throttle.Stop()
        self.fetched_cycles = 0
        self.collected_items.clear()
        GLOBAL_CACHE._reset()
    
    def reset_cache(self):
        GLOBAL_CACHE._reset()
        
        for _, entry in self.collected_items.items():
            if entry.status is not CollectionStatus.BetterDataFound:
                entry.request_name()
                
    def save_items(self, items: list[CollectionEntry]):
        from Widgets.frenkey.LootEx.data import Data
        data = Data()
        
        if self.modified_weapon_mods:
            data.SaveWeaponMods(shared_file=False, mods=self.modified_weapon_mods)
            self.modified_weapon_mods.clear()
        
        if not items or len(items) == 0:
            return
        
        for item in items:
            self.modified_items.add_item(item)
        
        ConsoleLog("LootEx DataCollector", f"Data collection run complete. Collected new data for {len(items)} items.", Console.MessageType.Info)    
        data.SaveItems(shared_file=False, items=self.modified_items)
        
        for item in items:
            item.status = CollectionStatus.DataCollected
            item.changed = False
            
        if Console.is_window_active():
            messaging.SendMergingMessage()
            
        pass
    
    def run(self):            
        if self.throttle.IsExpired():
            self.throttle.Reset()
            
            if self.settings.collect_items:
                preference = UIManager.GetIntPreference(NumberPreference.TextLanguage)
                server_language = ServerLanguage(preference)
                if server_language == ServerLanguage.Unknown:
                    return
                
                if self.server_language != server_language:
                    self.reset_cache()
                    self.server_language = server_language
                
                available_items = self.get_available_items()
                
                for item_id in available_items:
                    if item_id <= 0:
                        continue
                    
                    if item_id not in self.collected_items:
                        entry = CollectionEntry(item_id)
                        self.collected_items[item_id] = entry
                        
                        # Get the existing entries with the same model id and item type
                        existing_entries = [entry for entry in self.collected_items.values() if entry.model_id == entry.model_id and entry.item_type.value == entry.item_type]
                        
                        # We still contain an amount in the name we need to find a single item
                        if entry.contains_amount:
                            if entry.quantity == 1:
                                entry.request_name()
                                
                                # Mark all existing entries as better data found so we don't process them again
                                for existing_entry in existing_entries:
                                    existing_entry.status = CollectionStatus.BetterDataFound
                                
                                continue
                        
                        if not entry.has_name(server_language):
                            entry.request_name()
                            continue
                        
                    entry = self.collected_items.get(item_id)
                    
                    if entry:  
                        if entry.status is CollectionStatus.DataCollected or entry.status is CollectionStatus.BetterDataFound:
                            continue
                                    
                        if entry.status == CollectionStatus.NameRequested:
                            if GLOBAL_CACHE.Item.IsNameReady(item_id):
                                name = GLOBAL_CACHE.Item.GetName(item_id)
                                
                                if not name or name == "No Item":
                                    entry.request_name()
                                    continue
                                
                                entry.set_name(GLOBAL_CACHE.Item.GetName(item_id), server_language)
                                continue
                                                                                    
                        if entry.status == CollectionStatus.NameCollected or (entry.changed and entry.status != CollectionStatus.RequiresSave):
                            ConsoleLog("LootEx DataCollector", f"Collected new data for '{entry.names.get(server_language, '')}'.", Console.MessageType.Info) 
                            entry.status = CollectionStatus.RequiresSave
                            continue
                        
                if self.fetched_cycles >= 3:                                                                 
                    self.save_items([item for item in self.collected_items.values() if item.status == CollectionStatus.RequiresSave])
                    self.fetched_cycles = 0
                    GLOBAL_CACHE.Item.name_cache.clear()
                    GLOBAL_CACHE.Item.name_requested.clear()
                    
                
                self.fetched_cycles += 1
                                            
        pass
    
    def get_available_items(self):        
        merchant_open = ui_manager_extensions.UIManagerExtensions.IsMerchantWindowOpen()
        
        item_array : list[int] = GLOBAL_CACHE.ItemArray.GetItemArray(ALL_BAGS)
        trader_array : list[int] = merchant_open and GLOBAL_CACHE.Trading.Trader.GetOfferedItems() or []
        trader2_array : list[int] = merchant_open and GLOBAL_CACHE.Trading.Trader.GetOfferedItems2() or []
        merchant_array : list[int] = merchant_open and GLOBAL_CACHE.Trading.Merchant.GetOfferedItems() or []
        crafter_array : list[int] = ui_manager_extensions.UIManagerExtensions.IsCrafterOpen() and GLOBAL_CACHE.Trading.Crafter.GetOfferedItems() or []
        collector_array : list[int] = ui_manager_extensions.UIManagerExtensions.IsCollectorOpen() and GLOBAL_CACHE.Trading.Collector.GetOfferedItems() or []
        
        all_arrays = item_array + trader_array  + trader2_array + merchant_array + crafter_array + collector_array
        
        # Placeholder for actual implementation
        return all_arrays