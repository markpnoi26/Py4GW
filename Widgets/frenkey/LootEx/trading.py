from datetime import datetime
from enum import Enum
import math
from typing import Callable, Generator

from Py4GW import Console
from PyItem import PyItem

from Py4GWCoreLib.GlobalCache import GLOBAL_CACHE
from Py4GWCoreLib.Inventory import Inventory
from Py4GWCoreLib.Merchant import Trading
from Py4GWCoreLib.py4gwcorelib_src.Console import ConsoleLog
from Widgets.frenkey.LootEx import utility
from Widgets.frenkey.LootEx.cache import Cached_Item
from Widgets.frenkey.LootEx.enum import MAX_CHARACTER_GOLD, MAX_VAULT_GOLD, MerchantType

class TraderActionState(Enum):
    Pending = 0
    Running = 1
    Completed = 2
    Timeout = 3

class ActionType(Enum):
    Buy = 1
    Sell = 2

class TraderCoroutine:
    def __init__(self, generator_fn: Callable[[], Generator], timeout_seconds: float = 5.0):
        self.generator_fn = generator_fn
        self.generator = None
        self.state = TraderActionState.Pending
        self.started_at = datetime.min
        # self.timeout_seconds = timeout_seconds

    def step(self) -> TraderActionState:
        """
        Advances the coroutine by one 'yield'.
        Returns its current state.
        """
        # Start coroutine if not running yet
        if self.state == TraderActionState.Pending:
            self.generator = self.generator_fn()
            self.state = TraderActionState.Running
            self.started_at = datetime.now()

        # # Timeout?
        # if (datetime.now() - self.started_at).total_seconds() > self.timeout_seconds:
        #     self.state = TraderActionState.Timeout
        #     return self.state

        # Advance generator one step
        try:
            if self.generator is not None:
                next(self.generator)
                return self.state  # still Running
            
            else:
                self.state = TraderActionState.Completed
                return self.state

        except StopIteration:
            self.state = TraderActionState.Completed
            return self.state

        except Exception as e:
            ConsoleLog("LootEx", f"Coroutine error: {e}", Console.MessageType.Error)
            self.state = TraderActionState.Timeout
            return self.state
            
