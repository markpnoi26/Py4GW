import math
from typing import Tuple

from dangerous_models_runtime import can_cripple
from dangerous_models_runtime import can_knockdown

import Py4GW
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Agent
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import Profession
from Py4GWCoreLib import Range
from Py4GWCoreLib import Routines
from Py4GWCoreLib import Utils


class Build:
    def __init__(
        self,
        name: str = "Generic Build",
        required_primary: Profession = Profession(0),
        required_secondary: Profession = Profession(0),
        template_code: str = "AAAAAAAAAAAAAAAA",
        skills: list[int] = []
    ):
        self.build_name = name
        self.required_primary: Profession = required_primary
        self.required_secondary: Profession = required_secondary
        self.template_code = template_code
        self.skills = skills

    def ValidatePrimary(self, profession: Profession) -> bool:
        return self.required_primary == profession

    def ValidateSecondary(self, profession: Profession) -> bool:
        return self.required_secondary == profession

    def ValidateSkills(self):
        skills: list[int] = []
        for i in range(8):
            skill = GLOBAL_CACHE.SkillBar.GetSkillIDBySlot(i + 1)
            if skill:
                skills.append(skill)

        all_valid = sorted(self.skills) == sorted(skills)
        yield from Routines.Yield.wait(0 if all_valid else 1000)
        return all_valid

    def EquipBuild(self):
        yield from Routines.Yield.Skills.LoadSkillbar(self.template_code, log=False)

    def LoadSkillBar(self):
        yield from Routines.Yield.Skills.LoadSkillbar(self.template_code, log=False)

    def ProcessSkillCasting(self):
        raise NotImplementedError


