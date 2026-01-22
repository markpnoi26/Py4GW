class ModifierValueArg(IntEnum):
    None_ = -1
    Arg1 = 0
    Arg2 = 1
    Fixed = 2


rune_modifiers = [

]


def armor_matches_modifiers(comparison_modifiers: list[tuple[int, int, int]]) -> tuple[bool, bool]:
    results: list[tuple[bool, bool]] = []

    for mod in rune_modifiers:
        matched = False
        maxed = False

        for identifier, arg1, arg2 in comparison_modifiers:
            if mod.identifier != identifier:
                continue

            if mod.modifier_value_arg == ModifierValueArg.Arg1:
                if arg1 >= mod.min and arg1 <= mod.max and arg2 == mod.arg2:
                    matched = True
                    maxed = arg1 >= mod.max
                    results.append((matched, maxed))

            elif mod.modifier_value_arg == ModifierValueArg.Arg2:
                if arg2 >= mod.min and arg2 <= mod.max and arg1 == mod.arg1:
                    matched = True
                    maxed = arg2 >= mod.max
                    results.append((matched, maxed))

            elif mod.modifier_value_arg == ModifierValueArg.Fixed:
                if arg1 == mod.arg1 and arg2 == mod.arg2:
                    matched = True
                    maxed = True
                    results.append((matched, maxed))

        if not matched:
            return False, False

    if not results:
        return False, False

    if any(result[0] == False for result in results):
        return False, False

    return all(result[0] for result in results), all(result[1] for result in results)