class TraderAction:
    def __init__(self, item: Cached_Item, trader_type: MerchantType, action: ActionType, desired_quantity: int = -1):
        self.item = item
        self.action = action
        self.trader_type = trader_type
        self.price: int = -1
        self.initial_quantity: int = item.quantity

        # Determine target quantity
        if desired_quantity == -1:
            # Sell until zero
            # Buy until 1
            self.desired_quantity = 0 if action == ActionType.Sell else 1
        else:
            self.desired_quantity = desired_quantity

        self.coroutine: TraderCoroutine | None = None

    # Entry point
    def run(self) -> TraderCoroutine:
        return TraderCoroutine(self._gen_main)

    # Main generator function
    def _gen_main(self) -> Generator:
        """
        Loop until quantity objective is reached:
        - For Buy: item.quantity >= desired_quantity
        - For Sell: item.quantity <= desired_quantity
        """
        ConsoleLog(
            "LootEx",
            f"Starting TraderAction for {self.item.name} ({self.item.id}), "
            f"mode={self.action.name}, desired={self.desired_quantity}, initial={self.item.quantity}",
            Console.MessageType.Info,
                    False
        )

        while not self._is_done():
            yield from self._request_price()
            yield from self._wait_for_price()
            yield from self._execute_trade()
            yield from self._confirm_trade()

        ConsoleLog(
            "LootEx",
            f"TraderAction for {self.item.name} COMPLETED. Final quantity: {self.item.quantity}",
            Console.MessageType.Info,
                    False
        )

    # Condition to stop the trading action
    def _is_done(self) -> bool:
        self._update_item()
        
        if not self.is_item_valid:
            ConsoleLog(
                "LootEx",
                f"Item {self.item.name} ({self.item.id}) is no longer valid. Ending TraderAction.",
                Console.MessageType.Warning,
                    False
            )
            return True
        
        q = self.item.quantity
        
        current_gold = Inventory.GetGoldOnCharacter()
        vault_gold = Inventory.GetGoldInStorage()
        
        if self.action == ActionType.Buy and self.price > current_gold:
            if vault_gold + current_gold >= self.price:
                ConsoleLog(
                    "LootEx",
                    f"Withdrawing gold from vault to buy {self.item.name} ({self.item.id}). Current gold: {utility.Util.format_currency(current_gold)}, vault gold: {utility.Util.format_currency(vault_gold)}, needed: {utility.Util.format_currency(self.price)}.",
                    Console.MessageType.Info
                )
                Inventory.WithdrawGold(min((self.price * self.desired_quantity) - current_gold + 1000, vault_gold))
                return False
            
            ConsoleLog(
                "LootEx",
                f"Not enough gold to buy {self.item.name} ({self.item.id}). Current gold: {utility.Util.format_currency(current_gold)}, needed: {utility.Util.format_currency(self.price)}. Ending TraderAction.",
                Console.MessageType.Warning
            )
            return True
        
        if self.action == ActionType.Sell and current_gold + self.price > MAX_CHARACTER_GOLD:
            if vault_gold < MAX_VAULT_GOLD:
                ConsoleLog(
                    "LootEx",
                    f"Depositing gold to vault to sell {self.item.name} ({self.item.id}). Current gold: {utility.Util.format_currency(current_gold)}, vault gold: {utility.Util.format_currency(vault_gold)}, after sell: {utility.Util.format_currency(current_gold + self.price)}.",
                    Console.MessageType.Info
                )
                gold_to_deposit = min(math.floor(current_gold / 1000) * 1000, MAX_VAULT_GOLD - vault_gold)
                ConsoleLog(
                    "LootEx",
                    f"Depositing {utility.Util.format_currency(gold_to_deposit)} to vault.",
                    Console.MessageType.Info
                )
                
                Inventory.DepositGold(gold_to_deposit)
                return False
            
            ConsoleLog(
                "LootEx",
                f"Selling {self.item.name} ({self.item.id}) would exceed max gold limit. Current gold: {utility.Util.format_currency(current_gold)}, after sell: {utility.Util.format_currency(current_gold + self.price)}. Ending TraderAction.",
                Console.MessageType.Warning
            )
            return True
              
        # BUY MODE
        if self.action == ActionType.Buy:
            return q >= self.desired_quantity

        # SELL MODE
        if self.item.common_material:
            # cannot stop mid-stack, must stop when <= target
            return q < 10 or q <= self.desired_quantity

        # normal items
        return q <= self.desired_quantity

    # Request a price quote from the merchant
    def _request_price(self) -> Generator:             
        self._update_item()
        if not self.is_item_valid:
            ConsoleLog(
                "LootEx",
                f"Item {self.item.name} ({self.item.id}) is no longer valid. Cannot execute trade.",
                Console.MessageType.Warning,
                    False
            )
            return
        
        msg = "Requesting quote for buying" if self.action == ActionType.Buy else "Requesting quote for selling"

        ConsoleLog(
            "LootEx",
            f"{msg} {self.item.name} ({self.item.id})",
            Console.MessageType.Info,
                    False
        )

        if self.action == ActionType.Buy:
            Trading.Trader.RequestQuote(self.item.id)
        else:
            Trading.Trader.RequestSellQuote(self.item.id)

        self._start_quote_time = datetime.now()
        yield

    # Wait until we receive a price quote
    def _wait_for_price(self) -> Generator:
        while True:     
            self._update_item()
            if not self.is_item_valid:
                ConsoleLog(
                    "LootEx",
                    f"Item {self.item.name} ({self.item.id}) is no longer valid. Cannot execute trade.",
                    Console.MessageType.Warning
                )
                return
            
            quoted_id = Trading.Trader.GetQuotedItemID()
            quoted_value = Trading.Trader.GetQuotedValue()

            if quoted_id == self.item.id and quoted_value >= 0:
                self.price = quoted_value
                ConsoleLog(
                    "LootEx",
                    f"Received quote {quoted_value} for {self.item.name}",
                    Console.MessageType.Info,
                    False
                )
                return

            if (datetime.now() - self._start_quote_time).total_seconds() > 1.0:
                ConsoleLog(
                    "LootEx",
                    f"Quote timeout — requesting new quote for {self.item.name}",
                    Console.MessageType.Warning,
                    False
                )
                if self.action == ActionType.Buy:
                    Trading.Trader.RequestQuote(self.item.id)
                else:
                    Trading.Trader.RequestSellQuote(self.item.id)

                self._start_quote_time = datetime.now()

            yield

    # Execute the trade at the quoted price
    def _execute_trade(self) -> Generator:        
        self._update_item()
        if not self.is_item_valid:
            ConsoleLog(
                "LootEx",
                f"Item {self.item.name} ({self.item.id}) is no longer valid. Cannot execute trade.",
                Console.MessageType.Warning
            )
            return
        
        ConsoleLog(
            "LootEx",
            f"Executing {self.action.name} for {self.item.name} at price {self.price}",
            Console.MessageType.Info,
                    False
        )

        if self.action == ActionType.Buy:
            Trading.Trader.BuyItem(self.item.id, self.price)
        else:
            Trading.Trader.SellItem(self.item.id, self.price)

        self._start_trade_time = datetime.now()
        yield
        
    # Update item validity and quantity
    def _update_item(self) -> None:
        item = PyItem(self.item.id)
        self.is_item_valid = item.IsItemValid(self.item.id) and (self.action is not ActionType.Sell or item.is_inventory_item) if item else False
        self.item.quantity = 0 if not self.is_item_valid else item.quantity

    # Confirm that the trade has completed
    def _confirm_trade(self) -> Generator:
        """
        We watch the item's quantity and wait until it changes.
        Then the trade has completed.
        """
        initial = self.item.quantity
        start = datetime.now()

        while True:            
            self._update_item()
            
            if self.item.quantity != initial:
                ConsoleLog(
                    "LootEx",
                    f"Trade confirmed: {self.item.name} quantity changed {initial} -> {self.item.quantity}",
                    Console.MessageType.Info,
                    False
                )
                return

            if (datetime.now() - start).total_seconds() > 1.5:
                ConsoleLog(
                    "LootEx",
                    f"Trade confirmation TIMEOUT for {self.item.name}",
                    Console.MessageType.Warning
                )
                return

            yield
