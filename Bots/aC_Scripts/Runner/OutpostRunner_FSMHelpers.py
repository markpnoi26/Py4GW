import importlib
import os
from Py4GWCoreLib import *
from map_loader import load_map_data

class OutpostRunnerFSMHelpers:
    def __init__(self):
        self.current_map_script = None
        self.current_map_data = None


    def load_map_script(self, script_name):
        """
        Given a chain entry like:
            "Eye_Of_The_North__1_Eotn_To_Gunnars"
        (note the DOUBLE-underscore between region and run),
        split it properly and delegate to map_loader.
        """
        # split on the double-underscore delimiter
        if "__" in script_name:
            region, run = script_name.split("__", 1)
        else:
            # fallback (shouldn't happen with our UI)
            region, run = script_name.split("_", 1)

        # now load the Python file at maps/<region>/<run>.py
        data = load_map_data(region, run)
        self.current_map_data = data
        return {
            "outpost_path":     data["outpost_path"],
            "segments":         data["segments"],
            "ids":              data["ids"],
        }

    def travel_to_outpost(self, outpost_id):
        """Travel to the required outpost using Yield Travel."""
        ConsoleLog("OutpostRunnerFSM", f"Traveling to outpost ID {outpost_id}")
        return Routines.Yield.Map.TravelToOutpost(outpost_id)

    def wait_for_map_load(self, expected_map_id, timeout=15000):
        """Wait until we’re in the expected map."""
        return Routines.Yield.Map.WaitforMapLoad(expected_map_id, timeout=timeout)

    def follow_path(self, path_coords):
        """Use the official Yield.Path interface for clean navigation (no aggro)."""
        return Routines.Yield.Movement.FollowPath(path_coords)