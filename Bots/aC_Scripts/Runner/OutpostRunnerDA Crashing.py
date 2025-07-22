import Py4GW
import math
from typing import Tuple
from Py4GWCoreLib import Profession
from Py4GWCoreLib import GLOBAL_CACHE
from Py4GWCoreLib import Routines
from Py4GWCoreLib import ConsoleLog
from Py4GWCoreLib import AgentArray
from Py4GWCoreLib import Agent
from Py4GWCoreLib import Range
from Py4GWCoreLib import Utils
from Py4GWCoreLib import *
from dangerous_models_runtime import can_cripple, can_knockdown



class OutpostRunnerDA:
    def __init__(self):
        self.name = "Skill Manager"
        self.required_primary = Profession.Dervish
        self.required_secondary = Profession.Assassin
        self.template_code = "Ogei8xsMNudgxjozgAdAdXSTCA"

        self._last_cast_time = {}  # debounce table for skill IDs
        self._debounce_ms = 0.3   # 300ms minimum between same-skill casts

        # Toggle for debug logs
        self.debug_logs = True

        # Store skill IDs and slots for quick access
        self.zealous_renewal      = GLOBAL_CACHE.Skill.GetID("Zealous_Renewal")
        self.pious_haste          = GLOBAL_CACHE.Skill.GetID("Pious_Haste")
        self.dwarven_stability    = GLOBAL_CACHE.Skill.GetID("Dwarven_Stability")
        self.i_am_unstoppable     = GLOBAL_CACHE.Skill.GetID("I_Am_Unstoppable")
        self.shadow_form          = GLOBAL_CACHE.Skill.GetID("Shadow_Form")
        self.heart_of_shadow      = GLOBAL_CACHE.Skill.GetID("Heart_of_Shadow")
        self.shroud_of_distress   = GLOBAL_CACHE.Skill.GetID("Shroud_of_Distress")
        self.deadly_paradox      = GLOBAL_CACHE.Skill.GetID("Deadly_Paradox")

        self.zealous_slot         = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.zealous_renewal)
        self.pious_slot           = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.pious_haste)
        self.dwarven_slot         = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.dwarven_stability)
        self.iau_slot             = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.i_am_unstoppable)
        self.shadow_form_slot     = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.shadow_form)
        self.heart_slot           = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.heart_of_shadow)
        self.shroud_slot          = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.shroud_of_distress)
        self.deadly_paradox_slot = GLOBAL_CACHE.SkillBar.GetSlotBySkillID(self.deadly_paradox)

    def _can_cast_now(self, skill_id):
        now = time.time()
        last = self._last_cast_time.get(skill_id, 0)
        return (now - last) > self._debounce_ms

    def _mark_cast(self, skill_id):
        self._last_cast_time[skill_id] = time.time()

    def safe_cast(self, skill_id, aftercast_delay=250, log=False):
        """Wrapper around Routines.Yield.Skills.CastSkillID with debounce protection"""
        if not self._can_cast_now(skill_id):
            return False
        GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
        if Routines.Yield.Skills.CastSkillID(skill_id, log=log, aftercast_delay=aftercast_delay):
            self._mark_cast(skill_id)
            return True
        return False

    def ProcessSkillCasting(self):
        # Helper: compute cosine similarity between two vectors (for angle calculations)
        def vector_cos(v1, v2):
            dot = v1[0]*v2[0] + v1[1]*v2[1]
            mag1 = (v1[0]**2 + v1[1]**2) ** 0.5
            mag2 = (v2[0]**2 + v2[1]**2) ** 0.5
            if mag1 == 0 or mag2 == 0:
                return 1  # default if no direction
            return dot / (mag1 * mag2)

        while True:
            # Basic sanity checks: valid map, not loading, player alive, etc.
            if not Routines.Checks.Map.MapValid():
                yield from Routines.Yield.wait(1000)
                continue
            if GLOBAL_CACHE.Agent.IsDead(GLOBAL_CACHE.Player.GetAgentID()):
                yield from Routines.Yield.wait(1000)
                continue
            if not Routines.Checks.Skills.CanCast():
                # If player is casting, knocked down, etc., wait briefly
                yield from Routines.Yield.wait(100)
                continue

            player_id = GLOBAL_CACHE.Player.GetAgentID()
            player_pos = GLOBAL_CACHE.Player.GetXY()
            px, py = player_pos[0], player_pos[1]
            # Unit vector for player's facing direction (to evaluate front/back for targeting)
            facing_angle = GLOBAL_CACHE.Agent.GetRotationAngle(player_id)
            facing_vector = (math.cos(facing_angle), math.sin(facing_angle))

            # === Preemptive Anti-KD/Cripple ===
            if Routines.Checks.Skills.IsSkillSlotReady(self.iau_slot) and \
               not Routines.Checks.Effects.HasBuff(player_id, self.i_am_unstoppable):

                nearby_enemies = Routines.Agents.GetFilteredEnemyArray(px, py, 1500.0)
                danger_found = False
                for eid in nearby_enemies:
                    if GLOBAL_CACHE.Agent.IsAlive(eid):
                        mid = GLOBAL_CACHE.Agent.GetModelID(eid)
                        if can_cripple(mid) or can_knockdown(mid):
                            danger_found = True
                            break
                if danger_found:
                    if self.debug_logs:
                        ConsoleLog(self.name, "Dangerous enemy ahead! Preemptively using 'I Am Unstoppable!'", 
                                   Py4GW.Console.MessageType.Info, log=True)
                    if Routines.Yield.Skills.CastSkillID(self.i_am_unstoppable, log=False, aftercast_delay=100):
                        yield from Routines.Yield.wait(100)
                        continue

            # **1. Anti-Cripple:** Use "I Am Unstoppable!" immediately if crippled
            if Routines.Checks.Effects.HasBuff(player_id, self.i_am_unstoppable) is False:
                # (No direct HasCondition in API; using buff check as proxy or assume a method exists)
                # Check if player has "Crippled" condition (implementation dependent)
                if  GLOBAL_CACHE.Agent.IsCrippled(player_id):
                    ConsoleLog(self.name, "Crippled! Using 'I Am Unstoppable!'", 
                               Py4GW.Console.MessageType.Info, log=True)
                    if Routines.Yield.Skills.CastSkillID(self.i_am_unstoppable, log=False, aftercast_delay=100):
                        yield from Routines.Yield.wait(100)
                        continue

            # **2. Preemptive Shadow Form:** Cast before hitting caster mobs (~1500 range)
            has_sf = Routines.Checks.Effects.HasBuff(player_id, self.shadow_form)
            if not has_sf and Routines.Checks.Skills.IsSkillSlotReady(self.shadow_form_slot):
                # Scan for any hostile spellcaster within ~1500 units
                enemies_near = Routines.Agents.GetFilteredEnemyArray(px, py, 1500.0)
                caster_found = False
                for eid in enemies_near:
                    if GLOBAL_CACHE.Agent.IsAlive(eid) and not GLOBAL_CACHE.Agent.IsMartial(eid):
                        # Found an enemy that is likely a caster (not a martial attacker)
                        caster_found = True
                        break
                if caster_found:
                    player_agent_id = GLOBAL_CACHE.Player.GetAgentID()
                    has_deadly_paradox = Routines.Checks.Effects.HasBuff(player_agent_id, self.deadly_paradox)
                    # 1) Reset action queue before Deadly Paradox
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")

                    # 2) Cast Deadly Paradox if not already active
                    if not has_deadly_paradox and Routines.Checks.Skills.IsSkillSlotReady(self.deadly_paradox_slot):
                        ConsoleLog(self.name, "Casting Deadly Paradox before Shadow Form.", Py4GW.Console.MessageType.Info)
                        if Routines.Yield.Skills.CastSkillID(
                            self.deadly_paradox,
                            log=False,
                            aftercast_delay=200
                        ):
                            yield from Routines.Yield.wait(200)  # allow DP buff to apply

                    # 3) Reset queue again before Shadow Form
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")

                    # 4) Cast Shadow Form
                    if Routines.Yield.Skills.CastSkillID(
                        self.shadow_form,
                        log=False,
                        aftercast_delay=1950
                    ):
                        ConsoleLog(self.name, "Approaching casters: activating Shadow Form.", Py4GW.Console.MessageType.Info)
                        yield from Routines.Yield.wait(1950)
                        continue

            # **3. Emergency Defense:** Shroud of Distress if HP < 60% and not already active
            if GLOBAL_CACHE.Agent.GetHealth(player_id) < 0.60:
                has_shroud = Routines.Checks.Effects.HasBuff(player_id, self.shroud_of_distress)
                if not has_shroud and Routines.Checks.Skills.IsSkillSlotReady(self.shroud_slot):
                    ConsoleLog(self.name, "Health low! Casting Shroud of Distress.", 
                               Py4GW.Console.MessageType.Info, log=True)
                    if Routines.Yield.Skills.CastSkillID(self.shroud_of_distress, log=False, aftercast_delay=1750):
                        yield from Routines.Yield.wait(1750)
                        continue

            # **4. Maintain Stances:** Keep Pious Haste (speed) and Dwarven Stability up
            # Always cast Zealous Renewal immediately before Pious Haste for +50% IMS:contentReference[oaicite:9]{index=9}.
            has_pious   = Routines.Checks.Effects.HasBuff(player_id, self.pious_haste)
            has_dwarven = Routines.Checks.Effects.HasBuff(player_id, self.dwarven_stability)
            if not has_pious:
                # Extend stance duration first
                if not has_dwarven:
                    self.safe_cast(self.dwarven_stability, aftercast_delay=300)
                    yield from Routines.Yield.wait(300)

                # **Debounced** Zealous Renewal
                if Routines.Checks.Skills.IsSkillSlotReady(self.zealous_slot):
                    if self.safe_cast(self.zealous_renewal, aftercast_delay=300):
                        yield from Routines.Yield.wait(300)

                # **Debounced** Pious Haste
                if self.safe_cast(self.pious_haste, aftercast_delay=900):
                    ConsoleLog(self.name, "Activated Pious Haste (safe-cast).", Py4GW.Console.MessageType.Info, log=True)
                    yield from Routines.Yield.wait(900)
                continue

            # **6. Shadow Step for Distance (Heart of Shadow):** use on rear enemy for forward escape
            if Routines.Checks.Skills.IsSkillSlotReady(self.heart_slot):
                # Find an enemy directly behind the player to maximize forward teleport
                target_enemy = None
                most_behind_val = 1.0  # looking for lowest cosine (most behind, approaching -1)
                enemies_around = Routines.Agents.GetFilteredEnemyArray(px, py, 1000.0)
                for eid in enemies_around:
                    if not GLOBAL_CACHE.Agent.IsAlive(eid):
                        continue
                    ex, ey = GLOBAL_CACHE.Agent.GetXY(eid)
                    to_enemy_vec = (ex - px, ey - py)
                    cos_angle = vector_cos(facing_vector, to_enemy_vec)
                    if cos_angle < most_behind_val:
                        most_behind_val = cos_angle
                        target_enemy = eid
                if target_enemy:
                    GLOBAL_CACHE._ActionQueueManager.ResetQueue("ACTION")
                    yield from Routines.Yield.Agents.ChangeTarget(target_enemy)
                    ConsoleLog(self.name, "Using Heart of Shadow on rear target to leap forward.", 
                               Py4GW.Console.MessageType.Info, log=True)
                    if Routines.Yield.Skills.CastSkillID(self.heart_of_shadow, log=False, aftercast_delay=500):
                        yield from Routines.Yield.wait(800)
                        #GLOBAL_CACHE.Player.ChangeTarget(0)
                        # (Heart of Shadow heals as well, providing sustain during the run)
                        continue

            # Short idle wait before next loop iteration
            yield from Routines.Yield.wait(100)