class OutpostRunnerDA(Build):
    def __init__(self):
        super().__init__(
            name="D/A Outpost Runner",
            required_primary=Profession.Dervish,
            required_secondary=Profession.Assassin,
            template_code="Ogej4NfMLTIQ0k6MHYjb3l4OHQA"
        )

        self.debug_logs = True

        # Skill IDs
        self.zealous_renewal = GLOBAL_CACHE.Skill.GetID("Zealous_Renewal")
        self.pious_haste = GLOBAL_CACHE.Skill.GetID("Pious_Haste")
        self.dwarven_stability = GLOBAL_CACHE.Skill.GetID("Dwarven_Stability")
        self.i_am_unstoppable = GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable")
        self.shadow_form = GLOBAL_CACHE.Skill.GetID("Shadow_Form")
        self.heart_of_shadow = GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow")
        self.shroud_of_distress = GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
        self.deadly_paradox = GLOBAL_CACHE.Skill.GetID("Deadly_Paradox")

        # Skill slots
        self.zealous_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.zealous_renewal)
        self.pious_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.pious_haste)
        self.dwarven_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.dwarven_stability)
        self.iau_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.i_am_unstoppable)
        self.shadow_form_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.shadow_form)
        self.heart_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.heart_of_shadow)
        self.shroud_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.shroud_of_distress)
        self.deadly_paradox_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.deadly_paradox)

    # === SAFE CAST ===
    def safe_cast(self, skill_id, slot=None, aftercast=300, log_msg=None):
        """Safe casting"""
        if slot and not Routines.Checks.Skills.IsSkillSlotReady(slot):
            return False

        #GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
        ok = Routines.Yield.Skills.CastSkillID(skill_id, log=False, aftercast_delay=aftercast)
        if ok:
            if log_msg:
                ConsoleLog(self.build_name, log_msg, Py4GW.Console.MessageType.Info, log=True)
            yield from Routines.Yield.wait(aftercast + 150)
            return True
        return False

    # === VECTOR ANGLE like BuildMgr ===
    def vector_angle(self, a: Tuple[float, float], b: Tuple[float, float]) -> float:
        dot = a[0] * b[0] + a[1] * b[1]
        mag_a = math.hypot(*a)
        mag_b = math.hypot(*b)
        if mag_a == 0 or mag_b == 0:
            return 1
        return dot / (mag_a * mag_b)  # cosine similarity

    # === SAFE HEART OF SHADOW TELEPORT ===
    def safe_heart_teleport(self):
        """Teleports using Heart of Shadow only if there is an enemy within Touch range."""

        # Now we know there is at least one valid enemy → target nearest in Earshot
        if Routines.Yield.Agents.TargetNearestEnemy(Range.Earshot.value):
            yield from Routines.Yield.wait(500)

        # Cast Heart of Shadow on the targeted enemy
        yield from self.safe_cast(self.heart_of_shadow, self.heart_slot, 1000, "Emergency retreat: Heart of Shadow")

        # Wait for teleport animation if queue reset succeeded
        if GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION"):
            yield from Routines.Yield.wait(1000)

    def ProcessSkillCasting(self):
        while True:
            # === BASIC SAFE GUARDS ===
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue
            if not GLOBAL_CACHE.Map.IsExplorable():
                yield from Routines.Yield.wait(1000)
                return

            player_id = GLOBAL_CACHE.Player.GetAgentID()
            if GLOBAL_CACHE.Agent.IsDead(player_id):
                if GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION"):
                    yield from Routines.Yield.wait(1000)
                continue
            if not Routines.Checks.Skills.CanCast():
                yield from Routines.Yield.wait(100)
                continue

            # === BUFF STATE ===
            total_range = Range(max(Range.Spellcast.value, Range.Area.value))
            in_danger = Routines.Checks.Agents.InDanger(total_range)
            in_touch = Routines.Checks.Agents.InDanger(Range.Touch)
            has_shadow_form = Routines.Checks.Effects.HasBuff(player_id, self.shadow_form)
            shadow_time = GLOBAL_CACHE.Effects.GetEffectTimeRemaining(player_id, self.shadow_form) if has_shadow_form else 0
            has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_id, self.deadly_paradox)
            has_shroud = Routines.Checks.Effects.HasBuff(player_id, self.shroud_of_distress)
            has_pious = Routines.Checks.Effects.HasBuff(player_id, self.pious_haste)
            has_dwarven = Routines.Checks.Effects.HasBuff(player_id, self.dwarven_stability)
            hp = GLOBAL_CACHE.Agent.GetHealth(player_id)

            # === 1. SHADOW FORM + PARADOX MAINTENANCE ===
            if in_danger and shadow_time <= 3500:
                if not has_shadow_form:
                    # Force combo in one go
                    yield from self.safe_cast(self.deadly_paradox, self.deadly_paradox_slot, 100, "Casting Deadly Paradox")
                    # Immediately follow with SF
                    yield from self.safe_cast(self.shadow_form, self.shadow_form_slot, 2000, "Casting Shadow Form")


            # === 2. LOW-HP EMERGENCY SHROUD ===
            if hp < 0.60 and not has_shroud:
                yield from self.safe_cast(self.shroud_of_distress, self.shroud_slot, 2000, "Casting Shroud of Distress")
                continue

            # === 3. PREEMPTIVE ANTI-KD ===
            if Routines.Checks.Skills.IsSkillSlotReady(self.iau_slot) and not Routines.Checks.Effects.HasBuff(player_id, self.i_am_unstoppable):
                # scan nearby dangerous models
                danger_found = False
                for eid in Routines.Agents.GetFilteredEnemyArray(*GLOBAL_CACHE.Player.GetXY(), 1500.0):
                    if GLOBAL_CACHE.Agent.IsAlive(eid):
                        mid = GLOBAL_CACHE.Agent.GetModelID(eid)
                        if can_cripple(mid) or can_knockdown(mid):
                            danger_found = True
                            break
                if danger_found:
                    yield from self.safe_cast(self.i_am_unstoppable, self.iau_slot, 1750,"Anti cripple/kd casting: I Am Unstoppable!")
                    continue

            # === 4. MAINTAIN RUNNING STANCES ===
            both_ready = Routines.Checks.Skills.IsSkillSlotReady(self.zealous_slot) and Routines.Checks.Skills.IsSkillSlotReady(self.pious_slot)

            if not has_pious:
                # Refresh dwarven first for stance extension
                if not has_dwarven and Routines.Checks.Skills.IsSkillSlotReady(self.dwarven_slot):
                    yield from self.safe_cast(self.dwarven_stability, self.dwarven_slot, 750,
                                              "Maintaining stance extension: Dwarven Stability")
                    continue

                # Zealous Renewal → Pious Haste combo
                if both_ready:
                    yield from self.safe_cast(self.zealous_renewal, self.zealous_slot, 750,
                                              "Maintaining speed: Zealous Renewal")
                    continue

                if Routines.Checks.Skills.IsSkillSlotReady(self.pious_slot):
                    yield from self.safe_cast(self.pious_haste, self.pious_slot, 750,
                                              "Maintaining speed: Pious Haste")
                    continue

            elif not has_dwarven:
                yield from self.safe_cast(self.dwarven_stability, self.dwarven_slot, 750,
                                          "Maintaining stance extension: Dwarven Stability")
                continue

            # === 5. EMERGENCY TELEPORT IF TOO LOW HP ===

            if in_touch:
                yield from self.safe_heart_teleport()
                continue

            # === IDLE WAIT ===
            yield from Routines.Yield.wait(150)
