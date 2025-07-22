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


class ShroudOfDistressUtility(CustomSkillUtilityBase):
    def __init__(self, 
    current_build: list[CustomSkill], 
    score_definition: ScoreStaticDefinition,
    mana_required_to_cast: int = 0,
    allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO]
    ) -> None:

        super().__init__(
            skill=CustomSkill("Shroud_of_Distress"), 
            in_game_build=current_build, 
            score_definition=score_definition, 
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
        
        self.score_definition: ScoreStaticDefinition = score_definition
        self.renew_before_expiration_in_milliseconds: int = 1200

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        has_shroud_of_distress_buff = Routines.Checks.Effects.HasBuff(GLOBAL_CACHE.Player.GetAgentID(), self.custom_skill.skill_id)
        if has_shroud_of_distress_buff: 
            return None

        player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
        current_energy_percent = GLOBAL_CACHE.Agent.GetEnergy(player_agent_id)

        if current_energy_percent > 0.6: 
            return None

        buff_time_remaining = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(GLOBAL_CACHE.Player.GetAgentID(), self.custom_skill.skill_id)
        if buff_time_remaining > self.renew_before_expiration_in_milliseconds: return None

        return self.score_definition.get_score() 

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result