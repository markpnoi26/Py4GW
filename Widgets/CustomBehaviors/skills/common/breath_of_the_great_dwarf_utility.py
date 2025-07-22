from typing import Any
from typing import Generator
from typing import override

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.healing_score import HealingScore
from Widgets.CustomBehaviors.primitives.scores.score_per_health_gravity_definition import (
    ScorePerHealthGravityDefinition,
)
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class BreathOfTheGreatDwarfUtility(CustomSkillUtilityBase):
    def __init__(
        self, 
        current_build: list[CustomSkill], 
        score_definition: ScorePerHealthGravityDefinition = ScorePerHealthGravityDefinition(1), 
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:
            
            super().__init__(
                skill=CustomSkill("Breath_of_the_Great_Dwarf"),
                in_game_build=current_build, 
                score_definition=score_definition, 
                allowed_states=allowed_states)
            
            self.score_definition: ScorePerHealthGravityDefinition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        if custom_behavior_helpers.Heals.is_party_damaged(within_range=Range.Spirit, min_allies_count=3, less_health_than_percent=0.4):
            return self.score_definition.get_score(HealingScore.PARTY_DAMAGE_EMERGENCY)

        first_member_damaged: int | None = custom_behavior_helpers.Heals.get_first_member_damaged(within_range=Range.Spirit, less_health_than_percent=0.4, exclude_player=False)
        if first_member_damaged is not None:
            return self.score_definition.get_score(HealingScore.MEMBER_DAMAGED_EMERGENCY)

        if custom_behavior_helpers.Heals.is_party_damaged(within_range=Range.Spirit, min_allies_count=3, less_health_than_percent=0.6):
            return self.score_definition.get_score(HealingScore.PARTY_DAMAGE)

        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result 