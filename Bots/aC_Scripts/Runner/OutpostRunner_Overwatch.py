# OutpostRunner_Overwatch.py

import time

import map_loader

from Py4GWCoreLib import *
from Widgets.Messaging import SharedCommandType


class OutpostRunnerOverwatch:
    """
    Overwatch monitor for OutpostRunner.
    Runs as a coroutine to detect death/stuck conditions
    and triggers a resign/reset sequence.
    """

    def __init__(self, fsm_runner):
        """
        fsm_runner: instance of OutpostRunnerFSM (so we can call its restart, stop_skill_casting, etc.)
        """
        self.runner = fsm_runner
        self._coroutine = None
        self._active = False
        self._stuck_threshold = 15  # seconds of no movement before considered stuck

    def start(self):
        """Start overwatch coroutine"""
        if self._coroutine is None:
            self._active = True
            self._coroutine = self._loop()
            GLOBAL_CACHE.Coroutines.append(self._coroutine)
            ConsoleLog("OutpostRunnerFSM", "Overwatch started (monitoring stuck/death).")

    def stop(self):
        """Stop overwatch coroutine"""
        self._active = False
        if self._coroutine and self._coroutine in GLOBAL_CACHE.Coroutines:
            GLOBAL_CACHE.Coroutines.remove(self._coroutine)
        self._coroutine = None
        ConsoleLog("OutpostRunnerFSM", "Overwatch stopped.")

    def _loop(self):
        """Coroutine that yields and monitors player state"""
        
        # Always initialize safely, even if GetXY() returns None during load
        prev_pos = GLOBAL_CACHE.Player.GetXY() or (0.0, 0.0)
        last_move_time = time.time()

        def _generator():
            nonlocal prev_pos, last_move_time  # allow inner function to modify

            while True:
                # Stop if overwatch is no longer active
                if not self._active:
                    return  # Exit the coroutine cleanly

                # Skip checks during loading/zoning to avoid false stuck detection
                if not Routines.Checks.Map.MapValid():
                    yield from Routines.Yield.wait(1000)
                    # After zoning, reinitialize movement tracking
                    new_pos = GLOBAL_CACHE.Player.GetXY()
                    if new_pos:
                        prev_pos = new_pos
                    last_move_time = time.time()
                    continue

                # --- Death detection ---
                if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                    ConsoleLog("OutpostRunnerFSM", "⚠ Overwatch: Player died - resetting run.", Console.MessageType.Warning)
                    yield from self._trigger_resign_and_restart()
                    return

                # --- Stuck detection ---
                current_pos = GLOBAL_CACHE.Player.GetXY() or prev_pos
                if current_pos == prev_pos:
                    if time.time() - last_move_time > self._stuck_threshold:
                        ConsoleLog("OutpostRunnerFSM", f"⚠ Overwatch: Player stuck >{self._stuck_threshold}s - resetting run.", Console.MessageType.Warning)
                        yield from self._trigger_resign_and_restart()
                        return
                else:
                    # Player moved → reset timer
                    prev_pos = current_pos
                    last_move_time = time.time()

                # Sleep 1 second between checks
                yield from Routines.Yield.wait(1000)

        return _generator()

    def _trigger_resign_and_restart(self):
        # Mark current run failed
        current_run = next((r for r in self.runner.map_chain if r.started and not r.finished), None)
        if current_run:
            current_run.failures += 1

        # Stop FSM + buffs
        self.runner.soft_reset_for_retry()

        # Resign self
        ConsoleLog("OutpostRunnerFSM", "Overwatch: Sending /resign.", Console.MessageType.Info)
        GLOBAL_CACHE.Player.SendChatCommand("resign")

        # Broadcast resign for multi-box team
        accounts = GLOBAL_CACHE.ShMem.GetAllAccountData()
        sender_email = GLOBAL_CACHE.Player.GetAccountEmail()
        for account in accounts:
            ConsoleLog("Messaging", "Resigning account: " + account.AccountEmail)
            GLOBAL_CACHE.ShMem.SendMessage(sender_email, account.AccountEmail, SharedCommandType.Resign, (0,0,0,0))

        # Find unfinished runs
        if current_run:
            # Ensure region/run_name are present (parse from ID if missing)
            region = getattr(current_run, 'region', None)
            run_name = getattr(current_run, 'run_name', None)
            if not region or not run_name:
                if "__" in current_run.id:
                    region, run_name = current_run.id.split("__", 1)
                    current_run.region = region
                    current_run.run_name = run_name

            # Load map data for the same run we failed
            import map_loader
            data = map_loader.load_map_data(current_run.region, current_run.run_name)
            outpost_id = data["ids"]["outpost_id"]
            ConsoleLog("Overwatch", f"Retrying FAILED run: region={current_run.region}, run={current_run.run_name}, full_id={current_run.id}", Console.MessageType.Info)
            
            #  Wait for outpost map to load
            ConsoleLog("OutpostRunnerFSM", f"Waiting for outpost {outpost_id} to load...", Console.MessageType.Info)
            loaded_ok = yield from Routines.Yield.Map.WaitforMapLoad(outpost_id, log=True)
            if not loaded_ok:
                ConsoleLog("OutpostRunnerFSM", "Map load timeout, stopping script.", Console.MessageType.Error)
                self.runner._stop_skill_casting()
                return

            # Retry ONLY the failed run
            ConsoleLog("OutpostRunnerFSM", f"Restarting same run: {current_run.display}", Console.MessageType.Info)
            self.runner.set_map_chain([current_run])  # retry same run
            self.runner.start()
        else:
            ConsoleLog("OutpostRunnerFSM", "All runs finished, nothing to resume.", Console.MessageType.Info)