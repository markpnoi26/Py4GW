from typing import Any
from typing import Callable
from typing import Generator
from typing import List
from typing import override

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import (
    ScorePerAgentQuantityDefinition,
)
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class ShatterEnchantmentUtility(CustomSkillUtilityBase):
    def __init__(self, 
        current_build: list[CustomSkill], 
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(10),
        mana_required_to_cast: int = 20,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            skill=CustomSkill("Shatter_Enchantment"), 
            in_game_build=current_build, 
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition

    def _get_targets(self) -> list[custom_behavior_helpers.SortableAgentData]:
        
        targets = custom_behavior_helpers.Targets.get_all_possible_enemies_ordered_by_priority_raw(
                    within_range=Range.Spellcast,
                    condition=lambda agent_id: GLOBAL_CACHE.Agent.IsEnchanted(agent_id),
                    sort_key=(TargetingOrder.HP_ASC, TargetingOrder.DISTANCE_ASC))

        return targets

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        targets = self._get_targets()
        if len(targets) == 0: return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        enemies = self._get_targets()
        if len(enemies) == 0: return BehaviorResult.ACTION_SKIPPED
        target = enemies[0]
        result = yield from custom_behavior_helpers.Actions.cast_skill_to_target(self.custom_skill, target_agent_id=target.agent_id)
        return result