from abc import abstractmethod
from collections.abc import Generator
from typing import Any

from HeroAI.cache_data import CacheData
from Py4GWCoreLib import Routines
from Widgets.CustomBehaviors.primitives.behavior_state import BehaviorState
from Widgets.CustomBehaviors.primitives.constants import DEBUG
from Widgets.CustomBehaviors.primitives.helpers import custom_behavior_helpers
from Widgets.CustomBehaviors.primitives.helpers.behavior_result import BehaviorResult
from Widgets.CustomBehaviors.primitives.scores.score_definition import ScoreDefinition
from Widgets.CustomBehaviors.primitives.skills.custom_skill import CustomSkill
from Widgets.CustomBehaviors.primitives.skills.custom_skill_nature import CustomSkillNature


class CustomSkillUtilityBase:
    def __init__(self, skill: CustomSkill,
                 in_game_build: list[CustomSkill],
                 score_definition:ScoreDefinition,
                 mana_required_to_cast:float=0,
                 allowed_states:list[BehaviorState]=[BehaviorState.IN_AGGRO]):
        self.custom_skill: CustomSkill = skill
        self.in_game_build: list[CustomSkill] = in_game_build
        self.allowed_states: list[BehaviorState] | None = allowed_states
        self.mana_required_to_cast: float = mana_required_to_cast

    @abstractmethod
    def are_common_pre_checks_valid(self, current_state: BehaviorState) -> bool:
        if current_state is BehaviorState.IDLE: return False
        if self.allowed_states is not None and current_state not in self.allowed_states: return False
        if custom_behavior_helpers.Resources.get_player_absolute_energy() < self.mana_required_to_cast: return False
        if not Routines.Checks.Skills.IsSkillIDReady(self.custom_skill.skill_id): return False
        if not custom_behavior_helpers.Resources.has_enough_resources(self.custom_skill): return False
        return True
    
    @abstractmethod
    def _evaluate(self, current_state: BehaviorState, previously_attempted_skills: list[CustomSkill]) -> float | None:
        pass

    @abstractmethod
    def _execute(self, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        pass

    def evaluate(self, current_state: BehaviorState, previously_attempted_skills:list[CustomSkill]) -> float | None:
        # return self.custom_skill.skill_id
        if not self.are_common_pre_checks_valid(current_state): return None
        score:float | None = self._evaluate(current_state, previously_attempted_skills)
        if score is None: return None
        if score < 0 and score > 100: raise Exception(f"{self.custom_skill.skill_name} : score must be between 0 and 100, calculated {score}.")
        return score

    def execute(self, cached_data: CacheData, state: BehaviorState) -> Generator[Any | None, Any | None, BehaviorResult]:
        print(f"Executing {self.custom_skill.skill_name}")
        gen:Generator[Any | None, Any | None, BehaviorResult] = self._execute(state)
        result:BehaviorResult = yield from gen
        return result

    def nature_has_been_attempted_last(self, previously_attempted_skills: list[CustomSkill]) -> bool:
        if len(previously_attempted_skills) == 0: return False
        last_value = previously_attempted_skills[-1]
        is_nature_has_been_attempted_last = last_value.skill_nature == self.custom_skill.skill_nature
        return is_nature_has_been_attempted_last

    def is_another_interrupt_ready(self) -> bool:
        for skill in self.in_game_build:
            if skill.skill_nature == CustomSkillNature.Interrupt and skill.skill_id != self.custom_skill.skill_id:
                if Routines.Checks.Skills.IsSkillIDReady(skill.skill_id):
                    return True
        return False