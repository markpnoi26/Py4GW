from typing import Any
from typing import Callable
from typing import Generator
from typing import override

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class PowerDrainUtility(CustomSkillUtilityBase):

    def __init__(self, 
                    current_build: list[CustomSkill], 
                    score_definition: ScoreStaticDefinition = ScoreStaticDefinition(82),
            ) -> None:

            super().__init__(
                skill=CustomSkill("Power_Drain"), 
                in_game_build=current_build, 
                score_definition=score_definition)
            
            self.score_definition: ScoreStaticDefinition = score_definition

    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        
        if custom_behavior_helpers.Resources.get_player_absolute_energy() > 30 : return None
        if self.nature_has_been_attempted_last(previously_attempted_skills): return None
        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:

        action: Callable[[], Generator[Any, Any, BehaviorResult]] = lambda: (yield from custom_behavior_helpers.Actions.cast_skill_to_lambda(
            skill=self.custom_skill,
            select_target=lambda: custom_behavior_helpers.Targets.get_first_or_default_from_enemy_ordered_by_priority(
                within_range=Range.Spellcast,
                condition=lambda agent_id: GLOBAL_CACHE.Agent.IsCasting(agent_id) and 
                GLOBAL_CACHE.Skill.Flags.IsSpell(GLOBAL_CACHE.Agent.GetCastingSkill(agent_id)) and 
                GLOBAL_CACHE.Skill.Data.GetActivation(GLOBAL_CACHE.Agent.GetCastingSkill(agent_id)) >= 0.250,
                sort_key=(TargetingOrder.AGENT_QUANTITY_WITHIN_RANGE_DESC, TargetingOrder.CASTER_THEN_MELEE),
                range_to_count_enemies=GLOBAL_CACHE.Skill.Data.GetAoERange(self.custom_skill.skill_id))
        ))

        result: BehaviorResult = yield from custom_behavior_helpers.Helpers.wait_for_or_until_completion(500, action)
        return result 