from Py4GWCoreLib import *
from OutpostRunner_FSM import OutpostRunnerFSM
from map_loader import get_regions, get_runs
from StatsManager import RunInfo
from Py4GWCoreLib import IconsFontAwesome5

# UI state
selected_region = None
selected_run    = None
selected_chain  = []  # e.g. ["EOTN_eotn_to_gunnars"]

# Initialize FSM runner
runner_fsm = OutpostRunnerFSM()

def format_time(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02}:{secs:02}"

def parse_run_filename(region, run_filename):
    name = run_filename.lstrip("_")
    parts = name.split("_")
    order = int(parts[0]) if parts[0].isdigit() else 0
    origin = parts[1]
    destination = parts[-1]
    run_id = f"{region}__{run_filename}"
    # Create a RunInfo with region and run name for later reference (e.g. for restarts)
    return RunInfo(order, run_id, origin, destination, region, run_filename)

def draw_ui():
    global selected_region, selected_run, selected_chain

    if PyImGui.begin("OutpostRunner", PyImGui.WindowFlags.AlwaysAutoResize):
        # --- Region selector ---
        regions = get_regions()
        if regions:
            # default to first if none selected
            r_idx = regions.index(selected_region) if selected_region in regions else 0
            new_r = PyImGui.combo("Region", r_idx, regions)
            # on change, reset run
            if new_r != r_idx:
                selected_region = regions[new_r]
                selected_run    = None
            else:
                selected_region = regions[new_r]

        # --- Run selector ---
        if selected_region:
            runs = get_runs(selected_region)
            if runs:
                u_idx = runs.index(selected_run) if selected_run in runs else 0
                new_u = PyImGui.combo("Run", u_idx, runs)
                selected_run = runs[new_u]

        # --- Add to Chain button ---
        if PyImGui.small_button("Add to Chain"):
            run_info = parse_run_filename(selected_region, selected_run)
            if not any(r.id == run_info.id for r in selected_chain):
                selected_chain.append(run_info)

        # --- Show current chain ---
        PyImGui.text("Current Chain:")
        for idx, run in enumerate(sorted(selected_chain, key=lambda r: r.order)):
            PyImGui.text(f"{run.order} - {run.display}")
            PyImGui.same_line(0, 0)
            if PyImGui.small_button(f"Remove##{idx}"):
                selected_chain.pop(idx)

        # --- Start Run / Stop buttons ---
        if PyImGui.button("Start Run"):
            if selected_chain:
                runner_fsm.set_map_chain(sorted(selected_chain, key=lambda r: r.order))
                runner_fsm.start()
            else:
                ConsoleLog("OutpostRunner", "No runs in chain!")
        # Always show a Stop button to allow aborting the run at any time.
        PyImGui.same_line(0, 5)
        if PyImGui.button("Stop"):
            runner_fsm.reset()
            # This stops all coroutines and resets the FSM and stats manager.

        # ... after Start/Stop buttons:
        skill_status = "Running" if runner_fsm.skill_coroutine else "Stopped"
        overwatch_status = "Running" if runner_fsm.overwatch._active else "Stopped"
        PyImGui.text(f"Skillcasting: {skill_status}")
        PyImGui.text(f"Overwatch: {overwatch_status}")

        stats = getattr(runner_fsm, "chain_stats", None)
        if stats is not None and stats.runs:
            PyImGui.separator()
            PyImGui.text(f"Chain total time: {format_time(stats.total_chain_time())}")
            PyImGui.text(f"Runs completed: {stats.runs_completed()}/{len(stats.runs)}")
            PyImGui.text(f"Runs failed: {stats.runs_failed()}")

            for r in stats.runs:
                if r.finished:
                    PyImGui.text(f"{r.order}: {r.display} - Done: {format_time(r.duration)} {IconsFontAwesome5.ICON_CHECK} (fails:{r.failures})")
                elif r.started:
                    PyImGui.text(f"{r.order}: {r.display} {IconsFontAwesome5.ICON_RUNNING} in progress")
                else:
                    PyImGui.text(f"{r.order}: {r.display} {IconsFontAwesome5.ICON_PAUSE_CIRCLE} not started")

    PyImGui.end()

def main():
    draw_ui()
    runner_fsm.fsm.update()
