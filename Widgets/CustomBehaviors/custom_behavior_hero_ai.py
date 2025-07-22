from Py4GWCoreLib.Py4GWcorelib import ActionQueueManager
from Widgets.CustomBehaviors.primitives.custom_behavior_loader import CustomBehaviorLoader


def execute_enhanced_custom_heroai_combat():
    CustomBehaviorLoader().initialize_custom_behavior_candidate()

    custom_combat_behavior = CustomBehaviorLoader().custom_combat_behavior

    if custom_combat_behavior is not None:
        CustomBehaviorLoader().ensure_custom_behavior_match_in_game_build()

    if custom_combat_behavior:
        custom_combat_behavior.hero_ai_execute()

    ActionQueueManager().ProcessQueue("ACTION")
