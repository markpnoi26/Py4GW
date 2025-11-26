

from Py4GW import Console
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog

PERSISTENT = True

class InstanceManager:
    _initialized = False
    _instance = None

    def __new__(cls, inventory_handler = None):
        if cls._instance is None:
            cls._instance = super(InstanceManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, inventory_handler = None):
        if self._initialized:
            return
        
        from Py4GWCoreLib.py4gwcorelib_src.MerchantHandler import MerchantHandler
        from Py4GWCoreLib.py4gwcorelib_src.AutoInventoryHandler import AutoInventoryHandler
        from Widgets.frenkey.LootEx.inventory_handling import LootEx_Merchant_Handler, LootExAutoInventoryHandler
        
        if getattr(self, "merchant_handler", None) is None:
            self.merchant_handler = MerchantHandler()
            ConsoleLog("InventoryHandler", f"Initialized default MerchantHandler: {self.merchant_handler._instance}.", Console.MessageType.Debug)
        
        if getattr(self, "lootex_merchant_handler", None) is None:
            self.lootex_merchant_handler = LootEx_Merchant_Handler(inventory_handler)
            ConsoleLog("InventoryHandler", f"Initialized default LootEx_Merchant_Handler: {self.lootex_merchant_handler._instance}.", Console.MessageType.Debug)
            
        if getattr(self, "auto_inventory_handler", None) is None:
            self.auto_inventory_handler = AutoInventoryHandler()
        
        if getattr(self, "lootex_auto_inventory_handler", None) is None:
            self.lootex_auto_inventory_handler = LootExAutoInventoryHandler(inventory_handler)      
    
                  
    