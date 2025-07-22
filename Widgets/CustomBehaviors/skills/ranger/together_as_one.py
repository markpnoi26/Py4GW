from typing import Any
from typing import Callable
from typing import Generator
from typing import List
from typing import override

from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.constants import DEBUG
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.helpers.targeting_order import TargetingOrder
from Widgets.CustomBehaviors.primitives.scores.score_per_agent_quantity_definition import (
    ScorePerAgentQuantityDefinition,
)
from Widgets.CustomBehaviors.primitives.scores.score_static_definition import ScoreStaticDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_utility_base import CustomSkillUtilityBase


class TogetherAsOneUtility(CustomSkillUtilityBase):
    def __init__(self, 
        current_build: list[CustomSkill], 
        score_definition: ScoreStaticDefinition = ScoreStaticDefinition(90),
        mana_required_to_cast: int = 0,
        allowed_states: list[BehaviorState] = [BehaviorState.IN_AGGRO, BehaviorState.CLOSE_TO_AGGRO, BehaviorState.FAR_FROM_AGGRO]
        ) -> None:

        super().__init__(
            skill=CustomSkill("Together_as_one"), 
            in_game_build=current_build, 
            score_definition=score_definition,
            mana_required_to_cast=mana_required_to_cast, 
            allowed_states=allowed_states)
                
        self.score_definition: ScoreStaticDefinition = score_definition

    @override
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:

        return self.score_definition.get_score()

    @override
    def _execute(self, state: BehaviorState) -> Generator[Any, None, BehaviorResult]:

        if state is BehaviorState.IN_AGGRO:
            agent_array = GLOBAL_CACHE.AgentArray.GetAllyArray()
            agent_array = AgentArray.Filter.ByCondition(agent_array, lambda agent_id: GLOBAL_CACHE.Agent.IsAlive(agent_id))
            agent_array = AgentArray.Filter.ByCondition(agent_array, lambda agent_id: agent_id != GLOBAL_CACHE.Player.GetAgentID())
            agent_array = AgentArray.Filter.ByDistance(agent_array, GLOBAL_CACHE.Player.GetXY(), Range.Spellcast.value)

            agent_ids: list[int] = [agent_id for agent_id in agent_array]

            gravity_center: custom_behavior_helpers.GravityCenter | None = custom_behavior_helpers.Targets.find_optimal_gravity_center(Range.Area, agent_ids=agent_ids)
            if gravity_center is not None:
                if gravity_center.distance_from_player < Range.Area.value: # else it doesn't worth moving, we are too far
                    if DEBUG: print("TogetherAsOneUtility: moving to a better place (gravity center).")
                    exit_condition: Callable[[], bool] = lambda: False
                    tolerance: float = 30
                    path_points: list[tuple[float, float]] = [gravity_center.coordinates]
                    yield from Routines.Yield.Movement.FollowPath(
                        path_points=path_points, 
                        custom_exit_condition=exit_condition, 
                        tolerance=tolerance, log=True, 
                        timeout=4000, 
                        progress_callback=lambda progress: print(f"TogetherAsOneUtility: progress: {progress}"))
        
        result = yield from custom_behavior_helpers.Actions.cast_skill(self.custom_skill)
        return result