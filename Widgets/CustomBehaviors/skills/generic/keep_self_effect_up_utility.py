from tkinter.constants import N
from typing import Any
from typing import Generator
from typing import override

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class KeepSelfEffectUpUtility(CustomSkillUtilityBase):
    def __init__(self, 
    skill: CustomSkill, 
    current_build: list[CustomSkill], 
    score_definition: ScoreStaticDefinition,
    mana_required_to_cast: int = 0,
    renew_before_expiration_in_milliseconds: int = 200,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO]
    ) -> None:

        super().__init__(
            skill=skill, 
            in_game_build=current_build, 
            score_definition=score_definition, 
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition
        self.renew_before_expiration_in_milliseconds: int = renew_before_expiration_in_milliseconds

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        has_buff = Routines.Checks.Effects.HasBuff(GLOBAL_CACHE.Player.GetAgentID(), self.custom_skill.skill_id)
        if not has_buff: return self.score_definition.get_score()
        
        buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(GLOBAL_CACHE.Player.GetAgentID(), self.custom_skill.skill_id)
        if buff_time_remaining <= self.renew_before_expiration_in_milliseconds: return self.score_definition.get_score()
        
        return None

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result